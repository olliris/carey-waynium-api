import json
from transform import transform_payload

with open("test_carey_payload.json", "r") as f:
    carey_data = json.load(f)

waynium_payload = transform_payload(carey_data)

print("=== WAYNIUM PAYLOAD ===")
print(json.dumps(waynium_payload, indent=2))
