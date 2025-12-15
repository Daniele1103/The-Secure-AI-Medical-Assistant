import React from 'react';
import { Navbar as BootstrapNavbar, Nav, Container, Button } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import { useUser } from '../contexts/UserContext';
import axios from 'axios';

const Navbar = () => {
    const navigate = useNavigate();
    const { isLoggedIn, setIsLoggedIn, setPayload, payload } = useUser();

    const handleLogout = () => {
        axios.post('https://the-secure-ai-medical-assistant.onrender.com/auth/logout', {}, { withCredentials: true })
            .then(() => {
                setIsLoggedIn(false);
                setPayload(null);
            })
            .finally(() => {
                navigate('/login')
            });
    };

    return (
        <BootstrapNavbar bg="light" expand="lg" className="mb-4">
            <Container>
                <BootstrapNavbar.Brand>Secure AI Medical Assistant</BootstrapNavbar.Brand>
                <Nav className="ms-auto">
                    {isLoggedIn && payload ? (
                        <div className="d-flex align-items-center gap-3">
                            <div className="text-muted text-end">
                                <div><strong>User ID:</strong> {payload.sub}</div>
                                <div><strong>Email:</strong> {payload.email}</div>
                            </div>
                            <Button variant="danger" onClick={handleLogout}>
                                Logout
                            </Button>
                        </div>
                    ) : (
                        <>
                            <Button variant="outline-success" className="me-2" onClick={() => navigate('/login')}>
                                Login
                            </Button>
                            <Button variant="outline-secondary" onClick={() => navigate('/register')}>
                                Registrati
                            </Button>
                        </>
                    )}
                </Nav>
            </Container>
        </BootstrapNavbar>
    );
};

export default Navbar;
