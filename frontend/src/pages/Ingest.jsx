import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { Github, Loader } from 'lucide-react';

const Ingest = () => {
    const [repoUrl, setRepoUrl] = useState('');
    const [loading, setLoading] = useState(false);
    const [status, setStatus] = useState('');
    const navigate = useNavigate();
    const userId = localStorage.getItem('user_id');

    const handleIngest = async (e) => {
        e.preventDefault();
        if (!repoUrl) return;

        setLoading(true);
        setStatus('Initializing session...');

        try {
            // Ingest is synchronous in our simple version, or returns a session to poll
            // Our backend blocks until done (sync mode)
            setStatus('Cloning and analyzing repository... This may take a minute.');
            const { data } = await api.ingestRepo(repoUrl, userId);

            setStatus('Ingestion complete! Redirecting...');
            setTimeout(() => {
                navigate(`/chat/${data.session_id}`);
            }, 1000);

        } catch (error) {
            console.error('Ingestion failed:', error);
            setStatus('Failed to ingest repository. Please check the URL.');
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
            <div className="bg-white p-8 rounded-xl shadow-lg max-w-md w-full">
                <div className="flex justify-center mb-6">
                    <div className="p-4 bg-gray-100 rounded-full">
                        <Github className="w-10 h-10 text-gray-800" />
                    </div>
                </div>

                <h2 className="text-2xl font-bold text-center text-gray-800 mb-2">Analyze Repository</h2>
                <p className="text-center text-gray-500 mb-8">Enter a public GitHub URL to begin.</p>

                <form onSubmit={handleIngest}>
                    <div className="mb-6">
                        <input
                            type="url"
                            value={repoUrl}
                            onChange={(e) => setRepoUrl(e.target.value)}
                            placeholder="https://github.com/username/repo"
                            className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            required
                            disabled={loading}
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className={`w-full bg-black text-white py-3 rounded-lg font-medium hover:bg-gray-800 transition duration-200 flex items-center justify-center ${loading ? 'opacity-70 cursor-not-allowed' : ''}`}
                    >
                        {loading ? (
                            <>
                                <Loader className="w-5 h-5 animate-spin mr-2" />
                                Processing...
                            </>
                        ) : (
                            'Start Analysis'
                        )}
                    </button>
                </form>

                {status && (
                    <div className={`mt-4 text-center text-sm ${status.includes('Failed') ? 'text-red-500' : 'text-blue-600'}`}>
                        {status}
                    </div>
                )}

                <button onClick={() => navigate('/dashboard')} className="w-full mt-4 text-gray-500 text-sm hover:underline">
                    Back to Dashboard
                </button>
            </div>
        </div>
    );
};

export default Ingest;
