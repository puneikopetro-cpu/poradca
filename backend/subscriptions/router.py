"""Stripe subscription checkout + webhook endpoint."""
import os
import logging
from fastapi import APIRouter, Request, Header
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/subscribe", tags=["subscriptions"])

_DOMAIN = os.environ.get("APP_DOMAIN", "https://finadvisor.sk")

_AMOUNTS = {
    "starter_monthly": 490,  "starter_annual": 3900,
    "pro_monthly": 990,      "pro_annual": 7900,
    "expert_monthly": 1490,  "expert_annual": 11900,
}


class CheckoutRequest(BaseModel):
    email: str
    plan: str       # starter | pro | expert
    billing: str = "monthly"


def _stripe():
    key = os.environ.get("STRIPE_SECRET_KEY", "")
    if not key:
        return None, "Stripe not configured"
    try:
        import stripe as s  # type: ignore
        s.api_key = key
        return s, None
    except ImportError:
        return None, "stripe library not installed"


@router.post("/checkout")
async def create_checkout_session(body: CheckoutRequest):
    s, err = _stripe()
    if err:
        return JSONResponse({"error": err}, status_code=503)

    price_key = f"{body.plan}_{body.billing}"
    price_id = os.environ.get(f"STRIPE_PRICE_{body.plan.upper()}_{body.billing.upper()}", "")

    if not price_id:
        interval = "year" if body.billing == "annual" else "month"
        try:
            price_obj = s.Price.create(
                unit_amount=_AMOUNTS.get(price_key, 990),
                currency="eur",
                recurring={"interval": interval},
                product_data={"name": f"FinAdvisor SK — {body.plan.capitalize()}"},
            )
            price_id = price_obj["id"]
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    try:
        session = s.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            customer_email=body.email,
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=f"{_DOMAIN}/subscribe/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{_DOMAIN}/app?cancelled=1",
            metadata={"plan": body.plan, "billing": body.billing},
        )
        return {"url": session["url"]}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/success", response_class=HTMLResponse)
async def subscription_success(session_id: str = ""):
    """Redirect page after successful Stripe payment."""
    return HTMLResponse(content="""<!DOCTYPE html>
<html lang="sk">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="8;url=/learn">
<title>Platba úspešná — FinAdvisor SK</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0f172a;color:#f1f5f9;font-family:-apple-system,sans-serif;
     display:flex;align-items:center;justify-content:center;min-height:100vh;text-align:center;padding:24px}
.card{background:#1e293b;border:1px solid #334155;border-radius:24px;padding:48px 32px;max-width:460px}
.icon{font-size:64px;margin-bottom:20px}
h1{font-size:24px;font-weight:800;margin-bottom:10px}
p{color:#94a3b8;font-size:14px;line-height:1.6;margin-bottom:16px}
.btn{display:inline-block;background:#2563eb;color:#fff;border-radius:12px;
     padding:14px 28px;font-size:15px;font-weight:700;text-decoration:none}
.progress{height:3px;background:#334155;border-radius:99px;overflow:hidden;margin-top:20px}
.progress-fill{height:100%;background:#2563eb;border-radius:99px;animation:fill 8s linear forwards}
@keyframes fill{from{width:0}to{width:100%}}
.withdrawal-box{background:#0f2a1a;border:1px solid #166534;border-radius:12px;padding:16px;margin:20px 0;text-align:left;font-size:13px;color:#86efac;line-height:1.6}
.withdrawal-box strong{color:#4ade80}
</style></head>
<body>
<div class="card">
  <div class="icon">🎉</div>
  <h1>Platba úspešná!</h1>
  <p>Vitaj v FinAdvisor SK. Presmerujeme ťa na Academy za 8 sekúnd.</p>
  <div class="withdrawal-box">
    <strong>Právo na odstúpenie od zmluvy (14 dní)</strong><br>
    Máte právo odstúpiť od tejto zmluvy bez udania dôvodu do 14 dní od dňa uzavretia zmluvy podľa § 7 zákona č. 102/2014 Z.z.<br><br>
    Ak ste za toto obdobie nevyčerpali žiadny obsah, máte nárok na plné vrátenie platby.<br><br>
    Kontakt: <a href="mailto:petropuneiko@gmail.com" style="color:#60a5fa">petropuneiko@gmail.com</a>
  </div>
  <a href="/learn" class="btn">Otvoriť Academy →</a>
  <div class="progress"><div class="progress-fill"></div></div>
</div>
</body></html>""")


@router.get("/cancel", response_class=HTMLResponse)
async def subscription_cancel():
    return HTMLResponse(content="""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta http-equiv="refresh" content="3;url=/app">
<title>FinAdvisor SK</title>
<style>*{margin:0;padding:0;box-sizing:border-box}body{background:#0f172a;color:#f1f5f9;font-family:-apple-system,sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;text-align:center;padding:24px}.card{background:#1e293b;border:1px solid #334155;border-radius:24px;padding:48px 32px;max-width:380px}h1{font-size:22px;font-weight:800;margin-bottom:10px;margin-top:16px}p{color:#94a3b8;font-size:14px}</style></head>
<body><div class="card"><div style="font-size:48px">↩️</div><h1>Platba zrušená</h1><p>Presmerujeme ťa späť…</p></div></body></html>""")


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
):
    """Handle Stripe webhook events (payment confirmations)."""
    s, err = _stripe()
    if err:
        return JSONResponse({"error": err}, status_code=503)

    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    payload = await request.body()

    if webhook_secret and stripe_signature:
        try:
            event = s.Webhook.construct_event(payload, stripe_signature, webhook_secret)
        except Exception as e:
            logger.warning("Webhook signature failed: %s", e)
            return JSONResponse({"error": "Invalid signature"}, status_code=400)
    else:
        import json
        event = json.loads(payload)

    event_type = event.get("type", "")
    logger.info("Stripe webhook: %s", event_type)

    if event_type == "checkout.session.completed":
        session = event["data"]["object"]
        email = session.get("customer_email", "")
        plan = session.get("metadata", {}).get("plan", "pro")
        logger.info("New subscription: %s → plan=%s", email, plan)
        # TODO: update user subscription status in DB

    elif event_type == "customer.subscription.deleted":
        customer_id = event["data"]["object"].get("customer")
        logger.info("Subscription cancelled: customer=%s", customer_id)

    return {"received": True}
