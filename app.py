# app.py
from flask import Flask, request, jsonify, make_response

app = Flask(__name__)

@app.route("/carey/webhook", methods=["POST", "OPTIONS"])
def carey_webhook():
    # Préflight CORS (outil "Try it out" de Carey)
    if request.method == "OPTIONS":
        r = make_response("", 204)
        r.headers["Access-Control-Allow-Origin"] = "https://carey.3scale.net"
        r.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        r.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
        r.headers["Access-Control-Max-Age"] = "86400"
        return r

    # Reçoit le JSON (log pour vérif)
    payload = request.get_json(silent=True)
    print("CAREY IN:", payload)

    # Réponse immédiate (évite le 996 côté Carey)
    r = jsonify({"ok": True, "received": True})
    r.headers["Access-Control-Allow-Origin"] = "https://carey.3scale.net"
    r.headers["Vary"] = "Origin"
    return r, 200

@app.route("/health")
def health():
    return "OK", 200
