/**
 * Model Selector Web Component
 * Displays all 7 extraction methods as clickable options
 * 
 * Features:
 * - Shows all available OCR extraction methods
 * - Allows user to select preferred extraction method
 * - Displays method descriptions and capabilities
 * - Visual indication of selected method
 */

class ModelSelector extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        
        // State
        this.selectedModelId = null;
        this.availableModels = [];
        
        // Storage key for persisting selection
        this.STORAGE_KEY = 'receipt_selected_model';
    }

    connectedCallback() {
        this.loadSelectedModel();
        this.fetchAvailableModels();
    }

    async fetchAvailableModels() {
        try {
            // Try to fetch from API
            const apiUrl = this.getAttribute('api-url') || '/api/models';
            const response = await fetch(apiUrl);
            
            if (response.ok) {
                const data = await response.json();
                this.availableModels = data.models || [];
                
                // Set default if none selected
                if (!this.selectedModelId && data.default_model) {
                    this.selectedModelId = data.default_model;
                }
            } else {
                // Fallback to hardcoded list matching the 7 methods
                this.availableModels = this.getDefaultModels();
            }
        } catch (error) {
            console.error('Error fetching models:', error);
            // Fallback to hardcoded list
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
                description: 'Fast & reliable for clear receipts'
            },
            {
                id: 'ocr_easyocr',
                name: 'EasyOCR with Regex',
                description: 'Ready-to-use OCR with 80+ languages'
            },
            {
                id: 'ocr_easyocr_spatial',
                name: 'EasyOCR with Spatial Bounding Boxes',
                description: 'EasyOCR with spatial structure detection'
            },
            {
                id: 'ocr_paddle',
                name: 'PaddleOCR with Regex',
                description: 'Multilingual, high accuracy'
            },
            {
                id: 'ocr_paddle_spatial',
                name: 'PaddleOCR with Spatial Bounding Boxes',
                description: 'PaddleOCR with spatial structure detection'
            },
            {
                id: 'florence2',
                name: 'Florence-2 AI',
                description: 'Advanced AI vision-language model'
            },
            {
                id: 'donut_cord',
                name: 'DONUT End-to-End',
                description: 'Fast AI-powered extraction'
            }
        ];
    }

    render() {
        this.shadowRoot.innerHTML = `
            <style>
                ${this.getStyles()}
            </style>
            <div class="model-selector">
                <div class="selector-header">
                    <h3 class="selector-title">
                        <svg class="title-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
                        </svg>
                        Extraction Method
                    </h3>
                    <p class="selector-subtitle">Choose an OCR extraction method</p>
                </div>

                <div class="models-grid">
                    ${this.availableModels.map(model => this.renderModelCard(model)).join('')}
                </div>
            </div>
        `;
    }

    renderModelCard(model) {
        const isSelected = model.id === this.selectedModelId;
        const selectedClass = isSelected ? 'selected' : '';
        
        return `
            <button class="model-card ${selectedClass}" data-model-id="${model.id}">
                <div class="model-header">
                    <div class="model-check">
                        ${isSelected ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>' : ''}
                    </div>
                    <h4 class="model-name">${model.name}</h4>
                </div>
                <p class="model-description">${model.description}</p>
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

            .model-selector {
                background: white;
                border-radius: 12px;
                border: 1px solid #e5e7eb;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                overflow: hidden;
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            }

            .selector-header {
                padding: 20px 24px;
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                color: white;
            }

            .selector-title {
                display: flex;
                align-items: center;
                gap: 10px;
                font-size: 1.125rem;
                font-weight: 600;
                margin: 0 0 8px 0;
            }

            .title-icon {
                width: 24px;
                height: 24px;
            }

            .selector-subtitle {
                font-size: 0.875rem;
                opacity: 0.9;
                margin: 0;
            }

            .models-grid {
                padding: 20px;
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                gap: 16px;
            }

            .model-card {
                display: flex;
                flex-direction: column;
                align-items: flex-start;
                gap: 12px;
                padding: 16px;
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
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            }

            .model-card.selected {
                background: #ecfdf5;
                border-color: #10b981;
                box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
            }

            .model-header {
                display: flex;
                align-items: center;
                gap: 12px;
                width: 100%;
            }

            .model-check {
                width: 24px;
                height: 24px;
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
                background: #10b981;
                border-color: #10b981;
            }

            .model-check svg {
                width: 16px;
                height: 16px;
                stroke: white;
            }

            .model-name {
                font-size: 0.9375rem;
                font-weight: 600;
                color: #111827;
                margin: 0;
                flex: 1;
            }

            .model-description {
                font-size: 0.8125rem;
                color: #6b7280;
                margin: 0;
                line-height: 1.4;
            }

            /* Responsive */
            @media (max-width: 768px) {
                .models-grid {
                    grid-template-columns: 1fr;
                }
            }

            @media (min-width: 769px) and (max-width: 1024px) {
                .models-grid {
                    grid-template-columns: repeat(2, 1fr);
                }
            }
        `;
    }

    setupEventListeners() {
        const cards = this.shadowRoot.querySelectorAll('.model-card');
        cards.forEach(card => {
            card.addEventListener('click', () => {
                const modelId = card.dataset.modelId;
                this.selectModel(modelId);
            });
        });
    }

    selectModel(modelId) {
        this.selectedModelId = modelId;
        this.saveSelectedModel();
        this.render();
        this.setupEventListeners();
        
        // Dispatch custom event
        this.dispatchEvent(new CustomEvent('model-selected', {
            detail: {
                modelId: modelId,
                model: this.availableModels.find(m => m.id === modelId)
            }
        }));
    }

    getSelectedModel() {
        return {
            modelId: this.selectedModelId,
            model: this.availableModels.find(m => m.id === this.selectedModelId)
        };
    }

    loadSelectedModel() {
        try {
            const saved = localStorage.getItem(this.STORAGE_KEY);
            if (saved) {
                this.selectedModelId = saved;
            }
        } catch (error) {
            console.error('Error loading selected model:', error);
        }
    }

    saveSelectedModel() {
        try {
            if (this.selectedModelId) {
                localStorage.setItem(this.STORAGE_KEY, this.selectedModelId);
            }
        } catch (error) {
            console.error('Error saving selected model:', error);
        }
    }
}

// Register the custom element
customElements.define('model-selector', ModelSelector);
