# test_integration.py - Suite complète de tests
import json
import pytest
from transform import (
    transform_to_waynium,
    transform_carey_v2_to_waynium,
    transform_cancellation_to_waynium,
    split_datetime,
    map_vehicle_type,
    map_service_type
)

# ======================== FIXTURES ========================================
@pytest.fixture
def carey_v2_payload():
    """Payload Carey format v2"""
    return {
        "reservationId": "TEST-ABC-123",
        "reservationNumber": "WA1234567-7",
        "createdBy": "carey@central.com",
        "reservationSource": "APIv2",
        "serviceProvider": "Carey Belgium",
        "accountName": "SP - Carey Belgium",
        "passenger": {
            "firstName": "Jean",
            "lastName": "Dupont",
            "email": "jean.dupont@example.com",
            "mobile": "+33612345678",
            "language": "FR",
            "serviceLevel": "First Class",
            "passengerCount": 2
        },
        "pickup": {
            "time": "2025-10-15T14:30:00Z",
            "locationType": "Airport",
            "locationInstructions": "Terminal 2E, Porte 10",
            "specialInstructions": "Client VIP",
            "latitude": 49.00969,
            "longitude": 2.54792,
            "transportationCenterDetails": {
                "transportationCenterName": "Paris Charles De Gaulle",
                "transportationCenterCode": "CDG",
                "carrierName": "Air France",
                "carrierCode": "AF",
                "carrierNumber": "AF1234",
                "source": "ORY",
                "domestic": False,
                "privateAviation": False
            },
            "city": "Roissy-en-France",
            "postalCode": "95700",
            "country": "FR"
        },
        "dropoff": {
            "address": "1 Avenue des Champs-Élysées",
            "city": "Paris",
            "postalCode": "75008",
            "country": "FR",
            "latitude": 48.8708,
            "longitude": 2.3078
        },
        "service": {
            "type": "Airport",
            "tripType": "OneWay",
            "vehicleType": "Executive Sedan",
            "bagsCount": 3,
            "pickupSign": "Mr DUPONT",
            "greeterRequested": True
        },
        "payment": {
            "method": "Invoice",
            "priceEstimate": {
                "total": 150.00,
                "currency": "EUR",
                "taxIncluded": True
            }
        },
        "bookedBy": "Agent Smith",
        "status": "Confirmed",
        "notes": "Client VIP - Prévoir eau et journaux"
    }

@pytest.fixture
def carey_legacy_payload():
    """Payload Carey format legacy (trip.*)"""
    return {
        "publishTime": "2025-10-15T12:00:00Z",
        "trip": {
            "reservationNumber": "LEGACY-456",
            "serviceProvider": "Carey Belgium",
            "accountName": "Corporate Account",
            "status": "OPEN",
            "tripType": "POINT_TO_POINT",
            "serviceType": "PREMIUM",
            "vehicleType": "EXECUTIVE_SEDAN",
            "bagsCount": 2,
            "passengerDetails": {
                "firstName": "Marie",
                "lastName": "Martin",
                "emailAddress": "marie.martin@example.com",
                "mobileNumber": "+32475123456",
                "serviceLevel": "SERVICE_PLUS",
                "passengerCount": 1
            },
            "pickUpDetails": {
                "pickUpTime": "2025-10-15T16:00:00Z",
                "locationType": "AIRPORT",
                "puLatitude": 50.9010789,
                "puLongitude": 4.4844472,
                "locationInstructions": "Arrivals Hall",
                "transportationCenterDetails": {
                    "transportationCenterName": "Brussels Airport",
                    "transportationCenterCode": "BRU",
                    "carrierName": "Brussels Airlines",
                    "carrierCode": "SN",
                    "carrierNumber": "SN2345"
                }
            },
            "dropOffDetails": {
                "locationType": "ADDRESS",
                "addressDetails": {
                    "name": "European Commission",
                    "addressLine1": "Rue de la Loi 200",
                    "city": "Brussels",
                    "postalCode": "1000",
                    "countryCode": "BE",
                    "country": "Belgium"
                },
                "doLatitude": 50.8429541,
                "doLongitude": 4.3810627
            },
            "bookedBy": "Travel Agency XYZ"
        }
    }

@pytest.fixture
def cancellation_payload():
    """Payload d'annulation"""
    return {
        "cancelledTrip": {
            "reservationNumber": "CANCEL-789",
            "serviceProvider": "Carey Belgium",
            "cancellationNumber": "CXL-001",
            "cancellationTime": "2025-10-15T10:00:00Z"
        }
    }

