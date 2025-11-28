// ===== RECEIPT EXTRACTOR - DESKTOP APP RENDERER =====
// Combined Web App + Desktop App Functionality

const DEBUG = false;
const log = {
    info: (...args) => DEBUG && console.log('[INFO]', ...args),
    error: (...args) => console.error('[ERROR]', ...args),
    warn: (...args) => DEBUG && console.warn('[WARN]', ...args)
};

// ===== GLOBAL STATE =====
let selectedImagePath = null;
let extractionResults = null;
let selectedModel = null;
let availableModels = [];
let batchFiles = [];
let finetuneFiles = [];
let currentJobId = null;
let currentTab = 'extract';
let sessionStats = {
    total: 0,
    successful: 0
};

// ===== INITIALIZATION =====
document.addEventListener('DOMContentLoaded', () => {
    log.info('App initialized');

    if (!window.electronAPI) {
        log.error('electronAPI not available!');
        showError('Application Error', 'Unable to connect to application backend. Please restart the app.');
        return;
    }

    loadSettings();
    setupEventListeners();
    setupTabNavigation();
    setupBatchProcessing();
    setupFinetuning();
    setupThemeToggle();
    setupHistoryPanel();
    loadModels();
    updateSessionStats();

    log.info('All systems ready');
    announce('Receipt Extractor ready. Press Ctrl+O to select an image.', 'polite');
});

// ===== TAB NAVIGATION =====
function setupTabNavigation() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.dataset.tab;
            switchTab(tabName);
        });
    });
}

function switchTab(tabName) {
    currentTab = tabName;

    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));

    const activeBtn = document.querySelector(`.tab-btn[data-tab="${tabName}"]`);
    const activeContent = document.getElementById(`${tabName}Tab`);

    if (activeBtn) activeBtn.classList.add('active');
    if (activeContent) activeContent.classList.add('active');

    // Update sidebar content based on tab
    updateSidebarContent(tabName);

    announce(`Switched to ${tabName} tab`, 'polite');
}

function updateSidebarContent(tabName) {
    const sidebarContent = document.getElementById('sidebarContent');
    if (!sidebarContent) return;

    if (tabName === 'extract') {
        sidebarContent.innerHTML = `
            <section class="section">
                <h2 class="section-title">Input</h2>
                <button id="selectImageBtn" class="btn btn-primary">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                        <polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
                    </svg>
                    Select Image
                </button>
                <div id="imagePreview" class="hidden" style="margin-top: var(--space-3);">
                    <p id="imagePath" class="file-name" style="font-size: 0.75rem; color: var(--text-secondary); word-break: break-all;"></p>
                    <p id="fileSize" class="file-size" style="font-size: 0.75rem; color: var(--text-secondary); margin-top: var(--space-1);"></p>
                </div>
            </section>
            <section class="section">
                <h2 class="section-title">Engine</h2>
                <div class="engine-selector" id="engineSelector">
                    <!-- Model cards will be populated here -->
                </div>
            </section>
            <section class="section">
                <button id="extractBtn" class="btn btn-success btn-large" disabled>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polygon points="5 3 19 12 5 21 5 3"/>
                    </svg>
                    Execute
                </button>
            </section>
        `;

        // Re-attach event listeners
        document.getElementById('selectImageBtn').addEventListener('click', handleSelectImage);
        document.getElementById('extractBtn').addEventListener('click', handleExtract);
        renderModelSelector();

    } else if (tabName === 'batch') {
        sidebarContent.innerHTML = `
            <section class="section">
                <h2 class="section-title">Model Selection</h2>
                <select id="batchModelSelect" class="select-input" style="width: 100%;">
                    <option value="">Loading models...</option>
                </select>
            </section>
        `;
        populateBatchModelDropdown();

    } else if (tabName === 'finetune') {
        sidebarContent.innerHTML = `
            <section class="section">
                <h2 class="section-title">Quick Actions</h2>
                <p style="font-size: 0.875rem; color: var(--text-secondary); margin-bottom: var(--space-2);">
                    Configure and manage model training in the main panel
                </p>
            </section>
        `;
    }
}

