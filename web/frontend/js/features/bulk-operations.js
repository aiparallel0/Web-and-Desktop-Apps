/**
 * Bulk Operations Manager
 * Handles batch operations on multiple items
 */

import apiClient from '../core/api-client.js';
import modalSystem from '../components/modal-system.js';
import toastSystem from '../components/toast-system.js';
import eventBus from '../core/event-bus.js';

class BulkOperationsManager {
    constructor() {
        this.operations = new Map();
        this.queue = [];
        this.processing = false;
        this.maxConcurrent = 5;
        this.retryAttempts = 3;
    }

    /**
     * Register bulk operation
     */
    registerOperation(id, config) {
        this.operations.set(id, {
            id,
            name: config.name,
            description: config.description,
            icon: config.icon,
            handler: config.handler,
            confirmMessage: config.confirmMessage,
            requiresConfirmation: config.requiresConfirmation !== false,
            validate: config.validate
        });
    }

    /**
     * Execute bulk operation
     */
    async execute(operationId, items, options = {}) {
        const operation = this.operations.get(operationId);
        if (!operation) {
            throw new Error(`Operation ${operationId} not found`);
        }

        // Validate items
        if (operation.validate) {
            const validation = operation.validate(items);
            if (!validation.valid) {
                toastSystem.error(validation.message);
                return;
            }
        }

        // Confirm if required
        if (operation.requiresConfirmation) {
            const confirmMsg = typeof operation.confirmMessage === 'function'
                ? operation.confirmMessage(items)
                : operation.confirmMessage || `Are you sure you want to ${operation.name.toLowerCase()} ${items.length} items?`;

            const confirmed = await modalSystem.confirm(confirmMsg, {
                title: operation.name,
                confirmLabel: 'Continue',
                confirmClass: 'btn btn-primary'
            });

            if (!confirmed) return;
        }

        // Execute operation
        const toastId = toastSystem.loading(`${operation.name} in progress...`);

        try {
            const results = await this.processBatch(items, operation.handler, options);

            toastSystem.remove(toastId);

            const succeeded = results.filter(r => r.success).length;
            const failed = results.filter(r => !r.success).length;

            if (failed === 0) {
                toastSystem.success(`${operation.name} completed successfully for ${succeeded} items`);
            } else {
                toastSystem.warning(`${operation.name} completed: ${succeeded} succeeded, ${failed} failed`);
            }

            // Emit event
            eventBus.emit('bulk:operation:complete', {
                operationId,
                results,
                succeeded,
                failed
            });

            return results;

        } catch (error) {
            toastSystem.remove(toastId);
            toastSystem.error(`${operation.name} failed: ${error.message}`);
            throw error;
        }
    }

    /**
     * Process batch of items
     */
    async processBatch(items, handler, options = {}) {
        const {
            concurrent = this.maxConcurrent,
            retries = this.retryAttempts,
            onProgress = null
        } = options;

        const results = [];
        const queue = [...items];
        let completed = 0;
        let processing = 0;

        return new Promise((resolve, reject) => {
            const processNext = async () => {
                if (queue.length === 0 && processing === 0) {
                    resolve(results);
                    return;
                }

                while (queue.length > 0 && processing < concurrent) {
                    const item = queue.shift();
                    processing++;

                    this.processItem(item, handler, retries)
                        .then(result => {
                            results.push(result);
                            completed++;
                            processing--;

                            if (onProgress) {
                                onProgress(completed, items.length);
                            }

                            processNext();
                        })
                        .catch(error => {
                            results.push({
                                item,
                                success: false,
                                error: error.message
                            });
                            completed++;
                            processing--;

                            if (onProgress) {
                                onProgress(completed, items.length);
                            }

                            processNext();
                        });
                }
            };

            processNext();
        });
    }

    /**
     * Process single item with retries
     */
    async processItem(item, handler, maxRetries) {
        let lastError;

        for (let attempt = 0; attempt <= maxRetries; attempt++) {
            try {
                const result = await handler(item);
                return {
                    item,
                    success: true,
                    result
                };
            } catch (error) {
                lastError = error;

                if (attempt < maxRetries) {
                    await this.delay(Math.pow(2, attempt) * 1000);
                }
            }
        }

        return {
            item,
            success: false,
            error: lastError.message
        };
    }

    /**
     * Delay helper
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Delete items in bulk
     */
    async bulkDelete(items, endpoint = '/api/bulk-delete') {
        return this.execute('delete', items, {
            onProgress: (completed, total) => {
                console.log(`Deleting: ${completed}/${total}`);
            }
        });
    }

