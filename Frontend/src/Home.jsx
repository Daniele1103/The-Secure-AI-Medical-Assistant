import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Container, Button } from 'react-bootstrap';
import axios from 'axios';

import Navbar from './components/Navbar';
import ChatBox from './components/ChatBox';
import AppointmentsList from './components/AppointmentsList';
import Login from './pages/User/Login';
import Register from './pages/User/Register';

import { UserProvider, useUser } from './contexts/UserContext';

const InnerHome = () => {
    const { isLoggedIn, setIsLoggedIn, isLoading, setPayload, payload } = useUser();

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
                            !isLoggedIn ? (
                                <div className="text-center mt-5">
                                    <h3>Per favore effettua il login per usare l'assistente AI.</h3>
                                </div>
                            ) : (
                                <div className="d-flex gap-4">
                                    <div style={{ flex: 1 }}>
                                        <AppointmentsList />
                                    </div>
                                    <div style={{ flex: 3, paddingLeft: '15px' }}>
                                        <ChatBox />
                                    </div>
                                </div>
                            )
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
