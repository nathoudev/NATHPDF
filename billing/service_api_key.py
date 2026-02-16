# billing/service_api_key.py

from fastapi import Request, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from .rate_limit import limiter, RateLimitConfig
from .request_utils import get_client_ip
from .database import get_db
from .models import ApiKey


async def verify_api_key(
    request: Request,
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> ApiKey:
    """
    Vérifie que la clé API envoyée dans le header X-API-Key est valide.
    - Cherche la clé dans la table api_keys
    - Vérifie qu'elle est active
    - Vérifie le quota restant
    - Rate limiting par clé + par IP
    """

    # 1) Clé fournie ?
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API key")

    # 2) On cherche la clé en base
    api_key = (
        db.query(ApiKey)
        .filter(
            ApiKey.key == x_api_key,
            ApiKey.is_active == True,  # noqa: E712
        )
        .first()
    )

    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    # 3) Quota
    if api_key.quota_remaining is not None and api_key.quota_remaining <= 0:
        raise HTTPException(
            status_code=402,
            detail="Quota épuisé. Merci de recharger votre compte ou de ou de souscrire à une offre supérieure.",
            )

