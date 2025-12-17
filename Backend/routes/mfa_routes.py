from bson import ObjectId
from fastapi import APIRouter, Cookie, HTTPException, Response, Request
from db import users
from auth import get_user_id_from_token, create_access_token
from fido import fido2_server  # import del server già configurato
from fido2 import cbor
import base64
from fido2.server import to_descriptor
from fido2.webauthn import AttestedCredentialData

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
        cred = AttestedCredentialData(
            aaguid=b"\x00" * 16,
            credential_id=websafe_b64decode(d["credential_id"]),
            public_key=d["public_key"]
        )
        devices.append(to_descriptor(cred))

    options, state = fido2_server.register_begin(
        {
            "id": str(user["_id"]).encode(),
            "name": user["email"],
            "displayName": user["email"]
        },
        credentials=devices,
        user_verification="preferred"
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

    sign_count = getattr(cred, "sign_count", 0)
    print("sign_count",sign_count)

    device_record = {
    "credential_id": base64.urlsafe_b64encode(
        cred.credential_id
    ).rstrip(b"=").decode(),
    "public_key": cred.public_key,
    "sign_count": sign_count  # <-- usa auth_data.sign_count
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
            "id": websafe_b64decode(d["id"]),
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
    """
    Completa il login MFA e genera il cookie con JWT
    """
    data = await request.json()
    print("DEBUG: request body:", data)

    # Estrai user_id
    user_id = data.get("user_id")
    print("DEBUG: user_id:", user_id)
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id mancante")

    # Trova l'utente
    user = users.find_one({"_id": ObjectId(user_id)})
    print("DEBUG: user found:", user)
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato")

    # La credential è tutto il body tranne user_id
    credential = data.copy()
    credential.pop("user_id", None)
    print("DEBUG: credential to verify:", credential)

    # Verifica la challenge MFA
    state = user.get("mfa_challenge")
    print("DEBUG: MFA challenge state:", state)
    if not state:
        raise HTTPException(status_code=400, detail="Nessuna sfida MFA in corso")

    try:
        auth_data = fido2_server.authenticate_complete(
            state,
            user.get("webauthn_credentials", []),
            credential
        )
        print("DEBUG: auth_data:", auth_data)
    except Exception as e:
        print("DEBUG: MFA verification failed:", str(e))
        raise HTTPException(status_code=400, detail=f"MFA fallita: {str(e)}")

    # Cancella la challenge temporanea
    users.update_one({"_id": user["_id"]}, {"$unset": {"mfa_challenge": ""}})
    print("DEBUG: MFA challenge cleared")

    # Genera il JWT e setta il cookie
    token = create_access_token({
        "sub": str(user["_id"]),
        "email": user["email"]
    })
    print("DEBUG: JWT generated:", token)

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,  # HTTPS in produzione
        samesite="none",
        max_age=3600
    )
    print("DEBUG: cookie set")

    return {"message": "Login MFA completato"}

