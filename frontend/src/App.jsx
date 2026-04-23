import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Routes, Route, useLocation, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import NewsAdmin from './pages/NewsAdmin';
import AdminLayout from './layouts/AdminLayout';
import LoginPage from './pages/LoginPage';
import AdminDashboard from './pages/admin/AdminDashboard';
import AdminSources from './pages/admin/AdminSources';
import AdminDictionary from './pages/admin/AdminDictionary';
import AdminLogs from './pages/admin/AdminLogs';
import AdminSecurity from './pages/admin/AdminSecurity';

function App() {
  const [user, setUser] = useState({ authenticated: false, username: '' });
  const [authLoading, setAuthLoading] = useState(true);
  const location = useLocation();

  useEffect(() => {
    checkAuth();
  }, [location.pathname]);

  const checkAuth = async () => {
    try {
      const res = await axios.get('/api/auth/me');
      setUser(res.data);
    } catch (err) {
      setUser({ authenticated: false, username: '' });
    } finally {
      setAuthLoading(false);
    }
  };

  const handleLoginSuccess = (userData) => {
    setUser({ authenticated: true, ...userData });
  };

  const handleLogout = async () => {
    try {
      await axios.get('/api/logout');
      setUser({ authenticated: false, username: '' });
      // Forzamos redirección al portal público tras cerrar sesión
      window.location.href = '/';
    } catch (err) {
      console.error("Logout failed", err);
    }
  };

  // Evitar parpadeos mientras se verifica la sesión
  if (authLoading) return null;

  const isAdminRoute = location.pathname.startsWith('/admin');
  const isLoginRoute = location.pathname === '/login';

  return (
    <div className="min-h-screen transition-colors duration-300">
      {/* 
        El Navbar solo aparece en el portal público. 
        El área administrativa tiene su propio Sidebar dentro del AdminLayout.
      */}
      {!isAdminRoute && !isLoginRoute && (
        <Navbar 
          isAdmin={user.authenticated} 
          onLoginClick={() => window.location.href = '/login'} 
        />
      )}
      
      <Routes>
        {/* --- Rutas Públicas --- */}
        <Route path="/" element={<Dashboard />} />
        
        <Route path="/login" element={
          user.authenticated ? <Navigate to="/admin" replace /> : <LoginPage onLoginSuccess={handleLoginSuccess} />
        } />

        {/* --- Rutas Administrativas (Protegidas) --- */}
        <Route path="/admin" element={<AdminLayout user={user} onLogout={handleLogout} />}>
          <Route index element={<AdminDashboard />} />
          <Route path="news" element={<NewsAdmin />} />
          <Route path="sources" element={<AdminSources />} />
          <Route path="dictionary" element={<AdminDictionary />} />
          <Route path="logs" element={<AdminLogs />} />
          <Route path="security" element={<AdminSecurity />} />
        </Route>

        {/* --- Fallback a Home --- */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>

      {/* Footer solo para el portal público */}
      {!isAdminRoute && !isLoginRoute && (
        <footer className="bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 py-12 transition-colors duration-300">
          <div className="max-w-7xl mx-auto px-4 text-center">
            <div className="flex items-center justify-center gap-3 mb-6">
              <img 
                src="/static/logo-v2.png" 
                alt="El Tech Criollo Logo" 
                className="h-10 w-auto opacity-90 hover:opacity-100 transition-opacity dark:brightness-110"
              />
              <span className="font-serif font-black text-xl dark:text-white tracking-tighter uppercase">EL TECH CRIOLLO</span>
            </div>
            <p className="text-slate-500 dark:text-slate-400 text-sm max-w-md mx-auto font-medium">
              Inteligencia artificial aplicada al ecosistema tecnológico colombiano. 
              Curaduría humana, velocidad de IA.
            </p>
            <div className="mt-8 pt-8 border-t border-slate-100 dark:border-slate-800 text-slate-400 text-[10px] uppercase tracking-widest font-black">
              © 2026 El Tech Criollo • Hecho en Colombia
            </div>
          </div>
        </footer>
      )}
    </div>
  );
}

export default App;
