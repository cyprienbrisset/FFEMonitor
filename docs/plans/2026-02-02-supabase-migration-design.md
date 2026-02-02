# FFE Monitor - Migration Supabase & PWA

**Date** : 2 février 2026
**Statut** : Validé

---

## Résumé

Migration de FFE Monitor vers une architecture multi-utilisateurs avec :
- **Supabase** pour l'authentification et la base de données
- **OneSignal** pour les push notifications
- **PWA** pour l'installation sur mobile/desktop
- **Plans tarifaires** (Free/Premium/Pro) avec délais de notification différenciés

---

## Décisions Clés

| Aspect | Décision |
|--------|----------|
| Gestion des plans | Manuelle (admin assigne via Supabase) |
| Push notifications | OneSignal |
| Table concours | Partagée, surveillance globale |
| Service surveillance | Backend FastAPI existant |
| PWA offline | App-shell only (UI cachée, données online) |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (PWA)                          │
│  HTML/CSS/JS + Service Worker + OneSignal + Supabase Client     │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      SUPABASE (Cloud)                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │    Auth     │  │  PostgreSQL │  │  Realtime   │             │
│  │  (JWT)      │  │   Database  │  │  WebSocket  │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI)                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ Surveillance│  │  Scraper    │  │ Notification│             │
│  │   Service   │  │   FFE       │  │   Dispatcher│             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                         │                                       │
│                         ▼                                       │
│              OneSignal + Telegram + Email                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Schéma Base de Données

### Table `profiles`
Extension des utilisateurs Supabase Auth.