// ===== MODEL MANAGEMENT =====
async function loadModels() {
    try {
        const result = await window.electronAPI.getModels();
        if (result && result.success) {
            availableModels = result.models;
            selectedModel = result.default_model;
            renderModelSelector();
            populateBatchModelDropdown();
            populateFinetuneModelDropdown();
        }
    } catch (error) {
        log.error('Error loading models:', error);
    }
}

function renderModelSelector() {
    const selector = document.getElementById('engineSelector');
    if (!selector) return;

    if (!availableModels || availableModels.length === 0) {
        selector.innerHTML = '<p style="color: var(--text-secondary);">Loading models...</p>';
        return;
    }

    selector.innerHTML = '';
    availableModels.forEach(model => {
        const isSelected = model.id === selectedModel;
        const card = document.createElement('label');
        card.className = 'engine-option';
        card.innerHTML = `
            <input type="radio" name="engine" value="${model.id}" ${isSelected ? 'checked' : ''}>
            <div class="engine-card">
                <div class="engine-icon">${getModelIcon(model.type)}</div>
                <div class="engine-info">
                    <span class="engine-name">${model.name}</span>
                    <span class="engine-desc">${model.type.toUpperCase()}</span>
                </div>
                <div class="engine-badge">${model.type === 'donut' ? 'AI' : model.type === 'florence' ? 'Best' : 'Fast'}</div>
            </div>
        `;

        const radio = card.querySelector('input');
        radio.addEventListener('change', () => {
            selectedModel = model.id;
            saveSettings();
            announce(`Selected ${model.name} engine`, 'polite');
        });

        selector.appendChild(card);
    });
}

function getModelIcon(type) {
    const icons = {
        'donut': '🍩',
        'florence': '🔬',
        'ocr': '⚡',
        'easyocr': '⚡',
        'paddle': '🎯'
    };
    return icons[type] || '📄';
}

function populateBatchModelDropdown() {
    const select = document.getElementById('batchModelSelect');
    if (!select || !availableModels) return;

    select.innerHTML = '<option value="">Select a model</option>';
    availableModels.forEach(model => {
        const option = document.createElement('option');
        option.value = model.id;
        option.textContent = `${model.name} (${model.type})`;
        if (model.id === selectedModel) {
            option.selected = true;
        }
        select.appendChild(option);
    });
}

function populateFinetuneModelDropdown() {
    const select = document.getElementById('finetuneModelSelect');
    if (!select || !availableModels) return;

    select.innerHTML = '<option value="">Select a model</option>';
    const finetuneableModels = availableModels.filter(m =>
        ['donut', 'florence', 'easyocr', 'paddle'].includes(m.type)
    );

    finetuneableModels.forEach(model => {
        const option = document.createElement('option');
        option.value = model.id;
        option.textContent = `${model.name} (${model.type})`;
        select.appendChild(option);
    });
}

// ===== EVENT LISTENERS =====
function setupEventListeners() {
    // Upload area drag & drop
    const uploadArea = document.getElementById('uploadArea');
    if (uploadArea) {
        uploadArea.addEventListener('click', handleSelectImage);
        uploadArea.addEventListener('dragover', handleDragOver);
        uploadArea.addEventListener('dragleave', handleDragLeave);
        uploadArea.addEventListener('drop', handleDrop);
    }

    // Export dropdown
    const exportDropdown = document.getElementById('exportDropdown');
    const exportMenu = document.getElementById('exportMenu');
    if (exportDropdown && exportMenu) {
        exportDropdown.addEventListener('click', (e) => {
            e.stopPropagation();
            exportMenu.classList.toggle('hidden');
        });

        document.addEventListener('click', () => {
            exportMenu.classList.add('hidden');
        });

        document.querySelectorAll('.dropdown-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const format = e.currentTarget.dataset.format;
                handleExport(format);
            });
        });
    }

    // Toggle JSON
    const toggleJsonBtn = document.getElementById('toggleJsonBtn');
    if (toggleJsonBtn) {
        toggleJsonBtn.addEventListener('click', handleToggleJson);
    }

    // Keyboard shortcuts
    setupKeyboardShortcuts();
}

