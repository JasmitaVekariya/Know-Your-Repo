import React, { useState, useRef, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import ReactMarkdown from 'react-markdown';
import { Send, ArrowLeft, Bot, User } from 'lucide-react';

const Chat = () => {
    const { sessionId } = useParams();
    const userId = localStorage.getItem('user_id');
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef(null);
    const navigate = useNavigate();

    // Scroll to bottom on new message
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    // Load History
    useEffect(() => {
        if (sessionId) {
            setLoading(true);
            api.getChatHistory(sessionId)
                .then(({ data }) => {
                    setMessages(data);
                })
                .catch(err => console.error("Failed to load chat history", err))
                .finally(() => setLoading(false));
        }
    }, [sessionId]);

    const handleSend = async (e) => {
        e.preventDefault();
        if (!input.trim() || loading) return;

        const userMsg = { role: 'user', content: input };
        setMessages((prev) => [...prev, userMsg]);
        setInput('');
        setLoading(true);

        try {
            const { data } = await api.chat(userId, sessionId, userMsg.content);
            const botMsg = { role: 'bot', content: data.answer };
            setMessages((prev) => [...prev, botMsg]);
        } catch (error) {
            console.error('Chat failed:', error);
            setMessages((prev) => [...prev, { role: 'bot', content: 'Sorry, I encountered an error. Please try again.' }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-screen bg-gray-50">
            {/* Header */}
            <div className="bg-white border-b border-gray-200 px-6 py-4 flex items-center shadow-sm">
                <button onClick={() => navigate('/dashboard')} className="mr-4 text-gray-500 hover:text-gray-800">
                    <ArrowLeft className="w-5 h-5" />
                </button>
                <div>
                    <h1 className="text-lg font-bold text-gray-800">Repository Chat</h1>
                    <p className="text-xs text-gray-500">Session: {sessionId?.substring(0, 8)}...</p>
                </div>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {messages.length === 0 && (
                    <div className="text-center text-gray-400 mt-20">
                        <Bot className="w-12 h-12 mx-auto mb-4 opacity-50" />
                        <p>Ask a question about the repository to get started.</p>
                        <p className="text-sm">e.g., "Explain the architecture" or "How does authentication work?"</p>
                    </div>
                )}

                {messages.map((msg, idx) => (
                    <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-3xl rounded-2xl px-6 py-4 ${msg.role === 'user'
                            ? 'bg-blue-600 text-white rounded-br-none'
                            : 'bg-white border border-gray-200 text-gray-800 rounded-bl-none shadow-sm'
                            }`}>
                            <div className="flex items-start mb-1">
                                {msg.role === 'bot' ? <Bot className="w-4 h-4 mr-2 mt-1 opacity-70" /> : null}
                                <div className="markdown-body text-sm leading-relaxed">
                                    <ReactMarkdown>
                                        {msg.content}
                                    </ReactMarkdown>
                                </div>
                            </div>
                        </div>
                    </div>
                ))}
                {loading && (
                    <div className="flex justify-start">
                        <div className="bg-white border border-gray-200 rounded-2xl rounded-bl-none px-6 py-4 shadow-sm flex items-center space-x-2">
                            <Bot className="w-4 h-4 opacity-70" />
                            <div className="flex space-x-1">
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                            </div>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="bg-white border-t border-gray-200 p-4">
                <form onSubmit={handleSend} className="max-w-4xl mx-auto flex space-x-4">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Type your question..."
                        className="flex-1 px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        disabled={loading}
                    />
                    <button
                        type="submit"
                        disabled={loading || !input.trim()}
                        className="bg-blue-600 text-white p-3 rounded-xl hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                        <Send className="w-5 h-5" />
                    </button>
                </form>
            </div>
        </div>
    );
};

export default Chat;
