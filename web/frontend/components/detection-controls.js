/**
 * Detection Controls Web Component
 * 7-Button Advanced Text Detection Control Panel
 * 
 * Features:
 * 1. Auto Detect - Automatic text region detection
 * 2. Manual Select - Click and drag to select text regions
 * 3. Line Detection - Detect and process line-by-line
 * 4. Column Mode - Handle multi-column receipts
 * 5. Rotate & Deskew - Auto-rotate and straighten image
 * 6. Enhance Quality - Apply image preprocessing filters
 * 7. Region Preview - Toggle bounding box overlay
 */

class DetectionControls extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        
        // Detection state
        this.detectionMode = 'auto'; // auto, manual, line, column
        this.deskewEnabled = true;
        this.enhanceEnabled = true;
        this.previewEnabled = false;
        this.manualRegions = [];
        
        // Preferences storage key
        this.STORAGE_KEY = 'receipt_detection_preferences';
    }

    connectedCallback() {
        this.loadPreferences();
        this.render();
        this.setupEventListeners();
    }

    render() {
        this.shadowRoot.innerHTML = `
            <style>
                ${this.getStyles()}
            </style>
            <div class="detection-controls">
                <div class="controls-header">
                    <h3 class="controls-title">
                        <svg class="title-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="3" y="3" width="18" height="18" rx="2"/>
                            <path d="M9 9h6M9 15h6"/>
                        </svg>
                        Text Detection Controls
                    </h3>
                    <button class="reset-btn" id="resetBtn" title="Reset to defaults">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>
                            <path d="M21 3v5h-5M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>
                            <path d="M3 21v-5h5"/>
                        </svg>
                    </button>
                </div>

                <div class="controls-grid">
                    <!-- Mode Selection -->
                    <div class="control-group mode-group">
                        <label class="group-label">Detection Mode</label>
                        <div class="mode-buttons">
                            <button class="mode-btn active" data-mode="auto" title="Automatic text region detection">
                                <svg class="mode-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
                                </svg>
                                <span class="mode-label">Auto Detect</span>
                                <span class="mode-desc">Automatic detection</span>
                            </button>

                            <button class="mode-btn" data-mode="manual" title="Click and drag to select text regions">
                                <svg class="mode-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2v-4M9 21H5a2 2 0 0 1-2-2v-4"/>
                                </svg>
                                <span class="mode-label">Manual Select</span>
                                <span class="mode-desc">Draw regions</span>
                            </button>

                            <button class="mode-btn" data-mode="line" title="Detect and process line-by-line">
                                <svg class="mode-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <line x1="3" y1="6" x2="21" y2="6"/>
                                    <line x1="3" y1="12" x2="21" y2="12"/>
                                    <line x1="3" y1="18" x2="21" y2="18"/>
                                </svg>
                                <span class="mode-label">Line Detection</span>
                                <span class="mode-desc">Line-by-line</span>
                            </button>

                            <button class="mode-btn" data-mode="column" title="Handle multi-column receipts">
                                <svg class="mode-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <rect x="3" y="3" width="7" height="18"/>
                                    <rect x="14" y="3" width="7" height="18"/>
                                </svg>
                                <span class="mode-label">Column Mode</span>
                                <span class="mode-desc">Multi-column</span>
                            </button>
                        </div>
                    </div>

                    <!-- Enhancement Options -->
                    <div class="control-group options-group">
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
                </div>

                <!-- Manual Region Info (shown when manual mode is selected) -->
                <div class="manual-info hidden" id="manualInfo">
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
                    <button class="clear-regions-btn" id="clearRegionsBtn">
                        Clear All Regions
                    </button>
                </div>

                <!-- Apply Button -->
                <div class="controls-footer">
                    <button class="apply-btn" id="applyBtn">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="20 6 9 17 4 12"/>
                        </svg>
                        Apply Settings
                    </button>
                </div>
            </div>
        `;
    }

    getStyles() {
        return `
            * {
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }

            .detection-controls {
                background: white;
                border-radius: 12px;
                border: 1px solid #e5e7eb;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                overflow: hidden;
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            }

            .controls-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 16px 20px;
                background: #3B82F6;
                color: white;
            }

            .controls-title {
                display: flex;
                align-items: center;
                gap: 10px;
                font-size: 1.125rem;
                font-weight: 600;
                margin: 0;
            }

            .title-icon {
                width: 24px;
                height: 24px;
            }

            .reset-btn {
                background: rgba(255, 255, 255, 0.2);
                border: none;
                border-radius: 6px;
                padding: 8px;
                cursor: pointer;
                transition: background 0.2s;
                display: flex;
                align-items: center;
                justify-content: center;
            }

            .reset-btn:hover {
                background: rgba(255, 255, 255, 0.3);
            }

            .reset-btn svg {
                width: 18px;
                height: 18px;
                stroke: white;
            }

            .controls-grid {
                padding: 20px;
                display: flex;
                flex-direction: column;
                gap: 24px;
            }

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
                gap: 12px;
            }

            .mode-btn {
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 8px;
                padding: 16px 12px;
                background: #f9fafb;
                border: 2px solid #e5e7eb;
                border-radius: 10px;
                cursor: pointer;
                transition: all 0.2s;
                text-align: center;
            }

            .mode-btn:hover {
                background: #f3f4f6;
                border-color: #d1d5db;
                transform: translateY(-2px);
            }

            .mode-btn.active {
                background: #eff6ff;
                border-color: #2563eb;
                box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
            }

            .mode-icon {
                width: 32px;
                height: 32px;
                stroke: #6b7280;
                transition: stroke 0.2s;
            }

            .mode-btn.active .mode-icon {
                stroke: #2563eb;
            }

            .mode-label {
                font-size: 0.875rem;
                font-weight: 600;
                color: #111827;
            }

            .mode-desc {
                font-size: 0.75rem;
                color: #6b7280;
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
                width: 20px;
                height: 20px;
                cursor: pointer;
                accent-color: #2563eb;
            }

            .option-content {
                display: flex;
                align-items: center;
                gap: 12px;
                flex: 1;
            }

            .option-icon {
                width: 24px;
                height: 24px;
                stroke: #6b7280;
                flex-shrink: 0;
            }

            .option-text {
                display: flex;
                flex-direction: column;
                gap: 2px;
            }

            .option-text strong {
                font-size: 0.875rem;
                color: #111827;
            }

            .option-text span {
                font-size: 0.75rem;
                color: #6b7280;
            }

            /* Manual Info */
            .manual-info {
                margin: 0 20px;
                padding: 16px;
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
                width: 24px;
                height: 24px;
                stroke: #d97706;
                flex-shrink: 0;
            }

            .info-banner strong {
                display: block;
                color: #92400e;
                font-size: 0.875rem;
                margin-bottom: 4px;
            }

            .info-banner p {
                font-size: 0.8125rem;
                color: #78350f;
                margin: 0;
            }

            .clear-regions-btn {
                width: 100%;
                padding: 8px 16px;
                background: white;
                border: 1px solid #fbbf24;
                border-radius: 6px;
                color: #d97706;
                font-size: 0.875rem;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s;
            }

            .clear-regions-btn:hover {
                background: #fef3c7;
            }

            /* Footer */
            .controls-footer {
                padding: 16px 20px;
                background: #f9fafb;
                border-top: 1px solid #e5e7eb;
            }

            .apply-btn {
                width: 100%;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                padding: 12px 24px;
                background: #2563eb;
                border: none;
                border-radius: 8px;
                color: white;
                font-size: 0.9375rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s;
            }

            .apply-btn:hover {
                background: #1e40af;
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
            }

            .apply-btn svg {
                width: 20px;
                height: 20px;
            }

            /* Responsive */
            @media (max-width: 768px) {
                .mode-buttons {
                    grid-template-columns: repeat(2, 1fr);
                }
            }
        `;
    }

    setupEventListeners() {
        // Mode selection
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

        // Options toggles
        const deskewToggle = this.shadowRoot.getElementById('deskewToggle');
        const enhanceToggle = this.shadowRoot.getElementById('enhanceToggle');
        const previewToggle = this.shadowRoot.getElementById('previewToggle');

        deskewToggle.addEventListener('change', (e) => {
            this.deskewEnabled = e.target.checked;
            this.savePreferences();
        });

        enhanceToggle.addEventListener('change', (e) => {
            this.enhanceEnabled = e.target.checked;
            this.savePreferences();
        });

        previewToggle.addEventListener('change', (e) => {
            this.previewEnabled = e.target.checked;
            this.dispatchEvent(new CustomEvent('preview-toggle', { detail: { enabled: this.previewEnabled } }));
            this.savePreferences();
        });

        // Clear regions
        const clearRegionsBtn = this.shadowRoot.getElementById('clearRegionsBtn');
        clearRegionsBtn.addEventListener('click', () => {
            this.manualRegions = [];
            this.updateManualInfo();
            this.dispatchEvent(new CustomEvent('regions-cleared'));
        });

        // Reset
        const resetBtn = this.shadowRoot.getElementById('resetBtn');
        resetBtn.addEventListener('click', () => {
            this.resetToDefaults();
        });

        // Apply
        const applyBtn = this.shadowRoot.getElementById('applyBtn');
        applyBtn.addEventListener('click', () => {
            this.applySettings();
        });
    }

    updateManualInfo() {
        const manualInfo = this.shadowRoot.getElementById('manualInfo');
        const regionCount = this.shadowRoot.getElementById('regionCount');
        
        if (this.detectionMode === 'manual') {
            manualInfo.classList.remove('hidden');
        } else {
            manualInfo.classList.add('hidden');
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
            detection_mode: this.detectionMode,
            enable_deskew: this.deskewEnabled,
            enable_enhancement: this.enhanceEnabled,
            column_mode: this.detectionMode === 'column',
            manual_regions: this.detectionMode === 'manual' ? this.manualRegions : null
        };
    }

    applySettings() {
        const settings = this.getSettings();
        this.dispatchEvent(new CustomEvent('settings-applied', { detail: settings }));
    }

    resetToDefaults() {
        this.detectionMode = 'auto';
        this.deskewEnabled = true;
        this.enhanceEnabled = true;
        this.previewEnabled = false;
        this.manualRegions = [];
        
        this.savePreferences();
        this.render();
        this.setupEventListeners();
    }

    loadPreferences() {
        try {
            const saved = localStorage.getItem(this.STORAGE_KEY);
            if (saved) {
                const prefs = JSON.parse(saved);
                this.detectionMode = prefs.detectionMode || 'auto';
                this.deskewEnabled = prefs.deskewEnabled !== false;
                this.enhanceEnabled = prefs.enhanceEnabled !== false;
                this.previewEnabled = prefs.previewEnabled || false;
            }
        } catch (error) {
            console.error('Error loading detection preferences:', error);
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
            localStorage.setItem(this.STORAGE_KEY, JSON.stringify(prefs));
        } catch (error) {
            console.error('Error saving detection preferences:', error);
        }
    }
}

// Register the custom element
customElements.define('detection-controls', DetectionControls);
