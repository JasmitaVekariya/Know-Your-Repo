import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api } from '../api/client';

const ChatContext = createContext();

export const useChat = () => {
    const context = useContext(ChatContext);
    if (!context) {
        throw new Error('useChat must be used within a ChatProvider');
    }
    return context;
};

export const ChatProvider = ({ children }) => {
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(false);
    const userId = localStorage.getItem('user_id');

    const fetchHistory = useCallback(async () => {
        if (!userId) {
            setHistory([]);
            return;
        }

        // Don't set loading true here to avoid flickering if we just want a background refresh
        // But for initial load it might be needed. We'll handle loading state in components mostly,
        // or add an initialLoading state.
        try {
            const { data } = await api.getChats(userId);
            setHistory(data);
        } catch (error) {
            console.error('Failed to fetch chat history', error);
        }
    }, [userId]);

    // Initial fetch
    useEffect(() => {
        fetchHistory();
    }, [fetchHistory]);

    // Exposed value
    const value = {
        history,
        loading, // We might want to expose this if we want global loading
        refreshHistory: fetchHistory
    };

    return (
        <ChatContext.Provider value={value}>
            {children}
        </ChatContext.Provider>
    );
};
