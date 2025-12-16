import React, { useState } from "react";
import axios from "axios";
import { Card, Button, Alert, Spinner } from "react-bootstrap";

const MFALogin = ({ userId, onSuccess }) => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const startMFA = () => {
        setLoading(true);
        setError("");

        // 1️⃣ Chiedi al backend la challenge MFA
        axios.post(
            "https://the-secure-ai-medical-assistant.onrender.com/mfa/login/begin",
            { user_id: userId },
            { withCredentials: true }
        )
            .then((res) => {
                const options = res.data;

                // Conversioni Base64 → ArrayBuffer
                options.challenge = Uint8Array.from(atob(options.challenge), c => c.charCodeAt(0));

                if (options.allowCredentials) {
                    options.allowCredentials = options.allowCredentials.map(cred => ({
                        ...cred,
                        id: Uint8Array.from(atob(cred.id), c => c.charCodeAt(0))
                    }));
                }

                // 2️⃣ Chiamata WebAuthn API
                return navigator.credentials.get({ publicKey: options });
            })
            .then((assertion) => {
                // 3️⃣ Prepara dati per il backend
                const credentialData = {
                    id: assertion.id,
                    rawId: btoa(String.fromCharCode(...new Uint8Array(assertion.rawId))),
                    type: assertion.type,
                    response: {
                        authenticatorData: btoa(String.fromCharCode(...new Uint8Array(assertion.response.authenticatorData))),
                        clientDataJSON: btoa(String.fromCharCode(...new Uint8Array(assertion.response.clientDataJSON))),
                        signature: btoa(String.fromCharCode(...new Uint8Array(assertion.response.signature))),
                        userHandle: assertion.response.userHandle ? btoa(String.fromCharCode(...new Uint8Array(assertion.response.userHandle))) : null
                    }
                };

                // 4️⃣ Completa login MFA
                return axios.post(
                    "https://the-secure-ai-medical-assistant.onrender.com/mfa/login/complete",
                    { user_id: userId, credential: credentialData },
                    { withCredentials: true }
                );
            })
            .then(() => {
                // MFA completata con successo
                if (onSuccess) onSuccess();
            })
            .catch((err) => {
                console.error(err);
                setError(err.response?.data?.detail || "Errore durante il login MFA");
            })
            .finally(() => {
                setLoading(false);
            });
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
