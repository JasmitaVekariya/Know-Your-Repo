import React, { useState } from 'react';
import { Menu } from 'lucide-react';
import Sidebar from '../components/Sidebar';

const MainLayout = ({ children }) => {
    const [sidebarOpen, setSidebarOpen] = useState(false);

    return (
        <div className="flex h-screen bg-gray-50 dark:bg-gray-900 overflow-hidden transition-colors duration-200">
            {/* Sidebar */}
            <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

            {/* Main Content */}
            <div className="flex-1 flex flex-col h-full w-full relative">
                {/* Mobile Header */}
                <div className="md:hidden flex items-center p-4 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
                    <button
                        onClick={() => setSidebarOpen(true)}
                        className="p-2 -ml-2 text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white"
                    >
                        <Menu className="w-6 h-6" />
                    </button>
                    <span className="ml-2 font-semibold text-gray-900 dark:text-white">Repository Chat</span>
                </div>

                {/* Content Area */}
                <main className="flex-1 overflow-auto relative">
                    {children}
                </main>
            </div>
        </div>
    );
};

export default MainLayout;
