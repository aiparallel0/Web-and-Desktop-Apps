/**
 * Receipt Extractor - Modern SPA Controller
 * Handles upload, extraction, and results display
 */

// =============================================================================
// CONFIGURATION
// =============================================================================

// Detect if backend is available at different ports (development mode)
const detectBackendUrl = () => {
    // In production, frontend and backend are on same origin
    // In development, frontend is on port 3000, backend on port 5000
    const currentPort = window.location.port;
    if (currentPort === '3000') {
        // Development mode - backend is on port 5000
        return `${window.location.protocol}//${window.location.hostname}:5000`;
    }
    // Production or same-origin deployment
    return window.location.origin;
};

const CONFIG = {
    API_BASE_URL: detectBackendUrl(),
    API_ENDPOINTS: {
        quickExtract: '/api/quick-extract',
        extract: '/api/extract',
        models: '/api/models'
    },
    MAX_FILE_SIZE: 100 * 1024 * 1024, // 100MB
    EXTRACTION_TIMEOUT: 60000, // 60 seconds
    UPGRADE_THRESHOLD: 3 // Show upgrade banner after 3 extractions
};

// =============================================================================
// STATE MANAGEMENT
// =============================================================================

const AppState = {
    extractionCount: 0,
    currentFile: null,
    currentResults: null,
    selectedModel: null,
    availableModels: [],

    incrementExtractionCount() {
        this.extractionCount++;
        localStorage.setItem('extraction_count', this.extractionCount);

        if (this.extractionCount >= CONFIG.UPGRADE_THRESHOLD) {
            showUpgradeBanner();
        }
    },

    loadExtractionCount() {
        const count = localStorage.getItem('extraction_count');
        this.extractionCount = count ? parseInt(count, 10) : 0;
    },

    reset() {
        this.currentFile = null;
        this.currentResults = null;
    }
};

// =============================================================================
// API SERVICE
// =============================================================================

class APIService {
    static async fetchModels() {
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}${CONFIG.API_ENDPOINTS.models}`);
            if (!response.ok) throw new Error('Failed to fetch models');
            const data = await response.json();
            return data.models || [];
        } catch (error) {
            console.error('Error fetching models:', error);
            return [];
        }
    }

    static async extractReceipt(file, modelId = null) {
        const formData = new FormData();
        formData.append('image', file);
        if (modelId) {
            formData.append('model_id', modelId);
        }

        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}${CONFIG.API_ENDPOINTS.extract}`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error extracting receipt:', error);
            throw error;
        }
    }

    static async quickExtract(file) {
        // Fallback to regular extract endpoint if quick-extract not available
        return this.extractReceipt(file);
    }
}

// =============================================================================
// UI CONTROLLER
// =============================================================================

class UIController {
    static showSection(sectionId) {
        // Hide all sections
        ['processingSection', 'resultsSection'].forEach(id => {
            const section = document.getElementById(id);
            if (section) section.classList.add('hidden');
        });

        // Show requested section
        const section = document.getElementById(sectionId);
        if (section) {
            section.classList.remove('hidden');
            section.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    static hideSection(sectionId) {
        const section = document.getElementById(sectionId);
        if (section) section.classList.add('hidden');
    }

    static showLoading() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) overlay.classList.remove('hidden');
    }

