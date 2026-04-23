import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Globe, Search, ArrowUpRight, Plus, Edit2, Trash2, X, Check, AlertCircle } from 'lucide-react';

const AdminSources = () => {
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  
  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [editId, setEditId] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    url: '',
    type: 'rss',
    region: 'global',
    require_ai: false
  });

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

  const handleOpenModal = (source = null) => {
    if (source) {
      setFormData(source);
      setEditId(source.id);
    } else {
      setFormData({
        name: '',
        url: '',
        type: 'rss',
        region: 'global',
        require_ai: false
      });
      setEditId(null);
    }
    setIsModalOpen(true);
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      if (editId !== null) {
        await axios.put(`/api/sources/${editId}`, formData);
      } else {
        await axios.post('/api/sources', formData);
      }
      await fetchSources();
      setIsModalOpen(false);
    } catch (err) {
      alert("Error al guardar la fuente. Revisa los logs.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("¿Estás seguro de eliminar esta fuente? Esto detendrá el escaneo de este sitio.")) return;
    try {
      await axios.delete(`/api/sources/${id}`);
      await fetchSources();
    } catch (err) {
      alert("Error al eliminar la fuente.");
    }
  };

  const filteredSources = sources.filter(s => 
      s.name.toLowerCase().includes(search.toLowerCase()) ||
      s.url.toLowerCase().includes(search.toLowerCase())
    );

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-4xl font-serif font-black text-slate-900 dark:text-white tracking-tighter uppercase leading-none">
            CENTRAL DE<br/>INTELIGENCIA
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-[10px] font-black uppercase tracking-[0.2em] mt-3 flex items-center gap-2">
            <span className="w-2 h-2 bg-primary-light rounded-full animate-pulse"></span>
            Gestión de puntos de entrada de datos
          </p>
        </div>
        
        <div className="flex flex-col sm:flex-row gap-3 w-full md:w-auto">
          <div className="relative group flex-grow">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-primary-light transition-colors" size={18} />
            <input 
              type="text" 
              placeholder="Buscar fuente..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-12 pr-6 py-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-sm outline-none focus:ring-2 focus:ring-primary-light transition-all w-full md:w-64 shadow-sm"
            />
          </div>
          <button 
            onClick={() => handleOpenModal()}
            className="flex items-center justify-center gap-2 px-6 py-4 bg-slate-900 dark:bg-white text-white dark:text-slate-900 rounded-2xl font-black text-[10px] uppercase tracking-widest hover:bg-primary-dark dark:hover:bg-slate-100 transition-all shadow-lg active:scale-95"
          >
            <Plus size={16} strokeWidth={3} />
            Nueva Fuente
          </button>
        </div>
      </header>

      <div className="bg-white dark:bg-slate-900 rounded-[2.5rem] border border-slate-200 dark:border-slate-800 overflow-hidden shadow-2xl transition-all">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 dark:bg-slate-950/50 border-b border-slate-200 dark:border-slate-800">
                <th className="px-8 py-6 text-[10px] font-black uppercase tracking-widest text-slate-400">Fuente / URL</th>
                <th className="px-8 py-6 text-[10px] font-black uppercase tracking-widest text-slate-400 text-center">Clase</th>
                <th className="px-8 py-6 text-[10px] font-black uppercase tracking-widest text-slate-400 text-center">IA</th>
                <th className="px-8 py-6 text-[10px] font-black uppercase tracking-widest text-slate-400">Cobertura</th>
                <th className="px-8 py-6 text-[10px] font-black uppercase tracking-widest text-slate-400 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {loading ? (
                Array(6).fill(0).map((_, i) => (
                  <tr key={i} className="animate-pulse">
                    <td colSpan="5" className="px-8 py-8 h-20 bg-slate-50/50 dark:bg-slate-900/50"></td>
                  </tr>
                ))
              ) : filteredSources.map((s) => (
                <tr key={s.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/30 transition-all group">
                  <td className="px-8 py-6">
                    <div className="flex items-center gap-5">
                      <div className="w-12 h-12 rounded-2xl bg-slate-100 dark:bg-slate-950 flex items-center justify-center text-slate-400 group-hover:bg-white dark:group-hover:bg-slate-900 transition-colors shadow-sm">
                        <Globe size={20} />
                      </div>
                      <div>
                        <p className="text-sm font-bold text-slate-900 dark:text-white leading-tight">{s.name}</p>
                        <a 
                          href={s.url} 
                          target="_blank" 
                          rel="noreferrer" 
                          className="text-[10px] text-slate-400 hover:text-primary-light font-medium flex items-center gap-1 transition-colors mt-0.5"
                        >
                          {s.url.replace(/(^\w+:|^)\/\//, '').substring(0, 30)}...
                          <ArrowUpRight size={10} />
                        </a>
                      </div>
                    </div>
                  </td>
                  <td className="px-8 py-6 text-center">
                    <span className="px-3 py-1 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 text-[9px] font-black uppercase tracking-tighter rounded-lg border border-slate-200 dark:border-slate-700">
                      {s.type}
                    </span>
                  </td>
                  <td className="px-8 py-6 text-center">
                    {s.require_ai ? (
                      <span className="inline-flex items-center gap-1 px-3 py-1 bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400 text-[9px] font-black uppercase tracking-widest rounded-lg border border-purple-100 dark:border-purple-900/30">
                        <Check size={10} strokeWidth={4} /> Forzada
                      </span>
                    ) : (
                      <span className="text-[9px] font-black text-slate-300 dark:text-slate-600 uppercase tracking-widest">Auto</span>
                    )}
                  </td>
                  <td className="px-8 py-6">
                    <div className="flex flex-col">
                       <span className="text-xs font-bold text-slate-600 dark:text-slate-300 capitalize">{s.region}</span>
                       <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest mt-1">Región de Nodo</span>
                    </div>
                  </td>
                  <td className="px-8 py-6">
                    <div className="flex justify-end gap-2">
                      <button 
                        onClick={() => handleOpenModal(s)}
                        className="p-3 text-slate-400 hover:text-primary-light hover:bg-white dark:hover:bg-slate-800 rounded-xl transition-all shadow-sm active:scale-90"
                        title="Editar Fuente"
                      >
                        <Edit2 size={16} />
                      </button>
                      <button 
                        onClick={() => handleDelete(s.id)}
                        className="p-3 text-slate-400 hover:text-red-500 hover:bg-white dark:hover:bg-slate-800 rounded-xl transition-all shadow-sm active:scale-90"
                        title="Eliminar Fuente"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {filteredSources.length === 0 && !loading && (
          <div className="py-24 text-center">
            <AlertCircle className="mx-auto text-slate-200 dark:text-slate-800 mb-4" size={48} />
            <p className="text-slate-400 font-medium">No se encontraron fuentes activas con ese criterio.</p>
          </div>
        )}
      </div>

      {/* Modal de Gestión */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-slate-900/80 backdrop-blur-sm" onClick={() => setIsModalOpen(false)}></div>
          <div className="relative bg-white dark:bg-slate-900 w-full max-w-lg rounded-[2.5rem] shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden animate-in zoom-in-95 duration-300">
            <div className="px-8 pt-8 pb-4 flex justify-between items-center border-b border-slate-100 dark:border-slate-800">
              <div>
                <h2 className="text-xl font-serif font-black text-slate-900 dark:text-white uppercase tracking-tight">
                  {editId !== null ? 'Editar Fuente' : 'Nueva Fuente'}
                </h2>
                <p className="text-[10px] text-slate-400 font-black uppercase tracking-widest mt-1">Configuración de Nodo de Red</p>
              </div>
              <button 
                onClick={() => setIsModalOpen(false)}
                className="p-3 text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 rounded-2xl transition-colors"
              >
                <X size={20} />
              </button>
            </div>
            
            <form onSubmit={handleSave} className="p-8 space-y-6">
              <div className="grid grid-cols-1 gap-6">
                <div className="space-y-2">
                  <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Nombre Comercial</label>
                  <input 
                    required
                    type="text" 
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    placeholder="Ej: Forbes Tecnología"
                    className="w-full px-6 py-4 rounded-2xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-sm focus:ring-2 focus:ring-primary-light outline-none transition-all dark:text-white"
                  />
                </div>
                
                <div className="space-y-2">
                  <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Punto de Acceso (URL)</label>
                  <input 
                    required
                    type="url" 
                    value={formData.url}
                    onChange={(e) => setFormData({...formData, url: e.target.value})}
                    placeholder="https://ejemplo.com/rss"
                    className="w-full px-6 py-4 rounded-2xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-sm focus:ring-2 focus:ring-primary-light outline-none transition-all dark:text-white"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Clase de Protocolo</label>
                    <select 
                      value={formData.type}
                      onChange={(e) => setFormData({...formData, type: e.target.value})}
                      className="w-full px-6 py-4 rounded-2xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-sm focus:ring-2 focus:ring-primary-light outline-none transition-all dark:text-white appearance-none"
                    >
                      <option value="rss">RSS Feed</option>
                      <option value="wpapi">WordPress API</option>
                      <option value="html">HTML Scraper</option>
                      <option value="dynamic">Playwright</option>
                      <option value="mintic">MinTIC Bot</option>
                      <option value="sena">SENA Bot</option>
                    </select>
                  </div>
                  
                  <div className="space-y-2">
                    <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Radio de Cobertura</label>
                    <select 
                      value={formData.region}
                      onChange={(e) => setFormData({...formData, region: e.target.value})}
                      className="w-full px-6 py-4 rounded-2xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-sm focus:ring-2 focus:ring-primary-light outline-none transition-all dark:text-white appearance-none"
                    >
                      <option value="colombia">Colombia</option>
                      <option value="global">Global</option>
                    </select>
                  </div>
                </div>

                <div className="flex items-center gap-4 px-6 py-4 bg-slate-50 dark:bg-slate-950 rounded-2xl border border-slate-200 dark:border-slate-800 cursor-pointer group"
                     onClick={() => setFormData({...formData, require_ai: !formData.require_ai})}>
                  <div className={`w-6 h-6 rounded-lg flex items-center justify-center border-2 transition-all ${formData.require_ai ? 'bg-primary-light border-primary-light text-white' : 'border-slate-200 dark:border-slate-800'}`}>
                    {formData.require_ai && <Check size={14} strokeWidth={4} />}
                  </div>
                  <div>
                    <p className="text-xs font-bold text-slate-700 dark:text-slate-200 uppercase tracking-tight">Validación IA Obligatoria</p>
                    <p className="text-[9px] text-slate-400 uppercase tracking-widest mt-0.5">Ignora el filtro de palabras clave</p>
                  </div>
                </div>
              </div>

              <div className="pt-4 flex gap-3">
                <button 
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="flex-1 py-4 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 rounded-2xl font-black text-[10px] uppercase tracking-widest hover:bg-slate-200 dark:hover:bg-slate-700 transition-all"
                >
                  Cancelar
                </button>
                <button 
                  type="submit"
                  disabled={isSubmitting}
                  className="flex-1 py-4 bg-slate-900 dark:bg-white text-white dark:text-slate-900 rounded-2xl font-black text-[10px] uppercase tracking-widest hover:bg-primary-dark dark:hover:bg-slate-100 transition-all shadow-lg flex items-center justify-center gap-2"
                >
                  {isSubmitting ? (
                    <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
                  ) : (
                    <Check size={16} strokeWidth={3} />
                  )}
                  {editId !== null ? 'Actualizar' : 'Guardar Nodo'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminSources;