function setupKeyboardShortcuts() {
    const keyboardShortcuts = {
        'Control+o': () => handleSelectImage(),
        'Meta+o': () => handleSelectImage(),
        'Control+e': () => {
            const btn = document.getElementById('extractBtn');
            if (btn && !btn.disabled) handleExtract();
        },
        'Meta+e': () => {
            const btn = document.getElementById('extractBtn');
            if (btn && !btn.disabled) handleExtract();
        },
        'Control+1': () => switchTab('extract'),
        'Control+2': () => switchTab('batch'),
        'Control+3': () => switchTab('finetune')
    };

    document.addEventListener('keydown', (e) => {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT' || e.target.tagName === 'TEXTAREA') {
            return;
        }

        const key = `${e.ctrlKey ? 'Control+' : ''}${e.metaKey ? 'Meta+' : ''}${e.key.toLowerCase()}`;
        const handler = keyboardShortcuts[key];

        if (handler) {
            e.preventDefault();
            handler();
        }
    });
}

// ===== IMAGE SELECTION =====
async function handleSelectImage() {
    log.info('Select image clicked');
    try {
        const result = await window.electronAPI.selectImage();
        log.info('Got result:', result);

        if (result && result.success && result.path) {
            selectedImagePath = result.path;
            log.info('Image selected:', selectedImagePath);

            const imagePreview = document.getElementById('imagePreview');
            const imagePath = document.getElementById('imagePath');
            const fileSize = document.getElementById('fileSize');
            const extractBtn = document.getElementById('extractBtn');

            if (imagePreview) imagePreview.classList.remove('hidden');
            if (imagePath) imagePath.textContent = result.name || result.path.split(/[\\\/]/).pop();
            if (fileSize && result.size) {
                const sizeMB = (result.size / (1024 * 1024)).toFixed(2);
                fileSize.textContent = `${sizeMB} MB`;
            }
            if (extractBtn) extractBtn.disabled = false;

            announce(`Image selected: ${result.name}`, 'polite');
            log.info('Image preview updated');
        } else {
            log.info('Selection cancelled or failed');
        }
    } catch (error) {
        log.error('Error selecting image:', error);
        showError('Selection Error', error.message);
        announce('Error selecting image', 'assertive');
    }
}

function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    e.currentTarget.classList.add('drag-over');
}

function handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    e.currentTarget.classList.remove('drag-over');
}

async function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    e.currentTarget.classList.remove('drag-over');

    const files = e.dataTransfer.files;
    if (files.length === 0) return;

    const file = files[0];
    const filePath = file.path;
    const validExtensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'];
    const ext = filePath.toLowerCase().substring(filePath.lastIndexOf('.'));

    if (!validExtensions.includes(ext)) {
        showError('Invalid File Type', 'Please drop a valid image file (JPG, PNG, BMP, TIFF)');
        announce('Invalid file type', 'assertive');
        return;
    }

    selectedImagePath = filePath;
    const imagePreview = document.getElementById('imagePreview');
    const imagePath = document.getElementById('imagePath');
    const fileSize = document.getElementById('fileSize');
    const extractBtn = document.getElementById('extractBtn');

    if (imagePreview) imagePreview.classList.remove('hidden');
    if (imagePath) imagePath.textContent = file.name;
    if (fileSize && file.size) {
        const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
        fileSize.textContent = `${sizeMB} MB`;
    }
    if (extractBtn) extractBtn.disabled = false;

    announce(`Image dropped: ${file.name}`, 'polite');
}

