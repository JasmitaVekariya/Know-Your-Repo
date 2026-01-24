import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { Github, Loader } from 'lucide-react';
import { useChat } from '../context/ChatContext';

const Ingest = () => {
    const { refreshHistory } = useChat();
    const [repoUrl, setRepoUrl] = useState('');
    const [loading, setLoading] = useState(false);
    const [selectedMode, setSelectedMode] = useState('architect');
    const [status, setStatus] = useState('');
    const navigate = useNavigate(); // Added missing navigate hook

    // Available modes from backend
    const modes = [
        { id: 'architect', title: 'Repo Architectural Analysis', desc: 'High-level patterns, data flow, & decisions.' },
        { id: 'extension', title: 'Code Extension', desc: 'Where & how to add new features safely.' },
        { id: 'system_design', title: 'System Design', desc: 'Scalability, infrastructure, & trade-offs.' },
        { id: 'debugger', title: 'Code Debugger', desc: 'Root cause analysis & bug fixing.' },
    ];

    const userId = localStorage.getItem('user_id') || 'demo-user';

    const handleIngest = async (e) => {
        e.preventDefault();
        if (!repoUrl) return;

        setLoading(true);
        setStatus('Initializing session...');

        try {
            setStatus('Cloning and analyzing repository... This may take a minute.');
            const { data } = await api.ingestRepo(repoUrl, userId, selectedMode);

            // Refresh sidebar history immediately
            if (refreshHistory) refreshHistory();

            setStatus('Ingestion complete! Redirecting...');
            setTimeout(() => {
                navigate(`/chat/${data.session_id}`);
            }, 500);

        } catch (error) {
            console.error('Ingestion failed:', error);
            let msg = error.response?.data?.detail;
            if (typeof msg === 'object') {
                msg = JSON.stringify(msg);
            }
            setStatus(msg || 'Failed to ingest repository. Please check the URL.');
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col items-center justify-center h-full px-4 text-center overflow-y-auto py-10">
            {/* Logo/Icon */}
            <div className="mb-6">
                <div className="w-16 h-16 bg-white dark:bg-gray-800 rounded-full flex items-center justify-center shadow-sm border border-gray-100 dark:border-gray-700 mx-auto transition-colors">
                    <Github className="w-8 h-8 text-black dark:text-white" />
                </div>
            </div>

            {/* Welcome Text */}
            <h1 className="text-2xl font-semibold text-gray-800 dark:text-gray-100 mb-2">
                What do you want to build today?
            </h1>
            <p className="text-gray-500 dark:text-gray-400 mb-8">
                Start by analyzing a GitHub repository. select a mode below.
            </p>

            {/* Input Box */}
            <div className="w-full max-w-2xl mb-8">
                <form onSubmit={handleIngest} className="relative">
                    <div className="relative flex items-center w-full px-4 py-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-sm focus-within:ring-2 focus-within:ring-blue-500 hover:border-gray-300 dark:hover:border-gray-600 transition-all">
                        <Github className="w-5 h-5 text-gray-400 mr-3" />
                        <input
                            type="url"
                            value={repoUrl}
                            onChange={(e) => setRepoUrl(e.target.value)}
                            placeholder="Paste GitHub Repository URL (e.g., https://github.com/owner/repo)"
                            className="flex-1 bg-transparent border-none focus:outline-none text-gray-800 dark:text-gray-100 placeholder-gray-400"
                            required
                            disabled={loading}
                        />
                        <button
                            type="submit"
                            disabled={loading || !repoUrl}
                            className={`ml-2 p-2 rounded-lg transition-colors ${loading || !repoUrl ? 'bg-gray-100 dark:bg-gray-700 text-gray-400 cursor-not-allowed' : 'bg-black dark:bg-white text-white dark:text-black hover:bg-gray-800 dark:hover:bg-gray-200'}`}
                        >
                            {loading ? <Loader className="w-4 h-4 animate-spin" /> : <span className="text-sm font-medium px-2">Analyze</span>}
                        </button>
                    </div>
                </form>

                {/* Status Message */}
                {status && (
                    <div className={`mt-4 text-sm font-medium ${status.toLowerCase().includes('failed') || status.toLowerCase().includes('error') ? 'text-red-500 dark:text-red-400' : 'text-blue-600 dark:text-blue-400 animate-pulse'}`}>
                        {status}
                    </div>
                )}
            </div>

            {/* Mode Selection Grid */}
            <div className="w-full max-w-2xl">
                <h3 className="text-left text-sm font-semibold text-gray-500 dark:text-gray-400 mb-4 uppercase tracking-wider">Select Analysis Mode</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {modes.map((mode) => (
                        <div
                            key={mode.id}
                            onClick={() => setSelectedMode(mode.id)}
                            className={`p-4 rounded-xl border cursor-pointer transition-all duration-200 text-left relative group
                                ${selectedMode === mode.id
                                    ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-500 ring-1 ring-blue-500'
                                    : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-700'
                                }
                            `}
                        >
                            <h3 className={`font-semibold mb-1 ${selectedMode === mode.id ? 'text-blue-700 dark:text-blue-400' : 'text-gray-800 dark:text-gray-200'}`}>
                                {mode.title}
                            </h3>
                            <p className="text-xs text-gray-500 dark:text-gray-400">
                                {mode.desc}
                            </p>

                            {/* Selected Indicator */}
                            {selectedMode === mode.id && (
                                <div className="absolute top-4 right-4 text-blue-500">
                                    <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default Ingest;
