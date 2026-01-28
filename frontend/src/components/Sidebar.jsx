import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { MessageSquare, Plus, LogOut, LayoutDashboard, Github, History, User, MoreHorizontal, Trash2, Star, Moon, Sun, SidebarClose } from 'lucide-react';
import { useChat } from '../context/ChatContext';
import { useTheme } from '../context/ThemeContext';
import { api } from '../api/client';

const Sidebar = ({ isOpen, onClose }) => {
    const { history, loading, refreshHistory } = useChat();
    const { theme, toggleTheme } = useTheme();
    const [showProfileMenu, setShowProfileMenu] = useState(false);
    const [activeMenu, setActiveMenu] = useState(null); // sessionId of open menu
    const [userName, setUserName] = useState('Developer');
    const navigate = useNavigate();
    const location = useLocation();
    const userId = localStorage.getItem('user_id');

    useEffect(() => {
        if (userId) {
            api.getUser(userId).then(({ data }) => {
                if (data.name) {
                    setUserName(data.name);
                } else if (data.email) {
                    setUserName(data.email.split('@')[0]);
                }
            }).catch(console.error);
        }
    }, [userId]);

    const handleNewChat = () => {
        navigate('/new');
        if (window.innerWidth < 768) onClose();
    };

    const handleLogout = () => {
        localStorage.removeItem('user_id');
        navigate('/');
    };

    const handleDashboard = () => {
        navigate('/dashboard');
        setShowProfileMenu(false);
    };

    const handleDeleteChat = async (e, sessionId) => {
        e.stopPropagation();
        if (window.confirm("Are you sure you want to delete this chat?")) {
            try {
                await api.deleteChat(sessionId);
                refreshHistory();
                if (location.pathname.includes(sessionId)) {
                    navigate('/new');
                }
            } catch (error) {
                console.error("Failed to delete chat", error);
            }
        }
        setActiveMenu(null);
    };

    const handleToggleFavorite = async (e, sessionId) => {
        e.stopPropagation();
        try {
            await api.toggleFavorite(sessionId);
            refreshHistory();
        } catch (error) {
            console.error("Failed to toggle favorite", error);
        }
        setActiveMenu(null);
    };

    // Helper to group chats by date
    const groupChats = (chats) => {
        const groups = {
            'Today': [],
            'Yesterday': [],
            'Previous 7 Days': [],
            'Previous 30 Days': [],
            'Older': []
        };

        const now = new Date();
        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);
        const last7Days = new Date(today);
        last7Days.setDate(last7Days.getDate() - 7);
        const last30Days = new Date(today);
        last30Days.setDate(last30Days.getDate() - 30);

        chats.forEach(chat => {
            const chatDate = new Date(chat.created_at);
            // Reset time part for accurate date comparison
            const chatDateOnly = new Date(chatDate.getFullYear(), chatDate.getMonth(), chatDate.getDate());

            let group = 'Older';
            if (chatDateOnly.getTime() === today.getTime()) {
                group = 'Today';
            } else if (chatDateOnly.getTime() === yesterday.getTime()) {
                group = 'Yesterday';
            } else if (chatDateOnly > last7Days) {
                group = 'Previous 7 Days';
            } else if (chatDateOnly > last30Days) {
                group = 'Previous 30 Days';
            }

            groups[group].push(chat);
        });

        return groups;
    };

    const groupedHistory = groupChats(history || []);
    const groupOrder = ['Today', 'Yesterday', 'Previous 7 Days', 'Previous 30 Days', 'Older'];

    return (
        <>
            {/* Mobile Overlay */}
            {isOpen && (
                <div
                    className="fixed inset-0 bg-black bg-opacity-50 z-20 md:hidden"
                    onClick={onClose}
                />
            )}

            {/* Sidebar Container */}
            <div className={`
                fixed md:static inset-y-0 left-0 z-30
                w-64 flex flex-col
                bg-gray-100 dark:bg-black 
                text-gray-900 dark:text-gray-100
                border-r border-gray-200 dark:border-gray-800
                transform transition-all duration-200 ease-in-out
                ${isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
            `} onClick={() => setActiveMenu(null)}>
                {/* Sidebar Header with Collapse */}
                <div className="flex items-center justify-between px-4 pt-4 pb-2">
                    <div className="flex items-center space-x-2 text-gray-400">
                        {/* Optional branding or just spacing */}
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-800 text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white transition-colors"
                        title="Collapse menu"
                    >
                        <SidebarClose className="w-5 h-5" />
                    </button>
                </div>

                {/* New Chat Button */}
                <div className="px-4 pb-4">
                    <button
                        onClick={handleNewChat}
                        className="w-full flex items-center justify-start space-x-3 px-4 py-3 
                        bg-white dark:bg-gray-800 
                        hover:bg-gray-200 dark:hover:bg-gray-700 
                        text-gray-900 dark:text-white
                        rounded-lg transition-colors border border-gray-200 dark:border-gray-700 shadow-sm"
                    >
                        <Plus className="w-5 h-5" />
                        <span className="font-medium text-sm">New Chat</span>
                    </button>
                </div>

                {/* History List */}
                <div className="flex-1 overflow-y-auto px-2 py-2 scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-700 scrollbar-track-transparent">
                    {loading ? (
                        <div className="px-4 py-2 text-sm text-gray-500 dark:text-gray-400">Loading...</div>
                    ) : history.length === 0 ? (
                        <div className="px-4 py-2 text-sm text-gray-500">No chat history</div>
                    ) : (
                        groupOrder.map(group => {
                            const chats = groupedHistory[group];
                            if (chats.length === 0) return null;

                            return (
                                <div key={group} className="mb-4">
                                    <div className="px-4 mb-2 text-xs font-semibold text-gray-500 uppercase tracking-wider sticky top-0 bg-gray-100 dark:bg-black py-1 z-10 transition-colors">
                                        {group}
                                    </div>
                                    <div className="space-y-1">
                                        {chats.map((chat) => (
                                            <div key={chat.session_id} className="relative group">
                                                <button
                                                    onClick={() => {
                                                        navigate(`/chat/${chat.session_id}`);
                                                        if (window.innerWidth < 768) onClose();
                                                    }}
                                                    className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-sm transition-colors text-left pr-8
                                                        ${location.pathname.includes(chat.session_id)
                                                            ? 'bg-gray-300 dark:bg-gray-800 text-gray-900 dark:text-white'
                                                            : 'text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-900'}
                                                    `}
                                                >
                                                    <div className="flex flex-col flex-1 min-w-0">
                                                        <span className="truncate font-medium">{chat.repo_name || 'Unknown Repo'}</span>
                                                        <span className="text-[10px] uppercase tracking-wider text-gray-400 dark:text-gray-500 font-bold">
                                                            {chat.mode ? `${chat.mode}` : 'Architect'}
                                                        </span>
                                                    </div>
                                                </button>

                                                {/* Actions Menu Trigger */}
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        setActiveMenu(activeMenu === chat.session_id ? null : chat.session_id);
                                                    }}
                                                    className={`absolute right-2 top-1/2 transform -translate-y-1/2 p-1 rounded hover:bg-gray-700 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity ${activeMenu === chat.session_id ? 'opacity-100' : ''}`}
                                                >
                                                    <MoreHorizontal className="w-4 h-4" />
                                                </button>

                                                {/* Context Menu */}
                                                {activeMenu === chat.session_id && (
                                                    <div className="absolute right-0 top-full mt-1 w-32 bg-gray-800 border border-gray-700 rounded shadow-lg z-20 py-1">
                                                        <button
                                                            onClick={(e) => handleToggleFavorite(e, chat.session_id)}
                                                            className="w-full text-left px-3 py-2 text-xs hover:bg-gray-700 flex items-center space-x-2"
                                                        >
                                                            <Star className="w-3 h-3" />
                                                            <span>{chat.is_favorite ? 'Unfavorite' : 'Favorite'}</span>
                                                        </button>
                                                        <button
                                                            onClick={(e) => handleDeleteChat(e, chat.session_id)}
                                                            className="w-full text-left px-3 py-2 text-xs hover:bg-gray-700 text-red-400 flex items-center space-x-2"
                                                        >
                                                            <Trash2 className="w-3 h-3" />
                                                            <span>Delete</span>
                                                        </button>
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            );
                        })
                    )}
                </div>

                {/* User Profile */}
                <div className="p-4 border-t border-gray-200 dark:border-gray-800 transition-colors">
                    <div className="relative">
                        <button
                            onClick={(e) => {
                                e.stopPropagation();
                                setShowProfileMenu(!showProfileMenu);
                            }}
                            className="w-full flex items-center justify-between px-2 py-2 hover:bg-gray-200 dark:hover:bg-gray-800 rounded-lg transition-colors text-gray-900 dark:text-gray-100"
                        >
                            <div className="flex items-center space-x-3">
                                <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center">
                                    <span className="text-white font-bold text-xs">{userName.substring(0, 2).toUpperCase()}</span>
                                </div>
                                <div className="text-sm font-medium">{userName}</div>
                            </div>
                        </button>

                        {/* Profile Menu Popover */}
                        {showProfileMenu && (
                            <div className="absolute bottom-full left-0 w-full mb-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl overflow-hidden z-50 text-gray-700 dark:text-gray-200">
                                <button
                                    onClick={handleDashboard}
                                    className="w-full flex items-center space-x-3 px-4 py-3 hover:bg-gray-100 dark:hover:bg-gray-800 text-sm transition-colors"
                                >
                                    <LayoutDashboard className="w-4 h-4" />
                                    <span>Dashboard</span>
                                </button>
                                <div className="h-px bg-gray-200 dark:bg-gray-800"></div>
                                <button
                                    onClick={() => {
                                        toggleTheme();
                                        setShowProfileMenu(false);
                                    }}
                                    className="w-full flex items-center space-x-3 px-4 py-3 hover:bg-gray-100 dark:hover:bg-gray-800 text-sm transition-colors"
                                >
                                    {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
                                    <span>{theme === 'dark' ? 'Light Mode' : 'Dark Mode'}</span>
                                </button>
                                <div className="h-px bg-gray-200 dark:bg-gray-800"></div>
                                <button
                                    onClick={handleLogout}
                                    className="w-full flex items-center space-x-3 px-4 py-3 hover:bg-gray-100 dark:hover:bg-gray-800 text-sm text-red-500 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 transition-colors"
                                >
                                    <LogOut className="w-4 h-4" />
                                    <span>Log out</span>
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </>
    );
};

export default Sidebar;
