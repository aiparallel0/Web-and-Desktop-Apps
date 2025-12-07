/**
 * Receipt Manager
 * Manages receipt history, CRUD operations, and export
 */

class ReceiptManager {
    constructor(apiClient, authManager) {
        this.apiClient = apiClient;
        this.authManager = authManager;
        this.receipts = [];
        this.filters = {
            search: '',
            dateFrom: null,
            dateTo: null,
            minAmount: null,
            maxAmount: null,
            merchant: '',
            sortBy: 'date',
            sortOrder: 'desc'
        };
        this.pagination = {
            page: 1,
            perPage: 20,
            total: 0,
            totalPages: 0
        };
        this.listeners = new Set();
    }

    /**
     * Fetch receipts from server
     */
    async fetchReceipts(options = {}) {
        try {
            const params = new URLSearchParams({
                page: options.page || this.pagination.page,
                per_page: options.perPage || this.pagination.perPage,
                sort_by: options.sortBy || this.filters.sortBy,
                sort_order: options.sortOrder || this.filters.sortOrder,
                ...this.buildFilterParams()
            });

            const response = await this.apiClient.get(
                `/api/receipts?${params}`,
                { auth: true }
            );

            if (response.success) {
                this.receipts = response.data.receipts;
                this.pagination = {
                    page: response.data.page,
                    perPage: response.data.per_page,
                    total: response.data.total,
                    totalPages: response.data.total_pages
                };
                this.notifyListeners();
                return { success: true, receipts: this.receipts };
            }

            return response;
        } catch (error) {
            console.error('Error fetching receipts:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Build filter parameters
     */
    buildFilterParams() {
        const params = {};

        if (this.filters.search) {
            params.search = this.filters.search;
        }
        if (this.filters.dateFrom) {
            params.date_from = this.filters.dateFrom;
        }
        if (this.filters.dateTo) {
            params.date_to = this.filters.dateTo;
        }
        if (this.filters.minAmount) {
            params.min_amount = this.filters.minAmount;
        }
        if (this.filters.maxAmount) {
            params.max_amount = this.filters.maxAmount;
        }
        if (this.filters.merchant) {
            params.merchant = this.filters.merchant;
        }

        return params;
    }

    /**
     * Get single receipt
     */
    async getReceipt(id) {
        try {
            const response = await this.apiClient.get(
                `/api/receipts/${id}`,
                { auth: true }
            );

            if (response.success) {
                return { success: true, receipt: response.data.receipt };
            }

            return response;
        } catch (error) {
            console.error('Error fetching receipt:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Create receipt
     */
    async createReceipt(receiptData) {
        try {
            const response = await this.apiClient.post(
                '/api/receipts',
                receiptData,
                { auth: true }
            );

            if (response.success) {
                this.receipts.unshift(response.data.receipt);
                this.pagination.total++;
                this.notifyListeners();
                return { success: true, receipt: response.data.receipt };
            }

            return response;
        } catch (error) {
            console.error('Error creating receipt:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Update receipt
     */
    async updateReceipt(id, updates) {
        try {
            const response = await this.apiClient.patch(
                `/api/receipts/${id}`,
                updates,
                { auth: true }
            );

            if (response.success) {
                const index = this.receipts.findIndex(r => r.id === id);
                if (index !== -1) {
                    this.receipts[index] = { ...this.receipts[index], ...response.data.receipt };
                }
                this.notifyListeners();
                return { success: true, receipt: response.data.receipt };
            }

            return response;
        } catch (error) {
            console.error('Error updating receipt:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Delete receipt
     */
    async deleteReceipt(id) {
        try {
            const response = await this.apiClient.delete(
                `/api/receipts/${id}`,
                { auth: true }
            );

            if (response.success) {
                this.receipts = this.receipts.filter(r => r.id !== id);
                this.pagination.total--;
                this.notifyListeners();
                return { success: true };
            }

            return response;
        } catch (error) {
            console.error('Error deleting receipt:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Bulk delete receipts
     */
    async bulkDelete(ids) {
        try {
            const response = await this.apiClient.post(
                '/api/receipts/bulk-delete',
                { ids },
                { auth: true }
            );

            if (response.success) {
                this.receipts = this.receipts.filter(r => !ids.includes(r.id));
                this.pagination.total -= ids.length;
                this.notifyListeners();
                return { success: true };
            }

            return response;
        } catch (error) {
            console.error('Error bulk deleting receipts:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Export receipt
     */
    async exportReceipt(id, format = 'json') {
        try {
            const response = await this.apiClient.download(
                `/api/receipts/${id}/export?format=${format}`,
                `receipt_${id}.${format}`,
                { auth: true }
            );

            return response;
        } catch (error) {
            console.error('Error exporting receipt:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Export multiple receipts
     */
    async exportReceipts(ids, format = 'csv') {
        try {
            const response = await this.apiClient.post(
                '/api/receipts/export',
                { ids, format },
                { auth: true, responseType: 'blob' }
            );

            if (response.success) {
                const filename = `receipts_${new Date().toISOString().split('T')[0]}.${format}`;
                await this.apiClient.download(response.data, filename);
                return { success: true };
            }

            return response;
        } catch (error) {
            console.error('Error exporting receipts:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Get receipt statistics
     */
    async getStats() {
        try {
            const response = await this.apiClient.get(
                '/api/receipts/stats',
                { auth: true }
            );

            if (response.success) {
                return { success: true, stats: response.data };
            }

            return response;
        } catch (error) {
            console.error('Error fetching receipt stats:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Search receipts
     */
    async search(query) {
        this.filters.search = query;
        this.pagination.page = 1;
        return this.fetchReceipts();
    }

    /**
     * Filter receipts
     */
    async filter(filters) {
        this.filters = { ...this.filters, ...filters };
        this.pagination.page = 1;
        return this.fetchReceipts();
    }

    /**
     * Sort receipts
     */
    async sort(sortBy, sortOrder = 'asc') {
        this.filters.sortBy = sortBy;
        this.filters.sortOrder = sortOrder;
        return this.fetchReceipts();
    }

    /**
     * Go to page
     */
    async goToPage(page) {
        this.pagination.page = page;
        return this.fetchReceipts();
    }

    /**
     * Next page
     */
    async nextPage() {
        if (this.pagination.page < this.pagination.totalPages) {
            this.pagination.page++;
            return this.fetchReceipts();
        }
    }

    /**
     * Previous page
     */
    async previousPage() {
        if (this.pagination.page > 1) {
            this.pagination.page--;
            return this.fetchReceipts();
        }
    }

    /**
     * Clear filters
     */
    clearFilters() {
        this.filters = {
            search: '',
            dateFrom: null,
            dateTo: null,
            minAmount: null,
            maxAmount: null,
            merchant: '',
            sortBy: 'date',
            sortOrder: 'desc'
        };
        this.pagination.page = 1;
        return this.fetchReceipts();
    }

    /**
     * Get local receipts
     */
    getReceipts() {
        return [...this.receipts];
    }

    /**
     * Get pagination info
     */
    getPagination() {
        return { ...this.pagination };
    }

    /**
     * Get filters
     */
    getFilters() {
        return { ...this.filters };
    }

    /**
     * Subscribe to changes
     */
    subscribe(listener) {
        this.listeners.add(listener);
        return () => {
            this.listeners.delete(listener);
        };
    }

    /**
     * Notify listeners
     */
    notifyListeners() {
        this.listeners.forEach(listener => {
            try {
                listener(this.receipts, this.pagination, this.filters);
            } catch (error) {
                console.error('Error in receipt listener:', error);
            }
        });
    }

    /**
     * Get receipt by ID (local)
     */
    getReceiptById(id) {
        return this.receipts.find(r => r.id === id);
    }

    /**
     * Calculate totals
     */
    calculateTotals(receipts = this.receipts) {
        return receipts.reduce((acc, receipt) => {
            const total = parseFloat(receipt.total || 0);
            return acc + total;
        }, 0);
    }

    /**
     * Group receipts by merchant
     */
    groupByMerchant(receipts = this.receipts) {
        return receipts.reduce((acc, receipt) => {
            const merchant = receipt.merchant || 'Unknown';
            if (!acc[merchant]) {
                acc[merchant] = [];
            }
            acc[merchant].push(receipt);
            return acc;
        }, {});
    }

    /**
     * Group receipts by date
     */
    groupByDate(receipts = this.receipts) {
        return receipts.reduce((acc, receipt) => {
            const date = receipt.date ? receipt.date.split('T')[0] : 'Unknown';
            if (!acc[date]) {
                acc[date] = [];
            }
            acc[date].push(receipt);
            return acc;
        }, {});
    }

    /**
     * Get date range statistics
     */
    getDateRangeStats(dateFrom, dateTo, receipts = this.receipts) {
        const filtered = receipts.filter(r => {
            if (!r.date) return false;
            const receiptDate = new Date(r.date);
            return receiptDate >= new Date(dateFrom) && receiptDate <= new Date(dateTo);
        });

        return {
            count: filtered.length,
            total: this.calculateTotals(filtered),
            receipts: filtered
        };
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ReceiptManager;
}
