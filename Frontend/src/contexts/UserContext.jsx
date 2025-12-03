import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

export const UserContext = createContext();

export const UserProvider = ({ children }) => {
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [payload, setPayload] = useState(null);

    useEffect(() => {
        // Chiamata al backend per verificare il token nel cookie HttpOnly
        axios.get('http://127.0.0.1:8000/auth/me', { withCredentials: true })
            .then((response) => {
                console.log(response)
                if (response.data.logged_in) {
                    setIsLoggedIn(true);
                    console.log(response.data.user)
                    setPayload(response.data.user);
                } else {
                    setIsLoggedIn(false);
                    setPayload(null);
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
