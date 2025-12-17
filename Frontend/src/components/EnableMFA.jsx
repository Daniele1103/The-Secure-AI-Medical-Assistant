import React, { useState } from "react";
import axios from "axios";
import { encode, decode } from "cbor-web";
import { Card, Button, Alert, Spinner } from "react-bootstrap";

const EnableMFA = () => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState(false);


    function bufferToBase64url(buffer) {
        return btoa(
            String.fromCharCode(...new Uint8Array(buffer))
        )
            .replace(/\+/g, "-")
            .replace(/\//g, "_")
            .replace(/=+$/, "");
    }
    function base64UrlToUint8Array(base64urlString) {
        const padding = "=".repeat((4 - (base64urlString.length % 4)) % 4);
        const base64 = (base64urlString + padding).replace(/-/g, "+").replace(/_/g, "/");
        const raw = atob(base64);
        const buffer = new Uint8Array(raw.length);
        for (let i = 0; i < raw.length; i++) {
            buffer[i] = raw.charCodeAt(i);
        }
        return buffer;
    }

    const startMFARegistration = async () => {
        setLoading(true);
        setError("");
        setSuccess(false);

        try {
            const optionsResponse = await axios.post(
                "https://the-secure-ai-medical-assistant.onrender.com/mfa/register/begin",
                undefined,
                {
                    responseType: "arraybuffer",
                    withCredentials: true,
                }
            );
            console.log(optionsResponse.headers["content-type"]);
            console.log(optionsResponse.data instanceof ArrayBuffer);

            const options = decode(new Uint8Array(optionsResponse.data));
            console.log("options:", options);


            options.publicKey.challenge = base64UrlToUint8Array(options.publicKey.challenge);
            options.publicKey.user.id = base64UrlToUint8Array(options.publicKey.user.id);

            // Se ci sono excludeCredentials
            if (options.publicKey.excludeCredentials) {
                options.publicKey.excludeCredentials = options.publicKey.excludeCredentials.map((c) => ({
                    ...c,
                    id: base64UrlToUint8Array(c.id),
                }));
            }
            const credential = await navigator.credentials.create({ publicKey: options.publicKey });    //non prende ip numerici

            const payload = {
                id: credential.id,
                rawId: bufferToBase64url(credential.rawId),
                type: credential.type,
                response: {
                    attestationObject: bufferToBase64url(
                        credential.response.attestationObject
                    ),
                    clientDataJSON: bufferToBase64url(
                        credential.response.clientDataJSON
                    )
                }
            };

            await axios.post(
                "https://the-secure-ai-medical-assistant.onrender.com/mfa/register/complete",
                payload,
                {
                    withCredentials: true
                }
            );


            setSuccess(true);
        } catch (err) {
            console.error(err);
            setError("Si è verificato un errore durante l'attivazione della MFA.");
        } finally {
            deleteChallenge();
            setLoading(false);
        }
    };

    const deleteChallenge = () => {
        axios.post(
            "https://the-secure-ai-medical-assistant.onrender.com/mfa/register/cancel",
            {},
            { withCredentials: true }
        )
            .then(() => {
                console.log("Challenge cancellata correttamente");
            })
            .catch((e) => {
                console.warn("Impossibile cancellare la challenge:", e);
            });
    }


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
