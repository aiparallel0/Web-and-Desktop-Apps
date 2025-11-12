// renderer.js - Modern Receipt Extractor with Enhanced Security & Accessibility

const DEBUG = false; // Set to true for debug logging

// Debug logging utility
const log = {
    info: (...args) => DEBUG && console.log('[INFO]', ...args),
    error: (...args) => console.error('[ERROR]', ...args),
    warn: (...args) => DEBUG && console.warn('[WARN]', ...args)
};

// Security: Input Sanitization Utilities
const sanitize = {
    // XSS Protection - Sanitize HTML
    html: (str) => {
        if (typeof str !== 'string') return '';
        const div = document.createElement('div');
        div.textContent = str;  // Auto-escapes HTML entities
        return div.innerHTML;
    },

    // Number Validation
    number: (val) => {
        const num = parseFloat(val);
        return isNaN(num) ? 0 : num;
    },

    // Path Validation - Prevent Directory Traversal
    path: (path) => {
        if (typeof path !== 'string') return '';
        if (path.includes('..') || path.includes('~')) {
            log.warn('Potentially unsafe path detected:', path);
            return '';
        }
        return path;
    }
};

// Error Recovery: Retry mechanism with exponential backoff
const retry = async (fn, maxAttempts = 3, delay = 1000) => {
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        try {
            return await fn();
        } catch (error) {
            if (attempt === maxAttempts) throw error;
            const waitTime = delay * attempt; // Exponential backoff
            log.warn(`Attempt ${attempt} failed, retrying in ${waitTime}ms...`);
            announce(`Retrying operation (attempt ${attempt + 1} of ${maxAttempts})`, 'polite');
            await new Promise(resolve => setTimeout(resolve, waitTime));
        }
    }
};

// Accessibility: Screen reader announcements
const announce = (message, priority = 'polite') => {
    const announcer = document.getElementById('announcements');
    if (!announcer) return;

    announcer.setAttribute('aria-live', priority);
    announcer.textContent = message;

    // Clear after 1 second to avoid repeated announcements
    setTimeout(() => {
        announcer.textContent = '';
    }, 1000);
};

let selectedImagePath = null;
let extractionResults = null;
let sessionStats = {
    total: 0,
    successful: 0,
    totalCoverage: 0,
    coverageCount: 0
};

// DOM Elements
const selectImageBtn = document.getElementById('selectImageBtn');
const extractBtn = document.getElementById('extractBtn');
const saveBtn = document.getElementById('saveBtn');
const toggleJsonBtn = document.getElementById('toggleJson');
const removeImageBtn = document.getElementById('removeImage');
const uploadArea = document.getElementById('uploadArea');

const imagePreview = document.getElementById('imagePreview');
const previewImg = document.getElementById('previewImg');
const imagePath = document.getElementById('imagePath');
const fileSize = document.getElementById('fileSize');

const engineOCR = document.getElementById('engineOCR');
const engineFlorence2 = document.getElementById('engineFlorence2');
const engineCORD = document.getElementById('engineCORD');
const engineAdamCodd = document.getElementById('engineAdamCodd');
const aiSettings = document.getElementById('aiSettings');
const aiMode = document.getElementById('aiMode');

