/**
 * Comprehensive API Client
 * Handles all backend communication with retry logic, caching, and error handling
 */

class APIClient {
    constructor() {
        this.baseURL = this.detectBackendUrl();
        this.requestCache = new Map();
        this.cacheTimeout = 5 * 60 * 1000; // 5 minutes
        this.retryAttempts = 3;
        this.retryDelay = 1000;
        this.requestInterceptors = [];
        this.responseInterceptors = [];
    }

    detectBackendUrl() {
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
     * Make HTTP request with retry logic
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        // Run request interceptors
        for (const interceptor of this.requestInterceptors) {
            await interceptor(config);
        }

        // Check cache for GET requests
        if (config.method === 'GET' && !options.skipCache) {
            const cached = this.getFromCache(url);
            if (cached) {
                return cached;
            }
        }

        let lastError;
        for (let attempt = 0; attempt < this.retryAttempts; attempt++) {
            try {
                const response = await fetch(url, config);
                
                // Run response interceptors
                for (const interceptor of this.responseInterceptors) {
                    await interceptor(response);
                }

                if (!response.ok) {
                    const error = await this.handleErrorResponse(response);
                    throw error;
                }

                const data = await response.json();

                // Cache GET requests
                if (config.method === 'GET') {
                    this.setCache(url, data);
                }

                return data;
            } catch (error) {
                lastError = error;
                
                // Don't retry on client errors
                if (error.status >= 400 && error.status < 500) {
                    throw error;
                }

                // Wait before retrying
                if (attempt < this.retryAttempts - 1) {
                    await this.delay(this.retryDelay * (attempt + 1));
                }
            }
        }

        throw lastError;
    }

    /**
     * Handle error responses
     */
    async handleErrorResponse(response) {
        let message = `HTTP error! status: ${response.status}`;
        try {
            const data = await response.json();
            message = data.message || data.error || message;
        } catch (e) {
            // Response not JSON
        }

        const error = new Error(message);
        error.status = response.status;
        error.response = response;
        return error;
    }