// ===== EXTRACTION =====
async function handleExtract() {
    if (!selectedImagePath) {
        log.warn('No image selected');
        return;
    }

    if (!selectedModel) {
        showError('No Model Selected', 'Please select an extraction model');
        return;
    }

    log.info('Starting extraction with:', selectedModel);

    const extractBtn = document.getElementById('extractBtn');
    const progressSection = document.getElementById('progressSection');
    const resultsSection = document.getElementById('resultsSection');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const engineBadgeText = document.getElementById('engineBadgeText');

    if (extractBtn) {
        extractBtn.disabled = true;
        extractBtn.textContent = 'Processing...';
    }

    if (progressSection) progressSection.classList.remove('hidden');
    if (resultsSection) resultsSection.classList.add('hidden');
    if (progressBar) progressBar.style.width = '0%';
    if (progressText) progressText.textContent = 'Initializing...';
    if (engineBadgeText) {
        const modelName = availableModels.find(m => m.id === selectedModel)?.name || selectedModel;
        engineBadgeText.textContent = modelName;
    }

    announce(`Starting extraction with ${selectedModel} engine`, 'polite');

    const startTime = Date.now();

    // Simulate progress
    let progress = 0;
    const progressInterval = setInterval(() => {
        progress += Math.random() * 10;
        if (progress > 90) progress = 90;
        if (progressBar) progressBar.style.width = `${progress}%`;
    }, 200);

    try {
        const result = await window.electronAPI.extractReceipt({
            imagePath: selectedImagePath,
            model: selectedModel
        });

        clearInterval(progressInterval);
        if (progressBar) progressBar.style.width = '100%';

        const duration = ((Date.now() - startTime) / 1000).toFixed(1);
        log.info('Extraction completed in', duration, 's');
        log.info('Result:', result);

        if (result && result.success) {
            extractionResults = result.data;
            sessionStats.total++;
            sessionStats.successful++;
            updateSessionStats();

            if (progressSection) progressSection.classList.add('hidden');
            displayResults(result.data, duration, selectedModel);

            announce(`Extraction completed successfully in ${duration} seconds`, 'polite');
        } else {
            sessionStats.total++;
            updateSessionStats();
            log.error('Extraction failed:', result?.error);
            showError('Extraction Failed', result?.error || 'Unknown error occurred');
            announce('Extraction failed', 'assertive');
        }
    } catch (error) {
        clearInterval(progressInterval);
        sessionStats.total++;
        updateSessionStats();
        log.error('Extraction exception:', error);
        showError('Extraction Failed', error.message);
        announce('Extraction failed after multiple attempts', 'assertive');
    } finally {
        if (extractBtn) {
            extractBtn.disabled = false;
            extractBtn.textContent = 'Execute';
        }
    }
}

// ===== RESULTS DISPLAY =====
function displayResults(data, duration, engine) {
    log.info('Displaying results');

    const resultsSection = document.getElementById('resultsSection');
    if (resultsSection) resultsSection.classList.remove('hidden');

    const receipt = data.receipt || data;

    // Update store info
    const storeName = document.getElementById('storeName');
    const storeAddress = document.getElementById('storeAddress');
    const storePhone = document.getElementById('storePhone');
    const transactionDate = document.getElementById('transactionDate');

    if (storeName) storeName.textContent = receipt.store?.name || 'Unknown Store';
    if (storeAddress) storeAddress.textContent = receipt.store?.address || '';
    if (storePhone) storePhone.textContent = receipt.store?.phone || '';
    if (transactionDate) {
        const date = receipt.date || receipt.transaction_date || '';
        const time = receipt.time || receipt.transaction_time || '';
        transactionDate.textContent = `${date} ${time}`.trim();
    }

    // Update meta badges
    const confidenceBadge = document.getElementById('confidenceBadge');
    const processingTime = document.getElementById('processingTime');

    if (confidenceBadge) {
        const confidence = receipt.confidence || 'N/A';
        confidenceBadge.textContent = `Confidence: ${confidence}`;
    }
    if (processingTime) {
        processingTime.textContent = `Time: ${duration}s`;
    }

    // Display items
    displayItems(receipt.items || []);

    // Display totals
    const subtotalValue = document.getElementById('subtotalValue');
    const taxValue = document.getElementById('taxValue');
    const totalValue = document.getElementById('totalValue');

    if (subtotalValue) {
        const subtotal = receipt.totals?.subtotal || receipt.subtotal || '0.00';
        subtotalValue.textContent = `$${subtotal}`;
    }
    if (taxValue) {
        const tax = receipt.totals?.tax || receipt.tax || '0.00';
        taxValue.textContent = `$${tax}`;
    }
    if (totalValue) {
        const total = receipt.totals?.total || receipt.total || '0.00';
        totalValue.textContent = `$${total}`;
    }

    // Display validation
    displayValidation(receipt, duration);

    // Update JSON display
    const jsonOutput = document.getElementById('jsonOutput');
    if (jsonOutput) {
        jsonOutput.innerHTML = syntaxHighlight(JSON.stringify(data, null, 2));
    }

    log.info('Results displayed');
}

