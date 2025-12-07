/**
 * Batch Upload Component
 * Advanced drag-and-drop interface for uploading multiple receipts
 */

class BatchUploadComponent extends HTMLElement {
    constructor() {
        super();
        this.files = [];
        this.maxFiles = 50;
        this.maxFileSize = 100 * 1024 * 1024; // 100MB
        this.acceptedTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/bmp', 'image/tiff', 'application/pdf'];
    }

    connectedCallback() {
        this.render();
        this.setupEventListeners();
    }

    render() {
        this.innerHTML = `
            <div class="batch-upload-container">
                <div class="batch-upload-zone" id="batchDropZone">
                    <div class="upload-icon">
                        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                            <polyline points="17 8 12 3 7 8"></polyline>
                            <line x1="12" y1="3" x2="12" y2="15"></line>
                        </svg>
                    </div>
                    <h3 class="upload-title">Drop multiple receipts here</h3>
                    <p class="upload-subtitle">or click to browse files</p>
                    <p class="upload-limit">Up to ${this.maxFiles} files, max ${this.maxFileSize / (1024 * 1024)}MB each</p>
                    <input type="file" id="batchFileInput" multiple accept="${this.acceptedTypes.join(',')}" style="display: none;">
                </div>

                <div class="batch-files-list" id="batchFilesList" style="display: none;">
                    <div class="files-header">
                        <h4>Selected Files (<span id="fileCount">0</span>/${this.maxFiles})</h4>
                        <div class="files-actions">
                            <button class="btn btn-ghost btn-sm" id="clearAllBtn">Clear All</button>
                            <button class="btn btn-primary btn-sm" id="uploadAllBtn">Upload All</button>
                        </div>
                    </div>
                    <div class="files-grid" id="filesGrid"></div>
                </div>

                <div class="batch-upload-progress" id="uploadProgress" style="display: none;">
                    <div class="progress-header">
                        <h4>Uploading Files...</h4>
                        <span class="progress-count" id="progressCount">0 / 0</span>
                    </div>
                    <div class="progress-bar-container">
                        <div class="progress-bar" id="progressBar"></div>
                    </div>
                    <div class="progress-status" id="progressStatus">Preparing upload...</div>
                </div>
            </div>
        `;

        this.addStyles();
    }

