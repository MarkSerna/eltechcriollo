FROM python:3.11-slim

# Evitar que python escriba bytecode (.pyc) a disco y forzar purga de stdout buffering.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Crear carpeta del contenedor
WORKDIR /app

# Instalar dependencias del sistema requeridas por Playwright/Chromium
# Se añaden fuentes y librerías adicionales para evitar errores en Debian/Slim
RUN apt-get update && apt-get install -y \
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
    fonts-noto-color-emoji \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias primero para aprovechar caché en las capas de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar navegadores de Playwright (Solo Chromium para ahorrar espacio)
RUN playwright install chromium

# Copiar el código fuente completo
COPY . .

# Comando default: Correr el orquestador single-shot.
# Si prefieres que el contenedor no muera nunca se requeriría un while loop o librería schedule.
CMD ["python", "main.py"]
