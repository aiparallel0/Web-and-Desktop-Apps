/**
 * Enhanced Main Application Controller
 * Integrates all utilities and manages application state
 */

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', async () => {
    // Initialize application
    const app = new EnhancedApp();
    await app.init();
    
    // Make app globally available for debugging
    window.app = app;
});

class EnhancedApp {
    constructor() {
        this.initialized = false;
        this.currentUser = null;
        this.currentReceipt = null;
        
        // Initialize managers (will be set up in init())
        this.state = null;
        this.receiptManager = null;
        this.batchProcessor = null;
    }

    /**
     * Initialize application
     */
    async init() {
        if (this.initialized) return;

        console.log('Initializing Enhanced Receipt Extractor...');

        try {
            // Initialize state manager
            this.initStateManager();

            // Initialize API client with auth
            if (typeof apiClient !== 'undefined') {
                if (typeof authManager !== 'undefined') {
                    apiClient.setAuthManager(authManager);
                }
            }

            // Initialize receipt manager
            if (typeof ReceiptManager !== 'undefined' && typeof apiClient !== 'undefined') {
                this.receiptManager = new ReceiptManager(apiClient, authManager);
            }

            // Initialize batch processor
            if (typeof BatchProcessor !== 'undefined' && typeof apiClient !== 'undefined') {
                this.batchProcessor = new BatchProcessor(apiClient);
                this.setupBatchProcessorListeners();
            }

            // Setup auth listeners
            this.setupAuthListeners();

            // Setup UI event listeners
            this.setupUIListeners();

            // Setup upload zone
            this.setupUploadZone();

            // Check authentication status
            this.checkAuthStatus();

            // Setup analytics
            if (typeof analytics !== 'undefined') {
                analytics.trackEvent('app_initialized', {
                    version: '2.0.0',
                    timestamp: new Date().toISOString()
                });
            }

            this.initialized = true;
            console.log('✓ Application initialized successfully');

            // Show welcome message for first-time users
            this.showWelcomeMessage();

        } catch (error) {
            console.error('Failed to initialize application:', error);
            if (typeof toast !== 'undefined') {
                toast.error('Failed to initialize application. Please refresh the page.', 'Initialization Error');
            }
        }
    }

    /**
     * Initialize state manager
     */
    initStateManager() {
        if (typeof StateManager !== 'undefined') {
            this.state = new StateManager({
                isAuthenticated: false,
                user: null,
                currentFile: null,
                currentResults: null,
                selectedModel: 'ocr_easyocr',
                extractionMode: 'auto',
                darkMode: false,
                showTutorial: true
            }, {
                persist: true,
                persistKey: 'receipt_extractor_state',
                persistFields: ['selectedModel', 'extractionMode', 'darkMode', 'showTutorial']
            });

            // Subscribe to dark mode changes
            this.state.subscribe('darkMode', (darkMode) => {
                this.toggleDarkMode(darkMode);
            });

            // Apply initial dark mode setting
            if (this.state.get('darkMode')) {
                this.toggleDarkMode(true);
            }
        }
    }

    /**
     * Setup authentication listeners
     */
    setupAuthListeners() {
        if (typeof authManager === 'undefined') return;

        authManager.addAuthListener((isAuth) => {
            this.onAuthStateChange(isAuth);
        });
    }

    /**
     * Check authentication status
     */
    checkAuthStatus() {
        if (typeof authManager === 'undefined') return;

        const isAuth = authManager.isAuthenticated();
        this.onAuthStateChange(isAuth);
    }

    /**
     * Handle auth state changes
     */
    onAuthStateChange(isAuthenticated) {
        if (this.state) {
            this.state.set('isAuthenticated', isAuthenticated);
        }

        // Update UI elements
        this.updateAuthUI(isAuthenticated);

        if (isAuthenticated && typeof authManager !== 'undefined') {
            this.currentUser = authManager.getUser();
            if (this.state) {
                this.state.set('user', this.currentUser);
            }

            // Load user's receipts if on dashboard
            if (window.location.pathname.includes('dashboard')) {
                this.loadUserReceipts();
            }
        } else {
            this.currentUser = null;
            if (this.state) {
                this.state.set('user', null);
            }
        }
    }

    /**
     * Update authentication UI
     */
    updateAuthUI(isAuthenticated) {
        const signInBtn = document.getElementById('signInBtn');
        const userMenu = document.getElementById('userMenu');

        if (signInBtn) {
            if (isAuthenticated) {
                signInBtn.textContent = 'Dashboard';
                signInBtn.onclick = () => window.location.href = 'dashboard.html';
            } else {
                signInBtn.textContent = 'Sign In';
                signInBtn.onclick = () => this.showLoginModal();
            }
        }

        // Update user menu if exists
        if (userMenu && isAuthenticated && this.currentUser) {
            userMenu.innerHTML = `
                <div class="user-profile">
                    <span>${this.currentUser.name || this.currentUser.email}</span>
                    <button onclick="app.logout()">Logout</button>
                </div>
            `;
        }
    }

