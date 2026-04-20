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
        self.db_fallback_enabled = config.paths.db_fallback
        self.engine = None
        
        if self.db_url:
            # Limpieza básica para URLs de Supabase/Postgres
            if self.db_url.startswith("postgres://"):
                self.db_url = self.db_url.replace("postgres://", "postgresql://", 1)
            
            self.table_name = "public.articles"
            try:
                # Si usamos el pooler de Supabase (puerto 6543 o pooler.supabase), usar NullPool
                if ":6543" in self.db_url or "pooler.supabase" in self.db_url:
                    self.engine = create_engine(self.db_url, poolclass=NullPool)
                else:
                    self.engine = create_engine(self.db_url, pool_pre_ping=True)
                
                # Probar la conexión inmediatamente y mapear tablas
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                    # DEBUG: Listar tablas existentes en public
                    res = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
                    tables = [row[0] for row in res.fetchall()]
                    logger.info(f"☁️ Conexión Supabase OK. Tablas en 'public': {tables}")
                logger.info("☁️ Conexión persistente con Supabase establecida correctamente.")
            except Exception as e:
                if self.db_fallback_enabled:
                    logger.warning(f"⚠️ Error de conexión a DB externa: {e}. Activando fallo seguro a SQLite...")
                    self.db_url = None # Fuerza el fallback abajo
                else:
                    logger.error(f"❌ Error fatal de conexión a DB externa (Fallback desactivado): {e}")
                    raise e

        if not self.db_url:
            # Fallback a SQLite local
            db_path = config.paths.db_path
            self.db_url = f"sqlite:///{db_path}"
            self.table_name = "articles"
            self.engine = create_engine(self.db_url)
            logger.info(f"💾 Usando base de datos local (SQLite): {db_path}")

        self.metadata = MetaData()

    def initialize_schema(self) -> None:
        """Inicializa la base de datos y crea la tabla si no existe."""
        if not self.engine: 
            logger.error("❌ No se puede inicializar el esquema: El motor de DB no está listo.")
            return
        
        logger.info("🔍 Verificando esquema de base de datos...")
        
        query_create = f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
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
            # 1. Crear tabla base
            with self.engine.begin() as conn:
                logger.debug("🔨 Verificando/Creando tabla base...")
                conn.execute(text(query_create))
            
            # 2. Gestión de columnas faltantes (migraciones simples)
            is_postgres = "postgresql" in self.db_url
            for col_name in ['image_url', 'region', 'department']:
                try:
                    if is_postgres:
                        # PostgreSQL soporta ADD COLUMN IF NOT EXISTS (9.6+)
                        with self.engine.begin() as conn:
                            conn.execute(text(f"ALTER TABLE {self.table_name} ADD COLUMN IF NOT EXISTS {col_name} TEXT"))
                    else:
                        # SQLite no soporta IF NOT EXISTS en ALTER TABLE, usamos try/except individual
                        with self.engine.begin() as conn:
                            conn.execute(text(f"ALTER TABLE {self.table_name} ADD COLUMN {col_name} TEXT"))
                except Exception:
                    # Probablemente la columna ya existe
                    logger.debug(f"ℹ️ Columna '{col_name}' ya presente o no se pudo añadir.")
                    pass
            
            # 3. Verificación final (en una conexión limpia)
            with self.engine.connect() as conn:
                if is_postgres:
                    res = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
                    tables = [row[0] for row in res.fetchall()]
                    logger.info(f"🔍 [POST-INIT] Tablas actuales en public: {tables}")
                else:
                    logger.info("✅ Esquema de base de datos verificado y listo.")
                    
        except SQLAlchemyError as e:
            logger.error(f"❌ Error crítico inicializando el esquema: {e}")

    def is_processed(self, url: str) -> bool:
        """Verifica si un enlace ha sido insertado previamente."""
        if not self.engine: return False
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(f"SELECT 1 FROM {self.table_name} WHERE url = :url"), {"url": url})
                return result.fetchone() is not None
        except SQLAlchemyError as e:
            logger.error(f"Error verificando enlace {url}: {e}")
            return False

    def get_processed_urls(self, urls: List[str]) -> Set[str]:
        """Devuelve un set con las URLs que ya están en la BD."""
        if not self.engine or not urls: return set()
        try:
            with self.engine.connect() as conn:
                query = text(f"SELECT url FROM {self.table_name} WHERE url IN :urls")
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
                query = text(f"""
                    INSERT INTO {self.table_name} (title, url, source, region, department, ai_comment, reel_script, image_url)
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
                query = text(f"""
                    SELECT title, url, source, region, department, ai_comment, reel_script, image_url, processed_at 
                    FROM {self.table_name} ORDER BY processed_at DESC LIMIT 150
                """)
                rows = conn.execute(query).fetchall()
                keys = ["title", "link", "source_name", "region", "department",
                        "ai_comment", "reel_script", "image_url", "processed_at"]
                return [dict(zip(keys, row)) for row in rows]
        except SQLAlchemyError as e:
            if self.table_name in str(e) and "does not exist" in str(e):
                logger.warning(f"⚠️ Tabla '{self.table_name}' no encontrada. Intentando crearla ahora...")
                self.initialize_schema()
                # Reintentar una vez tras inicializar
                try:
                    with self.engine.connect() as conn:
                        rows = conn.execute(query).fetchall()
                        return [dict(zip(keys, row)) for row in rows]
                except Exception:
                    pass
            logger.error(f"Error obteniendo artículos de la DB: {e}")
            return []
