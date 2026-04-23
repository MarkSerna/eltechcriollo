from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, Text, String, DateTime, func
from sqlalchemy.pool import NullPool
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, List, Set, Dict, Any
import bcrypt
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
            telegram_sent BOOLEAN DEFAULT FALSE,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        query_ai_logs = f"""
        CREATE TABLE IF NOT EXISTS ai_usage_logs (
            id SERIAL PRIMARY KEY,
            provider TEXT,
            status TEXT, -- 'success', 'error', '429'
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """

        query_admin_users = f"""
        CREATE TABLE IF NOT EXISTS admin_users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE,
            password_hash TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """

        query_sources = f"""
        CREATE TABLE IF NOT EXISTS sources (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            url TEXT UNIQUE NOT NULL,
            type TEXT NOT NULL,
            region TEXT DEFAULT 'global',
            require_ai BOOLEAN DEFAULT FALSE,
            selectors TEXT, -- Almacenado como JSON string
            extra TEXT,     -- Almacenado como JSON string
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """

        # Ajuste para SQLite (SERIAL no existe)
        if "sqlite" in self.db_url:
            query_create = query_create.replace("SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")
            query_ai_logs = query_ai_logs.replace("SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")
            query_admin_users = query_admin_users.replace("SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")
            query_sources = query_sources.replace("SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")

        try:
            # 1. Crear tablas base
            with self.engine.begin() as conn:
                logger.debug("🔨 Verificando/Creando tablas del sistema...")
                conn.execute(text(query_create))
                conn.execute(text(query_ai_logs))
                conn.execute(text(query_admin_users))
                conn.execute(text(query_sources))
            
            # 2. Bootstraps
            self._bootstrap_admin()
            self._bootstrap_sources()

            # 3. Gestión de columnas faltantes
            is_postgres = "postgresql" in self.db_url
            for col_name in ['image_url', 'region', 'department', 'telegram_sent']:
                try:
                    if is_postgres:
                        # PostgreSQL soporta ADD COLUMN IF NOT EXISTS (9.6+)
                        with self.engine.begin() as conn:
                            # Ajuste dinámico para tipos (booleano vs texto)
                            db_type = "BOOLEAN DEFAULT FALSE" if col_name == "telegram_sent" else "TEXT"
                            conn.execute(text(f"ALTER TABLE {self.table_name} ADD COLUMN IF NOT EXISTS {col_name} {db_type}"))
                    else:
                        # SQLite no soporta IF NOT EXISTS en ALTER TABLE
                        with self.engine.begin() as conn:
                            db_type = "BOOLEAN DEFAULT FALSE" if col_name == "telegram_sent" else "TEXT"
                            conn.execute(text(f"ALTER TABLE {self.table_name} ADD COLUMN {col_name} {db_type}"))
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
                    SELECT title, url, source, region, department, ai_comment, reel_script, image_url, telegram_sent, processed_at 
                    FROM {self.table_name} ORDER BY processed_at DESC LIMIT 150
                """)
                rows = conn.execute(query).fetchall()
                keys = ["title", "link", "source_name", "region", "department",
                        "ai_comment", "reel_script", "image_url", "telegram_sent", "processed_at"]
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

    def log_ai_usage(self, provider: str, status: str) -> None:
        """Registra el uso de la IA para monitoreo de cuota."""
        if not self.engine: return
        try:
            with self.engine.begin() as conn:
                query = text("INSERT INTO ai_usage_logs (provider, status) VALUES (:p, :s)")
                conn.execute(query, {"p": provider, "s": status})
        except Exception as e:
            logger.error(f"Error loggeando uso de IA: {e}")

    def get_ai_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de uso de IA en la última hora."""
        if not self.engine: return {}
        try:
            with self.engine.connect() as conn:
                # PostgreSQL vs SQLite timestamp logic
                if "postgresql" in self.db_url:
                    time_filter = "timestamp > NOW() - INTERVAL '1 hour'"
                else:
                    time_filter = "timestamp > datetime('now', '-1 hour')"
                
                query = text(f"SELECT status, COUNT(*) FROM ai_usage_logs WHERE {time_filter} GROUP BY status")
                res = conn.execute(query).fetchall()
                
                stats = {"success": 0, "429": 0, "error": 0, "total": 0}
                for row in res:
                    stats[row[0]] = row[1]
                    stats["total"] += row[1]
                return stats
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de IA: {e}")
            return {}

    def _bootstrap_admin(self) -> None:
        """Crea el usuario admin inicial si la tabla está vacía."""
        if not self.engine: return
        try:
            with self.engine.connect() as conn:
                res = conn.execute(text("SELECT COUNT(*) FROM admin_users")).scalar()
                if res == 0:
                    logger.info("🔐 Iniciando bootstrap de seguridad: Creando usuario 'admin' por defecto.")
                    password = "admin123".encode('utf-8')
                    hashed = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')
                    conn.execute(
                        text("INSERT INTO admin_users (username, password_hash) VALUES (:u, :p)"),
                        {"u": "admin", "p": hashed}
                    )
                    conn.commit()
        except Exception as e:
            logger.error(f"Error en bootstrap de admin: {e}")

    def verify_credentials(self, username, password) -> bool:
        """Valida que el usuario y la contraseña sean correctos."""
        if not self.engine: return False
        try:
            with self.engine.connect() as conn:
                query = text("SELECT password_hash FROM admin_users WHERE username = :u")
                res = conn.execute(query, {"u": username}).fetchone()
                if not res: return False
                
                stored_hash = res[0].encode('utf-8')
                return bcrypt.checkpw(password.encode('utf-8'), stored_hash)
        except Exception as e:
            logger.error(f"Error verificando credenciales: {e}")
            return False

    def create_admin_user(self, username, password) -> bool:
        """Crea un nuevo administrador."""
        if not self.engine: return False
        try:
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            with self.engine.begin() as conn:
                conn.execute(
                    text("INSERT INTO admin_users (username, password_hash) VALUES (:u, :p)"),
                    {"u": username, "p": hashed}
                )
            return True
        except Exception as e:
            logger.error(f"Error creando administrador: {e}")
            return False

    def get_all_admins(self) -> list:
        """Lista todos los administradores registrados."""
        if not self.engine: return []
        try:
            with self.engine.connect() as conn:
                res = conn.execute(text("SELECT id, username, created_at FROM admin_users")).fetchall()
                return [{"id": r[0], "username": r[1], "created_at": r[2]} for r in res]
        except Exception as e:
            logger.error(f"Error listando administradores: {e}")
            return []

    def get_articles_with_placeholder(self, placeholder: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Identifica artículos que tienen el texto de 'procesando' para intentar repararlos."""
        if not self.engine: return []
        try:
            with self.engine.connect() as conn:
                query = text(f"""
                    SELECT title, url, source, region, department, image_url 
                    FROM {self.table_name} 
                    WHERE ai_comment = :placeholder
                    ORDER BY processed_at DESC LIMIT :limit
                """)
                rows = conn.execute(query, {"placeholder": placeholder, "limit": limit}).fetchall()
                keys = ["title", "link", "source_name", "region", "department", "image_url"]
                return [dict(zip(keys, row)) for row in rows]
        except SQLAlchemyError as e:
            logger.error(f"Error buscando artículos con placeholder: {e}")
            return []

    def update_article_ai_content(self, url: str, ai_comment: str, reel_script: str) -> bool:
        """Actualiza el contenido de IA para un artículo existente."""
        if not self.engine: return False
        try:
            with self.engine.begin() as conn:
                query = text(f"""
                    UPDATE {self.table_name} 
                    SET ai_comment = :comment, reel_script = :reel
                    WHERE url = :url
                """)
                conn.execute(query, {"comment": ai_comment, "reel": reel_script, "url": url})
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error actualizando contenido de IA para {url}: {e}")
            return False

    def mark_as_sent_to_telegram(self, url: str) -> bool:
        """Marca un artículo como enviado al canal de Telegram."""
        if not self.engine: return False
        try:
            with self.engine.begin() as conn:
                query = text(f"UPDATE {self.table_name} SET telegram_sent = TRUE WHERE url = :url")
                conn.execute(query, {"url": url})
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error marcando como enviado a Telegram {url}: {e}")
            return False

    def get_all_news_manager(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retorna una lista extendida de noticias para gestión administrativa."""
        if not self.engine: return []
        try:
            with self.engine.connect() as conn:
                query = text(f"""
                    SELECT title, url, source, region, department, ai_comment, reel_script, image_url, telegram_sent, processed_at 
                    FROM {self.table_name} 
                    ORDER BY processed_at DESC LIMIT :limit
                """)
                rows = conn.execute(query, {"limit": limit}).fetchall()
                keys = ["title", "link", "source_name", "region", "department",
                        "ai_comment", "reel_script", "image_url", "telegram_sent", "processed_at"]
                return [dict(zip(keys, row)) for row in rows]
        except SQLAlchemyError as e:
            logger.error(f"Error obteniendo noticias para el manager: {e}")
            return []

    def get_article_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Busca un artículo específico por su URL."""
        if not self.engine: return None
        try:
            with self.engine.connect() as conn:
                query = text(f"SELECT * FROM {self.table_name} WHERE url = :url")
                row = conn.execute(query, {"url": url}).fetchone()
                if row:
                    # En SQLAlchemy 1.4+ se usa _mapping, en versiones anteriores se puede convertir el Row
                    try:
                        return dict(row._mapping)
                    except AttributeError:
                        return dict(row)
                return None
        except SQLAlchemyError as e:
            logger.error(f"Error buscando artículo por URL: {e}")
            return None

    # --- Gestión de Fuentes (Sources) ---

    def _bootstrap_sources(self) -> None:
        """Importa fuentes desde sources.json si la tabla está vacía."""
        if not self.engine: return
        try:
            with self.engine.connect() as conn:
                count = conn.execute(text("SELECT COUNT(*) FROM sources")).scalar()
                if count > 0: return # Ya hay datos
            
            import json
            sources_path = config.paths.sources_path
            if not sources_path.exists():
                logger.warning(f"No se encontró {sources_path} para bootstrap de fuentes.")
                return

            with open(sources_path, "r", encoding="utf-8") as f:
                sources = json.load(f)
            
            logger.info(f"🚚 Migrando {len(sources)} fuentes desde JSON a Base de Datos...")
            with self.engine.begin() as conn:
                query = text("""
                    INSERT INTO sources (name, url, type, region, require_ai, selectors, extra)
                    VALUES (:name, :url, :type, :region, :require_ai, :selectors, :extra)
                """)
                for src in sources:
                    conn.execute(query, {
                        "name": src.get("name"),
                        "url": src.get("url"),
                        "type": src.get("type"),
                        "region": src.get("region", "global"),
                        "require_ai": src.get("require_ai", False),
                        "selectors": json.dumps(src.get("selectors", {})),
                        "extra": json.dumps(src.get("extra", {}))
                    })
            logger.info("✅ Migración de fuentes completada.")
        except Exception as e:
            logger.error(f"Error en bootstrap de fuentes: {e}")

    def get_all_sources(self) -> List[Dict[str, Any]]:
        """Retorna todas las fuentes activas de la base de datos."""
        if not self.engine: return []
        try:
            import json
            with self.engine.connect() as conn:
                query = text("SELECT id, name, url, type, region, require_ai, selectors, extra, is_active FROM sources ORDER BY id ASC")
                rows = conn.execute(query).fetchall()
                results = []
                for r in rows:
                    results.append({
                        "id": r[0],
                        "name": r[1],
                        "url": r[2],
                        "type": r[3],
                        "region": r[4],
                        "require_ai": r[5],
                        "selectors": json.loads(r[6] or '{}'),
                        "extra": json.loads(r[7] or '{}'),
                        "is_active": r[8]
                    })
                return results
        except Exception as e:
            logger.error(f"Error obteniendo fuentes de DB: {e}")
            return []

    def add_source_db(self, source_data: dict) -> bool:
        """Agrega una nueva fuente a la base de datos."""
        if not self.engine: return False
        try:
            import json
            with self.engine.begin() as conn:
                query = text("""
                    INSERT INTO sources (name, url, type, region, require_ai, selectors, extra)
                    VALUES (:name, :url, :type, :region, :require_ai, :selectors, :extra)
                """)
                conn.execute(query, {
                    "name": source_data.get("name"),
                    "url": source_data.get("url"),
                    "type": source_data.get("type"),
                    "region": source_data.get("region", "global"),
                    "require_ai": source_data.get("require_ai", False),
                    "selectors": json.dumps(source_data.get("selectors", {})),
                    "extra": json.dumps(source_data.get("extra", {}))
                })
            return True
        except Exception as e:
            logger.error(f"Error agregando fuente a DB: {e}")
            return False

    def update_source_db(self, source_id: int, source_data: dict) -> bool:
        """Actualiza una fuente por su ID en la base de datos."""
        if not self.engine: return False
        try:
            import json
            with self.engine.begin() as conn:
                query = text("""
                    UPDATE sources 
                    SET name = :name, url = :url, type = :type, region = :region, 
                        require_ai = :require_ai, selectors = :selectors, extra = :extra,
                        is_active = :is_active
                    WHERE id = :id
                """)
                conn.execute(query, {
                    "id": source_id,
                    "name": source_data.get("name"),
                    "url": source_data.get("url"),
                    "type": source_data.get("type"),
                    "region": source_data.get("region"),
                    "require_ai": source_data.get("require_ai"),
                    "selectors": json.dumps(source_data.get("selectors", {})),
                    "extra": json.dumps(source_data.get("extra", {})),
                    "is_active": source_data.get("is_active", True)
                })
            return True
        except Exception as e:
            logger.error(f"Error actualizando fuente en DB (ID {source_id}): {e}")
            return False

    def delete_source_db(self, source_id: int) -> bool:
        """Elimina una fuente por su ID."""
        if not self.engine: return False
        try:
            with self.engine.begin() as conn:
                conn.execute(text("DELETE FROM sources WHERE id = :id"), {"id": source_id})
            return True
        except Exception as e:
            logger.error(f"Error eliminando fuente de DB (ID {source_id}): {e}")
            return False
