from flask import Flask, request, jsonify
from flask_cors import CORS
from transform import transform_payload
import requests
import logging

app = Flask(__name__)
CORS(app)  # Pour autoriser les appels depuis carey.3scale.net

# Logging basique
logging.basicConfig(level=logging.INFO)

# Configuration API Waynium (à adapter)
WAYNIUM_API_URL = "https://sandbox-api.waynium.com/booking"
WAYNIUM_API_KEY = "YOUR_API_KEY_HERE"  # 🔁 Remplace ça !

@app.route("/carey/webhook", methods=["POST"])
def carey_webhook():
    try:
        # Parse JSON Carey
        carey_payload = request.get_json(force=True)
        logging.info("Payload Carey reçu : %s", carey_payload)

        # Transformation Carey → Waynium
        waynium_payload = transform_payload(carey_payload)
        logging.info("Payload Waynium généré : %s", waynium_payload)

        # Envoi vers Waynium
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {WAYNIUM_API_KEY}"
        }

        response = requests.post(WAYNIUM_API_URL, json=waynium_payload, headers=headers)
        logging.info("Réponse Waynium : %s", response.text)

        if response.status_code == 200:
            return jsonify({"status": "success", "waynium_response": response.json()}), 200
        else:
            return jsonify({"status": "error", "code": response.status_code, "response": response.text}), 500

    except Exception as e:
        logging.exception("Erreur pendant le traitement du webhook Carey")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    # Laisse le port modifiable via ENV si besoin
    import os
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
