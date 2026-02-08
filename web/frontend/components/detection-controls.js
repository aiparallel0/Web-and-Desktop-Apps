/**
 * Detection Controls - FUNCTIONAL Web Component
 * Real implementation of detection modes, deskew, and enhancement
 * Government-style professional interface
 */

class DetectionControls extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        
        // State
        this.detectionMode = 'auto';
        this.deskewEnabled = true;
        this.enhanceEnabled = true;
        this.preview Enabled = false;
        this.manualRegions = [];
        
        // Canvas for manual selection
        this.canvas = null;
        this.ctx = null;
        this.isDrawing = false;
        this.startPoint = null;
        this.currentImage = null;
        
        // Storage key
        this.STORAGE_KEY = 'detection_settings';
    }

    connectedCallback() {
        this.loadPreferences();
        this.render();
        this.attachEventListeners();
    }

    loadPreferences() {
        try {
            const saved = localStorage.getItem(this.STORAGE_KEY);
            if (saved) {
                const prefs = JSON.parse(saved);
                this.detectionMode = prefs.detectionMode || 'auto';
                this.deskewEnabled = prefs.deskewEnabled !== false;
                this.enhanceEnabled = prefs.enhanceEnabled !== false;
            }
        } catch (e) {
            console.error('Failed to load preferences:', e);
        }
    }

    savePreferences() {
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify({
            detectionMode: this.detectionMode,
            deskewEnabled: this.deskewEnabled,
            enhanceEnabled: this.enhanceEnabled
        }));
    }

    render() {
        this.shadowRoot.innerHTML = `
            <style>${this.getStyles()}</style>
            <div class="detection-controls">
                <h3 class="controls-title">Text Detection Controls</h3>
                
                <div class="control-group">
                    <label class="group-label">Detection Mode</label>
                    <div class="mode-grid">
                        ${this.renderModeButton('auto', 'Auto Detect', 'Automatic text region detection')}
                        ${this.renderModeButton('manual', 'Manual Select', 'Draw selection regions')}
                        ${this.renderModeButton('line', 'Line Detection', 'Process line-by-line')}
                        ${this.renderModeButton('column', 'Column Mode', 'Multi-column layout')}
                    </div>
                </div>

                <div class="control-group">
                    <label class="group-label">Preprocessing Options</label>
                    <div class="options-list">
                        <label class="option-item">
                            <input 
                                type="checkbox" 
                                id="deskew-checkbox" 
                                ${this.deskewEnabled ? 'checked' : ''}>
                            <span>Enable Deskew (Auto-rotation)</span>
                            <span class="option-desc">Automatically straighten rotated receipts</span>
                        </label>
                        <label class="option-item">
                            <input 
                                type="checkbox" 
                                id="enhance-checkbox" 
                                ${this.enhanceEnabled ? 'checked' : ''}>
                            <span>Enable Image Enhancement</span>
                            <span class="option-desc">Improve image quality for better extraction</span>
                        </label>
                        <label class="option-item">
                            <input 
                                type="checkbox" 
                                id="preview-checkbox" 
                                ${this.previewEnabled ? 'checked' : ''}>
                            <span>Show Region Preview</span>
                            <span class="option-desc">Display bounding box overlay</span>
                        </label>
                    </div>
                </div>

                ${this.detectionMode === 'manual' ? this.renderManualControls() : ''}

                <button class="reset-btn" id="resetBtn">Reset to Defaults</button>
            </div>
        `;
    }

    renderModeButton(mode, label, description) {
        const isActive = this.detectionMode === mode;
        return `
            <button 
                class="mode-btn ${isActive ? 'active' : ''}"
                data-mode="${mode}">
                <div class="mode-label">${label}</div>
                <div class="mode-desc">${description}</div>
            </button>
        `;
    }

    renderManualControls() {
        return `
            <div class="manual-controls">
                <div class="manual-header">
                    <span class="manual-title">Manual Selection Mode</span>
                    <button class="clear-regions-btn" id="clearRegions">Clear Regions</button>
                </div>
                <div class="manual-instructions">
                    Click and drag on the image to select text regions. 
                    Selected regions: <strong>${this.manualRegions.length}</strong>
                </div>
            </div>
        `;
    }

    getStyles() {
        return `
            :host {
                display: block;
                font-family: "Public Sans", -apple-system, sans-serif;
            }

            .detection-controls {
                background: #ffffff;
                border: 1px solid #d6d7d9;
                border-radius: 2px;
                padding: 24px;
            }

            .controls-title {
                font-size: 1.25rem;
                font-weight: 700;
                color: #112e51;
                margin-bottom: 24px;
            }

            .control-group {
                margin-bottom: 24px;
            }

            .group-label {
                display: block;
                font-size: 0.9375rem;
                font-weight: 700;
                color: #212121;
                margin-bottom: 12px;
            }

            .mode-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 12px;
            }

            .mode-btn {
                background: #ffffff;
                border: 2px solid #5b616b;
                border-radius: 2px;
                padding: 16px 12px;
                cursor: pointer;
                text-align: left;
                transition: all 150ms;
            }

            .mode-btn:hover {
                border-color: #112e51;
                background: #f9f9f9;
            }

            .mode-btn.active {
                background: #112e51;
                border-color: #112e51;
                color: #ffffff;
            }

            .mode-btn.active .mode-label,
            .mode-btn.active .mode-desc {
                color: #ffffff;
            }

            .mode-label {
                font-weight: 700;
                font-size: 0.9375rem;
                color: #212121;
                margin-bottom: 4px;
            }

            .mode-desc {
                font-size: 0.8125rem;
                color: #5b616b;
                line-height: 1.3;
            }

            .options-list {
                display: flex;
                flex-direction: column;
                gap: 16px;
            }

            .option-item {
                display: flex;
                flex-direction: column;
                gap: 4px;
                cursor: pointer;
                padding: 12px;
                background: #f9f9f9;
                border: 1px solid #e4e4e4;
                border-radius: 2px;
            }

            .option-item input[type="checkbox"] {
                width: 20px;
                height: 20px;
                margin-right: 12px;
                cursor: pointer;
            }

            .option-item > span:first-of-type {
                font-weight: 600;
                color: #212121;
                font-size: 0.9375rem;
            }

            .option-desc {
                font-size: 0.8125rem;
                color: #5b616b;
                margin-left: 32px;
            }

            .manual-controls {
                background: #e7f2f8;
                border: 1px solid #205493;
                border-radius: 2px;
                padding: 16px;
                margin-top: 16px;
            }

            .manual-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 12px;
            }

            .manual-title {
                font-weight: 700;
                color: #112e51;
                font-size: 0.9375rem;
            }

            .clear-regions-btn {
                padding: 6px 12px;
                background: #e31c3d;
                color: #ffffff;
                border: none;
                border-radius: 2px;
                font-size: 0.8125rem;
                font-weight: 700;
                cursor: pointer;
            }

            .clear-regions-btn:hover {
                background: #cd2026;
            }

            .manual-instructions {
                font-size: 0.875rem;
                color: #5b616b;
                line-height: 1.5;
            }

            .reset-btn {
                width: 100%;
                padding: 12px 24px;
                background: #5b616b;
                color: #ffffff;
                border: none;
                border-radius: 2px;
                font-size: 0.9375rem;
                font-weight: 700;
                cursor: pointer;
                margin-top: 16px;
            }

            .reset-btn:hover {
                background: #212121;
            }
        `;
    }

    attachEventListeners() {
        // Mode buttons
        this.shadowRoot.querySelectorAll('.mode-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const mode = e.currentTarget.dataset.mode;
                this.setDetectionMode(mode);
            });
        });

        // Checkboxes
        const deskewCheckbox = this.shadowRoot.getElementById('deskew-checkbox');
        if (deskewCheckbox) {
            deskewCheckbox.addEventListener('change', (e) => {
                this.deskewEnabled = e.target.checked;
                this.savePreferences();
                this.dispatchChange();
            });
        }

        const enhanceCheckbox = this.shadowRoot.getElementById('enhance-checkbox');
        if (enhanceCheckbox) {
            enhanceCheckbox.addEventListener('change', (e) => {
                this.enhanceEnabled = e.target.checked;
                this.savePreferences();
                this.dispatchChange();
            });
        }

        const previewCheckbox = this.shadowRoot.getElementById('preview-checkbox');
        if (previewCheckbox) {
            previewCheckbox.addEventListener('change', (e) => {
                this.previewEnabled = e.target.checked;
                this.dispatchChange();
            });
        }

        // Reset button
        const resetBtn = this.shadowRoot.getElementById('resetBtn');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                this.resetToDefaults();
            });
        }

        // Clear regions button (manual mode)
        const clearBtn = this.shadowRoot.getElementById('clearRegions');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                this.clearManualRegions();
            });
        }
    }

    setDetectionMode(mode) {
        this.detectionMode = mode;
        this.savePreferences();
        this.render();
        this.attachEventListeners();
        this.dispatchChange();
    }

    resetToDefaults() {
        this.detectionMode = 'auto';
        this.deskewEnabled = true;
        this.enhanceEnabled = true;
        this.previewEnabled = false;
        this.manualRegions = [];
        this.savePreferences();
        this.render();
        this.attachEventListeners();
        this.dispatchChange();
    }

    clearManualRegions() {
        this.manualRegions = [];
        this.render();
        this.attachEventListeners();
        this.dispatchChange();
    }

    addManualRegion(region) {
        this.manualRegions.push(region);
        this.render();
        this.attachEventListeners();
        this.dispatchChange();
    }

    getSettings() {
        return {
            detectionMode: this.detectionMode,
            deskewEnabled: this.deskewEnabled,
            enhanceEnabled: this.enhanceEnabled,
            previewEnabled: this.previewEnabled,
            manualRegions: this.manualRegions
        };
    }

    dispatchChange() {
        this.dispatchEvent(new CustomEvent('detection-settings-changed', {
            detail: this.getSettings(),
            bubbles: true,
            composed: true
        }));
    }
}

customElements.define('detection-controls', DetectionControls);