const progressSection = document.getElementById('progressSection');
const progressLog = document.getElementById('progressLog');
const resultsDisplay = document.getElementById('resultsDisplay');
const emptyState = document.getElementById('emptyState');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    log.info('App initialized');

    // Check if electronAPI is available
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
    function updateEngineSelection() {
        if (engineOCR.checked) {
            aiSettings.style.display = 'none';
            updateEngineInfo('ocr');
        } else if (engineFlorence2.checked) {
            aiSettings.style.display = 'block';
            updateEngineInfo('florence2');
        } else if (engineCORD.checked) {
            aiSettings.style.display = 'block';
            updateEngineInfo('cord');
        } else if (engineAdamCodd.checked) {
            aiSettings.style.display = 'block';
            updateEngineInfo('adamcodd');
        }
        saveSettings();
    }

    engineOCR.addEventListener('change', updateEngineSelection);
    engineFlorence2.addEventListener('change', updateEngineSelection);
    engineCORD.addEventListener('change', updateEngineSelection);
    engineAdamCodd.addEventListener('change', updateEngineSelection);

    // Mode selector buttons
    const modeButtons = document.querySelectorAll('.mode-btn');
    modeButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            modeButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            aiMode.value = btn.dataset.mode;
            saveSettings();
        });
    });

    // Image selection
    selectImageBtn.addEventListener('click', handleSelectImage);

    // Upload area click (triggers file selection)
    if (uploadArea) {
        uploadArea.addEventListener('click', handleSelectImage);
        uploadArea.style.cursor = 'pointer';

        // Drag & Drop handlers
        uploadArea.addEventListener('dragover', handleDragOver);
        uploadArea.addEventListener('dragleave', handleDragLeave);
        uploadArea.addEventListener('drop', handleDrop);
    }

    // Remove image
    if (removeImageBtn) {
        removeImageBtn.addEventListener('click', handleRemoveImage);
    }

    // Extract
    extractBtn.addEventListener('click', handleExtract);

    // Save
    saveBtn.addEventListener('click', handleSave);

    // Toggle JSON
    toggleJsonBtn.addEventListener('click', handleToggleJson);
    
    // Progress updates
    window.electronAPI.onProgress((data) => {
        if (progressLog) {
            const shouldScroll = progressLog.scrollTop + progressLog.clientHeight >= progressLog.scrollHeight - 10;
            progressLog.textContent += data + '\n';
            if (shouldScroll) {
                progressLog.scrollTop = progressLog.scrollHeight;
            }
        }
    });

    // Keyboard Shortcuts Handler
    const keyboardShortcuts = {
        'Control+o': () => handleSelectImage(),
        'Meta+o': () => handleSelectImage(),
        'Control+e': () => !extractBtn.disabled && handleExtract(),
        'Meta+e': () => !extractBtn.disabled && handleExtract(),
        'Control+s': () => !saveBtn.disabled && handleSave(),
        'Meta+s': () => !saveBtn.disabled && handleSave(),
        'Control+j': () => handleToggleJson(),
        'Meta+j': () => handleToggleJson(),
        'Delete': () => selectedImagePath && handleRemoveImage(),
        '1': () => selectEngine('ocr'),
        '2': () => selectEngine('florence2'),
        '3': () => selectEngine('cord'),
        '4': () => selectEngine('adamcodd')
    };

    // Global keyboard event listener
    document.addEventListener('keydown', (e) => {
        // Don't trigger shortcuts when typing in inputs
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT' || e.target.tagName === 'TEXTAREA') {
            return;
        }

        const key = `${e.ctrlKey ? 'Control+' : ''}${e.metaKey ? 'Meta+' : ''}${e.key.toLowerCase()}`;
        const handler = keyboardShortcuts[key] || keyboardShortcuts[e.key];

        if (handler) {
            e.preventDefault();
            handler();
        }
    });

    // Announce app ready
    announce('Receipt Extractor ready. Press Ctrl+O to select an image.', 'polite');
}

// Helper function to select engine by number key
function selectEngine(engineName) {
    const engines = {
        'ocr': engineOCR,
        'florence2': engineFlorence2,
        'cord': engineCORD,
        'adamcodd': engineAdamCodd
    };

    const engine = engines[engineName];
    if (engine) {
        engine.checked = true;
        engine.dispatchEvent(new Event('change'));
        announce(`Selected ${engineName.toUpperCase()} engine`, 'polite');
    }
}