# ======================== TESTS UNITAIRES =================================
def test_split_datetime():
    """Test parsing datetime ISO -> (date, heure)"""
    date, heure = split_datetime("2025-10-15T14:30:00Z")
    assert date == "2025-10-15"
    assert heure == "14:30"
    
    # Edge cases
    date, heure = split_datetime("")
    assert date == "0000-00-00"
    assert heure == "00:00"
    
    date, heure = split_datetime("invalid")
    assert date == "0000-00-00"

def test_map_vehicle_type():
    """Test mapping types de véhicules"""
    assert map_vehicle_type("EXECUTIVE_SEDAN") == "1"
    assert map_vehicle_type("Berline") == "1"
    assert map_vehicle_type("VAN") == "2"
    assert map_vehicle_type("SUV") == "3"
    assert map_vehicle_type("unknown") == "1"  # default

def test_map_service_type():
    """Test mapping types de service"""
    assert map_service_type("AIRPORT") == "1"
    assert map_service_type("HOURLY") == "2"
    assert map_service_type("anything") == "1"  # default = transfert

# ======================== TESTS INTEGRATION ===============================
def test_transform_v2_basic(carey_v2_payload):
    """Test transformation v2 -> Waynium structure complète"""
    result = transform_to_waynium(carey_v2_payload)
    
    # Vérification structure globale
    assert result["limo"] == "abllimousines"
    assert result["config"] == "createMissionComplete"
    assert "params" in result
    assert "C_Gen_Client" in result["params"]
    
    client = result["params"]["C_Gen_Client"][0]
    assert client["CLI_ID"] == 320
    
    commande = client["C_Com_Commande"][0]
    assert commande["ref"] == "WA1234567-7"
    
    mission = commande["C_Gen_Mission"][0]
    assert mission["MIS_REF_MISSION_CLIENT"] == "WA1234567-7"
    assert mission["MIS_DATE_DEBUT"] == "2025-10-15"
    assert mission["MIS_HEURE_DEBUT"] == "14:30"
    assert mission["MIS_PAX"] == "2"
    assert mission["MIS_TVE_ID"] == "1"  # Executive Sedan
    assert mission["MIS_TSE_ID"] == "1"  # Transfert

def test_transform_v2_passenger(carey_v2_payload):
    """Test données passager"""
    result = transform_to_waynium(carey_v2_payload)
    
    mission = result["params"]["C_Gen_Client"][0]["C_Com_Commande"][0]["C_Gen_Mission"][0]
    passenger = mission["C_Gen_Presence"][0]["PRS_PAS_ID"]
    
    assert passenger["PAS_NOM"] == "DUPONT"
    assert passenger["PAS_PRENOM"] == "Jean"
    assert passenger["PAS_TELEPHONE"] == "+33612345678"
    assert passenger["PAS_LAN_ID"] == "2"  # FR
    assert passenger["PAS_FLAG_SMS"] == "1"

def test_transform_v2_locations(carey_v2_payload):
    """Test lieux (pickup/dropoff)"""
    result = transform_to_waynium(carey_v2_payload)
    
    mission = result["params"]["C_Gen_Client"][0]["C_Com_Commande"][0]["C_Gen_Mission"][0]
    etapes = mission["C_Gen_EtapePresence"]
    
    # Pickup (étape 0)
    pickup = etapes[0]["EPR_LIE_ID"]
    assert pickup["LIE_TLI_ID"] == "1"  # Airport
    assert "CDG" in pickup["LIE_LIBELLE"] or "Paris" in pickup["LIE_LIBELLE"]
    assert pickup["LIE_PAY_ID"] == "65"  # France
    assert pickup["LIE_LAT"] == "49.00969"
    assert "CAREY_PICKUP" in pickup["LIE_REF_EXTERNE"]
    
    # Dropoff (étape 1)
    dropoff = etapes[1]["EPR_LIE_ID"]
    assert dropoff["LIE_TLI_ID"] == "2"  # Address
    assert dropoff["LIE_VILLE"] == "Paris"
    assert dropoff["LIE_CP"] == "75008"
    assert "CAREY_DROPOFF" in dropoff["LIE_REF_EXTERNE"]

