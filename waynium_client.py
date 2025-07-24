import requests
import os
import jwt
import datetime

def forward_to_waynium(carey_data):
    try:
        jwt_secret = os.getenv("WAYNIUM_SECRET", "demo_secret")
        jwt_issuer = os.getenv("WAYNIUM_ISSUER", "demo_issuer")
        jwt_url = os.getenv("WAYNIUM_ENDPOINT", "https://gds.waynium.net/gdsv2/set-ressource")

        payload = {
            "sub": "carey_integration",
            "iat": datetime.datetime.utcnow()
        }

        token = jwt.encode(payload, jwt_secret, algorithm="HS256")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Placeholder transformation - replace with real logic
        waynium_payload = {
            "booking_id": carey_data.get("reservationId", "UNKNOWN"),
            "passenger_name": f"{carey_data.get('passenger', {}).get('firstName', '')} {carey_data.get('passenger', {}).get('lastName', '')}",
            "pickup_time": carey_data.get("pickup", {}).get("time", ""),
            "pickup_location": carey_data.get("pickup", {}).get("location", "")
        }

        response = requests.post(jwt_url, json=waynium_payload, headers=headers)
        return response.text
    except Exception as e:
        return str(e)
