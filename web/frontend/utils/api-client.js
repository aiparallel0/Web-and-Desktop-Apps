/**
 * API Client - Comprehensive backend communication layer
 * Handles all API requests with retry logic, error handling, and request queueing
 */

class APIClient {
    constructor(baseUrl = null) {
        this.baseUrl = baseUrl || this.detectBaseUrl();
        this.timeout = 120000; // 2 minutes
        this.maxRetries = 3;
        this.retryDelay = 1000;
        this.requestQueue = [];
        this.isProcessingQueue = false;
        this.cache = new Map();
        this.cacheTimeout = 300000; // 5 minutes
        
        // Request interceptors
        this.requestInterceptors = [];
        this.responseInterceptors = [];
        
        // Statistics
        this.stats = {
            totalRequests: 0,
            successfulRequests: 0,
            failedRequests: 0,
            totalRetries: 0,
            avgResponseTime: 0
        };
    }

    detectBaseUrl() {
        if (typeof window !== 'undefined') {
            if (window.RECEIPT_EXTRACTOR_API_URL) {
                return window.RECEIPT_EXTRACTOR_API_URL;
            }
            if (window.location.port === '3000') {
                return `${window.location.protocol}//${window.location.hostname}:5000`;
            }
            return window.location.origin;
        }
        return 'http://localhost:5000';
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
     * Make HTTP request with retry logic
     */
    async request(endpoint, options = {}, retryCount = 0) {
        const url = `${this.baseUrl}${endpoint}`;
        const startTime = performance.now();
        
        this.stats.totalRequests++;

        try {
            // Apply request interceptors
            const config = await this.applyRequestInterceptors({
                url,
                ...options
            });

            // Create abort controller
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.timeout);

            // Make request
            const response = await fetch(config.url, {
                ...config,
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            // Calculate response time
            const endTime = performance.now();
            const responseTime = endTime - startTime;
            
            // Update stats
            this.updateStats(responseTime, response.ok);

            // Apply response interceptors
            const processedResponse = await this.applyResponseInterceptors({
                response,
                responseTime,
                url: config.url
            });

            if (!processedResponse.response.ok) {
                throw new APIError(
                    `HTTP ${processedResponse.response.status}`,
                    processedResponse.response.status,
                    url
                );
            }

            this.stats.successfulRequests++;
            return processedResponse;

        } catch (error) {
            this.stats.failedRequests++;

            // Handle timeout
            if (error.name === 'AbortError') {
                throw new APIError('Request timeout', 408, url);
            }

            // Handle network errors
            if (error instanceof TypeError && error.message === 'Failed to fetch') {
                throw new APIError('Network error - backend may be offline', 0, url);
            }

            // Retry logic
            if (retryCount < this.maxRetries && this.shouldRetry(error)) {
                this.stats.totalRetries++;
                console.warn(`Retry ${retryCount + 1}/${this.maxRetries} for ${url}`);
                
                await this.delay(this.retryDelay * (retryCount + 1));
                return this.request(endpoint, options, retryCount + 1);
            }

            throw error;
        }
    }

    /**
     * Determine if request should be retried
     */
    shouldRetry(error) {
        if (error instanceof APIError) {
            // Retry on server errors (5xx) and some client errors
            return error.status >= 500 || error.status === 408 || error.status === 429;
        }
        return true;
    }

    /**
     * Update statistics
     */
    updateStats(responseTime, success) {
        const totalTime = this.stats.avgResponseTime * (this.stats.totalRequests - 1);
        this.stats.avgResponseTime = (totalTime + responseTime) / this.stats.totalRequests;
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
        // Check cache
        const cacheKey = `GET:${endpoint}`;
        if (this.cache.has(cacheKey)) {
            const cached = this.cache.get(cacheKey);
            if (Date.now() - cached.timestamp < this.cacheTimeout) {
                console.log('Returning cached response for', endpoint);
                return cached.data;
            }
            this.cache.delete(cacheKey);
        }

        const result = await this.request(endpoint, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                ...options.headers
            },
            ...options
        });

        const data = await result.response.json();
        
        // Cache successful GET requests
        if (options.cache !== false) {
            this.cache.set(cacheKey, {
                data,
                timestamp: Date.now()
            });
        }

        return data;
    }

