# transform.py - Conforme au format Waynium réel
import re
from datetime import datetime
from typing import Optional

def extract(d, path, default=None):
    """Navigation sécurisée dans dict imbriqués"""
    cur = d
    for k in path.split("."):
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        else:
            return default
    return cur

def to_utc_z(dt):
    """Force le suffix Z pour UTC"""
    if not dt or not isinstance(dt, str):
        return dt
    if dt.endswith("Z") or re.search(r"[+-]\d{2}:\d{2}$", dt):
        return dt
    return dt + "Z"

def clean_phone(p):
    """Nettoie un numéro de téléphone au format international"""
    if not isinstance(p, str):
        return ""
    p = re.sub(r"[^\d+]", "", p)
    if not p:
        return ""
    if p[0] != "+":
        return "+" + p
    return p

def split_datetime(dt_str: str) -> tuple[str, str]:
    """Split ISO datetime en (date, heure) pour Waynium
    '2025-08-01T10:30:00Z' -> ('2025-08-01', '10:30')
    """
    if not dt_str:
        return "0000-00-00", "00:00"
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M")
    except:
        return "0000-00-00", "00:00"

def map_vehicle_type(carey_vehicle: str) -> str:
    """Map Carey vehicle -> Waynium MIS_TVE_ID
    Voir: https://abllimousines.way-plan.com/bop3/C_Gen_TypeVehicule/
    """
    mapping = {
        "BERLINE": "1",
        "SEDAN": "1",
        "EXECUTIVE_SEDAN": "1",
        "VAN": "2",
        "EXECUTIVE_VAN": "2",
        "MINIVAN": "2",
        "SUV": "3",
        "LUXURY_SEDAN": "4",
    }
    key = (carey_vehicle or "SEDAN").upper().replace(" ", "_")
    return mapping.get(key, "1")  # Default: berline

def map_service_type(carey_service: str) -> str:
    """Map service type -> Waynium MIS_TSE_ID
    1 = Transfert (point to point)
    2 = Mise à disposition (hourly)
    """
    key = (carey_service or "").upper()
    if "HOURLY" in key or "DISPOSITION" in key:
        return "2"
    return "1"  # Default: transfert

def detect_country_id(country_code: str) -> str:
    """Map ISO country code -> Waynium PAY_ID
    À compléter selon la base Waynium
    """
    mapping = {
        "FR": "65",  # France
        "BE": "21",  # Belgique
        "CH": "204", # Suisse
        "LU": "125", # Luxembourg
        "GB": "77",  # UK
        "US": "223", # USA
    }
    return mapping.get(country_code.upper(), "65")

def build_location_object(
    name: str,
    address: str,
    city: str,
    postal_code: str,
    country_code: str,
    latitude: Optional[float],
    longitude: Optional[float],
    location_type: str = "ADDRESS",
    airport_code: str = "",
    carey_ref: str = ""
) -> dict:
    """Construit un objet LIE_ID pour Waynium (lieu)"""
    
    # Type de lieu Waynium: 1=aéroport, 2=adresse, 3=hôtel, etc.
    tli_mapping = {
        "AIRPORT": "1",
        "HOTEL": "3",
        "ADDRESS": "2",
        "STATION": "4",
        "PORT": "5",
    }
    tli_id = tli_mapping.get(location_type.upper(), "2")
    
    # Formattage de l'adresse complète
    parts = [p for p in [name, address, postal_code, city] if p]
    formatted_address = ", ".join(parts)
    
    # Label du lieu (priorité: nom > ville > adresse)
    label = name or city or address or "Non spécifié"
    
    return {
        "LIE_TLI_ID": tli_id,
        "LIE_LIBELLE": label,
        "LIE_FORMATED": formatted_address,
        "LIE_VILLE": city or "",
        "LIE_CP": postal_code or "",
        "LIE_PAY_ID": detect_country_id(country_code),
        "LIE_LAT": str(latitude) if latitude else "",
        "LIE_LNG": str(longitude) if longitude else "",
        "LIE_REF_EXTERNE": carey_ref or airport_code or f"CAREY_{label.upper().replace(' ', '_')}"
    }

