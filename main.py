import re
from datetime import datetime

# Remaps et normalisations “soft”
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
    Retourne: (normalized_data, effective_api_key, corrections_appliquees[list])
    """
    corrections = []
    if not isinstance(data, dict):
        return data, None, corrections

    # --- Auth: header ou body (legacy) ---
    api_key = None
    for hk in ("x-api-key", "X-API-KEY", "authorization", "Authorization"):
        if hk in headers and headers[hk]:
            val = headers[hk]
            if hk.lower().startswith("authorization") and isinstance(val, str) and val.lower().startswith("bearer "):
                api_key = val.split(" ", 1)[1].strip()
                corrections.append("auth:Authorization->Bearer")
            else:
                api_key = str(val).strip()
                corrections.append(f"auth:{hk}")
            break
    if not api_key and "apiKey" in data and data["apiKey"]:
        api_key = str(data["apiKey"]).strip()
        corrections.append("auth:body.apiKey")

    data["_effectiveApiKey"] = api_key

    # --- publishTime ---
    if "publishTime" in data and isinstance(data["publishTime"], str):
        if not (data["publishTime"].endswith("Z") or re.search(r"[+-]\d{2}:\d{2}$", data["publishTime"])):
            data["publishTime"] = _force_utc_z(data["publishTime"])
            corrections.append("publishTime:+Z")

    trip = data.get("trip") or {}
    data["trip"] = trip

    # --- enums upper/mapping ---
    for f in ENUM_UPPER_FIELDS:
        if f in trip and trip[f] is not None:
            old = trip[f]
            newv = _upper_enum(trip[f], f)
            if newv != old:
                corrections.append(f"{f}:{old}→{newv}")
            trip[f] = newv

    # --- passengerDetails ---
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

    # --- pickUpDetails ---
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

    # --- dropOffDetails ---
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

    # --- trip-level timestamps / phones ---
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

    # --- reservationPreferences fallback ---
    if "reservationPreferences" in trip and isinstance(trip["reservationPreferences"], list):
        for pref in trip["reservationPreferences"]:
            if isinstance(pref, dict):
                t = pref.get("type")
                if not isinstance(t, str) or t.strip().upper() not in {"NOTE", "INSTRUCTION"}:
                    pref["type"] = "NOTE"

    return data, api_key, corrections

def validate_minimal(data: dict):
    """
    Validation légère post-normalisation.
    Retourne (ok: bool, errors: list[str])
    """
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
        if val in (None, "", {}):
            errs.append(f"missing {name}")

    pu = trip.get("pickUpDetails", {})
    if isinstance(pu, dict):
        if "pickUpTime" not in pu or not pu.get("pickUpTime"):
            errs.append("missing trip.pickUpDetails.pickUpTime")

    return (len(errs) == 0), errs
