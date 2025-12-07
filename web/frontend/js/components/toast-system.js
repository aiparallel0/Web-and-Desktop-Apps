/**
 * Toast Notification System
 * Provides user feedback with beautiful, accessible toast notifications
 */

import eventBus from '../core/event-bus.js';

class ToastSystem {
    constructor() {
        this.container = null;
        this.toasts = new Map();
        this.maxToasts = 5;
        this.defaultDuration = 4000;
        this.positions = {
            'top-right': { top: '20px', right: '20px' },
            'top-left': { top: '20px', left: '20px' },
            'bottom-right': { bottom: '20px', right: '20px' },
            'bottom-left': { bottom: '20px', left: '20px' },
            'top-center': { top: '20px', left: '50%', transform: 'translateX(-50%)' },
            'bottom-center': { bottom: '20px', left: '50%', transform: 'translateX(-50%)' }
        };
        this.defaultPosition = 'top-right';
        
        this.init();
    }

    init() {
        this.createContainer();
        this.setupEventListeners();
    }

    createContainer() {
        this.container = document.createElement('div');
        this.container.className = 'toast-container';
        this.container.setAttribute('role', 'region');
        this.container.setAttribute('aria-label', 'Notifications');
        this.setPosition(this.defaultPosition);
        document.body.appendChild(this.container);
    }

    setPosition(position) {
        const styles = this.positions[position] || this.positions[this.defaultPosition];
        Object.assign(this.container.style, styles);
    }

    setupEventListeners() {
        eventBus.on('toast:show', (data) => {
            this.show(data.message, data.type, data.options);
        });

        eventBus.on('toast:clear', () => {
            this.clearAll();
        });
    }

    show(message, type = 'info', options = {}) {
        const id = this.generateId();
        const toast = this.createToast(id, message, type, options);
        
        // Remove oldest toast if limit exceeded
        if (this.toasts.size >= this.maxToasts) {
            const oldestId = this.toasts.keys().next().value;
            this.remove(oldestId);
        }

        this.toasts.set(id, toast);
        this.container.appendChild(toast.element);

        // Trigger animation
        requestAnimationFrame(() => {
            toast.element.classList.add('toast-show');
        });

        // Auto dismiss
        if (options.duration !== 0) {
            const duration = options.duration || this.defaultDuration;
            toast.timeout = setTimeout(() => {
                this.remove(id);
            }, duration);
        }

        // Call onShow callback
        if (options.onShow) {
            options.onShow(id);
        }

        return id;
    }

