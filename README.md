# 🤖 El Dev Criollo - Intelligence Hub

![Status](https://img.shields.io/badge/Status-Activo-brightgreen)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![Docker](https://img.shields.io/badge/Docker-Ready-cyan)
![AI](https://img.shields.io/badge/AI-Ollama--Gemma4-orange)

**El Dev Criollo** es un centro de inteligencia de noticias automatizado que combina web scraping, análisis satírico impulsado por IA y notificaciones visuales multi-canal. Diseñado para mantenerte informado sobre el ecosistema Tech y Startups sin el ruido mediático tradicional.

---

## ✨ Características Principales

*   **🕵️‍♂️ Scraper Multi-fuente:** Soporte nativo para RSS y sitios web estáticos con extracción inteligente de metadatos e imágenes.
*   **🧠 Análisis con IA Local:** Integración con **Ollama** utilizando el modelo **Gemma 4** para generar opiniones sarcásticas y guiones de video (TikTok/Reels).
*   **⏰ Autonomía Total:** Programación interna mediante `APScheduler` para escaneo continuo cada 30 minutos.
*   **📲 Notificaciones Visuales:** Envío enriquecido a **Telegram** incluyendo fotos de las noticias, resúmenes y opiniones de la IA.
*   **📊 Dashboard Moderno:** Interfaz web interactiva (FastAPI + Vanilla CSS) con estética *glassmorphism* y modo oscuro premium.
*   **🌍 Multi-región:** Clasificación automática de noticias entre el ecosistema Colombia y el radar global.

---

## 🚀 Propinas de Inicio Rápido

La forma más sencilla de correr el hub es mediante **Docker Compose**:

```bash
# 1. Clonar el repo e ingresar
cd eldevcriollo

# 2. Configurar credenciales
cp .env.example .env
# Edita el .env con tu TELEGRAM_BOT_TOKEN y CHAT_ID

# 3. Levantar con Docker
docker-compose up -d --build
```
El dashboard estará disponible en: `http://localhost:8088`

---

## 🛠 Arquitectura del Proyecto

El sistema utiliza una estructura modular **M-S-C** (Models, Services, Core):

-   **`/modules/core`**: El orquestador principal (`app.py`) que maneja el flujo de datos.
-   **`/modules/services`**: Capa de negocio (Scraper, AI, Notification, Database, Report).
-   **`/modules/models`**: Tipado fuerte y configuraciones centrales.
-   **`/templates` & `/static`**: Frontend moderno y minimalista.

---

## ⚙️ Configuración (.env)

| Variable | Descripción |
| :--- | :--- |
| `TELEGRAM_BOT_TOKEN` | Token oficial de tu bot creado en @BotFather. |
| `TELEGRAM_CHAT_ID` | Tu ID de chat personal (o grupo) para recibir alertas. |
| `OLLAMA_URL` | URL del servidor Ollama (por defecto: `host.docker.internal:11434`). |
| `OLLAMA_MODEL` | Modelo a utilizar (recomendado: `gemma4:31b-cloud` o similares). |

---

## 📝 Licencia

Este proyecto es una herramienta de experimentación para la comunidad Tech Colombiana. Úsalo con sabiduría y un poco de sarcasmo.

---
*Hecho con ❤️ por El Dev Criollo.*
