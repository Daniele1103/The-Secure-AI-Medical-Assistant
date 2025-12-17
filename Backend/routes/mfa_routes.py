from bson import ObjectId
from fastapi import APIRouter, Cookie, HTTPException, Response, Request
from db import users
from auth import get_user_id_from_token, create_access_token
from fido import fido2_server  # import del server già configurato
from fido2 import cbor
import cbor2
import base64
from fido2.server import to_descriptor
from fido2.webauthn import AttestedCredentialData
from fido2.webauthn import PublicKeyCredentialDescriptor
from fido2.cose import CoseKey

router = APIRouter(prefix="/mfa", tags=["Mfa"])


def websafe_b64decode(data: str) -> bytes:
    # Aggiunge padding se necessario
    padding = '=' * ((4 - len(data) % 4) % 4)
    return base64.urlsafe_b64decode(data + padding)

def websafe_b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

@router.post("/register/cancel")
async def register_cancel(access_token: str = Cookie(None)):
    user_id = get_user_id_from_token(access_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Utente non autenticato")
    users.update_one({"_id": ObjectId(user_id)}, {"$unset": {"mfa_challenge": ""}})
    return {"status": "cancelled"}

# =====================
# REGISTER BEGIN
# =====================
@router.post("/register/begin")
async def register_begin(access_token: str = Cookie(None)):

    print("Token ricevuto:", access_token)
    
    user_id = get_user_id_from_token(access_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Utente non autenticato")

    user = users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato")

    devices = []
    for d in user.get("webauthn_credentials", []):
        cred = AttestedCredentialData.create(
            aaguid=b"\x00" * 16,
            credential_id=websafe_b64decode(d["credential_id"]),
            public_key=CoseKey.parse(cbor2.loads(base64.urlsafe_b64decode(d["public_key"] + "==")))
        )
    devices.append(to_descriptor(cred))

    options, state = fido2_server.register_begin(
        {
            "id": str(user["_id"]).encode(),
            "name": user["email"],
            "displayName": user["email"]
        },
        credentials=devices,
        user_verification= "preferred"
    )

    users.update_one(
        {"_id": user["_id"]},
        {"$set": {"mfa_challenge": state}}
    )

    return Response(
        content=cbor.encode(options),
        media_type="application/cbor"
    )

# =====================
# REGISTER COMPLETE
# =====================
@router.post("/register/complete")
async def register_complete(request: Request, access_token: str = Cookie(None)):

    user_id = get_user_id_from_token(access_token)
    if not user_id:
        raise HTTPException(status_code=401)

    user = users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404)

    credential = await request.json()

    state = user.get("mfa_challenge")
    if not state:
        raise HTTPException(status_code=400, detail="Nessuna sfida MFA in corso")

    auth_data = fido2_server.register_complete(state, credential)

    cred = auth_data.credential_data
    print("cred: ",cred)

    device_record = {
        "credential_id": base64.urlsafe_b64encode(cred.credential_id).rstrip(b"=").decode(),
        "public_key": base64.urlsafe_b64encode(cbor2.dumps(cred.public_key)).decode(),
    }

    users.update_one(
        {"_id": user["_id"]},
        {
            "$push": {"webauthn_credentials": device_record},
            "$unset": {"mfa_challenge": ""},
            "$set": {"mfa_enabled": True},
        }
    )

    return {"status": "ok"}

# =======================
# LOGIN BEGIN
# =======================
@router.post("/login/begin")
async def login_begin(request: Request):
    """
    Genera le opzioni MFA per il login (WebAuthn Assertion)
    """
    data = await request.json()
    user_id = data.get("user_id")
    user = users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato")

    devices = [
        {
            "id": websafe_b64decode(d["credential_id"]),
            "type": d.get("type", "public-key")
        } for d in user.get("webauthn_credentials", [])
    ]

    if not devices:
        raise HTTPException(status_code=400, detail="Nessun dispositivo MFA registrato")

    options, state = fido2_server.authenticate_begin(devices)

    # Salva lo stato della challenge temporanea nel DB
    users.update_one({"_id": user["_id"]}, {"$set": {"mfa_challenge": state}})

    return Response(content=cbor.encode(options), media_type="application/cbor")

# =======================
# LOGIN COMPLETE
# =======================

@router.post("/login/complete")
async def mfa_login_complete(request: Request, response: Response):
    data = await request.json()

    user_id = data.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id mancante")

    user = users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato")

    credential = data.copy()
    credential.pop("user_id", None)

    # Ricostruisci le credenziali registrate
    def decode_public_key(encoded):
        return cbor2.loads(base64.urlsafe_b64decode(encoded + '=='))

    registered_credentials = [
        AttestedCredentialData.create(
            aaguid=b"\x00" * 16,
            credential_id=websafe_b64decode(d["credential_id"]),
            public_key=CoseKey.parse(cbor2.loads(base64.urlsafe_b64decode(d["public_key"] + "=="))) 
            )
        for d in user.get("webauthn_credentials", [])
    ]


    state = user.get("mfa_challenge")
    if not state:
        raise HTTPException(status_code=400, detail="Nessuna sfida MFA in corso")

    # VERIFICA WEBAUTHN
    try:
        fido2_server.authenticate_complete(
            state,
            registered_credentials,
            credential
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"MFA fallita: {str(e)}")

    # Pulisci challenge
    users.update_one({"_id": user["_id"]}, {"$unset": {"mfa_challenge": ""}})

    # JWT
    token = create_access_token({
        "sub": str(user["_id"]),
        "email": user["email"]
    })

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=3600
    )

    return {"message": "Login MFA completato"}