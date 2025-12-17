# fido.py
from fido2.server import Fido2Server
from fido2.webauthn import PublicKeyCredentialRpEntity

RP_ID = "127.0.0.1"

rp = PublicKeyCredentialRpEntity(
    id=RP_ID,
    name="Secure AI Medical Assistant"
)

fido2_server = Fido2Server(rp)
