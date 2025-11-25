import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Container, Button } from 'react-bootstrap';

import Navbar from './components/Navbar';
import Login from './pages/User/Login';
import Register from './pages/User/Register';

import { UserProvider, useUser } from './contexts/UserContext';

const InnerHome = () => {
    const { isLoggedIn, isLoading } = useUser();

    if (isLoading) {
        return (
            <Container fluid className="vh-100 d-flex justify-content-center align-items-center">
                <div className="spinner-border text-primary" role="status">
                    <span className="visually-hidden">Loading...</span>
                </div>
            </Container>
        );
    }

    return (
        <>
            <Navbar />
            <Container className="p-3 text-center mt-5">
                <Routes>
                    <Route
                        path="/"
                        element={
                            <div>
                                {!isLoggedIn ? (
                                    <div className="text-center mt-5">
                                        <h3>Per favore effettua il login per usare l'assistente AI.</h3>
                                    </div>
                                ) : (
                                    <div className="text-center mt-5">
                                        <h1>Benvenuto!</h1>
                                        <p className="lead">Scrivi qualcosa al tuo assistente AI:</p>
                                        <div className="d-flex justify-content-center gap-2 mt-3">
                                            <input
                                                type="text"
                                                placeholder="Scrivi qui..."
                                                className="form-control w-50"
                                            />
                                            <Button variant="primary">Invia</Button>
                                        </div>
                                    </div>
                                )}
                            </div>
                        }
                    />
                    <Route
                        path="/login"
                        element={isLoggedIn ? <Navigate to="/" replace /> : <Login />}
                    />
                    <Route
                        path="/register"
                        element={isLoggedIn ? <Navigate to="/" replace /> : <Register />}
                    />
                </Routes>
            </Container>
        </>
    );
};


const Home = () => (
    <Router>
        <UserProvider>
            <InnerHome />
        </UserProvider>
    </Router>
);

export default Home;
