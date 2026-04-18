import re
import json
from pathlib import Path
from typing import Tuple

from modules.utils.logger import logger


# ─────────────────────────────────────────────────────────────────────────────
# Puntajes por categoría
# ─────────────────────────────────────────────────────────────────────────────
SCORE_STRICT    = 5   # Un solo término strict ya deja pasar el umbral normal
SCORE_ENTITY    = 3   # Empresa / producto tech reconocible
SCORE_SUPPORTING = 1  # Término de apoyo (necesita varios para sumar)

# Umbral base — un artículo debe superar este puntaje para pasar SIN IA
SCORE_THRESHOLD_NORMAL   = 5
# Umbral para fuentes marcadas como require_ai — nunca pasan sin IA, pero el
# score se sigue calculando para loguear la calidad de la noticia.
SCORE_THRESHOLD_REQUIRE_AI = 999  # Imposible de alcanzar sin IA → siempre va a validación IA


def _load_dictionary() -> dict:
    """Carga el diccionario desde data/tech_dictionary.json con caché en módulo."""
    dict_path = Path("data/tech_dictionary.json")
    if not dict_path.exists():
        logger.warning("⚠️  tech_dictionary.json no encontrado. TechFilter usará listas vacías.")
        return {"TECH_STRICT": [], "TECH_ENTITIES": [], "TECH_SUPPORTING": [], "TECH_NEGATIVE": []}
    try:
        with open(dict_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error cargando tech_dictionary.json: {e}")
        return {"TECH_STRICT": [], "TECH_ENTITIES": [], "TECH_SUPPORTING": [], "TECH_NEGATIVE": []}


# Carga única al importar el módulo (evita I/O repetido)
_DICTIONARY = _load_dictionary()

STRICT_TERMS    = [t.lower() for t in _DICTIONARY.get("TECH_STRICT", [])]
ENTITY_TERMS    = [t.lower() for t in _DICTIONARY.get("TECH_ENTITIES", [])]
SUPPORTING_TERMS = [t.lower() for t in _DICTIONARY.get("TECH_SUPPORTING", [])]
NEGATIVE_TERMS  = [t.lower() for t in _DICTIONARY.get("TECH_NEGATIVE", [])]


def _term_pattern(term: str) -> re.Pattern:
    """Retorna un patrón regex con word-boundary apropiado para el término."""
    escaped = re.escape(term)
    if len(term) <= 3:
        # Acrónimos cortos: match exacto con word-boundary estricto
        return re.compile(r'\b' + escaped + r'\b', re.IGNORECASE)
    else:
        # Términos largos: permite formas plurales/flexionadas básicas en español
        return re.compile(r'\b' + escaped + r'(s|es|a|o|as|os|ción|ciones)?\b', re.IGNORECASE)


def _matches_any(terms: list, text: str) -> list:
    """Retorna la lista de términos que hacen match en el texto."""
    matched = []
    for term in terms:
        if _term_pattern(term).search(text):
            matched.append(term)
    return matched


def score(content: str, require_ai: bool = False) -> Tuple[bool, int, str]:
    """
    Evalúa el contenido de un artículo contra el diccionario tech.

    Retorna:
        (passes_filter: bool, total_score: int, reason: str)

    Si require_ai=True, passes_filter siempre será False (el artículo DEBE ir
    a validación IA), pero el score e información de debugging se calculan igual.
    """
    text = content.lower()

    # ── Paso 0: Exclusión negativa inmediata ──────────────────────────────────
    negative_matches = _matches_any(NEGATIVE_TERMS, text)
    if negative_matches:
        reason = f"❌ Exclusión negativa: '{negative_matches[0]}'"
        logger.debug(reason)
        return False, 0, reason

    # ── Paso 1: Calcular puntaje ───────────────────────────────────────────────
    total_score = 0
    score_breakdown = []

    strict_matches = _matches_any(STRICT_TERMS, text)
    for t in strict_matches:
        total_score += SCORE_STRICT
        score_breakdown.append(f"STRICT({t})")

    entity_matches = _matches_any(ENTITY_TERMS, text)
    for t in entity_matches:
        total_score += SCORE_ENTITY
        score_breakdown.append(f"ENTITY({t})")

    supporting_matches = _matches_any(SUPPORTING_TERMS, text)
    for t in supporting_matches:
        total_score += SCORE_SUPPORTING
        score_breakdown.append(f"SUPP({t})")

    # ── Paso 2: Decisión ──────────────────────────────────────────────────────
    threshold = SCORE_THRESHOLD_REQUIRE_AI if require_ai else SCORE_THRESHOLD_NORMAL

    if require_ai:
        # Fuentes regionales: solo pasan si el score > 0 (hay al menos alguna
        # señal tech) y la IA confirma. Aquí marcamos para que el orquestador
        # lo envíe a IA obligatoriamente.
        passes = False  # El TechFilter nunca aprueba directamente fuentes require_ai
        if total_score == 0:
            reason = f"⛔ [require_ai] Sin señal tech mínima (score=0). Descartado."
        else:
            reason = f"🔄 [require_ai] Score={total_score} → Requiere validación IA obligatoria."
    else:
        passes = total_score >= SCORE_THRESHOLD_NORMAL
        if passes:
            reason = f"✅ Score={total_score} → Pasa filtro pre-IA. [{', '.join(score_breakdown[:5])}]"
        else:
            reason = f"❌ Score={total_score} < {SCORE_THRESHOLD_NORMAL} → Rechazado pre-IA."

    logger.debug(reason)
    return passes, total_score, reason


def needs_ai_validation(content: str, require_ai: bool) -> Tuple[bool, int, str]:
    """
    Wrapper de alto nivel que el orquestador debe llamar.

    Retorna:
        (send_to_ai: bool, score: int, reason: str)

    - Si passes=True y require_ai=False → artículo pasa sin IA  
    - Si passes=False y score>0 y require_ai=True → mandar a IA
    - Si passes=False y score==0 → descartar inmediatamente
    """
    passes, total_score, reason = score(content, require_ai)

    if require_ai and total_score > 0:
        return True, total_score, reason  # Señal tech existe, pero la IA debe confirmar

    if passes:
        return False, total_score, reason  # Pasa sin IA

    return False, total_score, reason  # No pasa y no hay señal tech
