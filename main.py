# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from transform import transform_payload  # <-- garde ton mapping Carey -> Waynium ici
import os
import re
import json
import logging
import uuid
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------
WAYNIUM_API_URL = os.getenv("WAYNIUM_API_URL", "https://sandbox-api.waynium.com/booking")
WAYNIUM_API_KEY = os.getenv("WAYNIUM_API_KEY", "YOUR_API_KEY_HERE")

# Webhook key(s): accepte un header x-api-key OU Authorization: Bearer
# Optionnellement, accepte aussi 'apiKey' dans le body (legacy)
WEBHOOK_API_KEYS = {k.strip() for k in os.getenv("WEBHOOK_API_KEYS", "1").split(",") if k.strip()}
REQUIRE_HEADER_API_KEY = os.getenv("REQUIRE_HEADER_API_KEY", "false").lower() == "true"
ACCEPT_BODY_APIKEY = os.getenv("ACCEPT_BODY_APIKEY", "true").lower() == "true"

REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "15"))  # seconds

# -----------------------------------------------------------------------------
# Flask
# -----------------------------------------------------------------------------
app = Flask(__name__)
CORS(app)

# Logs structurés
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s"
)
logger = logging.getLogger("carey-webhook")

def log_json(level, **fields):
    fields.setdefault("ts", datetime.utcnow().isoformat() + "Z")
    msg = json.dumps(fields, ensure_ascii=False)
    getattr(logger, level)(msg)

# -----------------------------------------------------------------------------
# HTTP Session avec retries pour Waynium
# -----------------------------------------------------------------------------
def build_session():
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.6,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["POST", "GET"])
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

http = build_session()

# -----------------------------------------------------------------------------
# Compat / Normalisation (assouplissement)
# -----------------------------------------------------------------------------
ENUM_MAPS = {
    "tripType": {
        "POINT-TO-POINT/CITY-TO-CITY": "POINT_TO_POINT",
        "POINT_TO_POINT": "POINT_TO_POINT",
        "CITY_TO_CITY": "POINT_TO_POINT",
        "POINT-TO-POINT": "POINT_TO_POINT",
        "POINT TO POINT": "POINT_TO_POINT",
    },
    "serviceLevel": {
        "SERVICE +": "SERVICE_PLUS",
        "SERVICE+": "SERVICE_PLUS",
        "SERVICE PLUS": "SERVICE_PLUS",
        "SERVICE_PLUS": "SERVICE_PLUS",
    },
}

ENUM_UPPER_FIELDS = [
    "reservationSource", "serviceType", "vehicleType", "status",
    "locationType", "tripType", "paymentType"
]

PHONE_FIELDS = ["mobileNumber", "phoneNumber", "bookedByPhone"]

def _force_utc_z(dt_str):
    if not isinstance(dt_str, str) or not dt_str:
        return dt_str
    # déjà avec TZ ?
    if dt_str.endswith("Z") or re.search(r"[+-]\d{2}:\d{2}$", dt_str):
        return dt_str
    return dt_str + "Z"

def _to_float(x):
    try:
        return float(x)
    except Exception:
        return x

def _upper_enum(value, field):
    if not isinstance(value, str):
        return value
    v = value.strip()
    if field in ENUM_MAPS and v.upper() in ENUM_MAPS[field]:
        return ENUM_MAPS[field][v.upper()]
    return v.upper()

def _clean_phone(p):
    if not isinstance(p, str):
        return p
    p = re.sub(r"[^\d+]", "", p)
    p = "+" + re.sub(r"[^\d]", "", p) if p.startswith("+") else re.sub(r"[^\d]", "", p)
    return p

def _normalize_location_type(v):
    if not isinstance(v, str):
        return v
    m = v.strip().upper()
    if m in {"AIRPORT", "HOTEL", "ADDRESS", "PORT", "STATION"}:
        return m
    if m in {"TRANSPORTATIONCENTER", "TRANSPORTATION_CENTER"}:
        return "AIRPORT"
    return m

