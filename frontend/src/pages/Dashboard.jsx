import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { LogOut, MessageSquare, Wallet, Zap, Github } from 'lucide-react';

const Dashboard = () => {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [chatHistory, setChatHistory] = useState([]);
    const [historyLoading, setHistoryLoading] = useState(true);
    const [resumeLoading, setResumeLoading] = useState(null); // sessionId

    const navigate = useNavigate();
    const userId = localStorage.getItem('user_id');

    useEffect(() => {
        if (!userId) {
            navigate('/login');
            return;
        }
        fetchDashboard();
        fetchHistory();
    }, [userId]);

    const fetchDashboard = async () => {
        try {
            const { data } = await api.getDashboard(userId);
            setStats(data);
        } catch (error) {
            console.error('Failed to fetch dashboard', error);
        } finally {
            setLoading(false);
        }
    };

    const fetchHistory = async () => {
        try {
            const { data } = await api.getChats(userId);
            setChatHistory(data);
        } catch (error) {
            console.error('Failed to fetch chat history', error);
        } finally {
            setHistoryLoading(false);
        }
    };

    const startNewChat = () => {
        navigate('/ingest');
    };

    const handleLogout = () => {
        localStorage.removeItem('user_id');
        navigate('/login');
    }

    const handleResumeChat = async (sessionId, repoUrl) => {
        if (resumeLoading) return;
        setResumeLoading(sessionId);
        try {
            // Call resume endpoint to ensure vectors are ready
            await api.resumeSession(sessionId, repoUrl);
            navigate(`/chat/${sessionId}`);
        } catch (error) {
            console.error('Failed to resume chat', error);
            alert('Failed to resume chat session. See console.');
            setResumeLoading(null);
        }
    };

    if (loading) return <div className="p-10 text-center dark:text-white">Loading dashboard...</div>;

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8 transition-colors duration-200">
            {/* Header */}
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-gray-800 dark:text-white">Hello, {stats?.name || 'Developer'}</h1>
                    <p className="text-gray-500 dark:text-gray-400">Here's your repository intelligence overview.</p>
                </div>
                <div className="flex space-x-4">
                    <button onClick={startNewChat} className="flex items-center bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
                        <MessageSquare className="w-4 h-4 mr-2" />
                        Analyze New Repo
                    </button>
                    <button onClick={handleLogout} className="flex items-center text-gray-600 dark:text-gray-300 hover:text-red-600 dark:hover:text-red-400 transition-colors">
                        <LogOut className="w-5 h-5" />
                    </button>
                </div>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                <StatCard
                    icon={<Zap className="text-yellow-500" />}
                    title="Total Tokens"
                    value={stats?.total_tokens.toLocaleString()}
                    sub="Lifetime usage"
                />
                <StatCard
                    icon={<MessageSquare className="text-blue-500" />}
                    title="Prompts"
                    value={stats?.total_prompts}
                    sub="Questions asked"
                />
                <StatCard
                    icon={<Wallet className="text-red-500" />}
                    title="Unpaid Balance"
                    value={`$${stats?.price_left_to_pay}`}
                    sub={`Total Due: $${stats?.total_due_price}`}
                    highlight
                />
                <StatCard
                    icon={<Wallet className="text-green-500" />}
                    title="Paid"
                    value={`$${stats?.total_paid_price}`}
                    sub="Lifetime payments"
                />
            </div>

            {/* Usage Chart */}
            <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 transition-colors mb-8">
                <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-6">Token Usage (Last 30 Days)</h3>
                <div className="h-80 w-full min-h-[300px]">
                    <ResponsiveContainer width="100%" height="100%" minHeight={300}>
                        <AreaChart data={stats?.usage_chart}>
                            <defs>
                                <linearGradient id="colorTokens" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.1} />
                                    <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#374151" strokeOpacity={0.2} />
                            <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#9CA3AF' }} />
                            <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#9CA3AF' }} />
                            <Tooltip
                                contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)', backgroundColor: '#1F2937', color: '#F3F4F6' }}
                                itemStyle={{ color: '#F3F4F6' }}
                                labelStyle={{ color: '#9CA3AF' }}
                            />
                            <Area type="monotone" dataKey="tokens" stroke="#3B82F6" strokeWidth={3} fillOpacity={1} fill="url(#colorTokens)" />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Favorite Repositories */}
            <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 transition-colors">
                <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">Favorite Repositories</h3>
                {historyLoading ? (
                    <div className="text-gray-400 text-sm">Loading history...</div>
                ) : chatHistory.filter(c => c.is_favorite).length === 0 ? (
                    <div className="text-gray-400 text-sm">No favorite repositories yet. Mark a chat as favorite to see it here.</div>
                ) : (
                    <div className="space-y-3">
                        {chatHistory.filter(chat => chat.is_favorite).map((chat) => (
                            <div
                                key={chat.session_id}
                                onClick={() => handleResumeChat(chat.session_id, chat.repo_url)}
                                className="flex justify-between items-center p-4 border border-gray-100 dark:border-gray-700 rounded-lg hover:bg-blue-50 dark:hover:bg-gray-700 cursor-pointer transition-colors group"
                            >
                                <div className="flex items-center space-x-3">
                                    <div className="p-2 bg-gray-100 dark:bg-gray-900 rounded-lg group-hover:bg-blue-100 dark:group-hover:bg-blue-900 text-gray-600 dark:text-gray-400 group-hover:text-blue-600 dark:group-hover:text-blue-400">
                                        <Github className="w-5 h-5" />
                                    </div>
                                    <div>
                                        <h4 className="font-medium text-gray-800 dark:text-gray-200">{chat.repo_name}</h4>
                                        <p className="text-xs text-gray-500 dark:text-gray-400">{new Date(chat.created_at).toLocaleDateString()} • {chat.repo_url}</p>
                                    </div>
                                </div>
                                <div className="text-blue-600 dark:text-blue-400 opacity-0 group-hover:opacity-100 text-sm font-medium">
                                    {resumeLoading === chat.session_id ? 'Resuming...' : 'Open Chat →'}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

const StatCard = ({ icon, title, value, sub, highlight }) => (
    <div className={`bg-white dark:bg-gray-800 p-6 rounded-xl shadow-sm border transaction-colors ${highlight ? 'border-red-200 bg-red-50 dark:bg-red-900/10 dark:border-red-800' : 'border-gray-100 dark:border-gray-700'}`}>
        <div className="flex items-center justify-between mb-4">
            <span className="p-2 bg-gray-100 dark:bg-gray-700 rounded-lg">{icon}</span>
        </div>
        <h3 className="text-2xl font-bold text-gray-800 dark:text-white">{value}</h3>
        <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{title}</p>
        {sub && <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">{sub}</p>}
    </div>
);

export default Dashboard;
