import requests
import os
import jwt
import time
from dotenv import load_dotenv

load_dotenv()

WAYNIUM_URL = os.getenv("WAYNIUM_URL")  # ex: https://api-sandbox.waynium.com/reservations
WAYNIUM_API_KEY = os.getenv("WAYNIUM_API_KEY")
WAYNIUM_API_SECRET = os.getenv("WAYNIUM_API_SECRET")

def generate_jwt():
    payload = {
        "iss": WAYNIUM_API_KEY,
        "iat": int(time.time()),
        "exp": int(time.time()) + 300  # 5 min
    }
    return jwt.encode(payload, WAYNIUM_API_SECRET, algorithm="HS256")

def forward_to_waynium(data):
    token = generate_jwt()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(WAYNIUM_URL, json=data, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Waynium API call failed: {e}")
        return {"error": str(e)}
