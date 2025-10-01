# 🎨 Guide d'Utilisation - Server Manager

Interface web complète pour gérer votre serveur Carey→Waynium API.

---

## 🚀 Installation (5 minutes)

### Étape 1 : Uploader les Fichiers

```bash
# Se connecter au VPS
ssh root@46.255.164.90

# Aller dans le dossier
cd /opt/carey-waynium-api

# Créer server_manager.py
nano server_manager.py
# Coller le contenu du fichier server_manager.py
# Sauvegarder: Ctrl+X, puis Y, puis Entrée
```

### Étape 2 : Installer les Dépendances

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Installer Flask CORS (si pas déjà fait)
pip install flask-cors
```

### Étape 3 : Démarrer le Server Manager

```bash
# Démarrer le serveur de gestion (port 5001)
python3 server_manager.py

# Vous verrez:
# 🚀 Server Manager API
# 📁 Gestion de: /opt/carey-waynium-api
# 🔐 Mot de passe par défaut: 'password' (à changer!)
# 🌐 Interface web: Ouvrir web_manager.html dans votre navigateur
```

### Étape 4 : Ouvrir l'Interface Web

#### **Option A : Depuis Votre Ordinateur Local**

1. **Téléchargez** `web_manager.html` sur votre ordinateur
2. **Ouvrez-le** avec votre navigateur (Chrome, Firefox, Safari)
3. **L'interface se connectera** automatiquement au serveur

#### **Option B : Accès Direct (avec Nginx)**

Si vous avez Nginx configuré, ajoutez :

```bash
# Créer un alias pour l'interface
sudo nano /etc/nginx/sites-available/carey-api

# Ajouter:
location /manager {
    alias /opt/carey-waynium-api/web_manager.html;
}

# Redémarrer Nginx
sudo systemctl restart nginx
```

Puis accédez à : `http://46.255.164.90/manager`

---

## 🔐 Connexion

1. **Mot de passe par défaut** : `password`
2. Entrez-le dans l'écran de connexion
3. Cliquez "Se connecter"

### ⚠️ Changer le Mot de Passe (IMPORTANT!)

```bash
# Générer un nouveau hash SHA256
echo -n "votre_nouveau_mot_de_passe" | sha256sum

# Éditer server_manager.py
nano server_manager.py

# Remplacer la ligne:
ADMIN_PASSWORD_HASH = "5e88489..." # avec votre nouveau hash

# Redémarrer
pkill -f server_manager.py
python3 server_manager.py
```

---

## 🎯 Fonctionnalités

### 1. **Explorateur de Fichiers** (Sidebar Gauche)

- 📁 **Navigation** : Cliquez sur les dossiers pour explorer
- 📄 **Ouvrir fichier** : Cliquez sur un fichier pour l'éditer
- 🔄 **Actualiser** : Bouton dans la toolbar
- 📊 **Info système** : Nombre de fichiers et taille totale

### 2. **Éditeur de Code** (Centre)

#### **Éditer un Fichier**
1. Cliquez sur un fichier dans l'explorateur
2. Le contenu s'affiche dans l'éditeur
3. Modifiez le code
4. Cliquez "💾 Sauvegarder" ou **Ctrl+S**

#### **Fonctionnalités de l'Éditeur**
- ✏️ **Coloration syntaxique** : Thème VS Code Dark
- 📑 **Onglets multiples** : Ouvrez plusieurs fichiers
- ⌨️ **Raccourcis clavier** :
  - `Ctrl+S` / `Cmd+S` : Sauvegarder
  - `Ctrl+N` / `Cmd+N` : Nouveau fichier
  - `Esc` : Fermer les modals
- 💾 **Backup auto** : Avant chaque sauvegarde → `.backup`

### 3. **Gestion des Fichiers**

#### **Créer un Nouveau Fichier**
1. Cliquez "➕ Nouveau"
2. Entrez le nom (ex: `test.py`)
3. Cliquez "Créer"
4. Le fichier s'ouvre automatiquement

#### **Supprimer un Fichier**
1. Ouvrez le fichier à supprimer
2. Cliquez "🗑️ Supprimer"
3. Confirmez
4. ⚠️ **Attention** : Suppression définitive !

### 4. **Logs en Temps Réel**

#### **Afficher les Logs**
1. Cliquez "📋 Logs" dans la toolbar
2. Panel s'ouvre en bas
3. Affiche les 100 dernières lignes
4. Colorisation automatique :
   - 🔴 Rouge : Erreurs
   - 🟡 Jaune : Warnings
   - 🔵 Bleu : Info

#### **Rafraîchir les Logs**
- Cliquez à nouveau sur "📋 Logs" pour actualiser
- Ou redémarrez le service pour voir les nouveaux logs

### 5. **Contrôle du Service**

#### **Redémarrer le Service Carey API**
1. Cliquez "🔄 Redémarrer Service"
2. Confirmez
3. Attendez 2-3 secondes
4. Le service redémarre

⚠️ **Note** : Cela redémarre `carey_api.service` (votre API principale), pas le server manager.

---

## 🎨 Interface

### **Layout**

```
┌──────────────────────────────────────────────────┐
│  Sidebar (Explorer)  │   Main Content            │
│  ─────────────────   │  ────────────────────────  │
│  📁 Dossiers         │  [Toolbar: Boutons]       │
│  📄 Fichiers         │  ──────────────────────    │
│                      │  [Tabs: Fichiers ouverts] │
│  - transform.py      │  ──────────────────────    │
│  - main.py           │  [Éditeur de Code]        │
│  - waynium_mappings  │                           │
│  - .env              │  [Code Python ici...]     │
│  - README.md         │                           │
│                      │  ──────────────────────    │
│                      │  [Logs Panel (optionnel)] │
│                      │  ──────────────────────    │
│  [System Info]       │  [Status Bar]             │
└──────────────────────────────────────────────────┘
```