// Handle Image Selection
async function handleSelectImage() {
    log.info('Select image clicked');

    try {
        log.info('Calling electronAPI.selectImage()...');
        // Apply retry logic for network/IPC failures
        const result = await retry(async () => await window.electronAPI.selectImage());

        log.info('Got result:', result);

        if (result && result.success && result.path) {
            // Security: Validate path before using
            const validPath = sanitize.path(result.path);
            if (!validPath) {
                throw new Error('Invalid file path');
            }
            selectedImagePath = validPath;
            log.info('Image selected:', selectedImagePath);

            // Show preview
            imagePreview.classList.remove('hidden');
            previewImg.src = `file://${sanitize.path(result.path)}`;

            // Display file name (sanitized)
            const fileName = sanitize.html(result.path.split(/[\\\/]/).pop());
            imagePath.textContent = fileName;

            // Get file size (if available)
            try {
                const stats = await window.electronAPI.getFileStats(validPath);
                if (stats && stats.size) {
                    const sizeMB = (stats.size / (1024 * 1024)).toFixed(2);
                    fileSize.textContent = `${sizeMB} MB`;
                }
            } catch (e) {
                fileSize.textContent = '';
            }

            // Enable extract button
            extractBtn.disabled = false;
            document.getElementById('extract-status').textContent = 'Ready to extract';

            // Accessibility: Announce selection
            announce(`Image selected: ${fileName}`, 'polite');

            log.info('Image preview updated');
        } else {
            log.info('Selection cancelled or failed');
        }
    } catch (error) {
        log.error('Error selecting image:', error);
        showError('Selection Error', sanitize.html(error.message));
        announce('Error selecting image', 'assertive');
    }
}

// Handle Remove Image
function handleRemoveImage() {
    selectedImagePath = null;
    imagePreview.classList.add('hidden');
    extractBtn.disabled = true;
    document.getElementById('extract-status').textContent = 'Select an image first to enable extraction';
    previewImg.src = '';
    imagePath.textContent = '';
    fileSize.textContent = '';

    // Accessibility: Announce removal
    announce('Image removed', 'polite');
}

// Handle Drag Over
function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();

    if (uploadArea) {
        uploadArea.style.borderColor = 'var(--color-primary)';
        uploadArea.style.backgroundColor = 'rgba(0, 176, 240, 0.05)';
    }
}

// Handle Drag Leave
function handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();

    if (uploadArea) {
        uploadArea.style.borderColor = '';
        uploadArea.style.backgroundColor = '';
    }
}

// Handle Drop
async function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();

    if (uploadArea) {
        uploadArea.style.borderColor = '';
        uploadArea.style.backgroundColor = '';
    }

    const files = e.dataTransfer.files;
    if (files.length === 0) return;

    const file = files[0];
    const filePath = file.path;

    // Validate file type
    const validExtensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'];
    const ext = filePath.toLowerCase().substring(filePath.lastIndexOf('.'));

    if (!validExtensions.includes(ext)) {
        showError('Invalid File Type', 'Please drop a valid image file (JPG, PNG, BMP, TIFF)');
        announce('Invalid file type', 'assertive');
        return;
    }

    try {
        // Security: Validate path before using
        const validPath = sanitize.path(filePath);
        if (!validPath) {
            throw new Error('Invalid file path');
        }

        selectedImagePath = validPath;
        log.info('Image dropped:', selectedImagePath);

        // Show preview
        imagePreview.classList.remove('hidden');
        previewImg.src = `file://${sanitize.path(filePath)}`;

        // Display file name (sanitized)
        const fileName = sanitize.html(filePath.split(/[\\\/]/).pop());
        imagePath.textContent = fileName;

        // Get file size
        try {
            const stats = await window.electronAPI.getFileStats(validPath);
            if (stats && stats.size) {
                const sizeMB = (stats.size / (1024 * 1024)).toFixed(2);
                fileSize.textContent = `${sizeMB} MB`;
            }
        } catch (e) {
            fileSize.textContent = '';
        }

        // Enable extract button
        extractBtn.disabled = false;

        // Accessibility: Announce selection
        announce(`Image dropped: ${fileName}`, 'polite');

        log.info('Image preview updated via drag & drop');
    } catch (error) {
        log.error('Error handling dropped file:', error);
        showError('Drop Error', sanitize.html(error.message));
        announce('Error handling dropped file', 'assertive');
    }
}