def test_transform_v2_pricing(carey_v2_payload):
    """Test tarification"""
    result = transform_to_waynium(carey_v2_payload)
    
    mission = result["params"]["C_Gen_Client"][0]["C_Com_Commande"][0]["C_Gen_Mission"][0]
    frais = mission["C_Com_FraisMission"][0]
    
    assert frais["FMI_QTE"] == "1"
    assert float(frais["FMI_VENTE_HT"]) == 135.0  # 150 * 0.9
    assert float(frais["FMI_TVA"]) == 15.0  # 150 * 0.1
    assert "Paris" in frais["FMI_LIBELLE"]

def test_transform_v2_driver_notes(carey_v2_payload):
    """Test notes chauffeur"""
    result = transform_to_waynium(carey_v2_payload)
    
    mission = result["params"]["C_Gen_Client"][0]["C_Com_Commande"][0]["C_Gen_Mission"][0]
    notes = mission["MIS_NOTE_CHAUFFEUR"]
    
    assert "Bagages: 3" in notes
    assert "Panneau: Mr DUPONT" in notes
    assert "Greeter requis" in notes
    assert "Terminal 2E" in notes
    assert "Client VIP" in notes

def test_transform_legacy(carey_legacy_payload):
    """Test transformation legacy (trip.*) -> Waynium"""
    result = transform_to_waynium(carey_legacy_payload)
    
    assert result["limo"] == "abllimousines"
    
    commande = result["params"]["C_Gen_Client"][0]["C_Com_Commande"][0]
    assert commande["ref"] == "LEGACY-456"
    
    mission = commande["C_Gen_Mission"][0]
    assert mission["MIS_DATE_DEBUT"] == "2025-10-15"
    assert mission["MIS_HEURE_DEBUT"] == "16:00"
    
    passenger = mission["C_Gen_Presence"][0]["PRS_PAS_ID"]
    assert passenger["PAS_NOM"] == "MARTIN"
    assert passenger["PAS_PRENOM"] == "Marie"

def test_transform_cancellation(cancellation_payload):
    """Test transformation annulation"""
    result = transform_to_waynium(cancellation_payload)
    
    assert result["limo"] == "abllimousines"
    assert result["config"] == "updateMissionLight"
    
    mission = result["params"]["C_Gen_Mission"][0]
    assert mission["ref"] == "CANCEL-789"
    assert mission["MIS_SMI_ID"] == "7"  # Statut annulée

def test_transform_cancellation_from_status():
    """Test détection annulation depuis status"""
    payload = {
        "reservationNumber": "TEST-999",
        "status": "CANCELLED"
    }
    
    result = transform_to_waynium(payload)
    
    assert result["config"] == "updateMissionLight"
    assert result["params"]["C_Gen_Mission"][0]["MIS_SMI_ID"] == "7"

# ======================== TESTS EDGE CASES ================================
def test_transform_missing_optional_fields():
    """Test avec champs optionnels manquants"""
    minimal = {
        "reservationNumber": "MIN-001",
        "passenger": {
            "firstName": "Test",
            "lastName": "User",
            "mobile": "+33600000000"
        },
        "pickup": {
            "time": "2025-10-15T10:00:00Z",
            "city": "Paris",
            "country": "FR"
        },
        "dropoff": {
            "city": "Lyon",
            "country": "FR"
        }
    }
    
    result = transform_to_waynium(minimal)
    
    # Ne doit pas crasher
    assert result["limo"] == "abllimousines"
    assert result["params"]["C_Gen_Client"][0]["C_Com_Commande"][0]["ref"] == "MIN-001"

def test_transform_phone_formats():
    """Test nettoyage formats téléphone"""
    from transform import clean_phone
    
    assert clean_phone("+33 6 12 34 56 78") == "+33612345678"
    assert clean_phone("0612345678") == "+0612345678"
    assert clean_phone("+33-6-12-34-56-78") == "+33612345678"
    assert clean_phone("") == ""
    assert clean_phone(None) == ""

def test_transform_invalid_datetime():
    """Test avec datetime invalide"""
    payload = {
        "reservationNumber": "INV-DT",
        "passenger": {"firstName": "Test", "lastName": "User"},
        "pickup": {
            "time": "invalid-datetime",
            "city": "Paris",
            "country": "FR"
        },
        "dropoff": {"city": "Lyon", "country": "FR"}
    }
    
    result = transform_to_waynium(payload)
    
    mission = result["params"]["C_Gen_Client"][0]["C_Com_Commande"][0]["C_Gen_Mission"][0]
    assert mission["MIS_DATE_DEBUT"] == "0000-00-00"
    assert mission["MIS_HEURE_DEBUT"] == "00:00"

# ======================== EXECUTION =======================================
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
