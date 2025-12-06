/**
 * Unified Extractor Controls Web Component
 * Combines Model Selection (Extraction Methods) with Text Detection Controls
 * 
 * This unified component provides:
 * 1. Model Selection - Choose from 7 OCR extraction methods
 * 2. Detection Mode - Auto, Manual, Line, or Column detection
 * 3. Enhancement Options - Deskew and image quality enhancement
 * 4. Region Preview - Visual bounding box overlay
 * 
 * All in one cohesive, systematic interface.
 */

class UnifiedExtractorControls extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        
        // Model selection state
        this.selectedModelId = null;
        this.availableModels = [];
        
        // Detection control state
        this.detectionMode = 'auto'; // auto, manual, line, column
        this.deskewEnabled = true;
        this.enhanceEnabled = true;
        this.previewEnabled = false;
        this.manualRegions = [];
        
        // Storage keys
        this.MODEL_STORAGE_KEY = 'receipt_selected_model';
        this.DETECTION_STORAGE_KEY = 'receipt_detection_preferences';
    }

    connectedCallback() {
        this.loadPreferences();
        this.fetchAvailableModels();
    }

    async fetchAvailableModels() {
        try {
            const apiUrl = this.getAttribute('api-url') || '/api/models';
            const response = await fetch(apiUrl);
            
            if (response.ok) {
                const data = await response.json();
                this.availableModels = data.models || [];
                
                if (!this.selectedModelId && data.default_model) {
                    this.selectedModelId = data.default_model;
                }
            } else {
                this.availableModels = this.getDefaultModels();
            }
        } catch (error) {
            console.error('Error fetching models:', error);
            this.availableModels = this.getDefaultModels();
        }
        
        this.render();
        this.setupEventListeners();
    }

    getDefaultModels() {
        return [
            {
                id: 'ocr_tesseract',
                name: 'Tesseract OCR',
                description: 'Fast & reliable for clear receipts',
                accuracy: '~95%'
            },
            {
                id: 'ocr_easyocr',
                name: 'EasyOCR with Regex',
                description: 'Ready-to-use OCR with 80+ languages',
                accuracy: '~90%'
            },
            {
                id: 'ocr_easyocr_spatial',
                name: 'EasyOCR with Spatial Bounding Boxes',
                description: 'EasyOCR with spatial structure detection',
                accuracy: '~92%'
            },
            {
                id: 'ocr_paddle',
                name: 'PaddleOCR with Regex',
                description: 'Multilingual, high accuracy',
                accuracy: '~93%'
            },
            {
                id: 'ocr_paddle_spatial',
                name: 'PaddleOCR with Spatial Bounding Boxes',
                description: 'PaddleOCR with spatial structure detection',
                accuracy: '~94%'
            },
            {
                id: 'florence2',
                name: 'Florence-2 AI',
                description: 'Advanced AI vision-language model',
                accuracy: '~98%'
            },
            {
                id: 'donut_cord',
                name: 'DONUT End-to-End',
                description: 'Fast AI-powered extraction',
                accuracy: '~96%'
            }
        ];
    }

    render() {
        this.shadowRoot.innerHTML = `
            <style>
                ${this.getStyles()}
            </style>
            <div class="unified-controls">
                <!-- Main Header -->
                <div class="main-header">
                    <h2 class="main-title">
                        <svg class="main-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
                        </svg>
                        Extraction Configuration
                    </h2>
                    <p class="main-subtitle">Configure your OCR extraction method and text detection settings</p>
                </div>

                <!-- Unified Controls Grid -->
                <div class="unified-grid">
                    <!-- Section 1: Extraction Method Selection -->
                    <div class="control-section">
                        <div class="section-header">
                            <h3 class="section-title">
                                <svg class="section-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
                                </svg>
                                Extraction Method
                            </h3>
                            <span class="section-badge">Step 1</span>
                        </div>
                        <div class="models-grid">
                            ${this.availableModels.map(model => this.renderModelCard(model)).join('')}
                        </div>
                    </div>

                    <!-- Section 2: Text Detection Controls -->
                    <div class="control-section">
                        <div class="section-header">
                            <h3 class="section-title">
                                <svg class="section-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <rect x="3" y="3" width="18" height="18" rx="2"/>
                                    <path d="M9 9h6M9 15h6"/>
                                </svg>
                                Detection Settings
                            </h3>
                            <span class="section-badge">Step 2</span>
                        </div>

                        <!-- Detection Mode -->
                        <div class="control-group">
                            <label class="group-label">Detection Mode</label>
                            <div class="mode-buttons">
                                <button class="mode-btn ${this.detectionMode === 'auto' ? 'active' : ''}" data-mode="auto">
                                    <svg class="mode-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
                                    </svg>
                                    <span class="mode-label">Auto Detect</span>
                                </button>
                                <button class="mode-btn ${this.detectionMode === 'manual' ? 'active' : ''}" data-mode="manual">
                                    <svg class="mode-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2v-4M9 21H5a2 2 0 0 1-2-2v-4"/>
                                    </svg>
                                    <span class="mode-label">Manual Select</span>
                                </button>
                                <button class="mode-btn ${this.detectionMode === 'line' ? 'active' : ''}" data-mode="line">
                                    <svg class="mode-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <line x1="3" y1="6" x2="21" y2="6"/>
                                        <line x1="3" y1="12" x2="21" y2="12"/>
                                        <line x1="3" y1="18" x2="21" y2="18"/>
                                    </svg>
                                    <span class="mode-label">Line Detection</span>
                                </button>
                                <button class="mode-btn ${this.detectionMode === 'column' ? 'active' : ''}" data-mode="column">
                                    <svg class="mode-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <rect x="3" y="3" width="7" height="18"/>
                                        <rect x="14" y="3" width="7" height="18"/>
                                    </svg>
                                    <span class="mode-label">Column Mode</span>
                                </button>
                            </div>
                        </div>

                        <!-- Enhancement Options -->
                        <div class="control-group">
                            <label class="group-label">Enhancement Options</label>
                            <div class="options-list">
                                <label class="option-item">
                                    <input type="checkbox" id="deskewToggle" ${this.deskewEnabled ? 'checked' : ''}>
                                    <div class="option-content">
                                        <svg class="option-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
                                            <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
                                            <line x1="12" y1="22.08" x2="12" y2="12"/>
                                        </svg>
                                        <div class="option-text">
                                            <strong>Rotate & Deskew</strong>
                                            <span>Auto-rotate and straighten tilted images</span>
                                        </div>
                                    </div>
                                </label>
                                <label class="option-item">
                                    <input type="checkbox" id="enhanceToggle" ${this.enhanceEnabled ? 'checked' : ''}>
                                    <div class="option-content">
                                        <svg class="option-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                            <circle cx="12" cy="12" r="3"/>
                                            <path d="M12 1v6m0 6v6M5.64 5.64l4.24 4.24m4.24 4.24l4.24 4.24m-12.72 0l4.24-4.24m4.24-4.24l4.24-4.24"/>
                                        </svg>
                                        <div class="option-text">
                                            <strong>Enhance Quality</strong>
                                            <span>Apply preprocessing filters for better OCR</span>
                                        </div>
                                    </div>
                                </label>
                                <label class="option-item">
                                    <input type="checkbox" id="previewToggle" ${this.previewEnabled ? 'checked' : ''}>
                                    <div class="option-content">
                                        <svg class="option-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                                            <circle cx="12" cy="12" r="3"/>
                                        </svg>
                                        <div class="option-text">
                                            <strong>Region Preview</strong>
                                            <span>Show bounding boxes on image</span>
                                        </div>
                                    </div>
                                </label>
                            </div>
                        </div>

                        <!-- Manual Region Info -->
                        <div class="manual-info ${this.detectionMode === 'manual' ? '' : 'hidden'}" id="manualInfo">
                            <div class="info-banner">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <circle cx="12" cy="12" r="10"/>
                                    <line x1="12" y1="16" x2="12" y2="12"/>
                                    <line x1="12" y1="8" x2="12.01" y2="8"/>
                                </svg>
                                <div>
                                    <strong>Manual Selection Mode</strong>
                                    <p>Click and drag on the image to select text regions. Selected regions: <span id="regionCount">0</span></p>
                                </div>
                            </div>
                            <button class="clear-regions-btn" id="clearRegionsBtn">Clear All Regions</button>
                        </div>
                    </div>
                </div>

                <!-- Action Footer -->
                <div class="action-footer">
                    <button class="reset-btn" id="resetBtn">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>
                            <path d="M21 3v5h-5M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>
                            <path d="M3 21v-5h5"/>
                        </svg>
                        Reset to Defaults
                    </button>
                    <button class="apply-btn" id="applyBtn">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="20 6 9 17 4 12"/>
                        </svg>
                        Apply Settings & Extract
                    </button>
                </div>
            </div>
        `;
    }

    renderModelCard(model) {
        const isSelected = model.id === this.selectedModelId;
        const selectedClass = isSelected ? 'selected' : '';
        
        return `
            <button class="model-card ${selectedClass}" data-model-id="${model.id}">
                <div class="model-check">
                    ${isSelected ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>' : ''}
                </div>
                <div class="model-content">
                    <h4 class="model-name">${model.name}</h4>
                    ${model.accuracy ? `<span class="model-accuracy">${model.accuracy}</span>` : ''}
                    <p class="model-description">${model.description}</p>
                </div>
            </button>
        `;
    }

    getStyles() {
        return `
            * {
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }

            .unified-controls {
                background: white;
                border-radius: 16px;
                border: 1px solid #e5e7eb;
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
                overflow: hidden;
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            }

            /* Main Header */
            .main-header {
                padding: 24px 28px;
                background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
                color: white;
            }

            .main-title {
                display: flex;
                align-items: center;
                gap: 12px;
                font-size: 1.5rem;
                font-weight: 700;
                margin: 0 0 8px 0;
            }

            .main-icon {
                width: 28px;
                height: 28px;
            }

            .main-subtitle {
                font-size: 0.9375rem;
                opacity: 0.95;
                margin: 0;
            }

            /* Unified Grid */
            .unified-grid {
                padding: 28px;
                display: flex;
                flex-direction: column;
                gap: 32px;
            }

            /* Control Section */
            .control-section {
                display: flex;
                flex-direction: column;
                gap: 16px;
            }

            .section-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding-bottom: 12px;
                border-bottom: 2px solid #e5e7eb;
            }

            .section-title {
                display: flex;
                align-items: center;
                gap: 10px;
                font-size: 1.125rem;
                font-weight: 600;
                color: #111827;
                margin: 0;
            }

            .section-icon {
                width: 22px;
                height: 22px;
                stroke: #3B82F6;
            }

            .section-badge {
                background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
                color: white;
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 0.75rem;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }

            /* Models Grid */
            .models-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                gap: 12px;
            }

            .model-card {
                display: flex;
                align-items: flex-start;
                gap: 12px;
                padding: 14px;
                background: #f9fafb;
                border: 2px solid #e5e7eb;
                border-radius: 10px;
                cursor: pointer;
                transition: all 0.2s;
                text-align: left;
                width: 100%;
            }

            .model-card:hover {
                background: #f3f4f6;
                border-color: #d1d5db;
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
            }

            .model-card.selected {
                background: #EFF6FF;
                border-color: #3B82F6;
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
            }

            .model-check {
                width: 22px;
                height: 22px;
                border-radius: 50%;
                border: 2px solid #d1d5db;
                display: flex;
                align-items: center;
                justify-content: center;
                flex-shrink: 0;
                background: white;
                transition: all 0.2s;
            }

            .model-card.selected .model-check {
                background: #3B82F6;
                border-color: #3B82F6;
            }

            .model-check svg {
                width: 14px;
                height: 14px;
                stroke: white;
            }

            .model-content {
                flex: 1;
                display: flex;
                flex-direction: column;
                gap: 4px;
            }

            .model-name {
                font-size: 0.875rem;
                font-weight: 600;
                color: #111827;
                margin: 0;
            }

            .model-accuracy {
                font-size: 0.75rem;
                font-weight: 600;
                color: #10b981;
                display: inline-block;
            }

            .model-description {
                font-size: 0.75rem;
                color: #6b7280;
                margin: 0;
                line-height: 1.3;
            }

            /* Control Group */
            .control-group {
                display: flex;
                flex-direction: column;
                gap: 12px;
            }

            .group-label {
                font-size: 0.875rem;
                font-weight: 600;
                color: #374151;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }

            /* Mode Buttons */
            .mode-buttons {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
                gap: 10px;
            }

            .mode-btn {
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 6px;
                padding: 12px 10px;
                background: #f9fafb;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.2s;
                text-align: center;
            }

            .mode-btn:hover {
                background: #f3f4f6;
                border-color: #d1d5db;
                transform: translateY(-1px);
            }

            .mode-btn.active {
                background: #EFF6FF;
                border-color: #3B82F6;
                box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
            }

            .mode-icon {
                width: 24px;
                height: 24px;
                stroke: #6b7280;
                transition: stroke 0.2s;
            }

            .mode-btn.active .mode-icon {
                stroke: #3B82F6;
            }

            .mode-label {
                font-size: 0.8125rem;
                font-weight: 500;
                color: #111827;
            }

            /* Options List */
            .options-list {
                display: flex;
                flex-direction: column;
                gap: 8px;
            }

            .option-item {
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 12px;
                background: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.2s;
            }

            .option-item:hover {
                background: #f3f4f6;
                border-color: #d1d5db;
            }

            .option-item input[type="checkbox"] {
                width: 18px;
                height: 18px;
                cursor: pointer;
                accent-color: #3B82F6;
            }

            .option-content {
                display: flex;
                align-items: center;
                gap: 12px;
                flex: 1;
            }

            .option-icon {
                width: 22px;
                height: 22px;
                stroke: #6b7280;
                flex-shrink: 0;
            }

            .option-text {
                display: flex;
                flex-direction: column;
                gap: 2px;
            }

            .option-text strong {
                font-size: 0.8125rem;
                color: #111827;
            }

            .option-text span {
                font-size: 0.75rem;
                color: #6b7280;
            }

            /* Manual Info */
            .manual-info {
                padding: 14px;
                background: #fffbeb;
                border: 1px solid #fcd34d;
                border-radius: 8px;
            }

            .manual-info.hidden {
                display: none;
            }

            .info-banner {
                display: flex;
                gap: 12px;
                margin-bottom: 12px;
            }

            .info-banner svg {
                width: 22px;
                height: 22px;
                stroke: #d97706;
                flex-shrink: 0;
            }

            .info-banner strong {
                display: block;
                color: #92400e;
                font-size: 0.8125rem;
                margin-bottom: 4px;
            }

            .info-banner p {
                font-size: 0.75rem;
                color: #78350f;
                margin: 0;
            }

            .clear-regions-btn {
                width: 100%;
                padding: 8px 14px;
                background: white;
                border: 1px solid #fbbf24;
                border-radius: 6px;
                color: #d97706;
                font-size: 0.8125rem;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s;
            }

            .clear-regions-btn:hover {
                background: #fef3c7;
            }

            /* Action Footer */
            .action-footer {
                display: flex;
                gap: 12px;
                padding: 20px 28px;
                background: #f9fafb;
                border-top: 1px solid #e5e7eb;
            }

            .reset-btn {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                padding: 12px 20px;
                background: white;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                color: #6b7280;
                font-size: 0.9375rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s;
            }

            .reset-btn:hover {
                background: #f3f4f6;
                border-color: #d1d5db;
            }

            .reset-btn svg {
                width: 18px;
                height: 18px;
            }

            .apply-btn {
                flex: 1;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                padding: 12px 24px;
                background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
                border: none;
                border-radius: 8px;
                color: white;
                font-size: 0.9375rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s;
            }

            .apply-btn:hover {
                transform: translateY(-1px);
                box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
            }

            .apply-btn svg {
                width: 20px;
                height: 20px;
            }

            /* Responsive */
            @media (max-width: 768px) {
                .models-grid {
                    grid-template-columns: 1fr;
                }

                .mode-buttons {
                    grid-template-columns: repeat(2, 1fr);
                }

                .action-footer {
                    flex-direction: column;
                }
            }
        `;
    }

    setupEventListeners() {
        // Model selection
        const modelCards = this.shadowRoot.querySelectorAll('.model-card');
        modelCards.forEach(card => {
            card.addEventListener('click', () => {
                const modelId = card.dataset.modelId;
                this.selectModel(modelId);
            });
        });

        // Detection mode selection
        const modeButtons = this.shadowRoot.querySelectorAll('.mode-btn');
        modeButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                modeButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.detectionMode = btn.dataset.mode;
                this.updateManualInfo();
                this.savePreferences();
            });
        });

        // Enhancement options
        const deskewToggle = this.shadowRoot.getElementById('deskewToggle');
        const enhanceToggle = this.shadowRoot.getElementById('enhanceToggle');
        const previewToggle = this.shadowRoot.getElementById('previewToggle');

        deskewToggle?.addEventListener('change', (e) => {
            this.deskewEnabled = e.target.checked;
            this.savePreferences();
        });

        enhanceToggle?.addEventListener('change', (e) => {
            this.enhanceEnabled = e.target.checked;
            this.savePreferences();
        });

        previewToggle?.addEventListener('change', (e) => {
            this.previewEnabled = e.target.checked;
            this.dispatchEvent(new CustomEvent('preview-toggle', { detail: { enabled: this.previewEnabled } }));
            this.savePreferences();
        });

        // Clear regions
        const clearRegionsBtn = this.shadowRoot.getElementById('clearRegionsBtn');
        clearRegionsBtn?.addEventListener('click', () => {
            this.manualRegions = [];
            this.updateManualInfo();
            this.dispatchEvent(new CustomEvent('regions-cleared'));
        });

        // Reset button
        const resetBtn = this.shadowRoot.getElementById('resetBtn');
        resetBtn?.addEventListener('click', () => {
            this.resetToDefaults();
        });

        // Apply button
        const applyBtn = this.shadowRoot.getElementById('applyBtn');
        applyBtn?.addEventListener('click', () => {
            this.applySettings();
        });
    }

    selectModel(modelId) {
        this.selectedModelId = modelId;
        this.saveSelectedModel();
        
        // Update visual state
        const cards = this.shadowRoot.querySelectorAll('.model-card');
        cards.forEach(card => {
            if (card.dataset.modelId === modelId) {
                card.classList.add('selected');
                const checkDiv = card.querySelector('.model-check');
                if (checkDiv) {
                    checkDiv.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>';
                }
            } else {
                card.classList.remove('selected');
                const checkDiv = card.querySelector('.model-check');
                if (checkDiv) {
                    checkDiv.innerHTML = '';
                }
            }
        });
        
        // Dispatch event
        this.dispatchEvent(new CustomEvent('model-selected', {
            detail: {
                modelId: modelId,
                model: this.availableModels.find(m => m.id === modelId)
            }
        }));
    }

    updateManualInfo() {
        const manualInfo = this.shadowRoot.getElementById('manualInfo');
        const regionCount = this.shadowRoot.getElementById('regionCount');
        
        if (manualInfo) {
            if (this.detectionMode === 'manual') {
                manualInfo.classList.remove('hidden');
            } else {
                manualInfo.classList.add('hidden');
            }
        }
        
        if (regionCount) {
            regionCount.textContent = this.manualRegions.length;
        }
    }

    addManualRegion(region) {
        this.manualRegions.push(region);
        this.updateManualInfo();
    }

    getSettings() {
        return {
            model_id: this.selectedModelId,
            model: this.availableModels.find(m => m.id === this.selectedModelId),
            detection_mode: this.detectionMode,
            enable_deskew: this.deskewEnabled,
            enable_enhancement: this.enhanceEnabled,
            column_mode: this.detectionMode === 'column',
            manual_regions: this.detectionMode === 'manual' ? this.manualRegions : null,
            preview_enabled: this.previewEnabled
        };
    }

    applySettings() {
        const settings = this.getSettings();
        this.dispatchEvent(new CustomEvent('settings-applied', { detail: settings }));
    }

    resetToDefaults() {
        this.selectedModelId = 'ocr_tesseract';
        this.detectionMode = 'auto';
        this.deskewEnabled = true;
        this.enhanceEnabled = true;
        this.previewEnabled = false;
        this.manualRegions = [];
        
        this.savePreferences();
        this.saveSelectedModel();
        this.render();
        this.setupEventListeners();
    }

    loadPreferences() {
        try {
            // Load model selection
            const savedModel = localStorage.getItem(this.MODEL_STORAGE_KEY);
            if (savedModel) {
                this.selectedModelId = savedModel;
            }

            // Load detection preferences
            const savedDetection = localStorage.getItem(this.DETECTION_STORAGE_KEY);
            if (savedDetection) {
                const prefs = JSON.parse(savedDetection);
                this.detectionMode = prefs.detectionMode || 'auto';
                this.deskewEnabled = prefs.deskewEnabled !== false;
                this.enhanceEnabled = prefs.enhanceEnabled !== false;
                this.previewEnabled = prefs.previewEnabled || false;
            }
        } catch (error) {
            console.error('Error loading preferences:', error);
        }
    }

    savePreferences() {
        try {
            const prefs = {
                detectionMode: this.detectionMode,
                deskewEnabled: this.deskewEnabled,
                enhanceEnabled: this.enhanceEnabled,
                previewEnabled: this.previewEnabled
            };
            localStorage.setItem(this.DETECTION_STORAGE_KEY, JSON.stringify(prefs));
        } catch (error) {
            console.error('Error saving detection preferences:', error);
        }
    }

    saveSelectedModel() {
        try {
            if (this.selectedModelId) {
                localStorage.setItem(this.MODEL_STORAGE_KEY, this.selectedModelId);
            }
        } catch (error) {
            console.error('Error saving selected model:', error);
        }
    }
}

// Register the custom element
customElements.define('unified-extractor-controls', UnifiedExtractorControls);
