import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Search, Tag, Cpu, BookMarked } from 'lucide-react';

const AdminDictionary = () => {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    fetchDict();
  }, []);

  const fetchDict = async () => {
    try {
      const res = await axios.get('/api/dictionary');
      setEntries(res.data.entries);
    } catch (err) {
      console.error("Error fetching dictionary", err);
    } finally {
      setLoading(false);
    }
  };

  const filtered = entries.filter(e => 
    e.entity.toLowerCase().includes(search.toLowerCase()) ||
    e.type.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 text-left">
        <div>
          <h1 className="text-3xl font-serif font-black text-slate-900 dark:text-white tracking-tighter uppercase leading-none">
            DICCIONARIO<br/>TECNOLÓGICO
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-[10px] font-black uppercase tracking-[0.2em] mt-3">
            Palabras clave y entidades que activan el análisis de IA
          </p>
        </div>
        <div className="relative group w-full md:w-80">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-primary-light transition-colors" size={18} />
          <input 
            type="text" 
            placeholder="Filtrar por entidad o tipo..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-12 pr-6 py-4 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-sm outline-none focus:ring-2 focus:ring-primary-light transition-all shadow-xl shadow-slate-100 dark:shadow-none"
          />
        </div>
      </header>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 pb-12">
        {loading ? (
          Array(12).fill(0).map((_, i) => (
            <div key={i} className="h-40 bg-white dark:bg-slate-900 rounded-3xl border border-slate-100 dark:border-slate-800 animate-pulse"></div>
          ))
        ) : filtered.map((entry, idx) => (
          <div key={idx} className="bg-white dark:bg-slate-900 p-6 rounded-[2rem] border border-slate-200 dark:border-slate-800 hover:border-primary-light/40 hover:translate-y-[-4px] transition-all group relative overflow-hidden shadow-sm">
            {/* Indicador visual de tipo */}
            <div className="flex justify-between items-start mb-6">
               <div className="w-10 h-10 rounded-2xl bg-neutral-50 dark:bg-slate-950 flex items-center justify-center text-slate-400 group-hover:text-primary-light transition-colors shadow-inner">
                 <BookMarked size={20} />
               </div>
               <span className="text-[9px] font-black text-[#229ED9] uppercase tracking-tighter bg-blue-50 dark:bg-blue-900/20 px-3 py-1 rounded-full border border-blue-100 dark:border-blue-900/30">
                 {entry.type}
               </span>
            </div>

            <h4 className="text-base font-bold text-slate-900 dark:text-white truncate mb-1">
              {entry.entity}
            </h4>
            <p className="text-[10px] text-slate-400 font-medium uppercase tracking-[0.1em]">Entidad de prioridad</p>

            <div className="mt-6 pt-6 border-t border-slate-50 dark:border-slate-800/50 flex items-center justify-between opacity-50 group-hover:opacity-100 transition-opacity">
               <div className="flex items-center gap-2">
                  <Cpu size={14} className="text-primary-light" />
                  <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Active IA Core</span>
               </div>
               <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full"></div>
            </div>
          </div>
        ))}
      </div>

      {filtered.length === 0 && !loading && (
        <div className="py-24 text-center">
          <BookMarked size={48} className="mx-auto text-slate-200 mb-4" />
          <p className="text-slate-500 font-medium italic">No se encontraron coincidencias en el diccionario.</p>
        </div>
      )}
    </div>
  );
};

export default AdminDictionary;