def _recompute_domestic(pu_tcd):
    # Heuristique simple: si arrivée BRU et source != BRU -> international
    if not isinstance(pu_tcd, dict):
        return
    source = (pu_tcd.get("source") or "").upper()
    arrival = (pu_tcd.get("transportationCenterCode") or "").upper()
    if not source or not arrival:
        return
    if arrival == "BRU" and source and source != "BRU":
        pu_tcd["domestic"] = False

def normalize_payload(data: dict, headers: dict):
    """
    Retourne: normalized_data, effective_api_key, corrections_appliquees(list)
    """
    corrections = []
    if not isinstance(data, dict):
        return data, None, corrections

    # Auth
    api_key = None
    for hk in ("x-api-key", "X-API-KEY", "authorization", "Authorization"):
        if hk in headers and headers[hk]:
            val = headers[hk]
            if hk.lower().startswith("authorization") and isinstance(val, str) and val.lower().startswith("bearer "):
                api_key = val.split(" ", 1)[1].strip()
                corrections.append("auth:Authorization->Bearer")
            else:
                api_key = val.strip()
                corrections.append(f"auth:{hk}")
            break

    if not api_key and ACCEPT_BODY_APIKEY:
        if "apiKey" in data and data["apiKey"]:
            api_key = str(data["apiKey"]).strip()
            corrections.append("auth:body.apiKey")

    data["_effectiveApiKey"] = api_key

    # publishTime
    if "publishTime" in data and isinstance(data["publishTime"], str):
        if not (data["publishTime"].endswith("Z") or re.search(r"[+-]\d{2}:\d{2}$", data["publishTime"])):
            data["publishTime"] = _force_utc_z(data["publishTime"])
            corrections.append("publishTime:+Z")

    trip = data.get("trip") or {}
    data["trip"] = trip

    # enums uppercase / mapping
    for f in ENUM_UPPER_FIELDS:
        if f in trip and trip[f] is not None:
            old = trip[f]
            newv = _upper_enum(trip[f], f)
            if newv != old:
                corrections.append(f"{f}:{old}→{newv}")
            trip[f] = newv

    # nested: passengerDetails
    if "passengerDetails" in trip and isinstance(trip["passengerDetails"], dict):
        pd = trip["passengerDetails"]
        if "serviceLevel" in pd and pd["serviceLevel"] is not None:
            old = pd["serviceLevel"]
            newv = _upper_enum(pd["serviceLevel"], "serviceLevel")
            if newv != old:
                corrections.append(f"serviceLevel:{old}→{newv}")
            pd["serviceLevel"] = newv
        for pf in PHONE_FIELDS:
            if pf in pd and pd[pf]:
                old = pd[pf]
                pd[pf] = _clean_phone(pd[pf])
                if pd[pf] != old:
                    corrections.append(f"passengerDetails.{pf}:cleaned")

    # pickUpDetails
    if "pickUpDetails" in trip and isinstance(trip["pickUpDetails"], dict):
        pu = trip["pickUpDetails"]
        if "locationType" in pu and pu["locationType"]:
            old = pu["locationType"]
            pu["locationType"] = _normalize_location_type(pu["locationType"])
            if pu["locationType"] != old:
                corrections.append(f"pickUpDetails.locationType:{old}→{pu['locationType']}")
        if "pickUpTime" in pu and pu["pickUpTime"]:
            old = pu["pickUpTime"]
            pu["pickUpTime"] = _force_utc_z(pu["pickUpTime"])
            if pu["pickUpTime"] != old:
                corrections.append("pickUpTime:+Z")
        for k in ("puLatitude", "puLongitude"):
            if k in pu and isinstance(pu[k], str):
                old = pu[k]
                pu[k] = _to_float(pu[k])
                if pu[k] != old:
                    corrections.append(f"{k}:toFloat")
        tcd = pu.get("transportationCenterDetails")
        if isinstance(tcd, dict):
            before = tcd.get("domestic")
            _recompute_domestic(tcd)
            after = tcd.get("domestic")
            if before != after:
                corrections.append("transportationCenterDetails.domestic:recomputed")

    # dropOffDetails
    if "dropOffDetails" in trip and isinstance(trip["dropOffDetails"], dict):
        do = trip["dropOffDetails"]
        if "locationType" in do and do["locationType"]:
            old = do["locationType"]
            do["locationType"] = _normalize_location_type(do["locationType"])
            if do["locationType"] != old:
                corrections.append(f"dropOffDetails.locationType:{old}→{do['locationType']}")
        for k in ("doLatitude", "doLongitude"):
            if k in do and isinstance(do[k], str):
                old = do[k]
                do[k] = _to_float(do[k])
                if do[k] != old:
                    corrections.append(f"{k}:toFloat")
        ad = do.get("addressDetails")
        if isinstance(ad, dict):
            city = (ad.get("city") or "").strip().lower()
            cc = (ad.get("countryCode") or ad.get("country") or "").strip().upper()
            if city == "brussels" and cc == "BE" and not ad.get("postalCode"):
                ad["postalCode"] = "1000"
                corrections.append("addressDetails.postalCode:default(1000)")

    # trip-level timestamps / phones
    for tf in ("updateTime",):
        if tf in trip and trip[tf]:
            old = trip[tf]
            trip[tf] = _force_utc_z(trip[tf])
            if trip[tf] != old:
                corrections.append(f"{tf}:+Z")
    for pf in PHONE_FIELDS:
        if pf in trip and trip[pf]:
            old = trip[pf]
            trip[pf] = _clean_phone(trip[pf])
            if trip[pf] != old:
                corrections.append(f"{pf}:cleaned")

    # reservationPreferences type fallback
    if "reservationPreferences" in trip and isinstance(trip["reservationPreferences"], list):
        for pref in trip["reservationPreferences"]:
            if isinstance(pref, dict):
                t = pref.get("type")
                if not isinstance(t, str) or t.strip().upper() not in {"NOTE", "INSTRUCTION"}:
                    pref["type"] = "NOTE"
                    corrections.append("reservationPreferences.type:NOTE(default)")

    return data, api_key, corrections

