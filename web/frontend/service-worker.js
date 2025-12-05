/**
 * =============================================================================
 * RECEIPT EXTRACTOR - Service Worker
 * =============================================================================
 * 
 * Provides offline capabilities and caching for the PWA.
 * 
 * Caching Strategy:
 * - Static assets: Cache First with version validation
 * - API requests: Network First with offline fallback
 * - Images: Cache First with refresh
 * 
 * Cache Busting:
 * - Version-based cache invalidation
 * - Automatic update on new version detection
 * - Clear old caches on activation
 * 
 * =============================================================================
 */

const APP_VERSION = '2.0.1';
const CACHE_NAME = 'receipt-extractor-v2.0.1';
const STATIC_CACHE = 'static-v2.0.1';
const DYNAMIC_CACHE = 'dynamic-v2.0.1';

// Static assets to cache on install
const STATIC_ASSETS = [
    '/',
    '/index.html',
    '/styles.css',
    '/app.js',
    '/manifest.json',
    '/icons/icon-192x192.png',
    '/icons/icon-512x512.png'
];

// API endpoints to cache
const API_CACHE_PATTERNS = [
    /\/api\/models$/,
    /\/api\/health$/
];

// ============================================================================
// INSTALL EVENT
// ============================================================================

self.addEventListener('install', (event) => {
    console.log('[ServiceWorker] Installing version:', APP_VERSION);
    
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then((cache) => {
                console.log('[ServiceWorker] Caching static assets');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => {
                console.log('[ServiceWorker] Install complete, skipping waiting');
                // Force immediate activation
                return self.skipWaiting();
            })
            .catch((error) => {
                console.error('[ServiceWorker] Install failed:', error);
            })
    );
});

// ============================================================================
// ACTIVATE EVENT
// ============================================================================

self.addEventListener('activate', (event) => {
    console.log('[ServiceWorker] Activating version:', APP_VERSION);
    
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames
                        .filter((name) => {
                            // Delete ALL old caches that don't match current version
                            const isOldCache = (
                                (name.startsWith('receipt-extractor-') || 
                                 name.startsWith('static-') || 
                                 name.startsWith('dynamic-')) &&
                                name !== CACHE_NAME &&
                                name !== STATIC_CACHE &&
                                name !== DYNAMIC_CACHE
                            );
                            return isOldCache;
                        })
                        .map((name) => {
                            console.log('[ServiceWorker] Deleting old cache:', name);
                            return caches.delete(name);
                        })
                );
            })
            .then(() => {
                console.log('[ServiceWorker] Activate complete');
                return self.clients.claim();
            })
    );
});

// ============================================================================
// FETCH EVENT
// ============================================================================

self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Skip non-HTTP requests
    if (!url.protocol.startsWith('http')) {
        return;
    }
    
    // Handle API requests
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(handleApiRequest(request));
        return;
    }
    
    // Handle static assets
    if (isStaticAsset(url.pathname)) {
        event.respondWith(cacheFirst(request));
        return;
    }
    
    // Default: Network first
    event.respondWith(networkFirst(request));
});

// ============================================================================
// CACHING STRATEGIES
// ============================================================================

/**
 * Cache First strategy - for static assets
 */
async function cacheFirst(request) {
    const cachedResponse = await caches.match(request);
    
    if (cachedResponse) {
        return cachedResponse;
    }
    
    try {
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            const cache = await caches.open(STATIC_CACHE);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.error('[ServiceWorker] Fetch failed:', error);
        return offlineFallback(request);
    }
}

/**
 * Network First strategy - for dynamic content
 */
async function networkFirst(request) {
    try {
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            const cache = await caches.open(DYNAMIC_CACHE);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.log('[ServiceWorker] Network failed, trying cache');
        
        const cachedResponse = await caches.match(request);
        
        if (cachedResponse) {
            return cachedResponse;
        }
        
        return offlineFallback(request);
    }
}

/**
 * Handle API requests - Network first with caching for GET
 */
async function handleApiRequest(request) {
    // Only cache GET requests
    if (request.method !== 'GET') {
        return fetch(request).catch(() => offlineApiResponse(request));
    }
    
    // Check if this endpoint should be cached
    const url = new URL(request.url);
    const shouldCache = API_CACHE_PATTERNS.some(pattern => pattern.test(url.pathname));
    
    try {
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok && shouldCache) {
            const cache = await caches.open(DYNAMIC_CACHE);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.log('[ServiceWorker] API request failed, trying cache');
        
        const cachedResponse = await caches.match(request);
        
        if (cachedResponse) {
            return cachedResponse;
        }
        
        return offlineApiResponse(request);
    }
}

