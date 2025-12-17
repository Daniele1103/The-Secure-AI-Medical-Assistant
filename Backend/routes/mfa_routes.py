from fido2.utils import websafe_encode, websafe_decode
from fido import fido2_server
import time
from bson import ObjectId
from fastapi import APIRouter, Cookie, Request, HTTPException, Response
from db import users
from auth import create_access_token, decode_access_token
from fido2 import cbor
from auth import get_user_id_from_token

router = APIRouter(prefix="/mfa", tags=["Mfa"])

# Stato temporaneo WebAuthn (in memoria)
_mfa_states = {}

@router.post("/register/begin")
async def mfa_register_begin(access_token: str = Cookie(None)):
    if not access_token:
        raise HTTPException(status_code=401, detail="Token mancante")

    user_id = get_user_id_from_token(access_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Token non valido")

    user = users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

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

    return Response(
        content=options,
        media_type="application/cbor",
    )

@router.post("/register/complete")
async def mfa_register_complete(access_token: str = Cookie(None), raw: bytes = None):
    if not access_token:
        raise HTTPException(status_code=401, detail="Token mancante")

    user_id = get_user_id_from_token(access_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Token non valido")

    if raw is None:
        raise HTTPException(status_code=400, detail="Request body mancante")

    state = _mfa_states.get(user_id)
    if not state:
        raise HTTPException(status_code=400, detail="Missing MFA state")

    data = cbor.decode(raw)

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

    del _mfa_states[user_id]
    return {"status": "mfa_registered"}