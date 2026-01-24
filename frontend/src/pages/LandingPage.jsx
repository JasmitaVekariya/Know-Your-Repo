import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Brain, Zap, Layers, Coins, MoveRight, CheckCircle2, X } from 'lucide-react';
import { api } from '../api/client';

const ParticleBackground = () => {
    const canvasRef = useRef(null);

    useEffect(() => {
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        let animationFrameId;
        let w, h;
        let particles = [];

        const init = () => {
            w = canvas.width = window.innerWidth;
            h = canvas.height = window.innerHeight;
            particles = [];

            const particleCount = w > 768 ? 150 : 80;
            for (let i = 0; i < particleCount; i++) {
                particles.push({
                    x: Math.random() * w,
                    y: Math.random() * h,
                    vx: (Math.random() - 0.5) * 0.5,
                    vy: (Math.random() - 0.5) * 0.5,
                    size: Math.random() * 2 + 1,
                    color: i % 2 === 0 ? '#4F46E5' : (i % 3 === 0 ? '#10B981' : '#F59E0B')
                });
            }
        };

        const draw = () => {
            ctx.clearRect(0, 0, w, h);
            particles.forEach((p, i) => {
                p.x += p.vx;
                p.y += p.vy;
                if (p.x < 0 || p.x > w) p.vx *= -1;
                if (p.y < 0 || p.y > h) p.vy *= -1;
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
                ctx.fillStyle = p.color;
                ctx.fill();
                for (let j = i + 1; j < particles.length; j++) {
                    const p2 = particles[j];
                    const dist = Math.sqrt(Math.pow(p.x - p2.x, 2) + Math.pow(p.y - p2.y, 2));
                    if (dist < 150) {
                        ctx.beginPath();
                        ctx.strokeStyle = `rgba(100, 116, 139, ${0.1 - dist / 1500})`;
                        ctx.lineWidth = 0.5;
                        ctx.moveTo(p.x, p.y);
                        ctx.lineTo(p2.x, p2.y);
                        ctx.stroke();
                    }
                }
            });
            animationFrameId = requestAnimationFrame(draw);
        };

        init();
        window.addEventListener('resize', init);
        draw();

        return () => {
            window.removeEventListener('resize', init);
            cancelAnimationFrame(animationFrameId);
        };
    }, []);

    return <canvas ref={canvasRef} className="absolute inset-0 pointer-events-none opacity-40 z-0" />;
};

const FeatureCard = ({ icon: Icon, title, description, badge }) => (
    <div className="group p-8 rounded-3xl bg-white/50 dark:bg-gray-800/50 backdrop-blur-sm border border-gray-100 dark:border-gray-700 hover:border-blue-200 dark:hover:border-blue-800 hover:shadow-xl hover:shadow-blue-500/5 transition-all duration-300">
        <div className="w-12 h-12 bg-blue-50 dark:bg-blue-900/30 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
            <Icon className="w-6 h-6 text-blue-600 dark:text-blue-400" />
        </div>
        {badge && (
            <span className="inline-block px-3 py-1 mb-4 text-xs font-semibold tracking-wider text-blue-600 uppercase bg-blue-50 rounded-full dark:bg-blue-900/30 dark:text-blue-400">
                {badge}
            </span>
        )}
        <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-3">{title}</h3>
        <p className="text-gray-500 dark:text-gray-400 leading-relaxed">{description}</p>
    </div>
);

