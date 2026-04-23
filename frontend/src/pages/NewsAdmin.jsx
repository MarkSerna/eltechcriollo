import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { RefreshCcw, Send, CheckCircle2, AlertCircle, Search, Clock, ExternalLink } from 'lucide-react';

const NewsAdmin = () => {
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [processingUrls, setProcessingUrls] = useState(new Set());

  useEffect(() => {
    fetchNews();
  }, []);

  const fetchNews = async () => {
    setLoading(true);
    try {
      const res = await axios.get('/api/admin/news');
      setNews(res.data.news);
    } catch (err) {
      console.error("Error fetching admin news:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleReprocess = async (url) => {
    setProcessingUrls(prev => new Set(prev).add(url));
    try {
      await axios.post('/api/admin/reprocess', { url });
      // Refresh only this article or the whole list
      await fetchNews();
    } catch (err) {
      alert("Error al re-procesar: " + (err.response?.data?.error || err.message));
    } finally {
      setProcessingUrls(prev => {
        const next = new Set(prev);
        next.delete(url);
        return next;
      });
    }
  };

  const handlePublishTelegram = async (url) => {
    if (processingUrls.has(url)) return;
    setProcessingUrls(prev => new Set(prev).add(url));
    try {
      await axios.post('/api/admin/publish-telegram', { url });
      await fetchNews();
    } catch (err) {
      alert("Error al publicar: " + (err.response?.data?.error || err.message));
    } finally {
      setProcessingUrls(prev => {
        const next = new Set(prev);
        next.delete(url);
        return next;
      });
    }
  };

  const filteredNews = news.filter(item => 
    item.title.toLowerCase().includes(search.toLowerCase()) ||
    item.source_name.toLowerCase().includes(search.toLowerCase())
  );

  const isPlaceholder = (text) => text && text.includes("Análisis en progreso");

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 pt-28 pb-20 px-4 sm:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
          <div>
            <h1 className="text-3xl font-serif font-black text-slate-900 dark:text-white tracking-tight underline decoration-primary-light decoration-4 underline-offset-8">
              GESTIÓN DE CONTENIDOS
            </h1>
            <p className="text-slate-500 dark:text-slate-400 text-xs mt-4 uppercase tracking-[0.2em] font-bold">
              Control de calidad y notificaciones
            </p>
          </div>
          <div className="relative w-full md:w-96 group">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 group-focus-within:text-primary-light transition-colors" />
            <input 
              type="text" 
              placeholder="Buscar por título o fuente..."
              className="w-full pl-12 pr-4 py-3 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 focus:ring-2 focus:ring-primary-light transition-all text-sm shadow-sm placeholder:text-slate-400 font-medium tracking-tight text-slate-900 dark:text-white"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>

        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden shadow-xl animate-in fade-in duration-500">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 dark:bg-slate-950 border-b border-slate-200 dark:border-slate-800">
                  <th className="px-6 py-4 text-[10px] uppercase font-black tracking-widest text-slate-500">Noticia</th>
                  <th className="px-6 py-4 text-[10px] uppercase font-black tracking-widest text-slate-500">Fecha</th>
                  <th className="px-6 py-4 text-[10px] uppercase font-black tracking-widest text-slate-500">Estado IA</th>
                  <th className="px-6 py-4 text-[10px] uppercase font-black tracking-widest text-slate-500">Telegram</th>
                  <th className="px-6 py-4 text-[10px] uppercase font-black tracking-widest text-slate-500 text-right">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {loading && news.length === 0 ? (
                  Array(5).fill(0).map((_, i) => (
                    <tr key={i} className="animate-pulse">
                      <td colSpan="5" className="px-6 py-8 h-16 bg-slate-50/50 dark:bg-slate-900/50 text-center text-xs text-slate-400">Cargando noticias...</td>
                    </tr>
                  ))
                ) : filteredNews.map((item) => (
                  <tr key={item.link} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition-colors">
                    <td className="px-6 py-5 max-w-md">
                      <div className="flex flex-col gap-1">
                        <span className="text-sm font-bold text-slate-900 dark:text-slate-100 line-clamp-1">{item.title}</span>
                        <div className="flex items-center gap-2">
                           <span className="text-[10px] font-black text-primary-light uppercase tracking-tighter">{item.source_name}</span>
                           <a href={item.link} target="_blank" rel="noreferrer" className="text-slate-400 hover:text-primary-light transition-colors">
                             <ExternalLink className="w-3 h-3" />
                           </a>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-5 whitespace-nowrap">
                      <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400">
                        <Clock className="w-3 h-3" />
                        <span className="text-[11px] font-medium font-mono">{item.processed_at ? new Date(item.processed_at).toLocaleDateString('es-CO') : '---'}</span>
                      </div>
                    </td>
                    <td className="px-6 py-5">
                      {isPlaceholder(item.ai_comment) ? (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400 text-[10px] font-black uppercase tracking-tighter">
                          <AlertCircle className="w-3 h-3" /> ERROR IA
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400 text-[10px] font-black uppercase tracking-tighter">
                          <CheckCircle2 className="w-3 h-3" /> LISTO
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-5">
                      {item.telegram_sent ? (
                        <span className="inline-flex items-center gap-1.5 text-[#229ED9] animate-in slide-in-from-left-2 duration-300">
                          <Send className="w-4 h-4" />
                          <span className="text-[10px] font-black uppercase tracking-tighter">Enviado</span>
                        </span>
                      ) : (
                        <span className="text-slate-300 dark:text-slate-700">
                          <Send className="w-4 h-4" />
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-5 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button 
                          onClick={() => handleReprocess(item.link)}
                          disabled={processingUrls.has(item.link)}
                          className={`p-2.5 rounded-xl transition-all shadow-sm ${
                            isPlaceholder(item.ai_comment) 
                              ? 'bg-amber-100 text-amber-600 hover:bg-amber-200 dark:bg-amber-900/40 dark:text-amber-400' 
                              : 'bg-slate-100 text-slate-500 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-400'
                          } ${processingUrls.has(item.link) ? 'animate-spin opacity-50' : ''}`}
                          title="Volver a generar con IA"
                        >
                          <RefreshCcw className="w-4 h-4" />
                        </button>
                        <button 
                          onClick={() => handlePublishTelegram(item.link)}
                          disabled={item.telegram_sent || processingUrls.has(item.link)}
                          className={`p-2.5 rounded-xl transition-all shadow-sm ${
                            item.telegram_sent 
                              ? 'bg-slate-50 text-slate-200 dark:bg-slate-900 dark:text-slate-800 cursor-not-allowed' 
                              : 'bg-blue-50 text-[#229ED9] hover:bg-blue-100 dark:bg-blue-900/20 dark:hover:bg-blue-900/40'
                          } ${processingUrls.has(item.link) ? 'animate-pulse opacity-50' : ''}`}
                          title="Enviar a Telegram"
                        >
                          <Send className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {filteredNews.length === 0 && !loading && (
            <div className="py-20 text-center">
              <p className="text-slate-500 font-medium">No se encontraron noticias con esos criterios.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default NewsAdmin;
