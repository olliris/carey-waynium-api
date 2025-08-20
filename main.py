# main.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from transform import transform_payload
import os, re, json, logging, requests
from datetime import datetime

# ---------------------------------- Config ----------------------------------
# -> Tu peux aussi passer ces valeurs par variables d'env
WAYNIUM_API_URL    = os.getenv("WAYNIUM_API_URL", "https://stage-gdsapi.waynium.net/api-externe/set-ressource")
WAYNIUM_API_KEY    = os.getenv("WAYNIUM_API_KEY", "abllimousines")
WAYNIUM_API_SECRET = os.getenv("WAYNIUM_API_SECRET", "be5F47w72eGxwWe8EAZe9Y4vP38g2rRG")
WAYNIUM_AUTH_MODE  = os.getenv("WAYNIUM_AUTH_MODE", "HEADERS").upper()  # HEADERS | BASIC | HMAC

WEBHOOK_API_KEYS   = {k.strip() for k in os.getenv("WEBHOOK_API_KEYS", "1").split(",") if k.strip()}
REQUEST_TIMEOUT    = float(os.getenv("REQUEST_TIMEOUT", "15"))

# --------------------------------- Flask app --------------------------------
app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("carey-webhook")

def log_json(level, **fields):
    fields.setdefault("ts", datetime.utcnow().isoformat() + "Z")
    getattr(log, level)(json.dumps(fields, ensure_ascii=False))

# ------------------------------ Compat helpers ------------------------------
ENUM_MAPS = {
    "tripType": {
        "POINT-TO-POINT/CITY-TO-CITY": "POINT_TO_POINT",
        "CITY_TO_CITY": "POINT_TO_POINT",
        "POINT-TO-POINT": "POINT_TO_POINT",
        "POINT TO POINT": "POINT_TO_POINT",
        "POINT_TO_POINT": "POINT_TO_POINT",
    },
    "serviceLevel": {
        "SERVICE +": "SERVICE_PLUS",
        "SERVICE+": "SERVICE_PLUS",
        "SERVICE PLUS": "SERVICE_PLUS",
        "SERVICE_PLUS": "SERVICE_PLUS",
    },
}
ENUM_UPPER_FIELDS = ["reservationSource", "serviceType", "vehicleType", "status", "locationType", "tripType", "paymentType"]
PHONE_FIELDS = ["mobileNumber", "phoneNumber", "bookedByPhone"]

def _force_utc_z(dt_str):
    if isinstance(dt_str, str) and dt_str and not (dt_str.endswith("Z") or re.search(r"[+-]\d{2}:\d{2}$", dt_str)):
        return dt_str + "Z"
    return dt_str

def _to_float(x):
    try: return float(x)
    except Exception: return x

def _upper_enum(v, field):
    if not isinstance(v, str): return v
    u = v.strip().upper()
    if field in ENUM_MAPS and u in ENUM_MAPS[field]: return ENUM_MAPS[field][u]
    return u

def _clean_phone(p):
    if not isinstance(p, str): return p
    p2 = re.sub(r"[^\d+]", "", p)
    return ("+" + re.sub(r"[^\d]", "", p2[1:])) if p2.startswith("+") else re.sub(r"[^\d]", "", p2)

def _normalize_location_type(v):
    if not isinstance(v, str): return v
    u = v.strip().upper()
    if u in {"AIRPORT","HOTEL","ADDRESS","PORT","STATION"}: return u
    if u in {"TRANSPORTATIONCENTER","TRANSPORTATION_CENTER"}: return "AIRPORT"
    return u

def _recompute_domestic(tcd: dict):
    if not isinstance(tcd, dict): return
    src = (tcd.get("source") or "").upper()
    arr = (tcd.get("transportationCenterCode") or "").upper()
    if arr == "BRU" and src and src != "BRU":
        tcd["domestic"] = False

