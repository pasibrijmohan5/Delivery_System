import requests
import os
from dotenv import load_dotenv

# Load env from parent dir if needed
load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

def test_endpoint(name, url, secret_key):
    headers = {
        'Authorization': f'Key {secret_key}',
        'Content-Type': 'application/json',
    }
    
    payload = {
        "return_url": "http://127.0.0.1:8000/khalti/verify/",
        "website_url": "http://127.0.0.1:8000/",
        "amount": 1000,
        "purchase_order_id": "TEST_ID_123",
        "purchase_order_name": "Test Order",
        "customer_info": {
            "name": "Test User",
            "email": "test@example.com",
            "phone": "9800000000"
        }
    }
    
    print(f"\n--- Testing {name} ---")
    print(f"URL: {url}")
    try:
        response = requests.post(url, headers=headers, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

def test_khalti():
    secret_key = os.getenv('KHALTI_SECRET_KEY')
    if not secret_key:
        print("Error: KHALTI_SECRET_KEY not found in .env")
        return

    endpoints = {
        "Production": "https://khalti.com/api/v2/epayment/initiate/",
        "Dev Server": "https://dev.khalti.com/api/v2/epayment/initiate/",
        "Standard V2 (A)": "https://a.khalti.com/api/v2/epayment/initiate/",
    }
    
    for name, url in endpoints.items():
        test_endpoint(name, url, secret_key)

if __name__ == "__main__":
    test_khalti()
