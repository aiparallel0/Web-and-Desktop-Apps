/**
 * Event Bus System
 * Centralized pub/sub event system for application-wide communication
 */

class EventBus {
    constructor() {
        this.events = new Map();
        this.eventHistory = [];
        this.maxHistorySize = 100;
        this.middleware = [];
    }

    /**
     * Subscribe to an event
     */
    on(event, callback, options = {}) {
        if (!this.events.has(event)) {
            this.events.set(event, new Set());
        }

        const handler = {
            callback,
            once: options.once || false,
            priority: options.priority || 0,
            context: options.context || null
        };

        this.events.get(event).add(handler);

        return () => this.off(event, callback);
    }

    /**
     * Subscribe to event once
     */
    once(event, callback, options = {}) {
        return this.on(event, callback, { ...options, once: true });
    }

    /**
     * Unsubscribe from event
     */
    off(event, callback) {
        const handlers = this.events.get(event);
        if (!handlers) return;

        for (const handler of handlers) {
            if (handler.callback === callback) {
                handlers.delete(handler);
                break;
            }
        }

        if (handlers.size === 0) {
            this.events.delete(event);
        }
    }

    /**
     * Emit an event
     */
    async emit(event, data) {
        const handlers = this.events.get(event);
        if (!handlers || handlers.size === 0) {
            return;
        }

        // Run middleware
        let eventData = data;
        for (const mw of this.middleware) {
            eventData = await mw(event, eventData);
            if (eventData === false) return; // Cancel event
        }

        // Record in history
        this.addToHistory(event, eventData);

        // Sort handlers by priority
        const sorted = Array.from(handlers).sort((a, b) => b.priority - a.priority);

        // Execute handlers
        for (const handler of sorted) {
            try {
                if (handler.context) {
                    await handler.callback.call(handler.context, eventData);
                } else {
                    await handler.callback(eventData);
                }

                if (handler.once) {
                    handlers.delete(handler);
                }
            } catch (error) {
                console.error(`Error in event handler for "${event}":`, error);
            }
        }
    }

    /**
     * Add middleware
     */
    use(middleware) {
        this.middleware.push(middleware);
    }

    /**
     * Add to event history
     */
    addToHistory(event, data) {
        this.eventHistory.unshift({
            event,
            data,
            timestamp: new Date().toISOString()
        });

        if (this.eventHistory.length > this.maxHistorySize) {
            this.eventHistory = this.eventHistory.slice(0, this.maxHistorySize);
        }
    }

    /**
     * Get event history
     */
    getHistory(event = null) {
        if (event) {
            return this.eventHistory.filter(h => h.event === event);
        }
        return this.eventHistory;
    }

    /**
     * Clear all event handlers
     */
    clear() {
        this.events.clear();
        this.eventHistory = [];
    }
}

// Create singleton
const eventBus = new EventBus();

if (typeof window !== 'undefined') {
    window.EventBus = eventBus;
}

export default eventBus;
