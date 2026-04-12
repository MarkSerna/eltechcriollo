import sqlite3
from typing import Optional
from modules.utils.logger import logger
from modules.models.config import config

class DatabaseManager:
    """Clase para el manejo de la persistencia de los links extraídos."""
    
    def __init__(self):
        self.db_path = config.paths.db_path
        
    def _get_connection(self) -> Optional[sqlite3.Connection]:
        """Obtiene una conexión limpia de SQLite."""
        try:
            return sqlite3.connect(self.db_path)
        except sqlite3.Error as e:
            logger.error(f"Error conectando a SQLite en {self.db_path}: {e}")
            return None

    def initialize_schema(self) -> None:
        """Inicializa la base de datos y crea la tabla si no existe."""
        conn = self._get_connection()
        if not conn:
            return
            
        try:
            with conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS articles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT,
                        url TEXT UNIQUE NOT NULL,
                        source TEXT,
                        region TEXT,
                        ai_comment TEXT,
                        reel_script TEXT,
                        image_url TEXT,
                        processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
            logger.debug("Esquema de base de datos verificado e inicializado.")
        except sqlite3.Error as e:
            logger.error(f"Error inicializando el esquema: {e}")
        finally:
            conn.close()

    def is_processed(self, url: str) -> bool:
        """Verifica si un enlace ha sido insertado previamente."""
        conn = self._get_connection()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM articles WHERE url = ?", (url,))
            return cursor.fetchone() is not None
        except sqlite3.Error as e:
            logger.error(f"Error verificando enlace {url}: {e}")
            return False
        finally:
            conn.close()

    def mark_as_processed(self, article) -> bool:
        """Inserta un artículo enriquecido en la BD para evitar duplicados futuros."""
        conn = self._get_connection()
        if not conn:
            return False
            
        try:
            with conn:
                conn.execute(
                    "INSERT INTO articles (title, url, source, region, ai_comment, reel_script, image_url) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                    (article.title, article.link, article.source_name, article.region, article.ai_comment, article.reel_script, article.image_url)
                )
            return True
        except sqlite3.IntegrityError:
            # Ya existía el link
            return False
        except sqlite3.Error as e:
            logger.error(f"Error persistiendo artículo {article.link}: {e}")
            return False
        finally:
            conn.close()
            
    def get_todays_articles(self) -> list:
        """Retorna las noticias guardadas ordenadas cronológicamente."""
        conn = self._get_connection()
        if not conn:
            return []
            
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT title, url, source, region, ai_comment, reel_script, image_url, processed_at FROM articles ORDER BY processed_at DESC LIMIT 100")
            rows = cursor.fetchall()
            keys = ["title", "link", "source_name", "region", "ai_comment", "reel_script", "image_url", "processed_at"]
            return [dict(zip(keys, row)) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error obteniendo artículos de la DB: {e}")
            return []
        finally:
            conn.close()
