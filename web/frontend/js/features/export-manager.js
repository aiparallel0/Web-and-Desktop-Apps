/**
 * Export Manager
 * Handles exporting data to various formats (CSV, Excel, JSON, PDF)
 */

import apiClient from '../core/api-client.js';
import toastSystem from '../components/toast-system.js';
import modalSystem from '../components/modal-system.js';

class ExportManager {
    constructor() {
        this.formats = {
            json: {
                name: 'JSON',
                ext: 'json',
                mimeType: 'application/json',
                icon: '{ }'
            },
            csv: {
                name: 'CSV',
                ext: 'csv',
                mimeType: 'text/csv',
                icon: '📊'
            },
            excel: {
                name: 'Excel',
                ext: 'xlsx',
                mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                icon: '📈'
            },
            pdf: {
                name: 'PDF',
                ext: 'pdf',
                mimeType: 'application/pdf',
                icon: '📄'
            }
        };
    }

    /**
     * Show export dialog
     */
    async showExportDialog(data, options = {}) {
        const {
            title = 'Export Data',
            filename = 'export',
            defaultFormat = 'json',
            formats = ['json', 'csv', 'excel', 'pdf'],
            includeFields = true,
            onExport = null
        } = options;

        return new Promise((resolve) => {
            const formatsHtml = formats.map(format => {
                const config = this.formats[format];
                return `
                    <label class="export-format-option">
                        <input type="radio" 
                               name="exportFormat" 
                               value="${format}" 
                               ${format === defaultFormat ? 'checked' : ''}>
                        <div class="format-card">
                            <div class="format-icon">${config.icon}</div>
                            <div class="format-name">${config.name}</div>
                        </div>
                    </label>
                `;
            }).join('');

            const content = `
                <div class="export-dialog">
                    <div class="form-group">
                        <label>Export Format</label>
                        <div class="export-formats">
                            ${formatsHtml}
                        </div>
                    </div>

                    <div class="form-group">
                        <label for="exportFilename">Filename</label>
                        <input type="text" 
                               id="exportFilename" 
                               class="modal-input"
                               value="${filename}"
                               placeholder="Enter filename">
                    </div>

                    ${includeFields ? `
                        <div class="form-group">
                            <label>
                                <input type="checkbox" id="exportIncludeHeaders" checked>
                                Include column headers
                            </label>
                        </div>
                    ` : ''}

                    <div class="export-summary">
                        Exporting ${Array.isArray(data) ? data.length : Object.keys(data).length} items
                    </div>
                </div>
            `;

            const modalId = modalSystem.open('export-dialog', content, {
                title,
                size: 'medium',
                footer: {
                    buttons: [
                        {
                            label: 'Cancel',
                            className: 'btn btn-secondary',
                            action: 'cancel'
                        },
                        {
                            label: 'Export',
                            className: 'btn btn-primary',
                            action: 'export'
                        }
                    ]
                },
                onClose: () => resolve(null)
            });

            // Handle export button
            setTimeout(() => {
                const modal = document.querySelector(`[data-modal-id="${modalId}"]`);
                if (!modal) return;

                const exportBtn = modal.querySelector('[data-action="export"]');
                const cancelBtn = modal.querySelector('[data-action="cancel"]');

                exportBtn.addEventListener('click', async () => {
                    const format = modal.querySelector('input[name="exportFormat"]:checked').value;
                    const filenameInput = modal.querySelector('#exportFilename').value || filename;
                    const includeHeaders = modal.querySelector('#exportIncludeHeaders')?.checked ?? true;

                    modalSystem.close(modalId);

                    try {
                        const result = await this.export(data, {
                            format,
                            filename: filenameInput,
                            includeHeaders,
                            onExport
                        });

                        resolve(result);
                    } catch (error) {
                        toastSystem.error('Export failed: ' + error.message);
                        resolve(null);
                    }
                });

                cancelBtn.addEventListener('click', () => {
                    modalSystem.close(modalId);
                    resolve(null);
                });
            }, 100);
        });
    }

    /**
     * Export data to specified format
     */
    async export(data, options = {}) {
        const {
            format = 'json',
            filename = 'export',
            includeHeaders = true,
            onExport = null
        } = options;

        const toastId = toastSystem.loading(`Exporting to ${format.toUpperCase()}...`);

        try {
            let blob;
            const config = this.formats[format];

            switch (format) {
                case 'json':
                    blob = this.exportToJSON(data, options);
                    break;
                case 'csv':
                    blob = this.exportToCSV(data, { includeHeaders });
                    break;
                case 'excel':
                    blob = await this.exportToExcel(data, { includeHeaders });
                    break;
                case 'pdf':
                    blob = await this.exportToPDF(data, options);
                    break;
                default:
                    throw new Error(`Unsupported format: ${format}`);
            }

            // Download file
            const fullFilename = `${filename}.${config.ext}`;
            this.downloadBlob(blob, fullFilename);

            // Callback
            if (onExport) {
                onExport(format, fullFilename);
            }

            toastSystem.remove(toastId);
            toastSystem.success(`Exported to ${fullFilename}`);

            return { format, filename: fullFilename, success: true };

        } catch (error) {
            toastSystem.remove(toastId);
            throw error;
        }
    }

    /**
     * Export to JSON
     */
    exportToJSON(data, options = {}) {
        const {
            pretty = true,
            indent = 2
        } = options;

        const jsonStr = pretty 
            ? JSON.stringify(data, null, indent)
            : JSON.stringify(data);

        return new Blob([jsonStr], { type: this.formats.json.mimeType });
    }

