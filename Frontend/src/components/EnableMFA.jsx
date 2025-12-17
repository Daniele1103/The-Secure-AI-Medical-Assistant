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
            // 1️⃣ BEGIN REGISTRATION
            const beginRes = await axios.post(
                "https://the-secure-ai-medical-assistant.onrender.com/mfa/register/begin",
                {},
                {
                    responseType: "arraybuffer",
                    withCredentials: true,
                }
            );

            const publicKey = CBOR.decode(
                new Uint8Array(beginRes.data)
            );

            // 2️⃣ CREATE CREDENTIAL
            const credential = await navigator.credentials.create({
                publicKey,
            });

            // 3️⃣ COMPLETE REGISTRATION
            await axios.post(
                "https://the-secure-ai-medical-assistant.onrender.com/mfa/register/complete",
                CBOR.encode({
                    attestationObject: new Uint8Array(
                        credential.response.attestationObject
                    ),
                    clientDataJSON: new Uint8Array(
                        credential.response.clientDataJSON
                    ),
                }),
                {
                    headers: {
                        "Content-Type": "application/cbor",
                    },
                    withCredentials: true,
                }
            );

            setSuccess(true);
        } catch (err) {
            console.error(err);
            setError(
                err?.response?.data?.detail ||
                err?.message ||
                "Errore durante la registrazione MFA"
            );
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
