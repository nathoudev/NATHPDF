

# billing/routes_checkout.py

import os
import stripe
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

stripe.api_key = os.environ.get("STRIPE_API_KEY")

router = APIRouter(
    prefix="/billing",
    tags=["billing"],
)


class CheckoutRequest(BaseModel):
    email: str


@router.post("/create-checkout-session")
async def create_checkout_session(body: CheckoutRequest):
    """
    Crée une session de paiement Stripe pour un pack de conversions.
    Renvoie l'URL Stripe où rediriger l'utilisateur.
    """
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            customer_email=body.email,
            line_items=[
                {
                    "price_data": {
                        "currency": "eur",
                        "product_data": {
                            "name": "Pack 100 conversions PDF",
                        },
                        "unit_amount": 500,  # 5€ en centimes
                    },
                    "quantity": 1,
                }
            ],
            success_url="https://ton-domaine.com/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="https://ton-domaine.com/cancel",
        )
        return {"checkout_url": session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