// --- LOGIN MODAL ---
const LoginModal = ({ isOpen, onClose }) => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [isRegistering, setIsRegistering] = useState(false);
    const navigate = useNavigate();

    if (!isOpen) return null;

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            let response;
            if (isRegistering) {
                response = await api.register(email, password);
            } else {
                response = await api.login(email, password);
            }

            const { access_token } = response.data;
            localStorage.setItem('token', access_token);
            try {
                const payload = JSON.parse(atob(access_token.split('.')[1]));
                localStorage.setItem('user_id', payload.sub);
                localStorage.setItem('user_email', payload.email);

                // Dispatch event to notify ChatContext
                window.dispatchEvent(new Event('auth-change'));
            } catch (e) {
                console.error("Token decode failed", e);
            }
            onClose();
            navigate('/new');
        } catch (error) {
            console.error('Auth failed:', error);
            const msg = error.response?.data?.detail || error.message || "Unknown error";
            alert(`Authentication Error: ${typeof msg === 'object' ? JSON.stringify(msg) : msg}`);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
            <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-md p-8 relative animate-in fade-in zoom-in-95 duration-200">
                <button onClick={onClose} className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
                    <X className="w-5 h-5" />
                </button>

                <div className="mb-8 text-center">
                    <div className="inline-flex items-center justify-center w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-xl mb-4 text-blue-600 dark:text-blue-400">
                        <Brain className="w-6 h-6" />
                    </div>
                    <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                        {isRegistering ? 'Create your account' : 'Welcome back to KYR'}
                    </h2>
                    <p className="text-gray-500 dark:text-gray-300 mt-2">
                        {isRegistering ? 'Start analyzing your repos today.' : 'Sign in to continue your analysis.'}
                    </p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-white mb-1">Email</label>
                        <input
                            type="email"
                            required
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="w-full px-4 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none transition-all text-gray-900 dark:text-white"
                            placeholder="name@example.com"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-white mb-1">Password</label>
                        <input
                            type="password"
                            required
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full px-4 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none transition-all text-gray-900 dark:text-white"
                            placeholder="••••••••"
                        />
                    </div>
                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-xl transition-all shadow-lg shadow-blue-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {loading ? 'Processing...' : (isRegistering ? 'Sign Up' : 'Sign In')}
                    </button>
                </form>

                <div className="mt-6 text-center">
                    <button
                        onClick={() => setIsRegistering(!isRegistering)}
                        className="text-sm text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 font-medium transition-colors"
                    >
                        {isRegistering ? 'Already have an account? Sign In' : "Don't have an account? Sign Up"}
                    </button>
                </div>
            </div>
        </div>
    );
};

