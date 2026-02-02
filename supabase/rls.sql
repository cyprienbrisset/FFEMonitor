-- FFE Monitor - Row Level Security (RLS) Policies
-- À exécuter après triggers.sql

-- ============================================================================
-- PROFILES: Les utilisateurs gèrent leur propre profil
-- ============================================================================
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- Supprimer les policies existantes
DROP POLICY IF EXISTS "Users can view own profile" ON profiles;
DROP POLICY IF EXISTS "Users can update own profile" ON profiles;

-- Les utilisateurs peuvent voir leur propre profil
CREATE POLICY "Users can view own profile" ON profiles
    FOR SELECT
    USING (auth.uid() = id);

-- Les utilisateurs peuvent modifier leur propre profil
CREATE POLICY "Users can update own profile" ON profiles
    FOR UPDATE
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- ============================================================================
-- CONCOURS: Lecture pour tous les authentifiés, écriture via service_role
-- ============================================================================
ALTER TABLE concours ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Authenticated users can read concours" ON concours;
DROP POLICY IF EXISTS "Service role can manage concours" ON concours;

-- Tous les utilisateurs authentifiés peuvent lire les concours
CREATE POLICY "Authenticated users can read concours" ON concours
    FOR SELECT
    USING (auth.role() = 'authenticated');

-- Le service_role (backend) peut tout faire sur les concours
CREATE POLICY "Service role can manage concours" ON concours
    FOR ALL
    USING (auth.role() = 'service_role');

-- ============================================================================
-- SUBSCRIPTIONS: Les utilisateurs gèrent leurs propres abonnements
-- ============================================================================
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own subscriptions" ON subscriptions;
DROP POLICY IF EXISTS "Users can insert own subscriptions" ON subscriptions;
DROP POLICY IF EXISTS "Users can delete own subscriptions" ON subscriptions;
DROP POLICY IF EXISTS "Service role can manage subscriptions" ON subscriptions;

-- Les utilisateurs peuvent voir leurs propres abonnements
CREATE POLICY "Users can view own subscriptions" ON subscriptions
    FOR SELECT
    USING (auth.uid() = user_id);

-- Les utilisateurs peuvent créer leurs propres abonnements
CREATE POLICY "Users can insert own subscriptions" ON subscriptions
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Les utilisateurs peuvent supprimer leurs propres abonnements
CREATE POLICY "Users can delete own subscriptions" ON subscriptions
    FOR DELETE
    USING (auth.uid() = user_id);

-- Le service_role peut tout gérer
CREATE POLICY "Service role can manage subscriptions" ON subscriptions
    FOR ALL
    USING (auth.role() = 'service_role');

-- ============================================================================
-- NOTIFICATION_QUEUE: Gestion uniquement via service_role
-- ============================================================================
ALTER TABLE notification_queue ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Service role manages notification queue" ON notification_queue;

-- Seul le service_role peut gérer la file de notifications
CREATE POLICY "Service role manages notification queue" ON notification_queue
    FOR ALL
    USING (auth.role() = 'service_role');

-- ============================================================================
-- NOTIFICATION_LOG: Lecture pour les utilisateurs, écriture via service_role
-- ============================================================================
ALTER TABLE notification_log ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own notification log" ON notification_log;
DROP POLICY IF EXISTS "Service role manages notification log" ON notification_log;

-- Les utilisateurs peuvent voir leur propre historique
CREATE POLICY "Users can view own notification log" ON notification_log
    FOR SELECT
    USING (auth.uid() = user_id);

-- Le service_role peut tout gérer
CREATE POLICY "Service role manages notification log" ON notification_log
    FOR ALL
    USING (auth.role() = 'service_role');
