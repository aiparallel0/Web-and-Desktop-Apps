/**
 * Modal System
 * Advanced modal/dialog management with animations and keyboard support
 */

import eventBus from '../core/event-bus.js';

class ModalSystem {
    constructor() {
        this.modals = new Map();
        this.stack = [];
        this.backdrop = null;
        this.focusTrap = null;
        this.init();
    }

    init() {
        this.createBackdrop();
        this.setupEventListeners();
        this.setupKeyboardHandlers();
    }

    createBackdrop() {
        this.backdrop = document.createElement('div');
        this.backdrop.className = 'modal-backdrop';
        this.backdrop.style.display = 'none';
        document.body.appendChild(this.backdrop);

        this.backdrop.addEventListener('click', (e) => {
            if (e.target === this.backdrop) {
                const topModal = this.getTopModal();
                if (topModal && topModal.options.closeOnBackdrop !== false) {
                    this.close(topModal.id);
                }
            }
        });
    }

    setupEventListeners() {
        eventBus.on('modal:open', (data) => {
            this.open(data.id, data.content, data.options);
        });

        eventBus.on('modal:close', (data) => {
            this.close(data.id);
        });

        eventBus.on('modal:closeAll', () => {
            this.closeAll();
        });
    }

    setupKeyboardHandlers() {
        document.addEventListener('keydown', (e) => {
            if (this.stack.length === 0) return;

            const topModal = this.getTopModal();
            if (!topModal) return;

            // ESC key
            if (e.key === 'Escape' && topModal.options.closeOnEsc !== false) {
                e.preventDefault();
                this.close(topModal.id);
            }

            // Tab key - focus trap
            if (e.key === 'Tab') {
                this.handleTabKey(e, topModal);
            }
        });
    }

    open(id, content, options = {}) {
        // Check if modal already exists
        if (this.modals.has(id)) {
            console.warn(`Modal ${id} already exists`);
            return;
        }

        const modal = this.createModal(id, content, options);
        this.modals.set(id, modal);
        this.stack.push(modal);

        document.body.appendChild(modal.element);
        this.showBackdrop();

        // Trigger animation
        requestAnimationFrame(() => {
            modal.element.classList.add('modal-show');
            
            // Focus first focusable element
            this.setInitialFocus(modal);
        });

        // Lock body scroll
        document.body.style.overflow = 'hidden';

        // Call onOpen callback
        if (options.onOpen) {
            options.onOpen(id);
        }

        return id;
    }

    createModal(id, content, options) {
        const element = document.createElement('div');
        element.className = `modal ${options.className || ''}`;
        element.setAttribute('role', 'dialog');
        element.setAttribute('aria-modal', 'true');
        element.setAttribute('aria-labelledby', `${id}-title`);
        element.dataset.modalId = id;

        if (options.size) {
            element.classList.add(`modal-${options.size}`);
        }

        const modalContent = `
            <div class="modal-dialog">
                <div class="modal-content">
                    ${options.showHeader !== false ? this.createHeader(id, options) : ''}
                    <div class="modal-body">
                        ${typeof content === 'string' ? content : ''}
                    </div>
                    ${options.footer ? this.createFooter(options.footer) : ''}
                </div>
            </div>
        `;

        element.innerHTML = modalContent;

        // If content is an element, append it
        if (content instanceof HTMLElement) {
            const body = element.querySelector('.modal-body');
            body.innerHTML = '';
            body.appendChild(content);
        }

        // Setup close button
        const closeBtn = element.querySelector('.modal-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.close(id));
        }

        return {
            id,
            element,
            options,
            content
        };
    }

    createHeader(id, options) {
        const closeButton = options.showClose !== false ? `
            <button class="modal-close" aria-label="Close modal">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
            </button>
        ` : '';

        return `
            <div class="modal-header">
                <h2 class="modal-title" id="${id}-title">${options.title || 'Modal'}</h2>
                ${closeButton}
            </div>
        `;
    }

    createFooter(footer) {
        if (typeof footer === 'string') {
            return `<div class="modal-footer">${footer}</div>`;
        }

        const buttons = footer.buttons || [];
        const buttonsHtml = buttons.map(btn => {
            const className = btn.className || 'btn btn-secondary';
            const onclick = btn.onClick ? `data-action="${btn.action || 'custom'}"` : '';
            return `<button class="${className}" ${onclick}>${btn.label}</button>`;
        }).join('');

        return `<div class="modal-footer">${buttonsHtml}</div>`;
    }

    close(id) {
        const modal = this.modals.get(id);
        if (!modal) return;

        // Call onBeforeClose callback
        if (modal.options.onBeforeClose) {
            const shouldClose = modal.options.onBeforeClose(id);
            if (shouldClose === false) return;
        }

        // Animate out
        modal.element.classList.remove('modal-show');
        modal.element.classList.add('modal-hide');

        // Remove from stack
        this.stack = this.stack.filter(m => m.id !== id);

        // Hide backdrop if no more modals
        if (this.stack.length === 0) {
            this.hideBackdrop();
            document.body.style.overflow = '';
        }

        // Remove from DOM after animation
        setTimeout(() => {
            if (modal.element.parentNode) {
                modal.element.parentNode.removeChild(modal.element);
            }
            this.modals.delete(id);

            // Call onClose callback
            if (modal.options.onClose) {
                modal.options.onClose(id);
            }
        }, 300);
    }

