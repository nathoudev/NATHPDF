# billing/paypal_service.py

import os
import requests
from fastapi import HTTPException

PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")
PAYPAL_ENV = os.getenv("PAYPAL_ENV", "sandbox")

BASE_URL = (
    "https://api-m.paypal.com"
    if PAYPAL_ENV == "live"
    else "https://api-m.sandbox.paypal.com"
)


def get_access_token():
    response = requests.post(
        f"{BASE_URL}/v1/oauth2/token",
        auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET),
        data={"grant_type": "client_credentials"},
    )

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="PayPal auth failed")

    return response.json()["access_token"]


def create_order(amount="5.00", currency="EUR"):
    access_token = get_access_token()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }

    data = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "amount": {
                    "currency_code": currency,
                    "value": amount,
                }
            }
        ]
    }

    response = requests.post(
        f"{BASE_URL}/v2/checkout/orders",
        headers=headers,
        json=data,
    )

    if response.status_code != 201:
        raise HTTPException(status_code=500, detail="PayPal order creation failed")

    return response.json()
