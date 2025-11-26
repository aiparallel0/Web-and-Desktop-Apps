/**
 * Receipt Extractor Web App - Frontend Application
 */

// Configuration
const API_BASE_URL = 'http://localhost:5000/api';

// State
let selectedModel = null;
let availableModels = [];
let currentExtractionData = null;

// DOM Elements
const elements = {
    modelSelector: document.getElementById('modelSelector'),
    modelInfo: document.getElementById('modelInfo'),
    uploadArea: document.getElementById('uploadArea'),
    fileInput: document.getElementById('fileInput'),
    imagePreview: document.getElementById('imagePreview'),
    previewImg: document.getElementById('previewImg'),
    extractBtn: document.getElementById('extractBtn'),
    batchExtractBtn: document.getElementById('batchExtractBtn'),
    actionButtons: document.getElementById('actionButtons'),
    resultsSection: document.getElementById('resultsSection'),
    errorSection: document.getElementById('errorSection'),
    loadingOverlay: document.getElementById('loadingOverlay')
};

// Initialize app
async function init() {
    setupEventListeners();
    await loadModels();
}

// Setup event listeners
function setupEventListeners() {
    // File input change
    elements.fileInput.addEventListener('change', handleFileSelect);

    // Drag and drop
    elements.uploadArea.addEventListener('dragover', handleDragOver);
    elements.uploadArea.addEventListener('dragleave', handleDragLeave);
    elements.uploadArea.addEventListener('drop', handleDrop);

    // Extract button
    if (elements.extractBtn) {
        elements.extractBtn.addEventListener('click', handleExtract);
        console.log('Extract button listener attached');
    } else {
        console.error('Extract button not found!');
    }

    // Batch extract button
    if (elements.batchExtractBtn) {
        elements.batchExtractBtn.addEventListener('click', handleBatchExtract);
        console.log('Batch extract button listener attached');
    } else {
        console.error('Batch extract button not found!');
    }

    // Export buttons
    document.getElementById('exportJson').addEventListener('click', () => exportData('json'));
    document.getElementById('exportCsv').addEventListener('click', () => exportData('csv'));
    document.getElementById('exportTxt').addEventListener('click', () => exportData('txt'));
}

// Load available models
async function loadModels() {
    try {
        const response = await fetch(`${API_BASE_URL}/models`);
        const data = await response.json();

        if (data.success) {
            availableModels = data.models;
            selectedModel = data.current_model || data.default_model;
            renderModels();
        } else {
            showError('Failed to load models');
        }
    } catch (error) {
        console.error('Error loading models:', error);
        showError('Failed to connect to API server. Make sure the backend is running.');
    }
}

// Render model cards
function renderModels() {
    if (availableModels.length === 0) {
        elements.modelSelector.innerHTML = '<p class="loading">No models available</p>';
        return;
    }

    elements.modelSelector.innerHTML = '';

    availableModels.forEach(model => {
        const card = document.createElement('div');
        card.className = `model-card ${model.id === selectedModel ? 'selected' : ''}`;
        card.onclick = () => selectModel(model.id);

        const badgeClass = `badge-${model.type}`;

        card.innerHTML = `
            <h4>${model.name}</h4>
            <p>${model.description}</p>
            <span class="model-badge ${badgeClass}">${model.type.toUpperCase()}</span>
            ${model.requires_auth ? '<span class="model-badge" style="background: #fee2e2; color: #991b1b;">Auth Required</span>' : ''}
        `;

        elements.modelSelector.appendChild(card);
    });

    updateModelInfo();
}

// Select a model
async function selectModel(modelId) {
    try {
        const response = await fetch(`${API_BASE_URL}/models/select`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ model_id: modelId })
        });

        const data = await response.json();

        if (data.success) {
            selectedModel = modelId;
            renderModels();
        } else {
            showError(`Failed to select model: ${data.error}`);
        }
    } catch (error) {
        console.error('Error selecting model:', error);
        showError('Failed to select model');
    }
}

// Update model info display
function updateModelInfo() {
    const model = availableModels.find(m => m.id === selectedModel);
    if (model) {
        const capabilities = model.capabilities;
        const capList = Object.entries(capabilities)
            .filter(([_, value]) => value)
            .map(([key]) => key.replace('_', ' '))
            .join(', ');

        elements.modelInfo.innerHTML = `
            <strong>Selected Model:</strong> ${model.name}<br>
            <strong>Capabilities:</strong> ${capList || 'Basic extraction'}
        `;
    }
}