def transform_carey_v2_to_waynium(carey_payload: dict, cli_id: int = 320) -> dict:
    """
    Transforme un payload Carey (v2 ou legacy) vers le format Waynium complet
    
    Args:
        carey_payload: JSON Carey (format v2 avec pickup/dropoff OU legacy avec trip.*)
        cli_id: ID client Waynium (320 par défaut, à mapper selon account)
    
    Returns:
        Payload Waynium complet prêt pour set-ressource
    """
    
    # Détection format Carey
    is_v2 = "pickup" in carey_payload or "reservationId" in carey_payload
    
    if is_v2:
        # Format v2
        src = carey_payload
        p = src.get("passenger", {}) or {}
        pu = src.get("pickup", {}) or {}
        do = src.get("dropoff", {}) or {}
        s = src.get("service", {}) or {}
        pay = src.get("payment", {}) or {}
        tcd = pu.get("transportationCenterDetails", {}) or {}
        
        reservation_number = src.get("reservationNumber") or src.get("reservationId", "")
        pickup_time_iso = pu.get("time", "")
        passenger_first = p.get("firstName", "")
        passenger_last = p.get("lastName", "")
        passenger_phone = clean_phone(p.get("mobile", ""))
        passenger_language = p.get("language", "FR")
        passenger_notes = src.get("notes", "")
        passenger_count = p.get("passengerCount", 1)
        
        vehicle_type = s.get("vehicleType", "SEDAN")
        service_type = s.get("type", "AIRPORT")
        trip_type = s.get("tripType", "ONEWAY")
        bags_count = s.get("bagsCount", 0)
        pickup_sign = s.get("pickupSign", "")
        greeter = s.get("greeterRequested", False)
        
        pickup_loc_type = pu.get("locationType", "ADDRESS")
        pickup_instructions = pu.get("locationInstructions", "")
        pickup_special = pu.get("specialInstructions", "")
        
        # Tarification
        price_total = pay.get("priceEstimate", {}).get("total", 0)
        price_currency = pay.get("priceEstimate", {}).get("currency", "EUR")
        
        # Pickup location
        pickup_name = tcd.get("transportationCenterName", "")
        pickup_code = tcd.get("transportationCenterCode", "")
        pickup_address = pu.get("address", "")
        pickup_city = pu.get("city", "")
        pickup_postal = pu.get("postalCode", "")
        pickup_country = pu.get("country", "")
        pickup_lat = pu.get("latitude")
        pickup_lng = pu.get("longitude")
        
        # Dropoff location
        dropoff_address = do.get("address", "")
        dropoff_city = do.get("city", "")
        dropoff_postal = do.get("postalCode", "")
        dropoff_country = do.get("country", "")
        dropoff_lat = do.get("latitude")
        dropoff_lng = do.get("longitude")
        
        booked_by = src.get("bookedBy", "")
        status = src.get("status", "CONFIRMED")
        
    else:
        # Format legacy (trip.*)
        trip = carey_payload.get("trip", {})
        pd = trip.get("passengerDetails", {}) or {}
        pu = trip.get("pickUpDetails", {}) or {}
        do = trip.get("dropOffDetails", {}) or {}
        tcd = pu.get("transportationCenterDetails", {}) or {}
        ad = do.get("addressDetails", {}) or {}
        
        reservation_number = trip.get("reservationNumber", "")
        pickup_time_iso = pu.get("pickUpTime", "")
        passenger_first = pd.get("firstName", "")
        passenger_last = pd.get("lastName", "")
        passenger_phone = clean_phone(pd.get("mobileNumber", ""))
        passenger_language = pd.get("language", "FR")
        passenger_notes = ""
        passenger_count = pd.get("passengerCount", 1)
        
        vehicle_type = trip.get("vehicleType", "SEDAN")
        service_type = trip.get("serviceType", "PREMIUM")
        trip_type = trip.get("tripType", "POINT_TO_POINT")
        bags_count = trip.get("bagsCount", 0)
        pickup_sign = trip.get("pickupSign", "")
        greeter = trip.get("greeterRequested", False)
        
        pickup_loc_type = pu.get("locationType", "ADDRESS")
        pickup_instructions = pu.get("locationInstructions", "")
        pickup_special = pu.get("specialInstructions", "")
        
        price_total = 0  # Pas de prix dans legacy
        price_currency = "EUR"
        
        # Pickup
        pickup_name = tcd.get("transportationCenterName", "")
        pickup_code = tcd.get("transportationCenterCode", "")
        pickup_address = ""
        pickup_city = ""
        pickup_postal = ""
        pickup_country = ""
        pickup_lat = pu.get("puLatitude")
        pickup_lng = pu.get("puLongitude")
        
        # Dropoff
        dropoff_address = ad.get("addressLine1", "")
        dropoff_city = ad.get("city", "")
        dropoff_postal = ad.get("postalCode", "")
        dropoff_country = ad.get("countryCode", "")
        dropoff_lat = do.get("doLatitude")
        dropoff_lng = do.get("doLongitude")
        
        booked_by = trip.get("bookedBy", "")
        status = trip.get("status", "OPEN")
    
    # === Construction payload Waynium ===
    
    date_debut, heure_debut = split_datetime(pickup_time_iso)
    
    # Calcul heure fin (+ 1h par défaut pour transfert)
    try:
        dt_start = datetime.fromisoformat(pickup_time_iso.replace('Z', '+00:00'))
        dt_end = dt_start.replace(hour=dt_start.hour + 1)
        heure_fin = dt_end.strftime("%H:%M")
    except:
        heure_fin = "23:59"
    
    # Construction des lieux (étapes)
    pickup_location = build_location_object(
        name=pickup_name or pickup_city,
        address=pickup_address,
        city=pickup_city,
        postal_code=pickup_postal,
        country_code=pickup_country,
        latitude=pickup_lat,
        longitude=pickup_lng,
        location_type=pickup_loc_type,
        airport_code=pickup_code,
        carey_ref=f"CAREY_PICKUP_{reservation_number}"
    )
    
    dropoff_location = build_location_object(
        name=dropoff_city,
        address=dropoff_address,
        city=dropoff_city,
        postal_code=dropoff_postal,
        country_code=dropoff_country,
        latitude=dropoff_lat,
        longitude=dropoff_lng,
        location_type="ADDRESS",
        carey_ref=f"CAREY_DROPOFF_{reservation_number}"
    )
    
    # Mapping langue passager
    lang_map = {"FR": "2", "EN": "1", "ES": "4", "DE": "3", "IT": "5"}
    lan_id = lang_map.get(passenger_language.upper(), "2")
    
    # Notes chauffeur complètes
    driver_notes_parts = [
        f"Bagages: {bags_count}" if bags_count else "",
        f"Panneau: {pickup_sign}" if pickup_sign else "",
        f"Greeter requis" if greeter else "",
        pickup_instructions,
        pickup_special,
        passenger_notes
    ]
    driver_notes = " | ".join([p for p in driver_notes_parts if p])
    
    # Itinéraire texte
    itinerary = f"{pickup_name or pickup_city} → {dropoff_city}"
    
    # === Payload Waynium final ===
    return {
        "limo": "abllimousines",
        "config": "createMissionComplete",
        "params": {
            "C_Gen_Client": [
                {
                    "CLI_ID": cli_id,
                    "C_Com_Commande": [
                        {
                            "ref": reservation_number,
                            "COM_COT_ID": "2007",  # Type commande (à confirmer avec Waynium)
                            "COM_SCO_ID": "4",     # Statut commande (à confirmer)
                            "COM_DEMANDE": f"Réservation Carey - {booked_by}" if booked_by else "Réservation Carey",
                            "C_Gen_Mission": [
                                {
                                    "ref": reservation_number,
                                    "MIS_REF_MISSION_CLIENT": reservation_number,
                                    "MIS_TSE_ID": map_service_type(service_type),
                                    "MIS_TVE_ID": map_vehicle_type(vehicle_type),
                                    "MIS_DATE_DEBUT": date_debut,
                                    "MIS_HEURE_DEBUT": heure_debut,
                                    "MIS_HEURE_FIN": heure_fin,
                                    "MIS_PAX": str(passenger_count),
                                    "MIS_ITINERAIRE": itinerary,
                                    "MIS_NOTE_CHAUFFEUR": driver_notes,
                                    "C_Com_FraisMission": [
                                        {
                                            "ref": reservation_number,
                                            "FMI_SER_ID": "1",  # Service ID (à mapper)
                                            "FMI_LIBELLE": f"Transfert {pickup_name or pickup_city} - {dropoff_city}",
                                            "FMI_QTE": "1",
                                            "FMI_VENTE_HT": str(float(price_total) * 0.9) if price_total else "0.00",  # HT = 90% du TTC
                                            "FMI_TVA": str(float(price_total) * 0.1) if price_total else "0.00"
                                        }
                                    ],
                                    "C_Gen_EtapePresence": [
                                        {
                                            "EPR_TRI": "0",  # Étape 0 = pickup
                                            "EPR_LIE_ID": pickup_location
                                        },
                                        {
                                            "EPR_TRI": "1",  # Étape 1 = dropoff
                                            "EPR_LIE_ID": dropoff_location
                                        }
                                    ],
                                    "C_Gen_Presence": [
                                        {
                                            "PRS_TRI": "0",
                                            "PRS_PAS_ID": {
                                                "PAS_NOM": passenger_last.upper(),
                                                "PAS_PRENOM": passenger_first.capitalize(),
                                                "PAS_LAN_ID": lan_id,
                                                "PAS_TELEPHONE": passenger_phone,
                                                "PAS_FLAG_SMS": "1" if passenger_phone else "0",
                                                "PAS_INFO_CHAUFFEUR": f"Passager principal - {passenger_count} PAX"
                                            }
                                        }
                                    ]
                                }
                            ],
                            "COM_FAC_ID": {
                                "FAC_CLI_ID": str(cli_id),
                                "FAC_DATE": "0000-00-00",  # Date facture (géré par Waynium)
                                "FAC_NOM": f"{passenger_last.upper()} {passenger_first.capitalize()}",
                                "FAC_ADRESSE": dropoff_address,
                                "FAC_CP": dropoff_postal,
                                "FAC_VILLE": dropoff_city,
                                "FAC_PAY_ID": detect_country_id(dropoff_country),
                                "FAC_ECO_ID": "1"  # Échéance de paiement (à confirmer)
                            }
                        }
                    ]
                }
            ]
        }
    }

