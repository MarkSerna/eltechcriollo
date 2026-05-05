#!/bin/bash

# Script para migrar de requirements.txt a Poetry
# Uso: bash migrate_to_poetry.sh

echo "🚀 Iniciando migración a Poetry..."

# 1. Verificar si Poetry está instalado
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry no está instalado. Instalar con:"
    echo "   curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

# 2. Crear entorno virtual e instalar dependencias
echo "📦 Instalando dependencias con Poetry..."
poetry install

# 3. Actualizar Dockerfile para usar Poetry
echo "✏️ Actualizando Dockerfile..."
sed -i 's/pip install.*requirements.txt/poetry install --no-root/g' Dockerfile

# 4. Actualizar CI para usar Poetry
echo "✅ Migración completada!"
echo ""
echo "Para activar el entorno virtual: poetry shell"
echo "Para ejecutar el servidor: poetry run uvicorn api:app --reload"