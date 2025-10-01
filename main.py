# main.py - Production Ready avec Queue Asynchrone
from flask import Flask, request, jsonify
from flask_cors import CORS
from transform import transform_to_waynium
import os, json, logging, requests, jwt, hmac, hashlib
from datetime import datetime
from queue import Queue
from threading import Thread
import traceback

# ============================= CONFIG =====================================
WAYNIUM_API_URL = os.getenv("WAYNIUM_API_URL", "https://stage-gdsapi.waynium.net/api-externe/set-ressource")
WAYNIUM_API_KEY = os.getenv("WAYNIUM_API_KEY", "abllimousines")
WAYNIUM_API_SECRET = os.getenv("WAYNIUM_API_SECRET", "be5F47w72eGxwWe8EAZe9Y4vP38g2rRG")
WEBHOOK_API_KEYS = {k.strip() for k in os.getenv("WEBHOOK_API_KEYS", "1").split(",") if k.strip()}
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "15"))
ENABLE_QUEUE = os.getenv("ENABLE_QUEUE", "true").lower() == "true"
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

# ============================= FLASK APP ==================================
app = Flask(__name__)
CORS(app)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger("carey-waynium")

# ============================= QUEUE ASYNC ================================
webhook_queue = Queue() if ENABLE_QUEUE else None
stats = {"received": 0, "success": 0, "failed": 0, "queued": 0}

def log_json(level, **fields):
    """Log structuré JSON"""
    fields["timestamp"] = datetime.utcnow().isoformat() + "Z"
    getattr(log, level)(json.dumps(fields, ensure_ascii=False))

def generate_jwt_token() -> str:
    """Génère un token JWT pour Waynium"""
    payload = {
        "iss": WAYNIUM_API_KEY,
        "iat": int(datetime.utcnow().timestamp())
    }
    return jwt.encode(payload, WAYNIUM_API_SECRET, algorithm="HS256")

def send_to_waynium(payload: dict, attempt: int = 1) -> tuple[bool, dict]:
    """
    Envoie vers Waynium avec retry automatique
    Returns: (success: bool, response: dict)
    """
    try:
        stats["received"] += 1
        transaction_id = f"TXN-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{stats['received']}"
        
        # Parse payload
        raw_data = request.get_data()
        try:
            carey_payload = request.get_json(force=True)
        except Exception as e:
            log_json("error", event="json_parse_error", transaction_id=transaction_id, error=str(e))
            return jsonify({
                "status": "error",
                "code": 400,
                "message": "Invalid JSON payload"
            }), 400
        
        # Authentification
        api_key = extract_api_key(dict(request.headers), carey_payload)
        if not api_key or api_key not in WEBHOOK_API_KEYS:
            log_json("warning", 
                event="auth_failed",
                transaction_id=transaction_id,
                provided_key=api_key[:8] + "..." if api_key else None
            )
            return jsonify({
                "status": "error",
                "message": "Missing or invalid API key"
            }), 401
        
        # Validation signature (optionnelle)
        signature = request.headers.get("X-Carey-Signature")
        if signature and not validate_carey_signature(raw_data, signature):
            log_json("warning", event="signature_invalid", transaction_id=transaction_id)
            return jsonify({
                "status": "error",
                "message": "Invalid signature"
            }), 401
        
        # Log réception
        log_json("info",
            event="carey_webhook_received",
            transaction_id=transaction_id,
            reservation_ref=carey_payload.get("reservationNumber") or 
                          carey_payload.get("reservationId") or
                          carey_payload.get("trip", {}).get("reservationNumber", "unknown")
        )
        
        # Mode asynchrone: mise en queue
        if ENABLE_QUEUE:
            task = {
                "transaction_id": transaction_id,
                "payload": carey_payload,
                "received_at": datetime.utcnow().isoformat() + "Z"
            }
            webhook_queue.put(task)
            stats["queued"] += 1
            
            log_json("info", 
                event="queued",
                transaction_id=transaction_id,
                queue_size=webhook_queue.qsize()
            )
            
            resp = jsonify({
                "status": "accepted",
                "transaction_id": transaction_id,
                "queued": True,
                "queue_size": webhook_queue.qsize()
            })
            resp.headers["Access-Control-Allow-Origin"] = "*"
            return resp, 202
        
        # Mode synchrone: traitement immédiat
        try:
            waynium_payload = transform_to_waynium(carey_payload)
        except Exception as e:
            log_json("error",
                event="transform_error",
                transaction_id=transaction_id,
                error=str(e),
                trace=traceback.format_exc()
            )
            return jsonify({
                "status": "error",
                "code": 996,
                "message": "Transformation error",
                "details": str(e)
            }), 400
        
        # Envoi vers Waynium
        success, response = send_to_waynium(waynium_payload)
        
        if success:
            stats["success"] += 1
            resp = jsonify({
                "status": "success",
                "transaction_id": transaction_id,
                "waynium_response": response
            })
            resp.headers["Access-Control-Allow-Origin"] = "*"
            return resp, 200
        else:
            stats["failed"] += 1
            resp = jsonify({
                "status": "upstream_error",
                "transaction_id": transaction_id,
                "upstream": "waynium",
                "waynium_response": response
            })
            resp.headers["Access-Control-Allow-Origin"] = "*"
            return resp, 502
            
    except Exception as e:
        log_json("error",
            event="unhandled_exception",
            error=str(e),
            trace=traceback.format_exc()
        )
        return jsonify({
            "status": "error",
            "message": "Internal server error",
            "details": str(e)
        }), 500

