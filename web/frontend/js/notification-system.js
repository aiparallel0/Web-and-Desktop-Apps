/**
 * Advanced Notification and Toast System
 * Comprehensive notification management with queuing, actions, and persistence
 * @version 2.0.0
 */

(function(window) {
    'use strict';

    class NotificationSystem {
        constructor(options = {}) {
            this.options = {
                position: options.position || 'top-right', // top-right, top-left, bottom-right, bottom-left, top-center, bottom-center
                maxNotifications: options.maxNotifications || 5,
                defaultDuration: options.defaultDuration || 5000,
                animationDuration: options.animationDuration || 300,
                enableSound: options.enableSound !== false,
                pauseOnHover: options.pauseOnHover !== false,
                showProgress: options.showProgress !== false,
                enableStack: options.enableStack !== false,
                ...options
            };

            this.notifications = new Map();
            this.queue = [];
            this.container = null;
            this.sounds = new Map();
            this.init();
        }

        /**
         * Initialize notification system
         */
        init() {
            this.createContainer();
            this.loadSounds();
            this.setupStyles();
        }

        /**
         * Create container
         */
        createContainer() {
            this.container = document.createElement('div');
            this.container.id = 'notification-container';
            this.container.className = `notification-container notification-${this.options.position}`;
            
            const positions = {
                'top-right': 'top: 20px; right: 20px;',
                'top-left': 'top: 20px; left: 20px;',
                'bottom-right': 'bottom: 20px; right: 20px;',
                'bottom-left': 'bottom: 20px; left: 20px;',
                'top-center': 'top: 20px; left: 50%; transform: translateX(-50%);',
                'bottom-center': 'bottom: 20px; left: 50%; transform: translateX(-50%);'
            };

            this.container.style.cssText = `
                position: fixed;
                ${positions[this.options.position] || positions['top-right']}
                z-index: 10000;
                pointer-events: none;
                max-width: 400px;
            `;

            document.body.appendChild(this.container);
        }

        /**
         * Setup styles
         */
        setupStyles() {
            if (document.getElementById('notification-styles')) return;

            const style = document.createElement('style');
            style.id = 'notification-styles';
            style.textContent = `
                .notification {
                    pointer-events: auto;
                    margin-bottom: 12px;
                    animation: slideIn 0.3s ease-out;
                }

                .notification.removing {
                    animation: slideOut 0.3s ease-out;
                }

                @keyframes slideIn {
                    from {
                        transform: translateX(100%);
                        opacity: 0;
                    }
                    to {
                        transform: translateX(0);
                        opacity: 1;
                    }
                }

                @keyframes slideOut {
                    from {
                        transform: translateX(0);
                        opacity: 1;
                    }
                    to {
                        transform: translateX(100%);
                        opacity: 0;
                    }
                }

                .notification-progress {
                    position: absolute;
                    bottom: 0;
                    left: 0;
                    height: 3px;
                    background: currentColor;
                    opacity: 0.3;
                    animation: progressBar linear forwards;
                }

                @keyframes progressBar {
                    from { width: 100%; }
                    to { width: 0%; }
                }
            `;

            document.head.appendChild(style);
        }

        /**
         * Load notification sounds
         */
        loadSounds() {
            // Placeholder for sound loading
            // In production, load actual sound files
            this.sounds.set('success', null);
            this.sounds.set('error', null);
            this.sounds.set('warning', null);
            this.sounds.set('info', null);
        }

        /**
         * Show notification
         */
        show(message, type = 'info', options = {}) {
            const notification = {
                id: this.generateId(),
                message,
                type,
                duration: options.duration !== undefined ? options.duration : this.options.defaultDuration,
                title: options.title,
                icon: options.icon,
                actions: options.actions || [],
                dismissible: options.dismissible !== false,
                pauseOnHover: options.pauseOnHover !== undefined ? options.pauseOnHover : this.options.pauseOnHover,
                showProgress: options.showProgress !== undefined ? options.showProgress : this.options.showProgress,
                onClick: options.onClick,
                onClose: options.onClose,
                timestamp: Date.now()
            };

            // Check if at max capacity
            if (this.notifications.size >= this.options.maxNotifications) {
                if (this.options.enableStack) {
                    this.queue.push(notification);
                    return notification.id;
                } else {
                    // Remove oldest notification
                    const oldest = Array.from(this.notifications.values())[0];
                    this.close(oldest.id);
                }
            }

            this.display(notification);
            this.playSound(type);

            return notification.id;
        }

        /**
         * Display notification
         */
        display(notification) {
            const element = this.createNotificationElement(notification);
            
            this.container.appendChild(element);
            this.notifications.set(notification.id, { ...notification, element });

            // Auto-dismiss
            if (notification.duration > 0) {
                const timer = setTimeout(() => {
                    this.close(notification.id);
                }, notification.duration);

                notification.timer = timer;
            }

            // Process queue
            this.processQueue();
        }

        /**
         * Create notification element
         */
        createNotificationElement(notification) {
            const element = document.createElement('div');
            element.className = `notification notification-${notification.type}`;
            element.dataset.id = notification.id;
            
            const colors = {
                success: { bg: '#d1fae5', border: '#10b981', text: '#065f46', icon: '✓' },
                error: { bg: '#fee2e2', border: '#ef4444', text: '#991b1b', icon: '✕' },
                warning: { bg: '#fef3c7', border: '#f59e0b', text: '#92400e', icon: '⚠' },
                info: { bg: '#dbeafe', border: '#3b82f6', text: '#1e40af', icon: 'ℹ' }
            };

            const color = colors[notification.type] || colors.info;

            element.style.cssText = `
                background: ${color.bg};
                border-left: 4px solid ${color.border};
                border-radius: 8px;
                padding: 16px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                position: relative;
                overflow: hidden;
            `;

            // Content wrapper
            const content = document.createElement('div');
            content.style.cssText = 'display: flex; gap: 12px;';

            // Icon
            if (notification.icon !== false) {
                const icon = document.createElement('div');
                icon.style.cssText = `
                    width: 32px;
                    height: 32px;
                    border-radius: 50%;
                    background: ${color.border};
                    color: white;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-weight: bold;
                    flex-shrink: 0;
                `;
                icon.textContent = notification.icon || color.icon;
                content.appendChild(icon);
            }

            // Message container
            const messageContainer = document.createElement('div');
            messageContainer.style.cssText = 'flex: 1; min-width: 0;';

            // Title
            if (notification.title) {
                const title = document.createElement('div');
                title.style.cssText = `
                    font-weight: 600;
                    color: ${color.text};
                    margin-bottom: 4px;
                    font-size: 14px;
                `;
                title.textContent = notification.title;
                messageContainer.appendChild(title);
            }

            // Message
            const message = document.createElement('div');
            message.style.cssText = `
                color: ${color.text};
                font-size: 14px;
                line-height: 1.5;
            `;
            message.textContent = notification.message;
            messageContainer.appendChild(message);

            // Actions
            if (notification.actions.length > 0) {
                const actions = document.createElement('div');
                actions.style.cssText = 'margin-top: 12px; display: flex; gap: 8px;';

                notification.actions.forEach(action => {
                    const button = document.createElement('button');
                    button.textContent = action.label;
                    button.style.cssText = `
                        padding: 6px 12px;
                        border: none;
                        border-radius: 6px;
                        font-size: 13px;
                        font-weight: 500;
                        cursor: pointer;
                        background: ${color.border};
                        color: white;
                        transition: opacity 0.2s;
                    `;

                    button.addEventListener('mouseenter', () => {
                        button.style.opacity = '0.8';
                    });

                    button.addEventListener('mouseleave', () => {
                        button.style.opacity = '1';
                    });

                    button.addEventListener('click', () => {
                        if (action.onClick) action.onClick();
                        if (action.dismissOnClick !== false) {
                            this.close(notification.id);
                        }
                    });

                    actions.appendChild(button);
                });

                messageContainer.appendChild(actions);
            }

            content.appendChild(messageContainer);

            // Close button
            if (notification.dismissible) {
                const closeBtn = document.createElement('button');
                closeBtn.textContent = '×';
                closeBtn.style.cssText = `
                    position: absolute;
                    top: 8px;
                    right: 8px;
                    background: none;
                    border: none;
                    color: ${color.text};
                    font-size: 24px;
                    line-height: 1;
                    cursor: pointer;
                    opacity: 0.5;
                    transition: opacity 0.2s;
                    padding: 0;
                    width: 24px;
                    height: 24px;
                `;

                closeBtn.addEventListener('mouseenter', () => {
                    closeBtn.style.opacity = '1';
                });

                closeBtn.addEventListener('mouseleave', () => {
                    closeBtn.style.opacity = '0.5';
                });

                closeBtn.addEventListener('click', () => {
                    this.close(notification.id);
                });

                element.appendChild(closeBtn);
            }

            element.appendChild(content);

            // Progress bar
            if (notification.showProgress && notification.duration > 0) {
                const progress = document.createElement('div');
                progress.className = 'notification-progress';
                progress.style.cssText = `
                    animation-duration: ${notification.duration}ms;
                    background: ${color.border};
                `;
                element.appendChild(progress);
            }

            // Pause on hover
            if (notification.pauseOnHover) {
                element.addEventListener('mouseenter', () => {
                    if (notification.timer) {
                        clearTimeout(notification.timer);
                    }
                });

                element.addEventListener('mouseleave', () => {
                    if (notification.duration > 0) {
                        const remaining = notification.duration - (Date.now() - notification.timestamp);
                        if (remaining > 0) {
                            notification.timer = setTimeout(() => {
                                this.close(notification.id);
                            }, remaining);
                        }
                    }
                });
            }

            // Click handler
            if (notification.onClick) {
                element.style.cursor = 'pointer';
                element.addEventListener('click', (e) => {
                    if (!e.target.closest('button')) {
                        notification.onClick();
                    }
                });
            }

            return element;
        }

        /**
         * Close notification
         */
        close(id) {
            const notification = this.notifications.get(id);
            if (!notification) return;

            // Clear timer
            if (notification.timer) {
                clearTimeout(notification.timer);
            }

            // Add removing animation
            notification.element.classList.add('removing');

            // Remove after animation
            setTimeout(() => {
                notification.element.remove();
                this.notifications.delete(id);

                // Call onClose callback
                if (notification.onClose) {
                    notification.onClose();
                }

                // Process queue
                this.processQueue();
            }, this.options.animationDuration);
        }

        /**
         * Process notification queue
         */
        processQueue() {
            while (this.queue.length > 0 && this.notifications.size < this.options.maxNotifications) {
                const notification = this.queue.shift();
                this.display(notification);
            }
        }

        /**
         * Close all notifications
         */
        closeAll() {
            const ids = Array.from(this.notifications.keys());
            ids.forEach(id => this.close(id));
            this.queue = [];
        }

        /**
         * Play sound
         */
        playSound(type) {
            if (!this.options.enableSound) return;

            const sound = this.sounds.get(type);
            if (sound) {
                sound.play().catch(() => {
                    // Ignore audio play errors
                });
            }
        }

        /**
         * Generate unique ID
         */
        generateId() {
            return 'notif_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        }

        /**
         * Convenience methods
         */
        success(message, options = {}) {
            return this.show(message, 'success', options);
        }

        error(message, options = {}) {
            return this.show(message, 'error', options);
        }

        warning(message, options = {}) {
            return this.show(message, 'warning', options);
        }

        info(message, options = {}) {
            return this.show(message, 'info', options);
        }

        /**
         * Show confirmation notification
         */
        confirm(message, options = {}) {
            return new Promise((resolve) => {
                this.show(message, options.type || 'warning', {
                    ...options,
                    duration: 0, // Don't auto-dismiss
                    actions: [
                        {
                            label: options.confirmLabel || 'Confirm',
                            onClick: () => resolve(true)
                        },
                        {
                            label: options.cancelLabel || 'Cancel',
                            onClick: () => resolve(false)
                        }
                    ]
                });
            });
        }

        /**
         * Show loading notification
         */
        loading(message, options = {}) {
            const id = this.show(message, 'info', {
                ...options,
                duration: 0,
                dismissible: false,
                showProgress: false,
                icon: '⏳'
            });

            return {
                id,
                close: () => this.close(id),
                update: (newMessage) => {
                    const notification = this.notifications.get(id);
                    if (notification) {
                        const messageEl = notification.element.querySelector('div:last-child > div:last-child');
                        if (messageEl) {
                            messageEl.textContent = newMessage;
                        }
                    }
                }
            };
        }

        /**
         * Get notification count
         */
        getCount() {
            return this.notifications.size;
        }

        /**
         * Get notifications by type
         */
        getByType(type) {
            return Array.from(this.notifications.values()).filter(n => n.type === type);
        }

        /**
         * Update position
         */
        setPosition(position) {
            this.options.position = position;
            this.container.remove();
            this.createContainer();
            
            // Re-append existing notifications
            this.notifications.forEach(notification => {
                this.container.appendChild(notification.element);
            });
        }
    }

    /**
     * Notification Helper Functions
     */
    const NotificationHelpers = {
        /**
         * Show API error
         */
        showAPIError(error, options = {}) {
            const message = error.response?.data?.message || error.message || 'An error occurred';
            return window.notifications.error(message, {
                title: 'API Error',
                ...options
            });
        },

        /**
         * Show validation errors
         */
        showValidationErrors(errors, options = {}) {
            const messages = Array.isArray(errors) ? errors : Object.values(errors);
            return window.notifications.error(messages.join(', '), {
                title: 'Validation Error',
                ...options
            });
        },

        /**
         * Show success with undo
         */
        showSuccessWithUndo(message, undoCallback, options = {}) {
            return window.notifications.success(message, {
                ...options,
                actions: [
                    {
                        label: 'Undo',
                        onClick: undoCallback
                    }
                ]
            });
        },

        /**
         * Show network status
         */
        showNetworkStatus(online) {
            if (online) {
                return window.notifications.success('Connection restored', {
                    title: 'Online',
                    duration: 3000
                });
            } else {
                return window.notifications.error('No internet connection', {
                    title: 'Offline',
                    duration: 0
                });
            }
        },

        /**
         * Show update available
         */
        showUpdateAvailable(version, onUpdate) {
            return window.notifications.info(`Version ${version} is available`, {
                title: 'Update Available',
                duration: 0,
                actions: [
                    {
                        label: 'Update Now',
                        onClick: onUpdate
                    },
                    {
                        label: 'Later',
                        onClick: () => {}
                    }
                ]
            });
        }
    };

    // Create global instance
    window.notifications = new NotificationSystem();
    window.NotificationHelpers = NotificationHelpers;

    // Export classes
    window.NotificationSystem = NotificationSystem;

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = { NotificationSystem, NotificationHelpers };
    }

})(window);
