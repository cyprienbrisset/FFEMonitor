# CLAUDE.md - Guide de développement EngageWatch

## Vue d'ensemble du projet

**EngageWatch** est un outil de surveillance d'ouverture des concours équestres FFE (Fédération Française d'Équitation). Il permet aux cavaliers et gestionnaires d'écurie de recevoir des notifications instantanées dès l'ouverture des engagements sur https://ffecompet.ffe.com/concours.

### Problème résolu

Les engagements aux concours FFE ouvrent à des moments variables et les places sont limitées. Cet outil automatise la surveillance et notifie l'utilisateur dès l'apparition des boutons "Engager" (amateur) ou "Demande de participation" (international).

### Public cible

- **Utilisateurs finaux** : Cavaliers / gestionnaires d'écurie (niveau technique faible)
- **Utilisateurs techniques** : Développeurs qui déploient et maintiennent l'outil

---

## Stack technique

| Composant | Technologie | Justification |
|-----------|-------------|---------------|
| Backend | **Python 3.10+** | Écosystème riche, async natif |
| Framework web | **FastAPI** | Performance, async, documentation auto |
| Automatisation | **Playwright** | Gestion JS, cookies, sessions, anti-bot |
| Base de données | **SQLite** | Simplicité, stockage local, sans config |
| Frontend | **HTML/CSS/JS minimal** | Légèreté, pas de build nécessaire |
| Notifications | **Telegram** (prioritaire) | Push instantané, API simple |

---

## Structure du projet

```
FFEM/
├── backend/
│   ├── __init__.py
│   ├── main.py              # Application FastAPI, point d'entrée
│   ├── config.py            # Configuration (env vars, constantes)
│   ├── database.py          # Connexion SQLite, modèles
│   ├── models.py            # Modèles Pydantic
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── concours.py      # Routes CRUD concours
│   │   └── health.py        # Route /health
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth.py          # Authentification FFE via Playwright
│   │   ├── surveillance.py  # Boucle de surveillance asynchrone
│   │   └── notification.py  # Envoi notifications Telegram
│   └── utils/
│       ├── __init__.py
│       └── logger.py        # Configuration logging
├── frontend/
│   ├── index.html           # Interface principale
│   ├── style.css            # Styles minimalistes
│   └── app.js               # Logique frontend (fetch API)
├── data/
│   ├── engagewatch.db       # Base SQLite (gitignore)
│   └── cookies.json         # Cookies session FFE (gitignore)
├── tests/
│   ├── __init__.py
│   ├── test_api.py
│   ├── test_surveillance.py
│   └── test_notification.py
├── .env                     # Variables d'environnement (gitignore)
├── .env.example             # Template des variables
├── requirements.txt         # Dépendances Python
├── run.py                   # Script de lancement unifié
├── PRD.MD                   # Product Requirements Document
├── BACKLOG.md               # Backlog détaillé
├── claude.md                # Ce fichier
└── README.md                # Documentation utilisateur
```

---

## Modèle de données

### Table `concours`

| Champ | Type | Description |
|-------|------|-------------|
| `id` | INTEGER | Clé primaire auto-incrémentée |
| `numero` | INTEGER | Numéro unique du concours FFE |
| `statut` | TEXT | `ferme`, `engagement`, `demande` |
| `notifie` | BOOLEAN | Notification déjà envoyée |
| `last_check` | DATETIME | Dernière vérification |
| `created_at` | DATETIME | Date d'ajout à la surveillance |

---

## API REST (FastAPI)

### Endpoints

| Méthode | Route | Description |
|---------|-------|-------------|
| `GET` | `/health` | État de santé de l'application |
| `GET` | `/concours` | Liste tous les concours surveillés |
| `POST` | `/concours` | Ajoute un concours (body: `{"numero": 123456}`) |
| `DELETE` | `/concours/{numero}` | Retire un concours de la surveillance |
| `GET` | `/status` | État global (connexion FFE, surveillance active) |

