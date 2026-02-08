/**
 * Receipt Extractor - Main Application Controller
 * FUNCTIONAL implementation with real backend API integration
 * Government-style professional interface
 */

// =============================================================================
// CONFIGURATION
// =============================================================================

const API_CONFIG = {
    baseUrl: detectBackendUrl(),
    endpoints: {
        extract: '/api/extract',
        models: '/api/models',
        health: '/api/health'
    },
    maxFileSize: 100 * 1024 * 1024, // 100MB
    timeout: 60000
};

function detectBackendUrl() {
    if (window.RECEIPT_EXTRACTOR_API_URL) {
        return window.RECEIPT_EXTRACTOR_API_URL;
    }
    if (window.location.port === '3000') {
        return `${window.location.protocol}//${window.location.hostname}:5000`;
    }
    return window.location.origin;
}

// =============================================================================
// STATE MANAGEMENT
// =============================================================================

const AppState = {
    currentFile: null,
    currentResults: null,
    selectedModel: 'ocr_tesseract',
    detectionSettings: {
        mode: 'auto',
        deskewEnabled: true,
        enhanceEnabled: true
    },
    isProcessing: false,
    
    setFile(file) {
        this.currentFile = file;
    },
    
    setResults(results) {
        this.currentResults = results;
    },
    
    setProcessing(processing) {
        this.isProcessing = processing;
        this.updateUI();
    },
    
    updateUI() {
        // Update processing state in UI
        const processBtn = document.getElementById('processBtn');
        if (processBtn) {
            processBtn.disabled = this.isProcessing;
            processBtn.textContent = this.isProcessing ? 'Processing...' : 'Process Receipt';
        }
    }
};

// =============================================================================
// API SERVICE
// =============================================================================

