import React, { useState } from 'react';
import { Container, Row, Col, Form, Button, Alert } from 'react-bootstrap';
import axios from 'axios';
import { useUser } from '../../contexts/UserContext';
import MFALogin from './MFALogin';

const Login = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [showMFALogin, setShowMFALogin] = useState(false);

    const { setIsLoggedIn, setPayload, setIsLoading } = useUser();

    const refreshPayload = () => {
        axios.get('https://the-secure-ai-medical-assistant.onrender.com/auth/me', { withCredentials: true })
            .then((response) => {
                if (response.data.logged_in) {
                    setPayload(response.data.user);
                    setIsLoggedIn(true);
                } else {
                    setPayload(null);
                    setIsLoggedIn(false);
                }
            })
            .catch(() => {
                setPayload(null);
                setIsLoggedIn(false);
            })
            .finally(() => setIsLoading(false));
    }

    const handleSubmit = (e) => {
        e.preventDefault();
        setError('');

        axios.post('https://the-secure-ai-medical-assistant.onrender.com/auth/login',
            { email, password },
            { withCredentials: true }
        )
            .then((response) => {
                if (response.data.mfa_required) {
                    // Mostra il componente MFA
                    setShowMFALogin(true);
                    setUserId(response.data.user_id);
                } else {
                    // Login normale completato
                    setIsLoggedIn(true);
                    refreshPayload();
                }
            })
            .catch((err) => {
                if (err.response?.data?.detail) setError(err.response.data.detail);
                else setError('Errore di connessione al server');
            });
    };

    return (
        <Container className="mt-5">
            <Row className="justify-content-md-center">
                <Col md={6}>
                    <h2 className="mb-4 text-center">Login</h2>

                    {error && <Alert variant="danger">{error}</Alert>}

                    {!showMFALogin && (
                        <Form onSubmit={handleSubmit}>
                            <Form.Group className="mb-3" controlId="formEmail">
                                <Form.Label>Email</Form.Label>
                                <Form.Control
                                    type="email"
                                    placeholder="Inserisci email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    required
                                />
                            </Form.Group>

                            <Form.Group className="mb-3" controlId="formPassword">
                                <Form.Label>Password</Form.Label>
                                <Form.Control
                                    type="password"
                                    placeholder="Password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    required
                                />
                            </Form.Group>

                            <Button variant="primary" type="submit" className="w-100">
                                Accedi
                            </Button>
                        </Form>
                    )}

                    {showMFALogin && (
                        <MFALogin
                            userId={email}
                            onSuccess={() => {
                                setShowMFALogin(false);
                                refreshPayload();
                            }}
                        />
                    )}
                </Col>
            </Row>
        </Container>
    );
};

export default Login;
