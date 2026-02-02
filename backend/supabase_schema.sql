-- ============================================================================
-- FFE Monitor - Schéma Supabase
-- À exécuter dans le SQL Editor de Supabase
-- ============================================================================

-- 1. Table des profils utilisateurs (extension de auth.users)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    email TEXT,
    plan TEXT DEFAULT 'free' CHECK (plan IN ('free', 'premium', 'pro')),
    onesignal_player_id TEXT,
    telegram_chat_id TEXT,
    notification_email BOOLEAN DEFAULT true,
    notification_push BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Trigger pour créer automatiquement un profil à l'inscription
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email)
    VALUES (NEW.id, NEW.email);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- 2. Table des concours
CREATE TABLE IF NOT EXISTS public.concours (
    id BIGSERIAL PRIMARY KEY,
    numero INTEGER UNIQUE NOT NULL,
    nom TEXT,
    statut TEXT DEFAULT 'ferme' CHECK (statut IN ('ferme', 'engagement', 'demande')),
    is_open BOOLEAN DEFAULT false,
    opened_at TIMESTAMPTZ,
    notifie BOOLEAN DEFAULT false,
    last_check TIMESTAMPTZ,
    date_debut DATE,
    date_fin DATE,
    lieu TEXT,
    discipline TEXT,
    organisateur TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index pour les recherches
CREATE INDEX IF NOT EXISTS idx_concours_numero ON public.concours(numero);
CREATE INDEX IF NOT EXISTS idx_concours_statut ON public.concours(statut);
CREATE INDEX IF NOT EXISTS idx_concours_date_debut ON public.concours(date_debut);

-- 3. Table des abonnements utilisateur -> concours
CREATE TABLE IF NOT EXISTS public.subscriptions (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    concours_numero INTEGER REFERENCES public.concours(numero) ON DELETE CASCADE NOT NULL,
    notified BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, concours_numero)
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON public.subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_concours ON public.subscriptions(concours_numero);

-- 4. File d'attente des notifications
CREATE TABLE IF NOT EXISTS public.notification_queue (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    concours_numero INTEGER REFERENCES public.concours(numero) ON DELETE CASCADE NOT NULL,
    plan TEXT NOT NULL,
    send_at TIMESTAMPTZ NOT NULL,
    sent BOOLEAN DEFAULT false,
    sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notification_queue_pending ON public.notification_queue(sent, send_at);

-- 5. Historique des notifications envoyées
CREATE TABLE IF NOT EXISTS public.notification_log (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    concours_numero INTEGER NOT NULL,
    channel TEXT NOT NULL, -- 'push', 'email', 'telegram'
    plan TEXT NOT NULL,
    delay_seconds INTEGER NOT NULL,
    sent_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notification_log_user ON public.notification_log(user_id);

-- 6. Historique des vérifications (pour stats)
CREATE TABLE IF NOT EXISTS public.check_history (
    id BIGSERIAL PRIMARY KEY,
    concours_numero INTEGER NOT NULL,
    checked_at TIMESTAMPTZ DEFAULT NOW(),
    statut_before TEXT,
    statut_after TEXT,
    response_time_ms INTEGER,
    success BOOLEAN DEFAULT true
);

CREATE INDEX IF NOT EXISTS idx_check_history_concours ON public.check_history(concours_numero);
CREATE INDEX IF NOT EXISTS idx_check_history_date ON public.check_history(checked_at);

-- 7. Événements d'ouverture
CREATE TABLE IF NOT EXISTS public.opening_events (
    id BIGSERIAL PRIMARY KEY,
    concours_numero INTEGER NOT NULL,
    opened_at TIMESTAMPTZ DEFAULT NOW(),
    statut TEXT NOT NULL,
    notification_sent_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_opening_events_concours ON public.opening_events(concours_numero);

-- ============================================================================
-- Row Level Security (RLS)
-- ============================================================================

-- Activer RLS sur toutes les tables
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.concours ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notification_queue ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notification_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.check_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.opening_events ENABLE ROW LEVEL SECURITY;

-- Policies pour profiles
CREATE POLICY "Users can view own profile" ON public.profiles
    FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON public.profiles
    FOR UPDATE USING (auth.uid() = id);

-- Policies pour concours (lecture publique, écriture admin)
CREATE POLICY "Anyone can view concours" ON public.concours
    FOR SELECT USING (true);
CREATE POLICY "Service role can manage concours" ON public.concours
    FOR ALL USING (auth.role() = 'service_role');

-- Policies pour subscriptions
CREATE POLICY "Users can view own subscriptions" ON public.subscriptions
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can manage own subscriptions" ON public.subscriptions
    FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Service role can manage all subscriptions" ON public.subscriptions
    FOR ALL USING (auth.role() = 'service_role');

-- Policies pour notification_queue (service role only)
CREATE POLICY "Service role can manage notification_queue" ON public.notification_queue
    FOR ALL USING (auth.role() = 'service_role');

-- Policies pour notification_log
CREATE POLICY "Users can view own notification_log" ON public.notification_log
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Service role can manage notification_log" ON public.notification_log
    FOR ALL USING (auth.role() = 'service_role');

-- Policies pour check_history (service role only)
CREATE POLICY "Service role can manage check_history" ON public.check_history
    FOR ALL USING (auth.role() = 'service_role');

-- Policies pour opening_events (service role only)
CREATE POLICY "Service role can manage opening_events" ON public.opening_events
    FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- Fonctions utilitaires
-- ============================================================================

-- Fonction pour mettre à jour updated_at automatiquement
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers pour updated_at
DROP TRIGGER IF EXISTS update_profiles_updated_at ON public.profiles;
CREATE TRIGGER update_profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

DROP TRIGGER IF EXISTS update_concours_updated_at ON public.concours;
CREATE TRIGGER update_concours_updated_at
    BEFORE UPDATE ON public.concours
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();
