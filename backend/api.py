from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Form, Depends, HTTPException, Request, BackgroundTasks
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from datetime import date, timedelta
from collections import OrderedDict, defaultdict
from pydantic import BaseModel, Field

# Ensure module visibility
sys.path.insert(0, str(Path(__file__).parent))
load_dotenv()

from modules.core.app import main_orchestrator
from modules.services.database_manager import DatabaseManager
from modules.utils.logger import logger
from modules.services.notification_manager import NotificationManager
from modules.services.telegram_listener import TelegramBotListener
from modules.models.config import config
from modules.models.source import SourceConfig, ScrapedArticle
from apscheduler.schedulers.asyncio import AsyncIOScheduler

app = FastAPI(
    title="El Tech Criollo - Intelligence Hub",
    description="API para el centro de inteligencia de noticias automatizado",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "Auth", "description": "Endpoints de autenticación"},
        {"name": "News", "description": "Noticias y artículos"},
        {"name": "Admin", "description": "Administración del sistema"},
        {"name": "System", "description": "Endpoints del sistema"}
    ]
)

# --- Root Route for Health Check ---
@app.get("/", tags=["System"])
async def root():
    return {"status": "ok", "message": "El Tech Criollo API is running"}

# --- Security Configuration ---
SECRET_KEY = config.system.secret_key or os.urandom(32).hex()
if not config.system.secret_key:
    logger.warning("⚠️ SECRET_KEY no configurado. Se usará una clave efímera para esta sesión.")

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie=config.system.session_cookie_name,
    max_age=config.system.session_max_age,
    same_site=config.system.session_same_site,
    https_only=config.system.session_secure,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.system.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Shared Instances ---
db = DatabaseManager()
scheduler = AsyncIOScheduler()

# --- Auth Dependencies ---
def is_authenticated(request: Request):
    """Verifica si la sesión del usuario es válida."""
    if not request.session.get("authenticated"):
        raise HTTPException(status_code=401, detail="No autorizado")
    return True

class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=256)

class CreateAdminRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=10, max_length=256)

class PublishTelegramRequest(BaseModel):
    url: str = Field(min_length=10, max_length=2048)

# --- Startup Task ---
@app.on_event("startup")
async def startup_event():
    db.initialize_schema()
    
    # Scheduler Setup
    scheduler.add_job(main_orchestrator, 'interval', minutes=5, id='scraping_job')
    scheduler.start()
    logger.info("⏰ Programador activado: Escaneo cada 5 minutos.")
    
    # Telegram Listener
    if os.getenv("RENDER") != "true":
        listener = TelegramBotListener()
        asyncio.create_task(listener.poll())
        logger.info("🤖 Oyente de Telegram activado.")

# --- Static Files ---
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- Helper Functions ---
_MONTHS_ES = {
    1: "ene", 2: "feb", 3: "mar", 4: "abr", 5: "may", 6: "jun",
    7: "jul", 8: "ago", 9: "sep", 10: "oct", 11: "nov", 12: "dic"
}

def _group_by_day(articles: list) -> list:
    today = date.today()
    yesterday = today - timedelta(days=1)
    grouped = OrderedDict()

    for article in articles:
        raw_ts = article.get("processed_at", "")
        try:
            day_str = str(raw_ts)[:10]
            date.fromisoformat(day_str)
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

# --- API Endpoints ---

@app.post("/api/login", tags=["Auth"])
async def login(req_data: LoginRequest, request: Request):
    if db.verify_credentials(req_data.username, req_data.password):
        request.session.clear()
        request.session["authenticated"] = True
        request.session["username"] = req_data.username
        logger.info(f"🔐 Sesión iniciada: {req_data.username}")
        return {"status": "ok", "user": {"username": req_data.username, "authenticated": True}}
    raise HTTPException(status_code=401, detail="Credenciales inválidas")

@app.get("/api/auth/me", tags=["Auth"])
async def get_me(request: Request):
    if request.session.get("authenticated"):
        return {"authenticated": True, "username": request.session.get("username")}
    return {"authenticated": False, "username": "Invitado"}

@app.get("/api/logout", tags=["Auth"])
async def logout(request: Request):
    request.session.clear()
    return {"status": "ok"}

@app.post("/api/logout", tags=["Auth"])
async def logout_post(request: Request):
    request.session.clear()
    return {"status": "ok"}

@app.get("/api/news", tags=["News"])
async def get_news():
    articles = db.get_todays_articles()
    colombia = [a for a in articles if a.get("region") == "colombia"]
    glob = [a for a in articles if a.get("region") == "global"]
    
    featured = colombia[0] if colombia else (glob[0] if glob else None)
    
    dept_raw = defaultdict(list)
    for a in colombia:
        dept = a.get("department") or "Nacional"
        dept_raw[dept].append(a)
    
    EJE_CAFETERO = {"Caldas", "Risaralda", "Quindío", "Quindio"}
    sorted_depts = []
    for dept, arts in dept_raw.items():
        if dept != "Nacional":
            sorted_depts.append({"name": dept, "articles": arts})
            
    sorted_depts = sorted(sorted_depts, key=lambda x: len(x["articles"]) + (100 if x["name"] in EJE_CAFETERO else 0), reverse=True)
    if "Nacional" in dept_raw:
        sorted_depts.append({"name": "Nacional", "articles": dept_raw["Nacional"]})
        
    return {
        "featured": featured,
        "colombia": colombia,
        "global": glob,
        "departments": sorted_depts,
        "days_feed": _group_by_day(articles)
    }

