from bson import ObjectId
from fastapi import APIRouter, Cookie, HTTPException, Response, Request
from db import users
from auth import get_user_id_from_token
from fido import fido2_server  # import del server già configurato
from fido2 import cbor

router = APIRouter(prefix="/mfa", tags=["Mfa"])

# =====================
# REGISTER BEGIN
# =====================
@router.post("/register/begin")
def register_begin(token: str = Cookie(None)):

    print("Token ricevuto:", token)

    user_id = get_user_id_from_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Utente non autenticato")

    user = users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato")

    devices = user.get("mfa_devices", [])

    options, state = fido2_server.register_begin(
        {
            "id": str(user["_id"]).encode(),
            "name": user["username"],
            "displayName": user["username"]
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
def register_complete(request: Request, token: str = Cookie(None)):
    user_id = get_user_id_from_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Utente non autenticato")

    user = users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato")

    body = request.body()
    if not body:
        raise HTTPException(status_code=400, detail="Body mancante")

    credential = cbor.decode(body)
    state = user.get("mfa_challenge")
    if not state:
        raise HTTPException(status_code=400, detail="Nessuna sfida MFA in corso")

    auth_data = fido2_server.register_complete(state, credential)

    # Salva il nuovo device MFA
    devices = user.get("mfa_devices", [])
    devices.append(auth_data.credential_data)
    users.update_one(
        {"_id": user["_id"]},
        {"$set": {"mfa_devices": devices}, "$unset": {"mfa_challenge": ""}}
    )

    return {"status": "ok"}
