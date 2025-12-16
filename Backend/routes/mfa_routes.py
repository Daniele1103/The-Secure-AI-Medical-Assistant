from fido2.utils import websafe_encode, websafe_decode
from fido import fido2_server
import time
from bson import ObjectId
from fastapi import APIRouter, Request, HTTPException, Response
from db import users
from auth import create_access_token, decode_access_token

mfa_challenges = {}       # TEMP: in prod usa Redis
mfa_login_challenges = {}

router = APIRouter(prefix="/mfa", tags=["Mfa"])


@router.post("/register/begin")
async def mfa_register_begin(request: Request):
    # Recupera token dal cookie
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Non autenticato")

    payload = decode_access_token(token)
    user_id = payload["sub"]

    # Recupera utente dal DB
    user = users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato")

    # Genera challenge WebAuthn
    registration_data, state = fido2_server.register_begin(
        {
            "id": str(user_id).encode(),
            "name": user["email"],
            "displayName": user["email"],
        },
        user.get("webauthn_credentials", []),
        user_verification="preferred",
    )

    # Salva challenge temporaneamente
    mfa_challenges[user_id] = {
        "state": state,
        "created_at": time.time()
    }

    # Converte in dict JSON-friendly
    registration_dict = {
        "challenge": websafe_encode(registration_data.public_key.challenge).decode(),
        "user": {
            "id": websafe_encode(registration_data.public_key.user.id).decode(),
            "name": registration_data.public_key.user.name,
            "displayName": registration_data.public_key.user.display_name,
        },
        "pubKeyCredParams": [
            {"type": param.type.value, "alg": param.alg}
            for param in registration_data.public_key.pub_key_cred_params
        ],
        "timeout": registration_data.public_key.timeout,
        "excludeCredentials": [
            {
                "id": websafe_encode(cred.id).decode(),
                "type": cred.type.value
            } for cred in registration_data.public_key.exclude_credentials
        ],
        "authenticatorSelection": {
            "authenticatorAttachment": getattr(registration_data.public_key.authenticator_selection, "authenticator_attachment", None),
            "residentKey": registration_data.public_key.authenticator_selection.resident_key.value,
            "userVerification": registration_data.public_key.authenticator_selection.user_verification.value
        },
        "attestation": registration_data.public_key.attestation.value if registration_data.public_key.attestation else None
    }

    return registration_dict


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
                "attestationObject": websafe_decode(body["response"]["attestationObject"]),
                "clientDataJSON": websafe_decode(body["response"]["clientDataJSON"])
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

    login_data, state = fido2_server.authenticate_begin(
        credentials,
        user_verification="preferred"
    )

    mfa_login_challenges[user_id] = {
        "state": state,
        "created_at": time.time()
    }

    # Base64 encode per il frontend
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
            "userHandle": websafe_decode(credential_response["response"]["userHandle"]) if credential_response["response"].get("userHandle") else None
        }
    }

    assertion = fido2_server.authenticate_complete(
        challenge["state"],
        user.get("webauthn_credentials", []),
        credential_data
    )

    # Controllo sign_count
    for cred in user.get("webauthn_credentials", []):
        if cred["credential_id"] == assertion.credential.credential_id:
            if assertion.sign_count <= cred["sign_count"]:
                raise HTTPException(status_code=400, detail="Possibile replay attack!")
            cred["sign_count"] = assertion.sign_count
            break

    users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"webauthn_credentials": user["webauthn_credentials"]}}
    )

    del mfa_login_challenges[user_id]

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
