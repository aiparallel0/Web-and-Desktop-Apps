/**
 * Export Utility
 * Handles exporting receipt data to various formats (JSON, CSV, Excel, PDF)
 */

class ExportUtility {
    /**
     * Export data to JSON format
     * @param {Object|Array} data - Data to export
     * @param {string} filename - Output filename
     */
    static exportToJSON(data, filename = 'receipt-export.json') {
        const jsonString = JSON.stringify(data, null, 2);
        const blob = new Blob([jsonString], { type: 'application/json' });
        this.downloadBlob(blob, filename);
    }

    /**
     * Export data to CSV format
     * @param {Array} data - Array of objects to export
     * @param {string} filename - Output filename
     */
    static exportToCSV(data, filename = 'receipt-export.csv') {
        if (!Array.isArray(data) || data.length === 0) {
            console.error('Data must be a non-empty array');
            return;
        }

        // Get headers from first object
        const headers = Object.keys(data[0]);
        
        // Create CSV content
        let csvContent = headers.join(',') + '\n';
        
        // Add rows
        data.forEach(row => {
            const values = headers.map(header => {
                const value = row[header];
                // Escape commas and quotes
                if (value === null || value === undefined) return '';
                const stringValue = String(value);
                if (stringValue.includes(',') || stringValue.includes('"') || stringValue.includes('\n')) {
                    return '"' + stringValue.replace(/"/g, '""') + '"';
                }
                return stringValue;
            });
            csvContent += values.join(',') + '\n';
        });

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        this.downloadBlob(blob, filename);
    }

    /**
     * Export data to Excel format (simple XLSX using SheetJS if available)
     * @param {Array} data - Array of objects to export
     * @param {string} filename - Output filename
     */
    static exportToExcel(data, filename = 'receipt-export.xlsx') {
        if (typeof XLSX === 'undefined') {
            console.error('SheetJS library not loaded. Falling back to CSV export.');
            this.exportToCSV(data, filename.replace('.xlsx', '.csv'));
            return;
        }

        const worksheet = XLSX.utils.json_to_sheet(data);
        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, 'Receipts');
        
        // Generate buffer
        const excelBuffer = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
        const blob = new Blob([excelBuffer], { 
            type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
        });
        
        this.downloadBlob(blob, filename);
    }

    /**
     * Export data to TXT format
     * @param {Object|Array} data - Data to export
     * @param {string} filename - Output filename
     */
    static exportToTXT(data, filename = 'receipt-export.txt') {
        let textContent = '';

        if (Array.isArray(data)) {
            data.forEach((item, index) => {
                textContent += `=== Receipt ${index + 1} ===\n`;
                textContent += this.objectToText(item);
                textContent += '\n\n';
            });
        } else {
            textContent = this.objectToText(data);
        }

        const blob = new Blob([textContent], { type: 'text/plain;charset=utf-8;' });
        this.downloadBlob(blob, filename);
    }

    /**
     * Export receipt data as PDF (requires jsPDF library)
     * @param {Object} receiptData - Receipt data object
     * @param {string} filename - Output filename
     */
    static exportToPDF(receiptData, filename = 'receipt.pdf') {
        if (typeof jsPDF === 'undefined') {
            console.error('jsPDF library not loaded. Falling back to TXT export.');
            this.exportToTXT(receiptData, filename.replace('.pdf', '.txt'));
            return;
        }

        const doc = new jsPDF();
        
        // Title
        doc.setFontSize(20);
        doc.setFont(undefined, 'bold');
        doc.text('Receipt Details', 20, 20);
        
        // Merchant info
        doc.setFontSize(14);
        doc.setFont(undefined, 'bold');
        doc.text('Merchant Information', 20, 40);
        doc.setFontSize(11);
        doc.setFont(undefined, 'normal');
        doc.text(`Name: ${receiptData.merchant || 'N/A'}`, 20, 50);
        doc.text(`Date: ${receiptData.date || 'N/A'}`, 20, 57);
        doc.text(`Time: ${receiptData.time || 'N/A'}`, 20, 64);
        
        // Items
        if (receiptData.items && receiptData.items.length > 0) {
            doc.setFontSize(14);
            doc.setFont(undefined, 'bold');
            doc.text('Items', 20, 80);
            
            let yPos = 90;
            doc.setFontSize(10);
            doc.setFont(undefined, 'normal');
            
            receiptData.items.forEach((item, index) => {
                const itemText = `${item.name || 'Item ' + (index + 1)}`;
                const qtyText = item.quantity ? `x${item.quantity}` : '';
                const priceText = item.price ? `$${item.price.toFixed(2)}` : '';
                
                doc.text(itemText, 20, yPos);
                doc.text(qtyText, 120, yPos, { align: 'right' });
                doc.text(priceText, 180, yPos, { align: 'right' });
                
                yPos += 7;
                
                if (yPos > 270) {
                    doc.addPage();
                    yPos = 20;
                }
            });
            
            // Totals
            yPos += 10;
            doc.setFont(undefined, 'bold');
            
            if (receiptData.subtotal) {
                doc.text('Subtotal:', 120, yPos, { align: 'right' });
                doc.text(`$${receiptData.subtotal.toFixed(2)}`, 180, yPos, { align: 'right' });
                yPos += 7;
            }
            
            if (receiptData.tax) {
                doc.text('Tax:', 120, yPos, { align: 'right' });
                doc.text(`$${receiptData.tax.toFixed(2)}`, 180, yPos, { align: 'right' });
                yPos += 7;
            }
            
            if (receiptData.total) {
                doc.setFontSize(12);
                doc.text('Total:', 120, yPos, { align: 'right' });
                doc.text(`$${receiptData.total.toFixed(2)}`, 180, yPos, { align: 'right' });
            }
        }
        
        // Footer
        doc.setFontSize(8);
        doc.setFont(undefined, 'normal');
        doc.setTextColor(128);
        doc.text('Generated by Receipt Extractor', 105, 285, { align: 'center' });
        
        doc.save(filename);
    }

