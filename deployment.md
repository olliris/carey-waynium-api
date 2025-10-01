# 🚀 Guide de Déploiement - Carey → Waynium API v2

## ⚠️ Changements Majeurs v2

**Cette version v2 change COMPLÈTEMENT le format d'envoi vers Waynium !**

- ❌ **Ancien format** : Payload "plat" avec `booking_reference`, `passenger_first_name`, etc.
- ✅ **Nouveau format** : Structure hiérarchique Waynium avec `C_Gen_Client` → `C_Com_Commande` → `C_Gen_Mission`

**Vous DEVEZ redéployer `transform.py` et `main.py` pour que cela fonctionne !**

---

## 📋 Prérequis

```bash
# Se connecter au VPS
ssh root@46.255.164.90

# Vérifier Python version (>= 3.8)
python3 --version
```

---

## 🛠️ Installation / Mise à Jour

### Étape 1 : Backup de l'existant

```bash
cd /opt/carey-waynium-api
cp -r . ../carey-waynium-api.backup.$(date +%Y%m%d)
```

### Étape 2 : Arrêter le service actuel

```bash
systemctl stop carey_api.service
```

### Étape 3 : Mise à jour du code

```bash
cd /opt/carey-waynium-api

# Remplacer transform.py
cat > transform.py << 'EOF'
[Copier le contenu complet du nouveau transform.py ici]
EOF

# Remplacer main.py
cat > main.py << 'EOF'
[Copier le contenu complet du nouveau main.py ici]
EOF

# Installer nouvelles dépendances
source venv/bin/activate
pip install flask flask-cors requests pyjwt python-dotenv
```

### Étape 4 : Configuration

```bash
# Créer/mettre à jour .env
cat > .env << 'EOF'
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
EOF

chmod 600 .env  # Sécuriser le fichier
```

### Étape 5 : Vérification pre-flight

```bash
# Activer venv
source venv/bin/activate

# Test syntaxe Python
python3 -m py_compile transform.py
python3 -m py_compile main.py

# Test import
python3 -c "from transform import transform_to_waynium; print('✅ Transform OK')"
python3 -c "from main import app; print('✅ Main OK')"
```

### Étape 6 : Redémarrage du service

```bash
# Recharger systemd
systemctl daemon-reload

# Redémarrer le service
systemctl restart carey_api.service

# Vérifier le statut
systemctl status carey_api.service

# Suivre les logs en temps réel
journalctl -u carey_api.service -f
```

---

## 🧪 Tests Post-Déploiement

### Test 1 : Health Check

```bash
curl http://localhost:5000/healthz
# Attendu: {"status":"ok","timestamp":"..."}

curl http://localhost:5000/readyz
# Attendu: {"config_loaded":true,"queue_enabled":true,...}

curl http://localhost:5000/version
# Attendu: {"name":"carey-waynium-api","version":"2.0.0",...}
```

### Test 2 : Webhook avec payload v2

```bash
# Créer un payload de test
cat > test_payload_v2.json << 'EOF'
{
  "reservationNumber": "TEST-DEPLOY-001",
  "passenger": {
    "firstName": "Test",
    "lastName": "Deploy",
    "mobile": "+33612345678",
    "email": "test@example.com"
  },
  "pickup": {
    "time": "2025-12-01T14:00:00Z",
    "locationType": "Airport",
    "city": "Paris",
    "country": "FR",
    "transportationCenterDetails": {
      "transportationCenterName": "CDG",
      "transportationCenterCode": "CDG"
    }
  },
  "dropoff": {
    "address": "1 Rue de Test",
    "city": "Paris",
    "postalCode": "75001",
    "country": "FR"
  },
  "service": {
    "type": "Airport",
    "vehicleType": "Sedan"
  },
  "status": "Confirmed"
}
EOF

# Envoyer le test
curl -X POST http://localhost:5000/carey/webhook \
  -H "Content-Type: application/json" \
  -H "X-API-Key: 1" \
  -d @test_payload_v2.json

# Attendu en mode asynchrone (ENABLE_QUEUE=true):
# {"status":"accepted","transaction_id":"TXN-...","queued":true,"queue_size":1}

# Vérifier les logs
journalctl -u carey_api.service -n 50 --no-pager
```

### Test 3 : Vérification transformation

