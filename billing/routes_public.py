import os
from fastapi import APIRouter

router = APIRouter(prefix="/public", tags=["Public"])

@router.get("/config")
def public_config():
    """
    ⚠️ Ne jamais exposer PAYPAL_CLIENT_SECRET ici.
    On expose seulement des infos publiques nécessaires au front.
    """
    paypal_env = os.getenv("PAYPAL_ENV", "sandbox")  # sandbox|live
    paypal_client_id = os.getenv("PAYPAL_CLIENT_ID", "")
    public_base_url = os.getenv("PUBLIC_BASE_URL", "")

    return {
        "paypal_env": paypal_env,
        "paypal_client_id": paypal_client_id,
        "currency": "EUR",
        "public_base_url": public_base_url,
        "free_limit": 3,
        "pro_quota": 100,
        "pro_price_eur": 5,
    }
