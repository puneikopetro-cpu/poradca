from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import HTTPException as FastAPIHTTPException
import os

from backend.config import settings
from backend.database import Base, engine
from backend.logger import configure_logging, get_logger
from backend.middleware import RequestLoggingMiddleware
from backend.exception_handlers import register_exception_handlers
from backend.auth.router import router as auth_router
from backend.financial_profile.router import router as profile_router
from backend.recommendations.router import router as rec_router
from backend.leads.router import router as leads_router

# Register models
import backend.auth.models  # noqa
import backend.financial_profile.models  # noqa
import backend.recommendations.models  # noqa
import backend.leads.models  # noqa

configure_logging()
logger = get_logger(__name__)

app = FastAPI(
    title="Financial Advisor API — Slovakia",
    description="MVP платформа фінансового консультанта для Словаччини",
    version="1.0.0",
)

# Middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

# Auto-create all tables on startup (SQLite dev + PostgreSQL prod)
Base.metadata.create_all(bind=engine)
logger.info("DB tables ensured via create_all")

app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(rec_router)
app.include_router(leads_router)


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok", "service": "Financial Advisor API"}


@app.get("/", include_in_schema=False)
def serve_frontend():
    frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
    return FileResponse(frontend_path)


@app.get("/robots.txt", include_in_schema=False)
def robots():
    return FileResponse(os.path.join(os.path.dirname(__file__), "..", "frontend", "robots.txt"), media_type="text/plain")


@app.get("/sitemap.xml", include_in_schema=False)
def sitemap():
    return FileResponse(os.path.join(os.path.dirname(__file__), "..", "frontend", "sitemap.xml"), media_type="application/xml")


@app.get("/privacy", include_in_schema=False)
def privacy():
    return FileResponse(os.path.join(os.path.dirname(__file__), "..", "frontend", "privacy.html"))


@app.get("/admin", include_in_schema=False)
def admin_panel():
    return FileResponse(os.path.join(os.path.dirname(__file__), "..", "frontend", "admin.html"))


@app.get("/og-image.png", include_in_schema=False)
@app.get("/og-image.svg", include_in_schema=False)
def og_image():
    return FileResponse(os.path.join(os.path.dirname(__file__), "..", "frontend", "og-image.svg"), media_type="image/svg+xml")


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    path_404 = os.path.join(os.path.dirname(__file__), "..", "frontend", "404.html")
    if os.path.exists(path_404):
        return FileResponse(path_404, status_code=404)
    return JSONResponse({"error": "Not found"}, status_code=404)


# Serve static frontend files
_frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(_frontend_dir):
    app.mount("/static", StaticFiles(directory=_frontend_dir), name="static")


@app.post("/telegram/webhook", tags=["telegram"])
async def telegram_webhook(request: Request):
    """Receives Telegram updates via webhook (used in production)."""
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        return JSONResponse({"ok": False}, status_code=503)
    try:
        from telegram import Update
        from telegram.ext import Application
        from telegram_bot.bot import build_application

        update_data = await request.json()
        app_instance = await build_application(token)
        update = Update.de_json(update_data, app_instance.bot)
        await app_instance.process_update(update)
        return {"ok": True}
    except Exception as e:
        logger.exception("Webhook error: %s", e)
        return JSONResponse({"ok": False}, status_code=500)