function displayItems(items) {
    const tbody = document.getElementById('itemsTableBody');
    if (!tbody) return;

    tbody.innerHTML = '';

    if (!items || items.length === 0) {
        const row = document.createElement('tr');
        const cell = document.createElement('td');
        cell.setAttribute('colspan', '3');
        cell.style.textAlign = 'center';
        cell.style.color = 'var(--text-secondary)';
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
        qtyCell.style.textAlign = 'center';
        qtyCell.textContent = item.quantity || 1;
        row.appendChild(qtyCell);

        const priceCell = document.createElement('td');
        priceCell.className = 'item-price';
        priceCell.style.textAlign = 'right';
        const price = item.total_price || item.price || '0.00';
        priceCell.textContent = `$${price}`;
        row.appendChild(priceCell);

        tbody.appendChild(row);
    });
}

function displayValidation(receipt, duration) {
    const validationStatus = document.getElementById('validationStatus');
    const validationList = document.getElementById('validationList');

    if (!validationList) return;

    validationList.innerHTML = '';

    const checks = [];

    if (receipt.store?.name) {
        checks.push({ passed: true, text: `Store: ${receipt.store.name}` });
    } else {
        checks.push({ passed: false, text: 'Store not detected' });
    }

    const itemCount = receipt.items?.length || 0;
    if (itemCount > 0) {
        checks.push({ passed: true, text: `${itemCount} items found` });
    } else {
        checks.push({ passed: false, text: 'No items found' });
    }

    if (receipt.totals?.total || receipt.total) {
        const total = receipt.totals?.total || receipt.total;
        checks.push({ passed: true, text: `Total: $${total}` });
    } else {
        checks.push({ passed: false, text: 'Total not found' });
    }

    checks.push({ passed: true, text: `Completed in ${duration}s` });

    checks.forEach(check => {
        const li = document.createElement('li');
        li.textContent = `${check.passed ? '✓' : '✗'} ${check.text}`;
        li.style.color = check.passed ? 'var(--electric-green)' : '#ff4757';
        validationList.appendChild(li);
    });

    if (validationStatus) validationStatus.classList.remove('hidden');
}

function syntaxHighlight(json) {
    if (typeof json !== 'string') {
        json = JSON.stringify(json, null, 2);
    }

    json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

    return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, function (match) {
        let cls = 'json-number';
        if (/^"/.test(match)) {
            if (/:$/.test(match)) {
                cls = 'json-key';
            } else {
                cls = 'json-string';
            }
        } else if (/true|false/.test(match)) {
            cls = 'json-boolean';
        } else if (/null/.test(match)) {
            cls = 'json-null';
        }
        return '<span class="' + cls + '">' + match + '</span>';
    });
}

// ===== EXPORT FUNCTIONALITY =====
function handleToggleJson() {
    const jsonSection = document.getElementById('jsonSection');
    const toggleJsonBtn = document.getElementById('toggleJsonBtn');

    if (!jsonSection) return;

    const isHidden = jsonSection.classList.contains('hidden');

    if (isHidden) {
        jsonSection.classList.remove('hidden');
        if (toggleJsonBtn) toggleJsonBtn.textContent = 'Hide JSON';
        announce('JSON view shown', 'polite');
    } else {
        jsonSection.classList.add('hidden');
        if (toggleJsonBtn) toggleJsonBtn.textContent = 'JSON';
        announce('JSON view hidden', 'polite');
    }
}

async function handleExport(format) {
    if (!extractionResults) {
        showError('No Data', 'No extraction data to export');
        return;
    }

    try {
        const result = await window.electronAPI.saveResults({
            data: extractionResults,
            format: format,
            defaultPath: `receipt_${Date.now()}.${format}`
        });

        if (result && result.success) {
            announce(`Results exported as ${format.toUpperCase()}`, 'polite');
        } else {
            showError('Export Failed', 'Could not export file');
            announce('Export failed', 'assertive');
        }
    } catch (error) {
        log.error('Export error:', error);
        showError('Export Failed', error.message);
        announce('Export failed', 'assertive');
    }
}



