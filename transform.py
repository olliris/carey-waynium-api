# transform.py
import json
import logging
from datetime import datetime
import re

def extract(d, path, default=None):
    cur = d
    for k in path.split("."):
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        else:
            return default
    return cur

def to_utc_z(dt):
    if not dt or not isinstance(dt, str):
        return dt
    if dt.endswith("Z") or re.search(r"[+-]\d{2}:\d{2}$", dt):
        return dt
    return dt + "Z"

def clean_phone(p):
    if not isinstance(p, str):
        return p
    p = re.sub(r"[^\d+]", "", p)
    if p and p[0] != "+":
        return "+" + re.sub(r"[^\d]", "", p)
    return p

def upper_enum(v, fallback=None):
    if v is None:
        return fallback
    if not isinstance(v, str):
        return str(v).upper()
    return v.strip().upper().replace(" ", "_")

def to_float(x):
    try:
        return float(x)
    except Exception:
        return None

TRIP_TYPE_MAP = {
    "ONEWAY": "POINT_TO_POINT",
    "ONE_WAY": "POINT_TO_POINT",
    "ROUNDTRIP": "POINT_TO_POINT",
    "CITY_TO_CITY": "POINT_TO_POINT",
    "POINT_TO_POINT": "POINT_TO_POINT",
}

SERVICE_TYPE_MAP = {
    "AIRPORT": "PREMIUM",
    "PREMIUM": "PREMIUM",
    "BUSINESS": "PREMIUM",
    "FIRST_CLASS": "PREMIUM",
}

VEHICLE_TYPE_MAP = {
    "BERLINE": "EXECUTIVE_SEDAN",
    "SEDAN": "EXECUTIVE_SEDAN",
    "EXECUTIVE_SEDAN": "EXECUTIVE_SEDAN",
    "VAN": "EXECUTIVE_VAN",
    "SUV": "SUV",
}

STATUS_MAP = {
    "CONFIRMED": "OPEN",
    "OPEN": "OPEN",
    "PENDING": "OPEN",
    "CANCELLED": "CANCELLED",
    "CANCELED": "CANCELLED",
    "COMPLETED": "COMPLETED",
}

SERVICE_LEVEL_MAP = {
    "FIRST_CLASS": "SERVICE_PLUS",
    "SERVICE_PLUS": "SERVICE_PLUS",
    "STANDARD": "SERVICE_PLUS",
}

def map_enum(v, table, fallback=None):
    if v is None:
        return fallback
    key = upper_enum(v)
    return table.get(key, fallback or key)

def transform_to_waynium(carey_payload: dict) -> dict:
    src = carey_payload

    p = src.get("passenger", {}) or {}
    passenger_first = p.get("firstName") or ""
    passenger_last = p.get("lastName") or ""

    pu = src.get("pickup", {}) or {}
    do = src.get("dropoff", {}) or {}
    s = src.get("service", {}) or {}
    pay = src.get("payment", {}) or {}
    est = pay.get("priceEstimate", {}) or {}

    out = {
        "booking_reference": src.get("reservationNumber") or src.get("reservationId") or "",
        "created_by": src.get("createdBy") or "",
        "reservation_source": src.get("reservationSource") or "",
        "supplier_id": src.get("serviceProvider") or "",
        "account_name": src.get("accountName") or "",

        "passenger_first_name": passenger_first,
        "passenger_last_name": passenger_last,
        "passenger_email": p.get("email") or "",
        "passenger_mobile": clean_phone(p.get("mobile") or ""),
        "service_level": map_enum(p.get("serviceLevel"), SERVICE_LEVEL_MAP, "SERVICE_PLUS"),
        "passenger_count": p.get("passengerCount") or 1,

        "pickup_time": to_utc_z(pu.get("time")),
        "pickup_location_type": upper_enum(pu.get("locationType") or "ADDRESS"),
        "pickup_instructions": pu.get("locationInstructions") or "",
        "pickup_special_instructions": pu.get("specialInstructions") or "",
        "pickup_latitude": to_float(pu.get("latitude")),
        "pickup_longitude": to_float(pu.get("longitude")),
        "pickup_address": pu.get("address") or "",
        "pickup_city": pu.get("city") or "",
        "pickup_postal_code": pu.get("postalCode") or "",
        "pickup_country_code": pu.get("country") or "",
        "pickup_transport_center_name": extract(pu, "transportationCenterDetails.transportationCenterName") \
                                        or extract(pu, "transportationCenterDetails.transportationCenterCode") or "",
        "pickup_transport_center_code": extract(pu, "transportationCenterDetails.transportationCenterCode") or "",
        "pickup_carrier_name": extract(pu, "transportationCenterDetails.carrierName") or "",
        "pickup_carrier_code": extract(pu, "transportationCenterDetails.carrierCode") or "",
        "pickup_carrier_number": extract(pu, "transportationCenterDetails.carrierNumber") or "",
        "pickup_source": extract(pu, "transportationCenterDetails.source") or "",
        "pickup_domestic": bool(extract(pu, "transportationCenterDetails.domestic")),
        "pickup_private_aviation": bool(extract(pu, "transportationCenterDetails.privateAviation")),

        "dropoff_address": do.get("address") or "",
        "dropoff_city": do.get("city") or "",
        "dropoff_postal_code": do.get("postalCode") or "",
        "dropoff_country_code": do.get("country") or "",
        "dropoff_latitude": to_float(do.get("latitude")),
        "dropoff_longitude": to_float(do.get("longitude")),

        "service_type": map_enum(s.get("type"), SERVICE_TYPE_MAP, "PREMIUM"),
        "trip_type": map_enum(s.get("tripType"), TRIP_TYPE_MAP, "POINT_TO_POINT"),
        "vehicle_type": map_enum(s.get("vehicleType"), VEHICLE_TYPE_MAP, "EXECUTIVE_SEDAN"),
        "bags": s.get("bagsCount") or 0,
        "pickup_sign": s.get("pickupSign") or "",
        "greeter_requested": bool(s.get("greeterRequested", False)),

        "payment_method": upper_enum(pay.get("method") or "ACCOUNT"),
        "price_total": est.get("total"),
        "price_currency": est.get("currency"),
        "price_tax_included": bool(est.get("taxIncluded", True)),

        "booked_by": src.get("bookedBy") or "",
        "booked_by_phone": clean_phone(src.get("bookedByPhone") or ""),
        "trip_status": map_enum(src.get("status"), STATUS_MAP, "OPEN"),
        "notes": src.get("notes") or "",

        "reservation_version": src.get("reservationVersion") or 1,
        "update_time": to_utc_z(src.get("updateTime")),
        "meta_created": to_utc_z(extract(src, "meta.created")),
        "meta_source": extract(src, "meta.source") or "",

        "city": None,
    }

    out["city"] = out["dropoff_city"] or out["pickup_city"]
    return out

def transform_payload(carey_payload: dict) -> dict:
    # Compat: alias pour l’ancien nom utilisé ailleurs
    return transform_to_waynium(carey_payload)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json", help="Fichier JSON Carey à convertir")
    args = parser.parse_args()
    with open(args.input_json, "r", encoding="utf-8") as f:
        carey_data = json.load(f)
    print(json.dumps(transform_to_waynium(carey_data), indent=2, ensure_ascii=False))
