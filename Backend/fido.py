# fido.py
from fido2.server import Fido2Server
from fido2.webauthn import PublicKeyCredentialRpEntity

RP_ID = "localhost"

# Definisce l’identità dell’applicazione che utilizza WebAuthn (nome e ID mostrati all’utente durante la registrazione/autenticazione della passkey)
rp = PublicKeyCredentialRpEntity(
    id=RP_ID,           # Identifica la Relying Party, cioè il dominio che richiede l’autenticazione (in questo caso localhost, usato per sviluppo)
    name="Secure AI Medical Assistant"
)

fido2_server = Fido2Server(rp)