// ===== BATCH PROCESSING =====
function setupBatchProcessing() {
    const batchUploadArea = document.getElementById('batchUploadArea');
    const processBatchBtn = document.getElementById('processBatchBtn');
    const clearBatchBtn = document.getElementById('clearBatchBtn');
    const sourceBtns = document.querySelectorAll('.source-btn');
    const cloudBtns = document.querySelectorAll('.cloud-btn');
    const useAllModels = document.getElementById('useAllModels');

    if (batchUploadArea) {
        batchUploadArea.addEventListener('click', handleBatchSelect);
        batchUploadArea.addEventListener('dragover', handleDragOver);
        batchUploadArea.addEventListener('dragleave', handleDragLeave);
        batchUploadArea.addEventListener('drop', handleBatchDrop);
    }

    if (processBatchBtn) {
        processBatchBtn.addEventListener('click', processBatchImages);
    }

    if (clearBatchBtn) {
        clearBatchBtn.addEventListener('click', () => {
            batchFiles = [];
            const fileList = document.getElementById('batchFileList');
            if (fileList) fileList.classList.add('hidden');
            if (processBatchBtn) processBatchBtn.disabled = true;
            announce('Batch selection cleared', 'polite');
        });
    }

    sourceBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const source = btn.dataset.source;
            document.querySelectorAll('.source-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.source-content').forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById('localSource').classList.remove('active');
            document.getElementById('cloudSource').classList.remove('active');
            document.getElementById(source + 'Source').classList.add('active');
        });
    });

    cloudBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const provider = btn.dataset.provider;
            showError('Cloud Storage', 'Cloud storage integration is not yet implemented in the desktop app.');
        });
    });

    if (useAllModels) {
        useAllModels.addEventListener('change', (e) => {
            const batchModelSelect = document.getElementById('batchModelSelect');
            if (batchModelSelect) {
                batchModelSelect.disabled = e.target.checked;
            }
        });
    }
}

async function handleBatchSelect() {
    try {
        const result = await window.electronAPI.selectImages();
        if (result && !result.canceled && result.files) {
            batchFiles = result.files;
            displayBatchFiles();
            const processBatchBtn = document.getElementById('processBatchBtn');
            if (processBatchBtn) processBatchBtn.disabled = false;
            announce('Images selected for batch processing', 'polite');
        }
    } catch (error) {
        log.error('Error selecting batch images:', error);
        showError('Selection Error', error.message);
    }
}

function handleBatchDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    e.currentTarget.classList.remove('drag-over');

    const files = Array.from(e.dataTransfer.files);
    const validExtensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'];

    batchFiles = files.filter(file => {
        const ext = file.path.toLowerCase().substring(file.path.lastIndexOf('.'));
        return validExtensions.includes(ext);
    }).map(file => ({
        path: file.path,
        name: file.name,
        size: file.size
    }));

    if (batchFiles.length > 0) {
        displayBatchFiles();
        const processBatchBtn = document.getElementById('processBatchBtn');
        if (processBatchBtn) processBatchBtn.disabled = false;
        announce('Images added for batch processing', 'polite');
    } else {
        showError('Invalid Files', 'No valid image files found in selection');
    }
}

function displayBatchFiles() {
    const fileList = document.getElementById('batchFileList');
    if (!fileList) return;

    fileList.innerHTML = '';
    fileList.classList.remove('hidden');

    batchFiles.forEach(file => {
        const item = document.createElement('div');
        item.className = 'file-item';
        const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
        item.innerHTML = '<span>' + file.name + '</span><span>' + sizeMB + ' MB</span>';
        fileList.appendChild(item);
    });
}

