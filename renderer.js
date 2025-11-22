// renderer.js - Receipt Extractor with Fixed Models & Buttons

const DEBUG = true; // Enable debug logging
const log = {
    info: (...args) => DEBUG && console.log('[INFO]', ...args),
    error: (...args) => console.error('[ERROR]', ...args),
    warn: (...args) => DEBUG && console.warn('[WARN]', ...args)
};

// Security: Input Sanitization
const sanitize = {
    html: (str) => {
        if (typeof str !== 'string') return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    },
    number: (val) => {
        const num = parseFloat(val);
        return isNaN(num) ? 0 : num;
    },
    path: (path) => {
        if (typeof path !== 'string') return '';
        if (path.includes('..') || path.includes('~')) {
            log.warn('Potentially unsafe path detected:', path);
            return '';
        }
        return path;
    }
};

// State
let selectedImagePath = null;
let extractionResults = null;
let sessionStats = {
    total: 0,
    successful: 0
};

// DOM Elements
const selectImageBtn = document.getElementById('selectImageBtn');
const extractBtn = document.getElementById('extractBtn');
const saveBtn = document.getElementById('saveBtn');
const toggleJsonBtn = document.getElementById('toggleJson');
const imagePreview = document.getElementById('imagePreview');
const previewImg = document.getElementById('previewImg');
const imagePath = document.getElementById('imagePath');
const fileSize = document.getElementById('fileSize');

// Engine elements
const engineTesseract = document.getElementById('engineTesseract');
const engineEasyOCR = document.getElementById('engineEasyOCR');
const enginePaddle = document.getElementById('enginePaddle');
const engineFlorence2 = document.getElementById('engineFlorence2');
const aiSettings = document.getElementById('aiSettings');
const aiMode = document.getElementById('aiMode');

const progressSection = document.getElementById('progressSection');
const progressText = document.getElementById('progressText');
const logDisplay = document.getElementById('logDisplay');
const resultsSection = document.getElementById('resultsSection');
const uploadArea = document.getElementById('uploadArea');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    log.info('App initialized');

    if (!window.electronAPI) {
        log.error('electronAPI not available!');
        showError('Application Error', 'Unable to connect to application backend. Please restart the app.');
        return;
    }

    loadSettings();
    setupEventListeners();
    updateSessionStats();
    checkDependencies();

    log.info('All systems ready');
});

// Setup Event Listeners
function setupEventListeners() {
    log.info('Setting up event listeners...');

    // Engine selection - update when changed
    function updateEngineSelection() {
        const selectedEngine = getSelectedEngine();
        log.info('Engine changed to:', selectedEngine);

        // Show/hide AI settings based on engine
        if (selectedEngine === 'ocr_tesseract') {
            aiSettings.style.display = 'none';
        } else {
            aiSettings.style.display = 'block';
        }

        updateEngineInfo(selectedEngine);
        saveSettings();
    }

    // Add listeners to all engine radio buttons
    if (engineTesseract) engineTesseract.addEventListener('change', updateEngineSelection);
    if (engineEasyOCR) engineEasyOCR.addEventListener('change', updateEngineSelection);
    if (enginePaddle) enginePaddle.addEventListener('change', updateEngineSelection);
    if (engineFlorence2) engineFlorence2.addEventListener('change', updateEngineSelection);

    // Image selection
    if (selectImageBtn) {
        selectImageBtn.addEventListener('click', handleSelectImage);
        log.info('Select image button listener attached');
    } else {
        log.error('Select image button not found!');
    }

    // Extract button
    if (extractBtn) {
        extractBtn.addEventListener('click', handleExtract);
        log.info('Extract button listener attached');
    } else {
        log.error('Extract button not found!');
    }

    // Save button
    if (saveBtn) {
        saveBtn.addEventListener('click', handleSave);
        log.info('Save button listener attached');
    } else {
        log.error('Save button not found!');
    }

    // Toggle JSON button
    if (toggleJsonBtn) {
        toggleJsonBtn.addEventListener('click', handleToggleJson);
        log.info('Toggle JSON button listener attached');
    } else {
        log.error('Toggle JSON button not found!');
    }

    // Upload area drag and drop
    if (uploadArea) {
        uploadArea.addEventListener('click', handleSelectImage);
        uploadArea.addEventListener('dragover', handleDragOver);
        uploadArea.addEventListener('dragleave', handleDragLeave);
        uploadArea.addEventListener('drop', handleDrop);
        log.info('Upload area listeners attached');
    }

    // Progress updates
    if (window.electronAPI.onProgress) {
        window.electronAPI.onProgress((data) => {
            if (logDisplay) {
                logDisplay.textContent += data + '\n';
                logDisplay.scrollTop = logDisplay.scrollHeight;
            }
        });
    }

    // Keyboard Shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT' || e.target.tagName === 'TEXTAREA') {
            return;
        }

        if ((e.ctrlKey || e.metaKey) && e.key === 'o') {
            e.preventDefault();
            handleSelectImage();
        } else if ((e.ctrlKey || e.metaKey) && e.key === 'e' && !extractBtn.disabled) {
            e.preventDefault();
            handleExtract();
        } else if ((e.ctrlKey || e.metaKey) && e.key === 's' && !saveBtn.disabled) {
            e.preventDefault();
            handleSave();
        }
    });

    log.info('All event listeners set up successfully');
}