```bash
# Test unitaire de la transformation
cat > test_transform_manual.py << 'EOF'
from transform import transform_to_waynium
import json

payload = {
    "reservationNumber": "MANUAL-TEST",
    "passenger": {"firstName": "John", "lastName": "Doe", "mobile": "+33600000000"},
    "pickup": {"time": "2025-12-01T10:00:00Z", "city": "Paris", "country": "FR"},
    "dropoff": {"city": "Lyon", "country": "FR"}
}

result = transform_to_waynium(payload)
print(json.dumps(result, indent=2, ensure_ascii=False))

# Vérifications
assert result["limo"] == "abllimousines"
assert result["config"] == "createMissionComplete"
assert "C_Gen_Client" in result["params"]
print("\n✅ Transformation OK - Format Waynium valide")
EOF

python3 test_transform_manual.py
```

### Test 4 : Test annulation

```bash
cat > test_cancellation.json << 'EOF'
{
  "reservationNumber": "TEST-CANCEL-001",
  "status": "CANCELLED"
}
EOF

curl -X POST http://localhost:5000/carey/webhook \
  -H "Content-Type: application/json" \
  -H "X-API-Key: 1" \
  -d @test_cancellation.json

# Vérifier dans les logs que config = "updateMissionLight"
journalctl -u carey_api.service -n 20 | grep updateMissionLight
```

---

## 🔒 Sécurisation Production

### 1. Firewall UFW

```bash
# Installer UFW si nécessaire
apt install ufw

# Règles de base
ufw default deny incoming
ufw default allow outgoing

# Autoriser SSH
ufw allow 22/tcp

# Autoriser Flask (ou Nginx si utilisé)
ufw allow 5000/tcp

# Activer
ufw enable
ufw status
```

### 2. HTTPS avec Nginx + Let's Encrypt

```bash
# Installer Nginx et Certbot
apt install nginx certbot python3-certbot-nginx

# Configuration Nginx
cat > /etc/nginx/sites-available/carey-api << 'EOF'
server {
    listen 80;
    server_name votre-domaine.com;  # Remplacer!

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }
}
EOF

# Activer le site
ln -s /etc/nginx/sites-available/carey-api /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx

# Obtenir certificat SSL
certbot --nginx -d votre-domaine.com
```

### 3. Whitelist IP Carey (Optionnel)

```bash
# Dans Nginx, ajouter:
# location /carey/webhook {
#     allow 1.2.3.4;  # IP Carey
#     deny all;
#     proxy_pass http://127.0.0.1:5000;
# }
```

### 4. Rotation des Logs

```bash
# Créer config logrotate
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
    postrotate
        systemctl reload carey_api.service > /dev/null 2>&1 || true
    endscript
}
EOF

# Créer le dossier de logs
mkdir -p /var/log/carey-waynium-api
```

---

## 📊 Monitoring

### Métriques disponibles

```bash
# Stats temps réel
curl http://localhost:5000/stats

# Exemple réponse:
# {
#   "stats": {
#     "received": 150,
#     "success": 145,
#     "failed": 5,
#     "queued": 0
#   },
#   "queue_size": 0,
#   "queue_enabled": true
# }
```

### Alertes système (optionnel)

```bash
# Script de monitoring simple
cat > /opt/carey-waynium-api/monitor.sh << 'EOF'
#!/bin/bash
HEALTH=$(curl -s http://localhost:5000/healthz | jq -r '.status')
if [ "$HEALTH" != "ok" ]; then
    echo "ALERT: API down!" | mail -s "Carey API Alert" admin@example.com
fi
EOF

chmod +x /opt/carey-waynium-api/monitor.sh

# Ajouter au cron (toutes les 5 minutes)
crontab -e
# */5 * * * * /opt/carey-waynium-api/monitor.sh
```

---

## 🐛 Dépannage

### Problème : Service ne démarre pas

```bash
# Vérifier les logs systemd
journalctl -u carey_api.service -n 100 --no-pager

# Erreurs communes:
# 1. Port déjà utilisé
sudo lsof -i :5000
sudo kill -9 <PID>

# 2. Permissions .env
chmod 600 /opt/carey-waynium-api/.env

# 3. Dépendances manquantes
cd /opt/carey-waynium-api
source venv/bin/activate
pip install -r requirements.txt  # Si vous avez un requirements.txt
```