async function processBatchImages() {
    if (batchFiles.length === 0) {
        showError('No Files', 'No files selected for batch processing');
        return;
    }

    const useAllModelsChecked = document.getElementById('useAllModels');
    const batchModelSelect = document.getElementById('batchModelSelect');
    const selectedBatchModel = batchModelSelect ? batchModelSelect.value : null;

    if (!useAllModelsChecked.checked && !selectedBatchModel) {
        showError('No Model Selected', 'Please select a model');
        return;
    }

    const batchProgress = document.getElementById('batchProgress');
    const batchProgressBar = document.getElementById('batchProgressBar');
    const batchProgressText = document.getElementById('batchProgressText');
    const batchResults = document.getElementById('batchResults');
    const processBatchBtn = document.getElementById('processBatchBtn');

    if (batchProgress) batchProgress.classList.remove('hidden');
    if (batchResults) {
        batchResults.classList.add('hidden');
        batchResults.innerHTML = '';
    }
    if (processBatchBtn) processBatchBtn.disabled = true;

    const results = [];
    let processed = 0;

    for (const file of batchFiles) {
        processed++;
        if (batchProgressBar) {
            const percent = (processed / batchFiles.length) * 100;
            batchProgressBar.style.width = percent + '%';
        }
        if (batchProgressText) {
            batchProgressText.textContent = 'Processing: ' + processed + '/' + batchFiles.length;
        }

        try {
            const model = useAllModelsChecked.checked ? selectedModel : selectedBatchModel;
            const result = await window.electronAPI.extractReceipt({
                imagePath: file.path,
                model: model
            });

            results.push({
                filename: file.name,
                success: result.success,
                data: result.data,
                error: result.error
            });
        } catch (error) {
            results.push({
                filename: file.name,
                success: false,
                error: error.message
            });
        }
    }

    displayBatchResults(results);
    if (processBatchBtn) processBatchBtn.disabled = false;

    announce('Batch processing complete', 'polite');
}

function displayBatchResults(results) {
    const batchResults = document.getElementById('batchResults');
    const batchProgress = document.getElementById('batchProgress');

    if (batchProgress) batchProgress.classList.add('hidden');
    if (!batchResults) return;

    batchResults.classList.remove('hidden');
    batchResults.innerHTML = '<h3>Batch Results</h3>';

    results.forEach(result => {
        const item = document.createElement('div');
        item.className = 'result-item ' + (result.success ? 'success' : 'error');

        if (result.success && result.data) {
            const receipt = result.data.receipt || result.data;
            const storeName = receipt.store ? receipt.store.name : '-';
            const total = (receipt.totals && receipt.totals.total) ? receipt.totals.total : (receipt.total || '-');
            const itemCount = receipt.items ? receipt.items.length : 0;

            item.innerHTML = '<h4>' + result.filename + '</h4>' +
                '<p><strong>Store:</strong> ' + storeName + '</p>' +
                '<p><strong>Total:</strong> $' + total + '</p>' +
                '<p><strong>Items:</strong> ' + itemCount + '</p>';
        } else {
            item.innerHTML = '<h4>' + result.filename + '</h4>' +
                '<p style="color: #ff4757;">Error: ' + (result.error || 'Processing failed') + '</p>';
        }

        batchResults.appendChild(item);
    });
}

// ===== FINETUNING =====
function setupFinetuning() {
    const ftModeRadios = document.querySelectorAll('input[name="ftMode"]');
    const ftUploadArea = document.getElementById('ftUploadArea');
    const startFinetuneBtn = document.getElementById('startFinetuneBtn');
    const viewJobsBtn = document.getElementById('viewJobsBtn');
    const exportModelBtn = document.getElementById('exportModelBtn');
    const modalClose = document.querySelector('.modal-close');

    ftModeRadios.forEach(radio => {
        radio.addEventListener('change', (e) => {
            const mode = e.target.value;
            document.querySelectorAll('.ft-config').forEach(c => c.classList.remove('active'));
            const config = document.getElementById(mode + 'FtConfig');
            if (config) config.classList.add('active');
        });
    });

    if (ftUploadArea) {
        ftUploadArea.addEventListener('click', handleFinetuneSelect);
    }

    if (startFinetuneBtn) {
        startFinetuneBtn.addEventListener('click', () => {
            showError('Finetuning Not Available', 'Model finetuning requires the Flask backend server. Please use the web app for this feature.');
        });
    }

    if (viewJobsBtn) {
        viewJobsBtn.addEventListener('click', () => {
            showError('Training Jobs', 'Please use the web app to view training jobs.');
        });
    }

    if (exportModelBtn) {
        exportModelBtn.addEventListener('click', () => {
            showError('Export Model', 'Please use the web app to export models.');
        });
    }

    if (modalClose) {
        modalClose.addEventListener('click', () => {
            const modal = document.getElementById('jobsModal');
            if (modal) modal.classList.add('hidden');
        });
    }
}