// Handle file selection
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        processFile(file);
    }
}

// Handle drag over
function handleDragOver(event) {
    event.preventDefault();
    elements.uploadArea.classList.add('dragover');
}

// Handle drag leave
function handleDragLeave(event) {
    event.preventDefault();
    elements.uploadArea.classList.remove('dragover');
}

// Handle drop
function handleDrop(event) {
    event.preventDefault();
    elements.uploadArea.classList.remove('dragover');

    const file = event.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
        processFile(file);
    } else {
        showError('Please drop an image file');
    }
}

// Process selected file
function processFile(file) {
    // Validate file size
    const maxSize = 16 * 1024 * 1024; // 16MB
    if (file.size > maxSize) {
        showError('File size exceeds 16MB');
        return;
    }

    // Show preview
    const reader = new FileReader();
    reader.onload = (e) => {
        elements.previewImg.src = e.target.result;
        elements.imagePreview.classList.remove('hidden');
        // Enable buttons once image is loaded
        elements.extractBtn.disabled = false;
        elements.batchExtractBtn.disabled = false;
        console.log('Buttons enabled:', {
            extractBtn: !elements.extractBtn.disabled,
            batchExtractBtn: !elements.batchExtractBtn.disabled
        });
    };
    reader.readAsDataURL(file);

    // Store file for extraction
    elements.fileInput.file = file;
}

// Handle extraction
async function handleExtract() {
    const file = elements.fileInput.files[0];
    if (!file) {
        showError('Please select an image first');
        return;
    }

    if (!selectedModel) {
        showError('Please select a model first');
        return;
    }

    // Show loading
    showLoading(true);
    hideError();
    elements.resultsSection.classList.add('hidden');

    try {
        // Create form data
        const formData = new FormData();
        formData.append('image', file);
        formData.append('model_id', selectedModel);

        // Send request
        const response = await fetch(`${API_BASE_URL}/extract`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success && data.data) {
            currentExtractionData = data.data;
            displayResults(data.data);
        } else {
            const errorMsg = data.error || 'Extraction failed';
            showError(typeof errorMsg === 'object' ? errorMsg.message || 'Extraction failed' : errorMsg);
        }
    } catch (error) {
        console.error('Extraction error:', error);
        showError('Failed to extract receipt data. Please try again.');
    } finally {
        showLoading(false);
    }
}

// Handle batch extraction (all models)
async function handleBatchExtract() {
    console.log('handleBatchExtract called');
    const file = elements.fileInput.files[0];
    if (!file) {
        showError('Please select an image first');
        return;
    }

    console.log('Starting batch extraction with file:', file.name);
    // Show loading
    showLoading(true, 'Processing with ALL models... This may take a few minutes.');
    hideError();
    elements.resultsSection.classList.add('hidden');

    try {
        // Create form data
        const formData = new FormData();
        formData.append('image', file);

        // Send request to batch endpoint
        const response = await fetch(`${API_BASE_URL}/extract/batch`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            // Save batch results and trigger download
            downloadBatchResults(data);
            // Show success message
            showSuccess(`Successfully extracted with ${data.models_count} models! Results downloaded as JSON.`);
        } else {
            showError(data.error || 'Batch extraction failed');
        }
    } catch (error) {
        console.error('Batch extraction error:', error);
        showError('Failed to perform batch extraction. Please try again.');
    } finally {
        showLoading(false);
    }
}

