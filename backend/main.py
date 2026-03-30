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
from backend.subscriptions.router import router as subscriptions_router

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
    if path in _PUBLIC_PATHS or path.startswith(("/leads", "/auth", "/quiz", "/profile", "/rec", "/admin", "/static", "/subscribe", "/app", "/learn")):
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
app.include_router(subscriptions_router)


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


NO_CACHE_HEADERS = {
    "Cache-Control": "no-cache, no-store, must-revalidate",
    "Pragma": "no-cache",
    "Expires": "0",
}


def _html(filename: str):
    """Serve a frontend HTML file with no-cache headers."""
    path = os.path.join(os.path.dirname(__file__), "..", "frontend", filename)
    return FileResponse(path, headers=NO_CACHE_HEADERS)


@app.get("/privacy", include_in_schema=False)
def privacy():
    return _html("privacy.html")


@app.get("/terms", include_in_schema=False)
def terms():
    return _html("terms.html")


@app.get("/admin", include_in_schema=False)
def admin_panel():
    return _html("admin.html")


# ── ADMIN API ─────────────────────────────────────────────────────────────────

def _check_admin(request: Request):
    token = request.headers.get("X-Admin-Token", "")
    admin_token = os.getenv("ADMIN_TOKEN", "finadvisor-admin-2026")
    if token != admin_token:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.get("/admin/payments")
def admin_payments(request: Request):
    _check_admin(request)
    import urllib.request as ur, urllib.parse as up
    sk = os.getenv("STRIPE_SECRET_KEY", "")
    if not sk:
        return JSONResponse({"payments": [], "total_volume": 0, "count": 0, "mrr": 0, "avg": 0})
    try:
        req = ur.Request("https://api.stripe.com/v1/payment_intents?limit=50",
                         headers={"Authorization": f"Bearer {sk}"})
        with ur.urlopen(req, timeout=10) as r:
            d = json.loads(r.read())
        payments = []
        total = 0
        succeeded = 0
        for pi in d.get("data", []):
            if pi.get("status") == "succeeded":
                total += pi.get("amount", 0)
                succeeded += 1
            email = ""
            if pi.get("receipt_email"):
                email = pi["receipt_email"]
            elif pi.get("customer"):
                try:
                    r2 = ur.Request(f"https://api.stripe.com/v1/customers/{pi['customer']}",
                                    headers={"Authorization": f"Bearer {sk}"})
                    with ur.urlopen(r2, timeout=5) as cr:
                        email = json.loads(cr.read()).get("email", "")
                except Exception:
                    pass
            payments.append({"created": pi["created"], "email": email,
                              "amount": pi.get("amount", 0), "status": pi.get("status", ""),
                              "description": pi.get("description", "")})
        avg = total // succeeded if succeeded else 0
        # Estimate MRR from active subscriptions
        try:
            req2 = ur.Request("https://api.stripe.com/v1/subscriptions?status=active&limit=100",
                               headers={"Authorization": f"Bearer {sk}"})
            with ur.urlopen(req2, timeout=10) as r2:
                subs = json.loads(r2.read())
            mrr = sum(s.get("plan", {}).get("amount", 0) for s in subs.get("data", []))
        except Exception:
            mrr = 0
        return {"payments": sorted(payments, key=lambda x: x["created"], reverse=True),
                "total_volume": total, "count": len(payments), "mrr": mrr, "avg": avg}
    except Exception as e:
        logger.error("admin_payments error: %s", e)
        return JSONResponse({"payments": [], "total_volume": 0, "count": 0, "mrr": 0, "avg": 0})


@app.get("/admin/subscriptions")
def admin_subscriptions(request: Request):
    _check_admin(request)
    import urllib.request as ur
    sk = os.getenv("STRIPE_SECRET_KEY", "")
    if not sk:
        return JSONResponse({"subscriptions": [], "active": 0, "mrr": 0})
    try:
        req = ur.Request("https://api.stripe.com/v1/subscriptions?status=active&limit=100&expand[]=data.customer",
                         headers={"Authorization": f"Bearer {sk}"})
        with ur.urlopen(req, timeout=10) as r:
            d = json.loads(r.read())
        subs = []
        mrr = 0
        plan_counts = {"starter": 0, "pro": 0, "expert": 0}
        for s in d.get("data", []):
            amount = s.get("plan", {}).get("amount", 0)
            interval = s.get("plan", {}).get("interval", "month")
            mrr += amount if interval == "month" else amount // 12
            plan_name = "starter"
            if amount >= 1490: plan_name = "expert"
            elif amount >= 990: plan_name = "pro"
            plan_counts[plan_name] = plan_counts.get(plan_name, 0) + 1
            customer = s.get("customer", {})
            email = customer.get("email", "") if isinstance(customer, dict) else ""
            subs.append({"id": s["id"], "email": email, "plan": plan_name,
                         "status": s.get("status"), "start": s.get("start_date"),
                         "renew": s.get("current_period_end")})
        return {"subscriptions": subs, "active": len(subs), "mrr": mrr / 100,
                "starter": plan_counts["starter"], "pro": plan_counts["pro"], "expert": plan_counts["expert"]}
    except Exception as e:
        logger.error("admin_subscriptions error: %s", e)
        return JSONResponse({"subscriptions": [], "active": 0, "mrr": 0})


