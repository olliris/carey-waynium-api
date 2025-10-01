# 🗺️ Guide de Configuration des Mappings Waynium

## 📍 Où Trouver les IDs Waynium

Connectez-vous à votre interface Waynium et accédez aux URLs suivantes :

### 1. Types de Véhicules (MIS_TVE_ID)
**URL**: `https://abllimousines.way-plan.com/bop3/C_Gen_TypeVehicule/`

Vous verrez une liste comme :
```
ID | Libellé
---|-------------------
1  | Berline Économique
2  | Van 6 places
3  | SUV Premium
4  | Limousine
5  | Bus 20 places
```

### 2. Services (FMI_SER_ID)
**URL**: `https://abllimousines.way-plan.com/bop3/C_Com_Service/`

Exemple :
```
ID | Libellé
---|----------------------
1  | Transfert Aéroport
2  | Transfert Standard
3  | Mise à Disposition
4  | Service Premium VIP
5  | Événement Spécial
```

### 3. Clients (CLI_ID)
**URL**: `https://abllimousines.way-plan.com/bop3/C_Gen_Client/`

Liste de vos clients :
```
ID  | Nom Client
----|---------------------------
320 | ABL Limousines - Carey Belgium
321 | Corporate Account XYZ
322 | Hotel Marriott Brussels
```

---

## 🔧 Comment Mettre à Jour les Mappings

### Étape 1 : Récupérer les IDs depuis Waynium

```bash
# Se connecter au VPS
ssh root@46.255.164.90

# Ouvrir le fichier de mappings
cd /opt/carey-waynium-api
nano waynium_mappings.py
```

### Étape 2 : Mettre à Jour les Dictionnaires

#### Exemple : Ajouter un Nouveau Type de Véhicule

Supposons que Waynium vous dit :
- ID `6` = "Van Électrique"

```python
# Dans waynium_mappings.py, section VEHICLE_TYPE_MAPPING

VEHICLE_TYPE_MAPPING = {
    # ... mappings existants ...
    
    # Nouveau mapping
    "ELECTRIC_VAN": "6",
    "VAN_ELECTRIC": "6",
    "E-VAN": "6",
    
    "DEFAULT": "1"
}
```

#### Exemple : Ajouter un Nouveau Client

Carey vous envoie un nouveau compte : "Hotel Hilton Brussels"
Waynium vous donne CLI_ID = `325`

```python
# Dans waynium_mappings.py, section CLIENT_MAPPING

CLIENT_MAPPING = {
    # ... mappings existants ...
    
    # Nouveau client
    "Hotel Hilton Brussels": 325,
    "HILTON_BRUSSELS": 325,  # Variantes possibles
    
    "DEFAULT": 320
}
```

#### Exemple : Ajouter un Nouveau Service

Waynium crée un service "Roadshow" avec ID `10`

```python
# Dans waynium_mappings.py, section SERVICE_MAPPING

SERVICE_MAPPING = {
    # ... mappings existants ...
    
    # Nouveau service
    "ROADSHOW": "10",
    "ROAD_SHOW": "10",
    "MULTI_STOP": "10",
    
    "DEFAULT": "1"
}
```

### Étape 3 : Tester les Changements

```bash
# Test de validation
python3 << 'EOF'
from waynium_mappings import (
    get_vehicle_type_id,
    get_service_id,
    get_client_id,
    validate_mappings
)

# Valider la syntaxe
try:
    validate_mappings()
    print("✅ Mappings valides")
except ValueError as e:
    print(f"❌ Erreur: {e}")

# Tester les nouveaux mappings
print("\n--- Tests ---")
print(f"ELECTRIC_VAN -> {get_vehicle_type_id('ELECTRIC_VAN')}")
print(f"Hotel Hilton Brussels -> {get_client_id('Hotel Hilton Brussels')}")
print(f"ROADSHOW -> {get_service_id('ROADSHOW')}")
EOF
```

### Étape 4 : Redémarrer le Service

```bash
systemctl restart carey_api.service
systemctl status carey_api.service

# Vérifier les logs
journalctl -u carey_api.service -n 20
```

---

## 🎯 Cas d'Usage Réels

### Cas 1 : Carey Envoie un Nouveau Type de Véhicule

**Problème** : Carey envoie `"vehicleType": "Mercedes S-Class"`

**Solution** :
1. Aller sur Waynium : quel ID correspond à ce véhicule ? Disons `ID = 4` (Limousine)
2. Ajouter dans `VEHICLE_TYPE_MAPPING` :
```python
"MERCEDES_S_CLASS": "4",
"MERCEDES_S-CLASS": "4",
"S_CLASS": "4",
```
3. Redémarrer le service

### Cas 2 : Nouveau Compte Client Carey

**Problème** : Carey crée un compte "European Parliament"

**Solution** :
1. Créer le client dans Waynium → obtenir `CLI_ID` (ex: 330)
2. Ajouter dans `CLIENT_MAPPING` :
```python
"European Parliament": 330,
"EUROPEAN_PARLIAMENT": 330,
"EU_PARLIAMENT": 330,
```