    createToast(id, message, type, options) {
        const element = document.createElement('div');
        element.className = `toast toast-${type}`;
        element.setAttribute('role', 'alert');
        element.setAttribute('aria-live', type === 'error' ? 'assertive' : 'polite');
        element.dataset.toastId = id;

        const icon = this.getIcon(type);
        const closeBtn = options.closable !== false ? this.createCloseButton(id) : '';

        element.innerHTML = `
            <div class="toast-icon">${icon}</div>
            <div class="toast-content">
                ${options.title ? `<div class="toast-title">${options.title}</div>` : ''}
                <div class="toast-message">${message}</div>
                ${options.action ? this.createAction(id, options.action) : ''}
            </div>
            ${closeBtn}
        `;

        // Add click handler for action
        if (options.action) {
            const actionBtn = element.querySelector('.toast-action');
            actionBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                options.action.onClick(id);
                if (options.action.dismiss !== false) {
                    this.remove(id);
                }
            });
        }

        return {
            element,
            timeout: null,
            type,
            message
        };
    }

    getIcon(type) {
        const icons = {
            success: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                <polyline points="22 4 12 14.01 9 11.01"></polyline>
            </svg>`,
            error: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="15" y1="9" x2="9" y2="15"></line>
                <line x1="9" y1="9" x2="15" y2="15"></line>
            </svg>`,
            warning: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                <line x1="12" y1="9" x2="12" y2="13"></line>
                <line x1="12" y1="17" x2="12.01" y2="17"></line>
            </svg>`,
            info: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="16" x2="12" y2="12"></line>
                <line x1="12" y1="8" x2="12.01" y2="8"></line>
            </svg>`,
            loading: `<svg class="toast-spinner" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83"></path>
            </svg>`
        };

        return icons[type] || icons.info;
    }

    createCloseButton(id) {
        return `<button class="toast-close" onclick="toastSystem.remove('${id}')" aria-label="Close notification">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
        </button>`;
    }

    createAction(id, action) {
        return `<button class="toast-action">${action.label}</button>`;
    }

    remove(id) {
        const toast = this.toasts.get(id);
        if (!toast) return;

        // Clear timeout
        if (toast.timeout) {
            clearTimeout(toast.timeout);
        }

        // Animate out
        toast.element.classList.remove('toast-show');
        toast.element.classList.add('toast-hide');

        // Remove from DOM after animation
        setTimeout(() => {
            if (toast.element.parentNode) {
                toast.element.parentNode.removeChild(toast.element);
            }
            this.toasts.delete(id);
        }, 300);
    }

    clearAll() {
        this.toasts.forEach((toast, id) => {
            this.remove(id);
        });
    }

    // Convenience methods
    success(message, options = {}) {
        return this.show(message, 'success', options);
    }

    error(message, options = {}) {
        return this.show(message, 'error', { ...options, duration: options.duration || 6000 });
    }

    warning(message, options = {}) {
        return this.show(message, 'warning', options);
    }

    info(message, options = {}) {
        return this.show(message, 'info', options);
    }

    loading(message, options = {}) {
        return this.show(message, 'loading', { ...options, duration: 0, closable: false });
    }

    promise(promise, messages = {}) {
        const defaultMessages = {
            loading: 'Processing...',
            success: 'Success!',
            error: 'Failed'
        };

        const msgs = { ...defaultMessages, ...messages };
        const loadingId = this.loading(msgs.loading);

        return promise
            .then((result) => {
                this.remove(loadingId);
                this.success(msgs.success);
                return result;
            })
            .catch((error) => {
                this.remove(loadingId);
                this.error(msgs.error);
                throw error;
            });
    }

    update(id, updates) {
        const toast = this.toasts.get(id);
        if (!toast) return;

        if (updates.message) {
            const messageEl = toast.element.querySelector('.toast-message');
            if (messageEl) {
                messageEl.textContent = updates.message;
                toast.message = updates.message;
            }
        }

        if (updates.type) {
            toast.element.className = `toast toast-${updates.type}`;
            const iconEl = toast.element.querySelector('.toast-icon');
            if (iconEl) {
                iconEl.innerHTML = this.getIcon(updates.type);
            }
            toast.type = updates.type;
        }

        if (updates.duration !== undefined) {
            if (toast.timeout) {
                clearTimeout(toast.timeout);
            }
            if (updates.duration > 0) {
                toast.timeout = setTimeout(() => {
                    this.remove(id);
                }, updates.duration);
            }
        }
    }

    generateId() {
        return `toast_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
}

// Create singleton instance
const toastSystem = new ToastSystem();

// Expose globally
if (typeof window !== 'undefined') {
    window.toastSystem = toastSystem;
    window.toast = {
        show: (msg, type, opts) => toastSystem.show(msg, type, opts),
        success: (msg, opts) => toastSystem.success(msg, opts),
        error: (msg, opts) => toastSystem.error(msg, opts),
        warning: (msg, opts) => toastSystem.warning(msg, opts),
        info: (msg, opts) => toastSystem.info(msg, opts),
        loading: (msg, opts) => toastSystem.loading(msg, opts),
        promise: (promise, msgs) => toastSystem.promise(promise, msgs),
        remove: (id) => toastSystem.remove(id),
        clear: () => toastSystem.clearAll()
    };
}

export default toastSystem;
