import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Coffee, Sun, Moon, Lock, Mail, Podcast, Cpu } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

const Navbar = ({ isAdmin, onLoginClick }) => {
  const { theme, toggleTheme } = useTheme();
  const [scrolled, setScrolled] = useState(false);
  const location = useLocation();

  const [currentDate, setCurrentDate] = useState('');

  useEffect(() => {
    const d = new Date();
    const days = ['DOMINGO', 'LUNES', 'MARTES', 'MIÉRCOLES', 'JUEVES', 'VIERNES', 'SÁBADO'];
    const months = ['ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO', 'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE'];
    
    const formatted = `${days[d.getDay()]}, ${d.getDate()} DE ${months[d.getMonth()]} DE ${d.getFullYear()}`;
    setCurrentDate(formatted);

    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 transition-all duration-300">
      {/* 🔝 Utility Bar (Black Style) */}
      <div className="bg-slate-950 text-[10px] sm:text-xs text-slate-300 py-1.5 px-4 sm:px-8 flex justify-between items-center border-b border-slate-800">
        <div className="hidden sm:flex items-center space-x-4">
          <span className="font-medium tracking-widest">{currentDate}</span>
          <span className="text-slate-600">|</span>
        </div>
        <div className="flex items-center space-x-4 ml-auto">
          {isAdmin ? (
            <span className="flex items-center gap-1 text-emerald-400 font-bold tracking-tighter">
              <Lock className="w-3 h-3" /> SESIÓN ACTIVA
            </span>
          ) : (
            <button onClick={onLoginClick} className="flex items-center gap-1 hover:text-white transition-colors font-bold tracking-tighter uppercase cursor-pointer">
              <Lock className="w-3 h-3" /> ACCESO
            </button>
          )}
          
          <button 
            onClick={toggleTheme}
            className="hover:text-white transition-colors p-1 cursor-pointer"
          >
            {theme === 'dark' ? <Moon className="w-3.5 h-3.5" /> : <Sun className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* 🏢 Main Header (Glassmorphism) */}
      <div className={`glass-morphism transition-all duration-500 ${scrolled ? 'py-2 shadow-xl' : 'py-5'}`}>
        <div className="max-w-7xl mx-auto px-4 flex justify-between items-center">
          {/* Logo Area */}
          <Link to="/" className="flex items-center space-x-3 group">
            <img 
              src="/static/logo-v2.png" 
              alt="El Tech Criollo Logo" 
              className="h-12 w-auto transform group-hover:scale-105 transition-transform duration-300 drop-shadow-sm dark:brightness-110"
            />
            <div className="flex flex-col">
              <span className="text-xl sm:text-2xl font-serif font-black tracking-tighter text-slate-900 dark:text-white leading-none transform group-hover:scale-105 transition-transform">
                EL TECH CRIOLLO
              </span>
              <span className="text-[8px] sm:text-[10px] tracking-[0.1em] text-slate-600 dark:text-slate-300 font-bold -mt-0.5 ml-0.5 uppercase">
                El futuro es ahora y es criollo
              </span>
            </div>
          </Link>
 
          {/* Main Navigation - Newsletter/Podcast */}
          <div className="hidden lg:flex items-center space-x-8">
            {isAdmin && (
               <Link to="/admin" className="text-[10px] font-black tracking-widest text-[#229ED9] hover:text-sky-400 transition-colors flex items-center gap-2 py-1 uppercase decoration-2 underline-offset-4">
                 <Cpu className="w-4 h-4" /> GESTIÓN TECH
               </Link>
            )}
            <a href="#" className="text-xs font-black tracking-widest text-slate-700 dark:text-slate-200 hover:text-primary-light transition-colors flex items-center gap-2 py-1">
              <Mail className="w-4 h-4" /> NEWSLETTER
            </a>
            <a href="#" className="text-xs font-black tracking-widest text-slate-700 dark:text-slate-200 hover:text-primary-light transition-colors flex items-center gap-2 py-1">
              <Podcast className="w-4 h-4" /> PODCAST
            </a>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
