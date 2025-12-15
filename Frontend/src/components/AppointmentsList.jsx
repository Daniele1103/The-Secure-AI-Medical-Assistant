import React, { useEffect, useState } from 'react';
import { ListGroup, Spinner, Button } from 'react-bootstrap';
import axios from 'axios';

const AppointmentsList = () => {
    const [appointments, setAppointments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchAppointments = () => {
        setLoading(true);
        setError(null);

        axios.get('https://the-secure-ai-medical-assistant.onrender.com/frontend/my-appointments', { withCredentials: true })
            .then((response) => {
                const appts = response.data.appointments || [];
                setAppointments(appts);
            })
            .catch(() => {
                setError('Errore nel recupero degli appuntamenti');
            })
            .finally(() => {
                setLoading(false);
            });
    };

    useEffect(() => {
        fetchAppointments();
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
        return (
            <div className="p-3 text-center">
                Nessun appuntamento disponibile.
                <div className="mt-3">
                    <Button onClick={fetchAppointments}>Ricarica</Button>
                </div>
            </div>
        );
    }

    return (
        <div className="p-3">
            <h4 className="mb-4 text-center">I tuoi Appuntamenti</h4>

            <div
                style={{
                    maxHeight: '400px', // Altezza massima della lista (puoi regolare)
                    overflowY: 'auto',
                }}
            >
                <ListGroup>
                    {appointments.map((appt) => (
                        <ListGroup.Item
                            key={appt.appointment_id}
                            className="d-flex justify-content-start align-items-center mb-2 p-3 gap-4"
                            style={{
                                borderRadius: '0.75rem',
                                boxShadow: '0 2px 6px rgba(0,0,0,0.1)',
                                backgroundColor: '#f8f9fa'
                            }}
                        >
                            <div><strong>ID:</strong> {appt.appointment_id}</div>
                            <div><strong>Data:</strong> {appt.date}</div>
                            <div><strong>Ora:</strong> {appt.time}</div>
                        </ListGroup.Item>
                    ))}
                </ListGroup>
            </div>

            <div className="mt-3 text-center">
                <Button onClick={fetchAppointments} disabled={loading}>
                    {loading ? 'Caricamento...' : 'Ricarica'}
                </Button>
            </div>
        </div>
    );

};

export default AppointmentsList;
