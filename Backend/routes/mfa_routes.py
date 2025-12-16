from fido2.utils import websafe_encode
from fido import fido2_server
from fido2.utils import websafe_decode
import time
from bson import ObjectId
from fastapi import APIRouter, Request, HTTPException, Response
from db import users
from fido2.utils import websafe_encode, websafe_decode
from auth import hash_password, verify_password, create_access_token, decode_access_token

mfa_challenges = {}  # TEMP: in prod redis
mfa_login_challenges = {}

router = APIRouter(prefix="/mfa", tags=["Mfa"])

@router.post("/register/begin")
async def mfa_register_begin(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Non autenticato")

    payload = decode_access_token(token)
    user_id = payload["sub"]

    user = users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato")

    registration_data, state = fido2_server.register_begin(
        {
            "id": user_id.encode(),
            "name": user["email"],
            "displayName": user["email"],
        },
        user.get("webauthn_credentials", []),
        user_verification="preferred",
    )

    mfa_challenges[user_id] = {
        "state": state,
        "created_at": time.time()
    }

    registration_data["challenge"] = websafe_encode(
        registration_data["challenge"]
    ).decode()

    registration_data["user"]["id"] = websafe_encode(
        registration_data["user"]["id"]
    ).decode()

    return registration_data

@router.post("/register/complete")
async def mfa_register_complete(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Non autenticato")

    payload = decode_access_token(token)
    user_id = payload["sub"]

    body = await request.json()
    challenge = mfa_challenges.get(user_id)
    if not challenge:
        raise HTTPException(status_code=400, detail="Challenge scaduta")

    credential = fido2_server.register_complete(
        challenge["state"],
        {
            "id": body["id"],
            "rawId": websafe_decode(body["rawId"]),
            "type": body["type"],
            "response": {
                "attestationObject": websafe_decode(
                    body["response"]["attestationObject"]
                ),
                "clientDataJSON": websafe_decode(
                    body["response"]["clientDataJSON"]
                )
            }
        }
    )

    users.update_one(
        {"_id": ObjectId(user_id)},
        {
            "$push": {
                "webauthn_credentials": {
                    "credential_id": credential.credential_id,
                    "public_key": credential.public_key,
                    "sign_count": credential.sign_count
                }
            },
            "$set": {"mfa_enabled": True}
        }
    )

    del mfa_challenges[user_id]

    return {"message": "MFA attivata con successo"}


@router.post("/login/begin")
async def mfa_login_begin(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id richiesto")

    user = users.find_one({"_id": ObjectId(user_id)})
    if not user or not user.get("mfa_enabled", False):
        raise HTTPException(status_code=400, detail="Utente non trovato o MFA non attivo")

    credentials = user.get("webauthn_credentials", [])

    # Genera la challenge di login (assertion)
    login_data, state = fido2_server.authenticate_begin(
        credentials,
        user_verification="preferred"
    )

    # Salva temporaneamente lo state
    mfa_login_challenges[user_id] = {
        "state": state,
        "created_at": time.time()
    }

    # Conversione Base64
    for cred in login_data.get("allowCredentials", []):
        cred["id"] = websafe_encode(cred["id"]).decode()

    login_data["challenge"] = websafe_encode(login_data["challenge"]).decode()

    return login_data

@router.post("/login/complete")
async def mfa_login_complete(request: Request, response: Response):
    data = await request.json()
    user_id = data.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id richiesto")

    challenge = mfa_login_challenges.get(user_id)
    if not challenge:
        raise HTTPException(status_code=400, detail="Challenge MFA scaduta")

    user = users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato")

    # Verifica l'assertion inviata dal dispositivo
    credential_response = data.get("credential")
    if not credential_response:
        raise HTTPException(status_code=400, detail="Credential mancante")

    credential_id = websafe_decode(credential_response["rawId"])
    credential_data = {
        "id": credential_response["id"],
        "rawId": credential_id,
        "type": credential_response["type"],
        "response": {
            "authenticatorData": websafe_decode(credential_response["response"]["authenticatorData"]),
            "clientDataJSON": websafe_decode(credential_response["response"]["clientDataJSON"]),
            "signature": websafe_decode(credential_response["response"]["signature"]),
            # opzionale: userHandle se presente
            "userHandle": websafe_decode(credential_response["response"]["userHandle"]) if credential_response["response"].get("userHandle") else None
        }
    }

    assertion = fido2_server.authenticate_complete(
        challenge["state"],
        user.get("webauthn_credentials", []),
        credential_data
    )

    # Controllo sign_count e aggiornamento DB
    for cred in user.get("webauthn_credentials", []):
        if cred["credential_id"] == assertion.credential.credential_id:
            if assertion.sign_count <= cred["sign_count"]:
                raise HTTPException(status_code=400, detail="Possibile replay attack!")
            cred["sign_count"] = assertion.sign_count
            break

    # Aggiorna DB
    users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"webauthn_credentials": user["webauthn_credentials"]}}
    )

    # Elimina challenge temporanea
    del mfa_login_challenges[user_id]

    # Genera JWT e lo invia in cookie HttpOnly
    token = create_access_token({
        "sub": str(user["_id"]),
        "email": user["email"]
    })

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,  # True in produzione HTTPS
        samesite="none",
        max_age=3600
    )

    return {"message": "Login MFA completato"}