    /**
     * Export to CSV
     */
    exportToCSV(data, options = {}) {
        const {
            includeHeaders = true,
            delimiter = ',',
            linebreak = '\n'
        } = options;

        if (!Array.isArray(data) || data.length === 0) {
            throw new Error('Data must be a non-empty array');
        }

        // Get headers from first object
        const headers = Object.keys(data[0]);
        const rows = [];

        // Add headers
        if (includeHeaders) {
            rows.push(headers.map(h => this.escapeCSV(h)).join(delimiter));
        }

        // Add data rows
        data.forEach(item => {
            const row = headers.map(header => {
                const value = item[header];
                return this.escapeCSV(value);
            });
            rows.push(row.join(delimiter));
        });

        const csvContent = rows.join(linebreak);
        return new Blob([csvContent], { type: this.formats.csv.mimeType });
    }

    /**
     * Export to Excel
     */
    async exportToExcel(data, options = {}) {
        const {
            includeHeaders = true,
            sheetName = 'Sheet1'
        } = options;

        // For now, generate CSV and label as Excel
        // In production, you'd use a library like SheetJS
        const csvBlob = this.exportToCSV(data, { includeHeaders });
        return new Blob([await csvBlob.text()], { type: this.formats.excel.mimeType });
    }

    /**
     * Export to PDF
     */
    async exportToPDF(data, options = {}) {
        const {
            title = 'Export',
            orientation = 'portrait',
            pageSize = 'A4'
        } = options;

        // For now, generate text content
        // In production, you'd use a library like jsPDF
        let content = `${title}\n\n`;

        if (Array.isArray(data)) {
            data.forEach((item, index) => {
                content += `Item ${index + 1}:\n`;
                Object.entries(item).forEach(([key, value]) => {
                    content += `  ${key}: ${value}\n`;
                });
                content += '\n';
            });
        } else {
            Object.entries(data).forEach(([key, value]) => {
                content += `${key}: ${value}\n`;
            });
        }

        return new Blob([content], { type: this.formats.pdf.mimeType });
    }

    /**
     * Export via API
     */
    async exportViaAPI(ids, format = 'json') {
        try {
            const blob = await apiClient.exportData(ids, format);
            const filename = `export-${Date.now()}.${this.formats[format].ext}`;
            this.downloadBlob(blob, filename);
            return { success: true, filename };
        } catch (error) {
            throw new Error('API export failed: ' + error.message);
        }
    }

    /**
     * Export all data via API
     */
    async exportAllViaAPI(format = 'json', filters = {}) {
        try {
            const blob = await apiClient.exportAll(format, filters);
            const filename = `export-all-${Date.now()}.${this.formats[format].ext}`;
            this.downloadBlob(blob, filename);
            return { success: true, filename };
        } catch (error) {
            throw new Error('API export all failed: ' + error.message);
        }
    }

    /**
     * Download blob as file
     */
    downloadBlob(blob, filename) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    /**
     * Escape CSV value
     */
    escapeCSV(value) {
        if (value === null || value === undefined) {
            return '';
        }

        const str = String(value);

        // Check if value contains special characters
        if (str.includes(',') || str.includes('"') || str.includes('\n')) {
            return `"${str.replace(/"/g, '""')}"`;
        }

        return str;
    }

    /**
     * Export clipboard
     */
    async exportToClipboard(data, format = 'json') {
        try {
            let content;

            if (format === 'json') {
                content = JSON.stringify(data, null, 2);
            } else if (format === 'csv') {
                const blob = this.exportToCSV(data);
                content = await blob.text();
            } else {
                throw new Error('Clipboard export only supports JSON and CSV');
            }

            await navigator.clipboard.writeText(content);
            toastSystem.success('Copied to clipboard');

            return { success: true };
        } catch (error) {
            throw new Error('Clipboard export failed: ' + error.message);
        }
    }

    /**
     * Print data
     */
    printData(data, options = {}) {
        const {
            title = 'Print',
            includeHeaders = true
        } = options;

        const printWindow = window.open('', '_blank');
        
        let html = `
            <!DOCTYPE html>
            <html>
            <head>
                <title>${title}</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        padding: 20px;
                    }
                    h1 {
                        margin-bottom: 20px;
                    }
                    table {
                        width: 100%;
                        border-collapse: collapse;
                    }
                    th, td {
                        padding: 8px;
                        text-align: left;
                        border: 1px solid #ddd;
                    }
                    th {
                        background-color: #f3f4f6;
                        font-weight: 600;
                    }
                    @media print {
                        button {
                            display: none;
                        }
                    }
                </style>
            </head>
            <body>
                <h1>${title}</h1>
                <button onclick="window.print()">Print</button>
        `;

        if (Array.isArray(data) && data.length > 0) {
            const headers = Object.keys(data[0]);
            
            html += '<table>';
            
            if (includeHeaders) {
                html += '<thead><tr>';
                headers.forEach(header => {
                    html += `<th>${header}</th>`;
                });
                html += '</tr></thead>';
            }

            html += '<tbody>';
            data.forEach(item => {
                html += '<tr>';
                headers.forEach(header => {
                    html += `<td>${item[header] || ''}</td>`;
                });
                html += '</tr>';
            });
            html += '</tbody></table>';
        } else {
            html += '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
        }

        html += '</body></html>';

        printWindow.document.write(html);
        printWindow.document.close();
    }
}

// Create singleton
const exportManager = new ExportManager();

// Expose globally
if (typeof window !== 'undefined') {
    window.exportManager = exportManager;
    window.ExportManager = ExportManager;
}

export default exportManager;