    addStyles() {
        if (document.getElementById('batch-upload-styles')) return;

        const style = document.createElement('style');
        style.id = 'batch-upload-styles';
        style.textContent = `
            .batch-upload-container {
                width: 100%;
            }

            .batch-upload-zone {
                border: 3px dashed var(--color-gray-300);
                border-radius: var(--radius-xl);
                padding: var(--space-8);
                text-align: center;
                cursor: pointer;
                transition: all var(--transition-base);
                background: var(--color-gray-50);
            }

            .batch-upload-zone:hover,
            .batch-upload-zone.drag-over {
                border-color: var(--color-primary);
                background: var(--color-primary-50);
            }

            .upload-icon {
                margin: 0 auto var(--space-3);
                color: var(--color-gray-400);
            }

            .batch-upload-zone.drag-over .upload-icon {
                color: var(--color-primary);
                animation: bounce 0.6s ease;
            }

            .upload-title {
                font-size: 1.25rem;
                font-weight: var(--font-semibold);
                color: var(--color-gray-900);
                margin-bottom: 8px;
            }

            .upload-subtitle {
                color: var(--color-gray-600);
                margin-bottom: 8px;
            }

            .upload-limit {
                font-size: 0.875rem;
                color: var(--color-gray-500);
            }

            .batch-files-list {
                margin-top: var(--space-4);
                background: white;
                border-radius: var(--radius-lg);
                padding: var(--space-4);
                border: 1px solid var(--color-gray-200);
            }

            .files-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: var(--space-3);
                padding-bottom: var(--space-3);
                border-bottom: 1px solid var(--color-gray-200);
            }

            .files-header h4 {
                font-size: 1.125rem;
                color: var(--color-gray-900);
            }

            .files-actions {
                display: flex;
                gap: var(--space-2);
            }

            .files-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                gap: var(--space-3);
            }

            .file-item {
                position: relative;
                border: 1px solid var(--color-gray-200);
                border-radius: var(--radius-md);
                padding: var(--space-3);
                background: var(--color-gray-50);
                transition: all var(--transition-fast);
            }

            .file-item:hover {
                box-shadow: var(--shadow-md);
                border-color: var(--color-gray-300);
            }

            .file-item.uploading {
                opacity: 0.6;
                pointer-events: none;
            }

            .file-item.success {
                border-color: var(--color-success);
                background: var(--color-success-50);
            }

            .file-item.error {
                border-color: var(--color-danger);
                background: var(--color-danger-50);
            }

            .file-preview {
                width: 100%;
                height: 120px;
                background: var(--color-gray-200);
                border-radius: var(--radius-md);
                margin-bottom: var(--space-2);
                overflow: hidden;
                display: flex;
                align-items: center;
                justify-content: center;
            }

            .file-preview img {
                width: 100%;
                height: 100%;
                object-fit: cover;
            }

            .file-preview-icon {
                color: var(--color-gray-400);
            }

            .file-name {
                font-size: 0.875rem;
                font-weight: var(--font-medium);
                color: var(--color-gray-900);
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                margin-bottom: 4px;
            }

            .file-size {
                font-size: 0.75rem;
                color: var(--color-gray-500);
            }

            .file-remove {
                position: absolute;
                top: 8px;
                right: 8px;
                width: 24px;
                height: 24px;
                background: var(--color-danger);
                color: white;
                border: none;
                border-radius: var(--radius-full);
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1rem;
                line-height: 1;
                transition: all var(--transition-fast);
            }

            .file-remove:hover {
                background: var(--color-danger-600);
                transform: scale(1.1);
            }

            .file-status {
                margin-top: 8px;
                font-size: 0.75rem;
                font-weight: var(--font-semibold);
            }

            .file-status.success {
                color: var(--color-success-dark);
            }

            .file-status.error {
                color: var(--color-danger-dark);
            }

            .batch-upload-progress {
                margin-top: var(--space-4);
                background: white;
                border-radius: var(--radius-lg);
                padding: var(--space-4);
                border: 1px solid var(--color-gray-200);
            }

            .progress-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: var(--space-2);
            }

            .progress-header h4 {
                font-size: 1.125rem;
                color: var(--color-gray-900);
            }

            .progress-count {
                font-size: 0.875rem;
                color: var(--color-gray-600);
                font-weight: var(--font-medium);
            }

            .progress-bar-container {
                height: 8px;
                background: var(--color-gray-200);
                border-radius: var(--radius-full);
                overflow: hidden;
                margin-bottom: var(--space-2);
            }

            .progress-bar {
                height: 100%;
                background: var(--color-primary);
                border-radius: var(--radius-full);
                transition: width var(--transition-base);
                width: 0%;
            }

            .progress-status {
                font-size: 0.875rem;
                color: var(--color-gray-600);
            }

            @keyframes bounce {
                0%, 100% {
                    transform: translateY(0);
                }
                50% {
                    transform: translateY(-10px);
                }
            }

            @media (max-width: 768px) {
                .files-grid {
                    grid-template-columns: 1fr;
                }
            }
        `;
        document.head.appendChild(style);
    }

