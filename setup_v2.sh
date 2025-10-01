#!/bin/bash
# setup_v2.sh - Installation automatique Carey→Waynium API v2

set -e  # Exit on error

echo "🚀 Installation Carey→Waynium API v2.0.0"
echo "========================================"

# Vérifications préalables
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Ce script doit être exécuté en root"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 non trouvé"
    exit 1
fi

# Variables
INSTALL_DIR="/opt/carey-waynium-api"
BACKUP_DIR="/opt/carey-waynium-api.backup.$(date +%Y%m%d_%H%M%S)"
SERVICE_NAME="carey_api.service"

# Backup de l'existant
if [ -d "$INSTALL_DIR" ]; then
    echo "📦 Backup de l'installation existante..."
    cp -r "$INSTALL_DIR" "$BACKUP_DIR"
    echo "✅ Backup créé: $BACKUP_DIR"
    
    # Arrêter le service
    if systemctl is-active --quiet $SERVICE_NAME; then
        echo "⏸️  Arrêt du service existant..."
        systemctl stop $SERVICE_NAME
    fi
fi

# Création du répertoire
echo "📁 Création du répertoire d'installation..."
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Installation des dépendances système
echo "📦 Installation des dépendances système..."
apt update -qq
apt install -y python3-pip python3-venv curl jq

# Création environnement virtuel
echo "🐍 Création de l'environnement virtuel Python..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# Installation des packages Python
echo "📚 Installation des packages Python..."
pip install --quiet --upgrade pip
pip install --quiet flask flask-cors requests pyjwt python-dotenv gunicorn pytest

# Téléchargement des fichiers depuis GitHub (optionnel)
# Décommenter si vous hébergez les fichiers sur GitHub
# echo "⬇️  Téléchargement des fichiers depuis GitHub..."
# curl -sL https://raw.githubusercontent.com/votre-repo/main/transform.py -o transform.py
# curl -sL https://raw.githubusercontent.com/votre-repo/main/main.py -o main.py

# Création du fichier .env s'il n'existe pas
if [ ! -f ".env" ]; then
    echo "⚙️  Création du fichier .env..."
    cat > .env << 'EOF'
# Configuration Waynium
WAYNIUM_API_URL=https://stage-gdsapi.waynium.net/api-externe/set-ressource
WAYNIUM_API_KEY=abllimousines
WAYNIUM_API_SECRET=be5F47w72eGxwWe8EAZe9Y4vP38g2rRG

# Webhook authentication
WEBHOOK_API_KEYS=1

# App settings
PORT=5000
DEBUG=false
VERSION=2.0.0
REQUEST_TIMEOUT=15
MAX_RETRIES=3
ENABLE_QUEUE=true
EOF
    chmod 600 .env
    echo "✅ Fichier .env créé (à personnaliser!)"
else
    echo "ℹ️  Fichier .env existant conservé"
fi

# Création du service systemd
echo "🔧 Configuration du service systemd..."
cat > /etc/systemd/system/$SERVICE_NAME << EOF
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
EOF

# Reload systemd
systemctl daemon-reload

# Test de syntaxe Python
echo "🧪 Vérification des fichiers Python..."
if [ -f "transform.py" ] && [ -f "main.py" ]; then
    python3 -m py_compile transform.py
    python3 -m py_compile main.py
    echo "✅ Syntaxe Python valide"
else
    echo "⚠️  Fichiers transform.py ou main.py manquants!"
    echo "    Vous devez les créer manuellement dans $INSTALL_DIR"
fi

# Création du dossier de logs
mkdir -p /var/log/carey-waynium-api

# Configuration logrotate
echo "📋 Configuration de la rotation des logs..."
cat > /etc/logrotate.d/carey-api << 'EOF'
/var/log/carey-waynium-api/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0640 root root
    sharedscripts
}
EOF

echo ""
echo "✅ Installation terminée!"
echo ""
echo "📝 Prochaines étapes:"
echo "   1. Éditer $INSTALL_DIR/.env avec vos credentials"
echo "   2. Vérifier que transform.py et main.py sont présents"
echo "   3. Démarrer le service:"
echo "      systemctl enable $SERVICE_NAME"
echo "      systemctl start $SERVICE_NAME"
echo "      systemctl status $SERVICE_NAME"
echo ""
echo "   4. Tester l'API:"
echo "      curl http://localhost:5000/healthz"
echo "      curl http://localhost:5000/version"
echo ""
echo "📊 Logs en temps réel:"
echo "      journalctl -u $SERVICE_NAME -f"
echo ""
echo "🔙 En cas de problème, rollback disponible:"
echo "      $BACKUP_DIR"
echo ""