// Handle Extract
async function handleExtract() {
    if (!selectedImagePath) {
        log.warn('No image selected');
        return;
    }
    
    let selectedEngine = 'ocr';
    if (engineFlorence2.checked) selectedEngine = 'florence2';
    else if (engineCORD.checked) selectedEngine = 'cord';
    else if (engineAdamCodd.checked) selectedEngine = 'adamcodd';

    log.info('Starting extraction with:', selectedEngine);

    extractBtn.disabled = true;
    extractBtn.textContent = 'Processing...';

    progressLog.textContent = '';
    progressSection.classList.remove('hidden');
    resultsDisplay.classList.add('hidden');
    emptyState.classList.add('hidden');

    const engineBadgeText = document.getElementById('engineBadgeText');
    if (engineBadgeText) {
        const badgeNames = {
            'ocr': 'OCR',
            'florence2': 'Florence-2',
            'cord': 'CORD',
            'adamcodd': 'AdamCodd'
        };
        engineBadgeText.textContent = badgeNames[selectedEngine] || 'OCR';
    }

    // Accessibility: Announce extraction started
    announce(`Starting extraction with ${selectedEngine} engine`, 'polite');

    const startTime = Date.now();

    try {
        const extractionOptions = {
            imagePath: selectedImagePath,
            model: selectedEngine,
            mode: selectedEngine !== 'ocr' ? aiMode.value : 'fast'
        };

        log.info('Extraction options:', extractionOptions);

        // Apply retry logic with exponential backoff (3 attempts, 2s initial delay)
        const result = await retry(
            async () => await window.electronAPI.extractReceipt(extractionOptions),
            3,      // Max 3 attempts
            2000    // Start with 2s delay (then 4s, then 6s)
        );

        const duration = ((Date.now() - startTime) / 1000).toFixed(1);
        log.info('Extraction completed in', duration, 's');
        log.info('Result:', result);

        if (result && result.success) {
            extractionResults = result.data;

            sessionStats.total++;
            sessionStats.successful++;

            const receipt = result.data.receipt || result.data.best_result?.receipt || result.data;
            const coverage = receipt.coverage || receipt.extraction_coverage;
            if (coverage && coverage !== 'N/A') {
                const coverageNum = parseFloat(coverage);
                sessionStats.totalCoverage += coverageNum;
                sessionStats.coverageCount++;
            }

            const itemCount = receipt.items?.length || 0;

            updateSessionStats();
            progressSection.classList.add('hidden');
            displayResults(result.data, duration, selectedEngine);
            saveBtn.disabled = false;

            // Accessibility: Announce success
            announce(`Extraction completed successfully in ${duration} seconds. ${itemCount} items extracted.`, 'polite');
        } else {
            sessionStats.total++;
            updateSessionStats();
            log.error('Extraction failed:', result?.error);
            const errorMsg = sanitize.html(result?.error || 'Extraction Failed');
            const errorDetails = sanitize.html(result?.details || 'Unknown error occurred');
            showError(errorMsg, errorDetails);
            announce('Extraction failed', 'assertive');
        }
    } catch (error) {
        sessionStats.total++;
        updateSessionStats();
        log.error('Extraction exception:', error);
        showError('Extraction Failed', sanitize.html(error.message));
        announce('Extraction failed after multiple attempts', 'assertive');
    } finally {
        extractBtn.disabled = false;
        extractBtn.textContent = 'Extract Receipt';
    }
}

// Syntax highlight JSON
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

// Display Results
function displayResults(data, duration, engine) {
    log.info('Displaying results');
    
    emptyState.classList.add('hidden');
    resultsDisplay.classList.remove('hidden');
    
    // Update engine badge
    const resultEngineEl = document.getElementById('resultEngine');
    const resultEngineText = document.getElementById('resultEngineText');
    if (resultEngineText) {
        resultEngineText.textContent = engine === 'ocr' ? 'OCR' : 'Donut AI';
    }
    
    // Parse receipt data
    let receipt;
    let isQualityMode = false;
    
    if (data.best_result && data.all_results) {
        isQualityMode = true;
        receipt = data.best_result.receipt;
        displayStrategyComparison(data.all_results);
    } else if (data.receipt) {
        receipt = data.receipt;
    } else {
        receipt = data;
    }
    
    // Update stats
    const storeName = receipt.store?.name || 'Not detected';
    const itemCount = receipt.item_count || receipt.items?.length || 0;
    const total = Number(receipt.totals?.total || receipt.total || 0).toFixed(2);
    const coverage = receipt.coverage || receipt.extraction_coverage || 'N/A';

    document.getElementById('storeName').textContent = storeName;
    document.getElementById('itemCount').textContent = itemCount;
    document.getElementById('totalAmount').textContent = `$${total}`;
    document.getElementById('coverage').textContent = coverage;
    
    // Display items
    displayItems(receipt.items || []);
    
    // Display notes
    displayNotes(receipt.notes || receipt.extraction_notes || []);
    
    // Display validation
    displayValidation(receipt, duration);
    
    // Show JSON with syntax highlighting
    document.getElementById('jsonDisplay').innerHTML = syntaxHighlight(data);

    log.info('Results displayed');
}