### Schémas Pydantic

```python
class ConcoursCreate(BaseModel):
    numero: int

class ConcoursResponse(BaseModel):
    id: int
    numero: int
    statut: str  # "ferme" | "engagement" | "demande"
    notifie: bool
    last_check: datetime | None

class HealthResponse(BaseModel):
    status: str  # "ok"
    ffe_connected: bool
    surveillance_active: bool
    concours_count: int
```

---

## Règles métier critiques

### Détection d'ouverture

| Type de concours | Indicateur DOM | Statut résultant |
|------------------|----------------|------------------|
| Amateur | Bouton "Engager" | `engagement` |
| International | Bouton "Demande de participation" | `demande` |
| Non ouvert | Aucun bouton | `ferme` |

### Notifications

1. **Une seule notification par concours** : Mettre `notifie = True` après envoi
2. **Contenu obligatoire** :
   - Numéro du concours
   - Type d'ouverture (Engagement / Demande)
   - Lien direct : `https://ffecompet.ffe.com/concours/{numero}`
3. **Délai** : < 2 secondes après détection

### Surveillance

- **Intervalle** : 5-10 secondes entre chaque vérification
- **Capacité** : 5-20 concours simultanés
- **Reconnexion** : Automatique et transparente si session expirée

---

## Configuration

### Variables d'environnement (`.env`)

```env
# Identifiants FFE
FFE_USERNAME=votre_email@example.com
FFE_PASSWORD=votre_mot_de_passe

# Telegram
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxYZ
TELEGRAM_CHAT_ID=987654321

# Application
CHECK_INTERVAL=5           # Secondes entre chaque vérification
LOG_LEVEL=INFO             # DEBUG, INFO, WARNING, ERROR
DATABASE_PATH=data/engagewatch.db
COOKIES_PATH=data/cookies.json
```

---

## Conventions de code

### Python

- **Style** : PEP 8, formaté avec `black`
- **Type hints** : Obligatoires sur toutes les fonctions
- **Docstrings** : Format Google pour les fonctions publiques
- **Async** : Utiliser `async/await` pour toutes les opérations I/O

### Nommage

- **Variables/fonctions** : `snake_case`
- **Classes** : `PascalCase`
- **Constantes** : `UPPER_SNAKE_CASE`
- **Fichiers** : `snake_case.py`

### Imports

```python
# Ordre : stdlib, third-party, local
import asyncio
from datetime import datetime

from fastapi import FastAPI, HTTPException
from playwright.async_api import async_playwright

from backend.services.auth import FFEAuthenticator
```

### Gestion des erreurs

```python
# Toujours logger les erreurs avec contexte
try:
    await page.goto(url)
except Exception as e:
    logger.error(f"Erreur navigation vers {url}: {e}")
    raise
```

---

## Patterns d'implémentation

### Service d'authentification FFE

```python
class FFEAuthenticator:
    """Gère l'authentification au site FFE via Playwright."""

    def __init__(self, username: str, password: str, cookies_path: str):
        self.username = username
        self.password = password
        self.cookies_path = Path(cookies_path)
        self.browser = None
        self.context = None
        self.page = None

    async def login(self) -> bool:
        """Effectue la connexion ou charge les cookies existants."""
        pass

    async def is_session_valid(self) -> bool:
        """Vérifie si la session actuelle est toujours valide."""
        pass

    async def reconnect(self) -> bool:
        """Reconnexion automatique si session expirée."""
        pass
```

### Service de surveillance

```python
class SurveillanceService:
    """Boucle de surveillance asynchrone des concours."""

    def __init__(self, auth: FFEAuthenticator, db: Database, notifier: Notifier):
        self.auth = auth
        self.db = db
        self.notifier = notifier
        self.running = False

    async def start(self):
        """Démarre la boucle de surveillance."""
        self.running = True
        while self.running:
            concours_list = await self.db.get_all_concours()
            for concours in concours_list:
                if not concours.notifie:
                    await self.check_concours(concours)
            await asyncio.sleep(CHECK_INTERVAL)

    async def check_concours(self, concours: Concours) -> str:
        """Vérifie l'état d'un concours et notifie si ouvert."""
        pass
```