// ============================================================================
// HELPERS
// ============================================================================

/**
 * Check if URL is a static asset
 */
function isStaticAsset(pathname) {
    const staticExtensions = ['.css', '.js', '.png', '.jpg', '.jpeg', '.svg', '.ico', '.woff', '.woff2'];
    return staticExtensions.some(ext => pathname.endsWith(ext));
}

/**
 * Return offline fallback response
 */
function offlineFallback(request) {
    const url = new URL(request.url);
    
    // For HTML pages, return cached index.html
    if (request.headers.get('accept')?.includes('text/html')) {
        return caches.match('/index.html');
    }
    
    // For images, return a placeholder
    if (request.headers.get('accept')?.includes('image/')) {
        return new Response(
            '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><text x="50%" y="50%" text-anchor="middle">Offline</text></svg>',
            { headers: { 'Content-Type': 'image/svg+xml' } }
        );
    }
    
    return new Response('Offline', { status: 503 });
}

/**
 * Return offline API response
 */
function offlineApiResponse(request) {
    return new Response(
        JSON.stringify({
            success: false,
            error: 'You are offline. Please check your internet connection.',
            offline: true
        }),
        {
            status: 503,
            headers: { 'Content-Type': 'application/json' }
        }
    );
}

// ============================================================================
// BACKGROUND SYNC
// ============================================================================

self.addEventListener('sync', (event) => {
    console.log('[ServiceWorker] Sync event:', event.tag);
    
    if (event.tag === 'sync-extractions') {
        event.waitUntil(syncPendingExtractions());
    }
});

/**
 * Sync pending extractions when back online
 */
async function syncPendingExtractions() {
    // Get pending items from IndexedDB
    // This would be implemented when offline extraction queue is added
    console.log('[ServiceWorker] Syncing pending extractions...');
}

// ============================================================================
// PUSH NOTIFICATIONS
// ============================================================================

self.addEventListener('push', (event) => {
    console.log('[ServiceWorker] Push received');
    
    if (!event.data) return;
    
    const data = event.data.json();
    
    const options = {
        body: data.body || 'New notification',
        icon: '/icons/icon-192x192.png',
        badge: '/icons/badge-72x72.png',
        vibrate: [100, 50, 100],
        data: {
            url: data.url || '/'
        },
        actions: data.actions || []
    };
    
    event.waitUntil(
        self.registration.showNotification(data.title || 'Receipt Extractor', options)
    );
});

self.addEventListener('notificationclick', (event) => {
    console.log('[ServiceWorker] Notification clicked');
    
    event.notification.close();
    
    event.waitUntil(
        clients.matchAll({ type: 'window' })
            .then((clientList) => {
                // Focus existing window if available
                for (const client of clientList) {
                    if (client.url === event.notification.data.url && 'focus' in client) {
                        return client.focus();
                    }
                }
                
                // Open new window
                if (clients.openWindow) {
                    return clients.openWindow(event.notification.data.url);
                }
            })
    );
});

// ============================================================================
// MESSAGE HANDLING
// ============================================================================

self.addEventListener('message', (event) => {
    console.log('[ServiceWorker] Message received:', event.data);
    
    if (event.data.type === 'SKIP_WAITING') {
        console.log('[ServiceWorker] Skip waiting triggered');
        self.skipWaiting();
    }
    
    if (event.data.type === 'CLEAR_CACHE') {
        console.log('[ServiceWorker] Clearing all caches...');
        caches.keys().then((names) => {
            return Promise.all(
                names.map((name) => {
                    console.log('[ServiceWorker] Deleting cache:', name);
                    return caches.delete(name);
                })
            );
        }).then(() => {
            console.log('[ServiceWorker] All caches cleared');
        });
    }
    
    if (event.data.type === 'GET_VERSION') {
        event.ports[0].postMessage({ 
            version: APP_VERSION,
            cacheName: CACHE_NAME 
        });
    }
    
    if (event.data.type === 'FORCE_UPDATE') {
        console.log('[ServiceWorker] Force update triggered');
        // Clear caches and reload
        caches.keys().then((names) => {
            return Promise.all(names.map(name => caches.delete(name)));
        }).then(() => {
            self.clients.matchAll().then((clients) => {
                clients.forEach((client) => {
                    client.postMessage({ type: 'RELOAD_PAGE' });
                });
            });
        });
    }
});

console.log('[ServiceWorker] Script loaded, version:', APP_VERSION);
