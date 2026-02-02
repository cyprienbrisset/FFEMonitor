-- FFE Monitor - Schéma de base de données Supabase
-- À exécuter dans l'éditeur SQL de Supabase Dashboard

-- ============================================================================
-- TABLE: profiles
-- Extension des utilisateurs Supabase Auth
-- ============================================================================
CREATE TABLE IF NOT EXISTS profiles (
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

-- Index pour recherche par email
CREATE INDEX IF NOT EXISTS idx_profiles_email ON profiles(email);

-- ============================================================================
-- TABLE: concours
-- Table partagée, unique par numéro de concours FFE
-- ============================================================================
CREATE TABLE IF NOT EXISTS concours (
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

-- Index pour les concours ouverts
CREATE INDEX IF NOT EXISTS idx_concours_is_open ON concours(is_open) WHERE is_open = true;

-- Index pour les dates
CREATE INDEX IF NOT EXISTS idx_concours_dates ON concours(date_debut, date_fin);

-- ============================================================================
-- TABLE: subscriptions
-- Lie les utilisateurs aux concours qu'ils surveillent
-- ============================================================================
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    concours_numero INTEGER NOT NULL REFERENCES concours(numero) ON DELETE CASCADE,
    notified BOOLEAN DEFAULT false,
    notified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, concours_numero)
);

-- Index pour les abonnements d'un utilisateur
CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON subscriptions(user_id);

-- Index pour les abonnés d'un concours
CREATE INDEX IF NOT EXISTS idx_subscriptions_concours ON subscriptions(concours_numero);

-- ============================================================================
-- TABLE: notification_queue
-- File d'attente pour les notifications différées selon le plan
-- ============================================================================
CREATE TABLE IF NOT EXISTS notification_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    concours_numero INTEGER NOT NULL REFERENCES concours(numero),
    plan TEXT NOT NULL,
    send_at TIMESTAMPTZ NOT NULL,
    sent BOOLEAN DEFAULT false,
    sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index pour les notifications en attente
CREATE INDEX IF NOT EXISTS idx_notification_queue_pending
ON notification_queue(send_at)
WHERE sent = false;

-- ============================================================================
-- TABLE: notification_log
-- Historique des notifications envoyées
-- ============================================================================
CREATE TABLE IF NOT EXISTS notification_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES profiles(id),
    concours_numero INTEGER REFERENCES concours(numero),
    channel TEXT NOT NULL,
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    plan TEXT,
    delay_seconds INTEGER
);

-- Index pour l'historique par utilisateur
CREATE INDEX IF NOT EXISTS idx_notification_log_user ON notification_log(user_id);

-- Index pour l'historique par concours
CREATE INDEX IF NOT EXISTS idx_notification_log_concours ON notification_log(concours_numero);
