/**
 * Unified Extractor Controls - FUNCTIONAL Web Component
 * Connects to REAL backend APIs for model selection and extraction
 * Government-style professional interface
 */

class UnifiedExtractorControls extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        
        // API Configuration
        this.apiBaseUrl = this.getApiBaseUrl();
        this.apiConnected = false;
        
        // State
        this.selectedModelId = 'ocr_tesseract';
        this.availableModels = [];
        this.detectionMode = 'auto';
        this.deskewEnabled = true;
        this.enhanceEnabled = true;
        this.previewEnabled = false;
        this.manualRegions = [];
        this.isProcessing = false;
        
        // Storage keys
        this.MODEL_KEY = 'extractor_model_id';
        this.DETECTION_KEY = 'extractor_detection_settings';
    }

    getApiBaseUrl() {
        if (window.RECEIPT_EXTRACTOR_API_URL) {
            return window.RECEIPT_EXTRACTOR_API_URL;
        }
        if (window.location.port === '3000') {
            return `${window.location.protocol}//${window.location.hostname}:5000`;
        }
        return window.location.origin;
    }

    connectedCallback() {
        this.loadPreferences();
        this.fetchModels();
    }

    async fetchModels() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/models`);
            if (response.ok) {
                const data = await response.json();
                this.availableModels = data.models || this.getDefaultModels();
                this.apiConnected = true;
            } else {
                console.warn('API models endpoint returned error status, using fallback models');
                this.availableModels = this.getDefaultModels();
                this.apiConnected = false;
                this.showApiWarning('Unable to connect to API. Using default models.');
            }
        } catch (error) {
            console.error('Failed to fetch models:', error);
            this.availableModels = this.getDefaultModels();
            this.apiConnected = false;
            this.showApiWarning('API unavailable. Using offline model list.');
        }
        
        this.render();
        this.attachEventListeners();
    }

    showApiWarning(message) {
        // Dispatch event to notify parent of API connectivity issue
        this.dispatchEvent(new CustomEvent('api-warning', {
            detail: { message },
            bubbles: true,
            composed: true
        }));
    }

    getDefaultModels() {
        return [
            { id: 'ocr_tesseract', name: 'Tesseract OCR', description: 'Fast standard OCR', accuracy: '95%' },
            { id: 'ocr_easyocr', name: 'EasyOCR', description: '80+ languages', accuracy: '90%' },
            { id: 'ocr_paddle', name: 'PaddleOCR', description: 'High accuracy', accuracy: '93%' },
            { id: 'donut_cord', name: 'Donut', description: 'AI-powered extraction', accuracy: '92%' },
            { id: 'florence2', name: 'Florence-2', description: 'Vision-language model', accuracy: '94%' },
            { id: 'craft_detector', name: 'CRAFT', description: 'Text detection', accuracy: '91%' },
            { id: 'spatial', name: 'Spatial Multi-Method', description: 'Ensemble method', accuracy: '96%' }
        ];
    }

    loadPreferences() {
        const savedModel = localStorage.getItem(this.MODEL_KEY);
        if (savedModel) {
            this.selectedModelId = savedModel;
        }
        
        const savedSettings = localStorage.getItem(this.DETECTION_KEY);
        if (savedSettings) {
            try {
                const settings = JSON.parse(savedSettings);
                this.detectionMode = settings.detectionMode || 'auto';
                this.deskewEnabled = settings.deskewEnabled !== false;
                this.enhanceEnabled = settings.enhanceEnabled !== false;
            } catch (e) {
                console.error('Failed to parse settings:', e);
            }
        }
    }

    savePreferences() {
        localStorage.setItem(this.MODEL_KEY, this.selectedModelId);
        localStorage.setItem(this.DETECTION_KEY, JSON.stringify({
            detectionMode: this.detectionMode,
            deskewEnabled: this.deskewEnabled,
            enhanceEnabled: this.enhanceEnabled
        }));
    }

    render() {
        this.shadowRoot.innerHTML = `
            <style>${this.getStyles()}</style>
            <div class="unified-controls">
                <div class="control-section">
                    <h3 class="section-title">Extraction Method</h3>
                    <div class="model-grid">
                        ${this.availableModels.map(model => `
                            <button 
                                class="model-card ${model.id === this.selectedModelId ? 'selected' : ''}"
                                data-model-id="${model.id}"
                                type="button">
                                <div class="model-header">
                                    <div class="model-name">${model.name}</div>
                                    <div class="model-accuracy">${model.accuracy || 'N/A'}</div>
                                </div>
                                <div class="model-description">${model.description}</div>
                                ${model.id === this.selectedModelId ? '<div class="selected-badge">SELECTED</div>' : ''}
                            </button>
                        `).join('')}
                    </div>
                </div>

                <div class="control-section">
                    <h3 class="section-title">Detection Settings</h3>
                    <div class="settings-grid">
                        <div class="setting-group">
                            <label class="setting-label">Detection Mode</label>
                            <div class="mode-buttons">
                                ${['auto', 'manual', 'line', 'column'].map(mode => `
                                    <button 
                                        class="mode-btn ${this.detectionMode === mode ? 'active' : ''}"
                                        data-mode="${mode}"
                                        type="button">
                                        ${this.getModeLabel(mode)}
                                    </button>
                                `).join('')}
                            </div>
                        </div>

                        <div class="setting-group">
                            <label class="checkbox-label">
                                <input 
                                    type="checkbox" 
                                    id="deskew" 
                                    ${this.deskewEnabled ? 'checked' : ''}>
                                <span>Enable Deskew (Auto-rotation)</span>
                            </label>
                        </div>

                        <div class="setting-group">
                            <label class="checkbox-label">
                                <input 
                                    type="checkbox" 
                                    id="enhance" 
                                    ${this.enhanceEnabled ? 'checked' : ''}>
                                <span>Enable Image Enhancement</span>
                            </label>
                        </div>
                    </div>
                </div>

                <div class="control-section">
                    <button 
                        class="btn-process ${this.isProcessing ? 'processing' : ''}" 
                        id="processBtn"
                        type="button"
                        ${this.isProcessing ? 'disabled' : ''}>
                        ${this.isProcessing ? 'Processing...' : 'Process Receipt'}
                    </button>
                </div>
            </div>
        `;
    }

    getModeLabel(mode) {
        const labels = {
            auto: 'Auto Detect',
            manual: 'Manual Select',
            line: 'Line Detection',
            column: 'Column Mode'
        };
        return labels[mode] || mode;
    }

    getStyles() {
        return `
            :host {
                display: block;
                font-family: "Public Sans", -apple-system, sans-serif;
            }

            .unified-controls {
                background: #ffffff;
                border: 1px solid #d6d7d9;
                border-radius: 2px;
                padding: 24px;
            }

            .control-section {
                margin-bottom: 32px;
            }

            .control-section:last-child {
                margin-bottom: 0;
            }

            .section-title {
                font-size: 1.125rem;
                font-weight: 700;
                color: #112e51;
                margin-bottom: 16px;
            }

            .model-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                gap: 12px;
            }

            .model-card {
                background: #ffffff;
                border: 2px solid #d6d7d9;
                border-radius: 2px;
                padding: 16px;
                cursor: pointer;
                text-align: left;
                position: relative;
                transition: border-color 150ms;
            }

            .model-card:hover {
                border-color: #5b616b;
            }

            .model-card.selected {
                border-color: #112e51;
                background: #e7f2f8;
            }

            .model-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 8px;
            }

            .model-name {
                font-weight: 700;
                color: #112e51;
                font-size: 0.9375rem;
            }

            .model-accuracy {
                font-size: 0.8125rem;
                color: #2e8540;
                font-weight: 700;
            }

            .model-description {
                font-size: 0.875rem;
                color: #5b616b;
                line-height: 1.4;
            }

            .selected-badge {
                position: absolute;
                top: 8px;
                right: 8px;
                background: #112e51;
                color: #ffffff;
                font-size: 0.6875rem;
                font-weight: 700;
                padding: 2px 8px;
                border-radius: 2px;
            }

            .settings-grid {
                display: flex;
                flex-direction: column;
                gap: 20px;
            }

            .setting-group {
                display: flex;
                flex-direction: column;
                gap: 8px;
            }

            .setting-label {
                font-weight: 700;
                color: #212121;
                font-size: 0.9375rem;
            }

            .mode-buttons {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                gap: 8px;
            }

            .mode-btn {
                padding: 12px 16px;
                border: 2px solid #5b616b;
                border-radius: 2px;
                background: #ffffff;
                color: #212121;
                font-weight: 600;
                font-size: 0.875rem;
                cursor: pointer;
                transition: all 150ms;
            }

            .mode-btn:hover {
                border-color: #112e51;
                background: #f1f1f1;
            }

            .mode-btn.active {
                background: #112e51;
                color: #ffffff;
                border-color: #112e51;
            }

            .checkbox-label {
                display: flex;
                align-items: center;
                gap: 12px;
                cursor: pointer;
                color: #212121;
                font-size: 0.9375rem;
            }

            .checkbox-label input[type="checkbox"] {
                width: 20px;
                height: 20px;
                cursor: pointer;
            }

            .btn-process {
                width: 100%;
                padding: 16px 24px;
                background: #112e51;
                color: #ffffff;
                border: none;
                border-radius: 2px;
                font-size: 1rem;
                font-weight: 700;
                cursor: pointer;
                transition: background 150ms;
            }

            .btn-process:hover:not(:disabled) {
                background: #0d2540;
            }

            .btn-process:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }

            .btn-process.processing {
                background: #5b616b;
            }
        `;
    }

    attachEventListeners() {
        // Model selection
        this.shadowRoot.querySelectorAll('.model-card').forEach(card => {
            card.addEventListener('click', (e) => {
                const modelId = e.currentTarget.dataset.modelId;
                this.selectModel(modelId);
            });
        });

        // Detection mode buttons
        this.shadowRoot.querySelectorAll('.mode-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const mode = e.currentTarget.dataset.mode;
                this.setDetectionMode(mode);
            });
        });

        // Checkboxes
        const deskewCheckbox = this.shadowRoot.getElementById('deskew');
        if (deskewCheckbox) {
            deskewCheckbox.addEventListener('change', (e) => {
                this.deskewEnabled = e.target.checked;
                this.savePreferences();
                this.dispatchSettingsChange();
            });
        }

        const enhanceCheckbox = this.shadowRoot.getElementById('enhance');
        if (enhanceCheckbox) {
            enhanceCheckbox.addEventListener('change', (e) => {
                this.enhanceEnabled = e.target.checked;
                this.savePreferences();
                this.dispatchSettingsChange();
            });
        }

        // Process button
        const processBtn = this.shadowRoot.getElementById('processBtn');
        if (processBtn) {
            processBtn.addEventListener('click', () => {
                this.dispatchProcessRequest();
            });
        }
    }

    selectModel(modelId) {
        this.selectedModelId = modelId;
        this.savePreferences();
        this.render();
        this.attachEventListeners();
        
        // Dispatch event for parent components
        this.dispatchEvent(new CustomEvent('model-changed', {
            detail: { modelId: this.selectedModelId },
            bubbles: true,
            composed: true
        }));
    }

    setDetectionMode(mode) {
        this.detectionMode = mode;
        this.savePreferences();
        this.render();
        this.attachEventListeners();
        this.dispatchSettingsChange();
    }

    dispatchSettingsChange() {
        this.dispatchEvent(new CustomEvent('settings-changed', {
            detail: this.getSettings(),
            bubbles: true,
            composed: true
        }));
    }

    dispatchProcessRequest() {
        this.dispatchEvent(new CustomEvent('process-request', {
            detail: this.getSettings(),
            bubbles: true,
            composed: true
        }));
    }

    getSettings() {
        return {
            modelId: this.selectedModelId,
            detectionMode: this.detectionMode,
            enableDeskew: this.deskewEnabled,
            enableEnhancement: this.enhanceEnabled,
            manualRegions: this.manualRegions
        };
    }

    async processFile(file) {
        if (!file) {
            throw new Error('No file provided');
        }

        this.isProcessing = true;
        this.render();
        this.attachEventListeners();

        try {
            const formData = new FormData();
            formData.append('image', file);
            formData.append('model_id', this.selectedModelId);
            formData.append('detection_mode', this.detectionMode);
            formData.append('enable_deskew', this.deskewEnabled.toString());
            formData.append('enable_enhancement', this.enhanceEnabled.toString());
            formData.append('column_mode', (this.detectionMode === 'column').toString());

            if (this.manualRegions.length > 0) {
                formData.append('manual_regions', JSON.stringify(this.manualRegions));
            }

            const response = await fetch(`${this.apiBaseUrl}/api/extract`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Extraction failed');
            }

            const result = await response.json();
            
            this.isProcessing = false;
            this.render();
            this.attachEventListeners();

            return result;

        } catch (error) {
            this.isProcessing = false;
            this.render();
            this.attachEventListeners();
            throw error;
        }
    }
}

customElements.define('unified-extractor-controls', UnifiedExtractorControls);
