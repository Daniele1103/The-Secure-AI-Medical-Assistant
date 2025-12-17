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

# Funzione helper per serializzare CredentialCreationOptions
def options_to_dict(options):
    return {
        "challenge": websafe_encode(options.challenge),
        "rp": {
            "name": options.rp.name,
            "id": options.rp.id
        },
        "user": {
            "id": websafe_encode(options.user.id),
            "name": options.user.name,
            "displayName": options.user.display_name
        },
        "pubKeyCredParams": [
            {"type": p.type.value, "alg": p.alg} for p in options.pub_key_cred_params
        ],
        "timeout": options.timeout,
        "excludeCredentials": [
            {
                "id": websafe_encode(c.id),
                "type": c.type.value
            } for c in options.exclude_credentials
        ],
        "authenticatorSelection": {
            "authenticatorAttachment": options.authenticator_selection.authenticator_attachment,
            "residentKey": options.authenticator_selection.resident_key.value,
            "userVerification": options.authenticator_selection.user_verification.value,
        },
        "attestation": options.attestation,
        "extensions": options.extensions,
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
    print(f"Challenge salvata per user_id {user_id}")
    print(f"Options inviate al frontend: {options}")

    return Response(
        content=cbor.encode(options_to_dict(options)),
        media_type="application/cbor"
    )
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

    # Verifica e completa la registrazione
    auth_data = fido2_server.register_complete(
        state,
        data["attestationObject"],
        data["clientDataJSON"],
    )
    print(f"Credential ID registrato (raw bytes): {auth_data.credential_data.credential_id}")
    print(f"Utente {user_id} ha completato MFA con credenziale {websafe_encode(auth_data.credential_data.credential_id)}")

    # Aggiorna database
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