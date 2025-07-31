
import json
import logging

# Chargement du mapping statique Carey → Waynium
FIELD_MAPPING = {
    "trip.reservationNumber": "booking_reference",
    "trip.reservationSource": "booking_source",
    "trip.serviceProvider": "supplier_id",
    "trip.accountName": "account_name"
}

def extract_nested_value(data, key_path):
    """Extrait une valeur d'un dictionnaire imbriqué selon un chemin du type 'a.b.c'"""
    keys = key_path.split('.')
    for key in keys:
        if isinstance(data, dict) and key in data:
            data = data[key]
        else:
            return None
    return data

def transform_payload(carey_payload: dict) -> dict:
    waynium_payload = {}
    for carey_key, waynium_key in FIELD_MAPPING.items():
        value = extract_nested_value(carey_payload, carey_key)
        if value is not None:
            waynium_payload[waynium_key] = value
    return waynium_payload

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json", help="Fichier JSON Carey à convertir")
    args = parser.parse_args()

    try:
        with open(args.input_json, "r", encoding="utf-8") as f:
            carey_data = json.load(f)
        result = transform_payload(carey_data)
        print(json.dumps(result, indent=2))
    except Exception as e:
        logging.error(f"Erreur lors de la transformation: {e}")
