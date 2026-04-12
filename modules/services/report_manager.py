import os
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from modules.utils.logger import logger
from modules.models.config import config
from modules.models.source import ScrapedArticle

class ReportManager:
    """Clase encargada de consolidar y formatear artículos en un reporte diario Markdown."""
    
    def __init__(self):
        self.reports_dir = config.paths.reports_dir

    def generate_markdown(self, articles: List[ScrapedArticle]) -> Optional[Path]:
        """Genera el texto Markdown si existen artículos novedosos y lo guarda en disco."""
        if not articles:
            logger.info("No hay artículos nuevos que requieran ser reportados.")
            return None

        today = datetime.now().strftime("%Y-%m-%d")
        report_filename = f"recap_diario_{today}.md"
        report_path = self.reports_dir / report_filename
        
        try:
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(f"# 📰 Recap El Tech Criollo - {today}\n\n")
                f.write(f"*Total extraídas para revisión:* {len(articles)}\n\n")
                f.write("---\n\n")
                
                for article in articles:
                    f.write(f"## {article.title}\n")
                    f.write(f"**🌐 Fuente:** _{article.source_name}_\n\n")
                    f.write(f"**🔗 Enlace:** [Visitar Noticia Original]({article.link})\n\n")
                    f.write(f"**✍ Comentario del Tech Criollo:** \n")
                    f.write(f">\n\n")
                    f.write(f"---\n")
                    
            logger.info(f"Reporte diario generado exitosamente en: {report_path}")
            return report_path
            
        except IOError as e:
            logger.error(f"No de pudo guardar el informe en {report_path}: {e}")
            return None