### Problème : Waynium rejette les requêtes

```bash
# Activer le debug temporaire
export DEBUG=true
python3 main.py

# Vérifier le JWT généré
python3 << 'EOF'
import jwt
from datetime import datetime

payload = {"iss": "abllimousines", "iat": int(datetime.utcnow().timestamp())}
token = jwt.encode(payload, "be5F47w72eGxwWe8EAZe9Y4vP38g2rRG", algorithm="HS256")
print("JWT Token:", token)

# Decoder pour vérifier
decoded = jwt.decode(token, "be5F47w72eGxwWe8EAZe9Y4vP38g2rRG", algorithms=["HS256"])
print("Decoded:", decoded)
EOF
```

### Problème : Transformation échoue

```bash
# Test de transformation avec trace complète
python3 << 'EOF'
from transform import transform_to_waynium
import json
import traceback

payload = {...}  # Votre payload problématique

try:
    result = transform_to_waynium(payload)
    print(json.dumps(result, indent=2))
except Exception as e:
    print("ERROR:", str(e))
    traceback.print_exc()
EOF
```

### Problème : Queue bloquée

```bash
# Vérifier la taille de la queue
curl http://localhost:5000/stats | jq '.queue_size'

# Si > 100, redémarrer le service
systemctl restart carey_api.service
```

---

## 🔄 Rollback vers version précédente

```bash
# Arrêter le service
systemctl stop carey_api.service

# Restaurer le backup
cd /opt
rm -rf carey-waynium-api
cp -r carey-waynium-api.backup.YYYYMMDD carey-waynium-api

# Redémarrer
cd carey-waynium-api
source venv/bin/activate
systemctl start carey_api.service
systemctl status carey_api.service
```

---

## 📞 Checklist avant Go-Live Production

- [ ] **Tests fonctionnels** : Tous les tests passent (création, modification, annulation)
- [ ] **Configuration** : `.env` avec credentials PROD Waynium
- [ ] **HTTPS** : Nginx + Let's Encrypt configurés
- [ ] **Firewall** : UFW activé avec règles appropriées
- [ ] **Monitoring** : Health checks configurés
- [ ] **Logs** : Rotation configurée
- [ ] **Backup** : Script de backup automatique
- [ ] **Documentation** : Carey informé du nouveau endpoint
- [ ] **Whitelist** : IP du VPS whitelistée côté Carey
- [ ] **Load test** : Test avec 10+ réservations simultanées
- [ ] **Rollback plan** : Backup v1 disponible

---

## 🎯 Configuration Carey (à communiquer)

Une fois votre API déployée, communiquer à Carey :

```yaml
Webhook URL: https://votre-domaine.com/carey/webhook
Méthode: POST
Content-Type: application/json
Authentication: 
  - Header: X-API-Key: votre_cle_production
  OU
  - Header: Authorization: Bearer votre_cle_production

Format accepté: Carey API v2 (pickup/dropoff/passenger)
Format legacy: Supporté (trip.*)

Timeout recommandé: 30 secondes
Retry: 3 tentatives avec backoff exponentiel

Codes réponse:
  - 200: Traitement synchrone réussi
  - 202: Traitement asynchrone accepté (queued)
  - 400: Payload invalide
  - 401: Authentication échouée
  - 502: Erreur Waynium upstream
  - 500: Erreur serveur interne
```

---

## 📚 Ressources

- **Documentation Carey**: https://carey.3scale.net/outbound_res
- **Documentation Waynium**: https://waynium.atlassian.net/wiki/external/OTRjNDk3ZTM0ZmZjNDlhYjk2ODcxYTRlODdjZjMzNTk
- **JWT.io**: https://jwt.io (pour tester vos tokens)
- **Repository GitHub** (si applicable): [lien vers votre repo]

---

## 🆘 Support

En cas de problème :

1. **Logs** : `journalctl -u carey_api.service -f`
2. **Stats** : `curl http://localhost:5000/stats`
3. **Health** : `curl http://localhost:5000/readyz`
4. **Contact Waynium** : [contact technique Waynium]
5. **Contact Carey** : [contact technique Carey]

---

**Version**: 2.0.0  
**Dernière mise à jour**: Octobre 2025  
**Statut**: Production Ready ✅
