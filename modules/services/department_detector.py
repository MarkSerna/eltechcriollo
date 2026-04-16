"""
DepartmentDetector: detecta el departamento colombiano mencionado en una noticia.

Estrategia:
  1. Busca coincidencias de nombres de departamentos (exacto)
  2. Luego busca ciudades/municipios principales asociados a cada departamento
  3. Retorna el primer match (prioridad: departamento > ciudad capital > municipios)
  4. Si no hay match → retorna None (noticia "Nacional")
"""
from typing import Optional
import re

# ─── Mapa completo: departamento → [keywords a buscar en el texto] ──────────
# Se incluyen: nombre del departamento, capital, principales municipios y alias

DEPARTMENT_KEYWORDS: dict[str, list[str]] = {
    "Bogotá D.C.": [
        "bogotá", "bogota", "distrito capital", "d.c.", "capital del país",
        "ciudad capital", "chapinero", "usaquén", "usaquen", "suba", "kennedy",
        "bosa", "engativá", "engativa", "fontibón", "fontibon", "teusaquillo",
        "puente aranda", "tunjuelito", "rafael uribe", "ciudad bolívar",
    ],
    "Antioquia": [
        "antioquia", "medellín", "medellin", "rionegro", "bello", "itagüí",
        "itagui", "envigado", "sabaneta", "la estrella", "caldas antioquia",
        "apartadó", "apartado", "turbo", "urabá", "uraba", "caucasia",
        "puerto berrío", "puerto berrio", "marinilla", "el carmen de viboral",
        "la ceja", "el retiro", "copacabana", "girardota", "barbosa antioquia",
        "area metropolitana", "valle de aburrá", "valle de aburra",
    ],
    "Valle del Cauca": [
        "valle del cauca", "valle del cauca", "cali", "buenaventura", "palmira",
        "tuluá", "tulua", "cartago", "buga", "guadalajara de buga",
        "yumbo", "jamundí", "jamundi", "candelaria", "pradera", "florida valle",
        "dagua", "buenaventura", "sevilla valle",
    ],
    "Atlántico": [
        "atlántico", "atlantico", "barranquilla", "soledad", "malambo",
        "sabanalarga", "baranoa", "galapa", "puerto colombia", "tubará",
        "tubara", "juan de acosta",
    ],
    "Santander": [
        "santander", "bucaramanga", "barrancabermeja", "floridablanca",
        "girón", "giron santander", "piedecuesta", "lebrija", "socorro",
        "san gil", "vélez", "velez santander", "málaga santander",
    ],
    "Bolívar": [
        "bolívar", "bolivar", "cartagena", "cartagena de indias",
        "magangué", "magangue", "mompox", "el carmen de bolívar",
        "turbaco", "arjona bolívar",
    ],
    "Córdoba": [
        "córdoba", "cordoba", "montería", "monteria", "cereté", "cerete",
        "lorica", "sahagún", "sahagun", "montelíbano", "montelibano",
        "planeta rica", "tierralta",
    ],
    "Nariño": [
        "nariño", "narino", "pasto", "ipiales", "tumaco", "túquerres",
        "tuquerres", "la unión nariño", "samaniego", "la florida nariño",
    ],
    "Cundinamarca": [
        "cundinamarca", "soacha", "zipaquirá", "zipaquira", "fusagasugá",
        "fusagasuga", "facatativá", "facatativa", "chía", "chia cundinamarca",
        "cajicá", "cajica", "mosquera cundinamarca", "madrid cundinamarca",
        "funza", "girardot", "villeta", "la mesa cundinamarca",
    ],
    "Boyacá": [
        "boyacá", "boyaca", "tunja", "duitama", "sogamoso", "chiquinquirá",
        "chiquinquira", "paipa", "villa de leyva", "Puerto Boyacá",
        "moniquirá", "moniquira",
    ],
    "Tolima": [
        "tolima", "ibagué", "ibague", "espinal", "melgar", "honda tolima",
        "chaparral", "girardot tolima", "flandes", "lérida tolima",
        "mariquita", "ambalema",
    ],
    "Huila": [
        "huila", "neiva", "pitalito", "garzón", "garzon", "la plata huila",
        "campoalegre", "palermo huila", "rivera huila",
    ],
    "Cauca": [
        "cauca", "popayán", "popayan", "santander de quilichao",
        "puerto tejada", "caloto", "padilla cauca", "miranda cauca",
    ],
    "Nariño": [
        "nariño", "narino", "pasto", "tumaco", "ipiales",
    ],
    "Caldas": [
        "caldas", "manizales", "la dorada", "chinchiná", "chinchina",
        "villamaría", "villamaria", "aguadas", "anserma", "manzanares caldas",
        "salamina caldas", "neira caldas", "riosucio caldas",
    ],
    "Risaralda": [
        "risaralda", "pereira", "dosquebradas", "santa rosa de cabal",
        "la virginia", "belén de umbría", "belen de umbria",
        "quinchía", "quinchia", "marsella risaralda",
    ],
    "Quindío": [
        "quindío", "quindio", "armenia", "calarcá", "calarca",
        "montenegro quindío", "quimbaya", "circasia", "salento",
        "la tebaida", "filandia",
    ],
    "Cesar": [
        "cesar", "valledupar", "aguachica", "agustín codazzi",
        "codazzi", "la jagua de ibirico", "bosconia",
    ],
    "Magdalena": [
        "magdalena", "santa marta", "ciénaga", "cienaga", "fundación magdalena",
        "plato magdalena", "ariguaní",
    ],
    "La Guajira": [
        "la guajira", "guajira", "riohacha", "maicao", "uribia",
        "manaure", "fonseca",
    ],
    "Sucre": [
        "sucre", "sincelejo", "corozal", "sampués", "sampues",
        "morroa", "san marcos sucre",
    ],
    "Norte de Santander": [
        "norte de santander", "cúcuta", "cucuta", "ocaña", "ocana",
        "pamplona norte de santander", "villa del rosario", "los patios",
        "el zulia", "tibú", "tibu",
    ],
    "Arauca": [
        "arauca", "arauca ciudad", "saravena", "arauquita",
        "fortul", "tame",
    ],
    "Casanare": [
        "casanare", "yopal", "aguazul", "tauramena", "monterrey casanare",
        "villanueva casanare", "paz de ariporo",
    ],
    "Meta": [
        "meta", "villavicencio", "acacías", "acacias", "granada meta",
        "puerto lópez", "puerto lopez", "cumaral",
    ],
    "Vichada": [
        "vichada", "puerto carreño", "la primavera vichada",
    ],
    "Guainía": [
        "guainía", "guainia", "inírida", "inirida",
    ],
    "Vaupés": [
        "vaupés", "vaupes", "mitú", "mitu",
    ],
    "Amazonas": [
        "amazonas", "leticia", "puerto nariño",
    ],
    "Putumayo": [
        "putumayo", "mocoa", "puerto asís", "puerto asis",
        "orito", "san miguel putumayo",
    ],
    "Caquetá": [
        "caquetá", "caqueta", "florencia", "san vicente del caguán",
        "san vicente del caguan",
    ],
    "Guaviare": [
        "guaviare", "san josé del guaviare", "san jose del guaviare",
        "calamar guaviare",
    ],
    "Chocó": [
        "chocó", "choco", "quibdó", "quibdo", "istmina", "tadó", "tado",
        "bahía solano", "bahia solano", "nuquí", "nuqui",
    ],
    "San Andrés y Providencia": [
        "san andrés", "san andres", "providencia", "santa catalina",
        "archipelago",
    ],
}

# Pre-compilar patterns por eficiencia (sin distinción de mayúsculas)
_COMPILED: dict[str, list[re.Pattern]] = {
    dept: [re.compile(r"\b" + re.escape(kw) + r"\b", re.IGNORECASE)
           for kw in keywords]
    for dept, keywords in DEPARTMENT_KEYWORDS.items()
}


def detect(title: str, summary: str = "") -> Optional[str]:
    """
    Detecta el departamento colombiano más probable para una noticia.

    Args:
        title:   Título del artículo
        summary: Resumen o extracto (opcional)

    Returns:
        Nombre del departamento si se detecta, None si es noticia "Nacional" o no clasificable.
    """
    text = f"{title} {summary}".lower()

    # Bogotá tiene mayor probabilidad de falso positivo — verificar primero las regiones
    matches: dict[str, int] = {}
    for dept, patterns in _COMPILED.items():
        count = sum(1 for p in patterns if p.search(text))
        if count > 0:
            matches[dept] = count

    if not matches:
        return None

    # Retornar el departamento con más coincidencias
    return max(matches, key=lambda d: matches[d])
