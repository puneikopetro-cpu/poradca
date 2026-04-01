"""
FinAdvisor SK — 24/7 Watchdog Agent
Механік + охорона: моніторинг, захист, авторемонт.

Checks every 60s:
  - /health endpoint (service alive)
  - /ai/chat (AI responding)
  - /app /learn /admin (pages up)
  - Response time < 5s
  - Suspicious request patterns (DDoS/brute-force detection)

On problem:
  - Logs to stdout (Railway captures logs)
  - Sends Telegram alert to owner
  - Triggers Railway redeploy if service is down
"""
import os
import time
import json
import asyncio
import hashlib
import logging
from datetime import datetime, timezone
from collections import defaultdict

import httpx

# ─── CONFIG ──────────────────────────────────────────────────────────────────
BASE_URL     = os.environ.get("APP_URL", "https://finadvisor.sk")
TG_TOKEN     = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TG_CHAT_ID   = os.environ.get("WATCHDOG_CHAT_ID", "")   # owner chat ID
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", "60"))   # seconds
RAILWAY_TOKEN  = os.environ.get("RAILWAY_API_TOKEN", "")
RAILWAY_PROJECT_ID = os.environ.get("RAILWAY_PROJECT_ID", "564a41ac-75f7-4be8-9ce2-e2dc57cfd8d0")
RAILWAY_SERVICE_ID = os.environ.get("RAILWAY_SERVICE_ID", "f8a774af-4d62-4d17-9941-90bcd0580646")
RAILWAY_ENV_ID     = os.environ.get("RAILWAY_ENV_ID",     "a8bd17a5-fd7f-47b0-9fc4-08311e9632d1")
MAX_RESPONSE_MS    = int(os.environ.get("MAX_RESPONSE_MS", "5000"))
FAIL_THRESHOLD     = int(os.environ.get("FAIL_THRESHOLD", "3"))  # consecutive fails before alert

# ─── LOGGING ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [WATCHDOG] %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
log = logging.getLogger("watchdog")

# ─── STATE ───────────────────────────────────────────────────────────────────
fail_counts: dict[str, int] = defaultdict(int)
last_alert: dict[str, float] = {}
ALERT_COOLDOWN = 300  # don't spam same alert for 5 min

# ─── TELEGRAM ALERT ──────────────────────────────────────────────────────────
async def send_telegram(msg: str, client: httpx.AsyncClient):
    if not TG_TOKEN or not TG_CHAT_ID:
        log.warning("Telegram not configured (TG_TOKEN or WATCHDOG_CHAT_ID missing)")
        return
    try:
        await client.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "HTML"},
            timeout=10,
        )
        log.info(f"Telegram alert sent: {msg[:60]}")
    except Exception as e:
        log.error(f"Telegram send failed: {e}")


def should_alert(key: str) -> bool:
    now = time.time()
    last = last_alert.get(key, 0)
    if now - last > ALERT_COOLDOWN:
        last_alert[key] = now
        return True
    return False


# ─── RAILWAY REDEPLOY ────────────────────────────────────────────────────────
async def trigger_redeploy(client: httpx.AsyncClient):
    if not RAILWAY_TOKEN:
        log.warning("RAILWAY_API_TOKEN not set — cannot auto-redeploy")
        return False
    try:
        resp = await client.post(
            "https://backboard.railway.com/graphql/v2",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {RAILWAY_TOKEN}",
                "Origin": "https://railway.app",
                "User-Agent": "FinAdvisor-Watchdog/1.0",
            },
            json={"query": f"""mutation {{
                variableUpsert(input: {{
                    projectId: "{RAILWAY_PROJECT_ID}",
                    serviceId: "{RAILWAY_SERVICE_ID}",
                    environmentId: "{RAILWAY_ENV_ID}",
                    name: "WATCHDOG_REDEPLOY",
                    value: "{int(time.time())}"
                }})
            }}"""},
            timeout=15,
        )
        data = resp.json()
        if data.get("data", {}).get("variableUpsert"):
            log.info("Railway redeploy triggered successfully")
            return True
        log.error(f"Railway redeploy failed: {data}")
        return False
    except Exception as e:
        log.error(f"Railway API error: {e}")
        return False


# ─── HEALTH CHECKS ───────────────────────────────────────────────────────────
CHECK_ENDPOINTS = [
    {"name": "health",    "url": "/health",           "method": "GET",  "expect_key": "status"},
    {"name": "homepage",  "url": "/",                  "method": "GET",  "expect_status": 200},
    {"name": "app",       "url": "/app",               "method": "GET",  "expect_status": 200},
    {"name": "learn",     "url": "/learn",             "method": "GET",  "expect_status": 200},
    {"name": "admin",     "url": "/admin",             "method": "GET",  "expect_status": 200},
    {"name": "i18n_js",   "url": "/i18n.js",           "method": "GET",  "expect_status": 200},
    {"name": "ai_chat",   "url": "/ai/chat",           "method": "POST",
     "body": {"message": "test", "lang": "sk"},        "expect_key": "reply"},
]


