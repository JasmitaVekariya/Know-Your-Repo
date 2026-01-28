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
    // Use state for userId so we can trigger updates
    const [userId, setUserId] = useState(localStorage.getItem('user_id'));

    const fetchHistory = useCallback(async () => {
        const currentUserId = localStorage.getItem('user_id');
        setUserId(currentUserId); // Sync state

        if (!currentUserId) {
            setHistory([]);
            return;
        }

        try {
            const { data } = await api.getChats(currentUserId);
            setHistory(data);
        } catch (error) {
            console.error('Failed to fetch chat history', error);
        }
    }, []);

    // Initial fetch and listen for auth changes
    useEffect(() => {
        fetchHistory();

        const handleAuthChange = () => {
            // Force re-read from local storage if needed, or just re-fetch
            // verification: we need to re-read userId from localStorage inside fetchHistory 
            // but fetchHistory memoizes on 'userId' which is a const from render scope.
            // We need to move userId to state or ref, or just force update.
            // Actually, simplest is to just window.location.reload() on logout, 
            // but on login we want SPA feel.
            // Let's reload the history.
            fetchHistory();
        };

        window.addEventListener('auth-change', handleAuthChange);
        return () => window.removeEventListener('auth-change', handleAuthChange);
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
