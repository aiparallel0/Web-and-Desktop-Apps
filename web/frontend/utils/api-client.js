/**
 * API Client - Centralized API communication layer
 * Handles all HTTP requests with authentication, error handling, and retries
 */

class APIClient {
    constructor(baseURL = '') {
        this.baseURL = baseURL || this.detectBackendURL();
        this.defaultHeaders = {
            'Content-Type': 'application/json'
        };
        this.requestInterceptors = [];
        this.responseInterceptors = [];
        this.authManager = null;
    }

    /**
     * Detect backend URL based on environment
     */
    detectBackendURL() {
        if (window.RECEIPT_EXTRACTOR_API_URL) {
            return window.RECEIPT_EXTRACTOR_API_URL;
        }
        
        const FRONTEND_DEV_PORT = '3000';
        const BACKEND_DEV_PORT = '5000';
        
        if (window.location.port === FRONTEND_DEV_PORT) {
            return `${window.location.protocol}//${window.location.hostname}:${BACKEND_DEV_PORT}`;
        }
        
        return window.location.origin;
    }

    /**
     * Set auth manager for authenticated requests
     */
    setAuthManager(authManager) {
        this.authManager = authManager;
    }

    /**
     * Add request interceptor
     */
    addRequestInterceptor(interceptor) {
        this.requestInterceptors.push(interceptor);
    }

    /**
     * Add response interceptor
     */
    addResponseInterceptor(interceptor) {
        this.responseInterceptors.push(interceptor);
    }

    /**
     * Build full URL
     */
    buildURL(endpoint) {
        if (endpoint.startsWith('http://') || endpoint.startsWith('https://')) {
            return endpoint;
        }
        const cleanBase = this.baseURL.replace(/\/$/, '');
        const cleanEndpoint = endpoint.replace(/^\//, '');
        return `${cleanBase}/${cleanEndpoint}`;
    }

    /**
     * Apply request interceptors
     */
    async applyRequestInterceptors(config) {
        let modifiedConfig = { ...config };
        for (const interceptor of this.requestInterceptors) {
            modifiedConfig = await interceptor(modifiedConfig);
        }
        return modifiedConfig;
    }

    /**
     * Apply response interceptors
     */
    async applyResponseInterceptors(response) {
        let modifiedResponse = response;
        for (const interceptor of this.responseInterceptors) {
            modifiedResponse = await interceptor(modifiedResponse);
        }
        return modifiedResponse;
    }

    /**
     * Make HTTP request
     */
    async request(endpoint, options = {}) {
        const {
            method = 'GET',
            headers = {},
            body = null,
            auth = false,
            retry = 0,
            timeout = 30000,
            ...restOptions
        } = options;

        // Build request config
        let config = {
            method,
            headers: {
                ...this.defaultHeaders,
                ...headers
            },
            ...restOptions
        };

        // Add auth header if needed
        if (auth && this.authManager) {
            const token = this.authManager.getAccessToken();
            if (token) {
                config.headers['Authorization'] = `Bearer ${token}`;
            }
        }

        // Add body if provided
        if (body) {
            if (body instanceof FormData) {
                // Don't set Content-Type for FormData - browser will set it with boundary
                delete config.headers['Content-Type'];
                config.body = body;
            } else if (typeof body === 'object') {
                config.body = JSON.stringify(body);
            } else {
                config.body = body;
            }
        }

        // Apply request interceptors
        config = await this.applyRequestInterceptors(config);

        // Build full URL
        const url = this.buildURL(endpoint);

        // Create abort controller for timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);
        config.signal = controller.signal;

        try {
            // Make request
            let response = await fetch(url, config);

            // Clear timeout
            clearTimeout(timeoutId);

            // Apply response interceptors
            response = await this.applyResponseInterceptors(response);

            // Handle 401 with token refresh if authenticated
            if (response.status === 401 && auth && this.authManager) {
                const refreshed = await this.authManager.refreshAccessToken();
                if (refreshed) {
                    // Retry with new token
                    const newToken = this.authManager.getAccessToken();
                    config.headers['Authorization'] = `Bearer ${newToken}`;
                    response = await fetch(url, config);
                }
            }

            // Parse response
            const contentType = response.headers.get('content-type');
            let data;

            if (contentType && contentType.includes('application/json')) {
                data = await response.json();
            } else if (contentType && contentType.includes('text')) {
                data = await response.text();
            } else {
                data = await response.blob();
            }

            // Return standardized response
            if (response.ok) {
                return {
                    success: true,
                    data,
                    status: response.status,
                    headers: response.headers
                };
            } else {
                // Error response
                const error = {
                    success: false,
                    error: data.message || data.error || 'Request failed',
                    status: response.status,
                    data
                };

                // Retry on specific errors
                if (retry > 0 && this.shouldRetry(response.status)) {
                    await this.delay(1000 * (3 - retry)); // Exponential backoff
                    return this.request(endpoint, { ...options, retry: retry - 1 });
                }

                return error;
            }
        } catch (error) {
            clearTimeout(timeoutId);

            // Handle network errors
            if (error.name === 'AbortError') {
                return {
                    success: false,
                    error: 'Request timeout',
                    status: 408
                };
            }

            // Retry on network errors
            if (retry > 0) {
                await this.delay(1000 * (3 - retry));
                return this.request(endpoint, { ...options, retry: retry - 1 });
            }

            return {
                success: false,
                error: error.message || 'Network error',
                status: 0
            };
        }
    }

    /**
     * Check if request should be retried
     */
    shouldRetry(status) {
        return status >= 500 || status === 429; // Server errors or rate limit
    }

    /**
     * Delay helper for retries
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * GET request
     */
    async get(endpoint, options = {}) {
        return this.request(endpoint, {
            method: 'GET',
            ...options
        });
    }

    /**
     * POST request
     */
    async post(endpoint, body, options = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body,
            ...options
        });
    }

    /**
     * PUT request
     */
    async put(endpoint, body, options = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body,
            ...options
        });
    }

    /**
     * PATCH request
     */
    async patch(endpoint, body, options = {}) {
        return this.request(endpoint, {
            method: 'PATCH',
            body,
            ...options
        });
    }

    /**
     * DELETE request
     */
    async delete(endpoint, options = {}) {
        return this.request(endpoint, {
            method: 'DELETE',
            ...options
        });
    }

    /**
     * Upload file(s)
     */
    async upload(endpoint, files, additionalData = {}, options = {}) {
        const formData = new FormData();

        // Add files
        if (Array.isArray(files)) {
            files.forEach((file, index) => {
                formData.append(`file${index}`, file);
            });
        } else {
            formData.append('file', files);
        }

        // Add additional data
        Object.keys(additionalData).forEach(key => {
            const value = additionalData[key];
            if (typeof value === 'object') {
                formData.append(key, JSON.stringify(value));
            } else {
                formData.append(key, value);
            }
        });

        return this.post(endpoint, formData, options);
    }

    /**
     * Download file
     */
    async download(endpoint, filename, options = {}) {
        try {
            const response = await this.request(endpoint, {
                ...options,
                headers: {
                    ...options.headers
                }
            });

            if (!response.success) {
                throw new Error(response.error);
            }

            // Create download link
            const blob = response.data;
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            return { success: true };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    /**
     * Stream SSE events
     */
    streamEvents(endpoint, onMessage, onError = null, options = {}) {
        const url = this.buildURL(endpoint);
        const eventSource = new EventSource(url);

        eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                onMessage(data);
            } catch (error) {
                console.error('Error parsing SSE event:', error);
            }
        };

        eventSource.onerror = (error) => {
            console.error('SSE error:', error);
            if (onError) {
                onError(error);
            }
            eventSource.close();
        };

        return {
            close: () => eventSource.close()
        };
    }
}

