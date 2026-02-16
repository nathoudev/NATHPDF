# billing/mock_stripe.py
# billing/mock_stripe.py

import os
from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session

from .database import get_db
from .models import User, ApiKey, generate_api_key

MOCK_STRIPE = os.environ.get("MOCK_STRIPE", "0") == "1"
DEV_ADMIN_TOKEN = os.environ.get("DEV_ADMIN_TOKEN", "")

ENV = os.getenv("ENV", "dev")

router = APIRouter(prefix="/mock/stripe", tags=["mock-stripe"])


def _dev_only():
    if ENV == "prod":
        raise HTTPException(status_code=404, detail="Not found")


def _require_dev_token(x_dev_token: str | None):
    if not DEV_ADMIN_TOKEN:
        return
    if x_dev_token != DEV_ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid dev token")



@router.get("/mock/stripe/pay")
async def mock_pay(email: str):
    _dev_only()  # 👈 CETTE LIGNE EST LA PROTECTION

    # --- logique mock existante ---
    print(f"[MOCK STRIPE] Paiement simulé pour {email}")
    return {
        "status": "paiement_simulé",
        "email": email,
    }



@router.get("/pay")
async def mock_pay(
    email: str,
    db: Session = Depends(get_db),
    x_dev_token: str | None = Header(default=None, alias="X-Dev-Token"),
):
    if not MOCK_STRIPE:
        raise HTTPException(status_code=404, detail="Not found")

    _require_dev_token(x_dev_token)

    if not email:
        raise HTTPException(status_code=400, detail="Email requis")

    # Crée / récupère user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email)
        db.add(user)
        db.commit()
        db.refresh(user)

    # Crée une API key + quota
    quota = 100
    api_key_value = generate_api_key()
    api_key = ApiKey(key=api_key_value, user_id=user.id, quota_remaining=quota)
    db.add(api_key)
    db.commit()

    return {
        "status": "paiement_simulé",
        "email": email,
        "quota_added": quota,
        # DEV ONLY : tu peux laisser pour vérifier facilement
        "api_key": api_key_value,
    }