    /**
     * Show login modal
     */
    async showLoginModal() {
        if (typeof modal === 'undefined' || typeof FormValidator === 'undefined') {
            window.location.href = 'login.html';
            return;
        }

        const modalId = modal.show({
            title: 'Sign In',
            content: `
                <form id="loginForm" class="modal-form">
                    <div class="modal-form-group">
                        <label class="modal-form-label" for="loginEmail">Email</label>
                        <input type="email" id="loginEmail" name="email" class="modal-form-input" required>
                    </div>
                    <div class="modal-form-group">
                        <label class="modal-form-label" for="loginPassword">Password</label>
                        <input type="password" id="loginPassword" name="password" class="modal-form-input" required>
                    </div>
                    <div class="modal-form-group">
                        <label style="display: flex; align-items: center; gap: 8px; font-size: 14px;">
                            <input type="checkbox" name="rememberMe" checked>
                            <span>Remember me</span>
                        </label>
                    </div>
                </form>
                <p style="margin-top: 16px; text-align: center; font-size: 14px; color: #6B7280;">
                    Don't have an account? <a href="#" onclick="app.showRegisterModal(); event.preventDefault();" style="color: #3B82F6;">Sign up</a>
                </p>
            `,
            footer: `
                <button class="modal-btn modal-btn-secondary" data-action="cancel">Cancel</button>
                <button class="modal-btn modal-btn-primary" data-action="login">Sign In</button>
            `,
            size: 'sm',
            onClose: () => {
                if (loginValidator) {
                    loginValidator.destroy();
                }
            }
        });

        // Setup form validation
        setTimeout(() => {
            const form = document.getElementById('loginForm');
            const loginValidator = new FormValidator(form, {
                email: {
                    required: 'Email is required',
                    email: true
                },
                password: {
                    required: 'Password is required'
                }
            }, {
                validateOnBlur: true,
                onSubmit: async (data) => {
                    await this.handleLogin(data, modalId);
                }
            });

            // Add button listeners
            const loginBtn = document.querySelector('[data-action="login"]');
            const cancelBtn = document.querySelector('[data-action="cancel"]');

            if (loginBtn) {
                loginBtn.addEventListener('click', () => {
                    form.dispatchEvent(new Event('submit'));
                });
            }

            if (cancelBtn) {
                cancelBtn.addEventListener('click', () => {
                    modal.close(modalId);
                });
            }
        }, 0);
    }

    /**
     * Handle login
     */
    async handleLogin(data, modalId) {
        if (typeof authManager === 'undefined') return;

        const result = await authManager.login(data.email, data.password, data.rememberMe);

        if (result.success) {
            if (typeof toast !== 'undefined') {
                toast.success('Welcome back!', 'Login Successful');
            }
            modal.close(modalId);
            
            // Redirect to dashboard or reload
            if (window.location.pathname === '/index.html' || window.location.pathname === '/') {
                window.location.href = 'dashboard.html';
            } else {
                window.location.reload();
            }
        } else {
            if (typeof toast !== 'undefined') {
                toast.error(result.error || 'Login failed', 'Login Error');
            }
        }
    }

    /**
     * Show register modal
     */
    showRegisterModal() {
        // Close login modal if open
        if (typeof modal !== 'undefined') {
            modal.closeAll();
        }
        
        // Redirect to registration page
        window.location.href = 'register.html';
    }

    /**
     * Logout
     */
    async logout() {
        if (typeof authManager === 'undefined') return;

        const confirmed = typeof modal !== 'undefined' 
            ? await modal.confirm({
                title: 'Logout',
                message: 'Are you sure you want to logout?',
                confirmText: 'Logout',
                confirmClass: 'modal-btn-danger'
            })
            : confirm('Are you sure you want to logout?');

        if (confirmed) {
            await authManager.logout();
            
            if (typeof toast !== 'undefined') {
                toast.info('You have been logged out', 'Logged Out');
            }

            // Redirect to home page
            window.location.href = 'index.html';
        }
    }

    /**
     * Setup upload zone
     */
    setupUploadZone() {
        const uploadZone = document.getElementById('mainUploadZone');
        if (!uploadZone) return;

        // Listen for file selected event
        uploadZone.addEventListener('file-selected', (e) => {
            this.handleFileSelected(e.detail.file);
        });
    }

    /**
     * Handle file selected
     */
    async handleFileSelected(file) {
        if (!file) return;

        if (this.state) {
            this.state.set('currentFile', file);
        }

        // Show processing UI
        this.showProcessing();

        try {
            // Get selected model
            const modelId = this.state ? this.state.get('selectedModel') : 'ocr_easyocr';

            // Extract receipt
            const result = await this.extractReceipt(file, modelId);

            if (result.success) {
                this.handleExtractionSuccess(result);
            } else {
                this.handleExtractionError(result.error);
            }
        } catch (error) {
            this.handleExtractionError(error.message);
        }
    }

    /**
     * Extract receipt
     */
    async extractReceipt(file, modelId) {
        if (typeof apiClient === 'undefined') {
            throw new Error('API client not available');
        }

        // Upload file
        const response = await apiClient.upload(
            '/api/quick-extract',
            file,
            { model_id: modelId }
        );

        return response;
    }