@app.route("/healthz", methods=["GET"])
def healthz():
    """Health check simple"""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }), 200

@app.route("/readyz", methods=["GET"])
def readyz():
    """Readiness check avec vérification config"""
    checks = {
        "config_loaded": bool(WAYNIUM_API_KEY and WAYNIUM_API_SECRET),
        "waynium_url": WAYNIUM_API_URL,
        "queue_enabled": ENABLE_QUEUE,
        "queue_size": webhook_queue.qsize() if ENABLE_QUEUE else 0,
        "stats": stats
    }
    
    ready = checks["config_loaded"]
    return jsonify(checks), 200 if ready else 503

@app.route("/stats", methods=["GET"])
def get_stats():
    """Statistiques du service"""
    return jsonify({
        "stats": stats,
        "queue_size": webhook_queue.qsize() if ENABLE_QUEUE else 0,
        "queue_enabled": ENABLE_QUEUE,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }), 200

@app.route("/version", methods=["GET"])
def version():
    """Version de l'API"""
    return jsonify({
        "name": "carey-waynium-api",
        "version": os.getenv("VERSION", "2.0.0"),
        "waynium_url": WAYNIUM_API_URL,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }), 200

# ========================== ENTRYPOINT ====================================
if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    log.info(f"Starting Carey→Waynium API on port {port}")
    log.info(f"Waynium URL: {WAYNIUM_API_URL}")
    log.info(f"Queue mode: {'enabled' if ENABLE_QUEUE else 'disabled'}")
    log.info(f"Max retries: {MAX_RETRIES}")
    
    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug
    ):
        body_str = json.dumps(payload, ensure_ascii=False)
        token = generate_jwt_token()
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {token}"
        }
        
        log_json("info", 
            event="waynium_request",
            attempt=attempt,
            ref=payload.get("params", {}).get("C_Gen_Client", [{}])[0]
                .get("C_Com_Commande", [{}])[0].get("ref", "unknown")
        )
        
        r = requests.post(
            WAYNIUM_API_URL,
            data=body_str.encode("utf-8"),
            headers=headers,
            timeout=REQUEST_TIMEOUT
        )
        
        # Parse response
        try:
            resp_data = r.json()
        except:
            resp_data = {"raw": r.text}
        
        if r.status_code in (200, 201):
            log_json("info", 
                event="waynium_success",
                status=r.status_code,
                response=resp_data
            )
            return True, resp_data
        
        # Erreur Waynium
        log_json("warning",
            event="waynium_error",
            status=r.status_code,
            response=resp_data,
            attempt=attempt
        )
        
        # Retry si < MAX_RETRIES et erreur 5xx
        if attempt < MAX_RETRIES and r.status_code >= 500:
            log_json("info", event="waynium_retry", attempt=attempt+1)
            return send_to_waynium(payload, attempt + 1)
        
        return False, {
            "error": "waynium_rejected",
            "status": r.status_code,
            "response": resp_data
        }
        
    except requests.exceptions.Timeout:
        log_json("error", event="waynium_timeout", attempt=attempt)
        if attempt < MAX_RETRIES:
            return send_to_waynium(payload, attempt + 1)
        return False, {"error": "timeout"}
        
    except Exception as e:
        log_json("error", event="waynium_exception", error=str(e), trace=traceback.format_exc())
        return False, {"error": str(e)}

