from fido2.utils import websafe_encode, websafe_decode
from fido import fido2_server
import time
from bson import ObjectId
from fastapi import APIRouter, Request, HTTPException, Response
from db import users
from auth import create_access_token, decode_access_token


router = APIRouter(prefix="/mfa", tags=["Mfa"])

# Stato temporaneo WebAuthn (in memoria)
_mfa_states = {}

@router.post("/register/begin")
async def mfa_register_begin(request: Request):
    user_id = request.state.user_id  # string o ObjectId

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
async def mfa_register_complete(request: Request):
    user_id = request.state.user_id
    body = await request.body()

    state = _mfa_states.get(user_id)
    if not state:
        raise HTTPException(status_code=400, detail="Missing MFA state")

    data = fido2_server.register_complete(
        state,
        body,
    )

    users.update_one(
        {"_id": ObjectId(user_id)},
        {
            "$set": {
                "mfa_enabled": True,
            },
            "$push": {
                "mfa_credentials": data.credential_data,
            },
        },
    )

    del _mfa_states[user_id]

    return {"status": "mfa_registered"}