def transform_cancellation_to_waynium(carey_payload: dict) -> dict:
    """
    Transforme une annulation Carey vers Waynium
    
    Format Waynium annulation:
    MIS_SMI_ID = 7 (statut mission annulée)
    """
    
    # Détection format
    if "cancelledTrip" in carey_payload:
        # Format legacy
        cancelled = carey_payload.get("cancelledTrip", {})
        ref = cancelled.get("reservationNumber", "")
    elif "status" in carey_payload and carey_payload["status"].upper() in ["CANCELLED", "CANCELED"]:
        # Format v2
        ref = carey_payload.get("reservationNumber") or carey_payload.get("reservationId", "")
    else:
        # Fallback
        trip = carey_payload.get("trip", {})
        ref = trip.get("reservationNumber", "")
    
    return {
        "limo": "abllimousines",
        "config": "updateMissionLight",
        "params": {
            "C_Gen_Mission": [
                {
                    "ref": ref,
                    "MIS_SMI_ID": "7"  # 7 = Annulée dans Waynium
                }
            ]
        }
    }

# Alias pour compatibilité avec main.py existant
def transform_to_waynium(carey_payload: dict) -> dict:
    """Alias principal - détecte auto le type de transformation"""
    
    # Détection annulation
    is_cancellation = (
        "cancelledTrip" in carey_payload or
        (carey_payload.get("status", "").upper() in ["CANCELLED", "CANCELED"]) or
        (carey_payload.get("trip", {}).get("status", "").upper() in ["CANCELLED", "CANCELED"])
    )
    
    if is_cancellation:
        return transform_cancellation_to_waynium(carey_payload)
    
    return transform_carey_v2_to_waynium(carey_payload)

# Compat
transform_payload = transform_to_waynium
