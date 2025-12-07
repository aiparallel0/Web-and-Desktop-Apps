/**
 * Data Manager - Handles all data operations for receipts
 * @version 2.0.0
 */

(function(window) {
    'use strict';

    class DataManager {
        constructor() {
            this.receipts = [];
            this.filteredReceipts = [];
            this.currentFilters = {};
            this.currentSort = { field: 'date', direction: 'desc' };
            this.pagination = {
                currentPage: 1,
                itemsPerPage: 10,
                totalItems: 0,
                totalPages: 0
            };
            this.listeners = new Map();
            this.loadFromStorage();
        }

        /**
         * Load receipts from localStorage
         */
        loadFromStorage() {
            try {
                const stored = localStorage.getItem('receipts_data');
                if (stored) {
                    this.receipts = JSON.parse(stored);
                    this.filteredReceipts = [...this.receipts];
                    this.updatePagination();
                }
            } catch (error) {
                console.error('[DataManager] Error loading data:', error);
            }
        }

        /**
         * Save receipts to localStorage
         */
        saveToStorage() {
            try {
                localStorage.setItem('receipts_data', JSON.stringify(this.receipts));
            } catch (error) {
                console.error('[DataManager] Error saving data:', error);
            }
        }

        /**
         * Add a new receipt
         */
        addReceipt(receipt) {
            const newReceipt = {
                id: this.generateId(),
                ...receipt,
                createdAt: new Date().toISOString(),
                updatedAt: new Date().toISOString()
            };
            
            this.receipts.unshift(newReceipt);
            this.saveToStorage();
            this.applyFiltersAndSort();
            this.emit('receiptAdded', newReceipt);
            
            return newReceipt;
        }

        /**
         * Update a receipt
         */
        updateReceipt(id, updates) {
            const index = this.receipts.findIndex(r => r.id === id);
            if (index !== -1) {
                this.receipts[index] = {
                    ...this.receipts[index],
                    ...updates,
                    updatedAt: new Date().toISOString()
                };
                this.saveToStorage();
                this.applyFiltersAndSort();
                this.emit('receiptUpdated', this.receipts[index]);
                return this.receipts[index];
            }
            return null;
        }

        /**
         * Delete a receipt
         */
        deleteReceipt(id) {
            const index = this.receipts.findIndex(r => r.id === id);
            if (index !== -1) {
                const deleted = this.receipts.splice(index, 1)[0];
                this.saveToStorage();
                this.applyFiltersAndSort();
                this.emit('receiptDeleted', deleted);
                return true;
            }
            return false;
        }

        /**
         * Get a single receipt by ID
         */
        getReceipt(id) {
            return this.receipts.find(r => r.id === id);
        }

        /**
         * Get all receipts
         */
        getAllReceipts() {
            return [...this.receipts];
        }

        /**
         * Get current page of receipts
         */
        getCurrentPage() {
            const start = (this.pagination.currentPage - 1) * this.pagination.itemsPerPage;
            const end = start + this.pagination.itemsPerPage;
            return this.filteredReceipts.slice(start, end);
        }

        /**
         * Search receipts
         */
        search(query) {
            if (!query || query.trim() === '') {
                this.filteredReceipts = [...this.receipts];
            } else {
                const lowerQuery = query.toLowerCase();
                this.filteredReceipts = this.receipts.filter(receipt => {
                    return (
                        (receipt.merchant && receipt.merchant.toLowerCase().includes(lowerQuery)) ||
                        (receipt.total && receipt.total.toString().includes(lowerQuery)) ||
                        (receipt.date && receipt.date.includes(query)) ||
                        (receipt.category && receipt.category.toLowerCase().includes(lowerQuery))
                    );
                });
            }
            
            this.pagination.currentPage = 1;
            this.updatePagination();
            this.emit('dataChanged', this.filteredReceipts);
        }

        /**
         * Filter receipts
         */
        filter(filters) {
            this.currentFilters = filters;
            this.applyFiltersAndSort();
        }

        /**
         * Apply current filters and sort
         */
        applyFiltersAndSort() {
            // Start with all receipts
            let filtered = [...this.receipts];
            
            // Apply filters
            if (this.currentFilters.dateFrom) {
                filtered = filtered.filter(r => new Date(r.date) >= new Date(this.currentFilters.dateFrom));
            }
            
            if (this.currentFilters.dateTo) {
                filtered = filtered.filter(r => new Date(r.date) <= new Date(this.currentFilters.dateTo));
            }
            
            if (this.currentFilters.minAmount) {
                filtered = filtered.filter(r => parseFloat(r.total) >= parseFloat(this.currentFilters.minAmount));
            }
            
            if (this.currentFilters.maxAmount) {
                filtered = filtered.filter(r => parseFloat(r.total) <= parseFloat(this.currentFilters.maxAmount));
            }
            
            if (this.currentFilters.category) {
                filtered = filtered.filter(r => r.category === this.currentFilters.category);
            }
            
            if (this.currentFilters.merchant) {
                filtered = filtered.filter(r => r.merchant && r.merchant.toLowerCase().includes(this.currentFilters.merchant.toLowerCase()));
            }
            
            if (this.currentFilters.status) {
                filtered = filtered.filter(r => r.status === this.currentFilters.status);
            }
            
            // Apply sort
            filtered.sort((a, b) => {
                const field = this.currentSort.field;
                const direction = this.currentSort.direction === 'asc' ? 1 : -1;
                
                let aVal = a[field];
                let bVal = b[field];
                
                // Handle numbers
                if (field === 'total') {
                    aVal = parseFloat(aVal) || 0;
                    bVal = parseFloat(bVal) || 0;
                }
                
                // Handle dates
                if (field === 'date' || field === 'createdAt') {
                    aVal = new Date(aVal).getTime();
                    bVal = new Date(bVal).getTime();
                }
                
                if (aVal < bVal) return -direction;
                if (aVal > bVal) return direction;
                return 0;
            });
            
            this.filteredReceipts = filtered;
            this.pagination.currentPage = 1;
            this.updatePagination();
            this.emit('dataChanged', this.filteredReceipts);
        }

        /**
         * Sort receipts
         */
        sort(field, direction = 'asc') {
            this.currentSort = { field, direction };
            this.applyFiltersAndSort();
        }

        /**
         * Update pagination info
         */
        updatePagination() {
            this.pagination.totalItems = this.filteredReceipts.length;
            this.pagination.totalPages = Math.ceil(this.pagination.totalItems / this.pagination.itemsPerPage);
            
            // Ensure current page is valid
            if (this.pagination.currentPage > this.pagination.totalPages) {
                this.pagination.currentPage = Math.max(1, this.pagination.totalPages);
            }
        }

        /**
         * Go to specific page
         */
        goToPage(page) {
            if (page >= 1 && page <= this.pagination.totalPages) {
                this.pagination.currentPage = page;
                this.emit('pageChanged', page);
            }
        }

        /**
         * Set items per page
         */
        setItemsPerPage(count) {
            this.pagination.itemsPerPage = count;
            this.updatePagination();
            this.emit('dataChanged', this.filteredReceipts);
        }

        /**
         * Get pagination info
         */
        getPaginationInfo() {
            return { ...this.pagination };
        }

        /**
         * Bulk operations
         */
        bulkDelete(ids) {
            const deleted = [];
            ids.forEach(id => {
                const index = this.receipts.findIndex(r => r.id === id);
                if (index !== -1) {
                    deleted.push(this.receipts.splice(index, 1)[0]);
                }
            });
            
            if (deleted.length > 0) {
                this.saveToStorage();
                this.applyFiltersAndSort();
                this.emit('bulkDeleted', deleted);
            }
            
            return deleted;
        }

        /**
         * Bulk update
         */
        bulkUpdate(ids, updates) {
            const updated = [];
            ids.forEach(id => {
                const index = this.receipts.findIndex(r => r.id === id);
                if (index !== -1) {
                    this.receipts[index] = {
                        ...this.receipts[index],
                        ...updates,
                        updatedAt: new Date().toISOString()
                    };
                    updated.push(this.receipts[index]);
                }
            });
            
            if (updated.length > 0) {
                this.saveToStorage();
                this.applyFiltersAndSort();
                this.emit('bulkUpdated', updated);
            }
            
            return updated;
        }

        /**
         * Export data
         */
        exportData(format = 'json', includeFiltered = true) {
            const data = includeFiltered ? this.filteredReceipts : this.receipts;
            
            switch (format.toLowerCase()) {
                case 'json':
                    return this.exportJSON(data);
                case 'csv':
                    return this.exportCSV(data);
                case 'excel':
                    return this.exportExcel(data);
                default:
                    throw new Error(`Unsupported format: ${format}`);
            }
        }

        /**
         * Export as JSON
         */
        exportJSON(data) {
            const json = JSON.stringify(data, null, 2);
            const blob = new Blob([json], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            
            const link = document.createElement('a');
            link.href = url;
            link.download = `receipts_${Date.now()}.json`;
            link.click();
            
            URL.revokeObjectURL(url);
        }

        /**
         * Export as CSV
         */
        exportCSV(data) {
            if (data.length === 0) {
                alert('No data to export');
                return;
            }
            
            // Get all keys from first object
            const keys = Object.keys(data[0]);
            
            // Create CSV header
            let csv = keys.join(',') + '\n';
            
            // Add rows
            data.forEach(row => {
                const values = keys.map(key => {
                    const value = row[key];
                    // Escape commas and quotes
                    if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
                        return `"${value.replace(/"/g, '""')}"`;
                    }
                    return value;
                });
                csv += values.join(',') + '\n';
            });
            
            const blob = new Blob([csv], { type: 'text/csv' });
            const url = URL.createObjectURL(blob);
            
            const link = document.createElement('a');
            link.href = url;
            link.download = `receipts_${Date.now()}.csv`;
            link.click();
            
            URL.revokeObjectURL(url);
        }

        /**
         * Export as Excel (using CSV format)
         */
        exportExcel(data) {
            // For now, use CSV format with .xls extension
            // In production, use a library like xlsx
            this.exportCSV(data);
        }

        /**
         * Get statistics
         */
        getStatistics() {
            const total = this.receipts.length;
            const totalAmount = this.receipts.reduce((sum, r) => sum + (parseFloat(r.total) || 0), 0);
            const avgAmount = total > 0 ? totalAmount / total : 0;
            
            // Group by month
            const byMonth = {};
            this.receipts.forEach(r => {
                const month = new Date(r.date).toISOString().slice(0, 7);
                if (!byMonth[month]) {
                    byMonth[month] = { count: 0, amount: 0 };
                }
                byMonth[month].count++;
                byMonth[month].amount += parseFloat(r.total) || 0;
            });
            
            // Group by category
            const byCategory = {};
            this.receipts.forEach(r => {
                const category = r.category || 'Uncategorized';
                if (!byCategory[category]) {
                    byCategory[category] = { count: 0, amount: 0 };
                }
                byCategory[category].count++;
                byCategory[category].amount += parseFloat(r.total) || 0;
            });
            
            // Top merchants
            const merchantMap = {};
            this.receipts.forEach(r => {
                if (r.merchant) {
                    if (!merchantMap[r.merchant]) {
                        merchantMap[r.merchant] = { count: 0, amount: 0 };
                    }
                    merchantMap[r.merchant].count++;
                    merchantMap[r.merchant].amount += parseFloat(r.total) || 0;
                }
            });
            
            const topMerchants = Object.entries(merchantMap)
                .map(([name, data]) => ({ name, ...data }))
                .sort((a, b) => b.amount - a.amount)
                .slice(0, 10);
            
            return {
                total,
                totalAmount,
                avgAmount,
                byMonth,
                byCategory,
                topMerchants
            };
        }

        /**
         * Generate unique ID
         */
        generateId() {
            // Use crypto.getRandomValues for better security if available
            if (window.crypto && window.crypto.getRandomValues) {
                const array = new Uint32Array(2);
                window.crypto.getRandomValues(array);
                return 'receipt_' + Date.now() + '_' + Array.from(array).map(n => n.toString(36)).join('');
            }
            // Fallback to Math.random
            return 'receipt_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        }

        /**
         * Clear all data
         */
        clearAll() {
            if (confirm('Are you sure you want to delete all receipts? This cannot be undone.')) {
                this.receipts = [];
                this.filteredReceipts = [];
                this.saveToStorage();
                this.updatePagination();
                this.emit('dataCleared');
                return true;
            }
            return false;
        }

        /**
         * Import data
         */
        async importData(file) {
            return new Promise((resolve, reject) => {
                const reader = new FileReader();
                
                reader.onload = (e) => {
                    try {
                        const data = JSON.parse(e.target.result);
                        
                        if (!Array.isArray(data)) {
                            reject(new Error('Invalid data format'));
                            return;
                        }
                        
                        // Validate and add receipts
                        let imported = 0;
                        data.forEach(item => {
                            if (item && typeof item === 'object') {
                                this.addReceipt(item);
                                imported++;
                            }
                        });
                        
                        resolve({ imported, total: data.length });
                    } catch (error) {
                        reject(error);
                    }
                };
                
                reader.onerror = () => reject(new Error('Failed to read file'));
                reader.readAsText(file);
            });
        }

        /**
         * Event emitter
         */
        on(event, callback) {
            if (!this.listeners.has(event)) {
                this.listeners.set(event, new Set());
            }
            this.listeners.get(event).add(callback);
        }

        off(event, callback) {
            if (this.listeners.has(event)) {
                this.listeners.get(event).delete(callback);
            }
        }

        emit(event, data) {
            if (this.listeners.has(event)) {
                this.listeners.get(event).forEach(callback => {
                    try {
                        callback(data);
                    } catch (error) {
                        console.error(`[DataManager] Error in event listener for ${event}:`, error);
                    }
                });
            }
        }
    }

    // Create global instance
    window.DataManager = new DataManager();
    
    // Export for ES6 modules
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = DataManager;
    }

})(window);
