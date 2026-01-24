import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const client = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add Auth Interceptor
client.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

export const api = {
    // Auth
    login: (email, password) => {
        const formData = new FormData();
        formData.append('username', email); // OAuth2 expects username
        formData.append('password', password);
        return client.post('/auth/login', formData, {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        });
    },
    register: (email, password) => client.post('/auth/register', { email, password }),

    // User
    getUser: (userId) => client.get(`/user/${userId}`),
    getDashboard: (userId, days = 30) => client.get(`/user/${userId}/dashboard?days=${days}`),

    // Ingest
    ingestRepo: (repoUrl, userId) => client.post('/ingest', { repo_url: repoUrl, user_id: userId }),
    resumeSession: (sessionId, repoUrl) => client.post(`/ingest/${sessionId}/resume`, { repo_url: repoUrl }),

    // Chat
    getChats: (userId) => client.get(`/user/${userId}/chats`),
    getChatHistory: (sessionId) => client.get(`/chat/${sessionId}/history`),
    chat: (userId, sessionId, message) => client.post('/chat', {
        user_id: userId,
        session_id: sessionId,
        message
    }),
};
