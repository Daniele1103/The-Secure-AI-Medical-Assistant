from bson import ObjectId
from fastapi import APIRouter, Cookie, HTTPException, Response, Request
from db import users
from auth import get_user_id_from_token
from fido import fido2_server  # import del server già configurato
from fido2 import cbor
import base64

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

    devices = [
        {
            "id": websafe_b64decode(d["id"]),
            "type": d["type"]
        } for d in user.get("webauthn_credentials", [])
    ]

    options, state = fido2_server.register_begin(
        {
            "id": str(user["_id"]).encode(),
            "name": user["email"],
            "displayName": user["email"]
        },
        devices,
        user_verification="preferred"
    )

    # Salva lo stato della challenge nel DB
    users.update_one({"_id": user["_id"]}, {"$set": {"mfa_challenge": state}})

    return Response(content=cbor.encode(options), media_type="application/cbor")

# =====================
# REGISTER COMPLETE
# =====================
@router.post("/register/complete")
async def register_complete(request: Request, access_token: str = Cookie(None)):
    user_id = get_user_id_from_token(access_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Utente non autenticato")

    user = users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato")

    credential = await request.json()
    state = user.get("mfa_challenge")
    if not state:
        raise HTTPException(status_code=400, detail="Nessuna sfida MFA in corso")

    auth_data = fido2_server.register_complete(state, credential)

    device_record = {
        "id": base64.urlsafe_b64encode(auth_data.credential_data.credential_id).rstrip(b"=").decode(),
        "type": "public-key"
    }
    users.update_one(
        {"_id": user["_id"]},
        {"$push": {"webauthn_credentials": device_record}, "$unset": {"mfa_challenge": ""}, "$set": {"mfa_enabled": True}}
    )


    return {"status": "ok"}


# =======================
# LOGIN BEGIN
# =======================
@router.post("/login/begin")
async def login_begin(request: Request, userId: str):
    """
    Genera le opzioni MFA per il login (WebAuthn Assertion)
    """
    user = users.find_one({"_id": ObjectId(userId)})
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
async def login_complete(request: Request, access_token: str = Cookie(None)):
    """
    Completa il login MFA con la credential ottenuta dal browser
    """
    user_id = get_user_id_from_token(access_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Utente non autenticato")

    user = users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato")

    credential = await request.json()
    state = user.get("mfa_challenge")
    if not state:
        raise HTTPException(status_code=400, detail="Nessuna sfida MFA in corso")

    # Verifica l'assertion
    try:
        auth_data = fido2_server.authenticate_complete(state, user.get("webauthn_credentials", []), credential)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Autenticazione MFA fallita: {str(e)}")

    # Rimuove la challenge temporanea
    users.update_one({"_id": user["_id"]}, {"$unset": {"mfa_challenge": ""}})

    return {"status": "ok"}