@app.get("/api/stats", tags=["Admin"])
async def get_stats(authenticated: bool = Depends(is_authenticated)):
    articles = db.get_todays_articles()
    sources = db.get_all_sources()

    next_scan = "N/A"
    job = scheduler.get_job('scraping_job')
    if job and job.next_run_time:
        next_scan = job.next_run_time.isoformat()

    return {
        "articles_today": len(articles),
        "sources_count": len(sources),
        "recent_articles": articles[:5],
        "next_scan": next_scan
    }

@app.get("/api/ai-stats", tags=["Admin"])
async def get_ai_stats(authenticated: bool = Depends(is_authenticated)):
    return db.get_ai_stats()

@app.get("/api/logs", tags=["System"])
async def get_logs(authenticated: bool = Depends(is_authenticated)):
    today_str = date.today().isoformat()
    log_file = config.paths.logs_dir / f"bot_{today_str}.log"
    if not log_file.exists():
        return {"logs": ["No hay logs hoy."]}
    with open(log_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return {"logs": lines[-100:]}

@app.get("/api/dictionary", tags=["Admin"])
async def get_dictionary(authenticated: bool = Depends(is_authenticated)):
    dict_path = config.paths.base_dir / "data" / "tech_dictionary.json"
    if not dict_path.exists(): return {"entries": []}
    import json
    with open(dict_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    entries = []
    for group, items in data.items():
        for item in items:
            entries.append({"entity": item, "type": group})
    return {"entries": entries}

@app.get("/api/sources", tags=["Admin"])
async def get_sources(authenticated: bool = Depends(is_authenticated)):
    return {"sources": db.get_all_sources()}

@app.get("/api/admins", tags=["Admin"])
async def get_admins(authenticated: bool = Depends(is_authenticated)):
    return db.get_all_admins()

@app.post("/api/admins", tags=["Admin"])
async def create_admin(req_data: CreateAdminRequest, authenticated: bool = Depends(is_authenticated)):
    username = req_data.username.strip()
    password = req_data.password.strip()

    if not username:
        raise HTTPException(status_code=400, detail="Nombre de usuario inválido")
    if len(password) < 10:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 10 caracteres")

    success = db.create_admin_user(username, password)
    if not success:
        raise HTTPException(status_code=400, detail="No se pudo crear el administrador")
    return {"success": True}

@app.post("/api/sources", tags=["Admin"])
async def add_source(request: Request, authenticated: bool = Depends(is_authenticated)):
    new_source = await request.json()
    if not new_source.get("name") or not new_source.get("url"):
        raise HTTPException(status_code=400, detail="Faltan campos")
    db.add_source_db(new_source)
    return {"status": "ok", "sources": db.get_all_sources()}

@app.put("/api/sources/{source_id}", tags=["Admin"])
async def update_source(source_id: int, request: Request, authenticated: bool = Depends(is_authenticated)):
    data = await request.json()
    db.update_source_db(source_id, data)
    return {"status": "ok", "sources": db.get_all_sources()}

@app.delete("/api/sources/{source_id}", tags=["Admin"])
async def delete_source(source_id: int, authenticated: bool = Depends(is_authenticated)):
    db.delete_source_db(source_id)
    return {"status": "ok", "sources": db.get_all_sources()}

@app.post("/api/scrape", tags=["News"])
async def trigger_scrape(background_tasks: BackgroundTasks, authenticated: bool = Depends(is_authenticated)):
    background_tasks.add_task(main_orchestrator)
    return {"status": "working"}

@app.post("/api/admin/reprocess", tags=["Admin"])
async def reprocess(request: Request, authenticated: bool = Depends(is_authenticated)):
    data = await request.json()
    url = data.get("url")
    if not url: raise HTTPException(400, "URL requerida")
    from modules.services.ai_manager import AIManager
    ai = AIManager()
    success = await ai.reprocess_article_by_url(url)
    return {"status": "ok" if success else "error"}

@app.post("/api/admin/publish-telegram", tags=["Admin"])
async def publish_telegram(req_data: PublishTelegramRequest, authenticated: bool = Depends(is_authenticated)):
    article_data = db.get_article_by_url(req_data.url)
    if not article_data:
        raise HTTPException(status_code=404, detail="Noticia no encontrada")

    article = ScrapedArticle(
        title=article_data.get("title"),
        link=article_data.get("url"),
        source_name=article_data.get("source"),
        summary=article_data.get("title") or ""
    )
    article.region = article_data.get("region")
    article.department = article_data.get("department")
    article.image_url = article_data.get("image_url")
    article.ai_comment = article_data.get("ai_comment") or ""
    article.reel_script = article_data.get("reel_script") or ""

    nm = NotificationManager()
    success = await nm.send_telegram_visual_news(article)
    if not success:
        raise HTTPException(status_code=502, detail="No se pudo publicar en Telegram")

    db.mark_as_sent_to_telegram(req_data.url)
    return {"status": "ok"}

@app.get("/api/admin/news", tags=["Admin"])
async def get_admin_news(authenticated: bool = Depends(is_authenticated)):
    return {"news": db.get_all_news_manager(limit=100)}

@app.post("/api/test-telegram", tags=["System"])
async def test_telegram(authenticated: bool = Depends(is_authenticated)):
    nm = NotificationManager()
    success = await nm.send_telegram_message("🚀 Test de Conexión Admin")
    return {"status": "ok" if success else "error"}