    closeAll() {
        const ids = Array.from(this.modals.keys());
        ids.forEach(id => this.close(id));
    }

    getTopModal() {
        return this.stack[this.stack.length - 1];
    }

    showBackdrop() {
        this.backdrop.style.display = 'block';
        requestAnimationFrame(() => {
            this.backdrop.classList.add('backdrop-show');
        });
    }

    hideBackdrop() {
        this.backdrop.classList.remove('backdrop-show');
        setTimeout(() => {
            this.backdrop.style.display = 'none';
        }, 300);
    }

    setInitialFocus(modal) {
        const focusableElements = modal.element.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );

        if (focusableElements.length > 0) {
            focusableElements[0].focus();
        }
    }

    handleTabKey(e, modal) {
        const focusableElements = modal.element.querySelectorAll(
            'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
        );

        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        if (e.shiftKey) {
            if (document.activeElement === firstElement) {
                e.preventDefault();
                lastElement.focus();
            }
        } else {
            if (document.activeElement === lastElement) {
                e.preventDefault();
                firstElement.focus();
            }
        }
    }

    // Convenience methods
    confirm(message, options = {}) {
        return new Promise((resolve) => {
            const id = this.generateId();
            const content = `<p>${message}</p>`;

            this.open(id, content, {
                title: options.title || 'Confirm',
                size: 'small',
                footer: {
                    buttons: [
                        {
                            label: options.cancelLabel || 'Cancel',
                            className: 'btn btn-secondary',
                            action: 'cancel'
                        },
                        {
                            label: options.confirmLabel || 'Confirm',
                            className: options.confirmClass || 'btn btn-primary',
                            action: 'confirm'
                        }
                    ]
                },
                onClose: (id) => {
                    resolve(false);
                }
            });

            // Add button click handlers
            setTimeout(() => {
                const modal = this.modals.get(id);
                if (modal) {
                    const buttons = modal.element.querySelectorAll('[data-action]');
                    buttons.forEach(btn => {
                        btn.addEventListener('click', () => {
                            const action = btn.getAttribute('data-action');
                            this.close(id);
                            resolve(action === 'confirm');
                        });
                    });
                }
            }, 100);
        });
    }

    alert(message, options = {}) {
        return new Promise((resolve) => {
            const id = this.generateId();
            const content = `<p>${message}</p>`;

            this.open(id, content, {
                title: options.title || 'Alert',
                size: 'small',
                footer: {
                    buttons: [
                        {
                            label: options.okLabel || 'OK',
                            className: 'btn btn-primary',
                            action: 'ok'
                        }
                    ]
                },
                onClose: () => resolve()
            });

            setTimeout(() => {
                const modal = this.modals.get(id);
                if (modal) {
                    const okBtn = modal.element.querySelector('[data-action="ok"]');
                    if (okBtn) {
                        okBtn.addEventListener('click', () => {
                            this.close(id);
                            resolve();
                        });
                    }
                }
            }, 100);
        });
    }

    prompt(message, options = {}) {
        return new Promise((resolve) => {
            const id = this.generateId();
            const content = `
                <p>${message}</p>
                <input type="text" 
                       class="modal-input" 
                       placeholder="${options.placeholder || ''}"
                       value="${options.default || ''}"
                       id="${id}-input">
            `;

            this.open(id, content, {
                title: options.title || 'Input',
                size: 'small',
                footer: {
                    buttons: [
                        {
                            label: options.cancelLabel || 'Cancel',
                            className: 'btn btn-secondary',
                            action: 'cancel'
                        },
                        {
                            label: options.confirmLabel || 'OK',
                            className: 'btn btn-primary',
                            action: 'ok'
                        }
                    ]
                },
                onClose: () => resolve(null)
            });

            setTimeout(() => {
                const modal = this.modals.get(id);
                if (modal) {
                    const input = modal.element.querySelector(`#${id}-input`);
                    const buttons = modal.element.querySelectorAll('[data-action]');
                    
                    buttons.forEach(btn => {
                        btn.addEventListener('click', () => {
                            const action = btn.getAttribute('data-action');
                            this.close(id);
                            resolve(action === 'ok' ? input.value : null);
                        });
                    });

                    // Submit on Enter
                    input.addEventListener('keydown', (e) => {
                        if (e.key === 'Enter') {
                            this.close(id);
                            resolve(input.value);
                        }
                    });

                    input.focus();
                }
            }, 100);
        });
    }

    generateId() {
        return `modal_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    isOpen(id) {
        return this.modals.has(id);
    }

    hasOpenModals() {
        return this.stack.length > 0;
    }
}

// Create singleton
const modalSystem = new ModalSystem();

// Expose globally
if (typeof window !== 'undefined') {
    window.modalSystem = modalSystem;
    window.modal = {
        open: (id, content, opts) => modalSystem.open(id, content, opts),
        close: (id) => modalSystem.close(id),
        closeAll: () => modalSystem.closeAll(),
        confirm: (msg, opts) => modalSystem.confirm(msg, opts),
        alert: (msg, opts) => modalSystem.alert(msg, opts),
        prompt: (msg, opts) => modalSystem.prompt(msg, opts)
    };
}

export default modalSystem;
