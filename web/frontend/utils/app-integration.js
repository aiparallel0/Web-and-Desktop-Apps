/**
 * Complete Integration Example
 * Demonstrates how all components work together with real backend integration
 */

(function() {
    'use strict';

    /**
     * Application Configuration
     */
    const APP_CONFIG = {
        name: 'Receipt Extractor',
        version: '2.0.0',
        apiTimeout: 120000,
        maxFileSize: 100 * 1024 * 1024,
        defaultModel: 'ocr_tesseract',
        supportedFormats: ['image/jpeg', 'image/png', 'image/webp', 'image/gif', 'application/pdf'],
        
        features: {
            preprocessing: true,
            manualSelection: true,
            batchProcessing: false,
            cloudStorage: false
        },

        ui: {
            theme: 'light',
            language: 'en',
            animations: true
        }
    };

    /**
     * Application State Manager
     */
    class ApplicationState {
        constructor() {
            this.state = {
                initialized: false,
                apiConnected: false,
                currentFile: null,
                currentResults: null,
                selectedModel: APP_CONFIG.defaultModel,
                detectionSettings: {
                    mode: 'auto',
                    deskewEnabled: true,
                    enhanceEnabled: true,
                    previewEnabled: false
                },
                processing: false,
                models: [],
                history: [],
                statistics: {
                    totalExtractions: 0,
                    successfulExtractions: 0,
                    failedExtractions: 0,
                    totalProcessingTime: 0,
                    avgProcessingTime: 0
                }
            };

            this.listeners = new Map();
            this.loadState();
        }

        /**
         * Get state value
         */
        get(key) {
            return key.split('.').reduce((obj, k) => obj?.[k], this.state);
        }

        /**
         * Set state value
         */
        set(key, value) {
            const keys = key.split('.');
            const lastKey = keys.pop();
            const target = keys.reduce((obj, k) => {
                if (!obj[k]) obj[k] = {};
                return obj[k];
            }, this.state);
            
            const oldValue = target[lastKey];
            target[lastKey] = value;

            this.notifyListeners(key, value, oldValue);
            this.saveState();

            return value;
        }

        /**
         * Subscribe to state changes
         */
        subscribe(key, callback) {
            if (!this.listeners.has(key)) {
                this.listeners.set(key, []);
            }
            this.listeners.get(key).push(callback);

            return () => {
                const callbacks = this.listeners.get(key);
                const index = callbacks.indexOf(callback);
                if (index !== -1) {
                    callbacks.splice(index, 1);
                }
            };
        }

        /**
         * Notify listeners of changes
         */
        notifyListeners(key, newValue, oldValue) {
            if (this.listeners.has(key)) {
                this.listeners.get(key).forEach(callback => {
                    try {
                        callback(newValue, oldValue);
                    } catch (error) {
                        console.error('Error in state listener:', error);
                    }
                });
            }
        }

        /**
         * Load state from storage
         */
        loadState() {
            if (window.storage) {
                const saved = window.storage.get('app_state');
                if (saved) {
                    this.state = { ...this.state, ...saved };
                }
            }
        }

        /**
         * Save state to storage
         */
        saveState() {
            if (window.storage) {
                window.storage.set('app_state', {
                    selectedModel: this.state.selectedModel,
                    detectionSettings: this.state.detectionSettings,
                    statistics: this.state.statistics
                });
            }
        }

        /**
         * Update statistics
         */
        updateStatistics(success, processingTime) {
            const stats = this.state.statistics;
            
            stats.totalExtractions++;
            if (success) {
                stats.successfulExtractions++;
            } else {
                stats.failedExtractions++;
            }
            
            stats.totalProcessingTime += processingTime;
            stats.avgProcessingTime = stats.totalProcessingTime / stats.totalExtractions;
            
            this.set('statistics', { ...stats });
        }

        /**
         * Add to history
         */
        addToHistory(entry) {
            const history = [...this.state.history, entry];
            
            // Keep only last 50 entries
            if (history.length > 50) {
                history.shift();
            }
            
            this.set('history', history);
        }

        /**
         * Reset state
         */
        reset() {
            this.state = {
                ...this.state,
                currentFile: null,
                currentResults: null,
                processing: false
            };
            this.saveState();
        }

        /**
         * Export state
         */
        export() {
            return JSON.stringify(this.state, null, 2);
        }
    }

    /**
     * Main Application Controller
     */
    class ReceiptExtractorApp {
        constructor() {
            this.config = APP_CONFIG;
            this.state = new ApplicationState();
            this.api = window.apiClient;
            this.events = window.appEvents;
            this.validator = window.Validators;
            this.imageProcessor = null;

            this.components = {
                uploadZone: null,
                unifiedControls: null,
                detectionControls: null
            };

            this.initialized = false;
        }

        /**
         * Initialize application
         */
        async initialize() {
            console.log(`${this.config.name} v${this.config.version} - Initializing...`);

            try {
                // Check API connection
                await this.checkApiConnection();

                // Load models
                await this.loadModels();

                // Initialize components
                this.initializeComponents();

                // Setup event handlers
                this.setupEventHandlers();

                // Setup state subscriptions
                this.setupStateSubscriptions();

                // Mark as initialized
                this.state.set('initialized', true);
                this.initialized = true;

                console.log('Application initialized successfully');
                
                // Emit initialization complete event
                if (this.events) {
                    this.events.bus.emit('app-initialized', {
                        version: this.config.version,
                        timestamp: Date.now()
                    });
                }

            } catch (error) {
                console.error('Application initialization failed:', error);
                this.showError('Failed to initialize application: ' + error.message);
            }
        }

        /**
         * Check API connection
         */
        async checkApiConnection() {
            console.log('Checking API connection...');
            
            const health = await this.api.checkHealth();
            this.state.set('apiConnected', health.healthy);

            if (!health.healthy) {
                this.showWarning('Backend API is not responding. Some features may be unavailable.');
            } else {
                console.log('API connection established');
                if (this.events) {
                    this.events.emitApiConnected();
                }
            }
        }

        /**
         * Load available models
         */
        async loadModels() {
            console.log('Loading models...');
            
            try {
                const data = await this.api.fetchModels();
                
                if (data.models && data.models.length > 0) {
                    this.state.set('models', data.models);
                    
                    if (data.default_model) {
                        this.state.set('selectedModel', data.default_model);
                    }
                    
                    console.log(`Loaded ${data.models.length} models`);
                } else {
                    throw new Error('No models available');
                }
            } catch (error) {
                console.error('Failed to load models:', error);
                this.showWarning('Using default model configuration');
            }
        }

        /**
         * Initialize UI components
         */
        initializeComponents() {
            console.log('Initializing components...');

            // Get component references
            this.components.uploadZone = document.getElementById('uploadZone');
            this.components.unifiedControls = document.getElementById('unifiedControls');
            this.components.detectionControls = document.getElementById('detectionControls');

            // Initialize image processor
            if (window.ImagePreprocessor) {
                this.imageProcessor = new window.ImagePreprocessor();
            }

            console.log('Components initialized');
        }

        /**
         * Setup event handlers
         */
        setupEventHandlers() {
            console.log('Setting up event handlers...');

            // Upload zone events
            if (this.components.uploadZone) {
                this.components.uploadZone.addEventListener('file-selected', (e) => {
                    this.handleFileSelected(e.detail.file);
                });

                this.components.uploadZone.addEventListener('extract-request', (e) => {
                    this.processExtraction(e.detail.file);
                });
            }

            // Unified controls events
            if (this.components.unifiedControls) {
                this.components.unifiedControls.addEventListener('model-changed', (e) => {
                    this.handleModelChanged(e.detail.modelId);
                });

                this.components.unifiedControls.addEventListener('settings-changed', (e) => {
                    this.handleSettingsChanged(e.detail);
                });

                this.components.unifiedControls.addEventListener('process-request', () => {
                    this.processCurrentFile();
                });

                this.components.unifiedControls.addEventListener('extraction-complete', (e) => {
                    this.handleExtractionComplete(e.detail);
                });

                this.components.unifiedControls.addEventListener('extraction-error', (e) => {
                    this.handleExtractionError(e.detail);
                });
            }

            // Detection controls events
            if (this.components.detectionControls) {
                this.components.detectionControls.addEventListener('detection-settings-changed', (e) => {
                    this.handleDetectionSettingsChanged(e.detail);
                });
            }

            // Global events
            if (this.events) {
                this.events.onApiDisconnected((data) => {
                    this.showError('API connection lost: ' + data.reason);
                });
            }

            // Keyboard shortcuts
            document.addEventListener('keydown', (e) => {
                this.handleKeyboardShortcut(e);
            });

            console.log('Event handlers setup complete');
        }

        /**
         * Setup state subscriptions
         */
        setupStateSubscriptions() {
            // Subscribe to processing state changes
            this.state.subscribe('processing', (processing) => {
                this.updateProcessingUI(processing);
            });

            // Subscribe to results changes
            this.state.subscribe('currentResults', (results) => {
                if (results) {
                    this.displayResults(results);
                }
            });

            // Subscribe to API connection changes
            this.state.subscribe('apiConnected', (connected) => {
                this.updateConnectionUI(connected);
            });
        }

        /**
         * Handle file selected
         */
        handleFileSelected(file) {
            console.log('File selected:', file.name);

            // Validate file
            const validation = this.validator.validateImageFile(file, {
                maxSize: this.config.maxFileSize,
                allowedTypes: this.config.supportedFormats
            });

            if (!validation.valid) {
                this.showError(validation.errors.join('\n'));
                return;
            }

            // Show warnings
            if (validation.warnings && validation.warnings.length > 0) {
                validation.warnings.forEach(warning => {
                    this.showWarning(warning);
                });
            }

            // Update state
            this.state.set('currentFile', file);

            // Emit event
            if (this.events) {
                this.events.emitFileSelected(file);
            }

            // Update detection controls with image if manual mode
            if (this.components.detectionControls && 
                this.state.get('detectionSettings.mode') === 'manual') {
                this.components.detectionControls.setImage(file);
            }
        }

        /**
         * Handle model changed
         */
        handleModelChanged(modelId) {
            console.log('Model changed:', modelId);
            const previousModel = this.state.get('selectedModel');
            this.state.set('selectedModel', modelId);

            if (this.events) {
                this.events.emitModelChanged(modelId, previousModel);
            }
        }

        /**
         * Handle settings changed
         */
        handleSettingsChanged(settings) {
            console.log('Settings changed:', settings);
            this.state.set('detectionSettings', {
                ...this.state.get('detectionSettings'),
                ...settings
            });

            if (this.events) {
                this.events.emitSettingsChanged(settings);
            }
        }

        /**
         * Handle detection settings changed
         */
        handleDetectionSettingsChanged(settings) {
            this.handleSettingsChanged(settings);
        }

        /**
         * Process current file
         */
        async processCurrentFile() {
            const file = this.state.get('currentFile');
            
            if (!file) {
                this.showError('No file selected. Please select a file first.');
                return;
            }

            await this.processExtraction(file);
        }

        /**
         * Process extraction
         */
        async processExtraction(file) {
            if (!file) {
                this.showError('No file provided');
                return;
            }

            // Check API connection
            if (!this.state.get('apiConnected')) {
                this.showError('Cannot process: API is not connected');
                return;
            }

            this.state.set('processing', true);
            const startTime = performance.now();

            try {
                // Emit extraction started event
                if (this.events) {
                    this.events.emitExtractionStarted(file, this.state.get('detectionSettings'));
                }

                // Get extraction settings
                const settings = {
                    modelId: this.state.get('selectedModel'),
                    ...this.state.get('detectionSettings')
                };

                // Call API
                const result = await this.api.extractReceipt(file, settings);

                const endTime = performance.now();
                const duration = (endTime - startTime) / 1000;

                // Update state
                this.state.set('currentResults', result);
                this.state.updateStatistics(result.success, duration);

                // Add to history
                this.state.addToHistory({
                    filename: file.name,
                    model: settings.modelId,
                    mode: settings.detectionMode,
                    success: result.success,
                    textsFound: result.texts?.length || 0,
                    duration,
                    timestamp: Date.now()
                });

                // Emit extraction complete event
                if (this.events) {
                    this.events.emitExtractionComplete(result, duration);
                }

                // Show success message
                this.showSuccess(`Extraction completed in ${duration.toFixed(2)}s. Found ${result.texts?.length || 0} text regions.`);

            } catch (error) {
                console.error('Extraction failed:', error);
                
                const endTime = performance.now();
                const duration = (endTime - startTime) / 1000;
                
                this.state.updateStatistics(false, duration);
                
                // Emit extraction error event
                if (this.events) {
                    this.events.emitExtractionError(error.message);
                }
                
                this.showError('Extraction failed: ' + error.message);
            } finally {
                this.state.set('processing', false);
            }
        }

        /**
         * Handle extraction complete
         */
        handleExtractionComplete(data) {
            console.log('Extraction complete:', data);
            // Additional handling if needed
        }

        /**
         * Handle extraction error
         */
        handleExtractionError(data) {
            console.error('Extraction error:', data);
            // Additional handling if needed
        }

        /**
         * Display results
         */
        displayResults(results) {
            if (window.UIHandler) {
                window.UIHandler.displayResults(results);
            }
        }

        /**
         * Update processing UI
         */
        updateProcessingUI(processing) {
            // Update all process buttons
            document.querySelectorAll('[data-action="process"]').forEach(btn => {
                btn.disabled = processing;
                btn.textContent = processing ? 'Processing...' : 'Process Receipt';
            });

            // Show/hide loading indicator
            const loadingIndicator = document.getElementById('loadingIndicator');
            if (loadingIndicator) {
                loadingIndicator.classList.toggle('hidden', !processing);
            }
        }

        /**
         * Update connection UI
         */
        updateConnectionUI(connected) {
            const statusIndicator = document.getElementById('apiStatus');
            if (statusIndicator) {
                statusIndicator.classList.toggle('connected', connected);
                statusIndicator.classList.toggle('disconnected', !connected);
                statusIndicator.title = connected ? 'API Connected' : 'API Disconnected';
            }
        }

        /**
         * Handle keyboard shortcuts
         */
        handleKeyboardShortcut(e) {
            // Ctrl/Cmd + Enter: Process
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                e.preventDefault();
                this.processCurrentFile();
            }

            // Ctrl/Cmd + O: Open file
            if ((e.ctrlKey || e.metaKey) && e.key === 'o') {
                e.preventDefault();
                const fileInput = document.getElementById('fileInput');
                if (fileInput) fileInput.click();
            }

            // Ctrl/Cmd + S: Save results
            if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                e.preventDefault();
                if (this.state.get('currentResults')) {
                    if (window.UIHandler) {
                        window.UIHandler.downloadResults();
                    }
                }
            }
        }

        /**
         * Show error message
         */
        showError(message, title = 'Error') {
            if (window.UIHandler) {
                window.UIHandler.showError(message, title);
            } else {
                console.error(title + ':', message);
                alert(title + ': ' + message);
            }

            if (this.events) {
                this.events.emitShowError(message, title);
            }
        }

        /**
         * Show warning message
         */
        showWarning(message, title = 'Warning') {
            if (window.UIHandler) {
                window.UIHandler.showError(message, title);
            } else {
                console.warn(title + ':', message);
            }
        }

        /**
         * Show success message
         */
        showSuccess(message) {
            if (window.UIHandler) {
                window.UIHandler.showSuccess(message);
            } else {
                console.log('Success:', message);
            }

            if (this.events) {
                this.events.emitShowSuccess(message);
            }
        }

        /**
         * Get application statistics
         */
        getStatistics() {
            return this.state.get('statistics');
        }

        /**
         * Get application history
         */
        getHistory() {
            return this.state.get('history');
        }

        /**
         * Export application data
         */
        exportData() {
            return {
                config: this.config,
                state: this.state.state,
                timestamp: Date.now()
            };
        }

        /**
         * Reset application
         */
        reset() {
            this.state.reset();
            
            // Reset components
            if (this.components.uploadZone && this.components.uploadZone.clearFile) {
                this.components.uploadZone.clearFile();
            }

            console.log('Application reset');
        }
    }

    /**
     * Initialize application when DOM is ready
     */
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            window.app = new ReceiptExtractorApp();
            window.app.initialize();
        });
    } else {
        window.app = new ReceiptExtractorApp();
        window.app.initialize();
    }

    // Export for external use
    window.ReceiptExtractorApp = ReceiptExtractorApp;
    window.ApplicationState = ApplicationState;
    window.APP_CONFIG = APP_CONFIG;

})();