// API Endpoints Registry
const API_ENDPOINTS = {
    // Auth endpoints
    AUTH: {
        LOGIN: '/api/auth/login',
        REGISTER: '/api/auth/register',
        LOGOUT: '/api/auth/logout',
        REFRESH: '/api/auth/refresh',
        ME: '/api/auth/me',
        UPDATE_PROFILE: '/api/auth/update-profile',
        CHANGE_PASSWORD: '/api/auth/change-password',
        FORGOT_PASSWORD: '/api/auth/forgot-password',
        RESET_PASSWORD: '/api/auth/reset-password'
    },

    // Receipt endpoints
    RECEIPTS: {
        QUICK_EXTRACT: '/api/quick-extract',
        EXTRACT: '/api/extract',
        LIST: '/api/receipts',
        GET: (id) => `/api/receipts/${id}`,
        UPDATE: (id) => `/api/receipts/${id}`,
        DELETE: (id) => `/api/receipts/${id}`,
        STATS: '/api/receipts/stats',
        EXPORT: (id) => `/api/receipts/${id}/export`,
        BATCH_EXTRACT: '/api/batch-extract',
        BATCH_STATUS: (jobId) => `/api/batch/${jobId}/status`,
        BATCH_RESULTS: (jobId) => `/api/batch/${jobId}/results`
    },

    // Model endpoints
    MODELS: {
        LIST: '/api/models',
        SELECT: '/api/models/select',
        INFO: (modelId) => `/api/models/${modelId}`,
        BENCHMARK: '/api/models/benchmark'
    },

    // Settings endpoints
    SETTINGS: {
        GET: '/api/settings',
        UPDATE: '/api/settings',
        API_KEYS: '/api/settings/api-keys',
        CREATE_API_KEY: '/api/settings/api-keys/create',
        DELETE_API_KEY: (keyId) => `/api/settings/api-keys/${keyId}`,
        WEBHOOKS: '/api/settings/webhooks',
        TEMPLATES: '/api/settings/templates'
    },

    // Billing endpoints
    BILLING: {
        SUBSCRIPTION: '/api/billing/subscription',
        CREATE_CHECKOUT: '/api/billing/create-checkout',
        CANCEL: '/api/billing/cancel',
        USAGE: '/api/billing/usage',
        INVOICES: '/api/billing/invoices'
    },

    // Analytics endpoints
    ANALYTICS: {
        OVERVIEW: '/api/analytics/overview',
        CHARTS: '/api/analytics/charts',
        EXPORT: '/api/analytics/export'
    },

    // Health check
    HEALTH: '/api/health'
};

// Create singleton instance
const apiClient = new APIClient();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { apiClient, API_ENDPOINTS };
}