// Display Items
function displayItems(items) {
    const tbody = document.getElementById('itemsTableBody');
    tbody.innerHTML = '';

    if (!items || items.length === 0) {
        const row = document.createElement('tr');
        row.setAttribute('role', 'row');
        const cell = document.createElement('td');
        cell.setAttribute('role', 'cell');
        cell.setAttribute('colspan', '4');
        cell.className = 'text-center text-muted';
        cell.textContent = 'No items extracted';
        row.appendChild(cell);
        tbody.appendChild(row);
        return;
    }

    // Security: Use safe DOM methods instead of innerHTML
    items.forEach(item => {
        const row = document.createElement('tr');
        row.setAttribute('role', 'row');

        // Product Name
        const nameCell = document.createElement('td');
        nameCell.setAttribute('role', 'cell');
        nameCell.textContent = item.name || '-';
        row.appendChild(nameCell);

        // Quantity (validated as number)
        const qtyCell = document.createElement('td');
        qtyCell.setAttribute('role', 'cell');
        qtyCell.className = 'text-center';
        qtyCell.textContent = Number(item.quantity) || 1;
        row.appendChild(qtyCell);

        // Unit Price (validated as number)
        const priceCell = document.createElement('td');
        priceCell.setAttribute('role', 'cell');
        priceCell.className = 'text-right';
        const unitPrice = item.unit_price ? Number(item.unit_price).toFixed(2) : '-';
        priceCell.textContent = unitPrice === '-' ? unitPrice : `$${unitPrice}`;
        row.appendChild(priceCell);

        // Total Price (validated as number)
        const totalCell = document.createElement('td');
        totalCell.setAttribute('role', 'cell');
        totalCell.className = 'text-right';
        const totalPrice = Number(item.total_price || 0).toFixed(2);
        totalCell.textContent = `$${totalPrice}`;
        row.appendChild(totalCell);

        tbody.appendChild(row);
    });
}

// Display Notes
function displayNotes(notes) {
    const notesSection = document.getElementById('extractionNotes');
    const notesList = document.getElementById('notesList');
    
    if (!notes || notes.length === 0) {
        notesSection.classList.add('hidden');
        return;
    }
    
    notesList.innerHTML = '';
    notes.forEach(note => {
        const li = document.createElement('li');
        li.textContent = note;
        notesList.appendChild(li);
    });
    
    notesSection.classList.remove('hidden');
}

// Display Validation
function displayValidation(receipt, duration) {
    const validationSection = document.getElementById('validationStatus');
    const validationList = document.getElementById('validationList');
    
    validationList.innerHTML = '';
    
    const checks = [];
    
    // Store
    if (receipt.store?.name) {
        checks.push({ passed: true, text: `Store: ${receipt.store.name}` });
    } else {
        checks.push({ passed: false, text: 'Store not detected' });
    }
    
    // Items
    const itemCount = receipt.items?.length || 0;
    if (itemCount > 0) {
        checks.push({ passed: true, text: `${itemCount} items found` });
    } else {
        checks.push({ passed: false, text: 'No items found' });
    }
    
    // Total
    if (receipt.totals?.total || receipt.total) {
        checks.push({ passed: true, text: `Total: $${receipt.totals?.total || receipt.total}` });
    } else {
        checks.push({ passed: false, text: 'Total not found' });
    }
    
    // Duration
    checks.push({ passed: true, text: `Completed in ${duration}s` });
    
    checks.forEach(check => {
        const li = document.createElement('li');
        li.textContent = `${check.passed ? 'âœ“' : 'âœ—'} ${check.text}`;
        li.style.color = check.passed ? 'var(--color-success)' : 'var(--color-error)';
        validationList.appendChild(li);
    });
    
    validationSection.classList.remove('hidden');
}

