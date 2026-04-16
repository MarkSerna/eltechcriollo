import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.models.source import ScrapedArticle
from modules.models.config import config
from modules.services.ai_manager import AIManager

ai = AIManager()

articles = [
    ScrapedArticle(
        title="MinTIC abre convocatoria para emprendedores digitales",
        link="http://test.com/1",
        source_name="MinTIC",
        region="colombia",
        summary="El Ministerio TIC abrió una nueva convocatoria para que emprendedores puedan acceder a capital.",
        image_url=None
    ),
    ScrapedArticle(
        title="Nuevo modelo de IA colombiano puede predecir el clima",
        link="http://test.com/2",
        source_name="ImpactoTIC",
        region="colombia",
        summary="Investigadores desarrollaron un algoritmo de inteligencia artificial que mejora la predicción climática usando machine learning y computación en la nube.",
        image_url=None
    ),
    ScrapedArticle(
        title="Gobierno aprueba subsidio para familias campesinas",
        link="http://test.com/3",
        source_name="General",
        region="colombia",
        summary="El programa busca digitalizar el acceso a los subsidios con una nueva plataforma web del gobierno.",
        image_url=None
    ),
    ScrapedArticle(
        title="Bogotá inaugura un nuevo puente",
        link="http://test.com/4",
        source_name="General",
        region="colombia",
        summary="La infraestructura mejorará la movilidad. Cuenta con tecnología LED y un sistema de control de luces.",
        image_url=None
    )
]

for article in articles:
    import re
    content = article.get_content_snapshot().lower()
    
    def has_keyword(kw_list, text):
        for kw in kw_list:
            kw_lower = kw.lower()
            if len(kw_lower) <= 3:
                if re.search(r'\b' + re.escape(kw_lower) + r'\b', text):
                    return True
            else:
                if re.search(r'\b' + re.escape(kw_lower) + r'(s|es|a|o|as|os)?\b', text):
                    return True
        return False
        
    is_valid = has_keyword(config.scraper.keywords, content)
    
    if is_valid and article.region == "colombia":
        is_tech_ai = ai.is_tech_news(article)
        if is_tech_ai is True:
            is_valid = True
            reason = "AI Approved"
        elif is_tech_ai is False:
            is_valid = False
            reason = "AI Rejected"
        else:
            has_strict = has_keyword(config.scraper.strict_keywords, content)
            supporting_count = sum(1 for kw in config.scraper.supporting_keywords if re.search(r'\b' + re.escape(kw.lower()) + r'\b', content))
            if not (has_strict or supporting_count >= 2):
                is_valid = False
                reason = "Fallback Rejected"
            else:
                reason = "Fallback Approved"
                
        print(f"[{'PASS' if is_valid else 'FAIL'}] {article.title} -> {reason}")
    else:
        print(f"[{'PASS' if is_valid else 'FAIL'}] {article.title} -> Global/No keywords")