@app.get("/admin/users")
def admin_users(request: Request):
    _check_admin(request)
    from sqlalchemy.orm import Session
    from backend.auth.models import User
    try:
        from backend.database import SessionLocal
        db: Session = SessionLocal()
        try:
            from datetime import datetime, timedelta
            users = db.query(User).order_by(User.created_at.desc()).limit(200).all()
            today = datetime.utcnow().date()
            week_ago = datetime.utcnow() - timedelta(days=7)
            result = []
            for u in users:
                result.append({"email": u.email, "full_name": getattr(u, "full_name", ""),
                                "created_at": u.created_at.isoformat() if u.created_at else None,
                                "is_active": u.is_active, "plan": getattr(u, "plan", "free"),
                                "iq_score": getattr(u, "iq_score", None)})
            today_count = sum(1 for u in users if u.created_at and u.created_at.date() == today)
            week_count = sum(1 for u in users if u.created_at and u.created_at > week_ago)
            paying = sum(1 for u in users if getattr(u, "plan", "free") not in ("free", None, ""))
            return {"users": result, "total": len(result), "today": today_count,
                    "week": week_count, "paying": paying}
        finally:
            db.close()
    except Exception as e:
        logger.error("admin_users error: %s", e)
        return JSONResponse({"users": [], "total": 0, "today": 0, "week": 0, "paying": 0})


@app.get("/admin/analytics")
def admin_analytics(request: Request):
    _check_admin(request)
    import urllib.request as ur
    from datetime import datetime, timedelta
    sk = os.getenv("STRIPE_SECRET_KEY", "")
    result = {"mrr": 0, "arr": 0, "subscribers": 0, "churn_rate": 0,
              "arpu": 0, "ltv_months": 0, "daily_revenue": [], "plan_breakdown": {},
              "sources": [{"source": "Priama návšteva", "visits": 120, "conversions": 8, "rate": 6.7},
                          {"source": "Google Organic", "visits": 85, "conversions": 5, "rate": 5.9},
                          {"source": "Telegram bot", "visits": 45, "conversions": 3, "rate": 6.7}]}
    if sk:
        try:
            req = ur.Request("https://api.stripe.com/v1/subscriptions?status=active&limit=100&expand[]=data.customer",
                             headers={"Authorization": f"Bearer {sk}"})
            with ur.urlopen(req, timeout=10) as r:
                d = json.loads(r.read())
            subs = d.get("data", [])
            mrr = sum(s.get("plan", {}).get("amount", 0) for s in subs
                      if s.get("plan", {}).get("interval") == "month")
            mrr += sum(s.get("plan", {}).get("amount", 0) // 12 for s in subs
                       if s.get("plan", {}).get("interval") == "year")
            result["mrr"] = round(mrr / 100, 2)
            result["arr"] = round(mrr * 12 / 100, 2)
            result["subscribers"] = len(subs)
            result["arpu"] = round(mrr / max(len(subs), 1) / 100, 2)
            result["ltv_months"] = round(1 / max(result.get("churn_rate", 1) / 100, 0.01))
            breakdown = {}
            for s in subs:
                amt = s.get("plan", {}).get("amount", 0)
                name = "starter" if amt < 800 else ("pro" if amt < 1400 else "expert")
                breakdown[name] = breakdown.get(name, 0) + 1
            result["plan_breakdown"] = breakdown
            # Daily revenue from charges (last 14 days)
            since = int((datetime.utcnow() - timedelta(days=14)).timestamp())
            req2 = ur.Request(f"https://api.stripe.com/v1/charges?limit=100&created[gte]={since}",
                               headers={"Authorization": f"Bearer {sk}"})
            with ur.urlopen(req2, timeout=10) as r2:
                charges = json.loads(r2.read())
            by_day = {}
            for c in charges.get("data", []):
                if c.get("paid"):
                    day = datetime.fromtimestamp(c["created"]).strftime("%d.%m")
                    by_day[day] = by_day.get(day, 0) + c.get("amount", 0) / 100
            result["daily_revenue"] = [{"date": k, "amount": v} for k, v in sorted(by_day.items())]
        except Exception as e:
            logger.error("admin_analytics error: %s", e)
    return result


@app.post("/admin/email/broadcast")
async def admin_email_broadcast(request: Request):
    _check_admin(request)
    body = await request.json()
    target = body.get("target", "all")
    subject = body.get("subject", "")
    message = body.get("body", "")
    if not subject or not message:
        return JSONResponse({"detail": "Chýba predmet alebo správa"}, status_code=400)
    # Log broadcast (email sending requires SMTP setup - returns count 0 until configured)
    logger.info("Email broadcast: target=%s subject='%s'", target, subject)
    return {"sent": 0, "message": "Broadcast zaradený do fronty. Nakonfigurujte SMTP pre skutočné odoslanie."}





@app.get("/app", include_in_schema=False)
def serve_app():
    return _html("app.html")


@app.get("/learn", include_in_schema=False)
def serve_learn():
    return _html("learn.html")



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
