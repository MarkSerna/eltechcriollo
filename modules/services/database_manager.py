from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, Text, String, DateTime, func
from sqlalchemy.pool import NullPool
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, List, Set, Dict, Any
from modules.utils.logger import logger
from modules.models.config import config

class DatabaseManager:
    """Clase para el manejo de la persistencia usando SQLAlchemy (soporta SQLite y PostgreSQL)."""
    
    def __init__(self):
        self.db_url = config.paths.database_url
        if not self.db_url:
            # Fallback a SQLite local
            db_path = config.paths.db_path
            self.db_url = f"sqlite:///{db_path}"
            logger.info(f"💾 Usando base de datos local (SQLite): {db_path}")
        else:
            # Limpieza básica para URLs de Supabase/Postgres
            if self.db_url.startswith("postgres://"):
                self.db_url = self.db_url.replace("postgres://", "postgresql://", 1)
            logger.info("☁️ Usando base de datos externa (PostgreSQL/Supabase)")

        try:
            # Si usamos el pooler de Supabase (puerto 6543), desactivamos el pooling local para evitar errores.
            if ":6543" in self.db_url:
                self.engine = create_engine(self.db_url, poolclass=NullPool)
                logger.debug("🔗 Conexión configurada en modo Pooler (NullPool).")
            else:
                self.engine = create_engine(self.db_url, pool_pre_ping=True)
            self.metadata = MetaData()
        except Exception as e:
            logger.error(f"Error creando el motor de base de datos: {e}")
            self.engine = None

    def initialize_schema(self) -> None:
        """Inicializa la base de datos y crea la tabla si no existe."""
        if not self.engine: 
            logger.error("❌ No se puede inicializar el esquema: El motor de DB no está listo.")
            return
        
        logger.info("🔍 Verificando esquema de base de datos...")
        
        query_create = """
        CREATE TABLE IF NOT EXISTS articles (
            id SERIAL PRIMARY KEY,
            title TEXT,
            url TEXT UNIQUE NOT NULL,
            source TEXT,
            region TEXT,
            department TEXT,
            ai_comment TEXT,
            reel_script TEXT,
            image_url TEXT,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        # Ajuste para SQLite (SERIAL no existe)
        if "sqlite" in self.db_url:
            query_create = query_create.replace("SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")

        try:
            with self.engine.begin() as conn:
                logger.debug("🔨 Ejecutando Query de creación de tabla...")
                conn.execute(text(query_create))
                
                # Gestión de columnas faltantes (migraciones simples)
                for col_name in ['image_url', 'region', 'department']:
                    try:
                        conn.execute(text(f"ALTER TABLE articles ADD COLUMN {col_name} TEXT"))
                        logger.info(f"🛠 Columna '{col_name}' añadida exitosamente.")
                    except Exception:
                        # Probablemente ya existe
                        pass
                        
            logger.info("✅ Esquema de base de datos verificado y listo.")
        except SQLAlchemyError as e:
            logger.error(f"❌ Error crítico inicializando el esquema: {e}")

    def is_processed(self, url: str) -> bool:
        """Verifica si un enlace ha sido insertado previamente."""
        if not self.engine: return False
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1 FROM articles WHERE url = :url"), {"url": url})
                return result.fetchone() is not None
        except SQLAlchemyError as e:
            logger.error(f"Error verificando enlace {url}: {e}")
            return False

    def get_processed_urls(self, urls: List[str]) -> Set[str]:
        """Devuelve un set con las URLs que ya están en la BD."""
        if not self.engine or not urls: return set()
        try:
            with self.engine.connect() as conn:
                query = text("SELECT url FROM articles WHERE url IN :urls")
                # SQL Alchemy requiere una tupla para IN clausulas con bindparams
                result = conn.execute(query, {"urls": tuple(urls)})
                return {row[0] for row in result.fetchall()}
        except SQLAlchemyError as e:
            logger.error(f"Error en consulta batch de enlaces: {e}")
            return set()

    def mark_as_processed(self, article) -> bool:
        """Inserta un artículo enriquecido en la BD."""
        if not self.engine: return False
        try:
            with self.engine.begin() as conn:
                query = text("""
                    INSERT INTO articles (title, url, source, region, department, ai_comment, reel_script, image_url)
                    VALUES (:title, :url, :source, :region, :department, :ai_comment, :reel_script, :image_url)
                """)
                conn.execute(query, {
                    "title": article.title,
                    "url": article.link,
                    "source": article.source_name,
                    "region": article.region,
                    "department": article.department,
                    "ai_comment": article.ai_comment,
                    "reel_script": article.reel_script,
                    "image_url": article.image_url
                })
            return True
        except SQLAlchemyError as e:
            # Capturar errores de integridad (duplicados) discretamente
            logger.debug(f"Artículo ya existía o error de integridad: {article.link}")
            return False

    def get_todays_articles(self) -> List[Dict[str, Any]]:
        """Retorna las noticias guardadas ordenadas cronológicamente."""
        if not self.engine: return []
        try:
            with self.engine.connect() as conn:
                query = text("""
                    SELECT title, url, source, region, department, ai_comment, reel_script, image_url, processed_at 
                    FROM articles ORDER BY processed_at DESC LIMIT 150
                """)
                rows = conn.execute(query).fetchall()
                keys = ["title", "link", "source_name", "region", "department",
                        "ai_comment", "reel_script", "image_url", "processed_at"]
                return [dict(zip(keys, row)) for row in rows]
        except SQLAlchemyError as e:
            logger.error(f"Error obteniendo artículos de la DB: {e}")
            return []