// Get selected engine
function getSelectedEngine() {
    if (engineTesseract && engineTesseract.checked) return 'ocr_tesseract';
    if (engineEasyOCR && engineEasyOCR.checked) return 'ocr_easyocr';
    if (enginePaddle && enginePaddle.checked) return 'ocr_paddle';
    if (engineFlorence2 && engineFlorence2.checked) return 'florence2';
    return 'ocr_tesseract'; // Default
}

// Drag and drop handlers
function handleDragOver(event) {
    event.preventDefault();
    uploadArea.style.borderColor = 'var(--color-primary)';
    uploadArea.style.backgroundColor = 'rgba(0, 122, 255, 0.05)';
}

function handleDragLeave(event) {
    event.preventDefault();
    uploadArea.style.borderColor = '';
    uploadArea.style.backgroundColor = '';
}

function handleDrop(event) {
    event.preventDefault();
    uploadArea.style.borderColor = '';
    uploadArea.style.backgroundColor = '';

    const files = event.dataTransfer.files;
    if (files.length > 0) {
        const file = files[0];
        if (file.type.startsWith('image/')) {
            // Simulate file selection
            processDroppedFile(file.path);
        } else {
            showError('Invalid File', 'Please drop an image file');
        }
    }
}

function processDroppedFile(filePath) {
    log.info('Processing dropped file:', filePath);
    selectedImagePath = sanitize.path(filePath);

    if (!selectedImagePath) {
        showError('Invalid Path', 'The dropped file path is invalid');
        return;
    }

    imagePreview.classList.remove('hidden');
    previewImg.src = `file://${selectedImagePath}`;

    const fileName = sanitize.html(filePath.split(/[\\\/]/).pop());
    imagePath.textContent = fileName;

    extractBtn.disabled = false;
    log.info('Extract button ENABLED after drop');
}

// Handle Image Selection
async function handleSelectImage() {
    log.info('Select image clicked');

    try {
        const result = await window.electronAPI.selectImage();
        log.info('Got result:', result);

        if (result && result.success && result.path) {
            const validPath = sanitize.path(result.path);
            if (!validPath) {
                throw new Error('Invalid file path');
            }

            selectedImagePath = validPath;
            log.info('Image selected:', selectedImagePath);

            imagePreview.classList.remove('hidden');
            previewImg.src = `file://${validPath}`;

            const fileName = sanitize.html(result.path.split(/[\\\/]/).pop());
            imagePath.textContent = fileName;

            try {
                const stats = await window.electronAPI.getFileStats(validPath);
                if (stats && stats.size) {
                    const sizeMB = (stats.size / (1024 * 1024)).toFixed(2);
                    fileSize.textContent = `${sizeMB} MB`;
                }
            } catch (e) {
                fileSize.textContent = '';
            }

            // CRITICAL: Enable extract button
            extractBtn.disabled = false;
            log.info('Extract button ENABLED');
        } else {
            log.info('Selection cancelled or failed');
        }
    } catch (error) {
        log.error('Error selecting image:', error);
        showError('Selection Error', sanitize.html(error.message));
    }
}

// Handle Extract
async function handleExtract() {
    log.info('Extract button clicked');

    if (!selectedImagePath) {
        log.warn('No image selected');
        showError('No Image', 'Please select an image first');
        return;
    }

    const selectedEngine = getSelectedEngine();
    log.info('Starting extraction with:', selectedEngine);

    // Disable button during processing
    extractBtn.disabled = true;
    extractBtn.textContent = 'Processing...';

    // Show progress
    if (progressText) progressText.textContent = 'Initializing...';
    if (logDisplay) logDisplay.textContent = '';
    if (progressSection) progressSection.classList.remove('hidden');
    if (resultsSection) resultsSection.classList.add('hidden');
    if (uploadArea) uploadArea.classList.add('hidden');

    const startTime = Date.now();

    try {
        const extractionOptions = {
            imagePath: selectedImagePath,
            model: selectedEngine,
            mode: selectedEngine !== 'ocr_tesseract' ? aiMode.value : 'fast'
        };

        log.info('Extraction options:', extractionOptions);

        const result = await window.electronAPI.extractReceipt(extractionOptions);
        const duration = ((Date.now() - startTime) / 1000).toFixed(1);

        log.info('Extraction completed in', duration, 's');
        log.info('Result:', result);

        if (result && result.success) {
            extractionResults = result.data;
            sessionStats.total++;
            sessionStats.successful++;
            updateSessionStats();

            progressSection.classList.add('hidden');
            displayResults(result.data, duration, selectedEngine);
            saveBtn.disabled = false;
        } else {
            sessionStats.total++;
            updateSessionStats();
            log.error('Extraction failed:', result?.error);
            showError('Extraction Failed', sanitize.html(result?.error || 'Unknown error occurred'));
        }
    } catch (error) {
        sessionStats.total++;
        updateSessionStats();
        log.error('Extraction exception:', error);
        showError('Extraction Failed', sanitize.html(error.message));
    } finally {
        extractBtn.disabled = false;
        extractBtn.textContent = 'Execute';
    }
}