// Display Strategy Comparison
function displayStrategyComparison(allResults) {
    const comparisonSection = document.getElementById('strategyComparison');
    const cards = document.getElementById('strategyCards');
    
    if (!allResults || allResults.length === 0) {
        comparisonSection.classList.add('hidden');
        return;
    }
    
    cards.innerHTML = '';
    comparisonSection.classList.remove('hidden');
    
    // Find best
    let bestScore = 0;
    let bestIndex = 0;
    allResults.forEach((result, index) => {
        if (result.success && result.item_count > bestScore) {
            bestScore = result.item_count;
            bestIndex = index;
        }
    });
    
    allResults.forEach((result, index) => {
        const card = document.createElement('div');
        card.className = 'strategy-card';
        
        if (index === bestIndex && result.success) {
            card.classList.add('best');
        }
        
        if (result.success) {
            const receipt = result.receipt;
            const coverage = receipt.coverage || receipt.extraction_coverage || 'N/A';
            const confidence = receipt.confidence || result.confidence || 'N/A';
            
            card.innerHTML = `
                <h4>${result.strategy}${index === bestIndex ? '<span class="badge">Best</span>' : ''}</h4>
                <p><strong>${result.item_count}</strong> items</p>
                <p>Coverage: ${coverage}</p>
                <p>Confidence: ${confidence}</p>
            `;
        } else {
            card.innerHTML = `
                <h4>${result.strategy}</h4>
                <p style="color: var(--color-error);">Failed</p>
                <p style="font-size: 12px;">${result.error || 'Unknown error'}</p>
            `;
        }
        
        cards.appendChild(card);
    });
}

// Show Error
function showError(title, details) {
    log.error('Showing error:', title, details);
    
    resultsDisplay.classList.add('hidden');
    emptyState.classList.remove('hidden');
    progressSection.classList.add('hidden');
    
    const h3 = emptyState.querySelector('h3');
    const p = emptyState.querySelector('p');
    
    if (h3) h3.textContent = title;
    if (p) p.textContent = details || 'Please try again';
}

// Handle Save
async function handleSave() {
    if (!extractionResults) return;
    
    saveBtn.disabled = true;
    const originalText = saveBtn.textContent;
    saveBtn.textContent = 'Saving...';
    
    try {
        const fileName = selectedImagePath.split(/[\\\/]/).pop().replace(/\.[^/.]+$/, '');
        const engine = engineOCR.checked ? 'ocr' : 'donut';

        const result = await window.electronAPI.saveResults({
            data: extractionResults,
            defaultPath: `${fileName}_${engine}_extraction.json`
        });

        if (result && result.success) {
            saveBtn.textContent = 'âœ" Saved';
            announce('Results saved successfully', 'polite');
            setTimeout(() => {
                saveBtn.textContent = originalText;
                saveBtn.disabled = false;
            }, 2000);
        } else {
            saveBtn.textContent = originalText;
            saveBtn.disabled = false;
            showError('Save Failed', 'Could not save file');
            announce('Save failed', 'assertive');
        }
    } catch (error) {
        log.error('Save error:', error);
        saveBtn.textContent = originalText;
        saveBtn.disabled = false;
        showError('Save Failed', sanitize.html(error.message));
        announce('Save failed', 'assertive');
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
        toggleJsonBtn.setAttribute('aria-pressed', 'true');
        announce('JSON view shown', 'polite');
    } else {
        jsonSection.classList.add('hidden');
        toggleJsonBtn.textContent = 'JSON';
        toggleJsonBtn.setAttribute('aria-pressed', 'false');
        announce('JSON view hidden', 'polite');
    }
}

