# waynium_mappings.py - Configuration centralisée des mappings Waynium
"""
Ce fichier contient tous les mappings entre les codes Carey et les IDs Waynium.
À mettre à jour selon votre configuration Waynium spécifique.

Pour obtenir les IDs Waynium :
1. Types véhicules : https://abllimousines.way-plan.com/bop3/C_Gen_TypeVehicule/
2. Services : https://abllimousines.way-plan.com/bop3/C_Com_Service/
3. Clients : https://abllimousines.way-plan.com/bop3/C_Gen_Client/
"""

# ===================== TYPES DE VÉHICULES (MIS_TVE_ID) =====================
# Format: "CODE_CAREY": "ID_WAYNIUM"
# Obtenir la liste depuis: https://abllimousines.way-plan.com/bop3/C_Gen_TypeVehicule/

VEHICLE_TYPE_MAPPING = {
    # Berlines / Sedans
    "SEDAN": "1",
    "BERLINE": "1",
    "EXECUTIVE_SEDAN": "1",
    "LUXURY_SEDAN": "1",
    "BUSINESS_SEDAN": "1",
    "STANDARD_SEDAN": "1",
    
    # Vans / Minivans
    "VAN": "2",
    "MINIVAN": "2",
    "EXECUTIVE_VAN": "2",
    "PASSENGER_VAN": "2",
    "SPRINTER": "2",
    
    # SUVs
    "SUV": "3",
    "LUXURY_SUV": "3",
    "EXECUTIVE_SUV": "3",
    "LARGE_SUV": "3",
    
    # Véhicules premium
    "LIMOUSINE": "4",
    "STRETCH_LIMOUSINE": "4",
    "PREMIUM_SEDAN": "4",
    
    # Véhicules spéciaux
    "BUS": "5",
    "COACH": "5",
    "MINIBUS": "5",
    
    # Valeur par défaut si non trouvé
    "DEFAULT": "1"
}

# ===================== SERVICES (FMI_SER_ID) =====================
# Format: "TYPE_SERVICE_CAREY": "ID_SERVICE_WAYNIUM"
# Obtenir la liste depuis: https://abllimousines.way-plan.com/bop3/C_Com_Service/

SERVICE_MAPPING = {
    # Transferts aéroport
    "AIRPORT": "1",
    "AIRPORT_TRANSFER": "1",
    "AIRPORT_PICKUP": "1",
    "AIRPORT_DROPOFF": "1",
    
    # Transferts standards
    "TRANSFER": "2",
    "POINT_TO_POINT": "2",
    "CITY_TO_CITY": "2",
    
    # Mise à disposition / Hourly
    "HOURLY": "3",
    "HOURLY_DISPOSAL": "3",
    "AS_DIRECTED": "3",
    "DISPOSITION": "3",
    
    # Services premium
    "PREMIUM": "4",
    "BUSINESS": "4",
    "FIRST_CLASS": "4",
    "VIP": "4",
    
    # Événements
    "EVENT": "5",
    "WEDDING": "5",
    "CORPORATE_EVENT": "5",
    
    # Valeur par défaut
    "DEFAULT": "1"
}

# ===================== CLIENTS (CLI_ID) =====================
# Format: "ACCOUNT_NAME_CAREY": CLI_ID_WAYNIUM (integer)
# Obtenir la liste depuis: https://abllimousines.way-plan.com/bop3/C_Gen_Client/

CLIENT_MAPPING = {
    # Comptes corporates
    "SP - Carey Belgium": 320,
    "Carey Belgium": 320,
    "CAREY_BELGIUM": 320,
    
    # Autres comptes (exemples à personnaliser)
    "Corporate Account": 321,
    "VIP Client": 322,
    "Travel Agency XYZ": 323,
    "Hotel Partner": 324,
    
    # Compte par défaut pour clients non mappés
    "DEFAULT": 320
}

# ===================== PAYS (PAY_ID) =====================
# Format: "CODE_ISO_PAYS": "ID_PAYS_WAYNIUM"

COUNTRY_MAPPING = {
    "FR": "65",   # France
    "BE": "21",   # Belgique
    "CH": "204",  # Suisse
    "LU": "125",  # Luxembourg
    "GB": "77",   # Royaume-Uni
    "UK": "77",   # UK (alias)
    "DE": "56",   # Allemagne
    "NL": "150",  # Pays-Bas
    "IT": "105",  # Italie
    "ES": "67",   # Espagne
    "US": "223",  # États-Unis
    "CA": "38",   # Canada
    "AE": "1",    # Émirats Arabes Unis
    
    # Valeur par défaut (France)
    "DEFAULT": "65"
}

# ===================== LANGUES PASSAGERS (PAS_LAN_ID) =====================
# Format: "CODE_LANGUE": "ID_LANGUE_WAYNIUM"

