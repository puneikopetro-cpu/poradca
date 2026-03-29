from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse, Response
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
from backend.quiz.router import router as quiz_router

# Register models
import backend.auth.models  # noqa
import backend.financial_profile.models  # noqa
import backend.recommendations.models  # noqa
import backend.leads.models  # noqa
import backend.quiz.models  # noqa

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

# ── MAINTENANCE MODE ─────────────────────────────────────────────────────────
# Set MAINTENANCE_MODE=true in Railway env to hide site from public.
# Owner access: https://finadvisor.sk/?preview=fa_owner_2024
# To unlock permanently: add cookie fa_preview=fa_owner_2024 (done automatically)

_MAINTENANCE = os.environ.get("MAINTENANCE_MODE", "false").lower() == "true"
_PREVIEW_TOKEN = "fa_owner_2024"
_COOKIE_NAME = "fa_preview"

# Paths that are ALWAYS accessible (API, webhook, health)
_PUBLIC_PATHS = {"/health", "/telegram/webhook", "/robots.txt", "/sitemap.xml"}

_COMING_SOON_HTML = """<!DOCTYPE html>
<html lang="sk">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>FinAdvisor SK — Čoskoro</title>
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  body{min-height:100vh;display:flex;align-items:center;justify-content:center;
       background:linear-gradient(135deg,#0f172a 0%,#1e3a5f 100%);font-family:'Segoe UI',sans-serif;color:#fff}
  .card{text-align:center;padding:48px 40px;max-width:480px}
  .logo{font-size:48px;margin-bottom:16px}
  h1{font-size:2rem;font-weight:700;margin-bottom:8px}
  .sub{color:#94a3b8;font-size:1.1rem;margin-bottom:32px}
  .badge{display:inline-block;background:#1d4ed8;color:#fff;border-radius:20px;
         padding:6px 18px;font-size:13px;font-weight:600;letter-spacing:.5px;margin-bottom:32px}
  .info{background:rgba(255,255,255,.07);border-radius:12px;padding:20px;font-size:14px;color:#cbd5e1;line-height:1.8}
  .info b{color:#fff}
</style>
</head>
<body>
<div class="card">
  <div class="logo">💹</div>
  <h1>FinAdvisor SK</h1>
  <p class="sub">Finančné poradenstvo na najvyššej úrovni</p>
  <div class="badge">🚧 Čoskoro spustíme</div>
  <div class="info">
    <b>Pracujeme na niečom výnimočnom.</b><br><br>
    Investície · Hypotéky · Poistenie<br>
    II. a III. pilier · Daňová optimalizácia<br><br>
    <b>Kontakt:</b> petropuneiko@gmail.com<br>
    <b>Tel:</b> +421 908 118 957
  </div>
</div>
</body>
</html>"""


@app.middleware("http")
async def maintenance_gate(request: Request, call_next):
    if not _MAINTENANCE:
        return await call_next(request)

    path = request.url.path

    # Always allow API / internal paths
    if path in _PUBLIC_PATHS or path.startswith(("/leads", "/auth", "/quiz", "/profile", "/rec")):
        return await call_next(request)

    # Allow if secret token passed in query → set cookie and redirect
    token_param = request.query_params.get("preview", "")
    if token_param == _PREVIEW_TOKEN:
        redirect_path = path if path != "/" else "/"
        resp = Response(
            status_code=302,
            headers={"Location": redirect_path.split("?")[0]},
        )
        resp.set_cookie(_COOKIE_NAME, _PREVIEW_TOKEN, max_age=60 * 60 * 24 * 30, httponly=True, samesite="lax")
        return resp

    # Allow if cookie present and valid
    cookie_val = request.cookies.get(_COOKIE_NAME, "")
    if cookie_val == _PREVIEW_TOKEN:
        return await call_next(request)

    # Otherwise → Coming Soon
    return HTMLResponse(_COMING_SOON_HTML, status_code=200)
# ─────────────────────────────────────────────────────────────────────────────

# Auto-create all tables on startup (SQLite dev + PostgreSQL prod)
Base.metadata.create_all(bind=engine)
logger.info("DB tables ensured via create_all")

# Auto-seed NBS questions if table is empty
def _seed_questions():
    try:
        import json as _json
        from backend.database import SessionLocal as _SL
        from backend.quiz.models import Question as _Q
        _db = _SL()
        try:
            if _db.query(_Q).count() == 0:
                _json_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "questions.json")
                if os.path.exists(_json_path):
                    with open(_json_path, encoding="utf-8") as f:
                        qs = _json.load(f)
                    for q in qs:
                        _db.add(_Q(number=q["number"], section=q["section"],
                                   sector=q["sector"], level=q["level"],
                                   text=q["text"], options=q["options"],
                                   correct=q["correct"]))
                    _db.commit()
                    logger.info("Seeded %d NBS questions", len(qs))
        finally:
            _db.close()
    except Exception as e:
        logger.warning("Question seed failed: %s", e)

_seed_questions()

app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(rec_router)
app.include_router(leads_router)
app.include_router(quiz_router)


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