// Display Results
function displayResults(data, duration, engine) {
    log.info('Displaying results');

    if (resultsSection) resultsSection.classList.remove('hidden');
    if (uploadArea) uploadArea.classList.add('hidden');

    // Update engine badge
    const engineBadgeText = document.getElementById('engineBadgeText');
    if (engineBadgeText) {
        const badgeNames = {
            'ocr_tesseract': 'TESSERACT',
            'ocr_easyocr': 'EASYOCR',
            'ocr_paddle': 'PADDLE',
            'florence2': 'FLORENCE-2'
        };
        engineBadgeText.textContent = badgeNames[engine] || 'OCR';
    }

    // Parse receipt data
    const receipt = data.receipt || data;

    // Update store info
    const storeName = receipt.store?.name || receipt.store_name || 'Not detected';
    const storeAddress = receipt.store?.address || receipt.store_address || '-';
    const storePhone = receipt.store?.phone || receipt.store_phone || '-';
    const transDate = receipt.date || receipt.transaction_date || '-';

    if (document.getElementById('storeName'))
        document.getElementById('storeName').textContent = storeName;
    if (document.getElementById('storeAddress'))
        document.getElementById('storeAddress').textContent = storeAddress;
    if (document.getElementById('storePhone'))
        document.getElementById('storePhone').textContent = storePhone;
    if (document.getElementById('transactionDate'))
        document.getElementById('transactionDate').textContent = transDate;

    // Update totals
    const total = Number(receipt.total || 0).toFixed(2);
    const subtotal = Number(receipt.subtotal || 0).toFixed(2);
    const tax = Number(receipt.tax || 0).toFixed(2);

    if (document.getElementById('totalValue'))
        document.getElementById('totalValue').textContent = `$${total}`;
    if (document.getElementById('subtotalValue'))
        document.getElementById('subtotalValue').textContent = `$${subtotal}`;
    if (document.getElementById('taxValue'))
        document.getElementById('taxValue').textContent = `$${tax}`;

    // Display items
    displayItems(receipt.items || []);

    // Show JSON
    const jsonOutput = document.getElementById('jsonOutput');
    if (jsonOutput) {
        jsonOutput.textContent = JSON.stringify(data, null, 2);
    }

    log.info('Results displayed successfully');
}

// Display Items
function displayItems(items) {
    const tbody = document.getElementById('itemsTableBody');
    if (!tbody) return;

    tbody.innerHTML = '';

    if (!items || items.length === 0) {
        const row = document.createElement('tr');
        const cell = document.createElement('td');
        cell.setAttribute('colspan', '3');
        cell.className = 'text-center';
        cell.textContent = 'No items extracted';
        row.appendChild(cell);
        tbody.appendChild(row);
        return;
    }

    items.forEach(item => {
        const row = document.createElement('tr');

        const nameCell = document.createElement('td');
        nameCell.textContent = item.name || '-';
        row.appendChild(nameCell);

        const qtyCell = document.createElement('td');
        qtyCell.textContent = Number(item.quantity) || 1;
        row.appendChild(qtyCell);

        const priceCell = document.createElement('td');
        const price = Number(item.total_price || item.price || 0).toFixed(2);
        priceCell.textContent = `$${price}`;
        row.appendChild(priceCell);

        tbody.appendChild(row);
    });
}

// Show Error
function showError(title, details) {
    log.error('Showing error:', title, details);

    if (progressSection) progressSection.classList.add('hidden');
    if (resultsSection) resultsSection.classList.add('hidden');
    if (uploadArea) uploadArea.classList.remove('hidden');

    // Show error message
    alert(`${title}\n\n${details}`);
}

