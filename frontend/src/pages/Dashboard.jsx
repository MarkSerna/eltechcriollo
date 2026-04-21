import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Newspaper, Globe2, Cpu, MapPin, Search } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import NewsCard from '../components/NewsCard';
import NewsModal from '../components/NewsModal';

const Dashboard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // all, colombia, global, tech
  const [search, setSearch] = useState('');
  const [selectedArticle, setSelectedArticle] = useState(null);

  useEffect(() => {
    fetchNews();
  }, []);

  const fetchNews = async () => {
    try {
      const res = await axios.get('/api/news');
      setData(res.data);
      setLoading(false);
    } catch (err) {
      console.error("Error fetching news:", err);
      setLoading(false);
    }
  };

  if (loading) return (
    <div className="flex items-center justify-center min-h-screen bg-white dark:bg-slate-900">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-light"></div>
    </div>
  );

  const filteredArticles = data?.days_feed?.map(day => ({
    ...day,
    articles: day.articles.filter(a => {
      const matchesSearch = a.title.toLowerCase().includes(search.toLowerCase()) || 
                          a.source_name.toLowerCase().includes(search.toLowerCase());
      const matchesRegion = filter === 'all' || a.region === filter;
      return matchesSearch && matchesRegion;
    })
  })).filter(day => day.articles.length > 0);

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 transition-colors duration-300">
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-36 pb-20">
        
        {/* 🌃 News Header & Stats */}
        <div className="mb-14">
          <div>
            <h1 className="text-4xl md:text-7xl font-serif font-black tracking-tighter mb-4 text-slate-900 dark:text-white leading-tight">
              EL TECH <span className="italic text-primary-light">CRIOLLO</span>
            </h1>
            <p className="text-slate-500 dark:text-slate-400 font-black tracking-[0.3em] text-[10px] uppercase">
              Noticias con criterio, alma de café y visión de frontera
            </p>
          </div>
        </div>

        {/* 🔍 Search & Filters (Pill Style) */}
        <div className="flex flex-col md:flex-row gap-6 mb-16 items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-8">
          <div className="relative w-full md:w-[450px] group">
            <Search className="absolute left-5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 group-focus-within:text-primary-light transition-colors" />
            <input 
              type="text" 
              placeholder="Explorar el ecosistema digital..."
              className="w-full pl-14 pr-6 py-4 rounded-full bg-white dark:bg-slate-900 border-none ring-1 ring-slate-200 dark:ring-slate-800 focus:ring-2 focus:ring-primary-light transition-all text-sm text-slate-900 dark:text-white shadow-sm placeholder:text-slate-400 font-medium tracking-tight"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <div className="flex flex-wrap gap-2 justify-center">
            {[
              { id: 'all', label: 'TODO' },
              { id: 'colombia', label: 'COLOMBIA' },
              { id: 'global', label: 'GLOBAL' },
              { id: 'IA', label: 'IA & FUTURO' }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setFilter(tab.id)}
                className={`px-6 py-2.5 rounded-full text-[10px] font-black tracking-widest transition-all ${
                  filter === tab.id 
                    ? 'bg-black text-white dark:bg-white dark:text-black shadow-lg scale-105' 
                    : 'bg-slate-200/50 text-slate-500 dark:bg-slate-900/50 hover:bg-slate-200 dark:hover:bg-slate-800'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Featured Card */}
        {data.featured && !search && filter === 'all' && (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-12 relative h-[500px] rounded-3xl overflow-hidden group cursor-pointer shadow-2xl"
            onClick={() => setSelectedArticle(data.featured)}
          >
            <img 
              src={data.featured.image_url || 'https://images.unsplash.com/photo-1485827404703-89b55fcc595e?q=80&w=1200'} 
              className="absolute inset-0 w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
              alt="Featured"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-slate-900 via-slate-900/40 to-transparent" />
            <div className="absolute bottom-0 left-0 p-8 md:p-12 max-w-3xl">
              <span className="inline-block px-3 py-1 bg-primary-light text-white text-[10px] font-black tracking-widest uppercase rounded-full mb-4 shadow-lg">
                DESTACADO HOY • {data.featured.source_name}
              </span>
              <h1 className="text-3xl md:text-5xl font-black text-white leading-tight mb-4 tracking-tighter font-serif">
                {data.featured.title}
              </h1>
              <p className="text-slate-200 text-sm md:text-lg line-clamp-3 mb-6 font-medium leading-relaxed">
                {data.featured.ai_comment}
              </p>
            </div>
          </motion.div>
        )}

        {/* Main Feed */}
        <div className="space-y-16">
          {filteredArticles?.map((day, idx) => (
            <section key={day.date} className="animate-in fade-in slide-in-from-bottom-4 duration-500" style={{ animationDelay: `${idx * 100}ms` }}>
              <div className="flex items-center gap-4 mb-8">
                <h2 className="text-2xl font-black text-slate-800 dark:text-slate-100 tracking-tight font-serif uppercase italic underline decoration-primary-light decoration-4 underline-offset-8 transition-colors">
                  {day.label}
                </h2>
                <div className="h-px flex-1 bg-slate-200 dark:bg-slate-800" />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                {day.articles.map(article => (
                  <NewsCard 
                    key={article.id} 
                    article={article} 
                    onClick={(a) => setSelectedArticle(a)} 
                  />
                ))}
              </div>
            </section>
          ))}
        </div>

        {filteredArticles?.length === 0 && (
          <div className="text-center py-20">
            <div className="text-6xl mb-4">📭</div>
            <h3 className="text-xl font-bold dark:text-white">Sin resultados</h3>
            <p className="text-slate-500">Prueba con otra búsqueda o filtro.</p>
          </div>
        )}
      </main>

      {/* News Detail Modal */}
      <AnimatePresence>
        {selectedArticle && (
          <NewsModal 
            article={selectedArticle} 
            onClose={() => setSelectedArticle(null)} 
          />
        )}
      </AnimatePresence>
    </div>
  );
};

export default Dashboard;
