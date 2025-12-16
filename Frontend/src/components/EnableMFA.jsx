import React, { useState } from "react";
import axios from "axios";
import { Card, Button, Alert, Spinner } from "react-bootstrap";

const EnableMFA = () => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState(false);

    const startMFARegistration = () => {
        setLoading(true);
        setError("");
        setSuccess(false);

        // 1️⃣ Chiedi al backend la challenge WebAuthn
        axios.post(
            "https://the-secure-ai-medical-assistant.onrender.com/mfa/register/begin",
            {},
            { withCredentials: true }
        )
            .then((beginRes) => {
                const options = beginRes.data;

                // 2️⃣ Conversioni Base64 → ArrayBuffer
                options.challenge = Uint8Array.from(
                    atob(options.challenge),
                    c => c.charCodeAt(0)
                );

                options.user.id = Uint8Array.from(
                    atob(options.user.id),
                    c => c.charCodeAt(0)
                );

                if (options.excludeCredentials) {
                    options.excludeCredentials = options.excludeCredentials.map(cred => ({
                        ...cred,
                        id: Uint8Array.from(atob(cred.id), c => c.charCodeAt(0))
                    }));
                }

                // 3️⃣ WebAuthn API
                return navigator.credentials.create({
                    publicKey: options
                });
            })
            .then((credential) => {
                // 4️⃣ Prepara risposta per il backend
                const credentialData = {
                    id: credential.id,
                    rawId: btoa(
                        String.fromCharCode(...new Uint8Array(credential.rawId))
                    ),
                    type: credential.type,
                    response: {
                        attestationObject: btoa(
                            String.fromCharCode(
                                ...new Uint8Array(credential.response.attestationObject)
                            )
                        ),
                        clientDataJSON: btoa(
                            String.fromCharCode(
                                ...new Uint8Array(credential.response.clientDataJSON)
                            )
                        )
                    }
                };

                // 5️⃣ Completa registrazione
                return axios.post(
                    "https://the-secure-ai-medical-assistant.onrender.com/mfa/register/complete",
                    credentialData,
                    { withCredentials: true }
                );
            })
            .then(() => {
                setSuccess(true);
            })
            .catch((err) => {
                console.error(err);
                setError(
                    err.response?.data?.detail ||
                    "Errore durante l'attivazione dell'MFA"
                );
            })
            .finally(() => {
                setLoading(false);
            });
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
