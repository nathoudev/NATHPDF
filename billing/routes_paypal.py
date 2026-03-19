

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from billing.paypal_service import create_order, get_access_token
from billing.database import get_db
from models import User, ApiKey
from billing.service_api_key import generate_api_key
import requests
import os

router = APIRouter(prefix="/paypal", tags=["PayPal"])

BASE_URL = (
    "https://api-m.paypal.com"
    if os.getenv("PAYPAL_ENV") == "live"
    else "https://api-m.sandbox.paypal.com"
)


@router.post("/create-order")
def create_paypal_order():
    order = create_order()
    return {"orderID": order["id"]}


@router.post("/capture-order")
def capture_order(orderID: str, db: Session = Depends(get_db)):

    access_token = get_access_token()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }

    # Capture paiement PayPal
    r = requests.post(
        f"{BASE_URL}/v2/checkout/orders/{orderID}/capture",
        headers=headers,
    )

    if r.status_code not in (200, 201):
        raise HTTPException(
            status_code=400,
            detail=f"Capture failed: {r.status_code} {r.text}",
        )

    capture = r.json()   # ✅ IMPORTANT — c’était manquant

    # Récupérer email depuis PayPal
    payer = capture.get("payer", {})
    email = payer.get("email_address")

    if not email:
        raise HTTPException(
            status_code=400,
            detail="Email not provided by PayPal",
        )

    # Création utilisateur + clé API
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email)
        db.add(user)
        db.commit()
        db.refresh(user)

    api_key_value = generate_api_key()

    api_key = ApiKey(
        key=api_key_value,
        user_id=user.id,
        quota_remaining=100,
    )

    db.add(api_key)
    db.commit()

    return {
        "status": "success",
        "api_key": api_key_value,
        "email": email,
    }

