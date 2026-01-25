import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

import Dashboard from './pages/Dashboard';
import Ingest from './pages/Ingest';
import Chat from './pages/Chat';
import LandingPage from './pages/LandingPage';
import ParticleBackground from './components/ParticleBackground';

import MainLayout from './layouts/MainLayout';
import { ChatProvider } from './context/ChatContext';
import { ThemeProvider } from './context/ThemeContext';

function App() {
  return (
    <ThemeProvider>
      <ChatProvider>
        <Router>
          <ParticleBackground />
          <Routes>
            <Route path="/" element={<LandingPage />} />

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
          </Routes>
        </Router>
      </ChatProvider>
    </ThemeProvider>
  );
}

export default App;