    static hideLoading() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) overlay.classList.add('hidden');
    }

    static showError(message) {
        alert(`Error: ${message}`);
        this.hideLoading();
    }

    static scrollToTop() {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

// =============================================================================
// EXTRACTION CONTROLLER
// =============================================================================

class ExtractionController {
    static async processFile(file) {
        if (!file) {
            UIController.showError('No file selected');
            return;
        }

        if (file.size > CONFIG.MAX_FILE_SIZE) {
            UIController.showError('File too large. Maximum size is 100MB');
            return;
        }

        try {
            // Show processing section with progress bar
            UIController.showSection('processingSection');
            const progressBar = document.getElementById('extractProgress');

            if (progressBar) {
                progressBar.setProgress(0, 'Uploading image...');

                // Simulate upload progress
                setTimeout(() => progressBar.setProgress(25, 'Analyzing image...'), 300);
                setTimeout(() => progressBar.setProgress(50, 'Detecting text regions...'), 800);
                setTimeout(() => progressBar.setProgress(75, 'Extracting data...'), 1500);
            }

            // Store file for later reference
            AppState.currentFile = file;

            // Call API
            const results = await APIService.quickExtract(file);

            if (progressBar) {
                progressBar.setProgress(100, 'Complete!');
            }

            // Wait a moment before showing results
            setTimeout(() => {
                this.showResults(results, file);
            }, 500);

        } catch (error) {
            console.error('Extraction error:', error);
            UIController.hideSection('processingSection');
            UIController.showError('Failed to extract receipt data. Please try again.');
        }
    }

    static showResults(results, file) {
        // Hide processing section
        UIController.hideSection('processingSection');

        // Show results section
        UIController.showSection('resultsSection');

        // Get results view component
        const resultsView = document.getElementById('extractResults');
        if (!resultsView) return;

        // Convert file to data URL for display
        const reader = new FileReader();
        reader.onload = (e) => {
            resultsView.setResults(results, e.target.result);
        };
        reader.readAsDataURL(file);

        // Store results
        AppState.currentResults = results;

        // Increment extraction count
        AppState.incrementExtractionCount();

        // Scroll to results
        UIController.scrollToTop();
    }

    static reset() {
        // Hide processing and results sections
        UIController.hideSection('processingSection');
        UIController.hideSection('resultsSection');

        // Reset upload zone
        const uploadZone = document.getElementById('mainUploadZone');
        if (uploadZone) {
            uploadZone.clearFile();
        }

        // Reset state
        AppState.reset();

        // Scroll to top
        UIController.scrollToTop();
    }
}

// =============================================================================
// UPGRADE BANNER
// =============================================================================

function showUpgradeBanner() {
    const banner = document.getElementById('upgradeBanner');
    if (banner && banner.classList.contains('hidden')) {
        banner.classList.remove('hidden');
    }
}

function hideUpgradeBanner() {
    const banner = document.getElementById('upgradeBanner');
    if (banner) {
        banner.classList.add('hidden');
    }
}

// =============================================================================
// EVENT HANDLERS
// =============================================================================

function setupEventHandlers() {
    // Upload zone file selection
    const uploadZone = document.getElementById('mainUploadZone');
    if (uploadZone) {
        uploadZone.onFileSelected = (file) => {
            ExtractionController.processFile(file);
        };
    }

    // Results view - process another
    const resultsView = document.getElementById('extractResults');
    if (resultsView) {
        resultsView.addEventListener('process-another', () => {
            ExtractionController.reset();
        });
    }

    // Upgrade banner
    const upgradeBtn = document.getElementById('upgradeBtn');
    if (upgradeBtn) {
        upgradeBtn.addEventListener('click', () => {
            window.location.href = '#pricing';
            hideUpgradeBanner();
        });
    }

    const closeUpgradeBtn = document.getElementById('closeUpgradeBtn');
    if (closeUpgradeBtn) {
        closeUpgradeBtn.addEventListener('click', () => {
            hideUpgradeBanner();
        });
    }

    // Sign in button
    const signInBtn = document.getElementById('signInBtn');
    if (signInBtn) {
        signInBtn.addEventListener('click', () => {
            // Show coming soon message - authentication feature not yet fully implemented
            alert('Sign In feature coming soon! For now, try our free extraction above - no account required.');
        });
    }

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });
}

// =============================================================================
// PERFORMANCE MONITORING
// =============================================================================

function setupPerformanceMonitoring() {
    // Measure page load time
    if (window.performance && window.performance.timing) {
        window.addEventListener('load', () => {
            setTimeout(() => {
                const perfData = window.performance.timing;
                const pageLoadTime = perfData.loadEventEnd - perfData.navigationStart;
                console.log(`Page load time: ${pageLoadTime}ms`);

                // Track if under 2s target
                if (pageLoadTime < 2000) {
                    console.log('✓ Page load performance target met (<2s)');
                } else {
                    console.warn(`⚠ Page load slower than target: ${pageLoadTime}ms`);
                }
            }, 0);
        });
    }

    // Track extraction performance
    const originalProcessFile = ExtractionController.processFile;
    ExtractionController.processFile = async function(file) {
        const startTime = performance.now();
        try {
            await originalProcessFile.call(this, file);
            const duration = performance.now() - startTime;
            console.log(`Extraction completed in ${Math.round(duration)}ms`);
        } catch (error) {
            const duration = performance.now() - startTime;
            console.error(`Extraction failed after ${Math.round(duration)}ms`, error);
            throw error;
        }
    };
}

// =============================================================================
// INITIALIZATION
// =============================================================================

async function init() {
    console.log('Initializing Receipt Extractor...');

    try {
        // Load extraction count from localStorage
        AppState.loadExtractionCount();

        // Setup event handlers
        setupEventHandlers();

        // Setup performance monitoring
        setupPerformanceMonitoring();

        // Load available models (optional, for future use)
        try {
            AppState.availableModels = await APIService.fetchModels();
            console.log(`Loaded ${AppState.availableModels.length} models`);
        } catch (error) {
            console.warn('Could not load models:', error);
        }

        console.log('✓ Receipt Extractor initialized successfully');
    } catch (error) {
        console.error('Initialization error:', error);
    }
}

// =============================================================================
// START APPLICATION
// =============================================================================

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

// Export for debugging
window.ReceiptExtractor = {
    AppState,
    APIService,
    UIController,
    ExtractionController,
    CONFIG
};
