from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure module visibility
sys.path.insert(0, str(Path(__file__).parent))
load_dotenv()

from modules.core.app import main_orchestrator
from modules.services.database_manager import DatabaseManager
from modules.utils.logger import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler

app = FastAPI(title="El Tech Criollo - Intelligence Hub")

# Configuración de Programación Automática (Cada 30 min)
@app.on_event("startup")
async def start_scheduler():
    scheduler = AsyncIOScheduler()
    # Ejecutamos el orquestador cada 30 minutos
    scheduler.add_job(main_orchestrator, 'interval', minutes=30)
    scheduler.start()
    logger.info("⏰ Programador activado: Escaneo autónomo cada 30 minutos configurado.")

# Setup directories for static and templates
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
templates_dir = Path(__file__).parent / "templates"
templates_dir.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

db = DatabaseManager()
db.initialize_schema()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Renderiza el tablero interactivo de lectura con Vanilla UI separando por región."""
    articles = db.get_todays_articles()
    
    colombia_news = [a for a in articles if a.get("region") == "colombia"]
    global_news = [a for a in articles if a.get("region") == "global"]
    
    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={"colombia_news": colombia_news, "global_news": global_news}
    )

from modules.services.notification_manager import NotificationManager

@app.post("/api/test-telegram")
async def test_telegram():
    """Envía un mini-reporte de prueba para verificar que el Bot funciona."""
    nm = NotificationManager()
    test_file = Path("reports/test_connection.md")
    test_file.write_text("# Test de Conexión 🚀\n\nSi estás recibiendo esto, ¡tu integración con **El Tech Criollo** está perfecta!\n\n---\n*Enviado desde el Dashboard Local*")
    
    success = nm.send_telegram_file(test_file)
    if success:
        return JSONResponse(content={"status": "ok", "message": "¡Mensaje de prueba enviado! Revisa tu Telegram."})
    else:
        return JSONResponse(status_code=500, content={"status": "error", "message": "Falla al enviar. Revisa logs y credenciales."})

@app.post("/api/scrape")
async def trigger_scrape(background_tasks: BackgroundTasks):
    """Endpoint para forzar que el robot extraiga y Ollama analice asíncronamente."""
    logger.info("🚀 Petición de Scraping forzada vía API Web..")
    def background_job():
        main_orchestrator()
        
    background_tasks.add_task(background_job)
    return JSONResponse(content={"status": "working", "message": "Scraping e Inferencia IA ha comenzado en fondo. Recarga la página en unos segundos."})