// Handle Save
async function handleSave() {
    if (!extractionResults) return;

    saveBtn.disabled = true;
    const originalText = saveBtn.textContent;
    saveBtn.textContent = 'Saving...';

    try {
        const fileName = selectedImagePath.split(/[\\\/]/).pop().replace(/\.[^/.]+$/, '');
        const engine = getSelectedEngine();

        const result = await window.electronAPI.saveResults({
            data: extractionResults,
            defaultPath: `${fileName}_${engine}_extraction.json`
        });

        if (result && result.success) {
            saveBtn.textContent = '✓ Saved';
            setTimeout(() => {
                saveBtn.textContent = originalText;
                saveBtn.disabled = false;
            }, 2000);
        } else {
            saveBtn.textContent = originalText;
            saveBtn.disabled = false;
            showError('Save Failed', 'Could not save file');
        }
    } catch (error) {
        log.error('Save error:', error);
        saveBtn.textContent = originalText;
        saveBtn.disabled = false;
        showError('Save Failed', sanitize.html(error.message));
    }
}

// Handle Toggle JSON
function handleToggleJson() {
    const jsonSection = document.getElementById('jsonSection');
    if (!jsonSection) return;

    const isHidden = jsonSection.classList.contains('hidden');

    if (isHidden) {
        jsonSection.classList.remove('hidden');
        toggleJsonBtn.textContent = 'Hide JSON';
    } else {
        jsonSection.classList.add('hidden');
        toggleJsonBtn.textContent = 'JSON';
    }
}

// Update Engine Info
function updateEngineInfo(engine) {
    const infoTitle = document.getElementById('engineInfoTitle');
    const infoText = document.getElementById('engineInfoText');

    if (!infoTitle || !infoText) return;

    const engineInfo = {
        'ocr_tesseract': {
            title: 'Tesseract OCR',
            text: 'Fast and reliable Tesseract OCR engine with rule-based parsing. Best for clear, printed receipts. Processing time: 1-2 seconds.'
        },
        'ocr_easyocr': {
            title: 'EasyOCR (RECOMMENDED)',
            text: 'Ready-to-use OCR with 80+ language support. Excellent accuracy with no installation required. Processing time: 2-4 seconds.'
        },
        'ocr_paddle': {
            title: 'PaddleOCR',
            text: 'Enterprise-grade PaddlePaddle OCR. Multilingual support with high accuracy. Production-ready. Processing time: 2-3 seconds.'
        },
        'florence2': {
            title: 'Florence-2 AI',
            text: 'Microsoft Florence-2 advanced AI model with region detection and OCR. Best overall accuracy. Processing time: 3-5 seconds.'
        }
    };

    const info = engineInfo[engine] || engineInfo.ocr_tesseract;
    infoTitle.textContent = info.title;
    infoText.textContent = info.text;
}

// Update Session Stats
function updateSessionStats() {
    const sessionCount = document.getElementById('sessionCount');
    const successCount = document.getElementById('successCount');

    if (sessionCount) sessionCount.textContent = sessionStats.total;
    if (successCount) successCount.textContent = sessionStats.successful;
}

// Load Settings
async function loadSettings() {
    try {
        const settings = await window.electronAPI.getSettings();
        log.info('Loaded settings:', settings);

        const model = settings.lastModel || 'ocr_tesseract';

        // Reset all checkboxes
        if (engineTesseract) engineTesseract.checked = false;
        if (engineEasyOCR) engineEasyOCR.checked = false;
        if (enginePaddle) enginePaddle.checked = false;
        if (engineFlorence2) engineFlorence2.checked = false;

        // Set the saved model
        if (model === 'ocr_tesseract' && engineTesseract) engineTesseract.checked = true;
        else if (model === 'ocr_easyocr' && engineEasyOCR) engineEasyOCR.checked = true;
        else if (model === 'ocr_paddle' && enginePaddle) enginePaddle.checked = true;
        else if (model === 'florence2' && engineFlorence2) engineFlorence2.checked = true;
        else if (engineTesseract) engineTesseract.checked = true; // Default

        // Show/hide AI settings
        if (model === 'ocr_tesseract') {
            aiSettings.style.display = 'none';
        } else {
            aiSettings.style.display = 'block';
        }

        if (settings.aiMode && aiMode) {
            aiMode.value = settings.aiMode;
        }

        updateEngineInfo(model);
    } catch (error) {
        log.error('Error loading settings:', error);
    }
}

// Save Settings
function saveSettings() {
    const selectedModel = getSelectedEngine();
    const settings = {
        lastModel: selectedModel,
        aiMode: aiMode ? aiMode.value : 'fast'
    };
    log.info('Saving settings:', settings);
    window.electronAPI.saveSettings(settings);
}

// Check Dependencies
async function checkDependencies() {
    try {
        const result = await window.electronAPI.checkDependencies();

        if (!result.python || !result.dependencies) {
            log.warn('Dependencies missing:', result.message);
            extractBtn.disabled = true;
            extractBtn.textContent = 'Dependencies Missing';
        } else {
            log.info('All dependencies ready');
        }
    } catch (error) {
        log.error('Error checking dependencies:', error);
    }
}
