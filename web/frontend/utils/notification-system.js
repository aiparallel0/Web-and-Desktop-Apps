/**
 * Notification System
 * Beautiful toast notifications and alert system
 */

class NotificationSystem {
    constructor() {
        this.notifications = [];
        this.maxNotifications = 5;
        this.defaultDuration = 5000;
        this.container = null;
        this.init();
    }

    init() {
        // Create container if it doesn't exist
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'notification-container';
            this.container.className = 'notification-container';
            document.body.appendChild(this.container);
        }

        this.addStyles();
    }

    addStyles() {
        if (document.getElementById('notification-styles')) return;

        const style = document.createElement('style');
        style.id = 'notification-styles';
        style.textContent = `
            .notification-container {
                position: fixed;
                top: var(--space-3);
                right: var(--space-3);
                z-index: 99999;
                display: flex;
                flex-direction: column;
                gap: var(--space-2);
                max-width: 400px;
                pointer-events: none;
            }

            .notification {
                background: white;
                border-radius: var(--radius-lg);
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
                padding: var(--space-3);
                display: flex;
                align-items: flex-start;
                gap: var(--space-2);
                animation: slideInRight 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                pointer-events: auto;
                border-left: 4px solid;
                min-width: 320px;
                position: relative;
                overflow: hidden;
            }

            .notification::before {
                content: '';
                position: absolute;
                bottom: 0;
                left: 0;
                height: 3px;
                background: currentColor;
                animation: notificationProgress var(--duration) linear;
                transform-origin: left;
            }

            .notification.success {
                border-left-color: var(--color-success);
            }

            .notification.success::before {
                background: var(--color-success);
            }

            .notification.error {
                border-left-color: var(--color-danger);
            }

            .notification.error::before {
                background: var(--color-danger);
            }

            .notification.warning {
                border-left-color: var(--color-warning);
            }

            .notification.warning::before {
                background: var(--color-warning);
            }

            .notification.info {
                border-left-color: var(--color-primary);
            }

            .notification.info::before {
                background: var(--color-primary);
            }

            .notification.removing {
                animation: slideOutRight 0.3s cubic-bezier(0.4, 0, 1, 1);
            }

            .notification-icon {
                width: 24px;
                height: 24px;
                flex-shrink: 0;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: var(--radius-full);
                margin-top: 2px;
            }

            .notification.success .notification-icon {
                background: var(--color-success-light);
                color: var(--color-success-dark);
            }

            .notification.error .notification-icon {
                background: var(--color-danger-light);
                color: var(--color-danger-dark);
            }

            .notification.warning .notification-icon {
                background: var(--color-warning-light);
                color: var(--color-warning);
            }

            .notification.info .notification-icon {
                background: var(--color-primary-50);
                color: var(--color-primary);
            }

            .notification-content {
                flex: 1;
                min-width: 0;
            }

            .notification-title {
                font-weight: var(--font-semibold);
                color: var(--color-gray-900);
                margin-bottom: 2px;
                font-size: 0.9375rem;
            }

            .notification-message {
                color: var(--color-gray-600);
                font-size: 0.875rem;
                line-height: 1.5;
                word-wrap: break-word;
            }

            .notification-actions {
                display: flex;
                gap: var(--space-1);
                margin-top: var(--space-2);
            }

            .notification-action {
                padding: 4px 12px;
                border: none;
                background: var(--color-primary);
                color: white;
                border-radius: var(--radius-md);
                font-size: 0.875rem;
                font-weight: var(--font-medium);
                cursor: pointer;
                transition: all var(--transition-fast);
            }

            .notification-action:hover {
                background: var(--color-primary-dark);
            }

            .notification-action.secondary {
                background: var(--color-gray-200);
                color: var(--color-gray-700);
            }

            .notification-action.secondary:hover {
                background: var(--color-gray-300);
            }

            .notification-close {
                width: 24px;
                height: 24px;
                border: none;
                background: transparent;
                color: var(--color-gray-400);
                cursor: pointer;
                border-radius: var(--radius-md);
                display: flex;
                align-items: center;
                justify-content: center;
                flex-shrink: 0;
                margin-top: 2px;
                transition: all var(--transition-fast);
            }

            .notification-close:hover {
                background: var(--color-gray-100);
                color: var(--color-gray-700);
            }

            @keyframes slideInRight {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }

            @keyframes slideOutRight {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(100%);
                    opacity: 0;
                }
            }

            @keyframes notificationProgress {
                from {
                    transform: scaleX(1);
                }
                to {
                    transform: scaleX(0);
                }
            }

            @media (max-width: 640px) {
                .notification-container {
                    top: auto;
                    bottom: var(--space-3);
                    left: var(--space-2);
                    right: var(--space-2);
                    max-width: none;
                }

                .notification {
                    min-width: auto;
                }
            }

            /* Alert styles */
            .alert-overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 100000;
                animation: fadeIn 0.2s ease;
            }

            .alert-dialog {
                background: white;
                border-radius: var(--radius-xl);
                max-width: 500px;
                width: 90%;
                box-shadow: 0 25px 50px rgba(0, 0, 0, 0.3);
                animation: scaleIn 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            }

            .alert-header {
                padding: var(--space-4);
                border-bottom: 1px solid var(--color-gray-200);
                display: flex;
                align-items: center;
                gap: var(--space-3);
            }

            .alert-icon {
                width: 48px;
                height: 48px;
                border-radius: var(--radius-full);
                display: flex;
                align-items: center;
                justify-content: center;
                flex-shrink: 0;
            }

            .alert-icon.success {
                background: var(--color-success-light);
                color: var(--color-success-dark);
            }

            .alert-icon.error {
                background: var(--color-danger-light);
                color: var(--color-danger-dark);
            }

            .alert-icon.warning {
                background: var(--color-warning-light);
                color: var(--color-warning);
            }

            .alert-title {
                font-size: 1.25rem;
                font-weight: var(--font-semibold);
                color: var(--color-gray-900);
                margin: 0;
            }

            .alert-body {
                padding: var(--space-4);
                color: var(--color-gray-600);
                line-height: 1.6;
            }

            .alert-footer {
                padding: var(--space-4);
                border-top: 1px solid var(--color-gray-200);
                display: flex;
                gap: var(--space-2);
                justify-content: flex-end;
            }

            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }

            @keyframes scaleIn {
                from {
                    opacity: 0;
                    transform: scale(0.9);
                }
                to {
                    opacity: 1;
                    transform: scale(1);
                }
            }
        `;
        document.head.appendChild(style);
    }

    /**
     * Show a toast notification
     * @param {Object} options - Notification options
     */
    show(options = {}) {
        const {
            type = 'info',
            title = '',
            message = '',
            duration = this.defaultDuration,
            actions = [],
            onClose = null
        } = options;

        // Limit number of notifications
        if (this.notifications.length >= this.maxNotifications) {
            this.remove(this.notifications[0]);
        }

        const id = 'notif-' + Date.now();
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.id = id;
        notification.style.setProperty('--duration', `${duration}ms`);

        const icons = {
            success: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>',
            error: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>',
            warning: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
            info: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>'
        };

        notification.innerHTML = `
            <div class="notification-icon">${icons[type] || icons.info}</div>
            <div class="notification-content">
                ${title ? `<div class="notification-title">${title}</div>` : ''}
                <div class="notification-message">${message}</div>
                ${actions.length > 0 ? `
                    <div class="notification-actions">
                        ${actions.map((action, index) => `
                            <button class="notification-action ${action.secondary ? 'secondary' : ''}" data-action="${index}">
                                ${action.label}
                            </button>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
            <button class="notification-close">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
            </button>
        `;

        // Add to container
        this.container.appendChild(notification);
        this.notifications.push({ id, element: notification });

        // Setup action buttons
        actions.forEach((action, index) => {
            const button = notification.querySelector(`[data-action="${index}"]`);
            button?.addEventListener('click', () => {
                if (action.onClick) action.onClick();
                this.remove(notification);
            });
        });

        // Setup close button
        notification.querySelector('.notification-close').addEventListener('click', () => {
            this.remove(notification);
            if (onClose) onClose();
        });

        // Auto remove after duration (if not infinite)
        if (duration > 0) {
            setTimeout(() => {
                if (notification.parentElement) {
                    this.remove(notification);
                }
            }, duration);
        }

        return { id, remove: () => this.remove(notification) };
    }

    /**
     * Remove a notification
     * @param {HTMLElement} notification - Notification element to remove
     */
    remove(notification) {
        if (!notification || !notification.parentElement) return;

        notification.classList.add('removing');
        setTimeout(() => {
            if (notification.parentElement) {
                notification.parentElement.removeChild(notification);
                this.notifications = this.notifications.filter(n => n.element !== notification);
            }
        }, 300);
    }

    /**
     * Show success notification
     */
    success(message, title = 'Success') {
        return this.show({ type: 'success', title, message });
    }

    /**
     * Show error notification
     */
    error(message, title = 'Error') {
        return this.show({ type: 'error', title, message });
    }

    /**
     * Show warning notification
     */
    warning(message, title = 'Warning') {
        return this.show({ type: 'warning', title, message });
    }

    /**
     * Show info notification
     */
    info(message, title = 'Info') {
        return this.show({ type: 'info', title, message });
    }

    /**
     * Show confirmation alert
     */
    confirm(options = {}) {
        const {
            title = 'Confirm Action',
            message = 'Are you sure?',
            type = 'warning',
            confirmText = 'Confirm',
            cancelText = 'Cancel',
            onConfirm = null,
            onCancel = null
        } = options;

        return new Promise((resolve) => {
            const overlay = document.createElement('div');
            overlay.className = 'alert-overlay';
            
            const icons = {
                success: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>',
                error: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>',
                warning: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>'
            };

            overlay.innerHTML = `
                <div class="alert-dialog">
                    <div class="alert-header">
                        <div class="alert-icon ${type}">${icons[type] || icons.warning}</div>
                        <h3 class="alert-title">${title}</h3>
                    </div>
                    <div class="alert-body">${message}</div>
                    <div class="alert-footer">
                        <button class="btn btn-secondary" id="alertCancel">${cancelText}</button>
                        <button class="btn btn-primary" id="alertConfirm">${confirmText}</button>
                    </div>
                </div>
            `;

            document.body.appendChild(overlay);

            const handleConfirm = () => {
                document.body.removeChild(overlay);
                if (onConfirm) onConfirm();
                resolve(true);
            };

            const handleCancel = () => {
                document.body.removeChild(overlay);
                if (onCancel) onCancel();
                resolve(false);
            };

            overlay.querySelector('#alertConfirm').addEventListener('click', handleConfirm);
            overlay.querySelector('#alertCancel').addEventListener('click', handleCancel);
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) handleCancel();
            });
        });
    }

    /**
     * Clear all notifications
     */
    clearAll() {
        this.notifications.forEach(({ element }) => this.remove(element));
    }
}

// Create global instance
const notify = new NotificationSystem();

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NotificationSystem;
}
window.NotificationSystem = NotificationSystem;
window.notify = notify;
