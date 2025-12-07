/**
 * Modal Manager
 * Manages modal dialogs with animations, accessibility, and focus management
 */

class ModalManager {
    constructor() {
        this.activeModals = [];
        this.modalCounter = 0;
        this.bodyScrollPosition = 0;
        
        this.init();
    }

    /**
     * Initialize modal system
     */
    init() {
        this.injectStyles();
        this.setupGlobalListeners();
    }

    /**
     * Inject modal styles
     */
    injectStyles() {
        if (document.getElementById('modal-styles')) return;

        const style = document.createElement('style');
        style.id = 'modal-styles';
        style.textContent = `
            .modal-overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.6);
                backdrop-filter: blur(4px);
                z-index: 10000;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
                opacity: 0;
                transition: opacity 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            }

            .modal-overlay.modal-entering {
                opacity: 1;
            }

            .modal-overlay.modal-exiting {
                opacity: 0;
            }

            .modal {
                background: white;
                border-radius: 16px;
                box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 
                           0 10px 10px -5px rgba(0, 0, 0, 0.04);
                max-width: 600px;
                width: 100%;
                max-height: 90vh;
                display: flex;
                flex-direction: column;
                transform: scale(0.95) translateY(20px);
                transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                overflow: hidden;
            }

            .modal-overlay.modal-entering .modal {
                transform: scale(1) translateY(0);
            }

            .modal-overlay.modal-exiting .modal {
                transform: scale(0.95) translateY(20px);
            }

            .modal-header {
                padding: 24px 24px 20px;
                border-bottom: 1px solid #E5E7EB;
                display: flex;
                align-items: center;
                justify-content: space-between;
                flex-shrink: 0;
            }

            .modal-title {
                font-size: 20px;
                font-weight: 600;
                color: #111827;
                margin: 0;
            }

            .modal-close {
                width: 32px;
                height: 32px;
                border: none;
                background: transparent;
                color: #9CA3AF;
                cursor: pointer;
                padding: 0;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 6px;
                transition: background 0.2s, color 0.2s;
            }

            .modal-close:hover {
                background: #F3F4F6;
                color: #6B7280;
            }

            .modal-close:focus {
                outline: 2px solid #3B82F6;
                outline-offset: 2px;
            }

            .modal-body {
                padding: 24px;
                overflow-y: auto;
                flex: 1;
            }

            .modal-footer {
                padding: 20px 24px;
                border-top: 1px solid #E5E7EB;
                display: flex;
                gap: 12px;
                justify-content: flex-end;
                flex-shrink: 0;
            }

            .modal-size-sm .modal {
                max-width: 400px;
            }

            .modal-size-lg .modal {
                max-width: 800px;
            }

            .modal-size-xl .modal {
                max-width: 1200px;
            }

            .modal-size-full .modal {
                max-width: calc(100vw - 40px);
                max-height: calc(100vh - 40px);
            }

            body.modal-open {
                overflow: hidden;
            }

            @media (max-width: 640px) {
                .modal {
                    max-width: 100%;
                    max-height: 100vh;
                    border-radius: 0;
                }

                .modal-overlay {
                    padding: 0;
                }
            }

            /* Form elements in modal */
            .modal-form-group {
                margin-bottom: 20px;
            }

            .modal-form-label {
                display: block;
                font-size: 14px;
                font-weight: 500;
                color: #374151;
                margin-bottom: 6px;
            }

            .modal-form-input,
            .modal-form-textarea,
            .modal-form-select {
                width: 100%;
                padding: 10px 14px;
                border: 1px solid #D1D5DB;
                border-radius: 8px;
                font-size: 14px;
                font-family: inherit;
                transition: border-color 0.2s, box-shadow 0.2s;
            }

            .modal-form-input:focus,
            .modal-form-textarea:focus,
            .modal-form-select:focus {
                outline: none;
                border-color: #3B82F6;
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
            }

            .modal-form-textarea {
                resize: vertical;
                min-height: 100px;
            }

            .modal-form-error {
                font-size: 13px;
                color: #DC2626;
                margin-top: 4px;
            }

            .modal-form-help {
                font-size: 13px;
                color: #6B7280;
                margin-top: 4px;
            }

            /* Buttons */
            .modal-btn {
                padding: 10px 20px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s;
                border: none;
                font-family: inherit;
            }

            .modal-btn-primary {
                background: #3B82F6;
                color: white;
            }

            .modal-btn-primary:hover {
                background: #2563EB;
            }

            .modal-btn-primary:focus {
                outline: 2px solid #3B82F6;
                outline-offset: 2px;
            }

            .modal-btn-secondary {
                background: white;
                color: #374151;
                border: 1px solid #D1D5DB;
            }

            .modal-btn-secondary:hover {
                background: #F9FAFB;
            }

            .modal-btn-danger {
                background: #DC2626;
                color: white;
            }

            .modal-btn-danger:hover {
                background: #B91C1C;
            }

            .modal-btn:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }
        `;
        document.head.appendChild(style);
    }

