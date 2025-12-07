/**
 * Batch Processing Manager
 * Handles batch upload and processing of multiple receipts with queue management
 */

class BatchProcessor {
    constructor(apiClient) {
        this.apiClient = apiClient;
        this.queue = [];
        this.processing = [];
        this.completed = [];
        this.failed = [];
        this.maxConcurrent = 3;
        this.isProcessing = false;
        this.isPaused = false;
        this.listeners = new Set();
        this.progressListeners = new Set();
    }

    /**
     * Add files to batch queue
     */
    addFiles(files) {
        const fileArray = Array.isArray(files) ? files : Array.from(files);
        
        const items = fileArray.map((file, index) => ({
            id: `batch_${Date.now()}_${index}`,
            file,
            status: 'queued',
            progress: 0,
            result: null,
            error: null,
            startTime: null,
            endTime: null
        }));

        this.queue.push(...items);
        this.notifyListeners();

        // Auto-start processing
        if (!this.isProcessing && !this.isPaused) {
            this.start();
        }

        return items.map(item => item.id);
    }

    /**
     * Start batch processing
     */
    async start() {
        if (this.isProcessing) return;
        
        this.isProcessing = true;
        this.isPaused = false;
        this.notifyListeners();

        while (this.queue.length > 0 && !this.isPaused) {
            // Process items up to max concurrent
            while (this.processing.length < this.maxConcurrent && this.queue.length > 0) {
                const item = this.queue.shift();
                this.processItem(item);
            }

            // Wait for at least one to finish
            if (this.processing.length > 0) {
                await this.waitForSlot();
            }
        }

        this.isProcessing = false;
        this.notifyListeners();

        // Check if all completed
        if (this.queue.length === 0 && this.processing.length === 0) {
            this.onBatchComplete();
        }
    }

    /**
     * Process single item
     */
    async processItem(item) {
        item.status = 'processing';
        item.startTime = Date.now();
        this.processing.push(item);
        this.notifyListeners();

        try {
            // Upload and extract
            const result = await this.uploadAndExtract(item);
            
            if (result.success) {
                item.status = 'completed';
                item.result = result.data;
                item.progress = 100;
                this.completed.push(item);
            } else {
                item.status = 'failed';
                item.error = result.error || 'Processing failed';
                this.failed.push(item);
            }
        } catch (error) {
            item.status = 'failed';
            item.error = error.message || 'Unknown error';
            this.failed.push(item);
        } finally {
            item.endTime = Date.now();
            
            // Remove from processing
            const index = this.processing.indexOf(item);
            if (index !== -1) {
                this.processing.splice(index, 1);
            }

            this.notifyListeners();
        }
    }