### **Thème**

- 🌙 **Dark Mode** (VS Code style)
- 🎨 **Couleurs** :
  - Background: `#1e1e1e`
  - Sidebar: `#252526`
  - Toolbar: `#323233`
  - Accent: `#007acc` (bleu)

---

## 🔧 Cas d'Usage Pratiques

### **Cas 1 : Modifier un Mapping**

```
1. Ouvrir waynium_mappings.py
2. Trouver VEHICLE_TYPE_MAPPING
3. Ajouter: "TESLA": "8",
4. Ctrl+S pour sauvegarder
5. Cliquer "🔄 Redémarrer Service"
6. Vérifier les logs
```

### **Cas 2 : Vérifier les Logs d'Erreur**

```
1. Cliquer "📋 Logs"
2. Chercher les lignes rouges (erreurs)
3. Analyser le message d'erreur
4. Corriger le fichier concerné
5. Sauvegarder et redémarrer
```

### **Cas 3 : Éditer la Configuration**

```
1. Ouvrir .env
2. Modifier WAYNIUM_API_URL (staging → prod)
3. Sauvegarder
4. Redémarrer le service
5. Vérifier via logs que la connexion fonctionne
```

### **Cas 4 : Créer un Fichier de Test**

```
1. Cliquer "➕ Nouveau"
2. Nom: test_manual.py
3. Écrire un script de test
4. Sauvegarder
5. Exécuter depuis SSH si besoin
```

---

## ⚠️ Limitations de Sécurité

### **IMPORTANT** : Cette Interface est pour Usage Interne Uniquement

1. **Pas d'HTTPS par défaut** : Utilisez Nginx avec SSL en production
2. **Authentification basique** : Changez le mot de passe immédiatement
3. **Pas de multi-utilisateurs** : Un seul mot de passe pour tous
4. **Firewall recommandé** : Limitez l'accès au port 5001

### **Sécurisation Recommandée**

```bash
# 1. Firewall : Bloquer port 5001 de l'extérieur
sudo ufw deny 5001/tcp

# 2. Accès SSH uniquement
# Utilisez un tunnel SSH depuis votre machine:
ssh -L 5001:localhost:5001 root@46.255.164.90

# Puis accédez à: http://localhost:5001 sur votre machine locale
```

### **Pour Production**

Si vous voulez exposer l'interface publiquement :

1. **Nginx reverse proxy** avec HTTPS
2. **Authentification HTTP Basic** (Nginx)
3. **Whitelist IP** (Nginx allow/deny)
4. **JWT tokens** (modification code nécessaire)

---

## 🐛 Dépannage

### **Problème : "Erreur de connexion"**

```bash
# Vérifier que server_manager tourne
ps aux | grep server_manager

# Si pas actif, démarrer:
cd /opt/carey-waynium-api
source venv/bin/activate
python3 server_manager.py

# Vérifier le port
netstat -tulpn | grep 5001
```

### **Problème : "Non autorisé" après connexion**

```bash
# Le mot de passe a peut-être été changé
# Réinitialiser dans server_manager.py:
nano server_manager.py

# Remettre:
ADMIN_PASSWORD_HASH = "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"
# (= "password")

# Redémarrer
pkill -f server_manager.py
python3 server_manager.py
```

### **Problème : Fichiers ne s'affichent pas**

```bash
# Vérifier les permissions
ls -la /opt/carey-waynium-api

# Si nécessaire:
sudo chown -R root:root /opt/carey-waynium-api
sudo chmod -R 755 /opt/carey-waynium-api
```

### **Problème : Interface web blanche**

- Vérifiez que `web_manager.html` contient tout le code
- Ouvrez la console du navigateur (F12) pour voir les erreurs
- Vérifiez l'URL API dans le code : `const API_BASE = ...`

---

## 🎓 Commandes Utiles

```bash
# Démarrer server_manager en arrière-plan
nohup python3 server_manager.py > /tmp/server_manager.log 2>&1 &

# Arrêter server_manager
pkill -f server_manager.py

# Voir les logs server_manager
tail -f /tmp/server_manager.log

# Créer un service systemd pour server_manager (optionnel)
sudo nano /etc/systemd/system/server_manager.service

# Contenu:
[Unit]
Description=Server Manager API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/carey-waynium-api
ExecStart=/opt/carey-waynium-api/venv/bin/python /opt/carey-waynium-api/server_manager.py
Restart=always

[Install]
WantedBy=multi-user.target

# Activer
sudo systemctl enable server_manager.service
sudo systemctl start server_manager.service
```

---

## 📚 Ressources

- **Port API principale** : 5000 (carey_api)
- **Port Server Manager** : 5001 (gestion)
- **Fichiers gérés** : `/opt/carey-waynium-api/*`
- **Logs système** : `journalctl -u carey_api.service`

---

## 🎉 Félicitations !

Vous avez maintenant une interface web complète pour gérer votre serveur ! 🚀

**Prochaines étapes** :
1. Changez le mot de passe
2. Explorez vos fichiers
3. Testez l'édition de code
4. Vérifiez les logs
5. Personnalisez vos mappings

**Besoin d'aide ?** Consultez ce guide ou les logs d'erreur. 💪
