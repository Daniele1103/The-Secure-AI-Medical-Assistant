import React from 'react';
import { Navbar as BootstrapNavbar, Nav, Container, Button } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import { useUser } from '../contexts/UserContext';
import axios from 'axios';

const Navbar = () => {
    const navigate = useNavigate();
    const { isLoggedIn, setIsLoggedIn, setPayload } = useUser();

    const handleLogout = () => {
        axios.post('http://127.0.0.1:8000/auth/logout', {}, { withCredentials: true })
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
                    {isLoggedIn ? (
                        <Button variant="danger" onClick={handleLogout}>
                            Logout
                        </Button>
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