    setupEventListeners() {
        const dropZone = this.querySelector('#batchDropZone');
        const fileInput = this.querySelector('#batchFileInput');
        const clearAllBtn = this.querySelector('#clearAllBtn');
        const uploadAllBtn = this.querySelector('#uploadAllBtn');

        // Click to select files
        dropZone.addEventListener('click', () => fileInput.click());

        // File input change
        fileInput.addEventListener('change', (e) => {
            this.handleFiles(Array.from(e.target.files));
        });

        // Drag and drop
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('drag-over');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('drag-over');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('drag-over');
            this.handleFiles(Array.from(e.dataTransfer.files));
        });

        // Clear all files
        clearAllBtn?.addEventListener('click', () => {
            this.clearFiles();
        });

        // Upload all files
        uploadAllBtn?.addEventListener('click', () => {
            this.uploadFiles();
        });
    }

    handleFiles(newFiles) {
        const validFiles = newFiles.filter(file => {
            if (!this.acceptedTypes.includes(file.type)) {
                console.warn(`File ${file.name} has invalid type`);
                return false;
            }
            if (file.size > this.maxFileSize) {
                console.warn(`File ${file.name} exceeds size limit`);
                return false;
            }
            return true;
        });

        const totalFiles = this.files.length + validFiles.length;
        if (totalFiles > this.maxFiles) {
            alert(`You can only upload up to ${this.maxFiles} files`);
            const allowed = this.maxFiles - this.files.length;
            validFiles.splice(allowed);
        }

        this.files.push(...validFiles);
        this.updateFilesList();
    }

    updateFilesList() {
        const filesList = this.querySelector('#batchFilesList');
        const filesGrid = this.querySelector('#filesGrid');
        const fileCount = this.querySelector('#fileCount');

        if (this.files.length === 0) {
            filesList.style.display = 'none';
            return;
        }

        filesList.style.display = 'block';
        fileCount.textContent = this.files.length;

        filesGrid.innerHTML = this.files.map((file, index) => {
            const preview = file.type.startsWith('image/') 
                ? `<img src="${URL.createObjectURL(file)}" alt="${file.name}">`
                : `<svg class="file-preview-icon" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                    <polyline points="14 2 14 8 20 8"></polyline>
                   </svg>`;

            return `
                <div class="file-item" data-index="${index}">
                    <button class="file-remove" onclick="this.closest('batch-upload').removeFile(${index})">×</button>
                    <div class="file-preview">${preview}</div>
                    <div class="file-name" title="${file.name}">${file.name}</div>
                    <div class="file-size">${this.formatFileSize(file.size)}</div>
                </div>
            `;
        }).join('');
    }

    removeFile(index) {
        this.files.splice(index, 1);
        this.updateFilesList();
    }

    clearFiles() {
        this.files = [];
        this.updateFilesList();
    }

    async uploadFiles() {
        if (this.files.length === 0) return;

        const uploadProgress = this.querySelector('#uploadProgress');
        const progressBar = this.querySelector('#progressBar');
        const progressCount = this.querySelector('#progressCount');
        const progressStatus = this.querySelector('#progressStatus');

        uploadProgress.style.display = 'block';

        let completed = 0;
        const total = this.files.length;

        for (let i = 0; i < this.files.length; i++) {
            const file = this.files[i];
            const fileItem = this.querySelector(`.file-item[data-index="${i}"]`);

            try {
                fileItem.classList.add('uploading');
                progressStatus.textContent = `Uploading ${file.name}...`;
                progressCount.textContent = `${completed} / ${total}`;

                // Simulate upload (replace with actual API call)
                await this.uploadFile(file);

                fileItem.classList.remove('uploading');
                fileItem.classList.add('success');
                fileItem.querySelector('.file-name').insertAdjacentHTML('afterend', 
                    '<div class="file-status success">✓ Uploaded</div>');

                completed++;
                const progress = (completed / total) * 100;
                progressBar.style.width = progress + '%';
                progressCount.textContent = `${completed} / ${total}`;

            } catch (error) {
                fileItem.classList.remove('uploading');
                fileItem.classList.add('error');
                fileItem.querySelector('.file-name').insertAdjacentHTML('afterend', 
                    '<div class="file-status error">✗ Failed</div>');
                console.error(`Failed to upload ${file.name}:`, error);
            }
        }

        progressStatus.textContent = `Upload complete! ${completed} of ${total} files processed.`;

        // Dispatch completion event
        this.dispatchEvent(new CustomEvent('upload-complete', {
            detail: { completed, total, files: this.files }
        }));
    }

    async uploadFile(file) {
        // Simulate API call - replace with actual implementation
        return new Promise((resolve) => {
            setTimeout(resolve, 1000 + Math.random() * 1000);
        });
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }
}

// Register custom element
customElements.define('batch-upload', BatchUploadComponent);
