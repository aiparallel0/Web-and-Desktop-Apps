/**
 * WebSocket Manager
 * Handles real-time communication with automatic reconnection
 */

class WebSocketManager {
    constructor() {
        this.ws = null;
        this.url = this.getWebSocketUrl();
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectDelay = 1000;
        this.heartbeatInterval = null;
        this.messageHandlers = new Map();
        this.connectionState = 'disconnected';
        this.eventListeners = new Map();
        this.messageQueue = [];
    }

    getWebSocketUrl() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        return `${protocol}//${host}/ws`;
    }

    connect() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            console.log('WebSocket already connected');
            return Promise.resolve();
        }

        return new Promise((resolve, reject) => {
            try {
                this.ws = new WebSocket(this.url);
                this.connectionState = 'connecting';
                this.emit('connecting');

                this.ws.onopen = () => {
                    console.log('WebSocket connected');
                    this.connectionState = 'connected';
                    this.reconnectAttempts = 0;
                    this.emit('connected');
                    this.startHeartbeat();
                    this.flushMessageQueue();
                    resolve();
                };

                this.ws.onmessage = (event) => {
                    this.handleMessage(event.data);
                };

                this.ws.onerror = (error) => {
                    console.error('WebSocket error:', error);
                    this.emit('error', error);
                    reject(error);
                };

                this.ws.onclose = (event) => {
                    console.log('WebSocket closed:', event.code, event.reason);
                    this.connectionState = 'disconnected';
                    this.emit('disconnected', { code: event.code, reason: event.reason });
                    this.stopHeartbeat();
                    this.attemptReconnect();
                };

            } catch (error) {
                console.error('Failed to create WebSocket:', error);
                reject(error);
            }
        });
    }

    disconnect() {
        if (this.ws) {
            this.stopHeartbeat();
            this.ws.close(1000, 'Client disconnect');
            this.ws = null;
            this.connectionState = 'disconnected';
        }
    }

    send(type, data) {
        const message = {
            type,
            data,
            timestamp: Date.now()
        };

        if (this.connectionState !== 'connected') {
            this.messageQueue.push(message);
            return false;
        }

        try {
            this.ws.send(JSON.stringify(message));
            return true;
        } catch (error) {
            console.error('Failed to send message:', error);
            this.messageQueue.push(message);
            return false;
        }
    }

    on(type, handler) {
        if (!this.messageHandlers.has(type)) {
            this.messageHandlers.set(type, new Set());
        }
        this.messageHandlers.get(type).add(handler);

        return () => this.off(type, handler);
    }

    off(type, handler) {
        const handlers = this.messageHandlers.get(type);
        if (handlers) {
            handlers.delete(handler);
        }
    }

    addEventListener(event, callback) {
        if (!this.eventListeners.has(event)) {
            this.eventListeners.set(event, new Set());
        }
        this.eventListeners.get(event).add(callback);
    }

    removeEventListener(event, callback) {
        const listeners = this.eventListeners.get(event);
        if (listeners) {
            listeners.delete(callback);
        }
    }

    emit(event, data) {
        const listeners = this.eventListeners.get(event);
        if (listeners) {
            listeners.forEach(callback => callback(data));
        }
    }

    handleMessage(rawData) {
        try {
            const message = JSON.parse(rawData);
            
            if (message.type === 'pong') {
                return; // Heartbeat response
            }

            const handlers = this.messageHandlers.get(message.type);
            if (handlers) {
                handlers.forEach(handler => {
                    try {
                        handler(message.data);
                    } catch (error) {
                        console.error(`Error in message handler for "${message.type}":`, error);
                    }
                });
            }

            this.emit('message', message);

        } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
        }
    }

    startHeartbeat() {
        this.heartbeatInterval = setInterval(() => {
            if (this.connectionState === 'connected') {
                this.send('ping', {});
            }
        }, 30000); // 30 seconds
    }

    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }

    attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnect attempts reached');
            this.emit('reconnect-failed');
            return;
        }

        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

        console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);

        setTimeout(() => {
            this.connect().catch(error => {
                console.error('Reconnect failed:', error);
            });
        }, delay);
    }

    flushMessageQueue() {
        while (this.messageQueue.length > 0) {
            const message = this.messageQueue.shift();
            this.send(message.type, message.data);
        }
    }

    getState() {
        return this.connectionState;
    }

    isConnected() {
        return this.connectionState === 'connected';
    }
}

const wsManager = new WebSocketManager();

if (typeof window !== 'undefined') {
    window.WebSocketManager = wsManager;
}

export default wsManager;
