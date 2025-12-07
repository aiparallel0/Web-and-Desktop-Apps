/**
 * Toast Notification System
 * Modern, accessible toast notifications with animations and queue management
 */

class ToastManager {
    constructor() {
        this.toasts = [];
        this.container = null;
        this.nextId = 1;
        this.maxToasts = 5;
        this.defaultDuration = 5000;
        
        this.init();
    }

    /**
     * Initialize toast container
     */
    init() {
        // Create container if it doesn't exist
        if (!document.getElementById('toast-container')) {
            this.container = document.createElement('div');
            this.container.id = 'toast-container';
            this.container.className = 'toast-container';
            this.container.setAttribute('aria-live', 'polite');
            this.container.setAttribute('aria-atomic', 'true');
            document.body.appendChild(this.container);
            
            // Add styles
            this.injectStyles();
        } else {
            this.container = document.getElementById('toast-container');
        }
    }

    /**
     * Inject toast styles
     */
    injectStyles() {
        if (document.getElementById('toast-styles')) return;

        const style = document.createElement('style');
        style.id = 'toast-styles';
        style.textContent = `
            .toast-container {
                position: fixed;
                top: 24px;
                right: 24px;
                z-index: 99999;
                display: flex;
                flex-direction: column;
                gap: 12px;
                max-width: 420px;
                pointer-events: none;
            }

            @media (max-width: 768px) {
                .toast-container {
                    top: 16px;
                    right: 16px;
                    left: 16px;
                    max-width: none;
                }
            }

            .toast {
                background: white;
                border-radius: 12px;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15), 0 4px 8px rgba(0, 0, 0, 0.08);
                padding: 16px 20px;
                display: flex;
                align-items: flex-start;
                gap: 12px;
                pointer-events: auto;
                transform: translateX(calc(100% + 24px));
                transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1),
                           opacity 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                opacity: 0;
                max-width: 100%;
            }

            .toast.toast-entering {
                transform: translateX(0);
                opacity: 1;
            }

            .toast.toast-exiting {
                transform: translateX(calc(100% + 24px));
                opacity: 0;
            }

            .toast-icon {
                flex-shrink: 0;
                width: 24px;
                height: 24px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 50%;
            }

            .toast-success .toast-icon {
                background: #DCFCE7;
                color: #16A34A;
            }

            .toast-error .toast-icon {
                background: #FEE2E2;
                color: #DC2626;
            }

            .toast-warning .toast-icon {
                background: #FEF3C7;
                color: #D97706;
            }

            .toast-info .toast-icon {
                background: #DBEAFE;
                color: #2563EB;
            }

            .toast-content {
                flex: 1;
                min-width: 0;
            }

            .toast-title {
                font-size: 14px;
                font-weight: 600;
                color: #111827;
                margin: 0 0 4px 0;
                line-height: 1.4;
            }

            .toast-message {
                font-size: 14px;
                color: #6B7280;
                margin: 0;
                line-height: 1.5;
                word-wrap: break-word;
            }

            .toast-close {
                flex-shrink: 0;
                width: 24px;
                height: 24px;
                border: none;
                background: transparent;
                color: #9CA3AF;
                cursor: pointer;
                padding: 0;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 4px;
                transition: background 0.2s, color 0.2s;
            }

            .toast-close:hover {
                background: #F3F4F6;
                color: #6B7280;
            }

            .toast-close:focus {
                outline: 2px solid #3B82F6;
                outline-offset: 2px;
            }

            .toast-progress {
                position: absolute;
                bottom: 0;
                left: 0;
                right: 0;
                height: 3px;
                background: rgba(0, 0, 0, 0.1);
                border-radius: 0 0 12px 12px;
                overflow: hidden;
            }

            .toast-progress-bar {
                height: 100%;
                background: currentColor;
                transform-origin: left;
                animation: toast-progress linear;
            }

            .toast-success .toast-progress-bar {
                color: #16A34A;
            }

            .toast-error .toast-progress-bar {
                color: #DC2626;
            }

            .toast-warning .toast-progress-bar {
                color: #D97706;
            }

            .toast-info .toast-progress-bar {
                color: #2563EB;
            }

            @keyframes toast-progress {
                from {
                    transform: scaleX(1);
                }
                to {
                    transform: scaleX(0);
                }
            }

            .toast-action {
                margin-top: 8px;
            }

            .toast-action-btn {
                background: transparent;
                border: 1px solid #E5E7EB;
                padding: 6px 12px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s;
                color: #374151;
            }

            .toast-action-btn:hover {
                background: #F9FAFB;
                border-color: #D1D5DB;
            }

            .toast-action-btn:focus {
                outline: 2px solid #3B82F6;
                outline-offset: 2px;
            }
        `;
        document.head.appendChild(style);
    }