def normalize_payload(data: dict, headers: dict):
    """
    Retourne (normalized_data, effective_api_key, corrections_appliquees)
    """
    corr = []
    if not isinstance(data, dict):
        return data, None, corr

    # Auth: header ou body (legacy)
    api_key = None
    for hk in ("x-api-key","X-API-KEY","authorization","Authorization"):
        if hk in headers and headers[hk]:
            val = str(headers[hk])
            if hk.lower().startswith("authorization") and val.lower().startswith("bearer "):
                api_key = val.split(" ",1)[1].strip(); corr.append("auth:Authorization->Bearer")
            else:
                api_key = val.strip(); corr.append(f"auth:{hk}")
            break
    if not api_key and "apiKey" in data and data["apiKey"]:
        api_key = str(data["apiKey"]).strip(); corr.append("auth:body.apiKey")
    data["_effectiveApiKey"] = api_key

    # publishTime
    if "publishTime" in data:
        old = data["publishTime"]
        data["publishTime"] = _force_utc_z(data["publishTime"])
        if data["publishTime"] != old: corr.append("publishTime:+Z")

    trip = data.get("trip") or {}
    data["trip"] = trip

    # enums top-level
    for f in ENUM_UPPER_FIELDS:
        if f in trip and trip[f] is not None:
            old = trip[f]; trip[f] = _upper_enum(trip[f], f)
            if trip[f] != old: corr.append(f"{f}:{old}→{trip[f]}")

    # passengerDetails
    if isinstance(trip.get("passengerDetails"), dict):
        pd = trip["passengerDetails"]
        if "serviceLevel" in pd and pd["serviceLevel"] is not None:
            old = pd["serviceLevel"]; pd["serviceLevel"] = _upper_enum(pd["serviceLevel"], "serviceLevel")
            if pd["serviceLevel"] != old: corr.append(f"serviceLevel:{old}→{pd['serviceLevel']}")
        for pf in PHONE_FIELDS:
            if pf in pd and pd[pf]:
                old = pd[pf]; pd[pf] = _clean_phone(pd[pf])
                if pd[pf] != old: corr.append(f"passengerDetails.{pf}:cleaned")

    # pickUpDetails
    if isinstance(trip.get("pickUpDetails"), dict):
        pu = trip["pickUpDetails"]
        if "locationType" in pu and pu["locationType"]:
            old = pu["locationType"]; pu["locationType"] = _normalize_location_type(pu["locationType"])
            if pu["locationType"] != old: corr.append(f"pickUpDetails.locationType:{old}→{pu['locationType']}")
        if "pickUpTime" in pu and pu["pickUpTime"]:
            old = pu["pickUpTime"]; pu["pickUpTime"] = _force_utc_z(pu["pickUpTime"])
            if pu["pickUpTime"] != old: corr.append("pickUpTime:+Z")
        for k in ("puLatitude","puLongitude"):
            if k in pu and isinstance(pu[k], str):
                old = pu[k]; pu[k] = _to_float(pu[k])
                if pu[k] != old: corr.append(f"{k}:toFloat")
        tcd = pu.get("transportationCenterDetails")
        if isinstance(tcd, dict):
            before = tcd.get("domestic"); _recompute_domestic(tcd); after = tcd.get("domestic")
            if before != after: corr.append("transportationCenterDetails.domestic:recomputed")

    # dropOffDetails
    if isinstance(trip.get("dropOffDetails"), dict):
        do = trip["dropOffDetails"]
        if "locationType" in do and do["locationType"]:
            old = do["locationType"]; do["locationType"] = _normalize_location_type(do["locationType"])
            if do["locationType"] != old: corr.append(f"dropOffDetails.locationType:{old}→{do['locationType']}")
        for k in ("doLatitude","doLongitude"):
            if k in do and isinstance(do[k], str):
                old = do[k]; do[k] = _to_float(do[k])
                if do[k] != old: corr.append(f"{k}:toFloat")
        ad = do.get("addressDetails")
        if isinstance(ad, dict):
            city = (ad.get("city") or "").strip().lower()
            cc = (ad.get("countryCode") or ad.get("country") or "").strip().upper()
            if city == "brussels" and cc == "BE" and not ad.get("postalCode"):
                ad["postalCode"] = "1000"; corr.append("addressDetails.postalCode:default(1000)")

    # trip-level times/phones
    if "updateTime" in trip and trip["updateTime"]:
        old = trip["updateTime"]; trip["updateTime"] = _force_utc_z(trip["updateTime"])
        if trip["updateTime"] != old: corr.append("updateTime:+Z")
    for pf in PHONE_FIELDS:
        if pf in trip and trip[pf]:
            old = trip[pf]; trip[pf] = _clean_phone(trip[pf])
            if trip[pf] != old: corr.append(f"{pf}:cleaned")

    # reservationPreferences fallback
    if isinstance(trip.get("reservationPreferences"), list):
        for pref in trip["reservationPreferences"]:
            if isinstance(pref, dict):
                t = pref.get("type")
                if not isinstance(t, str) or t.strip().upper() not in {"NOTE","INSTRUCTION"}:
                    pref["type"] = "NOTE"

    return data, api_key, corr

