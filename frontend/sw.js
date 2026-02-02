/**
 * FFE Monitor - Service Worker
 * Stratégie: Cache-first pour assets statiques, Network-first pour API
 */

const CACHE_NAME = 'ffemonitor-v1';
const STATIC_CACHE_NAME = 'ffemonitor-static-v1';

// Assets statiques à mettre en cache
const STATIC_ASSETS = [
    '/',
    '/app',
    '/login',
    '/static/style.css',
    '/static/app.js',
    '/static/supabase-client.js',
    '/static/onesignal-init.js',
    '/static/icons/icon-192.png',
    '/static/icons/icon-512.png',
    '/manifest.json',
    // Fonts Google (optionnel, selon ce qui est utilisé)
    'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap',
];

// Installation du Service Worker
self.addEventListener('install', (event) => {
    console.log('[SW] Installation...');

    event.waitUntil(
        caches.open(STATIC_CACHE_NAME)
            .then((cache) => {
                console.log('[SW] Mise en cache des assets statiques');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => {
                // Activation immédiate
                return self.skipWaiting();
            })
            .catch((error) => {
                console.error('[SW] Erreur installation:', error);
            })
    );
});

// Activation du Service Worker
self.addEventListener('activate', (event) => {
    console.log('[SW] Activation...');

    event.waitUntil(
        // Supprimer les anciens caches
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames
                        .filter((name) => name !== STATIC_CACHE_NAME && name !== CACHE_NAME)
                        .map((name) => {
                            console.log('[SW] Suppression ancien cache:', name);
                            return caches.delete(name);
                        })
                );
            })
            .then(() => {
                // Prendre le contrôle immédiatement
                return self.clients.claim();
            })
    );
});

// Interception des requêtes
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Ignorer les requêtes non-GET
    if (request.method !== 'GET') {
        return;
    }

    // Ignorer les requêtes vers d'autres domaines (sauf CDN)
    if (url.origin !== self.location.origin &&
        !url.origin.includes('fonts.googleapis.com') &&
        !url.origin.includes('fonts.gstatic.com') &&
        !url.origin.includes('cdn.onesignal.com')) {
        return;
    }

    // Stratégie Network-first pour les API
    if (url.pathname.startsWith('/api/') ||
        url.pathname.startsWith('/auth/') ||
        url.pathname.startsWith('/concours') ||
        url.pathname.startsWith('/subscriptions') ||
        url.pathname.startsWith('/health') ||
        url.pathname.startsWith('/status')) {
        event.respondWith(networkFirst(request));
        return;
    }

    // Stratégie Cache-first pour les assets statiques
    event.respondWith(cacheFirst(request));
});

/**
 * Stratégie Cache-first
 * Retourne le cache si disponible, sinon fait une requête réseau
 */
async function cacheFirst(request) {
    const cachedResponse = await caches.match(request);

    if (cachedResponse) {
        // Mise à jour en arrière-plan (stale-while-revalidate)
        fetchAndCache(request);
        return cachedResponse;
    }

    return fetchAndCache(request);
}

/**
 * Stratégie Network-first
 * Essaie le réseau d'abord, retourne le cache si hors ligne
 */
async function networkFirst(request) {
    try {
        const networkResponse = await fetch(request);

        // Ne pas mettre en cache les erreurs
        if (networkResponse.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }

        return networkResponse;
    } catch (error) {
        console.log('[SW] Réseau indisponible, utilisation du cache');

        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }

        // Retourner une page offline si disponible
        return caches.match('/offline.html');
    }
}

/**
 * Fetch et mise en cache
 */
async function fetchAndCache(request) {
    try {
        const networkResponse = await fetch(request);

        if (networkResponse.ok) {
            const cache = await caches.open(STATIC_CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }

        return networkResponse;
    } catch (error) {
        console.error('[SW] Erreur fetch:', error);

        // Retourner la version en cache si disponible
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }

        // Page offline pour les navigations
        if (request.mode === 'navigate') {
            return caches.match('/offline.html');
        }

        throw error;
    }
}

// Gestion des notifications push (pour OneSignal)
self.addEventListener('push', (event) => {
    console.log('[SW] Push reçu:', event);

    // OneSignal gère ses propres push, mais on peut ajouter de la logique ici
    if (event.data) {
        const data = event.data.json();
        console.log('[SW] Données push:', data);
    }
});

// Clic sur notification
self.addEventListener('notificationclick', (event) => {
    console.log('[SW] Clic sur notification:', event);

    event.notification.close();

    // Ouvrir l'app si elle n'est pas déjà ouverte
    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then((clientList) => {
                // Si l'app est déjà ouverte, la focus
                for (const client of clientList) {
                    if (client.url.includes('/app') && 'focus' in client) {
                        return client.focus();
                    }
                }

                // Sinon, ouvrir une nouvelle fenêtre
                if (clients.openWindow) {
                    const url = event.notification.data?.url || '/app';
                    return clients.openWindow(url);
                }
            })
    );
});

// Message depuis l'application
self.addEventListener('message', (event) => {
    console.log('[SW] Message reçu:', event.data);

    if (event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }

    if (event.data.type === 'CLEAR_CACHE') {
        caches.keys().then((names) => {
            names.forEach((name) => caches.delete(name));
        });
    }
});
