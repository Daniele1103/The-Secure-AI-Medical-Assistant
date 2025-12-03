import React, { useState } from 'react';
import axios from 'axios';
import { Container, Row, Col, Form, Button } from 'react-bootstrap';

const Register = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();

        if (password !== confirmPassword) {
            alert("Le password non corrispondono!");
            return;
        }

        axios.post(`http://127.0.0.1:8000/auth/register`, 
            { email, password },
            { headers: { "Content-Type": "application/json" } }
        )
        .then(response => {
            alert(response.data.message || "Registrazione completata!");
            setEmail('');
            setPassword('');
            setConfirmPassword('');
        })
        .catch(error => {
            console.error("Errore:", error);
            if (error.response && error.response.data) {
                alert(error.response.data.detail || "Errore durante la registrazione");
            } else {
                alert("Errore di connessione al server");
            }
        });
    };

    return (
        <Container className="mt-5">
            <Row className="justify-content-md-center">
                <Col md={6}>
                    <h2 className="mb-4 text-center">Registrati</h2>
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

                        <Form.Group className="mb-3" controlId="formConfirmPassword">
                            <Form.Label>Conferma Password</Form.Label>
                            <Form.Control
                                type="password"
                                placeholder="Conferma Password"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                required
                            />
                        </Form.Group>

                        <Button variant="success" type="submit" className="w-100">
                            Registrati
                        </Button>
                    </Form>
                </Col>
            </Row>
        </Container>
    );
};

export default Register;
