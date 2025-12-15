import React, { useEffect, useState } from 'react';
import { ListGroup, Spinner } from 'react-bootstrap';
import axios from 'axios';

const AppointmentsList = () => {
    const [appointments, setAppointments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        axios.get('https://the-secure-ai-medical-assistant.onrender.com/frontend/my-appointments', { withCredentials: true }) // Usa il nuovo endpoint frontend
            .then((response) => {
                const appts = response.data.appointments || [];
                setAppointments(appts);
            })
            .catch((err) => {
                setError('Errore nel recupero degli appuntamenti');
            })
            .finally(() => {
                setLoading(false);
            });
    }, []);

    if (loading) {
        return (
            <div className="d-flex justify-content-center align-items-center p-3">
                <Spinner animation="border" variant="primary" />
            </div>
        );
    }

    if (error) {
        return <div className="text-danger p-3">{error}</div>;
    }

    if (appointments.length === 0) {
        return <div className="p-3">Nessun appuntamento disponibile.</div>;
    }

    return (
        <ListGroup className="p-3">
            {appointments.map((appt) => (
                <ListGroup.Item key={appt.appointment_id}>
                    <strong>{appt.date}</strong> - {appt.time}
                </ListGroup.Item>
            ))}
        </ListGroup>
    );
};

export default AppointmentsList;
