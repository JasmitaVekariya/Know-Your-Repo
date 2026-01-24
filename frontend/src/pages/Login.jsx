import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';

const Login = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [isRegistering, setIsRegistering] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            let response;
            if (isRegistering) {
                response = await api.register(email, password);
            } else {
                try {
                    // Login expects form data in our client wrapper
                    response = await api.login(email, password);
                } catch (err) {
                    throw err;
                }
            }

            const { access_token } = response.data;
            localStorage.setItem('token', access_token);

            // Decode payload safely
            try {
                const payload = JSON.parse(atob(access_token.split('.')[1]));
                localStorage.setItem('user_id', payload.sub);
                localStorage.setItem('user_email', payload.email);
            } catch (e) {
                console.error("Token decode failed", e);
            }

            navigate('/dashboard');
        } catch (error) {
            console.error('Auth failed:', error);
            let msg = error.response?.data?.detail;
            if (typeof msg === 'object') {
                msg = JSON.stringify(msg);
            }
            if (!msg) {
                msg = error.message || "Unknown error occurred";
                if (error.response?.status) msg += ` (Status: ${error.response.status})`;
            }
            alert(`Authentication Error: ${msg}`);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-100">
            <div className="bg-white p-8 rounded-lg shadow-md w-96">
                <h2 className="text-2xl font-bold mb-6 text-center text-gray-800">
                    {isRegistering ? 'Create Account' : 'Welcome Back'}
                </h2>
                <form onSubmit={handleSubmit}>
                    <div className="mb-4">
                        <label className="block text-gray-700 text-sm font-bold mb-2">Email Address</label>
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                            placeholder="Enter your email"
                            required
                        />
                    </div>
                    <div className="mb-6">
                        <label className="block text-gray-700 text-sm font-bold mb-2">Password</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                            placeholder="••••••••"
                            required
                        />
                    </div>
                    <button
                        type="submit"
                        disabled={loading}
                        className={`w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition duration-200 ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                        {loading ? 'Processing...' : (isRegistering ? 'Sign Up' : 'Sign In')}
                    </button>
                </form>

                <div className="mt-4 text-center">
                    <button
                        onClick={() => setIsRegistering(!isRegistering)}
                        className="text-sm text-blue-600 hover:underline"
                    >
                        {isRegistering ? 'Already have an account? Sign In' : 'Need an account? Sign Up'}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Login;
