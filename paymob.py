"""
💳 Paymob v2 API (New)
=======================
For accounts with keys starting with: egy_sk_...
New flow:
  1. POST /v1/intention/ with Secret Key → get client_secret
  2. Build payment URL with Public Key + client_secret
"""

import httpx
import logging
from config import (
    PAYMOB_API_KEY,           # Secret Key  (egy_sk_...)
    PAYMOB_PUBLIC_KEY,        # Public Key  (egy_pk_...)
    PAYMOB_INTEGRATION_ID,
    CURRENCY,
)

BASE_URL = "https://accept.paymob.com"


async def create_payment_url(
    amount: float,
    booking_id: int,
    user_name: str,
    user_email: str = "",
    user_phone: str = "",
) -> str:
    """
    Creates a Paymob v2 payment URL.
    Returns the checkout URL for the user.
    """
    amount_cents = int(amount * 100)

    parts      = user_name.strip().split()
    first_name = parts[0] if parts else "Customer"
    last_name  = parts[1] if len(parts) > 1 else "NA"

    payload = {
        "amount":   amount_cents,
        "currency": CURRENCY,
        "payment_methods": [PAYMOB_INTEGRATION_ID],
        "items": [
            {
                "name":     f"Booking #{booking_id:04d}",
                "amount":   amount_cents,
                "quantity": 1,
            }
        ],
        "billing_data": {
            "first_name":   first_name,
            "last_name":    last_name,
            "phone_number": user_phone or "+201000000000",
            "email":        user_email or "guest@ticketflow.com",
        },
        "customer": {
            "first_name":   first_name,
            "last_name":    last_name,
            "email":        user_email or "guest@ticketflow.com",
        },
        "extras": {
            "booking_id": booking_id,
        },
    }

    headers = {
        "Authorization": f"Token {PAYMOB_API_KEY}",
        "Content-Type":  "application/json",
    }

    logging.info(f"[Paymob v2] Creating intention for booking #{booking_id}")

    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{BASE_URL}/v1/intention/",
            json=payload,
            headers=headers,
            timeout=20,
        )
        logging.info(f"[Paymob v2] Response status: {r.status_code}")
        logging.info(f"[Paymob v2] Response body: {r.text[:300]}")
        r.raise_for_status()

        data          = r.json()
        client_secret = data.get("client_secret")

        if not client_secret:
            raise ValueError(f"No client_secret in response: {data}")

    pay_url = (
        f"https://accept.paymob.com/unifiedcheckout/"
        f"?publicKey={PAYMOB_PUBLIC_KEY}"
        f"&clientSecret={client_secret}"
    )

    logging.info(f"[Paymob v2] ✅ Payment URL ready for booking #{booking_id}")
    return pay_url


def verify_hmac(data: dict) -> bool:
    """Webhook HMAC verification — skip in test mode"""
    from config import PAYMOB_HMAC_SECRET
    if not PAYMOB_HMAC_SECRET:
        return True
    import hmac as hmac_lib
    import hashlib
    obj    = data.get("obj", {})
    fields = [
        "amount_cents", "created_at", "currency", "error_occured",
        "has_parent_transaction", "id", "integration_id", "is_3d_secure",
        "is_auth", "is_capture", "is_refunded", "is_standalone_payment",
        "is_voided", "order", "owner", "pending",
        "source_data.pan", "source_data.sub_type", "source_data.type", "success",
    ]
    values = []
    for f in fields:
        if "." in f:
            k1, k2 = f.split(".")
            values.append(str(obj.get(k1, {}).get(k2, "")))
        else:
            values.append(str(obj.get(f, "")))
    expected = hmac_lib.new(
        PAYMOB_HMAC_SECRET.encode(),
        "".join(values).encode(),
        hashlib.sha512
    ).hexdigest()
    return data.get("hmac") == expected


def is_payment_successful(webhook_data: dict) -> tuple:
    obj        = webhook_data.get("obj", {})
    success    = obj.get("success", False)
    extras     = obj.get("order", {}).get("merchant_order_id", "0")
    booking_id = int(extras) if str(extras).isdigit() else 0
    return success, booking_id
