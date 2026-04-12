import sys
from pathlib import Path
from dotenv import load_dotenv

# 1. Ajustar el PYTHONPATH para asegurar que modules/ sea detectado sin instalar el paquete
sys.path.insert(0, str(Path(__file__).parent))

# 2. Cargar variables desde el archivo .env central (en caso de que app.py tarde)
load_dotenv()

# 3. Delegar control limpio sobre el submódulo central
from modules.core.app import main_orchestrator

import uvicorn

if __name__ == "__main__":
    # Arrancamos Uvicorn (Agnóstico a Windows/Linux)
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
