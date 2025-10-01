#!/bin/bash
# deploy_v2_complete.sh - Déploiement complet v2 avec mappings

set -e
echo "🚀 Déploiement Carey→Waynium API v2 avec Mappings"
echo "=================================================="

# Vérifications
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Doit être exécuté en root"
    exit 1
fi

INSTALL_DIR="/opt/carey-waynium-api"
BACKUP_DIR="/opt/carey-waynium-api.backup.$(date +%Y%m%d_%H%M%S)"

# Backup
if [ -d "$INSTALL_DIR" ]; then
    echo "📦 Backup en cours..."
    cp -r "$INSTALL_DIR" "$BACKUP_DIR"
    systemctl stop carey_api.service 2>/dev/null || true
fi

# Création dossier
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Installation dépendances
echo "📦 Installation dépendances..."
apt update -qq
apt install -y python3-pip python3-venv curl jq

# Environnement virtuel
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# Packages Python
pip install --quiet --upgrade pip
pip install --quiet flask flask-cors requests pyjwt python-dotenv gunicorn

# === CRÉATION DES FICHIERS ===

echo "📝 Création de waynium_mappings.py..."
cat > waynium_mappings.py << 'EOFMAPPINGS'
# waynium_mappings.py - À personnaliser selon votre config Waynium
# URLs de référence:
# - Véhicules: https://abllimousines.way-plan.com/bop3/C_Gen_TypeVehicule/
# - Services: https://abllimousines.way-plan.com/bop3/C_Com_Service/
# - Clients: https://abllimousines.way-plan.com/bop3/C_Gen_Client/

VEHICLE_TYPE_MAPPING = {
    "SEDAN": "1", "BERLINE": "1", "EXECUTIVE_SEDAN": "1",
    "VAN": "2", "MINIVAN": "2", "EXECUTIVE_VAN": "2",
    "SUV": "3", "LUXURY_SUV": "3",
    "LIMOUSINE": "4", "PREMIUM_SEDAN": "4",
    "BUS": "5", "COACH": "5",
    "DEFAULT": "1"
}

SERVICE_MAPPING = {
    "AIRPORT": "1", "AIRPORT_TRANSFER": "1",
    "TRANSFER": "2", "POINT_TO_POINT": "2",
    "HOURLY": "3", "DISPOSITION": "3",
    "PREMIUM": "4", "VIP": "4",
    "DEFAULT": "1"
}

CLIENT_MAPPING = {
    "SP - Carey Belgium": 320,
    "Carey Belgium": 320,
    "CAREY_BELGIUM": 320,
    "DEFAULT": 320
}

COUNTRY_MAPPING = {
    "FR": "65", "BE": "21", "CH": "204", "LU": "125",
    "GB": "77", "UK": "77", "DE": "56", "NL": "150",
    "IT": "105", "ES": "67", "US": "223", "CA": "38",
    "DEFAULT": "65"
}

LANGUAGE_MAPPING = {
    "FR": "2", "EN": "1", "ES": "4", "DE": "3",
    "IT": "5", "NL": "6", "DEFAULT": "2"
}

LOCATION_TYPE_MAPPING = {
    "AIRPORT": "1", "TRANSPORTATIONCENTER": "1",
    "ADDRESS": "2", "RESIDENCE": "2", "OFFICE": "2",
    "HOTEL": "3", "STATION": "4", "PORT": "5",
    "DEFAULT": "2"
}

MISSION_TYPE_MAPPING = {
    "TRANSFER": "1", "POINT_TO_POINT": "1", "AIRPORT": "1",
    "HOURLY": "2", "DISPOSITION": "2",
    "DEFAULT": "1"
}

MISSION_STATUS_MAPPING = {
    "OPEN": "1", "CONFIRMED": "1",
    "ASSIGNED": "2", "IN_PROGRESS": "3",
    "COMPLETED": "4", "CANCELLED": "7",
    "DEFAULT": "1"
}

def get_vehicle_type_id(carey_code: str, default: str = None) -> str:
    if not carey_code:
        return default or VEHICLE_TYPE_MAPPING["DEFAULT"]
    key = str(carey_code).upper().strip().replace(" ", "_")
    return VEHICLE_TYPE_MAPPING.get(key, default or VEHICLE_TYPE_MAPPING["DEFAULT"])

def get_service_id(carey_service: str, default: str = None) -> str:
    if not carey_service:
        return default or SERVICE_MAPPING["DEFAULT"]
    key = str(carey_service).upper().strip().replace(" ", "_")
    return SERVICE_MAPPING.get(key, default or SERVICE_MAPPING["DEFAULT"])

def get_client_id(account_name: str, default: int = None) -> int:
    if not account_name:
        return default or CLIENT_MAPPING["DEFAULT"]
    if account_name in CLIENT_MAPPING:
        return CLIENT_MAPPING[account_name]
    key = str(account_name).strip().upper().replace(" ", "_")
    for carey_name, cli_id in CLIENT_MAPPING.items():
        if carey_name.upper().replace(" ", "_") == key:
            return cli_id
    return default or CLIENT_MAPPING["DEFAULT"]

def get_country_id(country_code: str, default: str = None) -> str:
    if not country_code:
        return default or COUNTRY_MAPPING["DEFAULT"]
    key = str(country_code).upper().strip()
    return COUNTRY_MAPPING.get(key, default or COUNTRY_MAPPING["DEFAULT"])