LANGUAGE_MAPPING = {
    "FR": "2",   # Français
    "EN": "1",   # Anglais
    "ES": "4",   # Espagnol
    "DE": "3",   # Allemand
    "IT": "5",   # Italien
    "NL": "6",   # Néerlandais
    "PT": "7",   # Portugais
    "RU": "8",   # Russe
    "AR": "9",   # Arabe
    "ZH": "10",  # Chinois
    
    # Valeur par défaut (Français)
    "DEFAULT": "2"
}

# ===================== TYPES DE LIEUX (LIE_TLI_ID) =====================
# Format: "TYPE_LIEU_CAREY": "ID_TYPE_LIEU_WAYNIUM"

LOCATION_TYPE_MAPPING = {
    "AIRPORT": "1",
    "TRANSPORTATIONCENTER": "1",
    "TRANSPORTATION_CENTER": "1",
    
    "ADDRESS": "2",
    "RESIDENCE": "2",
    "OFFICE": "2",
    
    "HOTEL": "3",
    
    "STATION": "4",
    "TRAIN_STATION": "4",
    "RAILWAY_STATION": "4",
    
    "PORT": "5",
    "SEAPORT": "5",
    "HARBOR": "5",
    
    # Valeur par défaut
    "DEFAULT": "2"
}

# ===================== TYPES DE SERVICE MISSION (MIS_TSE_ID) =====================
# Format: "TYPE_SERVICE": "ID_TYPE_SERVICE_WAYNIUM"

MISSION_TYPE_MAPPING = {
    "TRANSFER": "1",
    "POINT_TO_POINT": "1",
    "AIRPORT": "1",
    "ONEWAY": "1",
    "ONE_WAY": "1",
    
    "HOURLY": "2",
    "DISPOSITION": "2",
    "AS_DIRECTED": "2",
    "HOURLY_DISPOSAL": "2",
    
    # Valeur par défaut
    "DEFAULT": "1"
}

# ===================== STATUTS MISSION (MIS_SMI_ID) =====================

MISSION_STATUS_MAPPING = {
    "OPEN": "1",
    "CONFIRMED": "1",
    "PENDING": "1",
    
    "ASSIGNED": "2",
    "DISPATCHED": "2",
    
    "IN_PROGRESS": "3",
    "ONGOING": "3",
    
    "COMPLETED": "4",
    "FINISHED": "4",
    
    "CANCELLED": "7",
    "CANCELED": "7",
    
    # Valeur par défaut
    "DEFAULT": "1"
}

# ===================== FONCTIONS HELPER =====================

def get_vehicle_type_id(carey_code: str, default: str = None) -> str:
    """
    Retourne l'ID Waynium pour un type de véhicule Carey.
    
    Args:
        carey_code: Code véhicule Carey (ex: "EXECUTIVE_SEDAN")
        default: Valeur par défaut si non trouvé (sinon utilise "DEFAULT")
    
    Returns:
        ID Waynium (string)
    
    Example:
        >>> get_vehicle_type_id("EXECUTIVE_SEDAN")
        "1"
        >>> get_vehicle_type_id("unknown_vehicle")
        "1"  # DEFAULT
    """
    if not carey_code:
        return default or VEHICLE_TYPE_MAPPING["DEFAULT"]
    
    key = str(carey_code).upper().strip().replace(" ", "_")
    return VEHICLE_TYPE_MAPPING.get(key, default or VEHICLE_TYPE_MAPPING["DEFAULT"])

def get_service_id(carey_service: str, default: str = None) -> str:
    """
    Retourne l'ID service Waynium pour un type de service Carey.
    
    Args:
        carey_service: Type service Carey (ex: "AIRPORT")
        default: Valeur par défaut si non trouvé
    
    Returns:
        ID service Waynium (string)
    """
    if not carey_service:
        return default or SERVICE_MAPPING["DEFAULT"]
    
    key = str(carey_service).upper().strip().replace(" ", "_")
    return SERVICE_MAPPING.get(key, default or SERVICE_MAPPING["DEFAULT"])

def get_client_id(account_name: str, default: int = None) -> int:
    """
    Retourne l'ID client Waynium pour un compte Carey.
    
    Args:
        account_name: Nom du compte Carey
        default: ID par défaut si non trouvé
    
    Returns:
        CLI_ID Waynium (integer)
    """
    if not account_name:
        return default or CLIENT_MAPPING["DEFAULT"]
    
    # Essai exact match d'abord
    if account_name in CLIENT_MAPPING:
        return CLIENT_MAPPING[account_name]
    
    # Essai avec normalisation
    key = str(account_name).strip().upper().replace(" ", "_")
    for carey_name, cli_id in CLIENT_MAPPING.items():
        if carey_name.upper().replace(" ", "_") == key:
            return cli_id
    
    return default or CLIENT_MAPPING["DEFAULT"]

