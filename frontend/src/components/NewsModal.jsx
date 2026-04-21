import React from 'react';
import { motion } from 'framer-motion';
import { X, ExternalLink, Calendar, MessageSquareQuote } from 'lucide-react';

const NewsModal = ({ article, onClose }) => {
  if (!article) return null;

  const rawDate = new Date(article.processed_at || article.created_at);
  const dateStr = !isNaN(rawDate.getTime()) 
    ? rawDate.toLocaleDateString('es-CO', { day: 'numeric', month: 'long', year: 'numeric' })
    : 'Reciente';

  const cleanText = article.ai_comment
    ? article.ai_comment
        .replace(/^"|"$/g, '')          // Remueve comillas al inicio/final
        .replace(/\*\*/g, '')           // Remueve negritas markdown
        .replace(/\*/g, '')             // Remueve asteriscos sueltos
        .replace(/^[\n\r\s]+/, '')      // Remueve espacios/saltos al inicio
    : '';

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.95, opacity: 0, y: 20 }}
        animate={{ scale: 1, opacity: 1, y: 0 }}
        exit={{ scale: 0.95, opacity: 0, y: 20 }}
        className="bg-white dark:bg-slate-900 w-full max-w-4xl lg:max-w-5xl max-h-[90vh] rounded-3xl overflow-hidden shadow-2xl relative flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button */}
        <button 
          onClick={onClose}
          className="absolute top-4 right-4 z-10 p-2 bg-black/20 hover:text-black/40 text-white rounded-full transition-colors backdrop-blur-md"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header Image */}
        <div className="relative h-72 sm:h-96 shrink-0">
          <img 
            src={article.image_url || 'https://images.unsplash.com/photo-1504711434969-e33886168f5c?q=80&w=1200'} 
            className="w-full h-full object-cover"
            alt={article.title}
          />
          <div className="absolute inset-0 bg-gradient-to-t from-white dark:from-slate-900 via-transparent to-transparent" />
        </div>

        {/* Content */}
        <div className="p-6 sm:p-12 overflow-y-auto">
          <div className="flex items-center gap-3 mb-6">
            <span className="px-3 py-1 bg-primary-light text-white text-[10px] font-black tracking-widest uppercase rounded-full">
              {article.source_name}
            </span>
            <div className="flex items-center gap-1.5 text-slate-400 dark:text-slate-500 text-[10px] font-bold uppercase tracking-wider">
              <Calendar className="w-3 h-3" />
              {dateStr}
            </div>
          </div>

          <h2 className="text-3xl sm:text-5xl font-serif font-black text-slate-900 dark:text-white leading-tight mb-8 tracking-tighter">
            {article.title}
          </h2>

          <div className="h-px w-20 bg-primary-light mb-10" />

          {cleanText && (
            <div className="prose dark:prose-invert max-w-none mb-12">
              <p className="text-slate-700 dark:text-slate-300 text-lg sm:text-xl leading-relaxed font-medium whitespace-pre-line first-letter:text-5xl first-letter:font-serif first-letter:font-black first-letter:mr-3 first-letter:float-left first-letter:text-primary-light">
                {cleanText}
              </p>
            </div>
          )}

          <div className="flex justify-end">
            <a 
              href={article.link} 
              target="_blank" 
              rel="noopener noreferrer"
              className="bg-slate-900 dark:bg-white text-white dark:text-slate-900 py-3 px-6 rounded-xl font-black text-[10px] tracking-widest flex items-center justify-center gap-2 hover:scale-[1.05] active:scale-[0.95] transition-all shadow-lg"
            >
              LEER NOTICIA COMPLETA
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default NewsModal;