// Update Engine Info
function updateEngineInfo(engine) {
    const infoCard = document.querySelector('.info-card');
    if (!infoCard) return;
    
    const infoContent = infoCard.querySelector('.info-content');
    if (!infoContent) return;
    
    const engineInfo = {
        'ocr': {
            title: 'OCR Method',
            text: 'Fast and reliable for clear, printed receipts. Uses Tesseract OCR engine. Processing time: 1-2 seconds.'
        },
        'florence2': {
            title: 'Florence-2 (RECOMMENDED)',
            text: 'Microsoft Florence-2 with fast OCR and region detection. Best public model with no authentication required. Processing time: 2-5 seconds.'
        },
        'cord': {
            title: 'CORD Model',
            text: 'Basic 4-field extraction (store, date, address, total). Good for simple receipts. Processing time: 5-10 seconds.'
        },
        'adamcodd': {
            title: 'AdamCodd Donut',
            text: 'Comprehensive extraction including items and prices. Requires HuggingFace authentication. Processing time: 5-10 seconds.'
        }
    };
    
    const info = engineInfo[engine] || engineInfo.ocr;
    infoContent.innerHTML = `
        <p class="info-title">${info.title}</p>
        <p class="info-text">${info.text}</p>
    `;
}

// Update Session Stats
function updateSessionStats() {
    const sessionBadge = document.getElementById('sessionBadge');
    const sessionCount = document.getElementById('sessionCount');
    
    if (sessionStats.total > 0) {
        if (sessionBadge) sessionBadge.style.display = 'flex';
        if (sessionCount) sessionCount.textContent = sessionStats.total;
    }
}

// Load Settings
async function loadSettings() {
    try {
        const settings = await window.electronAPI.getSettings();
        log.info('Loaded settings:', settings);
        
        const model = settings.lastModel || 'ocr';
        
        engineOCR.checked = false;
        engineFlorence2.checked = false;
        engineCORD.checked = false;
        engineAdamCodd.checked = false;

        if (model === 'florence2') engineFlorence2.checked = true;
        else if (model === 'cord') engineCORD.checked = true;
        else if (model === 'adamcodd') engineAdamCodd.checked = true;
        else if (model === 'sroie') engineCORD.checked = true; // Migrate old sroie to cord
        else engineOCR.checked = true;
        
        if (model === 'ocr') {
            aiSettings.style.display = 'none';
        } else {
            aiSettings.style.display = 'block';
        }
        
        if (settings.aiMode) {
            aiMode.value = settings.aiMode;
            // Update mode button states
            const modeButtons = document.querySelectorAll('.mode-btn');
            modeButtons.forEach(btn => {
                btn.classList.toggle('active', btn.dataset.mode === settings.aiMode);
            });
        }

        updateEngineInfo(model);
    } catch (error) {
        log.error('Error loading settings:', error);
    }
}

// Save Settings
function saveSettings() {
    let selectedModel = 'ocr';
    if (engineFlorence2.checked) selectedModel = 'florence2';
    else if (engineCORD.checked) selectedModel = 'cord';
    else if (engineAdamCodd.checked) selectedModel = 'adamcodd';

    const settings = {
        lastModel: selectedModel,
        aiMode: aiMode.value
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
            
            // Show warning in sidebar
            const sidebar = document.querySelector('.sidebar');
            if (sidebar) {
                const warning = document.createElement('div');
                warning.style.cssText = `
                    padding: var(--space-4);
                    background: #fef3c7;
                    border: 1px solid #fbbf24;
                    border-radius: var(--radius-md);
                    margin-bottom: var(--space-4);
                `;
                warning.innerHTML = `
                    <p style="font-size: 13px; font-weight: 600; color: #92400e; margin-bottom: 4px;">âš ï¸ Setup Required</p>
                    <p style="font-size: 12px; color: #92400e;">${result.message}</p>
                `;
                sidebar.insertBefore(warning, sidebar.firstChild);
            }
            
            extractBtn.disabled = true;
            extractBtn.textContent = 'Dependencies Missing';
        } else {
            log.info('All dependencies ready');
        }
    } catch (error) {
        log.error('Error checking dependencies:', error);
    }
}