    /**
     * POST request
     */
    async post(endpoint, body = null, options = {}) {
        const isFormData = body instanceof FormData;
        
        return this.request(endpoint, {
            method: 'POST',
            headers: isFormData ? {} : {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                ...options.headers
            },
            body: isFormData ? body : (body ? JSON.stringify(body) : null),
            ...options
        }).then(result => result.response.json());
    }

    /**
     * PUT request
     */
    async put(endpoint, body = null, options = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                ...options.headers
            },
            body: body ? JSON.stringify(body) : null,
            ...options
        }).then(result => result.response.json());
    }

    /**
     * DELETE request
     */
    async delete(endpoint, options = {}) {
        return this.request(endpoint, {
            method: 'DELETE',
            headers: {
                'Accept': 'application/json',
                ...options.headers
            },
            ...options
        }).then(result => result.response.json());
    }

    /**
     * Upload file with progress tracking
     */
    async uploadFile(endpoint, file, additionalData = {}, onProgress = null) {
        const formData = new FormData();
        formData.append('file', file);
        
        for (const [key, value] of Object.entries(additionalData)) {
            if (value !== null && value !== undefined) {
                formData.append(key, typeof value === 'object' ? JSON.stringify(value) : value);
            }
        }

        // For now, we'll use the standard post method
        // In the future, we can implement XMLHttpRequest for progress tracking
        if (onProgress) {
            console.warn('Progress tracking not yet implemented');
        }

        return this.post(endpoint, formData);
    }

    /**
     * Check backend health
     */
    async checkHealth() {
        try {
            const data = await this.get('/api/health', { cache: false });
            return {
                healthy: data.status === 'healthy' || data.status === 'ok',
                data
            };
        } catch (error) {
            return {
                healthy: false,
                error: error.message
            };
        }
    }

    /**
     * Fetch available models
     */
    async fetchModels() {
        return this.get('/api/models');
    }

    /**
     * Extract text from receipt
     */
    async extractReceipt(file, settings = {}) {
        const formData = new FormData();
        formData.append('image', file);
        
        // Add all settings
        const params = {
            model_id: settings.modelId || 'ocr_tesseract',
            detection_mode: settings.detectionMode || 'auto',
            enable_deskew: String(settings.deskewEnabled !== false),
            enable_enhancement: String(settings.enhanceEnabled !== false),
            column_mode: String(settings.detectionMode === 'column')
        };

        for (const [key, value] of Object.entries(params)) {
            formData.append(key, value);
        }

        if (settings.manualRegions && settings.manualRegions.length > 0) {
            formData.append('manual_regions', JSON.stringify(settings.manualRegions));
        }

        return this.post('/api/extract', formData);
    }

    /**
     * Clear cache
     */
    clearCache() {
        this.cache.clear();
    }

    /**
     * Get statistics
     */
    getStats() {
        return { ...this.stats };
    }

    /**
     * Reset statistics
     */
    resetStats() {
        this.stats = {
            totalRequests: 0,
            successfulRequests: 0,
            failedRequests: 0,
            totalRetries: 0,
            avgResponseTime: 0
        };
    }
}

/**
 * Custom API Error class
 */
class APIError extends Error {
    constructor(message, status, url) {
        super(message);
        this.name = 'APIError';
        this.status = status;
        this.url = url;
    }
}

/**
 * Create singleton instance
 */
const apiClient = new APIClient();

// Add default response interceptor for error handling
apiClient.addResponseInterceptor(async (result) => {
    const { response } = result;
    
    if (!response.ok) {
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        try {
            const errorData = await response.json();
            errorMessage = errorData.error || errorData.message || errorMessage;
        } catch (e) {
            // Use default error message
        }
        throw new APIError(errorMessage, response.status, result.url);
    }
    
    return result;
});

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { APIClient, APIError, apiClient };
}

window.APIClient = APIClient;
window.APIError = APIError;
window.apiClient = apiClient;
