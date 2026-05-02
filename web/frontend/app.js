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
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000);
            
            const response = await fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.health}`, {
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            if (response.ok) {
                const data = await response.json();
                return {
                    healthy: data.status === 'healthy' || data.status === 'ok',
                    data
                };
            }
            return { healthy: false };
        } catch (error) {
            console.error('Health check failed:', error);
            return { healthy: false };
        }
    }

    static async fetchModels() {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 10000);
            
            const response = await fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.models}`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json'
                },
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.models && Array.isArray(data.models)) {
                return {
                    models: data.models,
                    defaultModel: data.default_model || 'ocr_tesseract'
                };
            }
            
            throw new Error('Invalid response format');
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

        // Preprocess image if needed
        let processedFile = file;
        
        if ((settings.deskewEnabled || settings.enhanceEnabled) && window.ImageProcessingUtils) {
            try {
                console.log('Preprocessing image before upload...');
                processedFile = await window.ImageProcessingUtils.processFile(file, {
                    deskew: settings.deskewEnabled,
                    enhance: settings.enhanceEnabled,
                    enhanceOptions: {
                        brightness: 1.1,
                        contrast: 1.2,
                        sharpen: true
                    }
                });
                console.log('Preprocessing complete');
            } catch (preprocessError) {
                console.warn('Image preprocessing failed, using original:', preprocessError);
                processedFile = file;
            }
        }

        const formData = new FormData();
        formData.append('image', processedFile);
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

            console.log('Sending extraction request:', {
                model: settings.modelId,
                mode: settings.detectionMode,
                fileSize: processedFile.size,
                originalSize: file.size
            });

            const startTime = performance.now();

            const response = await fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.extract}`, {
                method: 'POST',
                body: formData,
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            const endTime = performance.now();
            const requestTime = (endTime - startTime) / 1000;

            if (!response.ok) {
                let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.error || errorData.message || errorMessage;
                    console.error('Backend error:', errorData);
                } catch (e) {
                    console.error('Failed to parse error response');
                }
                throw new Error(errorMessage);
            }

            const result = await response.json();
            
            console.log('Extraction completed:', {
                requestTime: requestTime.toFixed(2) + 's',
                processingTime: result.processing_time?.toFixed(2) + 's',
                textsFound: result.texts?.length || 0,
                success: result.success
            });

            // Add client-side timing
            result.client_request_time = requestTime;

            return result;

        } catch (error) {
            if (error.name === 'AbortError') {
                throw new Error('Request timeout - processing took too long. Try a smaller image or different model.');
            }
            throw error;
        }
    }

    static async testConnection() {
        const results = {
            health: false,
            models: false,
            message: ''
        };

        try {
            const health = await this.checkHealth();
            results.health = health.healthy;

            if (results.health) {
                try {
                    const models = await this.fetchModels();
                    results.models = models.models.length > 0;
                    results.message = 'Backend connection successful';
                } catch (e) {
                    results.message = 'Backend healthy but models endpoint failed';
                }
            } else {
                results.message = 'Backend health check failed';
            }
        } catch (error) {
            results.message = error.message;
        }

        return results;
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

        if (!results || !results.success) {
            this.showError(results?.error || results?.error_message || 'Extraction failed');
            resultsContainer.innerHTML = `
                <div class="results-card error">
                    <div class="results-header">
                        <h3>Extraction Failed</h3>
                    </div>
                    <div class="results-content">
                        <p class="error-message">${this.escapeHtml(results?.error || 'Unknown error occurred')}</p>
                    </div>
                </div>
            `;
            resultsContainer.classList.remove('hidden');
            return;
        }

        const texts = results.texts || results.data?.texts || [];
        const metadata = results.metadata || {};
        const processingTime = results.processing_time || results.client_request_time || 0;

        // Calculate statistics
        const totalChars = texts.reduce((sum, item) => sum + (item.text?.length || 0), 0);
        const avgConfidence = texts.length > 0
            ? texts.reduce((sum, item) => sum + (item.confidence || 0), 0) / texts.length
            : 0;

        let html = `
            <div class="results-card">
                <div class="results-header">
                    <h3>Extraction Results</h3>
                    <div class="results-badges">
                        <span class="badge badge-success">${texts.length} regions</span>
                        <span class="badge badge-info">${totalChars} characters</span>
                        ${avgConfidence > 0 ? `<span class="badge badge-primary">${(avgConfidence * 100).toFixed(1)}% avg confidence</span>` : ''}
                    </div>
                </div>
                
                <div class="results-metadata">
                    <div class="metadata-grid">
                        <div class="metadata-item">
                            <span class="metadata-label">Model:</span>
                            <span class="metadata-value">${this.escapeHtml(results.model_id || 'Unknown')}</span>
                        </div>
                        <div class="metadata-item">
                            <span class="metadata-label">Processing Time:</span>
                            <span class="metadata-value">${processingTime.toFixed(2)}s</span>
                        </div>
                        ${metadata.detection_mode ? `
                            <div class="metadata-item">
                                <span class="metadata-label">Detection Mode:</span>
                                <span class="metadata-value">${this.escapeHtml(metadata.detection_mode)}</span>
                            </div>
                        ` : ''}
                        ${metadata.image_size ? `
                            <div class="metadata-item">
                                <span class="metadata-label">Image Size:</span>
                                <span class="metadata-value">${metadata.image_size}</span>
                            </div>
                        ` : ''}
                        ${metadata.deskew_angle !== undefined ? `
                            <div class="metadata-item">
                                <span class="metadata-label">Deskew Angle:</span>
                                <span class="metadata-value">${metadata.deskew_angle.toFixed(2)}°</span>
                            </div>
                        ` : ''}
                    </div>
                </div>
                
                <div class="results-content">
                    ${texts.length > 0 ? `
                        <div class="extracted-text">
                            ${texts.map((item, idx) => {
                                const confidenceClass = item.confidence 
                                    ? item.confidence > 0.8 ? 'high' 
                                    : item.confidence > 0.5 ? 'medium' 
                                    : 'low'
                                    : '';
                                
                                return `
                                    <div class="text-item ${confidenceClass}">
                                        <div class="text-index">#${idx + 1}</div>
                                        <div class="text-content">
                                            <div class="text-value">${this.escapeHtml(item.text || '')}</div>
                                            ${item.confidence ? `
                                                <div class="text-confidence confidence-${confidenceClass}">
                                                    <div class="confidence-bar">
                                                        <div class="confidence-fill" style="width: ${item.confidence * 100}%"></div>
                                                    </div>
                                                    <span>${(item.confidence * 100).toFixed(1)}%</span>
                                                </div>
                                            ` : ''}
                                            ${item.bbox ? `
                                                <div class="text-bbox">
                                                    Position: (${item.bbox.x}, ${item.bbox.y}) 
                                                    Size: ${item.bbox.width}×${item.bbox.height}
                                                </div>
                                            ` : ''}
                                        </div>
                                    </div>
                                `;
                            }).join('')}
                        </div>
                    ` : '<p class="no-results">No text detected. Try a different model or adjust preprocessing settings.</p>'}
                </div>
                
                <div class="results-actions">
                    <button class="btn btn-primary" onclick="UIHandler.copyResults()" title="Copy all extracted text to clipboard">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                            <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"></path>
                        </svg>
                        Copy All Text
                    </button>
                    <button class="btn btn-secondary" onclick="UIHandler.downloadResults()" title="Download results as JSON">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"></path>
                            <polyline points="7 10 12 15 17 10"></polyline>
                            <line x1="12" y1="15" x2="12" y2="3"></line>
                        </svg>
                        Download JSON
                    </button>
                    <button class="btn btn-secondary" onclick="UIHandler.downloadText()" title="Download as plain text">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"></path>
                            <polyline points="14 2 14 8 20 8"></polyline>
                            <line x1="16" y1="13" x2="8" y2="13"></line>
                            <line x1="16" y1="17" x2="8" y2="17"></line>
                            <polyline points="10 9 9 9 8 9"></polyline>
                        </svg>
                        Download Text
                    </button>
                </div>
            </div>
        `;

        resultsContainer.innerHTML = html;
        resultsContainer.classList.remove('hidden');
        
        // Scroll to results
        resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    static escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    static copyResults() {
        const results = AppState.currentResults;
        if (!results) {
            this.showError('No results to copy');
            return;
        }

        const texts = results.texts || results.data?.texts || [];
        const allText = texts.map((item, idx) => `${idx + 1}. ${item.text}`).join('\n');

        if (!allText) {
            this.showError('No text to copy');
            return;
        }

        navigator.clipboard.writeText(allText).then(() => {
            this.showSuccess(`Copied ${texts.length} text regions to clipboard!`);
        }).catch(err => {
            console.error('Copy failed:', err);
            
            // Fallback: create textarea and copy
            const textarea = document.createElement('textarea');
            textarea.value = allText;
            textarea.style.position = 'fixed';
            textarea.style.opacity = '0';
            document.body.appendChild(textarea);
            textarea.select();
            
            try {
                document.execCommand('copy');
                this.showSuccess('Text copied to clipboard!');
            } catch (e) {
                this.showError('Failed to copy text');
            }
            
            document.body.removeChild(textarea);
        });
    }

    static downloadResults() {
        const results = AppState.currentResults;
        if (!results) {
            this.showError('No results to download');
            return;
        }

        const dataStr = JSON.stringify(results, null, 2);
        const blob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
        const filename = `receipt-extraction-${timestamp}.json`;
        
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        this.showSuccess(`Downloaded ${filename}`);
    }

    static downloadText() {
        const results = AppState.currentResults;
        if (!results) {
            this.showError('No results to download');
            return;
        }

        const texts = results.texts || results.data?.texts || [];
        const textContent = texts.map((item, idx) => `${idx + 1}. ${item.text}`).join('\n');
        
        if (!textContent) {
            this.showError('No text to download');
            return;
        }

        const blob = new Blob([textContent], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
        const filename = `receipt-text-${timestamp}.txt`;
        
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        this.showSuccess(`Downloaded ${filename}`);
    }
}

// =============================================================================
// FILE HANDLING
// =============================================================================

class FileHandler {
    static handleFileSelect(event) {
        const file = event.target.files?.[0] || event.dataTransfer?.files?.[0];
        if (!file) return;

        if (!FileHandler.validateFile(file)) {
            return;
        }

        AppState.setFile(file);
        FileHandler.displayFilePreview(file);
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

    // Show loading state
    const loadingIndicator = document.getElementById('loadingIndicator');
    if (loadingIndicator) {
        loadingIndicator.classList.remove('hidden');
    }

    // Check backend health
    const health = await APIService.checkHealth();
    console.log('Backend health check:', health.healthy ? 'OK' : 'FAILED');
    
    if (!health.healthy) {
        UIHandler.showError(
            'Backend server is not responding. Please ensure the backend is running.',
            'Connection Error'
        );
    } else {
        console.log('Backend version:', health.data?.version || 'unknown');
    }

    // Load models
    try {
        const modelsData = await APIService.fetchModels();
        console.log('Available models:', modelsData.models.length);
        AppState.selectedModel = modelsData.defaultModel;
    } catch (error) {
        console.error('Failed to load models:', error);
        UIHandler.showError('Failed to load available models. Using defaults.', 'Warning');
    }

    // Hide loading state
    if (loadingIndicator) {
        loadingIndicator.classList.add('hidden');
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
        dropZone.addEventListener('click', () => {
            if (fileInput) fileInput.click();
        });
    }

    // Listen to unified controls events
    const unifiedControls = document.getElementById('unifiedControls');
    if (unifiedControls) {
        unifiedControls.addEventListener('process-request', async (e) => {
            console.log('Process request received from controls');
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
        
        unifiedControls.addEventListener('api-warning', (e) => {
            UIHandler.showError(e.detail.message, 'API Connection Warning');
        });

        unifiedControls.addEventListener('extraction-complete', (e) => {
            console.log('Extraction completed:', e.detail);
        });

        unifiedControls.addEventListener('extraction-error', (e) => {
            console.error('Extraction error:', e.detail);
        });
    }

    // Listen to upload zone events
    const uploadZone = document.getElementById('uploadZone');
    if (uploadZone) {
        uploadZone.addEventListener('file-selected', (e) => {
            console.log('File selected:', e.detail.file.name);
            AppState.setFile(e.detail.file);
            
            // Update unified controls with the file
            if (unifiedControls && unifiedControls.setFile) {
                unifiedControls.setFile(e.detail.file);
            }
        });

        uploadZone.addEventListener('extract-request', async (e) => {
            console.log('Extract request from upload zone');
            AppState.setFile(e.detail.file);
            await handleExtraction();
        });

        uploadZone.addEventListener('upload-error', (e) => {
            UIHandler.showError(e.detail.message);
        });
    }

    // Listen to detection controls events
    const detectionControls = document.getElementById('detectionControls');
    if (detectionControls) {
        detectionControls.addEventListener('detection-settings-changed', (e) => {
            console.log('Detection settings changed:', e.detail);
            AppState.detectionSettings = {
                ...AppState.detectionSettings,
                ...e.detail
            };
        });
    }

    // Global process button
    const processBtn = document.getElementById('processBtn');
    if (processBtn) {
        processBtn.addEventListener('click', handleExtraction);
    }

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + Enter to process
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            handleExtraction();
        }
        
        // Ctrl/Cmd + O to open file
        if ((e.ctrlKey || e.metaKey) && e.key === 'o') {
            e.preventDefault();
            if (fileInput) fileInput.click();
        }
    });

    console.log('Application ready');
});

// Periodic health check
setInterval(async () => {
    const health = await APIService.checkHealth();
    if (!health.healthy) {
        console.warn('Backend health check failed');
    }
}, 60000); // Check every minute

// Export for use in other scripts
window.AppState = AppState;
window.APIService = APIService;
window.UIHandler = UIHandler;
window.FileHandler = FileHandler;
window.handleExtraction = handleExtraction;