    /**
     * Batch export multiple receipts
     * @param {Array} receipts - Array of receipt objects
     * @param {string} format - Export format (json, csv, excel, txt)
     * @param {string} filename - Output filename
     */
    static batchExport(receipts, format = 'csv', filename = null) {
        if (!filename) {
            const timestamp = new Date().toISOString().split('T')[0];
            filename = `receipts-${timestamp}`;
        }

        // Flatten receipt data for tabular formats
        const flattenedData = receipts.map((receipt, index) => {
            return {
                receipt_id: index + 1,
                merchant: receipt.merchant || '',
                date: receipt.date || '',
                time: receipt.time || '',
                subtotal: receipt.subtotal || 0,
                tax: receipt.tax || 0,
                total: receipt.total || 0,
                items_count: receipt.items?.length || 0,
                currency: receipt.currency || 'USD'
            };
        });

        switch (format.toLowerCase()) {
            case 'json':
                this.exportToJSON(receipts, `${filename}.json`);
                break;
            case 'csv':
                this.exportToCSV(flattenedData, `${filename}.csv`);
                break;
            case 'excel':
            case 'xlsx':
                this.exportToExcel(flattenedData, `${filename}.xlsx`);
                break;
            case 'txt':
                this.exportToTXT(receipts, `${filename}.txt`);
                break;
            default:
                console.error('Unsupported format:', format);
        }
    }

    /**
     * Export single receipt with image
     * @param {Object} receipt - Receipt data
     * @param {string} imageData - Base64 image data
     * @param {string} format - Export format
     */
    static exportWithImage(receipt, imageData, format = 'pdf') {
        if (format === 'pdf' && typeof jsPDF !== 'undefined') {
            const doc = new jsPDF();
            
            // Add image if available
            if (imageData) {
                try {
                    const imgWidth = 180;
                    const imgHeight = 120;
                    doc.addImage(imageData, 'JPEG', 15, 15, imgWidth, imgHeight);
                    
                    // Add receipt data below image
                    let yPos = imgHeight + 30;
                    doc.setFontSize(14);
                    doc.setFont(undefined, 'bold');
                    doc.text('Extracted Data', 20, yPos);
                    
                    yPos += 10;
                    doc.setFontSize(11);
                    doc.setFont(undefined, 'normal');
                    doc.text(`Merchant: ${receipt.merchant || 'N/A'}`, 20, yPos);
                    yPos += 7;
                    doc.text(`Date: ${receipt.date || 'N/A'}`, 20, yPos);
                    yPos += 7;
                    doc.text(`Total: $${(receipt.total || 0).toFixed(2)}`, 20, yPos);
                    
                    doc.save(`receipt-${receipt.date || 'export'}.pdf`);
                } catch (error) {
                    console.error('Error adding image to PDF:', error);
                    this.exportToPDF(receipt);
                }
            } else {
                this.exportToPDF(receipt);
            }
        } else {
            this.exportToPDF(receipt);
        }
    }

    /**
     * Helper function to convert object to text format
     * @param {Object} obj - Object to convert
     * @param {number} indent - Indentation level
     * @returns {string} Text representation
     */
    static objectToText(obj, indent = 0) {
        let text = '';
        const indentStr = '  '.repeat(indent);

        for (const [key, value] of Object.entries(obj)) {
            if (value === null || value === undefined) continue;
            
            const formattedKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            
            if (typeof value === 'object' && !Array.isArray(value)) {
                text += `${indentStr}${formattedKey}:\n`;
                text += this.objectToText(value, indent + 1);
            } else if (Array.isArray(value)) {
                text += `${indentStr}${formattedKey}:\n`;
                value.forEach((item, index) => {
                    if (typeof item === 'object') {
                        text += `${indentStr}  Item ${index + 1}:\n`;
                        text += this.objectToText(item, indent + 2);
                    } else {
                        text += `${indentStr}  - ${item}\n`;
                    }
                });
            } else {
                text += `${indentStr}${formattedKey}: ${value}\n`;
            }
        }

        return text;
    }

