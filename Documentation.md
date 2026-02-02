# FFE Monitor - Guide de Déploiement

Ce document décrit les étapes pour déployer FFE Monitor avec l'architecture multi-utilisateurs (Supabase + OneSignal + PWA).

---

## Table des matières

1. [Prérequis](#prérequis)
2. [Configuration Supabase](#configuration-supabase)
3. [Configuration OneSignal](#configuration-onesignal)
4. [Configuration du Backend](#configuration-du-backend)
5. [Déploiement Local](#déploiement-local)
6. [Déploiement Production](#déploiement-production)
7. [Vérification](#vérification)
8. [Dépannage](#dépannage)

---

## Prérequis

### Logiciels requis

- **Python 3.10+**
- **Node.js 18+** (pour les outils de build si nécessaire)
- **Git**

### Comptes requis

- Compte [Supabase](https://supabase.com) (gratuit)
- Compte [OneSignal](https://onesignal.com) (gratuit)

---

## Configuration Supabase

### 1. Créer le projet

1. Connectez-vous à [Supabase Dashboard](https://app.supabase.com)
2. Cliquez sur **New Project**
3. Choisissez un nom (ex: `ffemonitor`)
4. Sélectionnez la région la plus proche (ex: `eu-west-3` pour la France)
5. Définissez un mot de passe pour la base de données
6. Attendez la création du projet (~2 minutes)

### 2. Récupérer les clés

Dans **Project Settings > API** :

| Clé | Variable .env | Description |
|-----|---------------|-------------|
| Project URL | `SUPABASE_URL` | URL du projet |
| anon public | `SUPABASE_ANON_KEY` | Clé publique (frontend) |
| service_role | `SUPABASE_SERVICE_KEY` | Clé secrète (backend only) |

Dans **Project Settings > API > JWT Settings** :

| Clé | Variable .env |
|-----|---------------|
| JWT Secret | `SUPABASE_JWT_SECRET` |

### 3. Créer les tables

Dans **SQL Editor**, exécutez les scripts dans l'ordre :

```bash
# 1. Schéma de base
supabase/schema.sql

# 2. Triggers et fonctions
supabase/triggers.sql

# 3. Row Level Security
supabase/rls.sql
```

Pour chaque fichier :
1. Ouvrez le fichier dans votre éditeur
2. Copiez tout le contenu
3. Collez dans l'éditeur SQL Supabase
4. Cliquez sur **Run**

### 4. Configurer l'authentification

Dans **Authentication > Providers** :

1. **Email** : Activé par défaut
   - Désactiver "Confirm email" pour les tests (réactiver en production)

2. **Site URL** : `http://localhost:8000` (dev) ou votre domaine (prod)

3. **Redirect URLs** : Ajouter :
   - `http://localhost:8000/app`
   - `http://localhost:8000/reset-password`
   - `https://votre-domaine.com/app` (production)

---

## Configuration OneSignal

### 1. Créer l'application

1. Connectez-vous à [OneSignal Dashboard](https://app.onesignal.com)
2. Cliquez sur **New App/Website**
3. Nom : `FFE Monitor`
4. Plateforme : **Web**

### 2. Configurer le Web Push

1. **Site Setup** :
   - Site URL : `https://votre-domaine.com` (ou `http://localhost:8000` pour tests)
   - Cochez "My site is not fully HTTPS" si localhost

2. **Permission Prompt** :
   - Type : Slide Prompt (recommandé)
   - Message : "Recevez des alertes instantanées à l'ouverture des concours"

3. **Welcome Notification** : Désactiver (on gère nous-même)

### 3. Récupérer les clés

Dans **Settings > Keys & IDs** :

| Clé | Variable .env |
|-----|---------------|
| OneSignal App ID | `ONESIGNAL_APP_ID` |
| REST API Key | `ONESIGNAL_API_KEY` |

### 4. Intégrer le SDK

Le SDK OneSignal est automatiquement chargé via le Service Worker. Assurez-vous que le fichier `frontend/sw.js` est accessible à la racine du site.

---

## Configuration du Backend

### 1. Cloner le projet

```bash
git clone https://github.com/votre-repo/FFEM.git
cd FFEM
```

### 2. Créer l'environnement virtuel

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
playwright install chromium
```

### 4. Configurer les variables d'environnement

```bash
cp .env.example .env
```

Éditez `.env` avec vos valeurs :

```env
# SUPABASE (obligatoire)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_KEY=eyJ...
SUPABASE_JWT_SECRET=your-jwt-secret

# ONESIGNAL (obligatoire)
ONESIGNAL_APP_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
ONESIGNAL_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# DÉLAIS PAR PLAN
DELAY_FREE=600      # 10 minutes
DELAY_PREMIUM=60    # 1 minute
DELAY_PRO=10        # 10 secondes
```

---

## Déploiement Local

### Lancer l'application

```bash
python run.py
```

L'application sera disponible sur `http://localhost:8000`

### Tester le flux

1. Ouvrez `http://localhost:8000`
2. Créez un compte via l'onglet "Inscription"
3. Vérifiez votre email (si confirmation activée)
4. Connectez-vous
5. Ajoutez un concours à surveiller
6. Activez les notifications push quand demandé

---

## Déploiement Production

### Option 1 : VPS (recommandé)

#### 1. Préparer le serveur

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.10 python3.10-venv nginx certbot python3-certbot-nginx

# Créer l'utilisateur
sudo useradd -m -s /bin/bash ffemonitor
sudo su - ffemonitor
```

#### 2. Installer l'application

```bash
git clone https://github.com/votre-repo/FFEM.git
cd FFEM
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium --with-deps
```

#### 3. Configurer systemd

Créez `/etc/systemd/system/ffemonitor.service` :

```ini
[Unit]
Description=FFE Monitor
After=network.target

[Service]
Type=simple
User=ffemonitor
WorkingDirectory=/home/ffemonitor/FFEM
Environment="PATH=/home/ffemonitor/FFEM/venv/bin"
ExecStart=/home/ffemonitor/FFEM/venv/bin/python run.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable ffemonitor
sudo systemctl start ffemonitor
```

#### 4. Configurer Nginx

Créez `/etc/nginx/sites-available/ffemonitor` :

```nginx
server {
    listen 80;
    server_name votre-domaine.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/ffemonitor /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 5. Activer HTTPS

```bash
sudo certbot --nginx -d votre-domaine.com
```

### Option 2 : Docker

#### Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Installer Playwright
RUN playwright install chromium --with-deps

COPY . .

EXPOSE 8000

CMD ["python", "run.py"]
```

#### docker-compose.yml

```yaml
version: '3.8'

services:
  ffemonitor:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

```bash
docker-compose up -d
```

---

## Vérification

### Checklist de déploiement

- [ ] Supabase
  - [ ] Tables créées (profiles, concours, subscriptions, notification_queue, notification_log)
  - [ ] Triggers fonctionnels (création profil auto)
  - [ ] RLS activé sur toutes les tables
  - [ ] Auth Email provider configuré

- [ ] OneSignal
  - [ ] App créée
  - [ ] Web Push configuré
  - [ ] Service Worker accessible (`/sw.js`)

- [ ] Backend
  - [ ] `.env` configuré avec toutes les variables
  - [ ] Application démarre sans erreur
  - [ ] Logs affichent "FFE Monitor - Démarrage"

- [ ] Frontend
  - [ ] Page de login accessible
  - [ ] Inscription fonctionne
  - [ ] Connexion fonctionne
  - [ ] PWA installable (manifest.json chargé)

- [ ] Notifications Push
  - [ ] Permissions accordées dans le navigateur
  - [ ] Player ID enregistré dans le profil utilisateur
  - [ ] Notification de test reçue

### Tests fonctionnels

```bash
# Vérifier que l'API répond
curl http://localhost:8000/health

# Vérifier le manifest PWA
curl http://localhost:8000/manifest.json

# Vérifier le Service Worker
curl http://localhost:8000/sw.js
```

---

## Dépannage

### Erreurs courantes

#### "SUPABASE_URL non configuré"

Vérifiez que `.env` contient `SUPABASE_URL` et que le fichier est dans le bon répertoire.

#### "Invalid JWT token"

1. Vérifiez que `SUPABASE_JWT_SECRET` correspond à celui de Supabase
2. Vérifiez que le token n'est pas expiré
3. Essayez de vous reconnecter

#### "Push notifications ne fonctionnent pas"

1. Vérifiez que le site est en HTTPS (obligatoire pour le push)
2. Vérifiez que `ONESIGNAL_APP_ID` est correct
3. Vérifiez les permissions du navigateur
4. Consultez la console OneSignal pour les erreurs

#### "Playwright browser not found"

```bash
playwright install chromium --with-deps
```

#### "Permission denied sur data/"

```bash
mkdir -p data
chmod 755 data
```

### Logs

```bash
# Logs systemd
sudo journalctl -u ffemonitor -f

# Logs Docker
docker-compose logs -f ffemonitor
```

### Support

- Issues GitHub : https://github.com/votre-repo/FFEM/issues
- Documentation Supabase : https://supabase.com/docs
- Documentation OneSignal : https://documentation.onesignal.com

---

## Architecture des plans

| Plan | Délai notification | Prix suggéré |
|------|-------------------|--------------|
| Free | 10 minutes | Gratuit |
| Premium | 1 minute | 4,99€/mois |
| Pro | 10 secondes | 9,99€/mois |

Les plans sont gérés manuellement par l'administrateur via le dashboard Supabase :

```sql
-- Passer un utilisateur en Premium
UPDATE profiles SET plan = 'premium' WHERE email = 'user@example.com';

-- Passer un utilisateur en Pro
UPDATE profiles SET plan = 'pro' WHERE email = 'user@example.com';
```

---

## Mises à jour

### Mettre à jour l'application

```bash
cd FFEM
git pull origin main
pip install -r requirements.txt
sudo systemctl restart ffemonitor
```

### Mettre à jour le schéma Supabase

Si des migrations sont nécessaires, exécutez-les dans l'éditeur SQL de Supabase avant de redémarrer l'application.

---

*Documentation générée le 2 février 2026 - FFE Monitor v2.0*
