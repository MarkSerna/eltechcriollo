import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ShieldCheck, UserPlus, Users, Lock, AlertCircle, CheckCircle2 } from 'lucide-react';

const AdminSecurity = () => {
  const [admins, setAdmins] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newAdmin, setNewAdmin] = useState({ username: '', password: '' });
  const [submitting, setSubmitting] = useState(false);
  const [msg, setMsg] = useState(null);

  useEffect(() => {
    fetchAdmins();
  }, []);

  const fetchAdmins = async () => {
    try {
      const res = await axios.get('/api/admins');
      setAdmins(res.data);
    } catch (err) {
      console.error("Error fetching admins", err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddAdmin = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setMsg(null);
    try {
      const res = await axios.post('/api/admins', newAdmin);
      if (res.data.success) {
        setMsg({ type: 'success', text: 'Administrador creado correctamente' });
        setNewAdmin({ username: '', password: '' });
        fetchAdmins();
      } else {
        setMsg({ type: 'error', text: 'No se pudo crear el administrador' });
      }
    } catch (err) {
      setMsg({ type: 'error', text: 'Fallo de conexión con el servicio de seguridad' });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-serif font-black text-slate-900 dark:text-white tracking-tighter uppercase leading-none">
            SEGURIDAD Y<br/>USUARIOS
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-[10px] font-black uppercase tracking-[0.2em] mt-3">
            Gestión de identidades y privilegios de acceso
          </p>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start pb-12">
        {/* Listado de Administradores */}
        <div className="bg-white dark:bg-slate-900 rounded-[2.5rem] border border-slate-200 dark:border-slate-800 p-10 shadow-2xl">
          <div className="flex items-center gap-4 mb-10">
            <div className="w-12 h-12 bg-primary-light/10 text-primary-light rounded-2xl flex items-center justify-center">
              <Users size={24} />
            </div>
            <h3 className="text-xl font-serif font-black text-slate-900 dark:text-white uppercase tracking-tight">Personal Autorizado</h3>
          </div>
          
          <div className="space-y-5">
            {loading ? (
              Array(3).fill(0).map((_, i) => (
                <div key={i} className="h-24 bg-slate-50/50 dark:bg-slate-950/50 rounded-3xl animate-pulse"></div>
              ))
            ) : admins.map((admin, idx) => (
              <div key={idx} className="flex items-center justify-between p-6 rounded-[2rem] bg-slate-50 dark:bg-slate-950 border border-slate-100 dark:border-slate-800 hover:border-primary-light/30 transition-all group shadow-sm">
                 <div className="flex items-center gap-5">
                    <div className="w-14 h-14 rounded-2xl bg-white dark:bg-slate-900 flex items-center justify-center text-slate-400 group-hover:text-primary-light group-hover:scale-105 transition-all shadow-inner border border-slate-100 dark:border-slate-800">
                       <ShieldCheck size={28} />
                    </div>
                    <div>
                       <p className="text-base font-bold text-slate-900 dark:text-white tracking-tight">{admin.username}</p>
                       <p className="text-[10px] text-slate-400 dark:text-slate-500 font-black uppercase tracking-widest mt-1">
                         Incorporado: {new Date(admin.created_at).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })}
                       </p>
                    </div>
                 </div>
                 <div className="flex items-center gap-2">
                   <div className="w-2 h-2 bg-emerald-500 rounded-full shadow-[0_0_8px_rgba(16,185,129,0.5)]"></div>
                   <span className="text-[10px] font-black text-emerald-600 dark:text-emerald-400 uppercase tracking-tighter">Activo</span>
                 </div>
              </div>
            ))}
          </div>
        </div>

        {/* Formulario de Creación */}
        <div className="bg-slate-950 dark:bg-slate-950 rounded-[2.5rem] p-10 shadow-2xl border border-slate-900 relative overflow-hidden group">
           {/* Background Decoration */}
           <div className="absolute -right-20 -bottom-20 opacity-[0.03] group-hover:opacity-[0.08] transition-opacity duration-1000 rotate-12">
              <Lock size={300} className="text-white" />
           </div>

           <div className="relative z-10">
             <div className="flex items-center gap-4 mb-10">
                <div className="w-12 h-12 bg-white/5 text-primary-light rounded-2xl flex items-center justify-center border border-white/5">
                  <UserPlus size={24} />
                </div>
                <h3 className="text-xl font-serif font-black text-white uppercase tracking-tight">Nuevo Administrador</h3>
              </div>

              {msg && (
                <div className={`mb-8 p-5 rounded-2xl flex items-center gap-4 text-sm animate-in slide-in-from-top-4 duration-300 ${
                  msg.type === 'success' 
                    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' 
                    : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                }`}>
                  {msg.type === 'success' ? <CheckCircle2 size={24} /> : <AlertCircle size={24} />}
                  <span className="font-bold tracking-tight">{msg.text}</span>
                </div>
              )}

              <form onSubmit={handleAddAdmin} className="space-y-8">
                 <div className="space-y-3">
                    <label className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] px-1">ID de Identidad</label>
                    <input 
                      type="text" 
                      value={newAdmin.username}
                      onChange={(e) => setNewAdmin({...newAdmin, username: e.target.value})}
                      className="w-full bg-slate-900 border border-white/5 rounded-2xl px-6 py-5 text-white text-sm outline-none focus:ring-2 focus:ring-primary-light transition-all shadow-inner"
                      placeholder="Nombre de usuario"
                      required
                    />
                 </div>
                 <div className="space-y-3">
                    <label className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] px-1">Clave Maestra</label>
                    <input 
                      type="password" 
                      value={newAdmin.password}
                      onChange={(e) => setNewAdmin({...newAdmin, password: e.target.value})}
                      className="w-full bg-slate-900 border border-white/5 rounded-2xl px-6 py-5 text-white text-sm outline-none focus:ring-2 focus:ring-primary-light transition-all shadow-inner"
                      placeholder="••••••••••••"
                      required
                    />
                 </div>
                 <div className="pt-4">
                   <button 
                     type="submit" 
                     disabled={submitting}
                     className="w-full bg-primary-light text-white py-5 rounded-2xl font-black text-xs uppercase tracking-widest shadow-2xl shadow-primary-light/20 hover:scale-[1.01] active:scale-[0.99] transition-all flex items-center justify-center gap-3 disabled:opacity-50"
                   >
                     {submitting ? <RefreshCcw size={18} className="animate-spin" /> : <ShieldCheck size={18} />}
                     CONCEDER ACCESO
                   </button>
                 </div>
              </form>
           </div>
        </div>
      </div>
    </div>
  );
};

export default AdminSecurity;
