import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

def diagnostic_test():
    secret_key = os.getenv('KHALTI_SECRET_KEY')
    base_url = os.getenv('KHALTI_BASE_URL', 'https://a.khalti.com/api/v2/')
    
    print(f"--- DIAGNOSTIC TEST ---")
    print(f"Base URL: {base_url}")
    print(f"Secret Key: {secret_key[:18]}... (Length: {len(secret_key) if secret_key else 0})")
    
    if not secret_key:
        print("ERROR: KHALTI_SECRET_KEY not found!")
        return

    # 1. Try different endpoints
    endpoints = [
        "https://a.khalti.com/api/v2/epayment/initiate/",
        "https://dev.khalti.com/api/v2/epayment/initiate/",
        "https://khalti.com/api/v2/epayment/initiate/"
    ]
    
    payload = {
        "return_url": "http://127.0.0.1:8000/khalti/verify/",
        "website_url": "http://127.0.0.1:8000/",
        "amount": 1000,
        "purchase_order_id": "DIAG_TEST_123",
        "purchase_order_name": "Diagnostic Test",
        "customer_info": {
            "name": "Test User",
            "email": "test@example.com",
            "phone": "9800000000"
        }
    }
    
    for url in endpoints:
        print(f"\nTesting Endpoint: {url}")
        headers = {
            'Authorization': f'Key {secret_key}',
            'Content-Type': 'application/json',
        }
        try:
            response = requests.post(url, headers=headers, json=payload)
            print(f"Status Code: {response.status_code}")
            print(f"Response Body: {response.text}")
        except Exception as e:
            print(f"Request Error: {e}")

if __name__ == "__main__":
    diagnostic_test()