```sql
CREATE TABLE profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    plan TEXT DEFAULT 'free' CHECK (plan IN ('free', 'premium', 'pro')),
    onesignal_player_id TEXT,
    telegram_chat_id TEXT,
    notification_email BOOLEAN DEFAULT true,
    notification_push BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Table `concours`
Table partagée, unique par numéro.

```sql
CREATE TABLE concours (
    numero INTEGER PRIMARY KEY,
    nom TEXT,
    lieu TEXT,
    date_debut DATE,
    date_fin DATE,
    discipline TEXT,
    statut TEXT DEFAULT 'previsionnel',
    is_open BOOLEAN DEFAULT false,
    opened_at TIMESTAMPTZ,
    last_check TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Table `subscriptions`
Lie les utilisateurs aux concours surveillés.

```sql
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    concours_numero INTEGER REFERENCES concours(numero) ON DELETE CASCADE,
    notified BOOLEAN DEFAULT false,
    notified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, concours_numero)
);
```

### Table `notification_queue`
File d'attente pour les notifications différées.

```sql
CREATE TABLE notification_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    concours_numero INTEGER REFERENCES concours(numero),
    plan TEXT NOT NULL,
    send_at TIMESTAMPTZ NOT NULL,
    sent BOOLEAN DEFAULT false,
    sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_notification_queue_pending
ON notification_queue(send_at)
WHERE sent = false;
```

### Table `notification_log`
Historique des notifications envoyées.

```sql
CREATE TABLE notification_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES profiles(id),
    concours_numero INTEGER REFERENCES concours(numero),
    channel TEXT,
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    plan TEXT,
    delay_seconds INTEGER
);
```

---

## Délais par Plan

| Plan | Délai | Secondes |
|------|-------|----------|
| Free | 10 minutes | 600 |
| Premium | 1 minute | 60 |
| Pro | 10 secondes | 10 |

---

## Flux de Notification

1. **Surveillance** (toutes les 5 sec) détecte qu'un concours ouvre
2. **Mise à jour** : `concours.is_open = true`, `opened_at = NOW()`
3. **Dispatcher** récupère tous les abonnés du concours
4. **Queue** : Pour chaque abonné, insère dans `notification_queue` avec `send_at = opened_at + délai_plan`
5. **Worker** (boucle continue) :
   - Sélectionne les notifications où `send_at <= NOW()` et `sent = false`
   - Envoie via OneSignal (push), Email, Telegram selon préférences
   - Marque `sent = true`
6. **Log** : Enregistre dans `notification_log`

---

## Authentification

### Trigger création profile
```sql
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO profiles (id, email, plan)
    VALUES (NEW.id, NEW.email, 'free');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION handle_new_user();
```

### Row Level Security
```sql
-- Profiles : users voient/modifient leur propre profile
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users manage own profile" ON profiles
    FOR ALL USING (auth.uid() = id);

-- Subscriptions : users gèrent leurs propres abonnements
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users manage own subscriptions" ON subscriptions
    FOR ALL USING (auth.uid() = user_id);

-- Concours : lecture pour tous les authentifiés
ALTER TABLE concours ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Authenticated read concours" ON concours
    FOR SELECT USING (auth.role() = 'authenticated');

-- Concours : écriture uniquement via service_role (backend)
CREATE POLICY "Service write concours" ON concours
    FOR ALL USING (auth.role() = 'service_role');
```

---

## PWA

### manifest.json
```json
{
    "name": "FFE Monitor",
    "short_name": "FFE Monitor",
    "description": "Surveillance des concours FFE",
    "start_url": "/app",
    "display": "standalone",
    "background_color": "#1A1A1A",
    "theme_color": "#722F37",
    "icons": [
        { "src": "/static/icons/icon-192.png", "sizes": "192x192", "type": "image/png" },
        { "src": "/static/icons/icon-512.png", "sizes": "512x512", "type": "image/png" }
    ]
}
```

### Service Worker
- **Cache** : HTML, CSS, JS, images, fonts
- **Stratégie** : Cache-first pour assets statiques, Network-first pour API
- **Offline** : Affiche page "Hors ligne" si pas de réseau

### OneSignal Integration
```javascript
OneSignal.init({ appId: "ONESIGNAL_APP_ID" });

// Après connexion Supabase
OneSignal.getUserId(async (playerId) => {
    await supabase
        .from('profiles')
        .update({ onesignal_player_id: playerId })
        .eq('id', user.id);
});
```

---

## Backend (Modifications)

### Nouvelles dépendances
```
supabase>=2.0.0
onesignal-sdk>=2.0.0
python-jose>=3.3.0
```

### Configuration
```env
# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_KEY=eyJ...
SUPABASE_JWT_SECRET=your-jwt-secret

# OneSignal
ONESIGNAL_APP_ID=xxx
ONESIGNAL_API_KEY=xxx
```

### Structure modifiée
```
backend/
├── config.py                 # + variables Supabase/OneSignal
├── supabase_client.py        # Client Supabase singleton
├── routers/
│   ├── concours.py           # Modifié → Supabase
│   └── subscriptions.py      # NOUVEAU
├── services/
│   ├── surveillance.py       # Modifié → Supabase
│   ├── notification.py       # Modifié → + OneSignal + queue
│   └── scraper.py            # Inchangé
└── middleware/
    └── supabase_auth.py      # Vérifie JWT Supabase
```

### Nouveaux endpoints
```
POST   /subscriptions/{numero}    # S'abonner à un concours
DELETE /subscriptions/{numero}    # Se désabonner
GET    /subscriptions             # Lister ses abonnements
GET    /profile                   # Récupérer son profile
PATCH  /profile                   # Modifier préférences notifications
```

---

## Plan d'Implémentation

### Phase 1 : Supabase Setup
1. Créer projet Supabase
2. Créer les tables et triggers
3. Configurer RLS
4. Tester via dashboard

### Phase 2 : Backend Migration
5. Ajouter client Supabase
6. Modifier surveillance → Supabase
7. Créer notification queue/worker
8. Intégrer OneSignal
9. Créer endpoints subscriptions

### Phase 3 : Frontend Migration
10. Intégrer Supabase Auth
11. Refaire pages login/signup
12. Modifier app.html → subscriptions
13. Setup PWA (manifest, SW)
14. Intégrer OneSignal SDK

### Phase 4 : Tests & Deploy
15. Tests E2E
16. Déployer backend
17. Configurer domaine PWA
18. Tests production

---

## Fichiers à Créer/Modifier

| Fichier | Action |
|---------|--------|
| `backend/supabase_client.py` | Créer |
| `backend/middleware/supabase_auth.py` | Créer |
| `backend/routers/subscriptions.py` | Créer |
| `backend/services/notification.py` | Modifier (+ OneSignal + queue) |
| `backend/services/surveillance.py` | Modifier (Supabase) |
| `backend/config.py` | Modifier (+ Supabase/OneSignal) |
| `frontend/manifest.json` | Créer |
| `frontend/sw.js` | Créer |
| `frontend/login.html` | Refaire (Supabase Auth) |
| `frontend/app.html` | Modifier (subscriptions) |
| `frontend/js/supabase-client.js` | Créer |
| `frontend/js/onesignal-init.js` | Créer |

---

## Risques & Mitigations

| Risque | Mitigation |
|--------|------------|
| Latence Supabase | Backend et Supabase dans même région |
| OneSignal rate limits | Batch les notifications |
| JWT expiration | Auto-refresh côté client |
| Données FFE scraping | Garder fallback Playwright |