### Détection DOM

```python
# Sélecteurs pour détecter l'ouverture
SELECTORS = {
    "engager": "button:has-text('Engager'), a:has-text('Engager')",
    "demande": "button:has-text('Demande de participation'), a:has-text('Demande de participation')"
}

async def detect_opening(page: Page) -> str | None:
    """Retourne 'engagement', 'demande' ou None."""
    if await page.locator(SELECTORS["engager"]).count() > 0:
        return "engagement"
    if await page.locator(SELECTORS["demande"]).count() > 0:
        return "demande"
    return None
```

---

## Commandes de développement

```bash
# Installation
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate sur Windows
pip install -r requirements.txt
playwright install chromium

# Lancement
python run.py

# Tests
pytest tests/ -v

# Formatage
black backend/
isort backend/

# Lint
flake8 backend/
mypy backend/
```

---

## Dépendances (requirements.txt)

```
fastapi>=0.100.0
uvicorn[standard]>=0.23.0
playwright>=1.40.0
aiosqlite>=0.19.0
python-telegram-bot>=20.0
python-dotenv>=1.0.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
httpx>=0.25.0

# Dev
pytest>=7.4.0
pytest-asyncio>=0.21.0
black>=23.0.0
isort>=5.12.0
flake8>=6.1.0
mypy>=1.5.0
```

---

## Points de vigilance

### Fragilité du scraping

- Le site FFE peut changer sans préavis
- **Toujours** utiliser des sélecteurs résilients (texte plutôt que classes)
- Implémenter des fallbacks et une journalisation détaillée

### Rate limiting

- Ne pas surcharger le serveur FFE
- Respecter un intervalle minimum de 5 secondes
- Implémenter un backoff exponentiel en cas d'erreurs

### Sécurité

- **Ne jamais** committer `.env`, `cookies.json`, ou `engagewatch.db`
- Les identifiants FFE restent stockés localement uniquement
- Aucune automatisation d'engagement (hors périmètre)

### Session FFE

- Les cookies peuvent expirer
- Toujours vérifier la validité avant chaque cycle
- Reconnexion silencieuse sans interrompre la surveillance

---

## Workflow de développement

### Priorité d'implémentation (MoSCoW)

**Must Have (v1)**
1. Authentification FFE fonctionnelle
2. Surveillance des concours par numéro
3. Notification unique via Telegram
4. Interface web simple

**Should Have**
- Reconnexion automatique
- Logs détaillés
- Gestion des erreurs réseau

**Could Have**
- Autres canaux de notification (email, webhook)
- Filtres avancés

**Won't Have (v1)**
- Engagement automatique
- Application mobile
- Multi-comptes FFE

### Definition of Done

- [ ] Code fonctionnel sans intervention manuelle
- [ ] Interface utilisable par un non-technique
- [ ] Notification envoyée à l'ouverture réelle
- [ ] Pas de doublons de notification
- [ ] Application stable sur plusieurs heures

---

## URLs de référence

- **Site FFE Compétitions** : https://ffecompet.ffe.com/concours
- **Page concours** : `https://ffecompet.ffe.com/concours/{numero}`
- **API Telegram Bot** : https://core.telegram.org/bots/api

---

## Notes pour Claude

Lors du développement :

1. **Toujours vérifier** l'existence des fichiers avant modification
2. **Préférer** les modifications incrémentales aux réécritures complètes
3. **Tester** chaque composant isolément avant intégration
4. **Logger** abondamment pour faciliter le debug
5. **Ne jamais** hardcoder les identifiants ou tokens
6. **Respecter** la structure de dossiers définie
7. **Documenter** les changements de sélecteurs DOM si le site FFE évolue
