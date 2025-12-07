/**
 * File Upload Manager
 * Handles file uploads with progress tracking, validation, and preview
 * @version 2.0.0
 */

(function(window) {
    'use strict';

    class FileUploadManager {
        constructor(options = {}) {
            this.options = {
                maxFileSize: options.maxFileSize || 100 * 1024 * 1024, // 100MB
                allowedTypes: options.allowedTypes || ['image/*', 'application/pdf'],
                multiple: options.multiple !== false,
                autoUpload: options.autoUpload !== false,
                chunkSize: options.chunkSize || 1024 * 1024, // 1MB chunks
                maxConcurrent: options.maxConcurrent || 3,
                endpoint: options.endpoint || '/api/upload',
                ...options
            };

            this.files = new Map();
            this.queue = [];
            this.activeUploads = 0;
            this.listeners = new Map();
        }

        /**
         * Select files
         */
        async selectFiles() {
            return new Promise((resolve) => {
                const input = document.createElement('input');
                input.type = 'file';
                input.multiple = this.options.multiple;
                input.accept = this.options.allowedTypes.join(',');

                input.addEventListener('change', (e) => {
                    const files = Array.from(e.target.files);
                    resolve(files);
                });

                input.click();
            });
        }

        /**
         * Add files to upload queue
         */
        async addFiles(files) {
            const fileArray = Array.isArray(files) ? files : [files];
            const validFiles = [];

            for (const file of fileArray) {
                const validation = this.validateFile(file);
                
                if (validation.valid) {
                    const fileId = this.generateFileId(file);
                    const fileInfo = {
                        id: fileId,
                        file: file,
                        name: file.name,
                        size: file.size,
                        type: file.type,
                        progress: 0,
                        status: 'pending', // pending, uploading, completed, failed, cancelled
                        error: null,
                        preview: null,
                        uploadedBytes: 0,
                        startTime: null,
                        endTime: null,
                        speed: 0,
                        estimatedTimeRemaining: 0
                    };

                    // Generate preview if it's an image
                    if (file.type.startsWith('image/')) {
                        fileInfo.preview = await this.generatePreview(file);
                    }

                    this.files.set(fileId, fileInfo);
                    this.queue.push(fileId);
                    validFiles.push(fileInfo);

                    this.emit('fileAdded', fileInfo);
                } else {
                    this.emit('fileValidationFailed', { file, errors: validation.errors });
                }
            }

            // Auto-upload if enabled
            if (this.options.autoUpload && validFiles.length > 0) {
                this.processQueue();
            }

            return validFiles;
        }

        /**
         * Validate file
         */
        validateFile(file) {
            const errors = [];

            // Check file size
            if (file.size > this.options.maxFileSize) {
                errors.push(`File size exceeds maximum allowed size of ${this.formatFileSize(this.options.maxFileSize)}`);
            }

            if (file.size === 0) {
                errors.push('File is empty');
            }

            // Check file type
            const allowedTypes = this.options.allowedTypes;
            const isAllowed = allowedTypes.some(type => {
                if (type.endsWith('/*')) {
                    const category = type.split('/')[0];
                    return file.type.startsWith(category + '/');
                }
                return file.type === type;
            });

            if (!isAllowed) {
                errors.push(`File type ${file.type} is not allowed`);
            }

            // Check file name
            if (!/^[\w\-. ]+\.[a-zA-Z0-9]+$/.test(file.name)) {
                errors.push('File name contains invalid characters');
            }

            return {
                valid: errors.length === 0,
                errors
            };
        }

        /**
         * Generate file preview
         */
        async generatePreview(file) {
            return new Promise((resolve) => {
                const reader = new FileReader();
                
                reader.onload = (e) => {
                    resolve(e.target.result);
                };

                reader.onerror = () => {
                    resolve(null);
                };

                reader.readAsDataURL(file);
            });
        }

        /**
         * Process upload queue
         */
        async processQueue() {
            while (this.queue.length > 0 && this.activeUploads < this.options.maxConcurrent) {
                const fileId = this.queue.shift();
                const fileInfo = this.files.get(fileId);

                if (fileInfo && fileInfo.status === 'pending') {
                    this.uploadFile(fileId);
                }
            }
        }

        /**
         * Upload file
         */
        async uploadFile(fileId) {
            const fileInfo = this.files.get(fileId);
            if (!fileInfo) return;

            this.activeUploads++;
            fileInfo.status = 'uploading';
            fileInfo.startTime = Date.now();

            this.emit('uploadStart', fileInfo);

            try {
                // Choose upload method based on file size
                if (fileInfo.size > this.options.chunkSize * 10) {
                    await this.chunkedUpload(fileId);
                } else {
                    await this.simpleUpload(fileId);
                }

                fileInfo.status = 'completed';
                fileInfo.endTime = Date.now();
                fileInfo.progress = 100;

                this.emit('uploadComplete', fileInfo);
            } catch (error) {
                fileInfo.status = 'failed';
                fileInfo.error = error.message;

                this.emit('uploadFailed', { fileInfo, error });
            } finally {
                this.activeUploads--;
                this.processQueue();
            }
        }

        /**
         * Simple upload (entire file)
         */
        async simpleUpload(fileId) {
            const fileInfo = this.files.get(fileId);
            const formData = new FormData();
            formData.append('file', fileInfo.file);

            return new Promise((resolve, reject) => {
                const xhr = new XMLHttpRequest();

                // Store xhr for cancellation
                fileInfo.xhr = xhr;

                // Progress tracking
                xhr.upload.addEventListener('progress', (e) => {
                    if (e.lengthComputable) {
                        fileInfo.progress = (e.loaded / e.total) * 100;
                        fileInfo.uploadedBytes = e.loaded;
                        
                        // Calculate upload speed
                        const elapsed = (Date.now() - fileInfo.startTime) / 1000;
                        fileInfo.speed = e.loaded / elapsed;
                        
                        // Estimate remaining time
                        const remaining = e.total - e.loaded;
                        fileInfo.estimatedTimeRemaining = remaining / fileInfo.speed;

                        this.emit('uploadProgress', fileInfo);
                    }
                });

                xhr.addEventListener('load', () => {
                    if (xhr.status >= 200 && xhr.status < 300) {
                        try {
                            const response = JSON.parse(xhr.responseText);
                            fileInfo.response = response;
                            resolve(response);
                        } catch (error) {
                            reject(new Error('Invalid server response'));
                        }
                    } else {
                        reject(new Error(`Upload failed with status ${xhr.status}`));
                    }
                });

                xhr.addEventListener('error', () => {
                    reject(new Error('Network error occurred'));
                });

                xhr.addEventListener('abort', () => {
                    reject(new Error('Upload cancelled'));
                });

                xhr.open('POST', this.options.endpoint);
                
                // Add auth token if available
                const token = localStorage.getItem('access_token');
                if (token) {
                    xhr.setRequestHeader('Authorization', `Bearer ${token}`);
                }

                xhr.send(formData);
            });
        }

        /**
         * Chunked upload (for large files)
         */
        async chunkedUpload(fileId) {
            const fileInfo = this.files.get(fileId);
            const file = fileInfo.file;
            const chunkSize = this.options.chunkSize;
            const totalChunks = Math.ceil(file.size / chunkSize);

            fileInfo.totalChunks = totalChunks;
            fileInfo.uploadedChunks = 0;

            for (let chunkIndex = 0; chunkIndex < totalChunks; chunkIndex++) {
                // Check if cancelled
                if (fileInfo.status === 'cancelled') {
                    throw new Error('Upload cancelled');
                }

                const start = chunkIndex * chunkSize;
                const end = Math.min(start + chunkSize, file.size);
                const chunk = file.slice(start, end);

                await this.uploadChunk(fileId, chunk, chunkIndex, totalChunks);

                fileInfo.uploadedChunks++;
                fileInfo.progress = (fileInfo.uploadedChunks / totalChunks) * 100;
                fileInfo.uploadedBytes = end;

                // Calculate speed and ETA
                const elapsed = (Date.now() - fileInfo.startTime) / 1000;
                fileInfo.speed = end / elapsed;
                const remaining = file.size - end;
                fileInfo.estimatedTimeRemaining = remaining / fileInfo.speed;

                this.emit('uploadProgress', fileInfo);
            }

            // Finalize chunked upload
            await this.finalizeChunkedUpload(fileId);
        }

        /**
         * Upload single chunk
         */
        async uploadChunk(fileId, chunk, chunkIndex, totalChunks) {
            const fileInfo = this.files.get(fileId);
            const formData = new FormData();
            formData.append('chunk', chunk);
            formData.append('chunkIndex', chunkIndex);
            formData.append('totalChunks', totalChunks);
            formData.append('fileId', fileId);
            formData.append('fileName', fileInfo.name);

            return new Promise((resolve, reject) => {
                const xhr = new XMLHttpRequest();

                xhr.addEventListener('load', () => {
                    if (xhr.status >= 200 && xhr.status < 300) {
                        resolve();
                    } else {
                        reject(new Error(`Chunk upload failed with status ${xhr.status}`));
                    }
                });

                xhr.addEventListener('error', () => {
                    reject(new Error('Network error occurred'));
                });

                xhr.open('POST', `${this.options.endpoint}/chunk`);
                
                const token = localStorage.getItem('access_token');
                if (token) {
                    xhr.setRequestHeader('Authorization', `Bearer ${token}`);
                }

                xhr.send(formData);
            });
        }

        /**
         * Finalize chunked upload
         */
        async finalizeChunkedUpload(fileId) {
            const fileInfo = this.files.get(fileId);

            return new Promise((resolve, reject) => {
                const xhr = new XMLHttpRequest();

                xhr.addEventListener('load', () => {
                    if (xhr.status >= 200 && xhr.status < 300) {
                        try {
                            const response = JSON.parse(xhr.responseText);
                            fileInfo.response = response;
                            resolve(response);
                        } catch (error) {
                            reject(new Error('Invalid server response'));
                        }
                    } else {
                        reject(new Error(`Finalization failed with status ${xhr.status}`));
                    }
                });

                xhr.addEventListener('error', () => {
                    reject(new Error('Network error occurred'));
                });

                xhr.open('POST', `${this.options.endpoint}/finalize`);
                xhr.setRequestHeader('Content-Type', 'application/json');
                
                const token = localStorage.getItem('access_token');
                if (token) {
                    xhr.setRequestHeader('Authorization', `Bearer ${token}`);
                }

                xhr.send(JSON.stringify({
                    fileId: fileId,
                    fileName: fileInfo.name,
                    totalChunks: fileInfo.totalChunks
                }));
            });
        }

        /**
         * Cancel upload
         */
        cancelUpload(fileId) {
            const fileInfo = this.files.get(fileId);
            if (!fileInfo) return;

            if (fileInfo.xhr) {
                fileInfo.xhr.abort();
            }

            fileInfo.status = 'cancelled';
            this.emit('uploadCancelled', fileInfo);

            // Remove from queue
            const queueIndex = this.queue.indexOf(fileId);
            if (queueIndex !== -1) {
                this.queue.splice(queueIndex, 1);
            }
        }

        /**
         * Retry failed upload
         */
        retryUpload(fileId) {
            const fileInfo = this.files.get(fileId);
            if (!fileInfo || fileInfo.status !== 'failed') return;

            fileInfo.status = 'pending';
            fileInfo.progress = 0;
            fileInfo.uploadedBytes = 0;
            fileInfo.error = null;

            this.queue.push(fileId);
            this.processQueue();
        }

        /**
         * Remove file
         */
        removeFile(fileId) {
            this.cancelUpload(fileId);
            this.files.delete(fileId);
            this.emit('fileRemoved', { fileId });
        }

        /**
         * Get file info
         */
        getFileInfo(fileId) {
            return this.files.get(fileId);
        }

        /**
         * Get all files
         */
        getAllFiles() {
            return Array.from(this.files.values());
        }

        /**
         * Get files by status
         */
        getFilesByStatus(status) {
            return this.getAllFiles().filter(f => f.status === status);
        }

        /**
         * Clear completed uploads
         */
        clearCompleted() {
            const completed = this.getFilesByStatus('completed');
            completed.forEach(file => this.removeFile(file.id));
        }

        /**
         * Clear all files
         */
        clearAll() {
            this.getAllFiles().forEach(file => this.removeFile(file.id));
        }

        /**
         * Get overall progress
         */
        getOverallProgress() {
            const files = this.getAllFiles();
            if (files.length === 0) return 0;

            const totalProgress = files.reduce((sum, file) => sum + file.progress, 0);
            return totalProgress / files.length;
        }

        /**
         * Get upload statistics
         */
        getStatistics() {
            const files = this.getAllFiles();
            
            return {
                total: files.length,
                pending: this.getFilesByStatus('pending').length,
                uploading: this.getFilesByStatus('uploading').length,
                completed: this.getFilesByStatus('completed').length,
                failed: this.getFilesByStatus('failed').length,
                cancelled: this.getFilesByStatus('cancelled').length,
                totalSize: files.reduce((sum, f) => sum + f.size, 0),
                uploadedSize: files.reduce((sum, f) => sum + f.uploadedBytes, 0),
                overallProgress: this.getOverallProgress()
            };
        }

        /**
         * Format file size
         */
        formatFileSize(bytes) {
            if (bytes === 0) return '0 Bytes';

            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));

            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }

        /**
         * Format time
         */
        formatTime(seconds) {
            if (seconds < 60) return `${Math.round(seconds)}s`;
            if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
            return `${Math.round(seconds / 3600)}h`;
        }

        /**
         * Generate file ID
         */
        generateFileId(file) {
            return `file_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        }

        /**
         * Create upload UI
         */
        createUploadUI(containerId) {
            const container = document.getElementById(containerId);
            if (!container) return null;

            // Create drop zone
            const dropZone = document.createElement('div');
            dropZone.className = 'upload-drop-zone';
            dropZone.style.cssText = `
                border: 2px dashed #cbd5e1;
                border-radius: 12px;
                padding: 40px;
                text-align: center;
                background: #f9fafb;
                cursor: pointer;
                transition: all 0.2s;
            `;

            dropZone.innerHTML = `
                <div style="font-size: 48px; margin-bottom: 16px;">📁</div>
                <h3 style="margin: 0 0 8px 0; color: #111827;">Drop files here or click to browse</h3>
                <p style="margin: 0; color: #6b7280; font-size: 14px;">
                    Maximum file size: ${this.formatFileSize(this.options.maxFileSize)}
                </p>
            `;

            // Click to select
            dropZone.addEventListener('click', async () => {
                const files = await this.selectFiles();
                if (files.length > 0) {
                    await this.addFiles(files);
                }
            });

            // Drag and drop
            dropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                dropZone.style.borderColor = '#3b82f6';
                dropZone.style.background = '#dbeafe';
            });

            dropZone.addEventListener('dragleave', () => {
                dropZone.style.borderColor = '#cbd5e1';
                dropZone.style.background = '#f9fafb';
            });

            dropZone.addEventListener('drop', async (e) => {
                e.preventDefault();
                dropZone.style.borderColor = '#cbd5e1';
                dropZone.style.background = '#f9fafb';

                const files = Array.from(e.dataTransfer.files);
                if (files.length > 0) {
                    await this.addFiles(files);
                }
            });

            // File list
            const fileList = document.createElement('div');
            fileList.className = 'upload-file-list';
            fileList.style.cssText = 'margin-top: 24px;';

            container.appendChild(dropZone);
            container.appendChild(fileList);

            // Listen to file events and update UI
            this.on('fileAdded', () => this.updateFileList(fileList));
            this.on('uploadProgress', () => this.updateFileList(fileList));
            this.on('uploadComplete', () => this.updateFileList(fileList));
            this.on('uploadFailed', () => this.updateFileList(fileList));
            this.on('fileRemoved', () => this.updateFileList(fileList));

            return { dropZone, fileList };
        }

        /**
         * Update file list UI
         */
        updateFileList(container) {
            if (!container) return;

            container.innerHTML = '';
            const files = this.getAllFiles();

            files.forEach(file => {
                const fileCard = this.createFileCard(file);
                container.appendChild(fileCard);
            });
        }

        /**
         * Create file card UI
         */
        createFileCard(fileInfo) {
            const card = document.createElement('div');
            card.className = 'file-card';
            card.style.cssText = `
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 16px;
                margin-bottom: 12px;
                display: flex;
                align-items: center;
                gap: 16px;
            `;

            // Preview
            const preview = document.createElement('div');
            preview.style.cssText = `
                width: 48px;
                height: 48px;
                border-radius: 6px;
                background: #f3f4f6;
                flex-shrink: 0;
                overflow: hidden;
            `;

            if (fileInfo.preview) {
                preview.innerHTML = `<img src="${fileInfo.preview}" style="width: 100%; height: 100%; object-fit: cover;">`;
            } else {
                preview.innerHTML = '<div style="width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; font-size: 24px;">📄</div>';
            }

            // Info
            const info = document.createElement('div');
            info.style.cssText = 'flex: 1; min-width: 0;';
            
            const name = document.createElement('div');
            name.style.cssText = 'font-weight: 500; color: #111827; margin-bottom: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;';
            name.textContent = fileInfo.name;

            const details = document.createElement('div');
            details.style.cssText = 'font-size: 14px; color: #6b7280; margin-bottom: 8px;';
            details.textContent = this.formatFileSize(fileInfo.size);

            if (fileInfo.status === 'uploading') {
                details.textContent += ` • ${Math.round(fileInfo.progress)}% • ${this.formatFileSize(fileInfo.speed)}/s`;
            }

            const progress = document.createElement('div');
            progress.style.cssText = `
                width: 100%;
                height: 4px;
                background: #e5e7eb;
                border-radius: 2px;
                overflow: hidden;
            `;

            const progressBar = document.createElement('div');
            progressBar.style.cssText = `
                height: 100%;
                background: ${fileInfo.status === 'failed' ? '#ef4444' : '#3b82f6'};
                width: ${fileInfo.progress}%;
                transition: width 0.3s ease;
            `;
            progress.appendChild(progressBar);

            info.appendChild(name);
            info.appendChild(details);
            info.appendChild(progress);

            // Actions
            const actions = document.createElement('div');
            actions.style.cssText = 'display: flex; gap: 8px;';

            if (fileInfo.status === 'uploading') {
                const cancelBtn = document.createElement('button');
                cancelBtn.textContent = '✕';
                cancelBtn.style.cssText = `
                    width: 32px;
                    height: 32px;
                    border: none;
                    background: #fee2e2;
                    color: #991b1b;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 18px;
                `;
                cancelBtn.addEventListener('click', () => this.cancelUpload(fileInfo.id));
                actions.appendChild(cancelBtn);
            }

            if (fileInfo.status === 'failed') {
                const retryBtn = document.createElement('button');
                retryBtn.textContent = '↻';
                retryBtn.style.cssText = `
                    width: 32px;
                    height: 32px;
                    border: none;
                    background: #dbeafe;
                    color: #1e40af;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 18px;
                `;
                retryBtn.addEventListener('click', () => this.retryUpload(fileInfo.id));
                actions.appendChild(retryBtn);
            }

            const removeBtn = document.createElement('button');
            removeBtn.textContent = '🗑️';
            removeBtn.style.cssText = `
                width: 32px;
                height: 32px;
                border: none;
                background: #f3f4f6;
                color: #6b7280;
                border-radius: 6px;
                cursor: pointer;
                font-size: 16px;
            `;
            removeBtn.addEventListener('click', () => this.removeFile(fileInfo.id));
            actions.appendChild(removeBtn);

            card.appendChild(preview);
            card.appendChild(info);
            card.appendChild(actions);

            return card;
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
                        console.error(`Error in event listener for ${event}:`, error);
                    }
                });
            }
        }
    }

    // Export
    window.FileUploadManager = FileUploadManager;

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = FileUploadManager;
    }

})(window);
