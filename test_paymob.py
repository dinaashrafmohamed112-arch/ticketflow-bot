"""Test Paymob v2 API — run: python test_paymob.py"""
import os, httpx
from dotenv import load_dotenv
load_dotenv()

secret = os.getenv("PAYMOB_API_KEY", "")
public = os.getenv("PAYMOB_PUBLIC_KEY", "")

print(f"Secret Key: {secret[:15]}... ({len(secret)} chars)")
print(f"Public Key: {public[:15]}... ({len(public)} chars)")
print()

r = httpx.post(
    "https://accept.paymob.com/v1/intention/",
    headers={"Authorization": f"Token {secret}", "Content-Type": "application/json"},
    json={
        "amount": 100, "currency": "EGP",
        "payment_methods": [int(os.getenv("PAYMOB_INTEGRATION_ID","5578640"))],
        "items": [{"name": "Test", "amount": 100, "quantity": 1}],
        "billing_data": {"first_name":"Test","last_name":"User",
                         "phone_number":"+201000000000","email":"test@test.com"},
    },
    timeout=15
)
print(f"Status: {r.status_code}")
print(f"Response: {r.text[:400]}")
if r.status_code == 201:
    print("\n✅ Paymob v2 works!")
    cs = r.json().get("client_secret","")
    print(f"Payment URL: https://accept.paymob.com/unifiedcheckout/?publicKey={public}&clientSecret={cs[:20]}...")
