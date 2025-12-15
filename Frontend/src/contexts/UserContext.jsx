import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

export const UserContext = createContext();

export const UserProvider = ({ children }) => {
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [payload, setPayload] = useState(null);

    useEffect(() => {
        // Chiamata al backend per verificare il token nel cookie HttpOnly
        axios.get('https://the-secure-ai-medical-assistant.onrender.com/auth/me', { withCredentials: true })
            .then((response) => {
                console.log(response)
                if (response.data.logged_in) {
                    setPayload(response.data.user);
                    setIsLoggedIn(true);
                    //console.log(response.data.user)
                } else {
                    setPayload(null);
                    setIsLoggedIn(false);
                }
            })
            .catch(() => {
                setIsLoggedIn(false);
                setPayload(null);
            })
            .finally(() => {
                setIsLoading(false);
            });
    }, []);
    /*
        useEffect(() => {
            console.log("payload aggiornato:", payload);
        }, [payload]);
    */
    const value = {
        isLoggedIn,
        setIsLoggedIn,
        isLoading,
        setPayload,
        payload
    };

    return <UserContext.Provider value={value}>{children}</UserContext.Provider>;
};

export const useUser = () => useContext(UserContext);
