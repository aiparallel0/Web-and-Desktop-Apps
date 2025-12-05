/**
 * Upload Zone Web Component
 * Supports drag-drop, click-to-browse, paste, and camera capture
 */

class UploadZone extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        this.selectedFile = null;
        this.onFileSelected = null;
    }

    connectedCallback() {
        this.render();
        this.setupEventListeners();
    }

    render() {
        this.shadowRoot.innerHTML = `
            <style>
                :host {
                    display: block;
                }

                .upload-zone {
                    position: relative;
                    padding: 32px 24px;
                    background: white;
                    border: 3px dashed #D1D5DB;
                    border-radius: 16px;
                    text-align: center;
                    transition: all 250ms cubic-bezier(0.4, 0, 0.2, 1);
                    cursor: pointer;
                    min-height: 200px;
                    max-height: 400px;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                }

                .upload-zone:hover {
                    border-color: #3B82F6;
                    background: #F9FAFB;
                }

                .upload-zone.drag-over {
                    border-color: #10B981;
                    background: #ECFDF5;
                    transform: scale(1.02);
                }

                .upload-zone.has-file {
                    border-color: #10B981;
                    background: #ECFDF5;
                }

                .upload-icon {
                    width: 48px;
                    height: 48px;
                    margin-bottom: 12px;
                    color: #9CA3AF;
                    transition: color 250ms;
                }

                .upload-zone:hover .upload-icon {
                    color: #3B82F6;
                }

                .upload-title {
                    font-size: 1.25rem;
                    font-weight: 600;
                    color: #111827;
                    margin-bottom: 8px;
                }

                .upload-subtitle {
                    font-size: 1rem;
                    color: #6B7280;
                    margin-bottom: 24px;
                }

                .upload-methods {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 12px;
                    justify-content: center;
                    margin-top: 16px;
                }

                .method-btn {
                    padding: 8px 16px;
                    background: white;
                    border: 2px solid #E5E7EB;
                    border-radius: 8px;
                    font-size: 0.875rem;
                    font-weight: 600;
                    color: #4B5563;
                    cursor: pointer;
                    transition: all 150ms;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }

                .method-btn:hover {
                    border-color: #3B82F6;
                    color: #3B82F6;
                    background: #EFF6FF;
                }

                .method-icon {
                    width: 16px;
                    height: 16px;
                }

                input[type="file"] {
                    display: none;
                }

                .preview-container {
                    margin-top: 24px;
                    text-align: center;
                }

                .preview-image {
                    max-width: 100%;
                    max-height: 150px;
                    border-radius: 8px;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                    margin-bottom: 12px;
                    object-fit: contain;
                }

                .file-info {
                    font-size: 0.875rem;
                    color: #6B7280;
                }

                .file-name {
                    font-weight: 600;
                    color: #111827;
                }

                .action-buttons {
                    display: flex;
                    gap: 12px;
                    justify-content: center;
                    margin-top: 16px;
                }

                .btn {
                    padding: 12px 24px;
                    font-weight: 600;
                    border: none;
                    border-radius: 8px;
                    cursor: pointer;
                    transition: all 150ms;
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

                @media (max-width: 640px) {
                    .upload-zone {
                        padding: 24px 16px;
                        min-height: 180px;
                    }

                    .upload-methods {
                        flex-direction: column;
                    }

                    .method-btn {
                        width: 100%;
                    }
                }
            </style>

            <div class="upload-zone" id="dropZone">
                <svg class="upload-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
                </svg>

                <h3 class="upload-title">Drop your receipt here</h3>
                <p class="upload-subtitle">or choose upload method below</p>

                <input type="file" id="fileInput" accept="image/*">
                <input type="file" id="cameraInput" accept="image/*" capture="environment">

                <div class="upload-methods">
                    <button class="method-btn" id="browseBtn">
                        <svg class="method-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/>
                        </svg>
                        Browse Files
                    </button>
                    <button class="method-btn" id="cameraBtn">
                        <svg class="method-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z"/>
                            <circle cx="12" cy="13" r="4"/>
                        </svg>
                        Take Photo
                    </button>
                    <button class="method-btn" id="pasteBtn">
                        <svg class="method-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
                        </svg>
                        Paste (Ctrl+V)
                    </button>
                </div>

                <div class="preview-container hidden" id="previewContainer">
                    <img class="preview-image" id="previewImage" alt="Receipt preview">
                    <div class="file-info">
                        <span class="file-name" id="fileName"></span>
                        <span id="fileSize"></span>
                    </div>
                    <div class="action-buttons">
                        <button class="btn btn-primary" id="extractBtn">Extract Receipt Data</button>
                        <button class="btn btn-secondary" id="clearBtn">Clear</button>
                    </div>
                </div>
            </div>
        `;
    }

    setupEventListeners() {
        const dropZone = this.shadowRoot.getElementById('dropZone');
        const fileInput = this.shadowRoot.getElementById('fileInput');
        const cameraInput = this.shadowRoot.getElementById('cameraInput');
        const browseBtn = this.shadowRoot.getElementById('browseBtn');
        const cameraBtn = this.shadowRoot.getElementById('cameraBtn');
        const pasteBtn = this.shadowRoot.getElementById('pasteBtn');
        const extractBtn = this.shadowRoot.getElementById('extractBtn');
        const clearBtn = this.shadowRoot.getElementById('clearBtn');

        // Drag and drop
        dropZone.addEventListener('click', (e) => {
            if (e.target === dropZone || e.target.closest('.upload-icon, .upload-title, .upload-subtitle')) {
                fileInput.click();
            }
        });

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

            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFile(files[0]);
            }
        });

        // Browse files
        browseBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            fileInput.click();
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFile(e.target.files[0]);
            }
        });

        // Camera capture
        cameraBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            cameraInput.click();
        });

        cameraInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFile(e.target.files[0]);
            }
        });

        // Paste from clipboard
        pasteBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.requestPaste();
        });

        document.addEventListener('paste', (e) => {
            const items = e.clipboardData?.items;
            if (items) {
                for (let item of items) {
                    if (item.type.indexOf('image') !== -1) {
                        const file = item.getAsFile();
                        if (file) {
                            this.handleFile(file);
                            break;
                        }
                    }
                }
            }
        });

        // Action buttons
        extractBtn.addEventListener('click', () => {
            if (this.selectedFile && this.onFileSelected) {
                this.onFileSelected(this.selectedFile);
            }
        });

        clearBtn.addEventListener('click', () => {
            this.clearFile();
        });
    }

    requestPaste() {
        alert('Press Ctrl+V (or Cmd+V on Mac) to paste an image from your clipboard');
    }

    handleFile(file) {
        if (!file.type.startsWith('image/')) {
            alert('Please select an image file');
            return;
        }

        if (file.size > 100 * 1024 * 1024) {
            alert('File too large. Maximum size is 100MB');
            return;
        }

        this.selectedFile = file;

        // Show preview
        const reader = new FileReader();
        reader.onload = (e) => {
            const previewContainer = this.shadowRoot.getElementById('previewContainer');
            const previewImage = this.shadowRoot.getElementById('previewImage');
            const fileName = this.shadowRoot.getElementById('fileName');
            const fileSize = this.shadowRoot.getElementById('fileSize');
            const dropZone = this.shadowRoot.getElementById('dropZone');

            previewImage.src = e.target.result;
            fileName.textContent = file.name;
            fileSize.textContent = ` (${this.formatFileSize(file.size)})`;

            previewContainer.classList.remove('hidden');
            dropZone.classList.add('has-file');

            // Hide upload methods
            this.shadowRoot.querySelector('.upload-icon').style.display = 'none';
            this.shadowRoot.querySelector('.upload-title').style.display = 'none';
            this.shadowRoot.querySelector('.upload-subtitle').style.display = 'none';
            this.shadowRoot.querySelector('.upload-methods').style.display = 'none';
        };
        reader.readAsDataURL(file);
    }

    clearFile() {
        this.selectedFile = null;

        const previewContainer = this.shadowRoot.getElementById('previewContainer');
        const dropZone = this.shadowRoot.getElementById('dropZone');

        previewContainer.classList.add('hidden');
        dropZone.classList.remove('has-file');

        // Show upload methods
        this.shadowRoot.querySelector('.upload-icon').style.display = 'block';
        this.shadowRoot.querySelector('.upload-title').style.display = 'block';
        this.shadowRoot.querySelector('.upload-subtitle').style.display = 'block';
        this.shadowRoot.querySelector('.upload-methods').style.display = 'flex';

        // Reset file inputs
        this.shadowRoot.getElementById('fileInput').value = '';
        this.shadowRoot.getElementById('cameraInput').value = '';
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }

    getFile() {
        return this.selectedFile;
    }
}

customElements.define('upload-zone', UploadZone);
