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

    # Salva il nuovo device MFA
    devices = user.get("webauthn_credentials", [])
    devices.append(auth_data.credential_data)
    users.update_one(
    {"_id": user["_id"]},
    {
        "$set": {
            "webauthn_credentials": devices,
            "mfa_enabled": True
        },
        "$unset": {
            "mfa_challenge": ""
        }
    }
)


    return {"status": "ok"}