import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { Lock, User, AlertCircle, Loader2 } from 'lucide-react';

const LoginPage = ({ onLoginSuccess }) => {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      // Petición al nuevo endpoint JSON de login
      const res = await axios.post('/api/login', { username, password });
      if (res.data.status === 'ok') {
        onLoginSuccess(res.data.user);
        navigate('/admin');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error de conexión o credenciales');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950 px-4 transition-colors duration-500">
      <div className="max-w-md w-full">
        {/* Card de Login Premium */}
        <div className="bg-white dark:bg-slate-900 rounded-3xl shadow-2xl overflow-hidden border border-slate-200 dark:border-slate-800 animate-in fade-in zoom-in duration-500">
          <div className="p-8 sm:p-12">
            <div className="flex flex-col items-center mb-10 text-center">
              <div className="w-16 h-16 bg-primary-light rounded-2xl flex items-center justify-center text-white mb-6 shadow-xl shadow-primary-light/30">
                <Lock size={32} />
              </div>
              <h1 className="text-3xl font-serif font-black text-slate-900 dark:text-white tracking-tighter uppercase leading-none">
                CENTRO DE<br/>CONTROL
              </h1>
              <p className="text-slate-500 dark:text-slate-400 text-[10px] mt-4 font-black uppercase tracking-[0.2em]">
                Acceso Administrador Tech
              </p>
            </div>

            {error && (
              <div className="mb-6 p-4 bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/50 rounded-xl flex items-center gap-3 text-rose-600 dark:text-rose-400 text-sm animate-bounce-short">
                <AlertCircle size={18} />
                <span className="font-medium">{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-5">
              <div className="space-y-2">
                <label className="block text-[10px] font-black text-slate-400 uppercase tracking-[0.1em] px-1">Usuario</label>
                <div className="relative group">
                  <User className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-primary-light transition-colors" size={18} />
                  <input 
                    type="text" 
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="w-full pl-12 pr-4 py-4 rounded-2xl bg-neutral-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 focus:ring-2 focus:ring-primary-light transition-all text-slate-900 dark:text-white outline-none font-medium shadow-inner"
                    placeholder="Tu usuario"
                    required
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="block text-[10px] font-black text-slate-400 uppercase tracking-[0.1em] px-1">Contraseña</label>
                <div className="relative group">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-primary-light transition-colors" size={18} />
                  <input 
                    type="password" 
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-12 pr-4 py-4 rounded-2xl bg-neutral-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 focus:ring-2 focus:ring-primary-light transition-all text-slate-900 dark:text-white outline-none font-medium shadow-inner"
                    placeholder="••••••••"
                    required
                  />
                </div>
              </div>

              <div className="pt-2">
                <button 
                  type="submit" 
                  disabled={loading}
                  className="w-full py-4 bg-slate-900 dark:bg-primary-light text-white rounded-2xl font-black text-sm uppercase tracking-widest hover:scale-[1.01] active:scale-[0.98] transition-all flex items-center justify-center gap-2 shadow-xl shadow-primary-light/20 disabled:opacity-70 disabled:cursor-not-allowed"
                >
                  {loading ? <Loader2 className="animate-spin" size={20} /> : 'INICIAR SESIÓN'}
                </button>
              </div>
            </form>
          </div>
          
          <div className="p-6 bg-slate-50 dark:bg-black/20 border-t border-slate-100 dark:border-slate-800 text-center">
            <button 
              onClick={() => navigate('/')}
              className="text-[10px] font-black text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors uppercase tracking-[0.1em]"
            >
              ← Volver al Portal de noticias
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