const LandingPage = () => {
    const navigate = useNavigate();
    const [isLoginOpen, setIsLoginOpen] = useState(false);

    const handleStart = () => {
        const userId = localStorage.getItem('user_id');
        if (userId) {
            navigate('/new');
        } else {
            setIsLoginOpen(true);
        }
    };

    return (
        <div className="min-h-screen bg-black text-white font-sans selection:bg-blue-900">
            <LoginModal isOpen={isLoginOpen} onClose={() => setIsLoginOpen(false)} />

            {/* Navbar */}
            <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 dark:bg-gray-950/80 backdrop-blur-md border-b border-gray-100 dark:border-gray-800">
                <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        {/* KYR Logo */}
                        <div className="w-8 h-8 bg-gradient-to-tr from-blue-600 to-indigo-500 rounded-lg flex items-center justify-center text-white font-bold text-xl shadow-lg shadow-blue-500/20">
                            K
                        </div>
                        <span className="text-xl font-bold tracking-tight text-gray-900 dark:text-white">KYR</span>
                    </div>

                    <div className="hidden md:flex items-center gap-8">
                        {['Product', 'Use Cases', 'Pricing', 'Resources'].map((item) => (
                            <a key={item} href={`#${item.toLowerCase().replace(' ', '-')}`} className="text-sm font-medium text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white transition-colors">
                                {item}
                            </a>
                        ))}
                    </div>

                    <div className="flex items-center gap-4">
                        <button
                            onClick={() => setIsLoginOpen(true)}
                            className="text-sm font-semibold text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                        >
                            Sign In
                        </button>
                        <button
                            onClick={handleStart}
                            className="bg-gray-900 hover:bg-gray-800 dark:bg-white dark:hover:bg-gray-100 text-white dark:text-gray-900 px-6 py-2.5 rounded-full font-medium text-sm transition-all hover:shadow-lg hover:shadow-gray-500/20 active:scale-95"
                        >
                            Get Started
                        </button>
                    </div>
                </div>
            </nav>

            {/* Hero Section */}
            <header className="relative pt-32 pb-32 overflow-hidden">
                <div className="relative z-10 max-w-7xl mx-auto px-6 text-center">
                    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 text-sm font-medium mb-8 border border-blue-100 dark:border-blue-800/50">
                        <span className="relative flex h-2 w-2">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
                        </span>
                        KYR: Know Your Repo
                    </div>

                    <h1 className="text-5xl md:text-7xl font-bold tracking-tight text-gray-900 dark:text-white mb-8 max-w-5xl mx-auto leading-tight">
                        Experience liftoff with <br className="hidden md:block" />
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 animate-gradient-x">
                            Know Your Repo
                        </span>
                    </h1>

                    <p className="text-xl text-gray-600 dark:text-gray-400 max-w-2xl mx-auto mb-12 leading-relaxed">
                        Navigate, analyze, and master any codebase in seconds.
                        The first AI-native architecture platform built for speed.
                    </p>

                    <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                        <button
                            onClick={handleStart}
                            className="w-full sm:w-auto px-8 py-4 bg-blue-600 hover:bg-blue-700 text-white rounded-full font-semibold text-lg transition-all shadow-xl shadow-blue-500/30 flex items-center justify-center gap-2 hover:-translate-y-1"
                        >
                            Analyze Repo Now <ArrowRight className="w-5 h-5" />
                        </button>
                        <button className="w-full sm:w-auto px-8 py-4 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-200 border border-gray-200 dark:border-gray-700 rounded-full font-semibold text-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-all">
                            View Demo
                        </button>
                    </div>
                </div>
            </header>

            {/* Features Section */}
            <section id="product" className="py-24 bg-gray-50 dark:bg-gray-900/50 relative overflow-hidden">
                <div className="max-w-7xl mx-auto px-6">
                    <div className="text-center mb-20">
                        <h2 className="text-3xl md:text-5xl font-bold text-gray-900 dark:text-white mb-6">
                            Everything you need to <br />understand code instantly.
                        </h2>
                        <p className="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
                            Stop spending hours reading documentation. KYR ingests repositories
                            and creates a spatial map of your software architecture.
                        </p>
                    </div>

                    <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                        <FeatureCard
                            icon={Layers}
                            title="Architectural Maps"
                            description="Visualize dependencies, data flows, and component hierarchies in interactive 3D graphs."
                            badge="Core Engine"
                        />
                        <FeatureCard
                            icon={Brain}
                            title="Contextual Intelligence"
                            description="AI that understands your specific coding patterns, not just generic syntax."
                        />
                        <FeatureCard
                            icon={Zap}
                            title="Instant Navigation"
                            description="Jump between files based on logical connections, not just file paths."
                        />
                        <FeatureCard
                            icon={Coins}
                            title="Token-Based Access"
                            description="Flexible pay-as-you-go model. Only pay for the compute you actually use."
                            badge="New"
                        />
                    </div>
                </div>
            </section>

            {/* Token Pricing Section */}
            <section id="pricing" className="py-24 bg-white dark:bg-gray-950 border-t border-gray-100 dark:border-gray-800">
                <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center gap-16">
                    <div className="flex-1">
                        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-400 text-xs font-bold uppercase tracking-wider mb-6">
                            Flexible Pricing
                        </div>
                        <h2 className="text-4xl font-bold text-gray-900 dark:text-white mb-6">
                            Powered by Tokens.<br />
                            Built for Scale.
                        </h2>
                        <p className="text-lg text-gray-600 dark:text-gray-400 mb-8 leading-relaxed">
                            Forget expensive monthly seats. KYR's token-based model ensures you only pay
                            for the architectural analysis you need.
                        </p>

                        <div className="space-y-4 mb-8">
                            {[
                                '500 Free Tokens on Signup',
                                'Pay per Repo Analysis',
                                'Unlimited Chat Context',
                                'Enterprise-grade Security'
                            ].map((item, i) => (
                                <div key={i} className="flex items-center gap-3">
                                    <div className="flex-shrink-0 w-6 h-6 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
                                        <CheckCircle2 className="w-4 h-4 text-green-600 dark:text-green-400" />
                                    </div>
                                    <span className="text-gray-700 dark:text-gray-300 font-medium">{item}</span>
                                </div>
                            ))}
                        </div>

                        <button className="flex items-center gap-2 text-blue-600 dark:text-blue-400 font-bold hover:gap-4 transition-all">
                            View Token Packs <MoveRight className="w-5 h-5" />
                        </button>
                    </div>

                    {/* Visual representation of tokens */}
                    <div className="flex-1 relative">
                        <div className="relative z-10 bg-gradient-to-br from-gray-900 to-gray-800 dark:from-gray-800 dark:to-gray-900 rounded-3xl p-8 shadow-2xl border border-gray-700">
                            <div className="flex justify-between items-center mb-8">
                                <div>
                                    <p className="text-gray-400 text-sm">Current Balance</p>
                                    <p className="text-4xl font-mono font-bold text-white tracking-tight">2,450 <span className="text-amber-500 text-2xl">tokens</span></p>
                                </div>
                                <div className="w-12 h-12 bg-amber-500/20 rounded-full flex items-center justify-center">
                                    <Coins className="w-6 h-6 text-amber-400" />
                                </div>
                            </div>

                            <div className="space-y-4">
                                <div className="bg-white/5 rounded-xl p-4 flex justify-between items-center">
                                    <div className="flex items-center gap-3">
                                        <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center">
                                            <Layers className="w-4 h-4 text-blue-400" />
                                        </div>
                                        <div>
                                            <p className="text-white font-medium text-sm">Repo Analysis</p>
                                            <p className="text-gray-400 text-xs">facebook/react</p>
                                        </div>
                                    </div>
                                    <span className="text-red-400 font-mono text-sm">-50</span>
                                </div>
                                <div className="bg-white/5 rounded-xl p-4 flex justify-between items-center">
                                    <div className="flex items-center gap-3">
                                        <div className="w-8 h-8 rounded-lg bg-green-500/20 flex items-center justify-center">
                                            <Coins className="w-4 h-4 text-green-400" />
                                        </div>
                                        <div>
                                            <p className="text-white font-medium text-sm">Token Top-up</p>
                                            <p className="text-gray-400 text-xs">Credit Card</p>
                                        </div>
                                    </div>
                                    <span className="text-green-400 font-mono text-sm">+1000</span>
                                </div>
                            </div>

                            <button className="w-full mt-8 bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 rounded-xl transition-colors">
                                Buy Tokens
                            </button>
                        </div>

                        {/* Decorative glow behind the card */}
                        <div className="absolute -inset-4 bg-gradient-to-r from-blue-500 to-purple-500 rounded-3xl opacity-20 blur-2xl -z-10"></div>
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer className="bg-gray-50 dark:bg-gray-950 py-12 border-t border-gray-200 dark:border-gray-800">
                <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-6">
                    <p className="text-gray-500 text-sm">© 2026 KYR Inc. All rights reserved.</p>
                    <div className="flex gap-8">
                        {['Privacy', 'Terms', 'Security', 'Contact'].map(link => (
                            <a key={link} href="#" className="text-gray-500 hover:text-gray-900 dark:hover:text-white text-sm transition-colors">
                                {link}
                            </a>
                        ))}
                    </div>
                </div>
            </footer>
        </div>
    );
};

export default LandingPage;
