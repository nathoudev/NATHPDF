

import os
import stripe
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

stripe.api_key = os.environ.get("STRIPE_API_KEY")

billing_app = FastAPI(title="Billing API")


class CheckoutRequest(BaseModel):
    email: str


@billing_app.post("/create-checkout-session")
async def create_checkout_session(body: CheckoutRequest):
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
                        "unit_amount": 500,  # 5.00 € en centimes
                    },
                    "quantity": 1,
                }
            ],
            success_url="https://ton-site.com/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="https://ton-site.com/cancel",
        )
        return {"checkout_url": session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