def validate_minimal(data: dict):
    errs = []
    trip = data.get("trip")
    if not isinstance(trip, dict):
        return False, ["missing trip"]

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
        if val in (None, "", {}): errs.append(f"missing {name}")

    pu = trip.get("pickUpDetails", {})
    if isinstance(pu, dict) and not pu.get("pickUpTime"):
        errs.append("missing trip.pickUpDetails.pickUpTime")

    return (len(errs) == 0), errs

def _waynium_headers(body_bytes: bytes) -> dict:
    """
    HEADERS : X-API-KEY / X-API-SECRET
    BASIC   : Authorization: Basic base64(apiKey:secret)
    HMAC    : X-API-KEY + X-SIGNATURE (HMAC-SHA256(body))
    """
    import base64, hmac, hashlib
    if WAYNIUM_AUTH_MODE == "BASIC":
        token = base64.b64encode(f"{WAYNIUM_API_KEY}:{WAYNIUM_API_SECRET}".encode("utf-8")).decode("ascii")
        return {"Content-Type":"application/json","Authorization":f"Basic {token}"}
    if WAYNIUM_AUTH_MODE == "HMAC":
        signature = hmac.new(WAYNIUM_API_SECRET.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()
        return {"Content-Type":"application/json","X-API-KEY":WAYNIUM_API_KEY,"X-SIGNATURE":signature}
    return {"Content-Type":"application/json","X-API-KEY":WAYNIUM_API_KEY,"X-API-SECRET":WAYNIUM_API_SECRET}

# ---------------------------------- Routes ----------------------------------
@app.post("/carey/webhook")
def carey_webhook():
    try:
        raw = request.get_data(as_text=True)
        incoming = request.get_json(silent=True)
        if incoming is None:
            log_json("warning", event="parse_error", raw=raw[:2000])
            return jsonify({"status":"error","code":996,"message":"invalid JSON (parse error)"}), 400

        normalized, effective_key, corrections = normalize_payload(incoming, dict(request.headers))

        # Auth
        if not effective_key or effective_key not in WEBHOOK_API_KEYS:
            log_json("warning", event="auth_invalid")
            return jsonify({"status":"error","message":"Missing or invalid API key"}), 401

        # Validation light
        ok, errors = validate_minimal(normalized)
        if not ok:
            log_json("warning", event="validation_failed", errors=errors, corr=corrections)
            return jsonify({"status":"error","code":996,"message":"Validation failed",
                            "errors":errors,"correctionsApplied":corrections}), 400

        # Transform Carey -> Waynium
        try:
            waynium_payload = transform_payload(normalized)
        except Exception as te:
            log_json("error", event="transform_error", error=str(te))
            return jsonify({"status":"error","code":996,"message":"transform_error",
                            "errors":[str(te)],"correctionsApplied":corrections}), 400

        # Envoi Waynium
        body_str = json.dumps(waynium_payload, ensure_ascii=False)
        headers = _waynium_headers(body_str.encode("utf-8"))
        r = requests.post(WAYNIUM_API_URL, data=body_str.encode("utf-8"), headers=headers, timeout=REQUEST_TIMEOUT)

        if r.status_code in (200, 201):
            try: body = r.json()
            except Exception: body = {"raw": r.text}
            return jsonify({"status":"success","waynium_response":body,"correctionsApplied":corrections}), 200

        # Erreurs Waynium
        return jsonify({"status":"upstream_error","upstream":"waynium","code":r.status_code,"response":r.text}), 502 if r.status_code < 500 else r.status_code

    except Exception as e:
        log_json("error", event="unhandled_exception", error=str(e))
        return jsonify({"status":"error","message":str(e)}), 500

@app.get("/healthz")
def healthz():
    return jsonify({"ok": True, "ts": datetime.utcnow().isoformat() + "Z"}), 200

@app.get("/readyz")
def readyz():
    ready = bool(WAYNIUM_API_KEY and WAYNIUM_API_SECRET and WAYNIUM_API_URL)
    return jsonify({"ready": ready}), 200 if ready else 503

@app.get("/version")
def version():
    return jsonify({"name":"carey-waynium-api","version":os.getenv("VERSION","1.0.0"),"time":datetime.utcnow().isoformat()+"Z"}), 200

# -------------------------------- Entrypoint -------------------------------
if __name__ == "__main__":
    # dev/local: python main.py
    app.run(host="0.0.0.0", port=int(os.getenv("PORT","5000")))
