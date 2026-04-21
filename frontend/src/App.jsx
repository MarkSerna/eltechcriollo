import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';

function App() {
  const [user, setUser] = useState({ authenticated: false, username: '' });

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const res = await axios.get('/api/auth/me');
      setUser(res.data);
    } catch (err) {
      console.error("Auth check failed", err);
    }
  };

  const handleLogin = () => {
    // For now, redirect to the legacy login or we can implement a modal later
    window.location.href = '/login';
  };

  return (
    <div className="min-h-screen transition-colors duration-300">
      <Navbar 
        isAdmin={user.authenticated} 
        onLoginClick={handleLogin} 
      />
      
      <Dashboard />

      <footer className="bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 py-12 transition-colors duration-300">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <div className="flex items-center justify-center gap-3 mb-6">
            <img 
              src="/static/logo-v2.png" 
              alt="El Tech Criollo Logo" 
              className="h-10 w-auto opacity-90 hover:opacity-100 transition-opacity dark:brightness-110"
            />
            <span className="font-serif font-black text-xl dark:text-white tracking-tighter">EL TECH CRIOLLO</span>
          </div>
          <p className="text-slate-500 text-sm max-w-md mx-auto">
            Inteligencia artificial aplicada al ecosistema tecnológico colombiano. 
            Curaduría humana, velocidad de IA.
          </p>
          <div className="mt-8 pt-8 border-t border-slate-100 dark:border-slate-800 text-slate-400 text-[10px] uppercase tracking-widest font-bold">
            © 2026 El Tech Criollo • Hecho en Colombia
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
