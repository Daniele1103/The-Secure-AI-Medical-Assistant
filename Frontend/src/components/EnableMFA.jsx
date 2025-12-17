import React, { useState } from "react";
import axios from "axios";
import { encode, decode } from "cbor-web";
import { Card, Button, Alert, Spinner } from "react-bootstrap";

const EnableMFA = () => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState(false);


    const base64UrlToUint8Array = (base64UrlString) => {
        const padding = "=".repeat((4 - (base64UrlString.length % 4)) % 4);
        const base64 = (base64UrlString + padding).replace(/-/g, "+").replace(/_/g, "/");
        const rawData = atob(base64);
        return Uint8Array.from([...rawData].map((c) => c.charCodeAt(0)));
    };

    const uint8ArrayToBase64 = (arr) => {
        const str = String.fromCharCode.apply(null, arr);
        return btoa(str)
            .replace(/\+/g, "-")
            .replace(/\//g, "_")
            .replace(/=+$/, "");
    };

    const startMFARegistration = async () => {
        setLoading(true);
        setError("");
        setSuccess(false);

        try {
            // 1️⃣ Ottieni le opzioni dal backend
            const optionsResponse = await axios.post(
                "https://the-secure-ai-medical-assistant.onrender.com/mfa/register/begin",
                undefined, // nessun body
                {
                    responseType: "arraybuffer",
                    withCredentials: true,
                }
            );

            // Decodifica CBOR
            const options = decode(new Uint8Array(optionsResponse.data));
            console.log("options:", options);

            // 2️⃣ Converte challenge e user.id in Uint8Array
            options.publicKey.challenge = base64UrlToUint8Array(options.publicKey.challenge);
            options.publicKey.user.id = base64UrlToUint8Array(options.publicKey.user.id);

            // 3️⃣ Converte excludeCredentials se presenti
            if (options.publicKey.excludeCredentials) {
                options.publicKey.excludeCredentials = options.publicKey.excludeCredentials.map((cred) => ({
                    ...cred,
                    id: base64UrlToUint8Array(cred.id),
                }));
            }
            console.log(window.location.hostname);
            console.log(options.publicKey.rp.id);

            // 4️⃣ Crea la credential sul browser
            const credential = await navigator.credentials.create({ publicKey: options.publicKey });    //non prende ip numerici

            // 5️⃣ Prepara la credential per il backend
            const credentialForBackend = {
                id: credential.id,
                rawId: uint8ArrayToBase64(new Uint8Array(credential.rawId)),
                response: {
                    attestationObject: uint8ArrayToBase64(new Uint8Array(credential.response.attestationObject)),
                    clientDataJSON: uint8ArrayToBase64(new Uint8Array(credential.response.clientDataJSON))
                },
                type: credential.type,
                extensions: credential.getClientExtensionResults()
            };

            // 6️⃣ Invia la credential al backend
            await axios.post(
                "https://the-secure-ai-medical-assistant.onrender.com/mfa/register/complete",
                credentialForBackend,
                {
                    headers: { "Content-Type": "application/json" },
                    withCredentials: true,
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
