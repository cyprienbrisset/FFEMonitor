/**
 * FFE Monitor - Client Supabase Frontend
 * Gère l'authentification et les appels à Supabase
 */

// Configuration Supabase (injectée par le backend)
const SUPABASE_URL = window.SUPABASE_URL || '';
const SUPABASE_ANON_KEY = window.SUPABASE_ANON_KEY || '';

// Instance Supabase globale
let supabaseClient = null;

/**
 * Initialise le client Supabase
 */
function initSupabase() {
    if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
        console.error('[Supabase] Configuration manquante');
        return null;
    }

    if (!supabaseClient && window.supabase) {
        supabaseClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
            auth: {
                autoRefreshToken: true,
                persistSession: true,
                storage: window.localStorage,
            },
        });
        console.log('[Supabase] Client initialisé');
    }

    return supabaseClient;
}

/**
 * Récupère la session courante
 */
async function getSession() {
    const client = initSupabase();
    if (!client) return null;

    const { data: { session }, error } = await client.auth.getSession();
    if (error) {
        console.error('[Supabase] Erreur getSession:', error);
        return null;
    }
    return session;
}

/**
 * Récupère l'utilisateur courant
 */
async function getCurrentUser() {
    const client = initSupabase();
    if (!client) return null;

    const { data: { user }, error } = await client.auth.getUser();
    if (error) {
        console.error('[Supabase] Erreur getUser:', error);
        return null;
    }
    return user;
}

/**
 * Inscription avec email et mot de passe
 */
async function signUp(email, password) {
    const client = initSupabase();
    if (!client) throw new Error('Supabase non initialisé');

    const { data, error } = await client.auth.signUp({
        email,
        password,
    });

    if (error) throw error;
    return data;
}

/**
 * Connexion avec email et mot de passe
 */
async function signIn(email, password) {
    const client = initSupabase();
    if (!client) throw new Error('Supabase non initialisé');

    const { data, error } = await client.auth.signInWithPassword({
        email,
        password,
    });

    if (error) throw error;
    return data;
}

/**
 * Déconnexion
 */
async function signOut() {
    const client = initSupabase();
    if (!client) throw new Error('Supabase non initialisé');

    const { error } = await client.auth.signOut();
    if (error) throw error;
}

/**
 * Récupère le token d'accès pour les appels API
 */
async function getAccessToken() {
    const session = await getSession();
    return session?.access_token || null;
}

/**
 * Écoute les changements d'authentification
 */
function onAuthStateChange(callback) {
    const client = initSupabase();
    if (!client) return null;

    return client.auth.onAuthStateChange((event, session) => {
        console.log('[Supabase] Auth state change:', event);
        callback(event, session);
    });
}

/**
 * Réinitialisation du mot de passe
 */
async function resetPassword(email) {
    const client = initSupabase();
    if (!client) throw new Error('Supabase non initialisé');

    const { data, error } = await client.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/reset-password`,
    });

    if (error) throw error;
    return data;
}

/**
 * Mise à jour du mot de passe
 */
async function updatePassword(newPassword) {
    const client = initSupabase();
    if (!client) throw new Error('Supabase non initialisé');

    const { data, error } = await client.auth.updateUser({
        password: newPassword,
    });

    if (error) throw error;
    return data;
}

// Export global pour utilisation dans app.js
window.SupabaseAuth = {
    init: initSupabase,
    getSession,
    getCurrentUser,
    signUp,
    signIn,
    signOut,
    getAccessToken,
    onAuthStateChange,
    resetPassword,
    updatePassword,
};
