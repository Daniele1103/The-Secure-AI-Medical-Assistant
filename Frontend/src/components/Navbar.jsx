import React from 'react';
import { Navbar as BootstrapNavbar, Nav, Container, Button } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';

const Navbar = () => {
    const navigate = useNavigate();

    return (
        <BootstrapNavbar bg="light" expand="lg" className="mb-4">
            <Container>
                <BootstrapNavbar.Brand>Secure AI Medical Assistant</BootstrapNavbar.Brand>
                <Nav className="ms-auto">
                    <Button variant="outline-primary" className="me-2" onClick={() => navigate('/')}>
                        Home
                    </Button>
                    <Button variant="outline-success" className="me-2" onClick={() => navigate('/login')}>
                        Login
                    </Button>
                    <Button variant="outline-secondary" onClick={() => navigate('/register')}>
                        Registrati
                    </Button>
                </Nav>
            </Container>
        </BootstrapNavbar>
    );
};

export default Navbar;
