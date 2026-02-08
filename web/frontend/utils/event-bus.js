/**
 * Event Bus - Central event coordination system
 * Manages component communication and global events
 */

class EventBus {
    constructor() {
        this.events = new Map();
        this.onceEvents = new Map();
        this.wildcardListeners = [];
        this.history = [];
        this.maxHistory = 100;
        this.debug = false;
    }

    /**
     * Subscribe to event
     */
    on(eventName, callback, context = null) {
        if (!this.events.has(eventName)) {
            this.events.set(eventName, []);
        }

        const listener = {
            callback,
            context,
            id: this.generateId()
        };

        this.events.get(eventName).push(listener);

        if (this.debug) {
            console.log(`[EventBus] Subscribed to "${eventName}"`);
        }

        // Return unsubscribe function
        return () => this.off(eventName, listener.id);
    }

    /**
     * Subscribe to event once
     */
    once(eventName, callback, context = null) {
        if (!this.onceEvents.has(eventName)) {
            this.onceEvents.set(eventName, []);
        }

        const listener = {
            callback,
            context,
            id: this.generateId()
        };

        this.onceEvents.get(eventName).push(listener);

        if (this.debug) {
            console.log(`[EventBus] Subscribed once to "${eventName}"`);
        }

        return () => this.offOnce(eventName, listener.id);
    }

    /**
     * Unsubscribe from event
     */
    off(eventName, listenerId = null) {
        if (!this.events.has(eventName)) {
            return;
        }

        if (listenerId) {
            const listeners = this.events.get(eventName);
            const index = listeners.findIndex(l => l.id === listenerId);
            if (index !== -1) {
                listeners.splice(index, 1);
            }
        } else {
            this.events.delete(eventName);
        }

        if (this.debug) {
            console.log(`[EventBus] Unsubscribed from "${eventName}"`);
        }
    }

    /**
     * Unsubscribe from once event
     */
    offOnce(eventName, listenerId) {
        if (!this.onceEvents.has(eventName)) {
            return;
        }

        const listeners = this.onceEvents.get(eventName);
        const index = listeners.findIndex(l => l.id === listenerId);
        if (index !== -1) {
            listeners.splice(index, 1);
        }
    }

    /**
     * Emit event
     */
    emit(eventName, data = null) {
        const timestamp = Date.now();

        // Add to history
        this.addToHistory(eventName, data, timestamp);

        if (this.debug) {
            console.log(`[EventBus] Emitting "${eventName}"`, data);
        }

        // Emit to regular listeners
        if (this.events.has(eventName)) {
            const listeners = this.events.get(eventName);
            listeners.forEach(listener => {
                try {
                    listener.callback.call(listener.context, data, eventName);
                } catch (error) {
                    console.error(`[EventBus] Error in listener for "${eventName}":`, error);
                }
            });
        }

        // Emit to once listeners
        if (this.onceEvents.has(eventName)) {
            const listeners = this.onceEvents.get(eventName);
            listeners.forEach(listener => {
                try {
                    listener.callback.call(listener.context, data, eventName);
                } catch (error) {
                    console.error(`[EventBus] Error in once listener for "${eventName}":`, error);
                }
            });
            this.onceEvents.delete(eventName);
        }

        // Emit to wildcard listeners
        this.wildcardListeners.forEach(listener => {
            try {
                listener.callback.call(listener.context, eventName, data);
            } catch (error) {
                console.error('[EventBus] Error in wildcard listener:', error);
            }
        });
    }

    /**
     * Subscribe to all events
     */
    onAny(callback, context = null) {
        const listener = {
            callback,
            context,
            id: this.generateId()
        };

        this.wildcardListeners.push(listener);

        return () => {
            const index = this.wildcardListeners.findIndex(l => l.id === listener.id);
            if (index !== -1) {
                this.wildcardListeners.splice(index, 1);
            }
        };
    }

    /**
     * Clear all listeners
     */
    clear() {
        this.events.clear();
        this.onceEvents.clear();
        this.wildcardListeners = [];

        if (this.debug) {
            console.log('[EventBus] Cleared all listeners');
        }
    }

    /**
     * Get all event names
     */
    getEventNames() {
        return Array.from(this.events.keys());
    }

    /**
     * Get listener count for event
     */
    listenerCount(eventName) {
        const regularCount = this.events.has(eventName) ? this.events.get(eventName).length : 0;
        const onceCount = this.onceEvents.has(eventName) ? this.onceEvents.get(eventName).length : 0;
        return regularCount + onceCount;
    }

    /**
     * Add event to history
     */
    addToHistory(eventName, data, timestamp) {
        this.history.push({
            eventName,
            data,
            timestamp
        });

        if (this.history.length > this.maxHistory) {
            this.history.shift();
        }
    }

    /**
     * Get event history
     */
    getHistory(eventName = null, limit = null) {
        let history = this.history;

        if (eventName) {
            history = history.filter(h => h.eventName === eventName);
        }

        if (limit) {
            history = history.slice(-limit);
        }

        return history;
    }

    /**
     * Clear history
     */
    clearHistory() {
        this.history = [];
    }

    /**
     * Enable debug mode
     */
    enableDebug() {
        this.debug = true;
    }

    /**
     * Disable debug mode
     */
    disableDebug() {
        this.debug = false;
    }

