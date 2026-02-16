



from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
import os

from .database import get_db
from .models import User, ApiKey
from .email_utils import send_api_key_email
from .rate_limit import limiter, RateLimitConfig
from .request_utils import get_client_ip

router = APIRouter(prefix="/account", tags=["account"])


@router.post("/resend-api-key")
async def resend_api_key(payload: dict, request: Request, db: Session = Depends(get_db)):
    email = (payload.get("email") or "").strip().lower()

    # ✅ email obligatoire
    if not email:
        raise HTTPException(status_code=400, detail="Email requis")

    # ✅ rate limit anti-spam
    ip = get_client_ip(request)

    # 5 requêtes / minute par IP
    if not limiter.allow("resend_ip", ip, RateLimitConfig(max_requests=5, window_seconds=60)):
        raise HTTPException(status_code=429, detail="Too many requests, try later")

    # 3 requêtes / minute par email
    if not limiter.allow("resend_email", email, RateLimitConfig(max_requests=3, window_seconds=60)):
        raise HTTPException(status_code=429, detail="Too many requests, try later")

    # ✅ ne pas révéler si le compte existe ou pas
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return {"status": "ok"}

    api_key = (
        db.query(ApiKey)
        .filter(ApiKey.user_id == user.id)
        .order_by(ApiKey.id.desc())
        .first()
    )
    if not api_key:
        return {"status": "ok"}

    base_url = os.environ.get("PUBLIC_BASE_URL", "http://localhost:8080")

    try:
        send_api_key_email(email, api_key.key, api_key.quota_remaining, base_url)
    except Exception as e:
        print("[EMAIL] erreur:", repr(e))

    return {"status": "ok"}