// Download batch results as JSON
function downloadBatchResults(data) {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
    const filename = `batch_extraction_${timestamp}.json`;

    const content = JSON.stringify(data, null, 2);
    const blob = new Blob([content], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
}

// Display extraction results
function displayResults(data) {
    // Store information
    document.getElementById('storeName').textContent = data.store?.name || '-';
    document.getElementById('storeAddress').textContent = data.store?.address || '-';
    document.getElementById('storePhone').textContent = data.store?.phone || '-';

    // Transaction details
    document.getElementById('transDate').textContent = data.date || '-';
    document.getElementById('transTime').textContent = data.time || '-';
    document.getElementById('total').textContent = data.totals?.total ? `$${data.totals.total}` : '-';

    // Processing info
    const processingInfo = document.getElementById('processingInfo');
    processingInfo.innerHTML = `
        <strong>Model:</strong> ${data.model} |
        <strong>Processing Time:</strong> ${data.processing_time?.toFixed(2)}s |
        <strong>Confidence:</strong> ${data.confidence || 'N/A'}
    `;

    // Line items
    const lineItemsContainer = document.getElementById('lineItems');
    const itemCount = document.getElementById('itemCount');

    if (data.items && data.items.length > 0) {
        lineItemsContainer.innerHTML = '';
        data.items.forEach(item => {
            const itemDiv = document.createElement('div');
            itemDiv.className = 'line-item';
            itemDiv.innerHTML = `
                <span class="item-name">${item.name}</span>
                <span class="item-price">$${item.total_price}</span>
            `;
            lineItemsContainer.appendChild(itemDiv);
        });
        itemCount.textContent = data.items.length;
    } else {
        lineItemsContainer.innerHTML = '<p class="no-items">No items extracted</p>';
        itemCount.textContent = '0';
    }

    // Show results
    elements.resultsSection.classList.remove('hidden');
}

// Export data in different formats
function exportData(format) {
    if (!currentExtractionData) {
        showError('No data to export');
        return;
    }

    let content, filename, mimeType;

    switch (format) {
        case 'json':
            content = JSON.stringify(currentExtractionData, null, 2);
            filename = 'receipt_data.json';
            mimeType = 'application/json';
            break;

        case 'csv':
            content = convertToCSV(currentExtractionData);
            filename = 'receipt_data.csv';
            mimeType = 'text/csv';
            break;

        case 'txt':
            content = convertToText(currentExtractionData);
            filename = 'receipt_data.txt';
            mimeType = 'text/plain';
            break;

        default:
            return;
    }

    // Create download
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
}

// Convert data to CSV
function convertToCSV(data) {
    let csv = 'Item,Quantity,Price\n';

    if (data.items && data.items.length > 0) {
        data.items.forEach(item => {
            csv += `"${item.name}",${item.quantity},${item.total_price}\n`;
        });
    }

    csv += '\nStore Information\n';
    csv += `Name,${data.store?.name || ''}\n`;
    csv += `Address,${data.store?.address || ''}\n`;
    csv += `Phone,${data.store?.phone || ''}\n`;

    csv += '\nTransaction\n';
    csv += `Date,${data.date || ''}\n`;
    csv += `Total,${data.totals?.total || ''}\n`;

    return csv;
}

// Convert data to plain text
function convertToText(data) {
    let text = '=== RECEIPT EXTRACTION ===\n\n';

    text += '--- Store Information ---\n';
    text += `Name: ${data.store?.name || '-'}\n`;
    text += `Address: ${data.store?.address || '-'}\n`;
    text += `Phone: ${data.store?.phone || '-'}\n\n`;

    text += '--- Transaction Details ---\n';
    text += `Date: ${data.date || '-'}\n`;
    text += `Total: $${data.totals?.total || '-'}\n\n`;

    if (data.items && data.items.length > 0) {
        text += '--- Line Items ---\n';
        data.items.forEach((item, index) => {
            text += `${index + 1}. ${item.name} - $${item.total_price}\n`;
        });
    }

    text += `\n--- Extraction Info ---\n`;
    text += `Model: ${data.model}\n`;
    text += `Processing Time: ${data.processing_time?.toFixed(2)}s\n`;

    return text;
}

// Show loading overlay
function showLoading(show, message = 'Processing receipt...') {
    if (show) {
        elements.loadingOverlay.classList.remove('hidden');
        const loadingText = elements.loadingOverlay.querySelector('p');
        if (loadingText) {
            loadingText.textContent = message;
        }
    } else {
        elements.loadingOverlay.classList.add('hidden');
    }
}

// Show error
function showError(message) {
    elements.errorSection.classList.remove('hidden');
    document.getElementById('errorMessage').textContent = message;
}

// Show success message
function showSuccess(message) {
    // Temporarily show success in the error section (repurpose it)
    const errorSection = elements.errorSection;
    errorSection.style.backgroundColor = '#d1fae5';
    errorSection.style.borderColor = '#10b981';
    errorSection.classList.remove('hidden');
    document.getElementById('errorMessage').textContent = '✓ ' + message;
    document.getElementById('errorMessage').style.color = '#065f46';

    // Reset after 5 seconds
    setTimeout(() => {
        errorSection.style.backgroundColor = '';
        errorSection.style.borderColor = '';
        document.getElementById('errorMessage').style.color = '';
        hideError();
    }, 5000);
}

// Hide error
function hideError() {
    elements.errorSection.classList.add('hidden');
}

// Start the app
document.addEventListener('DOMContentLoaded', init);