    /**
     * Show toast notification
     */
    show(options) {
        const {
            type = 'info',
            title = '',
            message = '',
            duration = this.defaultDuration,
            action = null,
            onClose = null
        } = typeof options === 'string' ? { message: options } : options;

        // Create toast object
        const toast = {
            id: this.nextId++,
            type,
            title,
            message,
            duration,
            action,
            onClose,
            timer: null,
            element: null
        };

        // Remove oldest toast if at max capacity
        if (this.toasts.length >= this.maxToasts) {
            this.remove(this.toasts[0].id);
        }

        // Add toast to queue
        this.toasts.push(toast);

        // Create and show toast element
        this.createToastElement(toast);

        // Auto-remove after duration
        if (duration > 0) {
            toast.timer = setTimeout(() => {
                this.remove(toast.id);
            }, duration);
        }

        return toast.id;
    }

    /**
     * Create toast DOM element
     */
    createToastElement(toast) {
        const element = document.createElement('div');
        element.className = `toast toast-${toast.type}`;
        element.setAttribute('role', 'alert');
        element.setAttribute('aria-live', 'polite');

        // Icon
        const icon = this.getIcon(toast.type);
        const iconHtml = `
            <div class="toast-icon">
                ${icon}
            </div>
        `;

        // Content
        const contentHtml = `
            <div class="toast-content">
                ${toast.title ? `<div class="toast-title">${this.escapeHtml(toast.title)}</div>` : ''}
                ${toast.message ? `<div class="toast-message">${this.escapeHtml(toast.message)}</div>` : ''}
                ${toast.action ? `
                    <div class="toast-action">
                        <button class="toast-action-btn" data-action="true">
                            ${this.escapeHtml(toast.action.label || 'Action')}
                        </button>
                    </div>
                ` : ''}
            </div>
        `;

        // Close button
        const closeHtml = `
            <button class="toast-close" aria-label="Close notification">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
                </svg>
            </button>
        `;

        // Progress bar
        const progressHtml = toast.duration > 0 ? `
            <div class="toast-progress">
                <div class="toast-progress-bar" style="animation-duration: ${toast.duration}ms;"></div>
            </div>
        ` : '';

        element.innerHTML = iconHtml + contentHtml + closeHtml + progressHtml;

        // Add event listeners
        const closeBtn = element.querySelector('.toast-close');
        closeBtn.addEventListener('click', () => this.remove(toast.id));

        if (toast.action) {
            const actionBtn = element.querySelector('[data-action]');
            actionBtn.addEventListener('click', () => {
                if (toast.action.onClick) {
                    toast.action.onClick();
                }
                this.remove(toast.id);
            });
        }

        // Add to container
        this.container.appendChild(element);
        toast.element = element;

        // Trigger enter animation
        requestAnimationFrame(() => {
            element.classList.add('toast-entering');
        });
    }

    /**
     * Get icon for toast type
     */
    getIcon(type) {
        const icons = {
            success: '<svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/></svg>',
            error: '<svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/></svg>',
            warning: '<svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/></svg>',
            info: '<svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/></svg>'
        };
        return icons[type] || icons.info;
    }

    /**
     * Remove toast
     */
    remove(id) {
        const toastIndex = this.toasts.findIndex(t => t.id === id);
        if (toastIndex === -1) return;

        const toast = this.toasts[toastIndex];

        // Clear timer
        if (toast.timer) {
            clearTimeout(toast.timer);
        }

        // Exit animation
        if (toast.element) {
            toast.element.classList.remove('toast-entering');
            toast.element.classList.add('toast-exiting');

            setTimeout(() => {
                if (toast.element && toast.element.parentNode) {
                    toast.element.remove();
                }
            }, 300);
        }

        // Call onClose callback
        if (toast.onClose) {
            toast.onClose();
        }

        // Remove from array
        this.toasts.splice(toastIndex, 1);
    }

    /**
     * Remove all toasts
     */
    removeAll() {
        const ids = this.toasts.map(t => t.id);
        ids.forEach(id => this.remove(id));
    }

    /**
     * Success toast
     */
    success(message, title = 'Success', options = {}) {
        return this.show({
            type: 'success',
            title,
            message,
            ...options
        });
    }

    /**
     * Error toast
     */
    error(message, title = 'Error', options = {}) {
        return this.show({
            type: 'error',
            title,
            message,
            duration: 7000, // Longer duration for errors
            ...options
        });
    }

    /**
     * Warning toast
     */
    warning(message, title = 'Warning', options = {}) {
        return this.show({
            type: 'warning',
            title,
            message,
            ...options
        });
    }

    /**
     * Info toast
     */
    info(message, title = '', options = {}) {
        return this.show({
            type: 'info',
            title,
            message,
            ...options
        });
    }

    /**
     * Promise toast - shows loading, then success/error
     */
    async promise(promise, messages = {}) {
        const {
            loading = 'Loading...',
            success = 'Success!',
            error = 'Something went wrong'
        } = messages;

        const toastId = this.info(loading, '', { duration: 0 });

        try {
            const result = await promise;
            this.remove(toastId);
            this.success(success);
            return result;
        } catch (err) {
            this.remove(toastId);
            this.error(typeof error === 'function' ? error(err) : error);
            throw err;
        }
    }

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Create singleton instance
const toast = new ToastManager();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = toast;
}
