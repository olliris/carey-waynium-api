from flask import Flask, request, jsonify
from transform import transform_payload
import requests
import logging

app = Flask(__name__)

# URL cible de l’API Waynium (à adapter si sandbox)
WAYNIUM_API_URL = "https://api.waynium.com/booking"  # ⬅️ À adapter selon ton environnement
WAYNIUM_API_KEY = "YOUR_API_KEY_HERE"  # ⬅️ Remplace par ta clé API Waynium

# Configuration du logger
logging.basicConfig(level=logging.INFO)

@app.route("/webhook", methods=["POST"])
def carey_webhook():
    try:
        # Lecture du JSON Carey
        carey_data = request.get_json(force=True)
        logging.info("Payload reçu de Carey : %s", carey_data)

        # Transformation du payload Carey -> Waynium
        waynium_data = transform_payload(carey_data)
        logging.info("Payload transformé pour Waynium : %s", waynium_data)

        # Envoi vers Waynium
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {WAYNIUM_API_KEY}"
        }
        response = requests.post(WAYNIUM_API_URL, json=waynium_data, headers=headers)

        logging.info("Réponse Waynium : %s", response.text)

        if response.status_code == 200:
            return jsonify({"status": "success", "waynium_response": response.json()}), 200
        else:
            return jsonify({"status": "error", "code": response.status_code, "response": response.text}), 500

    except Exception as e:
        logging.exception("Erreur lors du traitement du webhook Carey")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
