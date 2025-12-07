/**
 * State Manager - Simple reactive state management
 * Provides global state with subscriptions and persistence
 */

class StateManager {
    constructor(initialState = {}, options = {}) {
        this.state = { ...initialState };
        this.subscribers = new Map();
        this.options = {
            persist: false,
            persistKey: 'app_state',
            persistFields: [],
            ...options
        };

        // Load persisted state if enabled
        if (this.options.persist) {
            this.loadPersistedState();
        }
    }

    /**
     * Get state value
     */
    get(key) {
        if (key === undefined) {
            return { ...this.state };
        }
        return this.state[key];
    }

    /**
     * Set state value
     */
    set(key, value) {
        const oldValue = this.state[key];
        this.state[key] = value;

        // Persist if enabled
        if (this.options.persist) {
            this.persistState();
        }

        // Notify subscribers
        this.notify(key, value, oldValue);
    }

    /**
     * Update multiple state values
     */
    update(updates) {
        Object.keys(updates).forEach(key => {
            this.set(key, updates[key]);
        });
    }

    /**
     * Subscribe to state changes
     */
    subscribe(key, callback) {
        if (!this.subscribers.has(key)) {
            this.subscribers.set(key, new Set());
        }
        this.subscribers.get(key).add(callback);

        // Return unsubscribe function
        return () => {
            const callbacks = this.subscribers.get(key);
            if (callbacks) {
                callbacks.delete(callback);
            }
        };
    }

    /**
     * Subscribe to all state changes
     */
    subscribeAll(callback) {
        return this.subscribe('*', callback);
    }

    /**
     * Notify subscribers
     */
    notify(key, newValue, oldValue) {
        // Notify specific key subscribers
        const keySubscribers = this.subscribers.get(key);
        if (keySubscribers) {
            keySubscribers.forEach(callback => {
                try {
                    callback(newValue, oldValue, key);
                } catch (error) {
                    console.error('Error in state subscriber:', error);
                }
            });
        }

        // Notify wildcard subscribers
        const allSubscribers = this.subscribers.get('*');
        if (allSubscribers) {
            allSubscribers.forEach(callback => {
                try {
                    callback(newValue, oldValue, key);
                } catch (error) {
                    console.error('Error in state subscriber:', error);
                }
            });
        }
    }

    /**
     * Reset state
     */
    reset(initialState = {}) {
        this.state = { ...initialState };
        
        if (this.options.persist) {
            this.persistState();
        }

        // Notify all subscribers
        Object.keys(this.state).forEach(key => {
            this.notify(key, this.state[key], undefined);
        });
    }

    /**
     * Clear state
     */
    clear() {
        this.reset({});
        localStorage.removeItem(this.options.persistKey);
    }

    /**
     * Persist state to localStorage
     */
    persistState() {
        try {
            const stateToPersist = this.options.persistFields.length > 0
                ? this.options.persistFields.reduce((acc, key) => {
                    if (this.state[key] !== undefined) {
                        acc[key] = this.state[key];
                    }
                    return acc;
                }, {})
                : this.state;

            localStorage.setItem(
                this.options.persistKey,
                JSON.stringify(stateToPersist)
            );
        } catch (error) {
            console.error('Error persisting state:', error);
        }
    }

    /**
     * Load persisted state
     */
    loadPersistedState() {
        try {
            const persisted = localStorage.getItem(this.options.persistKey);
            if (persisted) {
                const parsed = JSON.parse(persisted);
                this.state = { ...this.state, ...parsed };
            }
        } catch (error) {
            console.error('Error loading persisted state:', error);
        }
    }

    /**
     * Compute derived state
     */
    computed(key, computeFn, dependencies = []) {
        const compute = () => {
            const value = computeFn(this.state);
            this.set(key, value);
        };

        // Initial computation
        compute();

        // Recompute when dependencies change
        dependencies.forEach(dep => {
            this.subscribe(dep, compute);
        });
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = StateManager;
}
