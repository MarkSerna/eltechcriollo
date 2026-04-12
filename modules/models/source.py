from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class SourceConfig:
    """Modelo fuerte para cada sitio web incluido en sources.json."""
    name: str
    url: str
    type: str # 'rss' o 'html'
    region: str = "global" # Por defecto 'global', puede ser 'colombia'
    selectors: Optional[Dict[str, str]] = None
    
    def __post_init__(self):
        if self.selectors is None:
            self.selectors = {}
        
        # Validación de integridad lógica
        if self.type not in ["rss", "html", "dynamic"]:
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
    summary: str = ""
    ai_comment: str = ""
    reel_script: str = ""
    image_url: Optional[str] = None

    
    def get_content_snapshot(self) -> str:
        """Retorna una versión unificada del texto para analizar palabras clave."""
        return f"{self.title} {self.summary}".lower()
