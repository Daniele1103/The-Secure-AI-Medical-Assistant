from fido2.utils import websafe_encode
from fido import fido2_server
from bson import ObjectId
from fastapi import APIRouter, Cookie, HTTPException, Response
from db import users
from auth import get_user_id_from_token
from fido2 import cbor

router = APIRouter(prefix="/mfa", tags=["Mfa"])

# Stato temporaneo WebAuthn (in memoria)
_mfa_states = {}

# ----------------------------
# Helper per serializzare CredentialCreationOptions
# ----------------------------
def options_to_dict(options):
    pk = options.public_key  # qui sono tutti i campi che il browser si aspetta

    return {
        "challenge": websafe_encode(pk.challenge),
        "rp": {
            "name": pk.rp.name,
            "id": pk.rp.id
        },
        "user": {
            "id": websafe_encode(pk.user.id),
            "name": pk.user.name,
            "displayName": pk.user.display_name
        },
        "pubKeyCredParams": [
            {"type": p.type.value, "alg": p.alg} for p in pk.pub_key_cred_params
        ],
        "timeout": pk.timeout,
        "excludeCredentials": [
            {
                "id": websafe_encode(c.id),
                "type": c.type.value
            } for c in pk.exclude_credentials
        ],
        "authenticatorSelection": {
            "authenticatorAttachment": pk.authenticator_selection.authenticator_attachment,
            "residentKey": pk.authenticator_selection.resident_key.value,
            "userVerification": pk.authenticator_selection.user_verification.value,
        },
        "attestation": pk.attestation,
        "extensions": pk.extensions,
    }

# ----------------------------
# BEGIN REGISTRATION
# ----------------------------
@router.post("/register/begin")
async def mfa_register_begin(access_token: str = Cookie(None)):
    print("===== BEGIN MFA REGISTRATION =====")
    
    if not access_token:
        raise HTTPException(status_code=401, detail="Token mancante")

    user_id = get_user_id_from_token(access_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Token non valido")

    print(f"user_id estratto dal token: {user_id}")

    user = users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    print(f"Utente trovato: {user['email']} ({user_id})")

    # Genera challenge e opzioni WebAuthn
    options, state = fido2_server.register_begin(
        {
            "id": str(user["_id"]).encode(),
            "name": user["email"],
            "displayName": user["email"],
        },
        user.get("mfa_credentials", []),
        user_verification="preferred",
    )

    # Salva lo stato temporaneo
    _mfa_states[user_id] = state
    print(f"Challenge salvata in memoria per user_id {user_id}")
    print(f"Options inviate al frontend: {options}")

    return Response(
        content=cbor.encode(options_to_dict(options)),
        media_type="application/cbor"
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

    # Decodifica CBOR ricevuto dal frontend
    data = cbor.decode(raw)
    print(f"Dati ricevuti dal frontend per user_id {user_id}: {list(data.keys())}")

    # Completa la registrazione FIDO2
    auth_data = fido2_server.register_complete(
        state,
        data["attestationObject"],
        data["clientDataJSON"],
    )

    print(f"Credential ID registrato (raw bytes): {auth_data.credential_data.credential_id}")
    print(f"Utente {user_id} ha completato MFA con credenziale {websafe_encode(auth_data.credential_data.credential_id)}")

    # Salva credenziali e abilita MFA nel database
    users.update_one(
        {"_id": ObjectId(user_id)},
        {
            "$set": {"mfa_enabled": True},
            "$push": {"mfa_credentials": auth_data.credential_data},
        },
    )
    print(f"Database aggiornato: MFA abilitata e credenziali salvate per user_id {user_id}")

    # Rimuove lo stato temporaneo
    del _mfa_states[user_id]
    print(f"Stato temporaneo MFA rimosso per user_id {user_id}")

    return {"status": "mfa_registered"}
