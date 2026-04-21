from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, Form, Depends, HTTPException, Request, BackgroundTasks
from starlette.middleware.sessions import SessionMiddleware
import os

import sys
from pathlib import Path
from dotenv import load_dotenv
from datetime import date, timedelta
from collections import OrderedDict

# Ensure module visibility
sys.path.insert(0, str(Path(__file__).parent))
load_dotenv()

from modules.core.app import main_orchestrator
from modules.services.database_manager import DatabaseManager
from modules.utils.logger import logger
from modules.services.notification_manager import NotificationManager
from apscheduler.schedulers.asyncio import AsyncIOScheduler

app = FastAPI(title="El Tech Criollo - Intelligence Hub")

# Configuración de Seguridad (Sesiones)
SECRET_KEY = os.getenv("SECRET_KEY", "flash_default_secret_999")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

def is_authenticated(request: Request):
    """Verifica si la sesión del usuario es válida."""
    if not request.session.get("authenticated"):
        raise HTTPException(status_code=401, detail="No autorizado")
    return True

from modules.services.telegram_listener import TelegramBotListener
import asyncio

# Configuración de Programación Automática (Cada 30 min)
@app.on_event("startup")
async def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(main_orchestrator, 'interval', minutes=5)
    scheduler.start()
    logger.info("⏰ Programador activado: Escaneo autónomo cada 5 minutos configurado.")
    
    # Iniciar oyente de Chat para Telegram (Solo en local, desactivado en Render)
    if os.getenv("RENDER") != "true":
        listener = TelegramBotListener()
        asyncio.create_task(listener.poll())
        logger.info("🤖 Oyente de Telegram activado (Modo Interactivo Local)")
    else:
        logger.info("🚫 Entorno Render detectado: El Bot no responderá a mensajes directos (Polling desactivado)")

# Setup directories for static and templates
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
templates_dir = Path(__file__).parent / "templates"
templates_dir.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

db = DatabaseManager()
db.initialize_schema()

_MONTHS_ES = {
    1: "ene", 2: "feb", 3: "mar", 4: "abr", 5: "may", 6: "jun",
    7: "jul", 8: "ago", 9: "sep", 10: "oct", 11: "nov", 12: "dic"
}

def _group_by_day(articles: list) -> list:
    """
    Agrupa una lista de artículos por día (campo processed_at).
    Retorna lista ordenada de más reciente a más antiguo:
      [{"label": "Hoy · 15 abr 2026", "date": "2026-04-15", "articles": [...]}, ...]
    """
    today     = date.today()
    yesterday = today - timedelta(days=1)
    grouped: dict[str, list] = OrderedDict()

    for article in articles:
        raw_ts = article.get("processed_at", "")
        try:
            day_str = str(raw_ts)[:10]   # "YYYY-MM-DD"
            date.fromisoformat(day_str)  # valida el formato
        except Exception:
            day_str = str(today)

        if day_str not in grouped:
            grouped[day_str] = []
        grouped[day_str].append(article)

    result = []
    for day_str, arts in grouped.items():
        day = date.fromisoformat(day_str)
        readable = f"{day.day} {_MONTHS_ES[day.month]} {day.year}"
        if day == today:
            label = f"Hoy · {readable}"
        elif day == yesterday:
            label = f"Ayer · {readable}"
        else:
            label = readable
        result.append({"label": label, "date": day_str, "articles": arts})

    return result


async def render_dashboard(request: Request, is_admin: bool = False):
    """Función unificada para renderizar el tablero."""
    articles = db.get_todays_articles()

    colombia_news = [a for a in articles if a.get("region") == "colombia"]
    global_news   = [a for a in articles if a.get("region") == "global"]

    # Artículo destacado: el más reciente de Colombia
    featured = colombia_news[0] if colombia_news else None

    # ── Mapa regional: agrupar noticias colombianas por departamento ──────
    from collections import defaultdict
    dept_raw: dict[str, list] = defaultdict(list)
    for article in colombia_news:
        dept = article.get("department") or "Nacional"
        dept_raw[dept].append(article)

    # Ordenar: primero departamentos con más noticias, sumando puntos artificiales al Eje Cafetero
    EJE_CAFETERO = {"Caldas", "Risaralda", "Quindío", "Quindio"}
    sorted_depts = sorted(
        [(dept, arts) for dept, arts in dept_raw.items() if dept != "Nacional"],
        key=lambda x: len(x[1]) + (100 if x[0] in EJE_CAFETERO else 0),
        reverse=True,
    )
    if "Nacional" in dept_raw:
        sorted_depts.append(("Nacional", dept_raw["Nacional"]))

    departments_map = dict(sorted_depts)

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "featured":         featured,
            "days_colombia":    _group_by_day(colombia_news[1:] if featured else colombia_news),
            "days_global":      _group_by_day(global_news),
            "departments_map":  departments_map,
            "global_news":      global_news,
            "is_admin":         is_admin,
        }
    )

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Renderiza el tablero interactivo de lectura (Público)."""
    return await render_dashboard(request, is_admin=False)

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Página de inicio de sesión."""
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, password: str = Form(...)):
    """Procesa el inicio de sesión."""
    if password == ADMIN_PASSWORD:
        request.session["authenticated"] = True
        logger.info("🔐 Administración: Sesión iniciada con éxito.")
        return RedirectResponse(url="/admin", status_code=303)
    else:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Contraseña incorrecta"})

