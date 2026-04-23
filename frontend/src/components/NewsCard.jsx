import React from 'react';
import { ExternalLink, MessageSquareQuote, Calendar, Send } from 'lucide-react';
import { motion } from 'framer-motion';

const NewsCard = ({ article, onClick }) => {
  const { title, source_name, image_url, ai_comment, created_at, telegram_sent } = article;
  const rawDate = new Date(created_at);
  const isValidDate = !isNaN(rawDate.getTime());
  
  const dateStr = isValidDate 
    ? rawDate.toLocaleDateString('es-CO', { day: 'numeric', month: 'short' })
    : 'RECIENTE';

  return (
    <motion.div
      whileHover={{ y: -4 }}
      className="group relative overflow-hidden bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm hover:shadow-xl transition-all duration-300 cursor-pointer"
      onClick={() => onClick(article)}
    >
      {/* Image Container */}
      <div className="relative h-48 overflow-hidden">
        <img
          src={image_url || 'https://images.unsplash.com/photo-1504711434969-e33886168f5c?q=80&w=600'}
          alt={title}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
        />
        <div className="absolute top-3 left-3">
          <span className="px-3 py-1 bg-white/90 dark:bg-slate-900/90 backdrop-blur-sm text-[10px] font-bold uppercase tracking-widest rounded-full shadow-sm text-primary-light">
            {source_name}
          </span>
        </div>
        
        {telegram_sent && (
          <div className="absolute top-3 right-3" title="Enviado a Telegram">
            <div className="bg-[#229ED9] text-white p-1.5 rounded-full shadow-lg border border-white/20 animate-in zoom-in duration-300">
              <Send className="w-3.5 h-3.5" />
            </div>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-5">
        <div className="flex items-center gap-2 mb-3 text-slate-400 dark:text-slate-500">
          <Calendar className="w-3.5 h-3.5" />
          <span className="text-[11px] font-medium uppercase tracking-tight">{dateStr}</span>
        </div>

        <h3 className="text-lg font-extrabold text-slate-800 dark:text-slate-100 leading-tight mb-3 line-clamp-2 group-hover:text-primary-light transition-colors">
          {title}
        </h3>

        {ai_comment && (
          <div className="flex gap-2 p-3 bg-slate-50 dark:bg-slate-900/50 rounded-xl mb-4">
            <MessageSquareQuote className="w-4 h-4 text-primary-light flex-shrink-0 mt-0.5" />
            <p className="text-xs text-slate-600 dark:text-slate-400 line-clamp-3 italic leading-relaxed">
              "{ai_comment}"
            </p>
          </div>
        )}

        <div className="flex items-center justify-between mt-auto">
          <span className="text-[10px] font-bold text-slate-400 flex items-center gap-1">
            LECTURA RÁPIDA
          </span>
          <ExternalLink className="w-4 h-4 text-slate-300 group-hover:text-primary-light transition-colors" />
        </div>
      </div>
    </motion.div>
  );
};

export default NewsCard;
