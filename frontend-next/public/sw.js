/**
 * FFE Monitor - Service Worker for Next.js
 * Stratégie: Network-first pour navigation, Cache-first pour assets
 * Intégration OneSignal pour les notifications push
 */

// Import OneSignal SDK for push notifications
importScripts("https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.sw.js");

const CACHE_NAME = 'ffemonitor-v5';
const STATIC_CACHE_NAME = 'ffemonitor-static-v5';

// Assets statiques à mettre en cache
const STATIC_ASSETS = [
    '/logo.svg',
    '/manifest.json',
    '/offline.html',
    '/icons/icon-72.png',
    '/icons/icon-96.png',
    '/icons/icon-128.png',
    '/icons/icon-144.png',
    '/icons/icon-152.png',
    '/icons/icon-192.png',
    '/icons/icon-384.png',
    '/icons/icon-512.png',
    '/icons/icon-maskable-192.png',
    '/icons/icon-maskable-512.png',
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

    // Ignorer les requêtes Next.js internes et HMR
    if (url.pathname.startsWith('/_next/') ||
        url.pathname.includes('webpack') ||
        url.pathname.includes('hot-update') ||
        url.pathname.includes('.hot-update.')) {
        return;
    }

    // Ignorer les requêtes vers d'autres domaines
    if (url.origin !== self.location.origin) {
        return;
    }

    // Gérer les navigations avec fallback offline
    if (request.mode === 'navigate') {
        event.respondWith(
            fetch(request).catch(() => {
                return caches.match('/offline.html');
            })
        );
        return;
    }

    // Stratégie Network-first pour les API
    if (url.pathname.startsWith('/api/') ||
        url.pathname.startsWith('/auth/') ||
        url.pathname.startsWith('/concours') ||
        url.pathname.startsWith('/health') ||
        url.pathname.startsWith('/stats') ||
        url.pathname.startsWith('/calendar')) {
        event.respondWith(networkFirst(request));
        return;
    }

    // Stratégie Cache-first pour les assets statiques (images, etc.)
    if (url.pathname.match(/\.(svg|png|jpg|jpeg|gif|webp|ico|woff|woff2)$/)) {
        event.respondWith(cacheFirst(request));
        return;
    }
});

/**
 * Stratégie Cache-first
 */
async function cacheFirst(request) {
    const cachedResponse = await caches.match(request);

    if (cachedResponse) {
        // Refresh cache in background
        fetchAndCache(request).catch(() => {});
        return cachedResponse;
    }

    return fetchAndCache(request);
}

/**
 * Stratégie Network-first
 */
async function networkFirst(request) {
    try {
        const networkResponse = await fetch(request);

        if (networkResponse.ok && networkResponse.type !== 'opaqueredirect') {
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

        return new Response(JSON.stringify({ error: 'Offline' }), {
            status: 503,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}

/**
 * Fetch et mise en cache
 */
async function fetchAndCache(request) {
    try {
        const networkResponse = await fetch(request);

        if (networkResponse.ok && networkResponse.type !== 'opaqueredirect') {
            const cache = await caches.open(STATIC_CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }

        return networkResponse;
    } catch (error) {
        console.error('[SW] Erreur fetch:', error);

        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }

        throw error;
    }
}

// Clic sur notification
self.addEventListener('notificationclick', (event) => {
    console.log('[SW] Clic sur notification:', event);

    event.notification.close();

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then((clientList) => {
                for (const client of clientList) {
                    if (client.url.includes('/app') && 'focus' in client) {
                        return client.focus();
                    }
                }

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
