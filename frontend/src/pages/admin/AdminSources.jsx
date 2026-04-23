import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Globe, Search, ArrowUpRight } from 'lucide-react';

const AdminSources = () => {
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    fetchSources();
  }, []);

  const fetchSources = async () => {
    try {
      const res = await axios.get('/api/sources');
      setSources(res.data.sources);
    } catch (err) {
      console.error("Error fetching sources", err);
    } finally {
      setLoading(false);
    }
  };

  const filteredSources = sources.filter(s => 
    s.name.toLowerCase().includes(search.toLowerCase()) ||
    s.url.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-serif font-black text-slate-900 dark:text-white tracking-tighter uppercase leading-none">
            FUENTES DE<br/>INTELIGENCIA
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-[10px] font-black uppercase tracking-[0.2em] mt-3">
            Gestión de puntos de entrada de datos
          </p>
        </div>
        <div className="relative group">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-primary-light transition-colors" size={18} />
          <input 
            type="text" 
            placeholder="Buscar fuente..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-12 pr-6 py-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-sm outline-none focus:ring-2 focus:ring-primary-light transition-all w-full md:w-80 shadow-sm"
          />
        </div>
      </header>

      <div className="bg-white dark:bg-slate-900 rounded-[2.5rem] border border-slate-200 dark:border-slate-800 overflow-hidden shadow-2xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 dark:bg-slate-950 border-b border-slate-200 dark:border-slate-800">
                <th className="px-8 py-6 text-[10px] font-black uppercase tracking-widest text-slate-500">Fuente / URL</th>
                <th className="px-8 py-6 text-[10px] font-black uppercase tracking-widest text-slate-500">Clase</th>
                <th className="px-8 py-6 text-[10px] font-black uppercase tracking-widest text-slate-500">Cobertura</th>
                <th className="px-8 py-6 text-[10px] font-black uppercase tracking-widest text-slate-500 text-right">Estado Nodo</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {loading ? (
                Array(6).fill(0).map((_, i) => (
                  <tr key={i} className="animate-pulse">
                    <td colSpan="4" className="px-8 py-8 h-20 bg-slate-50/50 dark:bg-slate-900/50"></td>
                  </tr>
                ))
              ) : filteredSources.map((s, idx) => (
                <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors group">
                  <td className="px-8 py-6">
                    <div className="flex items-center gap-5">
                      <div className="w-12 h-12 rounded-2xl bg-slate-100 dark:bg-slate-950 flex items-center justify-center text-slate-400 group-hover:bg-white dark:group-hover:bg-slate-900 transition-colors">
                        <Globe size={24} />
                      </div>
                      <div>
                        <p className="text-sm font-bold text-slate-900 dark:text-white leading-tight">{s.name}</p>
                        <a 
                          href={s.url} 
                          target="_blank" 
                          rel="noreferrer" 
                          className="text-[10px] text-slate-400 hover:text-primary-light font-medium flex items-center gap-1 transition-colors mt-0.5"
                        >
                          {s.url.replace(/(^\w+:|^)\/\//, '').substring(0, 40)}...
                          <ArrowUpRight size={10} />
                        </a>
                      </div>
                    </div>
                  </td>
                  <td className="px-8 py-6">
                    <span className="px-4 py-1.5 bg-blue-50 dark:bg-blue-900/20 text-[#229ED9] text-[10px] font-black uppercase tracking-tighter rounded-full border border-blue-100 dark:border-blue-900/30">
                      {s.type}
                    </span>
                  </td>
                  <td className="px-8 py-6">
                    <div className="flex flex-col">
                       <span className="text-xs font-bold text-slate-600 dark:text-slate-300 capitalize">{s.region}</span>
                       <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest mt-1">Soberanía de Datos</span>
                    </div>
                  </td>
                  <td className="px-8 py-6 text-right">
                    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 text-[10px] font-black uppercase tracking-widest border border-emerald-100 dark:border-emerald-900/30">
                      <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.4)]"></span> Activo
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {filteredSources.length === 0 && !loading && (
          <div className="py-20 text-center text-slate-400">
            No se encontraron fuentes activas con ese criterio.
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminSources;
