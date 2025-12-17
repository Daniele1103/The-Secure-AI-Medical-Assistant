from fido2.utils import websafe_encode, websafe_decode
from fido import fido2_server
import time
from bson import ObjectId
from fastapi import APIRouter, Cookie, HTTPException, Response
from db import users
from auth import get_user_id_from_token
from fido2 import cbor

router = APIRouter(prefix="/mfa", tags=["Mfa"])

# Stato temporaneo WebAuthn (in memoria)
_mfa_states = {}

# ----------------------------
# BEGIN REGISTRATION
# ----------------------------
@router.post("/register/begin")
async def mfa_register_begin(access_token: str = Cookie(None)):
    print("===== BEGIN MFA REGISTRATION =====")
    
    if not access_token:
        print("Errore: token mancante")
        raise HTTPException(status_code=401, detail="Token mancante")

    user_id = get_user_id_from_token(access_token)
    print(f"user_id estratto dal token: {user_id}")
    
    if not user_id:
        print("Errore: token non valido")
        raise HTTPException(status_code=401, detail="Token non valido")

    user = users.find_one({"_id": ObjectId(user_id)})
    if not user:
        print(f"Errore: utente {user_id} non trovato")
        raise HTTPException(status_code=404, detail="User not found")

    print(f"Utente trovato: {user['email']} ({user['_id']})")
    
    options, state = fido2_server.register_begin(
        {
            "id": str(user["_id"]).encode(),
            "name": user["email"],
            "displayName": user["email"],
        },
        user.get("mfa_credentials", []),
        user_verification="preferred",
    )

    _mfa_states[user_id] = state
    print(f"Challenge salvata in memoria per user_id {user_id}")
    print(f"Options inviate al frontend: {options}")

    return Response(
        content=cbor.encode(options),
        media_type="application/cbor",
    )


# ----------------------------
# COMPLETE REGISTRATION
# ----------------------------
@router.post("/register/complete")
async def mfa_register_complete(access_token: str = Cookie(None), raw: bytes = None):
    print("===== COMPLETE MFA REGISTRATION =====")

    if not access_token:
        print("Errore: token mancante")
        raise HTTPException(status_code=401, detail="Token mancante")

    user_id = get_user_id_from_token(access_token)
    print(f"user_id estratto dal token: {user_id}")

    if not user_id:
        print("Errore: token non valido")
        raise HTTPException(status_code=401, detail="Token non valido")

    if raw is None:
        print("Errore: body della richiesta mancante")
        raise HTTPException(status_code=400, detail="Request body mancante")

    state = _mfa_states.get(user_id)
    if not state:
        print(f"Errore: nessuno stato MFA trovato per user_id {user_id}")
        raise HTTPException(status_code=400, detail="Missing MFA state")

    data = cbor.decode(raw)
    print(f"Dati ricevuti dal frontend: {data.keys()}")  # Mostra solo le chiavi principali

    auth_data = fido2_server.register_complete(
        state,
        data["attestationObject"],
        data["clientDataJSON"],
    )

    users.update_one(
        {"_id": ObjectId(user_id)},
        {
            "$set": {"mfa_enabled": True},
            "$push": {"mfa_credentials": auth_data.credential_data},
        },
    )
    print(f"MFA completata per user_id {user_id}. Credenziali salvate.")
    
    del _mfa_states[user_id]
    print(f"Stato temporaneo MFA rimosso per user_id {user_id}")

    return {"status": "mfa_registered"}
