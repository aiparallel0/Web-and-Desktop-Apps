/**
 * Main Application Controller
 * Orchestrates all application functionality and state management
 * @version 2.0.0
 */

(function(window) {
    'use strict';

    /**
     * Main Application Controller Class
     * Manages global app state, routing, and component coordination
     */
    class AppController {
        constructor() {
            this.state = {
                user: null,
                isAuthenticated: false,
                currentPage: 'home',
                receipts: [],
                apiKeys: [],
                templates: [],
                batchJobs: [],
                settings: this.loadSettings(),
                stats: {
                    totalExtractions: 0,
                    successRate: 0,
                    avgProcessingTime: 0,
                    apiCalls: 0
                }
            };

            this.listeners = new Map();
            this.init();
        }

        /**
         * Initialize the application
         */
        async init() {
            console.log('[AppController] Initializing application...');
            
            // Check authentication
            await this.checkAuth();
            
            // Load user data if authenticated
            if (this.state.isAuthenticated) {
                await this.loadUserData();
            }
            
            // Setup global event listeners
            this.setupGlobalListeners();
            
            // Setup navigation
            this.setupNavigation();
            
            // Initialize tooltips
            this.initTooltips();
            
            console.log('[AppController] Application initialized successfully');
        }

        /**
         * Check if user is authenticated
         */
        async checkAuth() {
            const token = localStorage.getItem('access_token');
            const userData = localStorage.getItem('user_data');
            
            if (token && userData) {
                try {
                    this.state.user = JSON.parse(userData);
                    this.state.isAuthenticated = true;
                    console.log('[AppController] User authenticated:', this.state.user.email);
                } catch (error) {
                    console.error('[AppController] Error parsing user data:', error);
                    this.logout();
                }
            }
        }

        /**
         * Load user data (receipts, stats, etc.)
         */
        async loadUserData() {
            console.log('[AppController] Loading user data...');
            
            try {
                // Load receipts
                const receipts = await this.api('GET', '/api/receipts');
                if (receipts && receipts.data) {
                    this.state.receipts = receipts.data;
                }
                
                // Load stats
                const stats = await this.api('GET', '/api/stats');
                if (stats) {
                    this.state.stats = stats;
                }
                
                // Load API keys
                const apiKeys = await this.api('GET', '/api/keys');
                if (apiKeys && apiKeys.data) {
                    this.state.apiKeys = apiKeys.data;
                }
                
                // Notify listeners of data update
                this.emit('dataLoaded', this.state);
                
            } catch (error) {
                console.error('[AppController] Error loading user data:', error);
            }
        }

        /**
         * Setup global event listeners
         */
        setupGlobalListeners() {
            // Handle form submissions
            document.addEventListener('submit', (e) => {
                if (e.target.hasAttribute('data-ajax-form')) {
                    e.preventDefault();
                    this.handleFormSubmit(e.target);
                }
            });

            // Handle auth links
            document.addEventListener('click', (e) => {
                if (e.target.hasAttribute('data-auth-action')) {
                    e.preventDefault();
                    const action = e.target.getAttribute('data-auth-action');
                    this.handleAuthAction(action);
                }
            });

            // Handle keyboard shortcuts
            document.addEventListener('keydown', (e) => {
                this.handleKeyboardShortcut(e);
            });

            // Handle online/offline status
            window.addEventListener('online', () => this.emit('networkStatus', true));
            window.addEventListener('offline', () => this.emit('networkStatus', false));
        }

        /**
         * Setup navigation and routing
         */
        setupNavigation() {
            // Handle hash changes
            window.addEventListener('hashchange', () => {
                this.handleRouteChange();
            });

            // Initial route
            this.handleRouteChange();
        }

        /**
         * Handle route changes
         */
        handleRouteChange() {
            const hash = window.location.hash.slice(1) || 'home';
            this.state.currentPage = hash;
            this.emit('routeChanged', hash);
            console.log('[AppController] Route changed to:', hash);
        }

        /**
         * Handle form submissions
         */
        async handleFormSubmit(form) {
            const action = form.getAttribute('action') || '';
            const method = form.getAttribute('method') || 'POST';
            const formData = new FormData(form);
            const data = Object.fromEntries(formData.entries());

            console.log('[AppController] Form submit:', action, method, data);

            try {
                this.showLoading(true);
                const result = await this.api(method, action, data);
                this.showLoading(false);
                
                if (result.success) {
                    this.showToast('Success!', 'success');
                    form.reset();
                    this.emit('formSubmitSuccess', { form, result });
                } else {
                    this.showToast(result.message || 'Error occurred', 'error');
                }
            } catch (error) {
                this.showLoading(false);
                this.showToast('An error occurred. Please try again.', 'error');
                console.error('[AppController] Form submit error:', error);
            }
        }

        /**
         * Handle authentication actions
         */
        handleAuthAction(action) {
            console.log('[AppController] Auth action:', action);
            
            switch (action) {
                case 'login':
                    window.location.href = 'enhanced-login.html';
                    break;
                case 'register':
                    window.location.href = 'enhanced-register.html';
                    break;
                case 'logout':
                    this.logout();
                    break;
                case 'profile':
                    window.location.href = 'dashboard.html#settings';
                    break;
            }
        }

        /**
         * Handle keyboard shortcuts
         */
        handleKeyboardShortcut(e) {
            // Ctrl/Cmd + K - Quick search
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                this.emit('showQuickSearch');
            }
            
            // Ctrl/Cmd + U - Quick upload
            if ((e.ctrlKey || e.metaKey) && e.key === 'u') {
                e.preventDefault();
                this.emit('showQuickUpload');
            }
            
            // Esc - Close modals
            if (e.key === 'Escape') {
                this.emit('closeModals');
            }
        }

        /**
         * Login user
         */
        async login(email, password, rememberMe = false) {
            console.log('[AppController] Logging in:', email);
            
            try {
                const response = await this.api('POST', '/api/auth/login', {
                    email,
                    password,
                    remember_me: rememberMe
                });

                if (response.success) {
                    this.state.user = response.user;
                    this.state.isAuthenticated = true;
                    
                    // Save to storage
                    localStorage.setItem('access_token', response.access_token);
                    localStorage.setItem('user_data', JSON.stringify(response.user));
                    
                    if (response.refresh_token) {
                        localStorage.setItem('refresh_token', response.refresh_token);
                    }
                    
                    // Redirect to dashboard
                    window.location.href = 'dashboard.html';
                    
                    return { success: true };
                } else {
                    return { success: false, message: response.message };
                }
            } catch (error) {
                console.error('[AppController] Login error:', error);
                return { success: false, message: 'An error occurred during login' };
            }
        }

        /**
         * Register new user
         */
        async register(userData) {
            console.log('[AppController] Registering user:', userData.email);
            
            try {
                const response = await this.api('POST', '/api/auth/register', userData);

                if (response.success) {
                    // Auto-login after registration
                    return await this.login(userData.email, userData.password);
                } else {
                    return { success: false, message: response.message };
                }
            } catch (error) {
                console.error('[AppController] Registration error:', error);
                return { success: false, message: 'An error occurred during registration' };
            }
        }

        /**
         * Logout user
         */
        logout() {
            console.log('[AppController] Logging out');
            
            // Clear storage
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('user_data');
            
            // Reset state
            this.state.user = null;
            this.state.isAuthenticated = false;
            this.state.receipts = [];
            this.state.apiKeys = [];
            
            // Redirect to home
            window.location.href = 'index.html';
        }

        /**
         * API call wrapper
         */
        async api(method, endpoint, data = null) {
            const token = localStorage.getItem('access_token');
            const headers = {
                'Content-Type': 'application/json'
            };
            
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }
            
            const options = {
                method,
                headers
            };
            
            if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
                options.body = JSON.stringify(data);
            }
            
            const baseUrl = window.location.origin;
            const url = `${baseUrl}${endpoint}`;
            
            try {
                const response = await fetch(url, options);
                
                // Handle unauthorized
                if (response.status === 401) {
                    this.logout();
                    throw new Error('Unauthorized');
                }
                
                // Parse JSON response
                if (response.headers.get('content-type')?.includes('application/json')) {
                    return await response.json();
                }
                
                return { success: response.ok };
            } catch (error) {
                console.error('[AppController] API error:', error);
                throw error;
            }
        }

        /**
         * Show loading indicator
         */
        showLoading(show = true) {
            const overlay = document.getElementById('loadingOverlay');
            if (overlay) {
                if (show) {
                    overlay.classList.remove('hidden');
                } else {
                    overlay.classList.add('hidden');
                }
            }
            this.emit('loadingStateChanged', show);
        }

        /**
         * Show toast notification
         */
        showToast(message, type = 'info', duration = 3000) {
            // Try to use toast utility if available
            if (window.ToastManager) {
                window.ToastManager.show(message, type);
                return;
            }
            
            // Fallback to simple notification
            const toast = document.createElement('div');
            toast.className = `toast toast-${type}`;
            toast.textContent = message;
            toast.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 16px 24px;
                background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
                color: white;
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                z-index: 10000;
                animation: slideInRight 0.3s ease-out;
            `;
            
            document.body.appendChild(toast);
            
            setTimeout(() => {
                toast.style.animation = 'slideOutRight 0.3s ease-out';
                setTimeout(() => toast.remove(), 300);
            }, duration);
        }

        /**
         * Load settings from storage
         */
        loadSettings() {
            try {
                const settings = localStorage.getItem('app_settings');
                return settings ? JSON.parse(settings) : this.getDefaultSettings();
            } catch (error) {
                console.error('[AppController] Error loading settings:', error);
                return this.getDefaultSettings();
            }
        }

        /**
         * Get default settings
         */
        getDefaultSettings() {
            return {
                theme: 'light',
                defaultModel: 'auto',
                defaultExportFormat: 'json',
                enableNotifications: true,
                enableEmailNotifications: true,
                autoSave: true,
                language: 'en'
            };
        }

        /**
         * Save settings
         */
        saveSettings(settings) {
            this.state.settings = { ...this.state.settings, ...settings };
            localStorage.setItem('app_settings', JSON.stringify(this.state.settings));
            this.emit('settingsChanged', this.state.settings);
            console.log('[AppController] Settings saved:', this.state.settings);
        }

        /**
         * Initialize tooltips
         */
        initTooltips() {
            const tooltips = document.querySelectorAll('[data-tooltip]');
            tooltips.forEach(element => {
                element.addEventListener('mouseenter', (e) => {
                    const text = e.target.getAttribute('data-tooltip');
                    this.showTooltip(e.target, text);
                });
                element.addEventListener('mouseleave', () => {
                    this.hideTooltip();
                });
            });
        }

        /**
         * Show tooltip
         */
        showTooltip(element, text) {
            const tooltip = document.createElement('div');
            tooltip.id = 'app-tooltip';
            tooltip.className = 'tooltip';
            tooltip.textContent = text;
            tooltip.style.cssText = `
                position: absolute;
                padding: 8px 12px;
                background: #1f2937;
                color: white;
                border-radius: 6px;
                font-size: 14px;
                z-index: 10001;
                pointer-events: none;
                white-space: nowrap;
            `;
            
            document.body.appendChild(tooltip);
            
            const rect = element.getBoundingClientRect();
            tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
            tooltip.style.top = rect.bottom + 8 + 'px';
        }

        /**
         * Hide tooltip
         */
        hideTooltip() {
            const tooltip = document.getElementById('app-tooltip');
            if (tooltip) {
                tooltip.remove();
            }
        }

        /**
         * Event emitter - subscribe to events
         */
        on(event, callback) {
            if (!this.listeners.has(event)) {
                this.listeners.set(event, new Set());
            }
            this.listeners.get(event).add(callback);
        }

        /**
         * Event emitter - unsubscribe from events
         */
        off(event, callback) {
            if (this.listeners.has(event)) {
                this.listeners.get(event).delete(callback);
            }
        }

        /**
         * Event emitter - emit event
         */
        emit(event, data) {
            if (this.listeners.has(event)) {
                this.listeners.get(event).forEach(callback => {
                    try {
                        callback(data);
                    } catch (error) {
                        console.error(`[AppController] Error in event listener for ${event}:`, error);
                    }
                });
            }
        }

        /**
         * Get current state
         */
        getState() {
            return { ...this.state };
        }

        /**
         * Update state
         */
        setState(updates) {
            this.state = { ...this.state, ...updates };
            this.emit('stateChanged', this.state);
        }
    }

    // Create global app instance
    window.App = new AppController();
    
    // Export for ES6 modules
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = AppController;
    }

})(window);