# -----------------------------------------------------------------------------
# Validations minimales (post-normalisation)
# -----------------------------------------------------------------------------
def validate_minimal(data: dict):
    """
    Retourne (ok: bool, errors: list[str]).
    On garde light, car la vraie validation est dans transform_payload/Waynium.
    """
    errs = []
    trip = data.get("trip")
    if not isinstance(trip, dict):
        return False, ["missing trip"]

    # Champs clés
    required = [
        ("trip.reservationNumber", trip.get("reservationNumber")),
        ("trip.status", trip.get("status")),
        ("trip.tripType", trip.get("tripType")),
        ("trip.serviceType", trip.get("serviceType")),
        ("trip.vehicleType", trip.get("vehicleType")),
        ("trip.pickUpDetails", trip.get("pickUpDetails")),
        ("trip.dropOffDetails", trip.get("dropOffDetails")),
    ]
    for name, val in required:
        if val in (None, "", {}):
            errs.append(f"missing {name}")

    # Formats simples
    pu = trip.get("pickUpDetails", {})
    if isinstance(pu, dict):
        if "pickUpTime" not in pu or not pu.get("pickUpTime"):
            errs.append("missing trip.pickUpDetails.pickUpTime")

    return (len(errs) == 0), errs

# -----------------------------------------------------------------------------
# Réponses utilitaires
# -----------------------------------------------------------------------------
def resp_error_unauthorized(req_id, message="Missing or invalid API key"):
    # 401 standard
    body = {"status": "error", "message": message, "requestId": req_id}
    return jsonify(body), 401

def resp_error_validation(req_id, errors, corrections=None):
    """
    On garde le **HTTP 400** standard, mais on inclut un code applicatif 996
    pour rester compatible avec tes logs/monitoring.
    """
    body = {
        "status": "error",
        "code": 996,
        "message": "Validation failed",
        "errors": errors,
        "correctionsApplied": corrections or [],
        "requestId": req_id
    }
    return jsonify(body), 400

