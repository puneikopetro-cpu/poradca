"""Stripe subscription checkout endpoint."""
import os
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter(prefix="/subscribe", tags=["subscriptions"])

# Price IDs — create these in Stripe Dashboard → Products
# then set STRIPE_PRICE_STARTER, STRIPE_PRICE_PRO, STRIPE_PRICE_EXPERT in Railway env
_PRICES = {
    "starter_monthly": os.environ.get("STRIPE_PRICE_STARTER_MONTHLY", ""),
    "starter_annual":  os.environ.get("STRIPE_PRICE_STARTER_ANNUAL", ""),
    "pro_monthly":     os.environ.get("STRIPE_PRICE_PRO_MONTHLY", ""),
    "pro_annual":      os.environ.get("STRIPE_PRICE_PRO_ANNUAL", ""),
    "expert_monthly":  os.environ.get("STRIPE_PRICE_EXPERT_MONTHLY", ""),
    "expert_annual":   os.environ.get("STRIPE_PRICE_EXPERT_ANNUAL", ""),
}

_DOMAIN = os.environ.get("APP_DOMAIN", "https://finadvisor.sk")


class CheckoutRequest(BaseModel):
    email: str
    plan: str   # starter | pro | expert
    billing: str = "monthly"  # monthly | annual


@router.post("/checkout")
async def create_checkout_session(body: CheckoutRequest):
    stripe_key = os.environ.get("STRIPE_SECRET_KEY", "")
    if not stripe_key:
        return JSONResponse(
            {"error": "Stripe not configured. Contact support."},
            status_code=503,
        )

    try:
        import stripe  # type: ignore
    except ImportError:
        return JSONResponse(
            {"error": "stripe library not installed"},
            status_code=500,
        )

    stripe.api_key = stripe_key
    price_key = f"{body.plan}_{body.billing}"
    price_id = _PRICES.get(price_key, "")

    if not price_id:
        # Fallback: create price on the fly using hardcoded amounts (cents)
        amounts = {
            "starter_monthly": 490,
            "starter_annual":  3900,
            "pro_monthly":     990,
            "pro_annual":      7900,
            "expert_monthly":  1490,
            "expert_annual":   11900,
        }
        currency_interval = {
            "monthly": ("month", 1),
            "annual":  ("year", 1),
        }
        amount = amounts.get(price_key, 990)
        interval, interval_count = currency_interval.get(body.billing, ("month", 1))
        try:
            price_obj = stripe.Price.create(
                unit_amount=amount,
                currency="eur",
                recurring={"interval": interval, "interval_count": interval_count},
                product_data={"name": f"FinAdvisor SK — {body.plan.capitalize()}"},
            )
            price_id = price_obj["id"]
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            customer_email=body.email,
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=f"{_DOMAIN}/app?subscribed=1",
            cancel_url=f"{_DOMAIN}/app?cancelled=1",
            metadata={"plan": body.plan, "billing": body.billing},
        )
        return {"url": session["url"]}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/success")
def subscription_success():
    return {"status": "success", "message": "Subscription activated"}
