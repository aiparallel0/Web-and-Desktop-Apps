/**
 * Advanced File Uploader
 * Drag & drop file upload with progress tracking and validation
 */

import eventBus from '../core/event-bus.js';
import toastSystem from '../components/toast-system.js';

class FileUploader {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        this.options = {
            multiple: false,
            maxFiles: 10,
            maxFileSize: 100 * 1024 * 1024, // 100MB
            accept: ['image/*', 'application/pdf'],
            autoUpload: false,
            uploadUrl: '/api/upload',
            onFileAdded: null,
            onFileRemoved: null,
            onUploadStart: null,
            onUploadProgress: null,
            onUploadComplete: null,
            onUploadError: null,
            validateFile: null,
            ...options
        };

        this.files = [];
        this.uploads = new Map();
        this.init();
    }

    init() {
        if (!this.container) {
            console.error('FileUploader: Container not found');
            return;
        }

        this.render();
        this.setupEventListeners();
    }

    render() {
        this.container.innerHTML = '';
        this.container.className = 'file-uploader';

        const dropZone = document.createElement('div');
        dropZone.className = 'file-dropzone';
        dropZone.innerHTML = `
            <div class="dropzone-content">
                <div class="dropzone-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                        <polyline points="17 8 12 3 7 8"></polyline>
                        <line x1="12" y1="3" x2="12" y2="15"></line>
                    </svg>
                </div>
                <div class="dropzone-text">
                    <p class="dropzone-title">Drop files here or click to browse</p>
                    <p class="dropzone-subtitle">
                        ${this.options.accept.join(', ')} 
                        ${this.options.maxFileSize ? `• Max ${this.formatBytes(this.options.maxFileSize)}` : ''}
                    </p>
                </div>
                <input type="file" 
                       class="file-input" 
                       ${this.options.multiple ? 'multiple' : ''}
                       ${this.options.accept.length > 0 ? `accept="${this.options.accept.join(',')}"` : ''}>
            </div>
        `;

        this.container.appendChild(dropZone);

        const fileList = document.createElement('div');
        fileList.className = 'file-list';
        this.container.appendChild(fileList);

        this.renderFileList();
    }

    renderFileList() {
        const fileList = this.container.querySelector('.file-list');
        if (!fileList) return;

        if (this.files.length === 0) {
            fileList.innerHTML = '';
            return;
        }

        fileList.innerHTML = this.files.map((file, index) => {
            const upload = this.uploads.get(file.id);
            const progress = upload ? upload.progress : 0;
            const status = upload ? upload.status : 'pending';

            return `
                <div class="file-item ${status}" data-file-id="${file.id}">
                    <div class="file-preview">
                        ${this.renderPreview(file)}
                    </div>
                    <div class="file-info">
                        <div class="file-name">${file.name}</div>
                        <div class="file-meta">
                            ${this.formatBytes(file.size)}
                            ${upload && upload.status === 'uploading' ? `• ${progress}%` : ''}
                            ${upload && upload.status === 'error' ? `• ${upload.error}` : ''}
                        </div>
                        ${upload && upload.status === 'uploading' ? `
                            <div class="file-progress">
                                <div class="progress-bar">
                                    <div class="progress-fill" style="width: ${progress}%"></div>
                                </div>
                            </div>
                        ` : ''}
                    </div>
                    <div class="file-actions">
                        ${status === 'pending' || status === 'error' ? `
                            <button class="file-action-btn" data-action="upload" title="Upload">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                                    <polyline points="17 8 12 3 7 8"></polyline>
                                    <line x1="12" y1="3" x2="12" y2="15"></line>
                                </svg>
                            </button>
                        ` : ''}
                        ${status === 'uploading' ? `
                            <button class="file-action-btn" data-action="cancel" title="Cancel">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <line x1="18" y1="6" x2="6" y2="18"></line>
                                    <line x1="6" y1="6" x2="18" y2="18"></line>
                                </svg>
                            </button>
                        ` : ''}
                        <button class="file-action-btn" data-action="remove" title="Remove">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="3 6 5 6 21 6"></polyline>
                                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                            </svg>
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    }

    renderPreview(file) {
        if (file.type.startsWith('image/')) {
            const url = URL.createObjectURL(file.file);
            return `<img src="${url}" alt="${file.name}" onload="URL.revokeObjectURL(this.src)">`;
        } else if (file.type === 'application/pdf') {
            return `<div class="file-icon pdf">PDF</div>`;
        } else {
            return `<div class="file-icon">📄</div>`;
        }
    }

    setupEventListeners() {
        const dropZone = this.container.querySelector('.file-dropzone');
        const fileInput = this.container.querySelector('.file-input');

        // Click to select
        dropZone.addEventListener('click', () => {
            fileInput.click();
        });

        // File selection
        fileInput.addEventListener('change', (e) => {
            this.handleFiles(Array.from(e.target.files));
            fileInput.value = ''; // Reset input
        });

        // Drag & drop
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');

            const files = Array.from(e.dataTransfer.files);
            this.handleFiles(files);
        });

        // File actions
        this.container.addEventListener('click', (e) => {
            const actionBtn = e.target.closest('.file-action-btn');
            if (!actionBtn) return;

            const fileItem = actionBtn.closest('.file-item');
            const fileId = fileItem.dataset.fileId;
            const action = actionBtn.dataset.action;

            switch (action) {
                case 'upload':
                    this.uploadFile(fileId);
                    break;
                case 'cancel':
                    this.cancelUpload(fileId);
                    break;
                case 'remove':
                    this.removeFile(fileId);
                    break;
            }
        });
    }

    handleFiles(files) {
        // Check max files limit
        if (this.files.length + files.length > this.options.maxFiles) {
            toastSystem.error(`Maximum ${this.options.maxFiles} files allowed`);
            return;
        }

        for (const file of files) {
            // Validate file
            const validation = this.validateFile(file);
            if (!validation.valid) {
                toastSystem.error(validation.error);
                continue;
            }

            // Add file
            const fileObj = {
                id: this.generateId(),
                file,
                name: file.name,
                size: file.size,
                type: file.type,
                addedAt: new Date()
            };

            this.files.push(fileObj);

            // Callback
            if (this.options.onFileAdded) {
                this.options.onFileAdded(fileObj);
            }

            // Auto upload
            if (this.options.autoUpload) {
                this.uploadFile(fileObj.id);
            }
        }

        this.renderFileList();
    }

    validateFile(file) {
        // Custom validation
        if (this.options.validateFile) {
            const result = this.options.validateFile(file);
            if (!result.valid) {
                return result;
            }
        }

        // Size validation
        if (this.options.maxFileSize && file.size > this.options.maxFileSize) {
            return {
                valid: false,
                error: `File ${file.name} exceeds maximum size of ${this.formatBytes(this.options.maxFileSize)}`
            };
        }

        // Type validation
        if (this.options.accept.length > 0) {
            const accepted = this.options.accept.some(type => {
                if (type.endsWith('/*')) {
                    const category = type.split('/')[0];
                    return file.type.startsWith(category + '/');
                }
                return file.type === type;
            });

            if (!accepted) {
                return {
                    valid: false,
                    error: `File type ${file.type} not accepted`
                };
            }
        }

        return { valid: true };
    }

    async uploadFile(fileId) {
        const fileObj = this.files.find(f => f.id === fileId);
        if (!fileObj) return;

        const formData = new FormData();
        formData.append('file', fileObj.file);

        const xhr = new XMLHttpRequest();

        const upload = {
            xhr,
            status: 'uploading',
            progress: 0,
            error: null
        };

        this.uploads.set(fileId, upload);
        this.renderFileList();

        // Callback
        if (this.options.onUploadStart) {
            this.options.onUploadStart(fileObj);
        }

        // Progress tracking
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const progress = Math.round((e.loaded / e.total) * 100);
                upload.progress = progress;
                this.renderFileList();

                if (this.options.onUploadProgress) {
                    this.options.onUploadProgress(fileObj, progress);
                }
            }
        });

        // Completion
        xhr.addEventListener('load', () => {
            if (xhr.status >= 200 && xhr.status < 300) {
                upload.status = 'complete';
                upload.progress = 100;

                try {
                    const response = JSON.parse(xhr.responseText);
                    
                    if (this.options.onUploadComplete) {
                        this.options.onUploadComplete(fileObj, response);
                    }

                    toastSystem.success(`${fileObj.name} uploaded successfully`);
                } catch (error) {
                    console.error('Upload response parse error:', error);
                }
            } else {
                upload.status = 'error';
                upload.error = `Upload failed: ${xhr.statusText}`;

                if (this.options.onUploadError) {
                    this.options.onUploadError(fileObj, upload.error);
                }

                toastSystem.error(upload.error);
            }

            this.renderFileList();
        });

        // Error
        xhr.addEventListener('error', () => {
            upload.status = 'error';
            upload.error = 'Network error';

            if (this.options.onUploadError) {
                this.options.onUploadError(fileObj, upload.error);
            }

            toastSystem.error(`Failed to upload ${fileObj.name}`);
            this.renderFileList();
        });

        // Send request
        xhr.open('POST', this.options.uploadUrl);
        xhr.send(formData);
    }

    cancelUpload(fileId) {
        const upload = this.uploads.get(fileId);
        if (upload && upload.xhr) {
            upload.xhr.abort();
            upload.status = 'cancelled';
            this.renderFileList();
        }
    }

    removeFile(fileId) {
        const index = this.files.findIndex(f => f.id === fileId);
        if (index === -1) return;

        const file = this.files[index];

        // Cancel upload if in progress
        this.cancelUpload(fileId);

        // Remove file
        this.files.splice(index, 1);
        this.uploads.delete(fileId);

        // Callback
        if (this.options.onFileRemoved) {
            this.options.onFileRemoved(file);
        }

        this.renderFileList();
    }

    uploadAll() {
        this.files.forEach(file => {
            const upload = this.uploads.get(file.id);
            if (!upload || upload.status === 'error' || upload.status === 'pending') {
                this.uploadFile(file.id);
            }
        });
    }

    clear() {
        this.files = [];
        this.uploads.clear();
        this.renderFileList();
    }

    getFiles() {
        return this.files;
    }

    getUploadedFiles() {
        return this.files.filter(file => {
            const upload = this.uploads.get(file.id);
            return upload && upload.status === 'complete';
        });
    }

    formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }

    generateId() {
        return `file_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
}

// Expose globally
if (typeof window !== 'undefined') {
    window.FileUploader = FileUploader;
}

export default FileUploader;
