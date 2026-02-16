

# billing/routes_checkout.py

import os
import stripe
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Initialisation Stripe
stripe.api_key = os.environ.get("STRIPE_API_KEY")

router = APIRouter(
    prefix="/billing",
    tags=["billing"],
)


@router.get("/checkout-session/{session_id}")
async def get_checkout_session(session_id: str):
    """
    Renvoie des infos minimales pour afficher la page success.
    """
    try:
        s = stripe.checkout.Session.retrieve(session_id)
        return {
            "id": s.id,
            "payment_status": s.get("payment_status"),
            "amount_total": s.get("amount_total"),
            "currency": s.get("currency"),
            "customer_email": (
                s.get("customer_details", {}) or {}
            ).get("email") or s.get("customer_email"),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class CheckoutRequest(BaseModel):
    email: str


@router.post("/create-checkout-session")
async def create_checkout_session(body: CheckoutRequest):
    try:
        base_url = os.environ.get(
            "PUBLIC_BASE_URL", "http://localhost:8080"
        ).rstrip("/")

        success_url = (
            f"{base_url}/static/success.html"
            f"?session_id={{CHECKOUT_SESSION_ID}}"
        )
        cancel_url = f"{base_url}/static/cancel.html"

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            customer_email=body.email,
            line_items=[
                {
                    "price_data": {
                        "currency": "eur",
                        "product_data": {
                            "name": "Pack 100 conversions PDF"
                        },
                        "unit_amount": 500,  # 5,00 €
                    },
                    "quantity": 1,
                }
            ],
            success_url=success_url,
            cancel_url=cancel_url,
        )

        return {"url": session.url}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
