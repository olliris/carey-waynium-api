# Carey → Waynium API v2.0 🚗

API Flask pour transformer et transférer automatiquement les réservations Carey vers Waynium.

---

## 🎯 Fonctionnalités

- ✅ **Transformation automatique** Carey → Format Waynium officiel
- ✅ **Support multi-formats** : Carey v2 (pickup/dropoff) + Legacy (trip.*)
- ✅ **Gestion annulations** : Détection auto + envoi `updateMissionLight`
- ✅ **Mappings configurables** : Véhicules, services, clients centralisés
- ✅ **Queue asynchrone** : Réponse immédiate 202, traitement en background
- ✅ **Retry automatique** : 3 tentatives sur erreurs Waynium
- ✅ **Authentication JWT** : Token HS256 généré automatiquement
- ✅ **Logs structurés** : JSON avec transaction_id
- ✅ **Health checks** : /healthz, /readyz, /stats
- ✅ **Tests unitaires** : Suite pytest complète

---

## 📁 Structure du Projet

```
/opt/carey-waynium-api/
├── main.py                  # API Flask principale
├── transform.py             # Transformation Carey→Waynium
├── waynium_mappings.py      # Configuration mappings (véhicules, services, etc.)
├── .env                     # Configuration (secrets)
├── venv/                    # Environnement Python
├── test_integration.py      # Tests (optionnel)
└── requirements.txt         # Dépendances Python
```

---

## 🚀 Installation Rapide

### Option 1 : Script Automatique

```bash
# Télécharger et exécuter le script
wget https://votre-serveur.com/deploy_v2_complete.sh
chmod +x deploy_v2_complete.sh
sudo ./deploy_v2_complete.sh
```

### Option 2 : Installation Manuelle

```bash
# 1. Connexion VPS
ssh root@46.255.164.90

# 2. Créer dossier
mkdir -p /opt/carey-waynium-api
cd /opt/carey-waynium-api

# 3. Environnement virtuel
python3 -m venv venv
source venv/bin/activate

# 4. Installer dépendances
pip install flask flask-cors requests pyjwt python-dotenv

# 5. Uploader les fichiers
# - main.py
# - transform.py
# - waynium_mappings.py
# - .env

# 6. Configurer systemd
sudo cp carey_api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable carey_api.service
sudo systemctl start carey_api.service
```

---

## ⚙️ Configuration

### 1. Fichier `.env`

```bash
# Waynium
WAYNIUM_API_URL=https://stage-gdsapi.waynium.net/api-externe/set-ressource
WAYNIUM_API_KEY=abllimousines
WAYNIUM_API_SECRET=be5F47w72eGxwWe8EAZe9Y4vP38g2rRG

# Webhook
WEBHOOK_API_KEYS=1,votre_cle_prod

# App
PORT=5000
DEBUG=false
ENABLE_QUEUE=true
MAX_RETRIES=3
REQUEST_TIMEOUT=15
```

### 2. Mappings Waynium

Éditez `waynium_mappings.py` pour personnaliser :

```python
# Exemple : Ajouter un nouveau véhicule
VEHICLE_TYPE_MAPPING = {
    # ... mappings existants ...
    "TESLA_MODEL_S": "8",  # ← Votre ID Waynium
    "DEFAULT": "1"
}
```

**Comment obtenir les IDs Waynium :**

1. Connectez-vous à votre interface Waynium
2. Accédez aux URLs :
   - Véhicules : `https://abllimousines.way-plan.com/bop3/C_Gen_TypeVehicule/`
   - Services : `https://abllimousines.way-plan.com/bop3/C_Com_Service/`
   - Clients : `https://abllimousines.way-plan.com/bop3/C_Gen_Client/`
3. Notez les IDs et mettez à jour les dictionnaires

📖 **Guide complet** : Voir `MAPPING_GUIDE.md`

---

## 🧪 Tests

### Health Checks

```bash
# Santé basique
curl http://localhost:5000/healthz

# Readiness avec config
curl http://localhost:5000/readyz

# Statistiques
curl http://localhost:5000/stats

# Version
curl http://localhost:5000/version
```

### Test Webhook

```bash
# Payload de test
cat > test.json << 'EOF'
{
  "reservationNumber": "TEST-001",
  "passenger": {
    "firstName": "Jean",
    "lastName": "Dupont",
    "mobile": "+33612345678"
  },
  "pickup": {
    "time": "2025-12-01T10:00:00Z",
    "city": "Paris",
    "country": "FR"
  },
  "dropoff": {
    "city": "Lyon",
    "country": "FR"
  },
  "service": {
    "vehicleType": "Sedan"
  }
}
EOF

# Envoyer
curl -X POST http://localhost:5000/carey/webhook \
  -H "Content-Type: application/json" \
  -H "X-API-Key: 1" \
  -d @test.json
```

