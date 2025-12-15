import React, { useState, useRef, useEffect } from 'react';
import { Container, Button, Form, Spinner } from 'react-bootstrap';
import axios from 'axios';
import { useUser } from '../contexts/UserContext';
import ReactMarkdown from 'react-markdown';

const ChatBox = () => {
    const [input, setInput] = useState("");
    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(false);

    const messagesEndRef = useRef(null); // ref al fondo della chat

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const sendMessage = () => {
        if (!input.trim()) return;

        const messageToSend = input;   // salva prima
        const userMessage = { role: 'user', content: messageToSend };
        setMessages(prev => [...prev, userMessage]);
        setInput("");                  // resetta subito

        setLoading(true);

        axios.post("https://the-secure-ai-medical-assistant.onrender.com/letta/ask", { message: messageToSend }, { withCredentials: true })
            .then((res) => {
                const aiMessage = { role: 'ai_medical_assistant', content: res.data.response };
                setMessages(prev => [...prev, aiMessage]);
                //console.log(messages)
            })
            .catch((err) => {
                console.error(err);
                const errorMessage = { role: 'ai', content: "Errore nel server, riprova." };
                setMessages(prev => [...prev, errorMessage]);
            })
            .finally(() => {
                setLoading(false);
            });
    };


    return (
        <div className="chatbox-container mt-4">
            <div
                className="chat-messages mb-3 p-3 border rounded"
                style={{ maxHeight: "400px", overflowY: "auto", background: "#f8f9fa"}}
            >
                {messages.map((msg, idx) => (
                    <div
                        key={idx}
                        className={`d-flex mb-2 ${msg.role === 'user' ? 'justify-content-end' : 'justify-content-start'}`}
                    >
                        <div
                            className={`p-2 ${msg.role === 'user' ? 'bg-primary text-white' : 'bg-light text-dark'}`}
                            style={{ maxWidth: '70%', borderRadius: "5rem" }}
                        >
                            {msg.role === 'user' ? (
                                msg.content
                            ) : (
                                <ReactMarkdown>{msg.content}</ReactMarkdown>
                            )}
                        </div>
                    </div>
                ))}

                {loading && (
                    <div className="d-flex justify-content-start">
                        <Spinner
                            animation="border"
                            size="sm"
                            role="status"
                            className="me-2"
                        >
                            <span className="visually-hidden">Loading...</span>
                        </Spinner>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <div className="d-flex gap-2">
                <Form.Control
                    type="text"
                    placeholder="Scrivi qui..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => {
                        if (!loading && e.key === 'Enter') {
                            sendMessage();
                        }
                    }}
                />
                <Button variant="primary" onClick={sendMessage} disabled={loading}>
                    Invia
                </Button>
            </div>
        </div>
    );
};

export default ChatBox;
