import hashlib
import hmac
import json
import requests
from django.conf import settings

def _base_url():
    return "https://sandbox.cashfree.com/pg" if settings.CASHFREE_ENV == "sandbox" else "https://api.cashfree.com/pg"

def _headers():
    if not settings.CASHFREE_APP_ID or not settings.CASHFREE_SECRET_KEY:
        raise RuntimeError("Cashfree credentials are not configured.")
    return {
        "x-client-id": settings.CASHFREE_APP_ID,
        "x-client-secret": settings.CASHFREE_SECRET_KEY,
        "x-api-version": settings.CASHFREE_API_VERSION,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

def create_order(*, order_id, amount, customer_id, customer_name, customer_email, customer_phone, return_url, notify_url):
    phone = "".join(ch for ch in (customer_phone or "") if ch.isdigit())
    if len(phone) != 10:
        raise ValueError("Enter a valid 10-digit mobile number for online checkout.")
    payload = {
        "order_id": order_id,
        "order_amount": float(amount),
        "order_currency": "INR",
        "customer_details": {
            "customer_id": str(customer_id)[:50],
            "customer_name": (customer_name or "Golden Gym Member")[:100],
            "customer_email": customer_email,
            "customer_phone": phone,
        },
        "order_meta": {
            "return_url": return_url,
            "notify_url": notify_url,
        },
        "order_note": "Golden Gym membership payment",
    }
    response = requests.post(f"{_base_url()}/orders", headers=_headers(), json=payload, timeout=20)
    response.raise_for_status()
    return response.json()

def fetch_order_payments(order_id):
    response = requests.get(f"{_base_url()}/orders/{order_id}/payments", headers=_headers(), timeout=20)
    response.raise_for_status()
    return response.json()

def verify_webhook_signature(raw_body, timestamp, signature):
    if not timestamp or not signature:
        return False
    signed_payload = timestamp.encode("utf-8") + raw_body
    expected = hmac.new(settings.CASHFREE_SECRET_KEY.encode("utf-8"), signed_payload, hashlib.sha256).digest()
    import base64
    return hmac.compare_digest(base64.b64encode(expected).decode("utf-8"), signature)


def create_refund(order_id, refund_id, amount, note="Member refund"):
    """Create an idempotently identified full/partial Cashfree order refund."""
    payload = {
        "refund_amount": float(amount),
        "refund_id": refund_id,
        "refund_note": (note or "Member refund")[:100],
        "refund_speed": "STANDARD",
    }
    headers = _headers()
    headers["x-idempotency-key"] = refund_id
    response = requests.post(
        f"{_base_url()}/orders/{order_id}/refunds",
        headers=headers, json=payload, timeout=25,
    )
    response.raise_for_status()
    return response.json()


def fetch_refund(order_id, refund_id):
    response = requests.get(
        f"{_base_url()}/orders/{order_id}/refunds/{refund_id}",
        headers=_headers(), timeout=20,
    )
    response.raise_for_status()
    return response.json()
