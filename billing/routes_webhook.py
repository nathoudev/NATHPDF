

# billing/routes_webhook.py

import os
import stripe
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text


from .database import get_db
from .models import User, ApiKey, generate_api_key,StripeEvent

from .email_utils import send_api_key_email 
import logging
logger = logging.getLogger("uvicorn.error")
 # 👈 NOUVEL IMPORT

router = APIRouter()

stripe.api_key = os.environ.get("STRIPE_API_KEY")
WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")
MOCK_STRIPE = os.environ.get("MOCK_STRIPE", "0") == "1"

@router.post("/stripe/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    # 1) Lire l’event Stripe (DEV vs réel)
    if MOCK_STRIPE:
        event = await request.json()
    else:
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")

        try:
            event = stripe.Webhook.construct_event(
                payload=payload,
                sig_header=sig_header,
                secret=WEBHOOK_SECRET,
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise HTTPException(status_code=400, detail="Invalid signature")

    event_id = event.get("id")
    event_type = event.get("type")






    # 2) Idempotence “pro”: si Stripe renvoie le même event, on ignore
    if event_id:
        already = db.query(StripeEvent).filter(StripeEvent.event_id == event_id).first()
        if already:
            return {"status": "already_processed"}

        db.add(StripeEvent(event_id=event_id, event_type=event_type))
        db.commit()

    # 3) Traitement du paiement validé
    if event_type == "checkout.session.completed":
        session_obj = event["data"]["object"]

        session_id = session_obj.get("id")

        email = (
            session_obj.get("customer_email")
            or (session_obj.get("customer_details") or {}).get("email")
        )

        

        if not email:
            return {"status": "no_email"}

        # 4) Anti-doublon par session Stripe (2e filet)
        if session_id:
            existing_key = (
                db.query(ApiKey)
                .filter(ApiKey.stripe_session_id == session_id)
                .first()
            )
            if existing_key:
                return {"status": "already_issued"}

        # 5) User
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(email=email)
            db.add(user)
            db.commit()
            db.refresh(user)

        # 6) Créer la clé + quota
        quota = 100
        api_key_value = generate_api_key()

        api_key = ApiKey(
            key=api_key_value,
            user_id=user.id,
            quota_remaining=quota,
            stripe_session_id=session_id,
        )
        db.add(api_key)
        db.commit()

        base_url = os.environ.get("PUBLIC_BASE_URL", "http://localhost:8080")
        try:
        	send_api_key_email(email, api_key_value, quota, base_url)
        except Exception as e:
        	print("[EMAIL] erreur:", repr(e))
        

        


        # 7) Email (optionnel, prochain step)
        # send_api_key_email(email, api_key_value, quota)

        return {"status": "issued"}

    return {"status": "success"}

