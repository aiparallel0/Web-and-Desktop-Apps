/**
 * Progressive Web App (PWA) Features
 * Service worker management, offline support, and installation
 */

import eventBus from '../core/event-bus.js';
import toastSystem from '../components/toast-system.js';

class PWAManager {
    constructor() {
        this.serviceWorker = null;
        this.deferredPrompt = null;
        this.isInstalled = false;
        this.isOnline = navigator.onLine;
        this.offlineQueue = [];

        this.init();
    }

    init() {
        this.checkInstallation();
        this.setupServiceWorker();
        this.setupNetworkMonitoring();
        this.setupInstallPrompt();
        this.setupUpdateNotifications();
    }

    /**
     * Check if app is installed
     */
    checkInstallation() {
        if (window.matchMedia('(display-mode: standalone)').matches) {
            this.isInstalled = true;
            eventBus.emit('pwa:installed');
        }

        // Check iOS standalone mode
        if ('standalone' in window.navigator && window.navigator.standalone) {
            this.isInstalled = true;
            eventBus.emit('pwa:installed');
        }
    }

    /**
     * Setup service worker
     */
    async setupServiceWorker() {
        if (!('serviceWorker' in navigator)) {
            console.warn('Service Worker not supported');
            return;
        }

        try {
            const registration = await navigator.serviceWorker.register('/service-worker.js', {
                scope: '/'
            });

            this.serviceWorker = registration;

            console.log('Service Worker registered:', registration.scope);

            // Check for updates
            registration.addEventListener('updatefound', () => {
                const newWorker = registration.installing;

                newWorker.addEventListener('statechange', () => {
                    if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                        this.notifyUpdate();
                    }
                });
            });

            // Check for updates every hour
            setInterval(() => {
                registration.update();
            }, 60 * 60 * 1000);

            eventBus.emit('pwa:sw-registered', registration);

        } catch (error) {
            console.error('Service Worker registration failed:', error);
        }
    }

    /**
     * Setup network monitoring
     */
    setupNetworkMonitoring() {
        window.addEventListener('online', () => {
            this.isOnline = true;
            eventBus.emit('pwa:online');
            toastSystem.success('Back online');

            // Process offline queue
            this.processOfflineQueue();
        });

        window.addEventListener('offline', () => {
            this.isOnline = false;
            eventBus.emit('pwa:offline');
            toastSystem.warning('You are offline. Changes will be synced when back online.');
        });
    }

    /**
     * Setup install prompt
     */
    setupInstallPrompt() {
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            this.deferredPrompt = e;
            eventBus.emit('pwa:installable');

            // Show install banner after a delay
            setTimeout(() => {
                this.showInstallBanner();
            }, 5000);
        });

        window.addEventListener('appinstalled', () => {
            this.isInstalled = true;
            this.deferredPrompt = null;
            eventBus.emit('pwa:installed');
            toastSystem.success('App installed successfully!');
        });
    }

    /**
     * Setup update notifications
     */
    setupUpdateNotifications() {
        if (!navigator.serviceWorker) return;

        navigator.serviceWorker.addEventListener('controllerchange', () => {
            window.location.reload();
        });
    }

    /**
     * Show install banner
     */
    showInstallBanner() {
        if (this.isInstalled || !this.deferredPrompt) return;

        toastSystem.info('Install this app for a better experience', {
            duration: 0,
            action: {
                label: 'Install',
                onClick: () => this.promptInstall()
            }
        });
    }

    /**
     * Prompt installation
     */
    async promptInstall() {
        if (!this.deferredPrompt) {
            toastSystem.error('Installation not available');
            return false;
        }

        this.deferredPrompt.prompt();

        const { outcome } = await this.deferredPrompt.userChoice;

        if (outcome === 'accepted') {
            console.log('User accepted installation');
            eventBus.emit('pwa:install-accepted');
        } else {
            console.log('User dismissed installation');
            eventBus.emit('pwa:install-dismissed');
        }

        this.deferredPrompt = null;
        return outcome === 'accepted';
    }

    /**
     * Notify about available update
     */
    notifyUpdate() {
        toastSystem.info('A new version is available!', {
            duration: 0,
            action: {
                label: 'Update',
                onClick: () => this.applyUpdate()
            }
        });
    }

    /**
     * Apply update
     */
    async applyUpdate() {
        if (!this.serviceWorker) return;

        const registration = this.serviceWorker;
        const waiting = registration.waiting;

        if (waiting) {
            waiting.postMessage({ type: 'SKIP_WAITING' });

            navigator.serviceWorker.addEventListener('controllerchange', () => {
                window.location.reload();
            });
        }
    }

    /**
     * Add to offline queue
     */
    addToOfflineQueue(request) {
        this.offlineQueue.push({
            request,
            timestamp: Date.now()
        });

        this.persistOfflineQueue();
    }

    /**
     * Process offline queue
     */
    async processOfflineQueue() {
        if (!this.isOnline || this.offlineQueue.length === 0) return;

        toastSystem.loading('Syncing offline changes...');

        const processed = [];
        const failed = [];

        for (const item of this.offlineQueue) {
            try {
                await fetch(item.request);
                processed.push(item);
            } catch (error) {
                failed.push(item);
            }
        }

        this.offlineQueue = failed;
        this.persistOfflineQueue();

        if (processed.length > 0) {
            toastSystem.success(`Synced ${processed.length} changes`);
        }

        if (failed.length > 0) {
            toastSystem.warning(`${failed.length} changes failed to sync`);
        }
    }

    /**
     * Persist offline queue
     */
    persistOfflineQueue() {
        try {
            localStorage.setItem('offline_queue', JSON.stringify(this.offlineQueue));
        } catch (error) {
            console.error('Failed to persist offline queue:', error);
        }
    }

    /**
     * Load offline queue
     */
    loadOfflineQueue() {
        try {
            const saved = localStorage.getItem('offline_queue');
            if (saved) {
                this.offlineQueue = JSON.parse(saved);
            }
        } catch (error) {
            console.error('Failed to load offline queue:', error);
        }
    }

    /**
     * Cache important resources
     */
    async cacheResources(urls) {
        if (!('caches' in window)) return;

        try {
            const cache = await caches.open('app-cache-v1');
            await cache.addAll(urls);
            console.log('Resources cached:', urls.length);
        } catch (error) {
            console.error('Failed to cache resources:', error);
        }
    }

    /**
     * Clear cache
     */
    async clearCache() {
        if (!('caches' in window)) return;

        try {
            const names = await caches.keys();
            await Promise.all(names.map(name => caches.delete(name)));
            toastSystem.success('Cache cleared');
        } catch (error) {
            console.error('Failed to clear cache:', error);
        }
    }

    /**
     * Get cache size
     */
    async getCacheSize() {
        if (!('caches' in window)) return 0;

        try {
            const names = await caches.keys();
            let totalSize = 0;

            for (const name of names) {
                const cache = await caches.open(name);
                const requests = await cache.keys();

                for (const request of requests) {
                    const response = await cache.match(request);
                    if (response) {
                        const blob = await response.blob();
                        totalSize += blob.size;
                    }
                }
            }

            return totalSize;
        } catch (error) {
            console.error('Failed to get cache size:', error);
            return 0;
        }
    }

    /**
     * Check if installable
     */
    isInstallable() {
        return this.deferredPrompt !== null;
    }

    /**
     * Check if online
     */
    checkOnline() {
        return this.isOnline;
    }

    /**
     * Get app info
     */
    async getAppInfo() {
        return {
            isInstalled: this.isInstalled,
            isInstallable: this.isInstallable(),
            isOnline: this.isOnline,
            serviceWorkerActive: this.serviceWorker !== null,
            cacheSize: await this.getCacheSize(),
            offlineQueueSize: this.offlineQueue.length
        };
    }

    /**
     * Share content (Web Share API)
     */
    async share(data) {
        if (!navigator.share) {
            console.warn('Web Share API not supported');
            return false;
        }

        try {
            await navigator.share({
                title: data.title,
                text: data.text,
                url: data.url
            });

            return true;
        } catch (error) {
            if (error.name !== 'AbortError') {
                console.error('Share failed:', error);
            }
            return false;
        }
    }

    /**
     * Request persistent storage
     */
    async requestPersistentStorage() {
        if (!navigator.storage || !navigator.storage.persist) {
            return false;
        }

        try {
            const isPersisted = await navigator.storage.persist();
            if (isPersisted) {
                console.log('Persistent storage granted');
            }
            return isPersisted;
        } catch (error) {
            console.error('Failed to request persistent storage:', error);
            return false;
        }
    }

    /**
     * Get storage estimate
     */
    async getStorageEstimate() {
        if (!navigator.storage || !navigator.storage.estimate) {
            return null;
        }

        try {
            const estimate = await navigator.storage.estimate();
            return {
                usage: estimate.usage,
                quota: estimate.quota,
                percent: (estimate.usage / estimate.quota) * 100
            };
        } catch (error) {
            console.error('Failed to get storage estimate:', error);
            return null;
        }
    }
}

// Create singleton
const pwaManager = new PWAManager();

// Load offline queue
pwaManager.loadOfflineQueue();

// Expose globally
if (typeof window !== 'undefined') {
    window.pwaManager = pwaManager;
    window.PWAManager = PWAManager;
}

export default pwaManager;