def resp_error_upstream(req_id, status_code, text):
    body = {
        "status": "upstream_error",
        "upstream": "waynium",
        "code": status_code,
        "response": text,
        "requestId": req_id
    }
    # 5xx si Waynium 5xx sinon 502
    http_code = 502 if status_code < 500 else status_code
    return jsonify(body), http_code

def resp_ok(req_id, waynium_json, corrections):
    body = {
        "status": "success",
        "requestId": req_id,
        "correctionsApplied": corrections,
        "waynium_response": waynium_json
    }
    return jsonify(body), 200

# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------
@app.route("/carey/webhook", methods=["POST"])
def carey_webhook():
    req_id = str(uuid.uuid4())
    try:
        raw = request.get_data(as_text=True)  # trace brut si JSON invalide
        incoming = request.get_json(silent=True)
        if incoming is None:
            log_json("warning", event="parse_error", requestId=req_id, raw=raw)
            return resp_error_validation(req_id, ["invalid JSON (parse error)"])

        # Normalisation / Compat
        normalized, effective_key, corrections = normalize_payload(incoming, dict(request.headers))

        # Auth
        if REQUIRE_HEADER_API_KEY and not any(h in request.headers for h in ("x-api-key", "X-API-KEY", "Authorization", "authorization")):
            log_json("warning", event="auth_missing_header", requestId=req_id)
            return resp_error_unauthorized(req_id, "API key must be in header")

        if not effective_key or effective_key not in WEBHOOK_API_KEYS:
            log_json("warning", event="auth_invalid", requestId=req_id)
            return resp_error_unauthorized(req_id)

        # Validations minimales (post-compat)
        ok, errors = validate_minimal(normalized)
        if not ok:
            log_json("warning", event="validation_failed", requestId=req_id, errors=errors, corr=corrections)
            return resp_error_validation(req_id, errors, corrections)

        # Transformation Carey -> Waynium
        try:
            waynium_payload = transform_payload(normalized)
        except Exception as te:
            log_json("error", event="transform_error", requestId=req_id, error=str(te))
            # 996 aussi ici (côté mapping)
            return resp_error_validation(req_id, [f"transform_error: {str(te)}"], corrections)

        # Envoi Waynium
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {WAYNIUM_API_KEY}"
        }

        r = http.post(WAYNIUM_API_URL, json=waynium_payload, headers=headers, timeout=REQUEST_TIMEOUT)
        log_json("info", event="waynium_response", requestId=req_id, status=r.status_code)

        # Succès attendu: 200 ou 201 (selon leur API)
        if r.status_code in (200, 201):
            # sécurité: essaye de parser JSON, sinon retourne texte
            try:
                body = r.json()
            except Exception:
                body = {"raw": r.text}
            return resp_ok(req_id, body, corrections)

        # Erreur côté Waynium
        return resp_error_upstream(req_id, r.status_code, r.text)

    except Exception as e:
        # 500 interne
        log_json("error", event="unhandled_exception", requestId=req_id, error=str(e))
        body = {"status": "error", "message": str(e), "requestId": req_id}
        return jsonify(body), 500

# --- Health / readiness / version ---
@app.get("/healthz")
def healthz():
    return jsonify({"ok": True, "ts": datetime.utcnow().isoformat() + "Z"}), 200

@app.get("/readyz")
def readyz():
    # ici tu peux ajouter des checks (clé Waynium présente, etc.)
    ready = WAYNIUM_API_KEY != "abllimousines"
    return jsonify({"ready": ready}), 200 if ready else 503

@app.get("/version")
def version():
    return jsonify({
        "name": "carey-webhook",
        "version": os.getenv("VERSION", "1.0.0"),
        "time": datetime.utcnow().isoformat() + "Z"
    }), 200

# -----------------------------------------------------------------------------
# Entrypoint local
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
