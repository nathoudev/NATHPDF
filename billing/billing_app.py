

from fastapi import FastAPI
from .routes_checkout import router as checkout_router
from .routes_webhook import router as webhook_router

billing_app = FastAPI(title="Billing API")

billing_app.include_router(checkout_router)
billing_app.include_router(webhook_router)
