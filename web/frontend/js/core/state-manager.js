/**
 * Central State Management System
 * Handles application-wide state with reactive updates
 */

class StateManager {
    constructor() {
        this.state = {
            user: {
                id: null,
                email: null,
                name: null,
                plan: 'free',
                avatar: null,
                company: null,
                preferences: {
                    theme: 'light',
                    defaultModel: 'auto',
                    exportFormat: 'json',
                    notifications: true,
                    autoProcess: false
                }
            },
            extractions: [],
            batchJobs: [],
            apiKeys: [],
            templates: [],
            notifications: [],
            analytics: {
                totalExtractions: 0,
                successRate: 0,
                avgProcessingTime: 0,
                apiCalls: 0,
                monthlyUsage: {
                    current: 0,
                    limit: 10
                }
            },
            ui: {
                sidebarCollapsed: false,
                activeSection: 'overview',
                activeTab: null,
                modals: {},
                loading: false,
                darkMode: false
            }
        };

        this.listeners = new Map();
        this.initializeFromStorage();
    }

    initializeFromStorage() {
        try {
            const savedState = localStorage.getItem('app_state');
            if (savedState) {
                const parsed = JSON.parse(savedState);
                this.state = this.deepMerge(this.state, parsed);
            }

            const darkMode = localStorage.getItem('dark_mode') === 'true';
            this.state.ui.darkMode = darkMode;
            if (darkMode) {
                document.body.classList.add('dark-mode');
            }
        } catch (error) {
            console.error('Error loading state from storage:', error);
        }
    }

    deepMerge(target, source) {
        const output = Object.assign({}, target);
        if (this.isObject(target) && this.isObject(source)) {
            Object.keys(source).forEach(key => {
                if (this.isObject(source[key])) {
                    if (!(key in target)) {
                        Object.assign(output, { [key]: source[key] });
                    } else {
                        output[key] = this.deepMerge(target[key], source[key]);
                    }
                } else {
                    Object.assign(output, { [key]: source[key] });
                }
            });
        }
        return output;
    }

    isObject(item) {
        return item && typeof item === 'object' && !Array.isArray(item);
    }

    get(path) {
        return path.split('.').reduce((obj, key) => obj?.[key], this.state);
    }

    set(path, value) {
        const keys = path.split('.');
        const lastKey = keys.pop();
        const target = keys.reduce((obj, key) => {
            if (!(key in obj)) obj[key] = {};
            return obj[key];
        }, this.state);

        target[lastKey] = value;
        this.notifyListeners(path, value);
        this.persistState();
    }

    update(path, updates) {
        const current = this.get(path);
        if (typeof current === 'object') {
            const updated = { ...current, ...updates };
            this.set(path, updated);
        }
    }

    subscribe(path, callback) {
        if (!this.listeners.has(path)) {
            this.listeners.set(path, new Set());
        }
        this.listeners.get(path).add(callback);

        return () => {
            const callbacks = this.listeners.get(path);
            if (callbacks) {
                callbacks.delete(callback);
            }
        };
    }

    notifyListeners(path, value) {
        const callbacks = this.listeners.get(path);
        if (callbacks) {
            callbacks.forEach(callback => callback(value));
        }

        const parts = path.split('.');
        for (let i = 0; i < parts.length; i++) {
            const partialPath = parts.slice(0, i + 1).join('.');
            const wildcardPath = partialPath + '.*';
            const wildcardCallbacks = this.listeners.get(wildcardPath);
            if (wildcardCallbacks) {
                wildcardCallbacks.forEach(callback => callback(value, path));
            }
        }
    }

    persistState() {
        try {
            const stateToPersist = {
                user: {
                    ...this.state.user,
                    preferences: this.state.user.preferences
                },
                analytics: this.state.analytics
            };
            localStorage.setItem('app_state', JSON.stringify(stateToPersist));
        } catch (error) {
            console.error('Error persisting state:', error);
        }
    }

    clear() {
        this.state = {
            user: { id: null, email: null, name: null, plan: 'free', preferences: {} },
            extractions: [],
            batchJobs: [],
            apiKeys: [],
            templates: [],
            notifications: [],
            analytics: { totalExtractions: 0, successRate: 0, avgProcessingTime: 0, apiCalls: 0 },
            ui: { sidebarCollapsed: false, activeSection: 'overview', modals: {}, loading: false }
        };
        localStorage.removeItem('app_state');
        this.notifyListeners('*', this.state);
    }

    addExtraction(extraction) {
        this.state.extractions.unshift(extraction);
        if (this.state.extractions.length > 100) {
            this.state.extractions = this.state.extractions.slice(0, 100);
        }
        this.notifyListeners('extractions', this.state.extractions);
        this.updateAnalytics();
    }

    updateAnalytics() {
        const extractions = this.state.extractions;
        if (extractions.length === 0) return;

        const successful = extractions.filter(e => e.status === 'success').length;
        const totalTime = extractions.reduce((sum, e) => sum + (e.processingTime || 0), 0);

        this.state.analytics.totalExtractions = extractions.length;
        this.state.analytics.successRate = (successful / extractions.length) * 100;
        this.state.analytics.avgProcessingTime = totalTime / extractions.length;

        this.notifyListeners('analytics', this.state.analytics);
        this.persistState();
    }

    addNotification(notification) {
        const id = Date.now() + Math.random();
        const notif = {
            id,
            timestamp: new Date().toISOString(),
            read: false,
            ...notification
        };

        this.state.notifications.unshift(notif);
        this.notifyListeners('notifications', this.state.notifications);

        return id;
    }

    markNotificationRead(id) {
        const notif = this.state.notifications.find(n => n.id === id);
        if (notif) {
            notif.read = true;
            this.notifyListeners('notifications', this.state.notifications);
        }
    }

    clearNotifications() {
        this.state.notifications = [];
        this.notifyListeners('notifications', this.state.notifications);
    }

    toggleDarkMode() {
        const darkMode = !this.state.ui.darkMode;
        this.state.ui.darkMode = darkMode;
        document.body.classList.toggle('dark-mode', darkMode);
        localStorage.setItem('dark_mode', darkMode);
        this.notifyListeners('ui.darkMode', darkMode);
    }

    setLoading(loading) {
        this.state.ui.loading = loading;
        this.notifyListeners('ui.loading', loading);
    }

    openModal(modalId, data = null) {
        this.state.ui.modals[modalId] = { open: true, data };
        this.notifyListeners('ui.modals', this.state.ui.modals);
    }

    closeModal(modalId) {
        if (this.state.ui.modals[modalId]) {
            this.state.ui.modals[modalId].open = false;
            this.notifyListeners('ui.modals', this.state.ui.modals);
        }
    }

    setActiveSection(section) {
        this.state.ui.activeSection = section;
        this.notifyListeners('ui.activeSection', section);
    }
}

const stateManager = new StateManager();

if (typeof window !== 'undefined') {
    window.StateManager = stateManager;
}

export default stateManager;