@app.get("/logout")
async def logout(request: Request):
    """Cierra la sesión administrativa."""
    request.session.clear()
    return RedirectResponse(url="/")

@app.get("/admin", response_class=HTMLResponse)
async def admin_home(request: Request):
    """Renderiza el tablero interactivo de lectura (Admin)."""
    if not request.session.get("authenticated"):
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("admin.html", {"request": request})

@app.get("/api/stats")
async def get_stats(authenticated: bool = Depends(is_authenticated)):
    """Retorna estadísticas para el dashboard admin."""
    articles = db.get_todays_articles()
    import json
    sources_path = Path(__file__).parent / "data" / "sources.json"
    with open(sources_path, "r", encoding="utf-8") as f:
        sources = json.load(f)
    
    return {
        "articles_today": len(articles),
        "sources_count": len(sources),
        "recent_articles": articles[:5]
    }

@app.get("/api/logs")
async def get_logs(authenticated: bool = Depends(is_authenticated)):
    """Lee las últimas líneas del log de hoy."""
    from datetime import date
    today_str = date.today().isoformat()
    log_file = Path(__file__).parent / "logs" / f"bot_{today_str}.log"
    
    if not log_file.exists():
        return {"logs": ["No hay logs registrados para hoy todavía."]}
    
    with open(log_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    return {"logs": lines[-100:]} # Últimas 100 líneas

@app.get("/api/dictionary")
async def get_dictionary(authenticated: bool = Depends(is_authenticated)):
    """Retorna el contenido del diccionario técnico."""
    import json
    dict_path = Path(__file__).parent / "data" / "tech_dictionary.json"
    with open(dict_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Flatten groups for easier JS handling
    entries = []
    for group, items in data.items():
        for item in items:
            entries.append({"entity": item, "type": group})
            
    return {"entries": entries}

@app.get("/api/sources")
async def get_sources(authenticated: bool = Depends(is_authenticated)):
    """Retorna la lista de fuentes configuradas."""
    import json
    sources_path = Path(__file__).parent / "data" / "sources.json"
    with open(sources_path, "r", encoding="utf-8") as f:
        sources = json.load(f)
    return {"sources": sources}

@app.post("/api/test-telegram")
async def test_telegram(authenticated: bool = Depends(is_authenticated)):
    """Envía un mini-reporte de prueba para verificar que el Bot funciona."""
    nm = NotificationManager()
    
    success = await nm.send_telegram_message("🚀 **Test de Conexión**\n\nSi estás recibiendo esto en tu canal, ¡tu integración con **El Tech Criollo** está perfecta!\n\n---\n*Enviado desde el Dashboard Local*")
    
    if success:
        return JSONResponse(content={"status": "ok", "message": "¡Mensaje de prueba enviado! Revisa tu Telegram."})
    else:
        return JSONResponse(status_code=500, content={"status": "error", "message": "Falla al enviar. Revisa logs y credenciales."})

@app.post("/api/scrape")
async def trigger_scrape(background_tasks: BackgroundTasks, authenticated: bool = Depends(is_authenticated)):
    """Endpoint para forzar que el robot extraiga y Ollama analice asíncronamente."""
    logger.info("🚀 Petición de Scraping forzada vía API Web (Asíncrona).")
    
    background_tasks.add_task(main_orchestrator)
    
    return JSONResponse(content={"status": "working", "message": "Scraping e Inferencia IA ha comenzado en fondo de forma asíncrona. Recarga la página en unos segundos."})

from pydantic import BaseModel

class ArticleResendRequest(BaseModel):
    title: str
    link: str
    source_name: str
    ai_comment: str
    image_url: str = ""

@app.post("/api/resend-article")
async def resend_article(request: ArticleResendRequest, authenticated: bool = Depends(is_authenticated)):
    """Endpoint para reenviar una noticia manualmente a Telegram desde el Dashboard."""
    logger.info(f"Reenviando artículo a Telegram: {request.title}")
    
    nm = NotificationManager()
    
    class FakeArticle:
        def __init__(self, data):
            self.title = data.title
            self.link = data.link
            self.source_name = data.source_name
            self.ai_comment = data.ai_comment
            self.image_url = data.image_url

    success = await nm.send_telegram_visual_news(FakeArticle(request))
    
    if success:
        return JSONResponse(content={"status": "ok", "message": "¡Noticia reenviada con éxito a Telegram!"})
    else:
        return JSONResponse(status_code=500, content={"status": "error", "message": "Fallo al reenviar la noticia."})