    /**
     * Show processing UI
     */
    showProcessing() {
        const processingSection = document.getElementById('processingSection');
        const resultsSection = document.getElementById('resultsSection');

        if (processingSection) {
            processingSection.classList.remove('hidden');
        }
        if (resultsSection) {
            resultsSection.classList.add('hidden');
        }

        // Scroll to processing section
        if (processingSection) {
            processingSection.scrollIntoView({ behavior: 'smooth' });
        }
    }

    /**
     * Handle extraction success
     */
    handleExtractionSuccess(result) {
        if (this.state) {
            this.state.set('currentResults', result.data);
        }
        this.currentReceipt = result.data;

        // Hide processing, show results
        const processingSection = document.getElementById('processingSection');
        const resultsSection = document.getElementById('resultsSection');

        if (processingSection) {
            processingSection.classList.add('hidden');
        }
        if (resultsSection) {
            resultsSection.classList.remove('hidden');
            resultsSection.scrollIntoView({ behavior: 'smooth' });
        }

        // Update results view component
        const resultsView = document.getElementById('extractResults');
        if (resultsView && resultsView.setResults) {
            resultsView.setResults(result.data);
        }

        // Show success toast
        if (typeof toast !== 'undefined') {
            toast.success('Receipt extracted successfully!', 'Success');
        }

        // Track conversion
        if (typeof analytics !== 'undefined') {
            analytics.trackConversion('extraction', 1);
        }

        // Increment extraction count
        if (AppState && AppState.incrementExtractionCount) {
            AppState.incrementExtractionCount();
        }
    }

    /**
     * Handle extraction error
     */
    handleExtractionError(error) {
        // Hide processing section
        const processingSection = document.getElementById('processingSection');
        if (processingSection) {
            processingSection.classList.add('hidden');
        }

        // Show error toast
        if (typeof toast !== 'undefined') {
            toast.error(error || 'Failed to extract receipt', 'Extraction Error');
        }

        // Track error
        if (typeof analytics !== 'undefined') {
            analytics.trackError(new Error(error), {
                context: 'receipt_extraction'
            });
        }
    }

    /**
     * Setup UI listeners
     */
    setupUIListeners() {
        // Upgrade button
        const upgradeBtn = document.getElementById('upgradeBtn');
        if (upgradeBtn) {
            upgradeBtn.addEventListener('click', () => {
                window.location.href = 'pricing.html';
            });
        }

        // Close upgrade banner
        const closeUpgradeBtn = document.getElementById('closeUpgradeBtn');
        if (closeUpgradeBtn) {
            closeUpgradeBtn.addEventListener('click', () => {
                const banner = document.getElementById('upgradeBanner');
                if (banner) {
                    banner.classList.add('hidden');
                }
            });
        }

        // Sign in button (fallback if not handled by auth)
        const signInBtn = document.getElementById('signInBtn');
        if (signInBtn && !signInBtn.onclick) {
            signInBtn.addEventListener('click', () => {
                this.showLoginModal();
            });
        }
    }

    /**
     * Setup batch processor listeners
     */
    setupBatchProcessorListeners() {
        if (!this.batchProcessor) return;

        // Listen for batch updates
        this.batchProcessor.subscribe((stats, items) => {
            this.onBatchUpdate(stats, items);
        });

        // Listen for progress updates
        this.batchProcessor.subscribeToProgress((item) => {
            this.onBatchItemProgress(item);
        });
    }

    /**
     * Handle batch updates
     */
    onBatchUpdate(stats, items) {
        console.log('Batch update:', stats);
        
        // Update UI if on batch page
        const batchStatus = document.getElementById('batchStatus');
        if (batchStatus) {
            batchStatus.innerHTML = `
                <div>Total: ${stats.total}</div>
                <div>Completed: ${stats.completed}</div>
                <div>Failed: ${stats.failed}</div>
                <div>Progress: ${stats.progress}%</div>
            `;
        }
    }

    /**
     * Handle batch item progress
     */
    onBatchItemProgress(item) {
        console.log('Item progress:', item.id, item.progress);
    }

    /**
     * Load user receipts
     */
    async loadUserReceipts() {
        if (!this.receiptManager) return;

        try {
            const result = await this.receiptManager.fetchReceipts();
            if (result.success) {
                console.log('Loaded receipts:', result.receipts.length);
            }
        } catch (error) {
            console.error('Error loading receipts:', error);
        }
    }

    /**
     * Toggle dark mode
     */
    toggleDarkMode(enabled) {
        if (enabled) {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
    }

    /**
     * Show welcome message
     */
    showWelcomeMessage() {
        const isFirstVisit = !localStorage.getItem('visited_before');
        
        if (isFirstVisit && typeof toast !== 'undefined') {
            setTimeout(() => {
                toast.info(
                    'Drag and drop your receipt or click to browse',
                    'Welcome to Receipt Extractor! 👋',
                    { duration: 7000 }
                );
                localStorage.setItem('visited_before', 'true');
            }, 1000);
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EnhancedApp;
}
