import React, { useState, useRef, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import ReactMarkdown from 'react-markdown';
import { Send, ArrowLeft, Bot, User } from 'lucide-react';
import CodeBlock from '../components/CodeBlock';
import MindMapPanel from './MindMapPanel';

const Chat = () => {
    const { sessionId } = useParams();
    const userId = localStorage.getItem('user_id');
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef(null);
    const navigate = useNavigate();

    // Mind Map State
    const [chatMetadata, setChatMetadata] = useState(null);
    const [isMindMapMode, setIsMindMapMode] = useState(false);

    // Scroll to bottom on new message
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    // Load Metadata & History
    useEffect(() => {
        if (sessionId) {
            setLoading(true);

            // 1. Fetch Metadata (Mode & Mind Map)
            api.getChatMetadata(sessionId)
                .then(({ data }) => {
                    setChatMetadata(data);
                    // Enable split screen if mind map exists or mode is architect
                    if (data.mode === 'architect' || (data.mind_map && data.mind_map.length > 0)) {
                        setIsMindMapMode(true);
                    }
                })
                .catch(err => console.error("Failed to load metadata", err));

            // 2. Fetch History
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

    // -- LAZY LOADING LOGIC --

    const loadPhaseContent = async (index, currentMap) => {
        if (!currentMap || !currentMap[index]) return;

        // If content already exists, do nothing
        if (currentMap[index].content && currentMap[index].content.length > 50) return;

        // Currently loading?
        if (currentMap[index].loading) return;

        // Set loading state locally
        const newMap = [...currentMap];
        newMap[index] = { ...newMap[index], loading: true };
        setChatMetadata(prev => ({ ...prev, mind_map: newMap }));

        try {
            const { data } = await api.generatePhaseContent(sessionId, index);

            // Update with real content
            setChatMetadata(prev => {
                const updatedMap = [...prev.mind_map];
                updatedMap[index] = {
                    ...updatedMap[index],
                    content: data.content,
                    loading: false
                };
                return { ...prev, mind_map: updatedMap };
            });
        } catch (error) {
            console.error("Failed to generate phase content", error);
            // Revert loading state
            setChatMetadata(prev => {
                const updatedMap = [...prev.mind_map];
                updatedMap[index] = { ...updatedMap[index], loading: false };
                return { ...prev, mind_map: updatedMap };
            });
        }
    };

    // Trigger lazy load when step changes or loaded initially
    useEffect(() => {
        if (chatMetadata && chatMetadata.mind_map) {
            // Only trigger for initial load of index 0
            // Subsequent loads are handled by click handlers
            const currentIndex = chatMetadata.current_step_index || 0;
            // logic to ensure we don't double load is inside loadPhaseContent
            loadPhaseContent(currentIndex, chatMetadata.mind_map);
        }
    }, [chatMetadata?.mind_map?.length]); // Only re-run if map length changes (initial load)

    const [processingNext, setProcessingNext] = useState(false);

    const handleNextStep = async () => {
        if (!chatMetadata || processingNext) return;
        const nextIndex = (chatMetadata.current_step_index || 0) + 1;

        if (nextIndex >= chatMetadata.mind_map.length) return;

        setProcessingNext(true);

        try {
            // Check if content needs generation
            const nextStep = chatMetadata.mind_map[nextIndex];
            if (!nextStep.content || nextStep.content.length < 50) {
                // Generate content BEFORE switching
                const { data } = await api.generatePhaseContent(sessionId, nextIndex);

                // Update local state with new content first
                setChatMetadata(prev => {
                    const newMap = [...prev.mind_map];
                    newMap[nextIndex] = {
                        ...newMap[nextIndex],
                        content: data.content
                    };
                    return { ...prev, mind_map: newMap };
                });
            }

            // NOW switch to next step
            setChatMetadata(prev => ({ ...prev, current_step_index: nextIndex }));
            await api.updateChatStep(sessionId, nextIndex);

        } catch (error) {
            console.error("Failed to transition to next step", error);
            const msg = error.response?.data?.detail || error.message || "Unknown error";
            alert(`Failed to generate next phase: ${msg}`);
        } finally {
            setProcessingNext(false);
        }
    };

    // Step click is only for navigation within UNLOCKED steps.
    // We assume if a step is clicked, it's already unlocked/generated.
    const handleStepClick = (index) => {
        setChatMetadata(prev => ({ ...prev, current_step_index: index }));
        // Ensure content is loaded just in case (e.g. if we allow clicking ahead in future, but we won't)
        // loadPhaseContent(index, chatMetadata.mind_map); 
    };

    // --- RENDER HELPERS ---

    const renderChatInterface = () => (
        <div className="flex flex-col h-full relative">
            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6 pb-20">
                {messages.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-full text-center text-gray-400 dark:text-gray-500 pb-20">
                        <Bot className="w-12 h-12 mb-4 opacity-50" />
                        <p>{isMindMapMode ? "Ask questions about this phase." : "Ask a question about the repository."}</p>
                    </div>
                )}

                {messages.map((msg, idx) => (
                    <div key={idx} className={`w-full ${msg.role === 'user' ? 'bg-transparent' : 'bg-transparent'}`}>
                        <div className={`mx-auto max-w-4xl flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>

                            {/* Bot Avatar */}
                            {msg.role === 'bot' && (
                                <div className="flex-shrink-0 mt-1">
                                    <div className="w-8 h-8 bg-green-500 rounded-sm flex items-center justify-center">
                                        <Bot className="w-5 h-5 text-white" />
                                    </div>
                                </div>
                            )}

                            {/* Content */}
                            <div className={`relative max-w-[90%] ${msg.role === 'user'
                                ? 'bg-blue-600 text-white px-4 py-3 rounded-2xl rounded-br-none'
                                : 'w-full text-gray-800 dark:text-gray-100 overflow-hidden'
                                }`}>
                                <div className={`markdown-body text-sm leading-relaxed ${msg.role === 'bot' ? '' : ''}`}>
                                    <ReactMarkdown
                                        components={{
                                            code({ node, inline, className, children, ...props }) {
                                                const match = /language-(\w+)/.exec(className || '');
                                                const content = String(children).replace(/\n$/, '');
                                                const isInline = inline || (!match && content.length < 50 && !content.includes('\n'));

                                                if (!isInline) {
                                                    return (
                                                        <CodeBlock className={className} {...props}>
                                                            {children}
                                                        </CodeBlock>
                                                    );
                                                }
                                                return <code className="bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded text-blue-600 dark:text-blue-400 font-mono text-sm font-semibold" {...props}>{children}</code>;
                                            }
                                        }}
                                    >
                                        {msg.content}
                                    </ReactMarkdown>
                                </div>
                            </div>
                        </div>
                    </div>
                ))}

                {loading && (
                    <div className="flex justify-start items-center space-x-2 pl-12">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area (Sticky Bottom) */}
            <div className="absolute bottom-0 left-0 right-0 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800 p-4">
                <form onSubmit={handleSend} className="flex space-x-3">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder={isMindMapMode ? "Ask about this phase..." : "Type your question..."}
                        className="flex-1 px-4 py-3 border border-gray-200 dark:border-gray-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400"
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

    // --- MAIN LAYOUT ---

    // Initial Loading State (Before we know mode)
    if (!chatMetadata && loading) {
        return (
            <div className="flex h-screen items-center justify-center bg-gray-50 dark:bg-gray-900">
                <div className="flex flex-col items-center">
                    <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mb-4"></div>
                    <p className="text-gray-500 dark:text-gray-400 font-medium">Loading session...</p>
                </div>
            </div>
        );
    }

    // Ensure we render split screen if mode is architect, even if mind map is still loading
    const showSplitScreen = isMindMapMode || (chatMetadata && chatMetadata.mode === 'architect');

    if (showSplitScreen) {
        return (
            <div className="flex h-screen bg-gray-50 dark:bg-gray-900 overflow-hidden">
                {/* Left Panel (40%) - Mind Map */}
                <div className="w-[40%] h-full flex-shrink-0 border-r border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
                    {(!chatMetadata || !chatMetadata.mind_map || chatMetadata.mind_map.length === 0) ? (
                        <div className="flex flex-col items-center justify-center h-full p-8 text-center">
                            <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mb-4"></div>
                            <h3 className="text-lg font-semibold text-gray-800 dark:text-white">Generating Curriculum...</h3>
                            <p className="text-gray-500 dark:text-gray-400 text-sm mt-2">Analyzing repository architecture to build your learning path.</p>
                        </div>
                    ) : (
                        <MindMapPanel
                            mindMap={chatMetadata.mind_map}
                            currentStepIndex={chatMetadata.current_step_index || 0}
                            onNext={handleNextStep}
                            onStepClick={handleStepClick}
                            onRetry={() => loadPhaseContent(chatMetadata.current_step_index, chatMetadata.mind_map)}
                            processingNext={processingNext}
                        />
                    )}
                </div>

                {/* Right Panel (60%) - Chat */}
                <div className="w-[60%] h-full bg-white dark:bg-gray-900">
                    <div className="h-full relative flex flex-col">
                        {/* Minimal Header */}
                        <div className="flex-shrink-0 bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm px-4 py-3 border-b border-gray-100 dark:border-gray-800 flex justify-between items-center z-10">
                            <div>
                                <span className="text-xs font-bold text-blue-600 uppercase tracking-wider block">Interactive Mode</span>
                                <h1 className="text-sm font-semibold text-gray-800 dark:text-gray-200 truncate max-w-[300px]">
                                    {chatMetadata?.repo_name || 'Repository Chat'}
                                </h1>
                            </div>
                            <button onClick={() => navigate('/')} className="text-gray-400 hover:text-gray-600 p-1 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
                                <ArrowLeft className="w-5 h-5" />
                            </button>
                        </div>

                        {/* Chat Body */}
                        <div className="flex-1 overflow-hidden relative">
                            {renderChatInterface()}
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    // Default Chat Layout (Full Width)
    return (
        <div className="flex flex-col h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-200">
            {/* Standard Header */}
            <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4 flex justify-between items-center shadow-sm">
                <div>
                    <h1 className="text-lg font-bold text-gray-800 dark:text-white flex items-center">
                        <button onClick={() => navigate('/')} className="mr-3 text-gray-500 hover:text-gray-700">
                            <ArrowLeft className="w-5 h-5" />
                        </button>
                        {chatMetadata?.repo_name ? `Chat: ${chatMetadata.repo_name}` : 'Repository Chat'}
                    </h1>
                </div>
            </div>

            {/* Standard Chat Body */}
            <div className="flex-1 overflow-hidden relative">
                {renderChatInterface()}
            </div>
        </div>
    );
};

export default Chat;