class APIService {
    static async checkHealth() {
        try {
            const response = await fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.health}`);
            return response.ok;
        } catch (error) {
            console.error('Health check failed:', error);
            return false;
        }
    }

    static async fetchModels() {
        try {
            const response = await fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.models}`);
            if (!response.ok) {
                throw new Error('Failed to fetch models');
            }
            const data = await response.json();
            return data.models || [];
        } catch (error) {
            console.error('Error fetching models:', error);
            throw error;
        }
    }

    static async extractReceipt(file, settings) {
        if (!file) {
            throw new Error('No file provided');
        }

        if (file.size > API_CONFIG.maxFileSize) {
            throw new Error(`File size exceeds ${API_CONFIG.maxFileSize / 1024 / 1024}MB limit`);
        }

        const formData = new FormData();
        formData.append('image', file);
        formData.append('model_id', settings.modelId || 'ocr_tesseract');
        formData.append('detection_mode', settings.detectionMode || 'auto');
        formData.append('enable_deskew', String(settings.deskewEnabled !== false));
        formData.append('enable_enhancement', String(settings.enhanceEnabled !== false));
        formData.append('column_mode', String(settings.detectionMode === 'column'));

        if (settings.manualRegions && settings.manualRegions.length > 0) {
            formData.append('manual_regions', JSON.stringify(settings.manualRegions));
        }

        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.timeout);

            const response = await fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.extract}`, {
                method: 'POST',
                body: formData,
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            return result;

        } catch (error) {
            if (error.name === 'AbortError') {
                throw new Error('Request timeout - please try again');
            }
            throw error;
        }
    }
}

// =============================================================================
// UI HANDLERS
// =============================================================================

class UIHandler {
    static showError(message, title = 'Error') {
        const errorContainer = document.getElementById('errorContainer') || this.createErrorContainer();
        errorContainer.innerHTML = `
            <div class="alert alert-error" role="alert">
                <strong>${title}:</strong> ${message}
            </div>
        `;
        errorContainer.classList.remove('hidden');
        
        // Auto-hide after 10 seconds
        setTimeout(() => {
            errorContainer.classList.add('hidden');
        }, 10000);
    }

    static showSuccess(message) {
        const successContainer = document.getElementById('successContainer') || this.createSuccessContainer();
        successContainer.innerHTML = `
            <div class="alert alert-success" role="alert">
                ${message}
            </div>
        `;
        successContainer.classList.remove('hidden');
        
        setTimeout(() => {
            successContainer.classList.add('hidden');
        }, 5000);
    }

    static createErrorContainer() {
        const container = document.createElement('div');
        container.id = 'errorContainer';
        container.className = 'hidden';
        container.style.position = 'fixed';
        container.style.top = '80px';
        container.style.left = '50%';
        container.style.transform = 'translateX(-50%)';
        container.style.zIndex = '9999';
        container.style.maxWidth = '600px';
        container.style.width = '90%';
        document.body.appendChild(container);
        return container;
    }

    static createSuccessContainer() {
        const container = document.createElement('div');
        container.id = 'successContainer';
        container.className = 'hidden';
        container.style.position = 'fixed';
        container.style.top = '80px';
        container.style.right = '20px';
        container.style.zIndex = '9999';
        container.style.maxWidth = '400px';
        document.body.appendChild(container);
        return container;
    }

    static displayResults(results) {
        const resultsContainer = document.getElementById('resultsContainer');
        if (!resultsContainer) {
            console.error('Results container not found');
            return;
        }

        if (!results.success) {
            this.showError(results.error || 'Extraction failed');
            return;
        }

        const texts = results.texts || results.data?.texts || [];
        const metadata = results.metadata || {};

        let html = `
            <div class="results-card">
                <div class="results-header">
                    <h3>Extraction Results</h3>
                    <span class="results-count">${texts.length} text regions found</span>
                </div>
                <div class="results-metadata">
                    <div class="metadata-item">
                        <span class="metadata-label">Model:</span>
                        <span class="metadata-value">${results.model_id || 'Unknown'}</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">Processing Time:</span>
                        <span class="metadata-value">${(results.processing_time || 0).toFixed(2)}s</span>
                    </div>
                    ${metadata.detection_mode ? `
                        <div class="metadata-item">
                            <span class="metadata-label">Detection Mode:</span>
                            <span class="metadata-value">${metadata.detection_mode}</span>
                        </div>
                    ` : ''}
                </div>
                <div class="results-content">
                    ${texts.length > 0 ? `
                        <div class="extracted-text">
                            ${texts.map((item, idx) => `
                                <div class="text-item">
                                    <div class="text-index">${idx + 1}</div>
                                    <div class="text-content">
                                        <div class="text-value">${this.escapeHtml(item.text || '')}</div>
                                        ${item.confidence ? `
                                            <div class="text-confidence">
                                                Confidence: ${(item.confidence * 100).toFixed(1)}%
                                            </div>
                                        ` : ''}
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    ` : '<p class="no-results">No text detected</p>'}
                </div>
                <div class="results-actions">
                    <button class="btn btn-primary" onclick="UIHandler.copyResults()">Copy All Text</button>
                    <button class="btn btn-secondary" onclick="UIHandler.downloadResults()">Download JSON</button>
                </div>
            </div>
        `;

        resultsContainer.innerHTML = html;
        resultsContainer.classList.remove('hidden');
    }

    static escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    static copyResults() {
        const results = AppState.currentResults;
        if (!results) return;

        const texts = results.texts || results.data?.texts || [];
        const allText = texts.map(item => item.text).join('\n');

        navigator.clipboard.writeText(allText).then(() => {
            this.showSuccess('Text copied to clipboard!');
        }).catch(err => {
            this.showError('Failed to copy text');
            console.error('Copy failed:', err);
        });
    }

    static downloadResults() {
        const results = AppState.currentResults;
        if (!results) return;

        const dataStr = JSON.stringify(results, null, 2);
        const blob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `receipt-extraction-${Date.now()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
}

// =============================================================================
// FILE HANDLING
// =============================================================================

class FileHandler {
    static handleFileSelect(event) {
        const file = event.target.files?.[0] || event.dataTransfer?.files?.[0];
        if (!file) return;

        if (!this.validateFile(file)) {
            return;
        }

        AppState.setFile(file);
        this.displayFilePreview(file);
    }

    static validateFile(file) {
        // Check file type
        const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'application/pdf'];
        if (!validTypes.includes(file.type)) {
            UIHandler.showError('Invalid file type. Please upload an image (JPG, PNG, WEBP) or PDF.');
            return false;
        }

        // Check file size
        if (file.size > API_CONFIG.maxFileSize) {
            UIHandler.showError(`File size exceeds ${API_CONFIG.maxFileSize / 1024 / 1024}MB limit.`);
            return false;
        }

        return true;
    }

    static displayFilePreview(file) {
        const previewContainer = document.getElementById('filePreview');
        if (!previewContainer) return;

        const reader = new FileReader();
        reader.onload = (e) => {
            previewContainer.innerHTML = `
                <div class="file-preview-card">
                    <img src="${e.target.result}" alt="Preview" style="max-width: 100%; height: auto;" />
                    <div class="file-info">
                        <strong>${file.name}</strong>
                        <span>${(file.size / 1024).toFixed(2)} KB</span>
                    </div>
                </div>
            `;
            previewContainer.classList.remove('hidden');
        };
        reader.readAsDataURL(file);
    }
}

// =============================================================================
// MAIN EXTRACTION HANDLER
// =============================================================================

async function handleExtraction() {
    const file = AppState.currentFile;
    if (!file) {
        UIHandler.showError('Please select a file first');
        return;
    }

    // Get settings from unified controls
    const unifiedControls = document.getElementById('unifiedControls');
    const settings = unifiedControls?.getSettings() || {
        modelId: AppState.selectedModel,
        detectionMode: AppState.detectionSettings.mode,
        deskewEnabled: AppState.detectionSettings.deskewEnabled,
        enhanceEnabled: AppState.detectionSettings.enhanceEnabled
    };

    AppState.setProcessing(true);

    try {
        const results = await APIService.extractReceipt(file, settings);
        AppState.setResults(results);
        UIHandler.displayResults(results);
        UIHandler.showSuccess('Extraction completed successfully!');
    } catch (error) {
        console.error('Extraction error:', error);
        UIHandler.showError(error.message || 'Extraction failed. Please try again.');
    } finally {
        AppState.setProcessing(false);
    }
}

// =============================================================================
// INITIALIZATION
// =============================================================================

document.addEventListener('DOMContentLoaded', async () => {
    console.log('Receipt Extractor initialized');
    console.log('API Base URL:', API_CONFIG.baseUrl);

    // Check backend health
    const isHealthy = await APIService.checkHealth();
    if (!isHealthy) {
        console.warn('Backend health check failed');
    }

    // Set up file input handlers
    const fileInput = document.getElementById('fileInput');
    if (fileInput) {
        fileInput.addEventListener('change', FileHandler.handleFileSelect);
    }

    // Set up drag and drop
    const dropZone = document.getElementById('dropZone');
    if (dropZone) {
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('drag-over');
        });
        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('drag-over');
        });
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('drag-over');
            FileHandler.handleFileSelect(e);
        });
    }

    // Listen to unified controls events
    const unifiedControls = document.getElementById('unifiedControls');
    if (unifiedControls) {
        unifiedControls.addEventListener('process-request', async (e) => {
            await handleExtraction();
        });
        
        unifiedControls.addEventListener('model-changed', (e) => {
            AppState.selectedModel = e.detail.modelId;
            console.log('Model changed:', e.detail.modelId);
        });
        
        unifiedControls.addEventListener('settings-changed', (e) => {
            AppState.detectionSettings = e.detail;
            console.log('Settings changed:', e.detail);
        });
    }

    // Global process button
    const processBtn = document.getElementById('processBtn');
    if (processBtn) {
        processBtn.addEventListener('click', handleExtraction);
    }
});

// Export for use in other scripts
window.AppState = AppState;
window.APIService = APIService;
window.UIHandler = UIHandler;
window.FileHandler = FileHandler;
window.handleExtraction = handleExtraction;
