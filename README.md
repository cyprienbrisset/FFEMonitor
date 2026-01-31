# EngageWatch

Outil de surveillance d'ouverture des concours équestres FFE avec notifications Telegram instantanées.

## Fonctionnalités

- Surveillance automatique des concours FFE par numéro
- Détection des boutons "Engager" et "Demande de participation"
- Notifications Telegram instantanées à l'ouverture
- Interface web simple et intuitive
- Fonctionne en local sur votre ordinateur

## Prérequis

- Python 3.10 ou supérieur
- Un compte FFE avec identifiants valides
- Un bot Telegram (gratuit)

## Installation

### 1. Cloner le projet

```bash
cd /chemin/vers/FFEM
```

### 2. Créer l'environnement virtuel

```bash
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Installer Playwright

```bash
playwright install chromium
```

### 5. Configurer l'application

Copier le fichier de configuration :

```bash
cp .env.example .env
```

Éditer `.env` avec vos informations :

```env
# Vos identifiants FFE
FFE_USERNAME=votre_email@example.com
FFE_PASSWORD=votre_mot_de_passe

# Telegram (voir section ci-dessous)
TELEGRAM_BOT_TOKEN=votre_token
TELEGRAM_CHAT_ID=votre_chat_id
```

## Configuration Telegram

### Créer un bot Telegram

1. Ouvrir Telegram et rechercher `@BotFather`
2. Envoyer `/newbot`
3. Suivre les instructions pour nommer votre bot
4. Copier le **token** fourni (format: `123456789:ABCdef...`)

### Obtenir votre Chat ID

1. Rechercher `@userinfobot` sur Telegram
2. Démarrer une conversation avec `/start`
3. Le bot vous donne votre **Chat ID** (un nombre)

### Activer votre bot

1. Rechercher votre bot par son nom sur Telegram
2. Cliquer sur "Démarrer" pour l'activer

## Utilisation

### Lancer l'application

```bash
python run.py
```

L'application démarre et affiche :

```
==================================================
  EngageWatch - Surveillance Concours FFE
==================================================

Interface disponible sur http://localhost:8000
```

### Accéder à l'interface

Ouvrir votre navigateur sur : **http://localhost:8000**

### Ajouter un concours

1. Trouver le numéro du concours sur [ffecompet.ffe.com](https://ffecompet.ffe.com/concours)
2. Entrer le numéro dans le champ de l'interface
3. Cliquer sur "Ajouter"

### Recevoir les notifications

Dès qu'un concours surveillé s'ouvre :
- Vous recevez une notification Telegram instantanée
- Le statut se met à jour dans l'interface

## Interface

L'interface affiche :

| Colonne | Description |
|---------|-------------|
| Numéro | Lien cliquable vers le concours FFE |
| Statut | Fermé / Ouvert - Engagement / Ouvert - Demande |
| Notification | En attente / Envoyée |
| Dernière vérif. | Date de la dernière vérification |

## Indicateurs de statut

- **🟢 Connexion FFE** : Vert = connecté au site FFE
- **🟢 Surveillance** : Vert = surveillance active

## Arrêter l'application

Appuyer sur `Ctrl+C` dans le terminal.

## Résolution de problèmes

### "Fichier .env manquant"

Créez le fichier `.env` à partir du template :
```bash
cp .env.example .env
```

### "Connexion FFE échouée"

- Vérifiez vos identifiants dans `.env`
- Testez votre connexion sur le site FFE manuellement

### "Pas de notification Telegram"

- Vérifiez le token et chat_id dans `.env`
- Assurez-vous d'avoir démarré une conversation avec votre bot

### L'interface ne s'affiche pas

- Vérifiez que le port 8000 n'est pas utilisé
- Essayez : `http://127.0.0.1:8000`

## Avertissements

- **Ne pas abuser** : Limitez le nombre de concours surveillés (5-20 max)
- **Usage personnel** : Cet outil est destiné à un usage personnel
- **Pas d'engagement automatique** : L'outil ne fait que surveiller

## Support

En cas de problème, vérifiez les logs dans le terminal où l'application est lancée.
