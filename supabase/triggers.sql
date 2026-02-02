-- FFE Monitor - Triggers et fonctions Supabase
-- À exécuter après schema.sql

-- ============================================================================
-- TRIGGER: Création automatique du profil utilisateur
-- Crée un profil dans la table profiles quand un utilisateur s'inscrit
-- ============================================================================
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO profiles (id, email, plan)
    VALUES (NEW.id, NEW.email, 'free');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Supprimer le trigger s'il existe déjà
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

-- Créer le trigger
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- ============================================================================
-- TRIGGER: Mise à jour automatique de updated_at sur profiles
-- ============================================================================
CREATE OR REPLACE FUNCTION handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS on_profiles_updated ON profiles;

CREATE TRIGGER on_profiles_updated
    BEFORE UPDATE ON profiles
    FOR EACH ROW EXECUTE FUNCTION handle_updated_at();

-- ============================================================================
-- TRIGGER: Mise à jour automatique de last_check sur concours
-- ============================================================================
CREATE OR REPLACE FUNCTION update_concours_last_check()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_check = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS on_concours_check ON concours;

CREATE TRIGGER on_concours_check
    BEFORE UPDATE ON concours
    FOR EACH ROW
    WHEN (OLD.statut IS DISTINCT FROM NEW.statut OR OLD.is_open IS DISTINCT FROM NEW.is_open)
    EXECUTE FUNCTION update_concours_last_check();
