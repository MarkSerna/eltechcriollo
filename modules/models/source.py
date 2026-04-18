from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class SourceConfig:
    """Modelo fuerte para cada sitio web incluido en sources.json."""
    name: str
    url: str
    type: str  # 'rss', 'html', 'dynamic', 'wpapi', 'mintic', 'sharepoint', 'sena'
    region: str = "global"  # Por defecto 'global', puede ser 'colombia'
    require_ai: bool = False  # Si True, el artículo SIEMPRE va a validación IA (sin fallback de keywords)
    selectors: Optional[Dict[str, str]] = None
    extra: Optional[Dict[str, Any]] = None  # Parámetros extra por tipo de fuente

    def __post_init__(self):
        if self.selectors is None:
            self.selectors = {}
        if self.extra is None:
            self.extra = {}

        # Validación de integridad lógica
        valid_types = ["rss", "html", "dynamic", "wpapi", "mintic", "sharepoint", "sena"]
        if self.type not in valid_types:
            raise ValueError(f"Tipo desconocido '{self.type}' en la fuente {self.name}")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SourceConfig":
        """Crea una instancia filtrando campos desconocidos para evitar errores de init."""
        import inspect
        sig = inspect.signature(cls)
        filtered_data = {k: v for k, v in data.items() if k in sig.parameters}
        return cls(**filtered_data)

@dataclass
class ScrapedArticle:
    """Modelo que representa una noticia que ha sido extraída exitosamente."""
    title: str
    link: str
    source_name: str
    region: str = "global"
    department: Optional[str] = None   # Departamento colombiano detectado
    summary: str = ""
    ai_comment: str = ""
    reel_script: str = ""
    image_url: Optional[str] = None

    def get_content_snapshot(self) -> str:
        """Retorna una versión unificada del texto para analizar palabras clave."""
        return f"{self.title} {self.summary}".lower()