    /**
     * Helper function to download a blob
     * @param {Blob} blob - Blob to download
     * @param {string} filename - Download filename
     */
    static downloadBlob(blob, filename) {
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }

    /**
     * Show export dialog with format selection
     * @param {Object|Array} data - Data to export
     * @param {Function} callback - Callback after export
     */
    static showExportDialog(data, callback) {
        const dialog = document.createElement('div');
        dialog.className = 'export-dialog-overlay';
        dialog.innerHTML = `
            <div class="export-dialog">
                <div class="export-dialog-header">
                    <h3>Export Data</h3>
                    <button class="export-close">&times;</button>
                </div>
                <div class="export-dialog-body">
                    <p>Choose export format:</p>
                    <div class="export-formats">
                        <button class="export-format-btn" data-format="json">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                                <polyline points="14 2 14 8 20 8"></polyline>
                            </svg>
                            <span>JSON</span>
                        </button>
                        <button class="export-format-btn" data-format="csv">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                                <polyline points="14 2 14 8 20 8"></polyline>
                            </svg>
                            <span>CSV</span>
                        </button>
                        <button class="export-format-btn" data-format="excel">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                                <polyline points="14 2 14 8 20 8"></polyline>
                            </svg>
                            <span>Excel</span>
                        </button>
                        <button class="export-format-btn" data-format="txt">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                                <polyline points="14 2 14 8 20 8"></polyline>
                            </svg>
                            <span>TXT</span>
                        </button>
                        <button class="export-format-btn" data-format="pdf">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                                <polyline points="14 2 14 8 20 8"></polyline>
                            </svg>
                            <span>PDF</span>
                        </button>
                    </div>
                </div>
            </div>
        `;

        // Add styles
        this.addDialogStyles();

        // Event listeners
        dialog.querySelector('.export-close').addEventListener('click', () => {
            document.body.removeChild(dialog);
        });

        dialog.querySelectorAll('.export-format-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const format = btn.dataset.format;
                if (Array.isArray(data)) {
                    this.batchExport(data, format);
                } else {
                    switch (format) {
                        case 'json':
                            this.exportToJSON(data);
                            break;
                        case 'csv':
                            this.exportToCSV([data]);
                            break;
                        case 'excel':
                            this.exportToExcel([data]);
                            break;
                        case 'txt':
                            this.exportToTXT(data);
                            break;
                        case 'pdf':
                            this.exportToPDF(data);
                            break;
                    }
                }
                document.body.removeChild(dialog);
                if (callback) callback(format);
            });
        });

        document.body.appendChild(dialog);
    }

    static addDialogStyles() {
        if (document.getElementById('export-dialog-styles')) return;

        const style = document.createElement('style');
        style.id = 'export-dialog-styles';
        style.textContent = `
            .export-dialog-overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 10000;
                animation: fadeIn 0.2s ease;
            }

            .export-dialog {
                background: white;
                border-radius: var(--radius-xl);
                max-width: 500px;
                width: 90%;
                box-shadow: 0 25px 50px rgba(0, 0, 0, 0.3);
                animation: slideInUp 0.3s ease;
            }

            .export-dialog-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: var(--space-4);
                border-bottom: 1px solid var(--color-gray-200);
            }

            .export-dialog-header h3 {
                margin: 0;
                font-size: 1.25rem;
                color: var(--color-gray-900);
            }

            .export-close {
                width: 32px;
                height: 32px;
                border: none;
                background: transparent;
                font-size: 1.5rem;
                color: var(--color-gray-500);
                cursor: pointer;
                border-radius: var(--radius-md);
                transition: all var(--transition-fast);
            }

            .export-close:hover {
                background: var(--color-gray-100);
                color: var(--color-gray-900);
            }

            .export-dialog-body {
                padding: var(--space-4);
            }

            .export-dialog-body p {
                margin-bottom: var(--space-3);
                color: var(--color-gray-600);
            }

            .export-formats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
                gap: var(--space-2);
            }

            .export-format-btn {
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 8px;
                padding: var(--space-3);
                border: 2px solid var(--color-gray-200);
                border-radius: var(--radius-lg);
                background: white;
                cursor: pointer;
                transition: all var(--transition-fast);
            }

            .export-format-btn:hover {
                border-color: var(--color-primary);
                background: var(--color-primary-50);
            }

            .export-format-btn svg {
                color: var(--color-gray-600);
            }

            .export-format-btn:hover svg {
                color: var(--color-primary);
            }

            .export-format-btn span {
                font-size: 0.875rem;
                font-weight: var(--font-medium);
                color: var(--color-gray-700);
            }

            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }

            @keyframes slideInUp {
                from {
                    opacity: 0;
                    transform: translateY(30px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
        `;
        document.head.appendChild(style);
    }
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ExportUtility;
}
window.ExportUtility = ExportUtility;