### Tests Unitaires

```bash
cd /opt/carey-waynium-api
source venv/bin/activate
pytest test_integration.py -v
```

---

## 📊 Monitoring

### Logs en Temps Réel

```bash
# Suivre les logs
journalctl -u carey_api.service -f

# Dernières 100 lignes
journalctl -u carey_api.service -n 100 --no-pager

# Filtrer par niveau
journalctl -u carey_api.service -p err
```

### Métriques

```bash
# Stats JSON
curl http://localhost:5000/stats | jq

# Exemple réponse:
{
  "stats": {
    "received": 1250,
    "success": 1235,
    "failed": 15,
    "queued": 2
  },
  "queue_size": 2,
  "queue_enabled": true
}
```

---

## 🔧 Opérations Courantes

### Redémarrer le Service

```bash
sudo systemctl restart carey_api.service
sudo systemctl status carey_api.service
```

### Ajouter un Nouveau Mapping

```bash
# 1. Éditer le fichier
nano /opt/carey-waynium-api/waynium_mappings.py

# 2. Ajouter votre mapping
VEHICLE_TYPE_MAPPING = {
    # ...
    "NOUVEAU_VEHICULE": "9",  # ← ID Waynium
}

# 3. Tester
python3 -c "from waynium_mappings import get_vehicle_type_id; print(get_vehicle_type_id('NOUVEAU_VEHICULE'))"

# 4. Redémarrer
sudo systemctl restart carey_api.service
```

### Changer l'URL Waynium (Staging → Prod)

```bash
# Éditer .env
nano /opt/carey-waynium-api/.env

# Modifier la ligne:
WAYNIUM_API_URL=https://gdsapi.waynium.net/api-externe/set-ressource

# Redémarrer
sudo systemctl restart carey_api.service
```

---

## 🐛 Dépannage

### Problème : Service ne démarre pas

```bash
# Vérifier les logs d'erreur
journalctl -u carey_api.service -n 50 -p err

# Tester manuellement
cd /opt/carey-waynium-api
source venv/bin/activate
python3 main.py
```

### Problème : Waynium rejette les requêtes

```bash
# Vérifier le JWT
python3 << 'EOF'
import jwt
from datetime import datetime

payload = {
    "iss": "abllimousines",
    "iat": int(datetime.utcnow().timestamp())
}
token = jwt.encode(payload, "be5F47w72eGxwWe8EAZe9Y4vP38g2rRG", algorithm="HS256")
print("Token:", token)

# Décoder
decoded = jwt.decode(token, "be5F47w72eGxwWe8EAZe9Y4vP38g2rRG", algorithms=["HS256"])
print("Decoded:", decoded)
EOF
```

### Problème : Mapping Incorrect

```bash
# Test interactif
python3
>>> from waynium_mappings import get_vehicle_type_id
>>> get_vehicle_type_id("EXECUTIVE_SEDAN")
'1'
>>> get_vehicle_type_id("UNKNOWN_CAR")
'1'  # Retourne DEFAULT
```

### Problème : Queue Bloquée

```bash
# Vérifier taille
curl http://localhost:5000/stats | jq '.queue_size'

# Si > 100, redémarrer
sudo systemctl restart carey_api.service
```

---

## 🔒 Sécurité

### HTTPS avec Nginx

```bash
# Installer Nginx + Certbot
apt install nginx certbot python3-certbot-nginx

# Config Nginx
cat > /etc/nginx/sites-available/carey-api << 'EOF'
server {
    listen 80;
    server_name votre-domaine.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

ln -s /etc/nginx/sites-available/carey-api /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx

# SSL
certbot --nginx -d votre-domaine.com
```

### Firewall

```bash
ufw allow 22/tcp   # SSH
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS
ufw enable
```

---

## 📞 Support & Contact

- **Documentation Carey** : https://carey.3scale.net/outbound_res
- **Documentation Waynium** : https://waynium.atlassian.net/wiki/external/...
- **Logs** : `journalctl -u carey_api.service -f`
- **Health** : `curl http://localhost:5000/readyz`

---

## 📝 Changelog

### v2.0.0 (2025-10-15)
- ✨ Format Waynium officiel (C_Gen_Client → C_Com_Commande → C_Gen_Mission)
- ✨ Système de mappings configurables
- ✨ Queue asynchrone avec threading
- ✨ Retry automatique (3 tentatives)
- ✨ Support annulations
- ✨ Logs JSON structurés
- ✨ Suite de tests complète

### v1.0.0 (2025-08-01)
- 🎉 Version initiale

---

**Version** : 2.0.0  
**Statut** : Production Ready ✅  
**Licence** : Propriétaire  
**Auteur** : Votre Équipe
