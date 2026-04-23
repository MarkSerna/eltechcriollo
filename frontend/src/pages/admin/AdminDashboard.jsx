import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Newspaper, 
  Rss, 
  Zap, 
  Timer, 
  TrendingUp, 
  RefreshCcw,
  CheckCircle2,
  ChevronRight,
  Play
} from 'lucide-react';

const AdminDashboard = () => {
  const [stats, setStats] = useState(null);
  const [aiHealth, setAiHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);

  useEffect(() => {
    fetchData();
    // Refresco automático cada 30 segundos
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const [resStats, resAi] = await Promise.all([
        axios.get('/api/stats'),
        axios.get('/api/ai-stats')
      ]);
      setStats(resStats.data);
      setAiHealth(resAi.data);
    } catch (err) {
      console.error("Error fetching admin stats", err);
    } finally {
      setLoading(false);
    }
  };

  const handleManualScan = async () => {
    if (scanning) return;
    setScanning(true);
    try {
      await axios.post('/api/scrape');
      // No esperamos al resultado ya que es asíncrono en backend
    } catch (err) {
      console.error("Error iniciando escaneo", err);
    } finally {
      // Feedback visual momentáneo
      setTimeout(() => {
        setScanning(false);
        fetchData();
      }, 2000);
    }
  };

  if (loading && !stats) {
    return (
      <div className="flex flex-col gap-8 animate-pulse">
        <div className="h-20 bg-slate-100 dark:bg-slate-900 rounded-3xl w-1/3"></div>
        <div className="grid grid-cols-4 gap-6">
          {[1,2,3,4].map(i => <div key={i} className="h-32 bg-slate-100 dark:bg-slate-900 rounded-3xl"></div>)}
        </div>
        <div className="h-96 bg-slate-100 dark:bg-slate-900 rounded-3xl w-full"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in duration-700">
      {/* Header con Acción Principal */}
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-serif font-black text-slate-950 dark:text-white tracking-tighter uppercase leading-none">
            CENTRO DE<br/>INTELIGENCIA
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-[10px] font-black uppercase tracking-[0.2em] mt-3">
            Monitoreo en tiempo real del ecosistema autónomo
          </p>
        </div>
        <button 
          onClick={handleManualScan}
          disabled={scanning}
          className="bg-slate-950 dark:bg-primary-light text-white px-8 py-4 rounded-2xl font-black text-xs uppercase tracking-widest flex items-center gap-3 hover:scale-[1.02] active:scale-[0.98] transition-all shadow-2xl shadow-primary-light/20 disabled:opacity-50"
        >
          {scanning ? <RefreshCcw size={18} className="animate-spin" /> : <Play size={18} fill="currentColor" />}
          {scanning ? 'PROCESANDO...' : 'EJECUTAR ESCANEO'}
        </button>
      </header>

      {/* Grid de KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard 
          icon={<Newspaper className="text-blue-500" />}
          label="Noticias Hoy"
          value={stats?.articles_today}
          trend="Actividad detectada"
          color="blue"
        />
        <StatCard 
          icon={<Rss className="text-purple-500" />}
          label="Fuentes"
          value={stats?.sources_count}
          trend="Scrapers operativos"
          color="purple"
        />
        <StatCard 
          icon={<Zap className={aiHealth?.total > 0 ? "text-emerald-500" : "text-amber-500"} />}
          label="Salud IA (1h)"
          value={aiHealth?.total > 0 ? (aiHealth['429'] > 0 ? 'Limitado' : 'Óptimo') : 'Inactivo'}
          trend={`${aiHealth?.total || 0} llamadas / ${aiHealth?.['429'] || 0} errores`}
          color={aiHealth?.total > 0 ? (aiHealth['429'] > 0 ? 'amber' : 'emerald') : 'slate'}
        />
        <StatCard 
          icon={<Timer className="text-rose-500" />}
          label="Próximo Scan"
          value={stats?.next_scan ? new Date(stats.next_scan).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '--:--'}
          trend="Basado en Scheduler"
          color="rose"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* News Overview */}
        <div className="lg:col-span-2 bg-white dark:bg-slate-900 rounded-[2.5rem] border border-slate-200 dark:border-slate-800 p-10 shadow-2xl overflow-hidden relative">
          <div className="flex justify-between items-center mb-8 relative z-10">
            <div>
               <h3 className="text-xl font-serif font-black text-slate-950 dark:text-white uppercase tracking-tight">Última Actividad</h3>
               <p className="text-[9px] text-slate-400 font-black tracking-widest mt-1 uppercase">Top 5 publicaciones recientes</p>
            </div>
            <span className="flex items-center gap-2 text-[10px] font-black bg-emerald-100 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 px-4 py-1.5 rounded-full border border-emerald-200 dark:border-emerald-800/50">
              <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse"></span> LIVE
            </span>
          </div>
          
          <div className="space-y-4 relative z-10">
            {stats?.recent_articles?.map((article, idx) => (
              <div key={idx} className="flex items-center justify-between p-5 rounded-3xl bg-slate-50/50 dark:bg-slate-950/50 border border-slate-100 dark:border-slate-800/50 hover:border-primary-light/40 hover:bg-white dark:hover:bg-slate-900 transition-all group">
                <div className="flex items-center gap-5 overflow-hidden">
                  <div className="w-12 h-12 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-center justify-center text-primary-light shrink-0 group-hover:scale-105 transition-transform">
                    <TrendingUp size={24} />
                  </div>
                  <div className="truncate">
                    <p className="text-sm font-bold text-slate-900 dark:text-white truncate tracking-tight">{article.title}</p>
                    <p className="text-[10px] font-black text-primary-light uppercase tracking-tighter mt-0.5">{article.source_name}</p>
                  </div>
                </div>
                <ChevronRight className="w-5 h-5 text-slate-300 group-hover:text-primary-light transition-colors" />
              </div>
            ))}
          </div>
        </div>

        {/* System Diagnostics */}
        <div className="bg-slate-950 dark:bg-slate-900 rounded-[2.5rem] p-10 shadow-2xl flex flex-col justify-between border border-slate-900 dark:border-slate-800 relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-8 opacity-10 group-hover:opacity-20 transition-opacity">
             <RefreshCcw size={120} className="text-white animate-spin-slow" />
          </div>

          <div className="relative z-10">
            <div className="w-12 h-1.5 bg-primary-light mb-8 rounded-full"></div>
            <h3 className="text-2xl font-serif font-black text-white mb-4 leading-tight uppercase">Diagnóstico<br/>del Núcleo</h3>
            <p className="text-slate-500 dark:text-slate-400 text-xs leading-relaxed font-medium">El Tech Criollo opera actualmente sobre un motor autónomo 100% asíncrono.</p>
          </div>

          <div className="space-y-6 pt-12 relative z-10">
            <DiagnosticRow label="Conexión BD" status="Estable" color="emerald" />
            <DiagnosticRow label="Bot Telegram" status="Activo" color="emerald" />
            <DiagnosticRow label="Semaforo IA" status="2 RPM" color="amber" />
            <DiagnosticRow label="Motor IA" status={aiHealth?.total > 0 ? "Ollama/Gemini" : "N/A"} color="blue" />
          </div>
        </div>
      </div>
    </div>
  );
};

const StatCard = ({ icon, label, value, trend, color }) => (
  <div className="bg-white dark:bg-slate-950 p-8 rounded-[2rem] border border-slate-200 dark:border-slate-800 shadow-xl hover:shadow-2xl hover:translate-y-[-4px] transition-all group overflow-hidden relative">
    <div className="absolute -right-4 -bottom-4 opacity-[0.03] group-hover:opacity-[0.08] transition-opacity transform group-hover:scale-125 duration-500">
      {React.cloneElement(icon, { size: 120 })}
    </div>
    
    <div className="w-14 h-14 rounded-2xl bg-neutral-50 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 flex items-center justify-center mb-6 shadow-inner group-hover:bg-white dark:group-hover:bg-slate-800 transition-colors">
      {React.cloneElement(icon, { size: 28 })}
    </div>
    <p className="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-2">{label}</p>
    <h4 className="text-4xl font-black text-slate-950 dark:text-white tracking-tighter mb-3">{value || '--'}</h4>
    <p className="text-[11px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-tight flex items-center gap-2">
      <CheckCircle2 size={14} className="text-emerald-500" /> {trend}
    </p>
  </div>
);

const DiagnosticRow = ({ label, status, color }) => {
  const colors = {
    emerald: 'text-emerald-400',
    amber: 'text-amber-400',
    blue: 'text-blue-400'
  };
  return (
    <div className="flex items-center justify-between border-b border-white/5 pb-3 last:border-0 last:pb-0">
      <span className="text-[10px] font-black text-slate-500 dark:text-slate-500 uppercase tracking-widest">{label}</span>
      <span className={`text-[10px] font-black uppercase tracking-widest ${colors[color] || 'text-white'}`}>{status}</span>
    </div>
  );
};

export default AdminDashboard;