def process_webhook_task(task: dict):
    """Traite une tâche de la queue"""
    try:
        carey_payload = task["payload"]
        transaction_id = task["transaction_id"]
        
        log_json("info", 
            event="queue_processing",
            transaction_id=transaction_id
        )
        
        # Transformation Carey → Waynium
        waynium_payload = transform_to_waynium(carey_payload)
        
        # Envoi vers Waynium
        success, response = send_to_waynium(waynium_payload)
        
        if success:
            stats["success"] += 1
            log_json("info",
                event="webhook_success",
                transaction_id=transaction_id
            )
        else:
            stats["failed"] += 1
            log_json("error",
                event="webhook_failed",
                transaction_id=transaction_id,
                waynium_response=response
            )
            
    except Exception as e:
        stats["failed"] += 1
        log_json("error",
            event="queue_task_exception",
            error=str(e),
            trace=traceback.format_exc()
        )

def queue_worker():
    """Worker thread pour traiter la queue en continu"""
    log.info("Queue worker started")
    while True:
        try:
            task = webhook_queue.get()
            process_webhook_task(task)
            webhook_queue.task_done()
        except Exception as e:
            log_json("error", event="queue_worker_exception", error=str(e))

# Démarrage worker si queue activée
if ENABLE_QUEUE:
    worker_thread = Thread(target=queue_worker, daemon=True)
    worker_thread.start()
    log.info("Async queue enabled")

# ========================== AUTH HELPERS ==================================
def extract_api_key(headers: dict, body: dict) -> str:
    """Extrait l'API key depuis headers ou body"""
    # Priorité: headers
    for hk in ("x-api-key", "X-API-KEY", "authorization", "Authorization"):
        if hk in headers and headers[hk]:
            val = str(headers[hk])
            if hk.lower().startswith("authorization"):
                if val.lower().startswith("bearer "):
                    return val.split(" ", 1)[1].strip()
                elif val.lower().startswith("apikey "):
                    return val.split(" ", 1)[1].strip()
            else:
                return val.strip()
    
    # Fallback: body
    if isinstance(body, dict) and body.get("apiKey"):
        return str(body["apiKey"]).strip()
    
    return None

def validate_carey_signature(payload_bytes: bytes, signature: str) -> bool:
    """Valide la signature HMAC du webhook Carey (si activé)"""
    secret = os.getenv("CAREY_WEBHOOK_SECRET")
    if not secret:
        return True  # Skip validation si pas configuré
    
    expected = hmac.new(
        secret.encode(),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected, signature)

# ========================== ROUTES ========================================
@app.route("/carey/webhook", methods=["POST", "OPTIONS"])
def carey_webhook():
    """
    Endpoint principal pour recevoir les webhooks Carey
    
    Mode synchrone (ENABLE_QUEUE=false): traitement immédiat, réponse après Waynium
    Mode asynchrone (ENABLE_QUEUE=true): mise en queue, réponse immédiate 202
    """
    
    # CORS preflight
    if request.method == "OPTIONS":
        resp = jsonify({"ok": True})
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-API-Key"
        return resp, 204
    
    try
