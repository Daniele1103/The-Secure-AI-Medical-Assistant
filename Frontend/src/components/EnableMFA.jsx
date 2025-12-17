import React, { useState } from "react";
import axios from "axios";
import CBOR from "cbor-web";
import { Card, Button, Alert, Spinner } from "react-bootstrap";

const EnableMFA = () => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState(false);

    const startMFARegistration = async () => {
        setLoading(true);
        setError("");
        setSuccess(false);

        try {
            // 1️⃣ Ottieni le opzioni dal backend
            const optionsResponse = await axios.post(
                "https://the-secure-ai-medical-assistant.onrender.com/mfa/register/begin",
                {},
                {
                    responseType: "arraybuffer",
                    withCredentials: true,
                }
            );

            const options = CBOR.decode(new Uint8Array(optionsResponse.data));

            // Converti alcune proprietà in ArrayBuffer se necessario
            options.user.id = Uint8Array.from(options.user.id);
            if (options.excludeCredentials) {
                options.excludeCredentials = options.excludeCredentials.map(cred => ({
                    ...cred,
                    id: Uint8Array.from(cred.id)
                }));
            }

            // 2️⃣ Crea la credential sul browser
            const credential = await navigator.credentials.create({ publicKey: options });

            // 3️⃣ Prepara la credential per inviarla al backend
            const credentialForBackend = {
                id: credential.id,
                rawId: new Uint8Array(credential.rawId),
                response: {
                    attestationObject: new Uint8Array(credential.response.attestationObject),
                    clientDataJSON: new Uint8Array(credential.response.clientDataJSON)
                },
                type: credential.type,
                extensions: credential.getClientExtensionResults()
            };

            // 4️⃣ Invia la credential al backend
            await axios.post(
                "https://the-secure-ai-medical-assistant.onrender.com/mfa/register/complete",
                CBOR.encode(credentialForBackend),
                {
                    headers: { "Content-Type": "application/cbor" },
                    withCredentials: true
                }
            );

            setSuccess(true);
        } catch (err) {
            console.error(err);
            setError("Si è verificato un errore durante l'attivazione della MFA.");
        } finally {
            setLoading(false);
        }
    };


    return (
        <Card className="p-4 shadow-sm">
            <h4 className="mb-3">Autenticazione a più fattori (MFA)</h4>

            <p>
                Aggiungi un ulteriore livello di sicurezza al tuo account usando
                biometria o una chiave di sicurezza hardware (FIDO2 / WebAuthn).
            </p>

            {error && <Alert variant="danger">{error}</Alert>}
            {success && (
                <Alert variant="success">
                    MFA attivata con successo!
                </Alert>
            )}

            <Button
                variant="primary"
                onClick={startMFARegistration}
                disabled={loading || success}
            >
                {loading ? (
                    <>
                        <Spinner
                            as="span"
                            animation="border"
                            size="sm"
                            className="me-2"
                        />
                        Attivazione in corso...
                    </>
                ) : (
                    "Abilita MFA"
                )}
            </Button>
        </Card>
    );
};

export default EnableMFA;
