# --- Python Runtime for Backend API ---
FROM python:3.11-slim-bookworm

# Evitar que python escriba bytecode (.pyc) a disco y forzar stdout buffering
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias del sistema mínimas para Playwright/Chromium y PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    libv4l-0 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcursor1 \
    libxi6 \
    libxtst6 \
    fonts-liberation \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar navegador Chromium para el scraper
RUN playwright install chromium
RUN playwright install-deps chromium

# Copiar el código fuente del backend
COPY . .

# Asegurar que existan los directorios necesarios
RUN mkdir -p data logs reports static templates

# Exponer el puerto para Render
EXPOSE 8000

# Comando default: Uvicorn para servir la API respetando el puerto de Render
CMD ["sh", "-c", "uvicorn api:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
