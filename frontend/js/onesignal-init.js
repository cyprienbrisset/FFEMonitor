/**
 * FFE Monitor - Initialisation OneSignal
 * Gère les push notifications via OneSignal
 */

// Configuration OneSignal (injectée par le backend)
const ONESIGNAL_APP_ID = window.ONESIGNAL_APP_ID || '';

/**
 * Initialise OneSignal
 */
async function initOneSignal() {
    if (!ONESIGNAL_APP_ID) {
        console.log('[OneSignal] App ID non configuré, notifications push désactivées');
        return;
    }

    // Attendre que le SDK soit chargé
    if (typeof OneSignal === 'undefined') {
        console.log('[OneSignal] SDK non chargé');
        return;
    }

    try {
        await OneSignal.init({
            appId: ONESIGNAL_APP_ID,
            allowLocalhostAsSecureOrigin: true, // Pour le dev local
            notifyButton: {
                enable: false, // On gère notre propre UI
            },
            welcomeNotification: {
                disable: true, // On envoie notre propre message de bienvenue
            },
        });

        console.log('[OneSignal] Initialisé');

        // Écouter les changements de permission
        OneSignal.Notifications.addEventListener('permissionChange', (permission) => {
            console.log('[OneSignal] Permission changée:', permission);
            if (permission) {
                registerPlayer();
            }
        });

        // Vérifier si déjà enregistré
        const permission = await OneSignal.Notifications.permission;
        console.log('[OneSignal] Permission actuelle:', permission);

    } catch (error) {
        console.error('[OneSignal] Erreur initialisation:', error);
    }
}

/**
 * Demande la permission pour les notifications
 */
async function requestNotificationPermission() {
    if (typeof OneSignal === 'undefined') {
        console.log('[OneSignal] SDK non disponible');
        return false;
    }

    try {
        // Vérifier si déjà autorisé
        const currentPermission = await OneSignal.Notifications.permission;
        if (currentPermission) {
            console.log('[OneSignal] Déjà autorisé');
            await registerPlayer();
            return true;
        }

        // Demander la permission
        await OneSignal.Notifications.requestPermission();

        const permission = await OneSignal.Notifications.permission;
        console.log('[OneSignal] Nouvelle permission:', permission);

        if (permission) {
            await registerPlayer();
            return true;
        }

        return false;

    } catch (error) {
        console.error('[OneSignal] Erreur demande permission:', error);
        return false;
    }
}

/**
 * Enregistre le player ID auprès du backend
 */
async function registerPlayer() {
    if (typeof OneSignal === 'undefined') return;

    try {
        const playerId = await OneSignal.User.PushSubscription.id;

        if (!playerId) {
            console.log('[OneSignal] Pas de player ID disponible');
            return;
        }

        console.log('[OneSignal] Player ID:', playerId);

        // Envoyer au backend pour l'associer au profil utilisateur
        const token = await window.SupabaseAuth?.getAccessToken();
        if (!token) {
            console.log('[OneSignal] Pas de token, impossible d\'enregistrer le player');
            return;
        }

        const response = await fetch('/subscriptions/profile', {
            method: 'PATCH',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                onesignal_player_id: playerId,
            }),
        });

        if (response.ok) {
            console.log('[OneSignal] Player ID enregistré dans le profil');
        } else {
            console.error('[OneSignal] Erreur enregistrement player:', await response.text());
        }

    } catch (error) {
        console.error('[OneSignal] Erreur registerPlayer:', error);
    }
}

/**
 * Vérifie si les notifications sont activées
 */
async function areNotificationsEnabled() {
    if (typeof OneSignal === 'undefined') return false;

    try {
        const permission = await OneSignal.Notifications.permission;
        return permission === true;
    } catch {
        return false;
    }
}

/**
 * Désactive les notifications
 */
async function disableNotifications() {
    if (typeof OneSignal === 'undefined') return;

    try {
        await OneSignal.User.PushSubscription.optOut();
        console.log('[OneSignal] Notifications désactivées');
    } catch (error) {
        console.error('[OneSignal] Erreur désactivation:', error);
    }
}

// Export global
window.OneSignalPush = {
    init: initOneSignal,
    requestPermission: requestNotificationPermission,
    registerPlayer,
    areNotificationsEnabled,
    disableNotifications,
};

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', () => {
    // Attendre un peu que le SDK OneSignal soit chargé
    setTimeout(initOneSignal, 1000);
});
