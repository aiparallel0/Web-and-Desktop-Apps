/**
 * WebSocket Manager
 * Real-time communication with automatic reconnection and event handling
 */

class WebSocketManager {
    constructor(url, options = {}) {
        this.url = url;
        this.options = {
            reconnect: true,
            reconnectInterval: 3000,
            reconnectMaxAttempts: 10,
            heartbeatInterval: 30000,
            debug: false,
            ...options
        };

        this.ws = null;
        this.reconnectAttempts = 0;
        this.reconnectTimer = null;
        this.heartbeatTimer = null;
        this.messageHandlers = new Map();
        this.connectionListeners = new Set();
        this.isConnected = false;
        this.messageQueue = [];

        if (this.url) {
            this.connect();
        }
    }

    /**
     * Connect to WebSocket server
     */
    connect() {
        if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
            this.log('Already connected or connecting');
            return;
        }

        try {
            this.log('Connecting to', this.url);
            this.ws = new WebSocket(this.url);

            this.ws.onopen = () => {
                this.log('Connected');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                
                // Send queued messages
                this.flushMessageQueue();

                // Start heartbeat
                this.startHeartbeat();

                // Notify listeners
                this.notifyConnectionListeners(true);
            };

            this.ws.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    this.handleMessage(message);
                } catch (error) {
                    this.log('Error parsing message:', error);
                }
            };

            this.ws.onerror = (error) => {
                this.log('WebSocket error:', error);
            };

            this.ws.onclose = () => {
                this.log('Disconnected');
                this.isConnected = false;
                
                // Stop heartbeat
                this.stopHeartbeat();

                // Notify listeners
                this.notifyConnectionListeners(false);

                // Attempt reconnection
                if (this.options.reconnect) {
                    this.scheduleReconnect();
                }
            };
        } catch (error) {
            this.log('Connection error:', error);
            if (this.options.reconnect) {
                this.scheduleReconnect();
            }
        }
    }

    /**
     * Disconnect from WebSocket server
     */
    disconnect() {
        this.options.reconnect = false;
        
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }

        this.stopHeartbeat();

        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }

        this.isConnected = false;
    }

    /**
     * Schedule reconnection
     */
    scheduleReconnect() {
        if (this.reconnectAttempts >= this.options.reconnectMaxAttempts) {
            this.log('Max reconnection attempts reached');
            return;
        }

        this.reconnectAttempts++;
        const delay = this.options.reconnectInterval * Math.min(this.reconnectAttempts, 5);
        
        this.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

        this.reconnectTimer = setTimeout(() => {
            this.connect();
        }, delay);
    }

    /**
     * Send message
     */
    send(type, data = {}) {
        const message = {
            type,
            data,
            timestamp: new Date().toISOString()
        };

        if (this.isConnected && this.ws.readyState === WebSocket.OPEN) {
            try {
                this.ws.send(JSON.stringify(message));
                this.log('Sent message:', message);
            } catch (error) {
                this.log('Error sending message:', error);
                this.messageQueue.push(message);
            }
        } else {
            this.log('Not connected, queuing message');
            this.messageQueue.push(message);
        }
    }

    /**
     * Flush message queue
     */
    flushMessageQueue() {
        while (this.messageQueue.length > 0) {
            const message = this.messageQueue.shift();
            try {
                this.ws.send(JSON.stringify(message));
                this.log('Sent queued message:', message);
            } catch (error) {
                this.log('Error sending queued message:', error);
                // Put it back in the queue
                this.messageQueue.unshift(message);
                break;
            }
        }
    }

    /**
     * Handle incoming message
     */
    handleMessage(message) {
        this.log('Received message:', message);

        const { type, data } = message;

        // Handle heartbeat response
        if (type === 'pong') {
            return;
        }

        // Call registered handlers
        const handlers = this.messageHandlers.get(type);
        if (handlers) {
            handlers.forEach(handler => {
                try {
                    handler(data, message);
                } catch (error) {
                    this.log('Error in message handler:', error);
                }
            });
        }

        // Call wildcard handlers
        const wildcardHandlers = this.messageHandlers.get('*');
        if (wildcardHandlers) {
            wildcardHandlers.forEach(handler => {
                try {
                    handler(data, message);
                } catch (error) {
                    this.log('Error in wildcard handler:', error);
                }
            });
        }
    }

    /**
     * Register message handler
     */
    on(type, handler) {
        if (!this.messageHandlers.has(type)) {
            this.messageHandlers.set(type, new Set());
        }
        this.messageHandlers.get(type).add(handler);

        // Return unsubscribe function
        return () => {
            const handlers = this.messageHandlers.get(type);
            if (handlers) {
                handlers.delete(handler);
            }
        };
    }

    /**
     * Remove message handler
     */
    off(type, handler) {
        const handlers = this.messageHandlers.get(type);
        if (handlers) {
            handlers.delete(handler);
        }
    }

    /**
     * Remove all handlers for a type
     */
    offAll(type) {
        this.messageHandlers.delete(type);
    }

    /**
     * Register connection listener
     */
    onConnection(listener) {
        this.connectionListeners.add(listener);
        
        // Immediately notify with current state
        listener(this.isConnected);

        // Return unsubscribe function
        return () => {
            this.connectionListeners.delete(listener);
        };
    }

    /**
     * Notify connection listeners
     */
    notifyConnectionListeners(connected) {
        this.connectionListeners.forEach(listener => {
            try {
                listener(connected);
            } catch (error) {
                this.log('Error in connection listener:', error);
            }
        });
    }

    /**
     * Start heartbeat
     */
    startHeartbeat() {
        if (!this.options.heartbeatInterval) return;

        this.heartbeatTimer = setInterval(() => {
            if (this.isConnected) {
                this.send('ping');
            }
        }, this.options.heartbeatInterval);
    }

    /**
     * Stop heartbeat
     */
    stopHeartbeat() {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }
    }

    /**
     * Get connection state
     */
    getState() {
        if (!this.ws) return 'CLOSED';
        
        const states = {
            [WebSocket.CONNECTING]: 'CONNECTING',
            [WebSocket.OPEN]: 'OPEN',
            [WebSocket.CLOSING]: 'CLOSING',
            [WebSocket.CLOSED]: 'CLOSED'
        };

        return states[this.ws.readyState] || 'UNKNOWN';
    }

    /**
     * Check if connected
     */
    connected() {
        return this.isConnected;
    }

    /**
     * Debug logging
     */
    log(...args) {
        if (this.options.debug) {
            console.log('[WebSocket]', ...args);
        }
    }
}

