/**
 * Results View Web Component
 * Side-by-side display of original image and extracted data
 */

class ResultsView extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        this.results = null;
        this.originalImage = null;
    }

    connectedCallback() {
        this.render();
    }

    render() {
        this.shadowRoot.innerHTML = `
            <style>
                :host {
                    display: block;
                }

                .results-container {
                    max-width: 1200px;
                    margin: 0 auto;
                }

                .results-header {
                    text-align: center;
                    margin-bottom: 32px;
                }

                .results-title {
                    font-size: 2rem;
                    font-weight: 700;
                    color: #111827;
                    margin-bottom: 8px;
                }

                .results-subtitle {
                    font-size: 1rem;
                    color: #6B7280;
                }

                .accuracy-badge {
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                    padding: 8px 16px;
                    background: #D1FAE5;
                    color: #065F46;
                    border-radius: 9999px;
                    font-weight: 600;
                    margin-top: 16px;
                }

                .results-layout {
                    display: grid;
                    grid-template-columns: 1fr;
                    gap: 24px;
                    margin-bottom: 32px;
                }

                @media (min-width: 1024px) {
                    .results-layout {
                        grid-template-columns: 1fr 1fr;
                    }
                }

                .results-panel {
                    background: white;
                    border-radius: 16px;
                    padding: 24px;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                }

                .panel-title {
                    font-size: 1.25rem;
                    font-weight: 700;
                    color: #111827;
                    margin-bottom: 16px;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }

                .panel-icon {
                    width: 24px;
                    height: 24px;
                    color: #3B82F6;
                }

                .image-container {
                    position: relative;
                    border-radius: 12px;
                    overflow: hidden;
                    background: #F3F4F6;
                    margin-bottom: 16px;
                }

                .receipt-image {
                    width: 100%;
                    height: auto;
                    display: block;
                }

                .data-section {
                    margin-bottom: 24px;
                }

                .data-section:last-child {
                    margin-bottom: 0;
                }

                .section-title {
                    font-size: 1rem;
                    font-weight: 600;
                    color: #374151;
                    margin-bottom: 12px;
                    padding-bottom: 8px;
                    border-bottom: 2px solid #E5E7EB;
                }

                .data-row {
                    display: flex;
                    justify-content: space-between;
                    padding: 8px 0;
                    border-bottom: 1px solid #F3F4F6;
                }

                .data-row:last-child {
                    border-bottom: none;
                }

                .data-label {
                    font-weight: 600;
                    color: #6B7280;
                }

                .data-value {
                    color: #111827;
                    text-align: right;
                    word-break: break-word;
                }

                .data-value.highlight {
                    font-size: 1.25rem;
                    font-weight: 700;
                    color: #10B981;
                }

                .items-table {
                    width: 100%;
                    border-collapse: collapse;
                }

                .items-table th {
                    background: #F9FAFB;
                    padding: 12px;
                    text-align: left;
                    font-weight: 600;
                    color: #374151;
                    border-bottom: 2px solid #E5E7EB;
                }

                .items-table td {
                    padding: 12px;
                    border-bottom: 1px solid #F3F4F6;
                    color: #111827;
                }

                .items-table tr:last-child td {
                    border-bottom: none;
                }

                .export-section {
                    background: white;
                    border-radius: 16px;
                    padding: 24px;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                }

                .export-buttons {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 12px;
                }

                .btn {
                    flex: 1;
                    min-width: 120px;
                    padding: 12px 24px;
                    font-weight: 600;
                    border: none;
                    border-radius: 8px;
                    cursor: pointer;
                    transition: all 150ms;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 8px;
                    min-height: 44px;
                }

                .btn-primary {
                    background: #3B82F6;
                    color: white;
                }

                .btn-primary:hover {
                    background: #2563EB;
                    transform: translateY(-1px);
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                }

                .btn-secondary {
                    background: #E5E7EB;
                    color: #374151;
                }

                .btn-secondary:hover {
                    background: #D1D5DB;
                }

                .btn-icon {
                    width: 16px;
                    height: 16px;
                }

                .action-row {
                    margin-top: 24px;
                    text-align: center;
                }

                .btn-new {
                    padding: 12px 32px;
                    background: #10B981;
                    color: white;
                    font-weight: 600;
                    border: none;
                    border-radius: 8px;
                    cursor: pointer;
                    font-size: 1rem;
                    transition: all 150ms;
                }

                .btn-new:hover {
                    background: #059669;
                    transform: translateY(-1px);
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                }

                .no-data {
                    text-align: center;
                    padding: 32px;
                    color: #9CA3AF;
                }

                @media (max-width: 640px) {
                    .export-buttons {
                        flex-direction: column;
                    }

                    .btn {
                        width: 100%;
                    }

                    .items-table {
                        font-size: 0.875rem;
                    }

                    .items-table th,
                    .items-table td {
                        padding: 8px;
                    }
                }
            </style>

            <div class="results-container">
                <div class="results-header">
                    <h2 class="results-title">✨ Extraction Complete!</h2>
                    <p class="results-subtitle">Review and export your extracted data</p>
                    <div class="accuracy-badge" id="accuracyBadge">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                        </svg>
                        <span id="accuracyText">High Confidence</span>
                    </div>
                </div>

                <div class="results-layout">
                    <!-- Left: Original Image -->
                    <div class="results-panel">
                        <h3 class="panel-title">
                            <svg class="panel-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                                <circle cx="8.5" cy="8.5" r="1.5"/>
                                <polyline points="21 15 16 10 5 21"/>
                            </svg>
                            Original Receipt
                        </h3>
                        <div class="image-container">
                            <img class="receipt-image" id="receiptImage" alt="Receipt" src="">
                        </div>
                    </div>

                    <!-- Right: Extracted Data -->
                    <div class="results-panel">
                        <h3 class="panel-title">
                            <svg class="panel-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                            </svg>
                            Extracted Data
                        </h3>
                        <div id="dataContainer">
                            <!-- Data will be inserted here -->
                        </div>
                    </div>
                </div>

                <!-- Export Section -->
                <div class="export-section">
                    <h3 class="panel-title">
                        <svg class="panel-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
                        </svg>
                        Export Data
                    </h3>
                    <div class="export-buttons">
                        <button class="btn btn-secondary" id="exportJson">
                            <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/>
                            </svg>
                            JSON
                        </button>
                        <button class="btn btn-secondary" id="exportCsv">
                            <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                            </svg>
                            CSV
                        </button>
                        <button class="btn btn-secondary" id="exportTxt">
                            <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                            </svg>
                            TXT
                        </button>
                        <button class="btn btn-primary" id="copyBtn">
                            <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/>
                            </svg>
                            Copy All
                        </button>
                    </div>
                </div>

                <div class="action-row">
                    <button class="btn-new" id="processAnotherBtn">Process Another Receipt</button>
                </div>
            </div>
        `;

        this.setupEventListeners();
    }

    setupEventListeners() {
        const exportJson = this.shadowRoot.getElementById('exportJson');
        const exportCsv = this.shadowRoot.getElementById('exportCsv');
        const exportTxt = this.shadowRoot.getElementById('exportTxt');
        const copyBtn = this.shadowRoot.getElementById('copyBtn');
        const processAnotherBtn = this.shadowRoot.getElementById('processAnotherBtn');

        exportJson.addEventListener('click', () => this.exportData('json'));
        exportCsv.addEventListener('click', () => this.exportData('csv'));
        exportTxt.addEventListener('click', () => this.exportData('txt'));
        copyBtn.addEventListener('click', () => this.copyData());
        processAnotherBtn.addEventListener('click', () => {
            this.dispatchEvent(new CustomEvent('process-another'));
        });
    }

    setResults(results, imageDataUrl) {
        this.results = results;
        this.originalImage = imageDataUrl;

        // Set image
        const receiptImage = this.shadowRoot.getElementById('receiptImage');
        if (receiptImage && imageDataUrl) {
            receiptImage.src = imageDataUrl;
        }

        // Set accuracy
        const confidence = results.confidence || 95;
        const accuracyText = this.shadowRoot.getElementById('accuracyText');
        if (accuracyText) {
            accuracyText.textContent = `${confidence}% Confidence`;
        }

        // Render data
        this.renderData();
    }

    renderData() {
        const dataContainer = this.shadowRoot.getElementById('dataContainer');
        if (!dataContainer || !this.results) return;

        const data = this.results.data || this.results;

        let html = '';

        // Store Information
        if (data.store_name || data.store_address || data.store_phone) {
            html += `
                <div class="data-section">
                    <div class="section-title">Store Information</div>
                    ${data.store_name ? `<div class="data-row"><span class="data-label">Name:</span><span class="data-value">${data.store_name}</span></div>` : ''}
                    ${data.store_address ? `<div class="data-row"><span class="data-label">Address:</span><span class="data-value">${data.store_address}</span></div>` : ''}
                    ${data.store_phone ? `<div class="data-row"><span class="data-label">Phone:</span><span class="data-value">${data.store_phone}</span></div>` : ''}
                </div>
            `;
        }

        // Transaction Details
        if (data.date || data.time || data.total || data.subtotal || data.tax) {
            html += `
                <div class="data-section">
                    <div class="section-title">Transaction Details</div>
                    ${data.date ? `<div class="data-row"><span class="data-label">Date:</span><span class="data-value">${data.date}</span></div>` : ''}
                    ${data.time ? `<div class="data-row"><span class="data-label">Time:</span><span class="data-value">${data.time}</span></div>` : ''}
                    ${data.subtotal ? `<div class="data-row"><span class="data-label">Subtotal:</span><span class="data-value">$${data.subtotal}</span></div>` : ''}
                    ${data.tax ? `<div class="data-row"><span class="data-label">Tax:</span><span class="data-value">$${data.tax}</span></div>` : ''}
                    ${data.total ? `<div class="data-row"><span class="data-label">Total:</span><span class="data-value highlight">$${data.total}</span></div>` : ''}
                </div>
            `;
        }

        // Line Items
        if (data.items && data.items.length > 0) {
            html += `
                <div class="data-section">
                    <div class="section-title">Line Items (${data.items.length})</div>
                    <table class="items-table">
                        <thead>
                            <tr>
                                <th>Item</th>
                                <th>Qty</th>
                                <th>Price</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.items.map(item => `
                                <tr>
                                    <td>${item.name || item.description || 'Unknown'}</td>
                                    <td>${item.quantity || item.qty || 1}</td>
                                    <td>$${item.price || item.amount || '0.00'}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
        }

        // Raw text (if available)
        if (data.raw_text) {
            html += `
                <div class="data-section">
                    <div class="section-title">Raw Text</div>
                    <div class="data-row"><pre style="white-space: pre-wrap; word-break: break-word;">${data.raw_text}</pre></div>
                </div>
            `;
        }

        if (html === '') {
            html = '<div class="no-data">No data extracted</div>';
        }

        dataContainer.innerHTML = html;
    }

    exportData(format) {
        if (!this.results) return;

        let content, filename, mimeType;

        switch (format) {
            case 'json':
                content = JSON.stringify(this.results, null, 2);
                filename = `receipt_${Date.now()}.json`;
                mimeType = 'application/json';
                break;

            case 'csv':
                content = this.convertToCSV();
                filename = `receipt_${Date.now()}.csv`;
                mimeType = 'text/csv';
                break;

            case 'txt':
                content = this.convertToTXT();
                filename = `receipt_${Date.now()}.txt`;
                mimeType = 'text/plain';
                break;

            default:
                return;
        }

        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
    }

    convertToCSV() {
        const data = this.results.data || this.results;
        let csv = 'Field,Value\n';

        if (data.store_name) csv += `Store Name,${data.store_name}\n`;
        if (data.store_address) csv += `Store Address,${data.store_address}\n`;
        if (data.date) csv += `Date,${data.date}\n`;
        if (data.time) csv += `Time,${data.time}\n`;
        if (data.total) csv += `Total,${data.total}\n`;

        if (data.items && data.items.length > 0) {
            csv += '\nItem,Quantity,Price\n';
            data.items.forEach(item => {
                csv += `${item.name || 'Unknown'},${item.quantity || 1},${item.price || '0.00'}\n`;
            });
        }

        return csv;
    }

    convertToTXT() {
        const data = this.results.data || this.results;
        let txt = 'RECEIPT EXTRACTION RESULTS\n';
        txt += '='.repeat(50) + '\n\n';

        if (data.store_name) txt += `Store Name: ${data.store_name}\n`;
        if (data.store_address) txt += `Address: ${data.store_address}\n`;
        if (data.date) txt += `Date: ${data.date}\n`;
        if (data.time) txt += `Time: ${data.time}\n`;
        txt += '\n';

        if (data.items && data.items.length > 0) {
            txt += 'LINE ITEMS:\n';
            txt += '-'.repeat(50) + '\n';
            data.items.forEach((item, i) => {
                txt += `${i + 1}. ${item.name || 'Unknown'} - Qty: ${item.quantity || 1} - $${item.price || '0.00'}\n`;
            });
            txt += '\n';
        }

        if (data.total) txt += `TOTAL: $${data.total}\n`;

        return txt;
    }

    copyData() {
        const text = this.convertToTXT();
        navigator.clipboard.writeText(text).then(() => {
            const copyBtn = this.shadowRoot.getElementById('copyBtn');
            const originalText = copyBtn.innerHTML;
            copyBtn.innerHTML = '✓ Copied!';
            setTimeout(() => {
                copyBtn.innerHTML = originalText;
            }, 2000);
        });
    }
}

customElements.define('results-view', ResultsView);