def get_country_id(country_code: str, default: str = None) -> str:
    """
    Retourne l'ID pays Waynium pour un code ISO pays.
    
    Args:
        country_code: Code ISO pays (ex: "FR", "BE")
        default: Valeur par défaut si non trouvé
    
    Returns:
        PAY_ID Waynium (string)
    """
    if not country_code:
        return default or COUNTRY_MAPPING["DEFAULT"]
    
    key = str(country_code).upper().strip()
    return COUNTRY_MAPPING.get(key, default or COUNTRY_MAPPING["DEFAULT"])

def get_language_id(language_code: str, default: str = None) -> str:
    """
    Retourne l'ID langue Waynium pour un code langue.
    
    Args:
        language_code: Code langue (ex: "FR", "EN")
        default: Valeur par défaut si non trouvé
    
    Returns:
        PAS_LAN_ID Waynium (string)
    """
    if not language_code:
        return default or LANGUAGE_MAPPING["DEFAULT"]
    
    key = str(language_code).upper().strip()
    return LANGUAGE_MAPPING.get(key, default or LANGUAGE_MAPPING["DEFAULT"])

def get_location_type_id(location_type: str, default: str = None) -> str:
    """
    Retourne l'ID type de lieu Waynium.
    
    Args:
        location_type: Type lieu Carey (ex: "AIRPORT", "HOTEL")
        default: Valeur par défaut si non trouvé
    
    Returns:
        LIE_TLI_ID Waynium (string)
    """
    if not location_type:
        return default or LOCATION_TYPE_MAPPING["DEFAULT"]
    
    key = str(location_type).upper().strip().replace(" ", "_")
    return LOCATION_TYPE_MAPPING.get(key, default or LOCATION_TYPE_MAPPING["DEFAULT"])

def get_mission_type_id(service_type: str, default: str = None) -> str:
    """
    Retourne l'ID type de mission Waynium (transfert vs disposition).
    
    Args:
        service_type: Type service Carey
        default: Valeur par défaut si non trouvé
    
    Returns:
        MIS_TSE_ID Waynium (string)
    """
    if not service_type:
        return default or MISSION_TYPE_MAPPING["DEFAULT"]
    
    key = str(service_type).upper().strip().replace(" ", "_")
    return MISSION_TYPE_MAPPING.get(key, default or MISSION_TYPE_MAPPING["DEFAULT"])

def get_mission_status_id(status: str, default: str = None) -> str:
    """
    Retourne l'ID statut mission Waynium.
    
    Args:
        status: Statut Carey (ex: "CONFIRMED", "CANCELLED")
        default: Valeur par défaut si non trouvé
    
    Returns:
        MIS_SMI_ID Waynium (string)
    """
    if not status:
        return default or MISSION_STATUS_MAPPING["DEFAULT"]
    
    key = str(status).upper().strip().replace(" ", "_")
    return MISSION_STATUS_MAPPING.get(key, default or MISSION_STATUS_MAPPING["DEFAULT"])

# ===================== VALIDATION =====================

def validate_mappings():
    """
    Valide que tous les mappings sont cohérents.
    À exécuter lors du démarrage de l'API.
    """
    errors = []
    
    # Vérifier que toutes les valeurs sont des strings ou ints
    for name, mapping in [
        ("VEHICLE_TYPE_MAPPING", VEHICLE_TYPE_MAPPING),
        ("SERVICE_MAPPING", SERVICE_MAPPING),
        ("COUNTRY_MAPPING", COUNTRY_MAPPING),
        ("LANGUAGE_MAPPING", LANGUAGE_MAPPING),
        ("LOCATION_TYPE_MAPPING", LOCATION_TYPE_MAPPING),
        ("MISSION_TYPE_MAPPING", MISSION_TYPE_MAPPING),
        ("MISSION_STATUS_MAPPING", MISSION_STATUS_MAPPING)
    ]:
        for key, value in mapping.items():
            if not isinstance(value, (str, int)):
                errors.append(f"{name}[{key}] = {value} (type invalide: {type(value)})")
    
    # Vérifier CLIENT_MAPPING
    for key, value in CLIENT_MAPPING.items():
        if not isinstance(value, int):
            errors.append(f"CLIENT_MAPPING[{key}] = {value} (doit être int)")
    
    if errors:
        raise ValueError(f"Erreurs dans les mappings:\n" + "\n".join(errors))
    
    return True

# Validation au chargement du module
try:
    validate_mappings()
except ValueError as e:
    print(f"⚠️  ATTENTION: {e}")