### Cas 3 : Service Spécifique pour un Événement

**Problème** : Besoin d'un service "EU Summit Transport"

**Solution** :
1. Créer le service dans Waynium → obtenir `FMI_SER_ID` (ex: 15)
2. Ajouter dans `SERVICE_MAPPING` :
```python
"EU_SUMMIT": "15",
"SUMMIT_TRANSPORT": "15",
"GOVERNMENT_EVENT": "15",
```

---

## 🔍 Débogage des Mappings

### Vérifier Quel ID Est Utilisé

Ajoutez des logs dans `transform.py` temporairement :

```python
# Dans transform_carey_v2_to_waynium(), après les mappings :

print(f"DEBUG - Vehicle: {vehicle_type} -> ID: {waynium_vehicle_id}")
print(f"DEBUG - Service: {service_type} -> ID: {waynium_service_id}")
print(f"DEBUG - Client: {account_name} -> ID: {cli_id}")
```

Puis regardez les logs :
```bash
journalctl -u carey_api.service -f | grep DEBUG
```

### Tester un Mapping Spécifique

```python
# Test interactif
python3
>>> from waynium_mappings import get_vehicle_type_id
>>> get_vehicle_type_id("EXECUTIVE_SEDAN")
'1'
>>> get_vehicle_type_id("TOTALLY_UNKNOWN_VEHICLE")
'1'  # Retourne DEFAULT
```

---

## 📊 Tableau de Référence Rapide

| Carey Envoie | Waynium Attend | Fichier Mapping | Fonction |
|--------------|----------------|-----------------|----------|
| `vehicleType: "Sedan"` | `MIS_TVE_ID: "1"` | `VEHICLE_TYPE_MAPPING` | `get_vehicle_type_id()` |
| `service.type: "Airport"` | `FMI_SER_ID: "1"` | `SERVICE_MAPPING` | `get_service_id()` |
| `accountName: "Carey Belgium"` | `CLI_ID: 320` | `CLIENT_MAPPING` | `get_client_id()` |
| `country: "FR"` | `PAY_ID: "65"` | `COUNTRY_MAPPING` | `get_country_id()` |
| `passenger.language: "FR"` | `PAS_LAN_ID: "2"` | `LANGUAGE_MAPPING` | `get_language_id()` |
| `locationType: "Airport"` | `LIE_TLI_ID: "1"` | `LOCATION_TYPE_MAPPING` | `get_location_type_id()` |

---

## ⚠️ Pièges à Éviter

### ❌ Ne PAS Faire

```python
# Mauvais : ID en integer au lieu de string
VEHICLE_TYPE_MAPPING = {
    "SEDAN": 1,  # ❌ Erreur !
}

# Mauvais : Oublier DEFAULT
SERVICE_MAPPING = {
    "AIRPORT": "1",
    # ❌ Pas de DEFAULT = erreur si service inconnu
}
```

### ✅ À Faire

```python
# Bon : ID en string
VEHICLE_TYPE_MAPPING = {
    "SEDAN": "1",  # ✅ Correct
    "DEFAULT": "1"  # ✅ Toujours avoir DEFAULT
}
```

---

## 🔄 Maintenance Continue

### Fichier de Suivi (Optionnel)

Créez un fichier `MAPPING_CHANGELOG.md` pour tracer les changements :

```markdown
# Historique des Mappings

## 2025-10-15
- Ajout véhicule "ELECTRIC_VAN" -> ID 6
- Nouveau client "Hotel Hilton" -> CLI_ID 325

## 2025-10-10
- Ajout service "ROADSHOW" -> ID 10
```

### Script d'Export des Mappings

```bash
# export_mappings.sh - Pour backup
cat > /opt/carey-waynium-api/export_mappings.sh << 'EOF'
#!/bin/bash
python3 << 'PYEOF'
from waynium_mappings import *
import json

data = {
    "vehicles": VEHICLE_TYPE_MAPPING,
    "services": SERVICE_MAPPING,
    "clients": CLIENT_MAPPING,
    "countries": COUNTRY_MAPPING,
    "languages": LANGUAGE_MAPPING
}

print(json.dumps(data, indent=2))
PYEOF
EOF

chmod +x export_mappings.sh
./export_mappings.sh > mappings_backup.json
```

---

## 📞 Workflow Complet

1. **Carey envoie un nouveau type** (ex: nouveau véhicule)
2. **Réception échoue** → logs montrent "UNKNOWN_VEHICLE"
3. **Contacter Waynium** : "Quel ID pour ce véhicule ?"
4. **Waynium répond** : "C'est l'ID 7"
5. **Éditer** `waynium_mappings.py`
6. **Tester** avec script Python
7. **Redémarrer** le service
8. **Vérifier** : renvoyer le webhook test
9. **Documenter** dans changelog

---

**Temps estimé pour un nouveau mapping** : 5-10 minutes

**Besoin d'aide ?** Contactez l'équipe Waynium avec la valeur exacte que Carey envoie.