async function handleFinetuneSelect() {
    try {
        const result = await window.electronAPI.selectImages();
        if (result && !result.canceled && result.files) {
            finetuneFiles = result.files;
            displayFinetuneFiles();
            const startFinetuneBtn = document.getElementById('startFinetuneBtn');
            if (startFinetuneBtn) startFinetuneBtn.disabled = false;
            announce('Training images selected', 'polite');
        }
    } catch (error) {
        log.error('Error selecting finetune images:', error);
        showError('Selection Error', error.message);
    }
}

function displayFinetuneFiles() {
    const fileList = document.getElementById('ftFileList');
    if (!fileList) return;

    fileList.innerHTML = '';
    fileList.classList.remove('hidden');

    finetuneFiles.forEach(file => {
        const item = document.createElement('div');
        item.className = 'file-item';
        const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
        item.innerHTML = '<span>' + file.name + '</span><span>' + sizeMB + ' MB</span>';
        fileList.appendChild(item);
    });
}

// ===== THEME TOGGLE =====
function setupThemeToggle() {
    const themeToggle = document.getElementById('themeToggle');
    if (!themeToggle) return;

    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.body.setAttribute('data-theme', savedTheme);

    themeToggle.addEventListener('click', () => {
        const currentTheme = document.body.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

        document.body.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);

        const sunIcon = themeToggle.querySelector('.sun-icon');
        const moonIcon = themeToggle.querySelector('.moon-icon');

        if (newTheme === 'light') {
            if (sunIcon) sunIcon.classList.add('hidden');
            if (moonIcon) moonIcon.classList.remove('hidden');
        } else {
            if (sunIcon) sunIcon.classList.remove('hidden');
            if (moonIcon) moonIcon.classList.add('hidden');
        }

        announce('Switched to ' + newTheme + ' theme', 'polite');
    });
}

// ===== HISTORY PANEL =====
function setupHistoryPanel() {
    const historyToggle = document.getElementById('historyToggle');
    const historyPanel = document.getElementById('historyPanel');
    const closeHistory = document.getElementById('closeHistory');

    if (historyToggle && historyPanel) {
        historyToggle.addEventListener('click', () => {
            historyPanel.classList.toggle('hidden');
        });
    }

    if (closeHistory && historyPanel) {
        closeHistory.addEventListener('click', () => {
            historyPanel.classList.add('hidden');
        });
    }
}

// ===== UTILITY FUNCTIONS =====
function showError(title, message) {
    log.error('Error:', title, message);
    alert(title + '\n\n' + message);
}

function announce(message, priority) {
    if (!priority) priority = 'polite';
    const announcer = document.getElementById('announcements');
    if (!announcer) return;

    announcer.setAttribute('aria-live', priority);
    announcer.textContent = message;

    setTimeout(() => {
        announcer.textContent = '';
    }, 1000);
}

function updateSessionStats() {
    const sessionCount = document.getElementById('sessionCount');
    const successCount = document.getElementById('successCount');

    if (sessionCount) sessionCount.textContent = sessionStats.total;
    if (successCount) successCount.textContent = sessionStats.successful;
}

async function loadSettings() {
    try {
        const settings = await window.electronAPI.getSettings();
        log.info('Loaded settings:', settings);

        if (settings.lastModel) {
            selectedModel = settings.lastModel;
        }
    } catch (error) {
        log.error('Error loading settings:', error);
    }
}

async function saveSettings() {
    try {
        await window.electronAPI.saveSettings({
            lastModel: selectedModel
        });
    } catch (error) {
        log.error('Error saving settings:', error);
    }
}

// Initialize default tab
setTimeout(() => {
    switchTab('extract');
}, 100);