    /**
     * Cache management
     */
    getFromCache(key) {
        const cached = this.requestCache.get(key);
        if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
            return cached.data;
        }
        return null;
    }

    setCache(key, data) {
        this.requestCache.set(key, {
            data,
            timestamp: Date.now()
        });
    }

    clearCache(pattern = null) {
        if (pattern) {
            for (const [key] of this.requestCache) {
                if (key.includes(pattern)) {
                    this.requestCache.delete(key);
                }
            }
        } else {
            this.requestCache.clear();
        }
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Interceptors
     */
    addRequestInterceptor(fn) {
        this.requestInterceptors.push(fn);
    }

    addResponseInterceptor(fn) {
        this.responseInterceptors.push(fn);
    }

    // =============================================================================
    // EXTRACTION APIs
    // =============================================================================

    async extract(file, options = {}) {
        const formData = new FormData();
        formData.append('image', file);
        
        if (options.modelId) {
            formData.append('model_id', options.modelId);
        }
        
        if (options.detectionSettings) {
            Object.keys(options.detectionSettings).forEach(key => {
                const value = options.detectionSettings[key];
                if (value !== null && value !== undefined) {
                    formData.append(key, typeof value === 'object' ? JSON.stringify(value) : value);
                }
            });
        }

        return this.request('/api/extract', {
            method: 'POST',
            body: formData,
            headers: {} // Let browser set Content-Type for FormData
        });
    }

    async quickExtract(file, options = {}) {
        return this.extract(file, options);
    }

    async batchExtract(files, options = {}) {
        const formData = new FormData();
        files.forEach((file, index) => {
            formData.append(`files[${index}]`, file);
        });
        
        if (options.modelId) {
            formData.append('model_id', options.modelId);
        }

        return this.request('/api/batch-extract', {
            method: 'POST',
            body: formData,
            headers: {}
        });
    }

    async getExtraction(id) {
        return this.request(`/api/extractions/${id}`);
    }

    async listExtractions(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(`/api/extractions?${query}`);
    }

    async deleteExtraction(id) {
        return this.request(`/api/extractions/${id}`, {
            method: 'DELETE'
        });
    }

    async reprocessExtraction(id, options = {}) {
        return this.request(`/api/extractions/${id}/reprocess`, {
            method: 'POST',
            body: JSON.stringify(options)
        });
    }

    // =============================================================================
    // BATCH PROCESSING APIs
    // =============================================================================

    async createBatchJob(files, options = {}) {
        const formData = new FormData();
        files.forEach((file, index) => {
            formData.append(`files`, file);
        });
        
        if (options.name) formData.append('name', options.name);
        if (options.modelId) formData.append('model_id', options.modelId);
        if (options.priority) formData.append('priority', options.priority);

        return this.request('/api/batch', {
            method: 'POST',
            body: formData,
            headers: {}
        });
    }

    async getBatchJob(id) {
        return this.request(`/api/batch/${id}`);
    }

    async listBatchJobs(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(`/api/batch?${query}`);
    }

    async cancelBatchJob(id) {
        return this.request(`/api/batch/${id}/cancel`, {
            method: 'POST'
        });
    }

    async deleteBatchJob(id) {
        return this.request(`/api/batch/${id}`, {
            method: 'DELETE'
        });
    }

    async downloadBatchResults(id, format = 'json') {
        const response = await fetch(`${this.baseURL}/api/batch/${id}/download?format=${format}`);
        if (!response.ok) throw new Error('Download failed');
        return response.blob();
    }

    // =============================================================================
    // API KEY APIs
    // =============================================================================

    async createApiKey(data) {
        return this.request('/api/keys', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async listApiKeys() {
        return this.request('/api/keys');
    }

    async revokeApiKey(id) {
        return this.request(`/api/keys/${id}/revoke`, {
            method: 'POST'
        });
    }

    async deleteApiKey(id) {
        return this.request(`/api/keys/${id}`, {
            method: 'DELETE'
        });
    }

    async getApiKeyUsage(id, params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(`/api/keys/${id}/usage?${query}`);
    }

    // =============================================================================
    // TEMPLATE APIs
    // =============================================================================

    async createTemplate(data) {
        return this.request('/api/templates', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async listTemplates(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(`/api/templates?${query}`);
    }

    async getTemplate(id) {
        return this.request(`/api/templates/${id}`);
    }

    async updateTemplate(id, data) {
        return this.request(`/api/templates/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    async deleteTemplate(id) {
        return this.request(`/api/templates/${id}`, {
            method: 'DELETE'
        });
    }

    async applyTemplate(templateId, extractionId) {
        return this.request(`/api/templates/${templateId}/apply`, {
            method: 'POST',
            body: JSON.stringify({ extraction_id: extractionId })
        });
    }

    // =============================================================================
    // ANALYTICS APIs
    // =============================================================================

    async getAnalytics(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(`/api/analytics?${query}`);
    }

    async getUsageStats(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(`/api/analytics/usage?${query}`);
    }

    async getModelStats(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(`/api/analytics/models?${query}`);
    }

    async getExtractionTrends(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(`/api/analytics/trends?${query}`);
    }

    // =============================================================================
    // MODEL APIs
    // =============================================================================

    async listModels() {
        return this.request('/api/models');
    }

    async getModel(id) {
        return this.request(`/api/models/${id}`);
    }

    async benchmarkModels(file) {
        const formData = new FormData();
        formData.append('image', file);

        return this.request('/api/models/benchmark', {
            method: 'POST',
            body: formData,
            headers: {}
        });
    }

    // =============================================================================
    // USER APIs
    // =============================================================================

    async getProfile() {
        return this.request('/api/user/profile');
    }

    async updateProfile(data) {
        return this.request('/api/user/profile', {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    async updatePreferences(data) {
        return this.request('/api/user/preferences', {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    async uploadAvatar(file) {
        const formData = new FormData();
        formData.append('avatar', file);

        return this.request('/api/user/avatar', {
            method: 'POST',
            body: formData,
            headers: {}
        });
    }

    // =============================================================================
    // AUTHENTICATION APIs
    // =============================================================================

    async login(email, password) {
        return this.request('/api/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });
    }

    async register(data) {
        return this.request('/api/auth/register', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async logout() {
        return this.request('/api/auth/logout', {
            method: 'POST'
        });
    }

    async refreshToken() {
        return this.request('/api/auth/refresh', {
            method: 'POST'
        });
    }

    async resetPassword(email) {
        return this.request('/api/auth/reset-password', {
            method: 'POST',
            body: JSON.stringify({ email })
        });
    }

    async verifyEmail(token) {
        return this.request('/api/auth/verify-email', {
            method: 'POST',
            body: JSON.stringify({ token })
        });
    }

    // =============================================================================
    // BILLING APIs
    // =============================================================================

    async getSubscription() {
        return this.request('/api/billing/subscription');
    }

    async createCheckoutSession(planId) {
        return this.request('/api/billing/checkout', {
            method: 'POST',
            body: JSON.stringify({ plan_id: planId })
        });
    }

    async cancelSubscription() {
        return this.request('/api/billing/subscription/cancel', {
            method: 'POST'
        });
    }

    async updatePaymentMethod(paymentMethodId) {
        return this.request('/api/billing/payment-method', {
            method: 'PUT',
            body: JSON.stringify({ payment_method_id: paymentMethodId })
        });
    }

    async getInvoices(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(`/api/billing/invoices?${query}`);
    }

    // =============================================================================
    // EXPORT APIs
    // =============================================================================

    async exportData(ids, format = 'json') {
        const response = await fetch(`${this.baseURL}/api/export`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ ids, format })
        });

        if (!response.ok) throw new Error('Export failed');
        return response.blob();
    }

    async exportAll(format = 'json', filters = {}) {
        const query = new URLSearchParams({ format, ...filters }).toString();
        const response = await fetch(`${this.baseURL}/api/export/all?${query}`);
        
        if (!response.ok) throw new Error('Export failed');
        return response.blob();
    }

    // =============================================================================
    // WEBHOOK APIs
    // =============================================================================

    async createWebhook(data) {
        return this.request('/api/webhooks', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async listWebhooks() {
        return this.request('/api/webhooks');
    }

    async deleteWebhook(id) {
        return this.request(`/api/webhooks/${id}`, {
            method: 'DELETE'
        });
    }

    async testWebhook(id) {
        return this.request(`/api/webhooks/${id}/test`, {
            method: 'POST'
        });
    }

    // =============================================================================
    // NOTIFICATION APIs
    // =============================================================================

    async getNotifications(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(`/api/notifications?${query}`);
    }

    async markNotificationRead(id) {
        return this.request(`/api/notifications/${id}/read`, {
            method: 'POST'
        });
    }

    async markAllNotificationsRead() {
        return this.request('/api/notifications/read-all', {
            method: 'POST'
        });
    }

    async deleteNotification(id) {
        return this.request(`/api/notifications/${id}`, {
            method: 'DELETE'
        });
    }

    // =============================================================================
    // SEARCH APIs
    // =============================================================================

    async search(query, filters = {}) {
        return this.request('/api/search', {
            method: 'POST',
            body: JSON.stringify({ query, ...filters })
        });
    }

    async searchExtractions(query, filters = {}) {
        return this.request('/api/search/extractions', {
            method: 'POST',
            body: JSON.stringify({ query, ...filters })
        });
    }
}

// Create and export singleton
const apiClient = new APIClient();

if (typeof window !== 'undefined') {
    window.APIClient = apiClient;
}

export default apiClient;
