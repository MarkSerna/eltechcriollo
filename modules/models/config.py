import os
from pathlib import Path
from dataclasses import dataclass
from typing import List

@dataclass
class DiscordConfig:
    """Configuración para Webhooks de Discord."""
    webhook_url: str = os.getenv("DISCORD_WEBHOOK_URL", "")

@dataclass
class TelegramConfig:
    """Configuración para bot de Telegram."""
    bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")


@dataclass
class PathConfig:
    """Configuración de rutas del sistema."""
    data_dir: Path = Path(os.getenv("DB_DIR", "data"))
    db_name: str = os.getenv("DB_NAME", "history.db")
    sources_path: Path = Path(os.getenv("SOURCES_PATH", "data/sources.json"))
    reports_dir: Path = Path(os.getenv("REPORTS_DIR", "reports"))
    logs_dir: Path = Path(os.getenv("LOGS_DIR", "logs"))
    
    @property
    def db_path(self) -> Path:
        return self.data_dir / self.db_name


@dataclass
class ScraperConfig:
    """Configuración de las arañas de extracción."""
    keywords: List[str] = None
    timeout: int = 15
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    def __post_init__(self):
        if self.keywords is None:
            self.keywords = [
                "IA", "Modelos de lenguaje", "Startups Colombianas", 
                "Desarrollo de Software", "Inteligencia Artificial", "AI", "Machine Learning"
            ]


@dataclass
class AIConfig:
    """Configuración para Ollama Local."""
    ollama_url: str = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "gemma4:31b-cloud")


@dataclass
class AppConfig:
    """Configuración global de la aplicación."""
    paths: PathConfig = None
    scraper: ScraperConfig = None
    discord: DiscordConfig = None
    telegram: TelegramConfig = None
    ai: AIConfig = None
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    cleanup_days: int = int(os.getenv("CLEANUP_DAYS", "7"))
    
    def __post_init__(self):
        if self.paths is None:
            self.paths = PathConfig()
        if self.scraper is None:
            self.scraper = ScraperConfig()
        if self.discord is None:
            self.discord = DiscordConfig()
        if self.telegram is None:
            self.telegram = TelegramConfig()
        if self.ai is None:
            self.ai = AIConfig()
            
            
        # Crear los directorios obligatorios si no existen
        self.paths.data_dir.mkdir(parents=True, exist_ok=True)
        self.paths.logs_dir.mkdir(parents=True, exist_ok=True)
        self.paths.reports_dir.mkdir(parents=True, exist_ok=True)

# Instancia global de configuración
config = AppConfig()