    /**
     * Setup global event listeners
     */
    setupGlobalListeners() {
        // Close on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.activeModals.length > 0) {
                const topModal = this.activeModals[this.activeModals.length - 1];
                if (topModal.options.closeOnEscape !== false) {
                    this.close(topModal.id);
                }
            }
        });
    }

    /**
     * Show modal
     */
    show(options) {
        const modal = {
            id: `modal-${++this.modalCounter}`,
            options: {
                title: '',
                content: '',
                size: 'md', // sm, md, lg, xl, full
                closeOnEscape: true,
                closeOnBackdrop: true,
                showClose: true,
                footer: null,
                onOpen: null,
                onClose: null,
                ...options
            },
            overlay: null,
            modalElement: null,
            previousFocus: document.activeElement
        };

        this.createModal(modal);
        this.activeModals.push(modal);

        // Lock body scroll
        if (this.activeModals.length === 1) {
            this.lockBodyScroll();
        }

        // Call onOpen callback
        if (modal.options.onOpen) {
            modal.options.onOpen(modal.id);
        }

        return modal.id;
    }

    /**
     * Create modal DOM element
     */
    createModal(modal) {
        // Create overlay
        const overlay = document.createElement('div');
        overlay.className = `modal-overlay modal-size-${modal.options.size}`;
        overlay.setAttribute('role', 'dialog');
        overlay.setAttribute('aria-modal', 'true');
        overlay.setAttribute('aria-labelledby', `${modal.id}-title`);

        // Close on backdrop click
        if (modal.options.closeOnBackdrop) {
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) {
                    this.close(modal.id);
                }
            });
        }

        // Create modal
        const modalEl = document.createElement('div');
        modalEl.className = 'modal';
        modalEl.setAttribute('role', 'document');

        // Header
        const header = `
            <div class="modal-header">
                <h2 class="modal-title" id="${modal.id}-title">${this.escapeHtml(modal.options.title)}</h2>
                ${modal.options.showClose ? `
                    <button class="modal-close" aria-label="Close dialog">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                            <path fill-rule="evenodd" d="M6.225 4.811a1 1 0 011.414 0L12 9.172l4.361-4.361a1 1 0 111.414 1.414L13.414 10.586l4.361 4.361a1 1 0 01-1.414 1.414L12 12.001l-4.361 4.361a1 1 0 01-1.414-1.414l4.361-4.361-4.361-4.361a1 1 0 010-1.414z" clip-rule="evenodd"/>
                        </svg>
                    </button>
                ` : ''}
            </div>
        `;

        // Body
        const body = `
            <div class="modal-body">
                ${modal.options.content}
            </div>
        `;

        // Footer
        let footer = '';
        if (modal.options.footer) {
            footer = `<div class="modal-footer">${modal.options.footer}</div>`;
        }

        modalEl.innerHTML = header + body + footer;

        // Add close button listener
        if (modal.options.showClose) {
            const closeBtn = modalEl.querySelector('.modal-close');
            closeBtn.addEventListener('click', () => this.close(modal.id));
        }

        overlay.appendChild(modalEl);
        document.body.appendChild(overlay);

        modal.overlay = overlay;
        modal.modalElement = modalEl;

        // Trigger enter animation
        requestAnimationFrame(() => {
            overlay.classList.add('modal-entering');
        });

        // Focus first focusable element
        this.focusFirstElement(modalEl);
    }

    /**
     * Close modal
     */
    close(id) {
        const modalIndex = this.activeModals.findIndex(m => m.id === id);
        if (modalIndex === -1) return;

        const modal = this.activeModals[modalIndex];

        // Exit animation
        if (modal.overlay) {
            modal.overlay.classList.remove('modal-entering');
            modal.overlay.classList.add('modal-exiting');

            setTimeout(() => {
                if (modal.overlay && modal.overlay.parentNode) {
                    modal.overlay.remove();
                }
            }, 300);
        }

        // Restore focus
        if (modal.previousFocus && modal.previousFocus.focus) {
            modal.previousFocus.focus();
        }

        // Call onClose callback
        if (modal.options.onClose) {
            modal.options.onClose();
        }

        // Remove from array
        this.activeModals.splice(modalIndex, 1);

        // Unlock body scroll if no more modals
        if (this.activeModals.length === 0) {
            this.unlockBodyScroll();
        }
    }

    /**
     * Close all modals
     */
    closeAll() {
        const ids = this.activeModals.map(m => m.id);
        ids.forEach(id => this.close(id));
    }

    /**
     * Confirm dialog
     */
    confirm(options) {
        return new Promise((resolve) => {
            const {
                title = 'Confirm',
                message = 'Are you sure?',
                confirmText = 'Confirm',
                cancelText = 'Cancel',
                confirmClass = 'modal-btn-primary',
                ...restOptions
            } = options;

            const footer = `
                <button class="modal-btn modal-btn-secondary" data-action="cancel">${this.escapeHtml(cancelText)}</button>
                <button class="modal-btn ${confirmClass}" data-action="confirm">${this.escapeHtml(confirmText)}</button>
            `;

            const modalId = this.show({
                title,
                content: `<p style="margin: 0; color: #374151; line-height: 1.6;">${this.escapeHtml(message)}</p>`,
                footer,
                size: 'sm',
                closeOnBackdrop: false,
                closeOnEscape: true,
                ...restOptions,
                onClose: () => resolve(false)
            });

            // Add button listeners
            setTimeout(() => {
                const modal = this.activeModals.find(m => m.id === modalId);
                if (modal) {
                    const confirmBtn = modal.modalElement.querySelector('[data-action="confirm"]');
                    const cancelBtn = modal.modalElement.querySelector('[data-action="cancel"]');

                    confirmBtn.addEventListener('click', () => {
                        resolve(true);
                        this.close(modalId);
                    });

                    cancelBtn.addEventListener('click', () => {
                        resolve(false);
                        this.close(modalId);
                    });
                }
            }, 0);
        });
    }

    /**
     * Alert dialog
     */
    alert(options) {
        return new Promise((resolve) => {
            const {
                title = 'Alert',
                message = '',
                buttonText = 'OK',
                ...restOptions
            } = typeof options === 'string' ? { message: options } : options;

            const footer = `
                <button class="modal-btn modal-btn-primary" data-action="ok">${this.escapeHtml(buttonText)}</button>
            `;

            const modalId = this.show({
                title,
                content: `<p style="margin: 0; color: #374151; line-height: 1.6;">${this.escapeHtml(message)}</p>`,
                footer,
                size: 'sm',
                ...restOptions,
                onClose: () => resolve()
            });

            // Add button listener
            setTimeout(() => {
                const modal = this.activeModals.find(m => m.id === modalId);
                if (modal) {
                    const okBtn = modal.modalElement.querySelector('[data-action="ok"]');
                    okBtn.addEventListener('click', () => {
                        resolve();
                        this.close(modalId);
                    });
                }
            }, 0);
        });
    }

    /**
     * Lock body scroll
     */
    lockBodyScroll() {
        this.bodyScrollPosition = window.pageYOffset;
        document.body.style.overflow = 'hidden';
        document.body.style.position = 'fixed';
        document.body.style.top = `-${this.bodyScrollPosition}px`;
        document.body.style.width = '100%';
        document.body.classList.add('modal-open');
    }

    /**
     * Unlock body scroll
     */
    unlockBodyScroll() {
        document.body.style.removeProperty('overflow');
        document.body.style.removeProperty('position');
        document.body.style.removeProperty('top');
        document.body.style.removeProperty('width');
        document.body.classList.remove('modal-open');
        window.scrollTo(0, this.bodyScrollPosition);
    }

    /**
     * Focus first focusable element
     */
    focusFirstElement(modal) {
        const focusableSelectors = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
        const focusable = modal.querySelectorAll(focusableSelectors);
        if (focusable.length > 0) {
            focusable[0].focus();
        }
    }

    /**
     * Escape HTML
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Create singleton instance
const modal = new ModalManager();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = modal;
}
