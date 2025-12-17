import React, { useState } from "react";
import axios from "axios";
import { decode } from "cbor-web";
import { Card, Button, Alert, Spinner } from "react-bootstrap";

const MFALogin = ({ user_id, onSuccess }) => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

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

    const startMFA = async () => {
        setLoading(true);
        setError("");

        try {
            // 1️⃣ Ottieni le opzioni MFA dal backend
            const optionsResponse = await axios.post(
                "https://the-secure-ai-medical-assistant.onrender.com/mfa/login/begin",
                { user_id },
                { responseType: "arraybuffer", withCredentials: true }
            );

            const options = decode(new Uint8Array(optionsResponse.data));

            // Converte challenge e user ID in Uint8Array
            options.publicKey.challenge = base64UrlToUint8Array(options.publicKey.challenge);
            options.publicKey.allowCredentials = options.publicKey.allowCredentials?.map((cred) => ({
                ...cred,
                id: base64UrlToUint8Array(cred.id),
            }));

            // 2️⃣ Crea la credential sul browser
            const assertion = await navigator.credentials.get({ publicKey: options.publicKey });

            console.log(assertion)
            // 3️⃣ Prepara la credential per il backend
            const credentialForBackend = {
                user_id,
                id: assertion.id,
                rawId: uint8ArrayToBase64(new Uint8Array(assertion.rawId)),
                response: {
                    authenticatorData: uint8ArrayToBase64(new Uint8Array(assertion.response.authenticatorData)),
                    clientDataJSON: uint8ArrayToBase64(new Uint8Array(assertion.response.clientDataJSON)),
                    signature: uint8ArrayToBase64(new Uint8Array(assertion.response.signature)),
                    userHandle: assertion.response.userHandle
                        ? uint8ArrayToBase64(new Uint8Array(assertion.response.userHandle))
                        : null
                },
                type: assertion.type,
                extensions: assertion.getClientExtensionResults()
            };

            // 4️⃣ Invia la credential al backend
            await axios.post(
                "https://the-secure-ai-medical-assistant.onrender.com/mfa/login/complete",
                credentialForBackend,
                { headers: { "Content-Type": "application/json" }, withCredentials: true }
            );

            // MFA completata con successo
            onSuccess();
        } catch (err) {
            console.error(err);
            setError("Errore durante il login MFA. Riprova.");
        } finally {
            setLoading(false);
        }
    };


    return (
        <Card className="p-4 shadow-sm">
            <h4 className="mb-3">Autenticazione a più fattori (MFA)</h4>
            <p>
                Completa il login usando la tua chiave di sicurezza o biometria (FIDO2 / WebAuthn).
            </p>

            {error && <Alert variant="danger">{error}</Alert>}

            <Button
                variant="primary"
                onClick={startMFA}
                disabled={loading}
                className="w-100"
            >
                {loading ? (
                    <>
                        <Spinner as="span" animation="border" size="sm" className="me-2" />
                        Login in corso...
                    </>
                ) : (
                    "Completa MFA"
                )}
            </Button>
        </Card>
    );
};

export default MFALogin;