def get_language_id(language_code: str, default: str = None) -> str:
    if not language_code:
        return default or LANGUAGE_MAPPING["DEFAULT"]
    key = str(language_code).upper().strip()
    return LANGUAGE_MAPPING.get(key, default or LANGUAGE_MAPPING["DEFAULT"])

def get_location_type_id(location_type: str, default: str = None) -> str:
    if not location_type:
        return default or LOCATION_TYPE_MAPPING["DEFAULT"]
    key = str(location_type).upper().strip().replace(" ", "_")
    return LOCATION_TYPE_MAPPING.get(key, default or LOCATION_TYPE_MAPPING["DEFAULT"])

def get_mission_type_id(service_type: str, default: str = None) -> str:
    if not service_type:
        return default or MISSION_TYPE_MAPPING["DEFAULT"]
    key = str(service_type).upper().strip().replace(" ", "_")
    return MISSION_TYPE_MAPPING.get(key, default or MISSION_TYPE_MAPPING["DEFAULT"])

def get_mission_status_id(status: str, default: str = None) -> str:
    if not status:
        return default or MISSION_STATUS_MAPPING["DEFAULT"]
    key = str(status).upper().strip().replace(" ", "_")
    return MISSION_STATUS_MAPPING.get(key, default or MISSION_STATUS_MAPPING["DEFAULT"])

def validate_mappings():
    errors = []
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
                errors.append(f"{name}[{key}] type invalide")
    for key, value in CLIENT_MAPPING.items():
        if not isinstance(value, int):
            errors.append(f"CLIENT_MAPPING[{key}] doit être int")
    if errors:
        raise ValueError("Erreurs mappings: " + ", ".join(errors))
    return True

try:
    validate_mappings()
    print("✅ Mappings validés")
except ValueError as e:
    print(f"⚠️ {e}")
EOFMAPPINGS

echo "✅ waynium_mappings.py créé"

# Vérification syntaxe
echo "🧪 Validation des mappings..."
python3 -c "from waynium_mappings import validate_mappings; validate_mappings()" || {
    echo "❌ Erreur dans waynium_mappings.py"
    exit 1
}

# Configuration .env
if [ ! -f ".env" ]; then
    echo "⚙️ Création .env..."
    cat > .env << 'EOFENV'
WAYNIUM_API_URL=https://stage-gdsapi.waynium.net/api-externe/set-ressource
WAYNIUM_API_KEY=abllimousines
WAYNIUM_API_SECRET=be5F47w72eGxwWe8EAZe9Y4vP38g2rRG
WEBHOOK_API_KEYS=1
PORT=5000
DEBUG=false
VERSION=2.0.0
REQUEST_TIMEOUT=15
MAX_RETRIES=3
ENABLE_QUEUE=true
EOFENV
    chmod 600 .env
fi

# Service systemd
echo "🔧 Configuration systemd..."
cat > /etc/systemd/system/carey_api.service << EOFSERVICE
[Unit]
Description=Carey to Waynium API v2
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin"
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOFSERVICE

systemctl daemon-reload

# Logs
mkdir -p /var/log/carey-waynium-api

# Test final
echo ""
echo "🧪 Tests de validation..."

# Test imports
python3 << 'EOFTEST'
try:
    from waynium_mappings import (
        get_vehicle_type_id,
        get_service_id,
        get_client_id,
        validate_mappings
    )
    validate_mappings()
    
    # Tests basiques
    assert get_vehicle_type_id("SEDAN") == "1"
    assert get_service_id("AIRPORT") == "1"
    assert get_client_id("Carey Belgium") == 320
    
    print("✅ Tous les tests passent")
except Exception as e:
    print(f"❌ Test échoué: {e}")
    exit(1)
EOFTEST

echo ""
echo "✅ Déploiement terminé!"
echo ""
echo "📝 Prochaines étapes:"
echo ""
echo "1. ⚙️  PERSONNALISER LES MAPPINGS:"
echo "   nano $INSTALL_DIR/waynium_mappings.py"
echo ""
echo "   Obtenir les IDs réels depuis Waynium:"
echo "   - Véhicules: https://abllimousines.way-plan.com/bop3/C_Gen_TypeVehicule/"
echo "   - Services: https://abllimousines.way-plan.com/bop3/C_Com_Service/"
echo "   - Clients: https://abllimousines.way-plan.com/bop3/C_Gen_Client/"
echo ""
echo "2. 🔐 VÉRIFIER .env avec vos credentials:"
echo "   nano $INSTALL_DIR/.env"
echo ""
echo "3. 📤 UPLOADER transform.py et main.py:"
echo "   (Utilisez les fichiers artifacts fournis précédemment)"
echo "   scp transform.py root@46.255.164.90:$INSTALL_DIR/"
echo "   scp main.py root@46.255.164.90:$INSTALL_DIR/"
echo ""
echo "4. 🚀 DÉMARRER LE SERVICE:"
echo "   systemctl enable carey_api.service"
echo "   systemctl start carey_api.service"
echo "   systemctl status carey_api.service"
echo ""
echo "5. ✅ TESTER:"
echo "   curl http://localhost:5000/healthz"
echo "   curl http://localhost:5000/version"
echo ""
echo "📊 Logs:"
echo "   journalctl -u carey_api.service -f"
echo ""
echo "🔙 Rollback disponible:"
echo "   $BACKUP_DIR"
echo ""
