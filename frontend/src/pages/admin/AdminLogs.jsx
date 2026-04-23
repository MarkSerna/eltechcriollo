import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Terminal, RefreshCcw, Clock } from 'lucide-react';

const AdminLogs = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const logContainerRef = useRef(null);

  useEffect(() => {
    fetchLogs();
    // Auto-refresh cada 15 segundos para monitoreo en vivo
    const interval = setInterval(fetchLogs, 15000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    // Auto-scroll al final cuando llegan nuevos logs
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs]);

  const fetchLogs = async () => {
    try {
      const res = await axios.get('/api/logs');
      setLogs(res.data.logs);
    } catch (err) {
      console.error("Error fetching logs", err);
    } finally {
      setLoading(false);
    }
  };

  const getLogColor = (line) => {
    if (line.includes('ERROR')) return 'text-rose-400 font-bold';
    if (line.includes('WARNING') || line.includes('WARN')) return 'text-amber-400';
    if (line.includes('INFO')) return 'text-blue-300';
    if (line.includes('SUCCESS') || line.includes('✅') || line.includes('FINALIZADA')) return 'text-emerald-400 font-bold';
    if (line.includes('🕷')) return 'text-purple-400';
    if (line.includes('🤖') || line.includes('IA')) return 'text-primary-light font-bold';
    return 'text-slate-400';
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500 flex flex-col h-[calc(100vh-160px)]">
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-serif font-black text-slate-900 dark:text-white tracking-tighter uppercase leading-none">
            LOGS DEL<br/>SISTEMA
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-[10px] font-black uppercase tracking-[0.2em] mt-3">
            Diagnóstico profundo y flujo de orquestación
          </p>
        </div>
        <div className="flex gap-3">
           <button 
             onClick={fetchLogs} 
             title="Refrescar logs"
             className="p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl hover:bg-slate-50 dark:hover:bg-slate-800 transition-all text-slate-500 dark:text-slate-400 shadow-sm group"
           >
             <RefreshCcw size={20} className="group-hover:rotate-180 transition-transform duration-500" />
           </button>
        </div>
      </header>

      {/* Terminal de Logs */}
      <div className="flex-1 bg-slate-950 dark:bg-slate-950 rounded-[2.5rem] border border-slate-900 shadow-2xl overflow-hidden flex flex-col relative max-h-[70vh]">
        {/* Header de la Terminal */}
        <div className="flex items-center justify-between px-8 py-4 bg-black/40 border-b border-white/5 shrink-0">
           <div className="flex items-center gap-4">
              <div className="flex gap-2">
                 <div className="w-3 h-3 rounded-full bg-rose-500/80"></div>
                 <div className="w-3 h-3 rounded-full bg-amber-500/80"></div>
                 <div className="w-3 h-3 rounded-full bg-emerald-500/80"></div>
              </div>
              <span className="text-[10px] font-black text-slate-600 uppercase tracking-widest border-l border-white/10 pl-4 py-1 flex items-center gap-2">
                <Terminal size={14} /> CLI_SUBSYSTEM
              </span>
           </div>
           <div className="flex items-center gap-6 text-[10px] font-black text-slate-600 uppercase tracking-widest">
              <div className="flex items-center gap-2">
                 <Clock size={12} /> {new Date().toLocaleTimeString()}
              </div>
              <div className="flex items-center gap-2 text-emerald-500">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span> STREAM_ACTIVE
              </div>
           </div>
        </div>
        
        {/* Contenido de los Logs */}
        <div 
          ref={logContainerRef}
          className="flex-1 p-8 font-mono text-xs overflow-y-auto space-y-1.5 custom-scrollbar-dark selection:bg-primary-light/40"
        >
          {loading && logs.length === 0 ? (
            <div className="flex items-center gap-3 text-slate-700 animate-pulse font-bold uppercase tracking-widest py-10">
               <RefreshCcw size={16} className="animate-spin" />
               Conectando con el buffer de salida...
            </div>
          ) : logs.map((line, idx) => (
            <div key={idx} className="group flex gap-6 hover:bg-white/5 py-1 px-4 -mx-4 rounded-md transition-colors border-l-2 border-transparent hover:border-primary-light/30">
              <span className="text-[10px] text-slate-800 select-none w-10 text-right font-black mono opacity-50">{idx + 1}</span>
              <span className={`${getLogColor(line)} leading-relaxed tracking-tight break-all`}>
                {line.replace(/\n$/, '')}
              </span>
            </div>
          ))}
          {logs.length === 0 && !loading && (
            <div className="flex flex-col items-center justify-center py-24 text-slate-800 space-y-4">
              <Terminal size={40} className="opacity-20" />
              <p className="italic uppercase tracking-[0.3em] text-[10px] font-black">Null Output: No hay eventos registrados hoy</p>
            </div>
          )}
        </div>

        {/* Footer Overlay */}
        <div className="absolute bottom-0 left-0 right-0 h-10 bg-gradient-to-t from-slate-950 to-transparent pointer-events-none opacity-50"></div>
      </div>
    </div>
  );
};

export default AdminLogs;