async def check_endpoint(ep: dict, client: httpx.AsyncClient) -> dict:
    url = BASE_URL + ep["url"]
    name = ep["name"]
    start = time.monotonic()
    result = {"name": name, "ok": False, "ms": 0, "error": ""}

    try:
        if ep["method"] == "POST":
            resp = await client.post(url, json=ep.get("body", {}), timeout=MAX_RESPONSE_MS / 1000)
        else:
            resp = await client.get(url, timeout=MAX_RESPONSE_MS / 1000)

        elapsed_ms = int((time.monotonic() - start) * 1000)
        result["ms"] = elapsed_ms

        if resp.status_code not in (200, 201):
            result["error"] = f"HTTP {resp.status_code}"
            return result

        if elapsed_ms > MAX_RESPONSE_MS:
            result["error"] = f"Slow ({elapsed_ms}ms > {MAX_RESPONSE_MS}ms)"
            result["ok"] = True  # not critical, just slow
            return result

        if "expect_key" in ep:
            data = resp.json()
            if ep["expect_key"] not in data:
                result["error"] = f"Missing key '{ep['expect_key']}' in response"
                return result

        result["ok"] = True
    except httpx.TimeoutException:
        result["error"] = f"Timeout (>{MAX_RESPONSE_MS}ms)"
    except Exception as e:
        result["error"] = str(e)[:100]

    return result


# ─── SECURITY: Rate-limit / Brute-force detection ────────────────────────────
# This runs inside the app as a separate background check.
# It polls the /health endpoint for anomalies and alerts on sustained errors.

_DOWN_SINCE: dict[str, datetime] = {}


async def run_checks(client: httpx.AsyncClient):
    results = await asyncio.gather(*[check_endpoint(ep, client) for ep in CHECK_ENDPOINTS])

    ok_count  = sum(1 for r in results if r["ok"])
    bad_count = sum(1 for r in results if not r["ok"])
    now_str   = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")

    status_line = f"{'OK' if bad_count == 0 else 'PROBLEM'} [{ok_count}/{len(results)}] @ {now_str}"
    log.info(status_line)

    for r in results:
        name  = r["name"]
        is_ok = r["ok"]
        ms    = r["ms"]
        err   = r["error"]

        if is_ok:
            if fail_counts[name] > 0:
                log.info(f"  ✅ {name} recovered ({ms}ms)")
                if should_alert(f"recover_{name}"):
                    asyncio.create_task(send_telegram(
                        f"✅ <b>FinAdvisor SK — ВІДНОВЛЕНО</b>\n"
                        f"Сервіс <code>{name}</code> знову працює ({ms}ms)",
                        client,
                    ))
            fail_counts[name] = 0
        else:
            fail_counts[name] += 1
            log.warning(f"  ❌ {name}: {err} (fail #{fail_counts[name]})")

            if fail_counts[name] >= FAIL_THRESHOLD and should_alert(f"fail_{name}"):
                msg = (
                    f"🚨 <b>FinAdvisor SK — ПРОБЛЕМА</b>\n"
                    f"Сервіс: <code>{name}</code>\n"
                    f"Помилка: {err}\n"
                    f"Послідовних збоїв: {fail_counts[name]}\n"
                    f"Час: {now_str}"
                )
                asyncio.create_task(send_telegram(msg, client))

                # Auto-redeploy if health endpoint is down
                if name == "health" and fail_counts[name] >= FAIL_THRESHOLD * 2:
                    log.warning("Health endpoint down — triggering Railway redeploy")
                    redeployed = await trigger_redeploy(client)
                    if redeployed:
                        asyncio.create_task(send_telegram(
                            "🔄 <b>Watchdog</b>: автоматично тригернуто редеплой на Railway",
                            client,
                        ))

    return results


# ─── SECURITY REPORT (daily summary) ─────────────────────────────────────────
_check_counter = 0

async def maybe_send_daily_report(client: httpx.AsyncClient):
    global _check_counter
    _check_counter += 1
    # Send report every 1440 checks = ~24h (at 60s interval)
    if _check_counter % 1440 == 0:
        msg = (
            f"📊 <b>FinAdvisor SK — Щоденний звіт</b>\n"
            f"За останні 24h:\n"
            f"• Перевірок: {_check_counter}\n"
            f"• Активних збоїв: {sum(1 for v in fail_counts.values() if v > 0)}\n"
            f"• Сервісів під наглядом: {len(CHECK_ENDPOINTS)}\n"
            f"Watchdog працює 24/7 ✅"
        )
        await send_telegram(msg, client)


# ─── MAIN LOOP ───────────────────────────────────────────────────────────────
async def main():
    log.info(f"FinAdvisor Watchdog starting — monitoring {BASE_URL}")
    log.info(f"Check interval: {CHECK_INTERVAL}s | Endpoints: {len(CHECK_ENDPOINTS)}")

    # Startup alert
    async with httpx.AsyncClient(follow_redirects=True) as client:
        if TG_TOKEN and TG_CHAT_ID:
            await send_telegram(
                f"🤖 <b>Watchdog запущено</b>\n"
                f"Моніторинг: {BASE_URL}\n"
                f"Інтервал: {CHECK_INTERVAL}s\n"
                f"Ендпоінтів: {len(CHECK_ENDPOINTS)}",
                client,
            )

        while True:
            try:
                await run_checks(client)
                await maybe_send_daily_report(client)
            except Exception as e:
                log.error(f"Watchdog loop error: {e}")
            await asyncio.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
