import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Ingest from './pages/Ingest';
import Chat from './pages/Chat';

import MainLayout from './layouts/MainLayout';
import { ChatProvider } from './context/ChatContext';

import { ThemeProvider } from './context/ThemeContext';

function App() {
  return (
    <ThemeProvider>
      <ChatProvider>
        <Router>
          <Routes>
            <Route path="/login" element={<Login />} />

            {/* Protected Routes wrapped in MainLayout */}
            <Route path="/dashboard" element={
              <MainLayout>
                <Dashboard />
              </MainLayout>
            } />
            <Route path="/new" element={
              <MainLayout>
                <Ingest />
              </MainLayout>
            } />
            <Route path="/chat/:sessionId" element={<Chat />} />

            {/* Default redirect to New Chat flow */}
            <Route path="/" element={<Navigate to="/new" replace />} />
          </Routes>
        </Router>
      </ChatProvider>
    </ThemeProvider>
  );
}

export default App;
