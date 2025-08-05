import json
from transform import transform_to_waynium

with open("test_carey_payload.json", "r") as file:
    carey_payload = json.load(file)

waynium_payload = transform_to_waynium(carey_payload)

print("=== WAYNIUM PAYLOAD ===")
print(json.dumps(waynium_payload, indent=2))

# ✅ Vérifications automatiques de quelques champs clés
expected_keys = [
    "booking_reference",
    "pickup_time",
    "pickup_address",
    "dropoff_address",
    "passenger_first_name",
    "passenger_last_name",
    "passenger_mobile",
    "passenger_email",
    "vehicle_type",
    "service_type",
    "city",
    "trip_status",
    "created_by",
    "bags",
    "service_level",
    "reservation_source"
]

print("\n=== FIELD CHECK ===")
for key in expected_keys:
    if key in waynium_payload:
        print(f"[✔] {key} found: {waynium_payload[key]}")
    else:
        print(f"[✘] {key} missing!")
