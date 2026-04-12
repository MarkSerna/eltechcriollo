FROM python:3.11-slim

# Evitar que python escriba bytecode (.pyc) a disco y forzar purga de stdout buffering.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Crear carpeta del contenedor
WORKDIR /app

# Instalar dependencias primero para aprovechar caché en las capas de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente completo
COPY . .

# Comando default: Correr el orquestador single-shot.
# Si prefieres que el contenedor no muera nunca se requeriría un while loop o librería schedule.
CMD ["python", "main.py"]