    /**
     * Upload and extract receipt
     */
    async uploadAndExtract(item) {
        try {
            const formData = new FormData();
            formData.append('image', item.file);

            // Track progress
            const xhr = new XMLHttpRequest();
            
            return new Promise((resolve, reject) => {
                xhr.upload.addEventListener('progress', (e) => {
                    if (e.lengthComputable) {
                        item.progress = Math.round((e.loaded / e.total) * 50); // Upload is 50%
                        this.notifyProgressListeners(item);
                    }
                });

                xhr.addEventListener('load', () => {
                    if (xhr.status >= 200 && xhr.status < 300) {
                        try {
                            const response = JSON.parse(xhr.responseText);
                            item.progress = 100;
                            this.notifyProgressListeners(item);
                            resolve({ success: true, data: response });
                        } catch (error) {
                            reject(new Error('Invalid response format'));
                        }
                    } else {
                        try {
                            const response = JSON.parse(xhr.responseText);
                            reject(new Error(response.error || 'Upload failed'));
                        } catch (error) {
                            reject(new Error(`Upload failed with status ${xhr.status}`));
                        }
                    }
                });

                xhr.addEventListener('error', () => {
                    reject(new Error('Network error'));
                });

                xhr.addEventListener('abort', () => {
                    reject(new Error('Upload cancelled'));
                });

                // Set up request
                const apiUrl = this.apiClient.buildURL('/api/extract');
                xhr.open('POST', apiUrl);
                
                // Add auth header if available
                if (this.apiClient.authManager) {
                    const token = this.apiClient.authManager.getAccessToken();
                    if (token) {
                        xhr.setRequestHeader('Authorization', `Bearer ${token}`);
                    }
                }

                xhr.send(formData);
            });
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    /**
     * Wait for processing slot
     */
    waitForSlot() {
        return new Promise(resolve => {
            const checkSlot = () => {
                if (this.processing.length < this.maxConcurrent || this.isPaused) {
                    resolve();
                } else {
                    setTimeout(checkSlot, 100);
                }
            };
            checkSlot();
        });
    }

    /**
     * Pause batch processing
     */
    pause() {
        this.isPaused = true;
        this.notifyListeners();
    }

    /**
     * Resume batch processing
     */
    resume() {
        if (this.isPaused) {
            this.isPaused = false;
            this.start();
        }
    }

    /**
     * Cancel batch processing
     */
    cancel() {
        this.isPaused = true;
        this.isProcessing = false;
        
        // Move queued items to failed
        this.queue.forEach(item => {
            item.status = 'cancelled';
            item.error = 'Cancelled by user';
            this.failed.push(item);
        });
        
        this.queue = [];
        this.notifyListeners();
    }

    /**
     * Clear completed/failed items
     */
    clear() {
        this.completed = [];
        this.failed = [];
        this.notifyListeners();
    }

    /**
     * Reset batch processor
     */
    reset() {
        this.cancel();
        this.clear();
        this.processing = [];
    }

    /**
     * Retry failed items
     */
    retryFailed() {
        const failedItems = [...this.failed];
        this.failed = [];
        
        failedItems.forEach(item => {
            item.status = 'queued';
            item.progress = 0;
            item.error = null;
            item.result = null;
            this.queue.push(item);
        });

        this.notifyListeners();
        this.start();
    }

    /**
     * Retry specific item
     */
    retryItem(itemId) {
        const item = this.failed.find(i => i.id === itemId);
        if (item) {
            item.status = 'queued';
            item.progress = 0;
            item.error = null;
            item.result = null;
            
            const index = this.failed.indexOf(item);
            this.failed.splice(index, 1);
            
            this.queue.push(item);
            this.notifyListeners();
            this.start();
        }
    }

    /**
     * Remove item from queue
     */
    removeItem(itemId) {
        // Check queue
        let index = this.queue.findIndex(i => i.id === itemId);
        if (index !== -1) {
            this.queue.splice(index, 1);
            this.notifyListeners();
            return true;
        }

        // Check completed
        index = this.completed.findIndex(i => i.id === itemId);
        if (index !== -1) {
            this.completed.splice(index, 1);
            this.notifyListeners();
            return true;
        }

        // Check failed
        index = this.failed.findIndex(i => i.id === itemId);
        if (index !== -1) {
            this.failed.splice(index, 1);
            this.notifyListeners();
            return true;
        }

        return false;
    }

    /**
     * Get batch statistics
     */
    getStats() {
        const total = this.queue.length + this.processing.length + this.completed.length + this.failed.length;
        const completedCount = this.completed.length;
        const failedCount = this.failed.length;
        const processingCount = this.processing.length;
        const queuedCount = this.queue.length;

        return {
            total,
            queued: queuedCount,
            processing: processingCount,
            completed: completedCount,
            failed: failedCount,
            progress: total > 0 ? Math.round((completedCount / total) * 100) : 0,
            successRate: (completedCount + failedCount) > 0 
                ? Math.round((completedCount / (completedCount + failedCount)) * 100)
                : 0
        };
    }

    /**
     * Get all items
     */
    getAllItems() {
        return {
            queue: [...this.queue],
            processing: [...this.processing],
            completed: [...this.completed],
            failed: [...this.failed]
        };
    }

    /**
     * Get item by ID
     */
    getItem(itemId) {
        return [...this.queue, ...this.processing, ...this.completed, ...this.failed]
            .find(item => item.id === itemId);
    }

    /**
     * Export results
     */
    exportResults(format = 'json') {
        const results = this.completed.map(item => item.result);
        
        let content, mimeType, extension;

        if (format === 'json') {
            content = JSON.stringify(results, null, 2);
            mimeType = 'application/json';
            extension = 'json';
        } else if (format === 'csv') {
            content = this.convertToCSV(results);
            mimeType = 'text/csv';
            extension = 'csv';
        }

        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `batch_results_${new Date().toISOString().split('T')[0]}.${extension}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    /**
     * Convert results to CSV
     */
    convertToCSV(results) {
        if (results.length === 0) return '';

        // Get all unique keys
        const keys = new Set();
        results.forEach(result => {
            Object.keys(result).forEach(key => keys.add(key));
        });

        const headers = Array.from(keys);
        const rows = results.map(result => {
            return headers.map(header => {
                const value = result[header];
                if (value === null || value === undefined) return '';
                if (typeof value === 'object') return JSON.stringify(value);
                return `"${String(value).replace(/"/g, '""')}"`;
            }).join(',');
        });

        return [headers.join(','), ...rows].join('\n');
    }

    /**
     * Subscribe to batch changes
     */
    subscribe(listener) {
        this.listeners.add(listener);
        return () => {
            this.listeners.delete(listener);
        };
    }

    /**
     * Subscribe to progress updates
     */
    subscribeToProgress(listener) {
        this.progressListeners.add(listener);
        return () => {
            this.progressListeners.delete(listener);
        };
    }

    /**
     * Notify listeners
     */
    notifyListeners() {
        const stats = this.getStats();
        const items = this.getAllItems();
        
        this.listeners.forEach(listener => {
            try {
                listener(stats, items);
            } catch (error) {
                console.error('Error in batch listener:', error);
            }
        });
    }

    /**
     * Notify progress listeners
     */
    notifyProgressListeners(item) {
        this.progressListeners.forEach(listener => {
            try {
                listener(item);
            } catch (error) {
                console.error('Error in progress listener:', error);
            }
        });
    }

    /**
     * Batch complete callback
     */
    onBatchComplete() {
        const stats = this.getStats();
        console.log('Batch processing complete:', stats);
        
        // Custom completion handler can be set
        if (this.onComplete) {
            this.onComplete(stats);
        }
    }

    /**
     * Set max concurrent uploads
     */
    setMaxConcurrent(max) {
        this.maxConcurrent = Math.max(1, Math.min(10, max));
    }

    /**
     * Get processing state
     */
    getState() {
        return {
            isProcessing: this.isProcessing,
            isPaused: this.isPaused,
            maxConcurrent: this.maxConcurrent
        };
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BatchProcessor;
}