    /**
     * Update items in bulk
     */
    async bulkUpdate(items, updates, endpoint = '/api/bulk-update') {
        return this.execute('update', items, {
            handler: async (item) => {
                return apiClient.request(endpoint, {
                    method: 'PUT',
                    body: JSON.stringify({
                        id: item.id,
                        updates
                    })
                });
            }
        });
    }

    /**
     * Export items in bulk
     */
    async bulkExport(items, format = 'json') {
        const ids = items.filter(item => item && item.id).map(item => item.id);
        if (ids.length === 0) {
            throw new Error('No valid items to export');
        }
        return apiClient.exportData(ids, format);
    }

    /**
     * Move items to folder/category
     */
    async bulkMove(items, targetId) {
        return this.execute('move', items, {
            handler: async (item) => {
                return apiClient.request(`/api/items/${item.id}/move`, {
                    method: 'POST',
                    body: JSON.stringify({ targetId })
                });
            }
        });
    }

    /**
     * Tag items
     */
    async bulkTag(items, tags) {
        return this.execute('tag', items, {
            handler: async (item) => {
                return apiClient.request(`/api/items/${item.id}/tags`, {
                    method: 'POST',
                    body: JSON.stringify({ tags })
                });
            }
        });
    }

    /**
     * Archive items
     */
    async bulkArchive(items) {
        return this.execute('archive', items, {
            handler: async (item) => {
                return apiClient.request(`/api/items/${item.id}/archive`, {
                    method: 'POST'
                });
            }
        });
    }

    /**
     * Restore items
     */
    async bulkRestore(items) {
        return this.execute('restore', items, {
            handler: async (item) => {
                return apiClient.request(`/api/items/${item.id}/restore`, {
                    method: 'POST'
                });
            }
        });
    }

    /**
     * Show bulk operation dialog
     */
    showBulkDialog(items, availableOperations = []) {
        const content = `
            <div class="bulk-operations-dialog">
                <p class="bulk-info">${items.length} items selected</p>
                
                <div class="bulk-operations-list">
                    ${availableOperations.map(opId => {
                        const op = this.operations.get(opId);
                        if (!op) return '';

                        return `
                            <button class="bulk-operation-btn" data-operation="${opId}">
                                <span class="operation-icon">${op.icon || '•'}</span>
                                <span class="operation-name">${op.name}</span>
                                ${op.description ? `<span class="operation-desc">${op.description}</span>` : ''}
                            </button>
                        `;
                    }).join('')}
                </div>
            </div>
        `;

        const modalId = modalSystem.open('bulk-operations', content, {
            title: 'Bulk Operations',
            size: 'medium'
        });

        setTimeout(() => {
            const modal = document.querySelector(`[data-modal-id="${modalId}"]`);
            if (!modal) return;

            modal.querySelectorAll('.bulk-operation-btn').forEach(btn => {
                btn.addEventListener('click', async () => {
                    const operationId = btn.dataset.operation;
                    modalSystem.close(modalId);
                    await this.execute(operationId, items);
                });
            });
        }, 100);
    }

    /**
     * Get operation
     */
    getOperation(id) {
        return this.operations.get(id);
    }

    /**
     * Get all operations
     */
    getAllOperations() {
        return Array.from(this.operations.values());
    }
}

// Create singleton
const bulkOperationsManager = new BulkOperationsManager();

// Register default operations
bulkOperationsManager.registerOperation('delete', {
    name: 'Delete',
    description: 'Permanently delete selected items',
    icon: '🗑️',
    confirmMessage: (items) => `Are you sure you want to delete ${items.length} items? This cannot be undone.`,
    handler: async (item) => {
        return apiClient.request(`/api/items/${item.id}`, {
            method: 'DELETE'
        });
    }
});

bulkOperationsManager.registerOperation('archive', {
    name: 'Archive',
    description: 'Move items to archive',
    icon: '📦',
    handler: async (item) => {
        return apiClient.request(`/api/items/${item.id}/archive`, {
            method: 'POST'
        });
    }
});

bulkOperationsManager.registerOperation('export', {
    name: 'Export',
    description: 'Export items to file',
    icon: '📥',
    requiresConfirmation: false,
    handler: async (item) => {
        return { success: true, item };
    }
});

// Expose globally
if (typeof window !== 'undefined') {
    window.bulkOperationsManager = bulkOperationsManager;
    window.BulkOperationsManager = BulkOperationsManager;
}

export default bulkOperationsManager;