    /**
     * Generate unique ID
     */
    generateId() {
        return `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Wait for event
     */
    waitFor(eventName, timeout = 10000) {
        return new Promise((resolve, reject) => {
            const timeoutId = setTimeout(() => {
                unsubscribe();
                reject(new Error(`Timeout waiting for event "${eventName}"`));
            }, timeout);

            const unsubscribe = this.once(eventName, (data) => {
                clearTimeout(timeoutId);
                resolve(data);
            });
        });
    }

    /**
     * Create namespaced event bus
     */
    namespace(prefix) {
        return new NamespacedEventBus(this, prefix);
    }
}

/**
 * Namespaced Event Bus
 */
class NamespacedEventBus {
    constructor(parentBus, prefix) {
        this.parent = parentBus;
        this.prefix = prefix;
    }

    on(eventName, callback, context) {
        return this.parent.on(`${this.prefix}:${eventName}`, callback, context);
    }

    once(eventName, callback, context) {
        return this.parent.once(`${this.prefix}:${eventName}`, callback, context);
    }

    off(eventName, listenerId) {
        return this.parent.off(`${this.prefix}:${eventName}`, listenerId);
    }

    emit(eventName, data) {
        return this.parent.emit(`${this.prefix}:${eventName}`, data);
    }

    waitFor(eventName, timeout) {
        return this.parent.waitFor(`${this.prefix}:${eventName}`, timeout);
    }
}

/**
 * Application Event Coordinator
 * Manages specific application events
 */
class AppEventCoordinator {
    constructor(eventBus) {
        this.bus = eventBus;
        this.setupListeners();
    }

    setupListeners() {
        // Log important events
        this.bus.on('file-selected', (data) => {
            console.log('File selected:', data.file.name);
        });

        this.bus.on('extraction-started', () => {
            console.log('Extraction started');
        });

        this.bus.on('extraction-complete', (data) => {
            console.log('Extraction complete:', data.result);
        });

        this.bus.on('extraction-error', (data) => {
            console.error('Extraction error:', data.error);
        });

        this.bus.on('model-changed', (data) => {
            console.log('Model changed to:', data.modelId);
        });

        this.bus.on('settings-changed', (data) => {
            console.log('Settings changed:', data);
        });
    }

    // File events
    onFileSelected(callback) {
        return this.bus.on('file-selected', callback);
    }

    emitFileSelected(file) {
        this.bus.emit('file-selected', { file, timestamp: Date.now() });
    }

    // Extraction events
    onExtractionStarted(callback) {
        return this.bus.on('extraction-started', callback);
    }

    emitExtractionStarted(file, settings) {
        this.bus.emit('extraction-started', { file, settings, timestamp: Date.now() });
    }

    onExtractionComplete(callback) {
        return this.bus.on('extraction-complete', callback);
    }

    emitExtractionComplete(result, duration) {
        this.bus.emit('extraction-complete', { result, duration, timestamp: Date.now() });
    }

    onExtractionError(callback) {
        return this.bus.on('extraction-error', callback);
    }

    emitExtractionError(error) {
        this.bus.emit('extraction-error', { error, timestamp: Date.now() });
    }

    // Model events
    onModelChanged(callback) {
        return this.bus.on('model-changed', callback);
    }

    emitModelChanged(modelId, previousModelId) {
        this.bus.emit('model-changed', { modelId, previousModelId, timestamp: Date.now() });
    }

    // Settings events
    onSettingsChanged(callback) {
        return this.bus.on('settings-changed', callback);
    }

    emitSettingsChanged(settings) {
        this.bus.emit('settings-changed', { settings, timestamp: Date.now() });
    }

    // API events
    onApiConnected(callback) {
        return this.bus.on('api-connected', callback);
    }

    emitApiConnected() {
        this.bus.emit('api-connected', { timestamp: Date.now() });
    }

    onApiDisconnected(callback) {
        return this.bus.on('api-disconnected', callback);
    }

    emitApiDisconnected(reason) {
        this.bus.emit('api-disconnected', { reason, timestamp: Date.now() });
    }

    // UI events
    onShowError(callback) {
        return this.bus.on('show-error', callback);
    }

    emitShowError(message, title) {
        this.bus.emit('show-error', { message, title, timestamp: Date.now() });
    }

    onShowSuccess(callback) {
        return this.bus.on('show-success', callback);
    }

    emitShowSuccess(message) {
        this.bus.emit('show-success', { message, timestamp: Date.now() });
    }

    // Results events
    onResultsCopied(callback) {
        return this.bus.on('results-copied', callback);
    }

    emitResultsCopied(textCount) {
        this.bus.emit('results-copied', { textCount, timestamp: Date.now() });
    }

    onResultsDownloaded(callback) {
        return this.bus.on('results-downloaded', callback);
    }

    emitResultsDownloaded(format, filename) {
        this.bus.emit('results-downloaded', { format, filename, timestamp: Date.now() });
    }
}

// Create singleton instances
const eventBus = new EventBus();
const appEvents = new AppEventCoordinator(eventBus);

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        EventBus,
        NamespacedEventBus,
        AppEventCoordinator,
        eventBus,
        appEvents
    };
}

window.EventBus = EventBus;
window.NamespacedEventBus = NamespacedEventBus;
window.AppEventCoordinator = AppEventCoordinator;
window.eventBus = eventBus;
window.appEvents = appEvents;
