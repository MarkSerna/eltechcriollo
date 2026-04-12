import logging
import sys
from datetime import datetime
from modules.models.config import config

def setup_logger():
    """Configura el sistema de logs con salida a consola y rotación/creación en disco."""
    logger = logging.getLogger("ElDevCriollo")
    
    # Prevenir que agregue repetidamente handlers
    if logger.handlers:
        return logger

    # Obtener el nivel de log desde la configuración (Info, Debug, Error)
    numeric_level = getattr(logging, config.log_level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Asegurar que sys.stdout soporte UTF-8 en Windows
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        
    # Salida por consola (STDOUT)
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(numeric_level)
    stdout_handler.setFormatter(formatter)
    
    # Salida por Archivo Diario
    today_str = datetime.now().strftime("%Y-%m-%d")
    log_file = config.paths.logs_dir / f"bot_{today_str}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    
    logger.addHandler(stdout_handler)
    logger.addHandler(file_handler)
    
    return logger

# Instancia global y lista para importar
logger = setup_logger()
