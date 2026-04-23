import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Newspaper, 
  Rss, 
  BookOpen, 
  Terminal, 
  ShieldCheck, 
  LogOut,
  ChevronRight,
  Monitor
} from 'lucide-react';

const AdminSidebar = ({ onLogout }) => {
  const location = useLocation();

  const menuItems = [
    { icon: <LayoutDashboard size={20} />, label: 'Dashboard', path: '/admin' },
    { icon: <Newspaper size={20} />, label: 'Gestión News', path: '/admin/news' },
    { icon: <Rss size={20} />, label: 'Fuentes News', path: '/admin/sources' },
    { icon: <BookOpen size={20} />, label: 'Diccionario', path: '/admin/dictionary' },
    { icon: <Terminal size={20} />, label: 'Logs Sistema', path: '/admin/logs' },
    { icon: <ShieldCheck size={20} />, label: 'Seguridad', path: '/admin/security' },
  ];

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-slate-950 text-slate-400 border-r border-slate-800 z-50 flex flex-col transition-all duration-300">
      {/* Sidebar Header */}
      <div className="p-6 border-b border-slate-900 flex items-center gap-3">
        <div className="w-8 h-8 bg-primary-light rounded-lg flex items-center justify-center text-white font-black shadow-lg shadow-primary-light/20">
          A
        </div>
        <div>
          <h2 className="text-sm font-black text-white tracking-widest uppercase">Admin Hub</h2>
          <p className="text-[10px] text-slate-500 font-bold uppercase tracking-tighter">Gestión Autónoma</p>
        </div>
      </div>

      {/* Navigation Menu */}
      <nav className="flex-1 py-6 px-4 space-y-1 overflow-y-auto custom-scrollbar">
        {menuItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center justify-between px-4 py-3 rounded-xl transition-all duration-200 group ${
                isActive 
                  ? 'bg-primary-light/10 text-primary-light font-bold border border-primary-light/20 shadow-sm' 
                  : 'hover:bg-slate-900 hover:text-slate-200'
              }`}
            >
              <div className="flex items-center gap-3">
                <span className={`${isActive ? 'text-primary-light' : 'text-slate-500 group-hover:text-slate-300'} transition-colors`}>
                  {item.icon}
                </span>
                <span className="text-sm tracking-tight">{item.label}</span>
              </div>
              {isActive && <div className="w-1.5 h-1.5 rounded-full bg-primary-light shadow-[0_0_8px_rgba(37,99,235,0.6)]" />}
            </Link>
          );
        })}
      </nav>

      {/* Footer Actions */}
      <div className="p-4 border-t border-slate-900 space-y-2">
        <Link 
          to="/" 
          className="flex items-center gap-3 px-4 py-2.5 rounded-lg text-xs font-bold text-slate-500 hover:text-white hover:bg-slate-900 transition-all uppercase tracking-widest"
        >
          <Monitor size={16} /> Ver Portal
        </Link>
        <button
          onClick={onLogout}
          className="w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-xs font-bold text-rose-500 hover:bg-rose-500/10 transition-all uppercase tracking-widest"
        >
          <LogOut size={16} /> Cerrar Sesión
        </button>
      </div>
    </aside>
  );
};

export default AdminSidebar;