/**
 * Server-Sent Events Manager
 * Alternative to WebSocket for one-way real-time updates
 */
class SSEManager {
    constructor(url, options = {}) {
        this.url = url;
        this.options = {
            reconnect: true,
            reconnectInterval: 3000,
            ...options
        };

        this.eventSource = null;
        this.messageHandlers = new Map();
        this.connectionListeners = new Set();
        this.isConnected = false;

        if (this.url) {
            this.connect();
        }
    }

    /**
     * Connect to SSE endpoint
     */
    connect() {
        if (this.eventSource) {
            this.disconnect();
        }

        try {
            this.eventSource = new EventSource(this.url);

            this.eventSource.onopen = () => {
                this.isConnected = true;
                this.notifyConnectionListeners(true);
            };

            this.eventSource.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    this.handleMessage(message);
                } catch (error) {
                    console.error('Error parsing SSE message:', error);
                }
            };

            this.eventSource.onerror = () => {
                this.isConnected = false;
                this.notifyConnectionListeners(false);

                if (this.options.reconnect) {
                    setTimeout(() => {
                        this.connect();
                    }, this.options.reconnectInterval);
                }
            };
        } catch (error) {
            console.error('SSE connection error:', error);
        }
    }

    /**
     * Disconnect from SSE
     */
    disconnect() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
            this.isConnected = false;
            this.notifyConnectionListeners(false);
        }
    }

    /**
     * Handle incoming message
     */
    handleMessage(message) {
        const { type, data } = message;

        const handlers = this.messageHandlers.get(type);
        if (handlers) {
            handlers.forEach(handler => {
                try {
                    handler(data, message);
                } catch (error) {
                    console.error('Error in SSE handler:', error);
                }
            });
        }

        const wildcardHandlers = this.messageHandlers.get('*');
        if (wildcardHandlers) {
            wildcardHandlers.forEach(handler => {
                try {
                    handler(data, message);
                } catch (error) {
                    console.error('Error in SSE wildcard handler:', error);
                }
            });
        }
    }

    /**
     * Register message handler
     */
    on(type, handler) {
        if (!this.messageHandlers.has(type)) {
            this.messageHandlers.set(type, new Set());
        }
        this.messageHandlers.get(type).add(handler);

        return () => {
            const handlers = this.messageHandlers.get(type);
            if (handlers) {
                handlers.delete(handler);
            }
        };
    }

    /**
     * Register connection listener
     */
    onConnection(listener) {
        this.connectionListeners.add(listener);
        listener(this.isConnected);

        return () => {
            this.connectionListeners.delete(listener);
        };
    }

    /**
     * Notify connection listeners
     */
    notifyConnectionListeners(connected) {
        this.connectionListeners.forEach(listener => {
            try {
                listener(connected);
            } catch (error) {
                console.error('Error in SSE connection listener:', error);
            }
        });
    }

    /**
     * Check if connected
     */
    connected() {
        return this.isConnected;
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { WebSocketManager, SSEManager };
}
