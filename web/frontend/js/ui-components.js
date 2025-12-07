/**
 * UI Components Library
 * Reusable UI components for building interfaces
 * @version 2.0.0
 */

(function(window) {
    'use strict';

    class UIComponents {
        /**
         * Create a modal dialog
         */
        static createModal(options = {}) {
            const {
                title = 'Modal',
                content = '',
                footer = '',
                size = 'medium',
                closeButton = true,
                backdrop = true,
                onClose = null
            } = options;

            // Create modal overlay
            const overlay = document.createElement('div');
            overlay.className = 'modal-overlay';
            overlay.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 9999;
                animation: fadeIn 0.2s ease-out;
            `;

            // Create modal container
            const modal = document.createElement('div');
            modal.className = `modal modal-${size}`;
            const modalWidth = {
                small: '400px',
                medium: '600px',
                large: '800px',
                fullscreen: '95vw'
            }[size] || '600px';

            modal.style.cssText = `
                background: white;
                border-radius: 12px;
                box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
                max-width: ${modalWidth};
                width: 100%;
                max-height: 90vh;
                display: flex;
                flex-direction: column;
                animation: slideInUp 0.3s ease-out;
            `;

            // Create header
            const header = document.createElement('div');
            header.className = 'modal-header';
            header.style.cssText = `
                padding: 24px;
                border-bottom: 1px solid #e5e7eb;
                display: flex;
                align-items: center;
                justify-content: space-between;
            `;

            const titleEl = document.createElement('h3');
            titleEl.textContent = title;
            titleEl.style.cssText = `
                margin: 0;
                font-size: 20px;
                font-weight: 600;
                color: #111827;
            `;
            header.appendChild(titleEl);

            if (closeButton) {
                const closeBtn = document.createElement('button');
                closeBtn.innerHTML = '×';
                closeBtn.className = 'modal-close';
                closeBtn.style.cssText = `
                    background: none;
                    border: none;
                    font-size: 32px;
                    line-height: 1;
                    color: #6b7280;
                    cursor: pointer;
                    padding: 0;
                    width: 32px;
                    height: 32px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    border-radius: 6px;
                    transition: all 0.2s;
                `;
                closeBtn.addEventListener('mouseenter', () => {
                    closeBtn.style.background = '#f3f4f6';
                    closeBtn.style.color = '#111827';
                });
                closeBtn.addEventListener('mouseleave', () => {
                    closeBtn.style.background = 'none';
                    closeBtn.style.color = '#6b7280';
                });
                closeBtn.addEventListener('click', () => {
                    this.closeModal(overlay, onClose);
                });
                header.appendChild(closeBtn);
            }

            // Create body
            const body = document.createElement('div');
            body.className = 'modal-body';
            body.style.cssText = `
                padding: 24px;
                overflow-y: auto;
                flex: 1;
            `;
            
            if (typeof content === 'string') {
                body.innerHTML = content;
            } else if (content instanceof HTMLElement) {
                body.appendChild(content);
            }

            // Create footer if provided
            let footerEl;
            if (footer) {
                footerEl = document.createElement('div');
                footerEl.className = 'modal-footer';
                footerEl.style.cssText = `
                    padding: 16px 24px;
                    border-top: 1px solid #e5e7eb;
                    display: flex;
                    justify-content: flex-end;
                    gap: 12px;
                `;
                
                if (typeof footer === 'string') {
                    footerEl.innerHTML = footer;
                } else if (footer instanceof HTMLElement) {
                    footerEl.appendChild(footer);
                }
            }

            // Assemble modal
            modal.appendChild(header);
            modal.appendChild(body);
            if (footerEl) {
                modal.appendChild(footerEl);
            }

            overlay.appendChild(modal);

            // Handle backdrop click
            if (backdrop) {
                overlay.addEventListener('click', (e) => {
                    if (e.target === overlay) {
                        this.closeModal(overlay, onClose);
                    }
                });
            }

            // Handle ESC key
            const escHandler = (e) => {
                if (e.key === 'Escape') {
                    this.closeModal(overlay, onClose);
                    document.removeEventListener('keydown', escHandler);
                }
            };
            document.addEventListener('keydown', escHandler);

            // Show modal
            document.body.appendChild(overlay);
            
            // Focus first input if available
            setTimeout(() => {
                const firstInput = modal.querySelector('input, textarea, select, button');
                if (firstInput) {
                    firstInput.focus();
                }
            }, 100);

            return {
                modal: overlay,
                body,
                close: () => this.closeModal(overlay, onClose)
            };
        }

        /**
         * Close modal
         */
        static closeModal(overlay, onClose) {
            overlay.style.animation = 'fadeOut 0.2s ease-out';
            setTimeout(() => {
                overlay.remove();
                if (onClose) onClose();
            }, 200);
        }

        /**
         * Create confirmation dialog
         */
        static confirm(message, title = 'Confirm', options = {}) {
            return new Promise((resolve) => {
                const {
                    confirmText = 'Confirm',
                    cancelText = 'Cancel',
                    confirmStyle = 'primary',
                    cancelStyle = 'secondary'
                } = options;

                const content = document.createElement('p');
                content.textContent = message;
                content.style.cssText = 'margin: 0; font-size: 16px; color: #374151;';

                const footer = document.createElement('div');
                footer.style.cssText = 'display: flex; gap: 12px;';

                const cancelBtn = this.createButton(cancelText, cancelStyle);
                const confirmBtn = this.createButton(confirmText, confirmStyle);

                cancelBtn.addEventListener('click', () => {
                    modal.close();
                    resolve(false);
                });

                confirmBtn.addEventListener('click', () => {
                    modal.close();
                    resolve(true);
                });

                footer.appendChild(cancelBtn);
                footer.appendChild(confirmBtn);

                const modal = this.createModal({
                    title,
                    content,
                    footer,
                    size: 'small',
                    onClose: () => resolve(false)
                });
            });
        }

        /**
         * Create alert dialog
         */
        static alert(message, title = 'Alert', type = 'info') {
            return new Promise((resolve) => {
                const content = document.createElement('div');
                content.style.cssText = 'display: flex; gap: 16px; align-items: start;';

                const icon = document.createElement('div');
                icon.style.cssText = `
                    width: 48px;
                    height: 48px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 24px;
                    flex-shrink: 0;
                `;

                const colors = {
                    info: { bg: '#dbeafe', icon: 'ℹ️' },
                    success: { bg: '#d1fae5', icon: '✓' },
                    warning: { bg: '#fef3c7', icon: '⚠️' },
                    error: { bg: '#fee2e2', icon: '✕' }
                };

                const color = colors[type] || colors.info;
                icon.style.background = color.bg;
                icon.textContent = color.icon;

                const text = document.createElement('p');
                text.textContent = message;
                text.style.cssText = 'margin: 0; font-size: 16px; color: #374151; flex: 1;';

                content.appendChild(icon);
                content.appendChild(text);

                const footer = document.createElement('div');
                const okBtn = this.createButton('OK', 'primary');
                okBtn.addEventListener('click', () => {
                    modal.close();
                    resolve();
                });
                footer.appendChild(okBtn);

                const modal = this.createModal({
                    title,
                    content,
                    footer,
                    size: 'small',
                    onClose: resolve
                });
            });
        }

        /**
         * Create button
         */
        static createButton(text, style = 'primary', options = {}) {
            const button = document.createElement('button');
            button.textContent = text;
            button.className = `btn btn-${style}`;
            
            const styles = {
                primary: {
                    background: '#3b82f6',
                    color: 'white',
                    hoverBg: '#2563eb'
                },
                secondary: {
                    background: '#6b7280',
                    color: 'white',
                    hoverBg: '#4b5563'
                },
                success: {
                    background: '#10b981',
                    color: 'white',
                    hoverBg: '#059669'
                },
                danger: {
                    background: '#ef4444',
                    color: 'white',
                    hoverBg: '#dc2626'
                },
                outline: {
                    background: 'transparent',
                    color: '#3b82f6',
                    border: '2px solid #3b82f6',
                    hoverBg: '#3b82f6',
                    hoverColor: 'white'
                }
            };

            const btnStyle = styles[style] || styles.primary;
            
            button.style.cssText = `
                padding: 10px 20px;
                border-radius: 8px;
                border: none;
                font-size: 16px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s;
                background: ${btnStyle.background};
                color: ${btnStyle.color};
                ${btnStyle.border ? `border: ${btnStyle.border};` : ''}
            `;

            button.addEventListener('mouseenter', () => {
                button.style.background = btnStyle.hoverBg;
                if (btnStyle.hoverColor) {
                    button.style.color = btnStyle.hoverColor;
                }
            });

            button.addEventListener('mouseleave', () => {
                button.style.background = btnStyle.background;
                button.style.color = btnStyle.color;
            });

            if (options.disabled) {
                button.disabled = true;
                button.style.opacity = '0.5';
                button.style.cursor = 'not-allowed';
            }

            return button;
        }

        /**
         * Create card
         */
        static createCard(options = {}) {
            const {
                title = '',
                content = '',
                footer = '',
                className = '',
                style = ''
            } = options;

            const card = document.createElement('div');
            card.className = `card ${className}`;
            card.style.cssText = `
                background: white;
                border-radius: 12px;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                overflow: hidden;
                ${style}
            `;

            if (title) {
                const header = document.createElement('div');
                header.className = 'card-header';
                header.style.cssText = `
                    padding: 20px;
                    border-bottom: 1px solid #e5e7eb;
                `;
                
                const titleEl = document.createElement('h3');
                titleEl.textContent = title;
                titleEl.style.cssText = `
                    margin: 0;
                    font-size: 18px;
                    font-weight: 600;
                    color: #111827;
                `;
                header.appendChild(titleEl);
                card.appendChild(header);
            }

            const body = document.createElement('div');
            body.className = 'card-body';
            body.style.cssText = 'padding: 20px;';
            
            if (typeof content === 'string') {
                body.innerHTML = content;
            } else if (content instanceof HTMLElement) {
                body.appendChild(content);
            }
            card.appendChild(body);

            if (footer) {
                const footerEl = document.createElement('div');
                footerEl.className = 'card-footer';
                footerEl.style.cssText = `
                    padding: 16px 20px;
                    border-top: 1px solid #e5e7eb;
                    background: #f9fafb;
                `;
                
                if (typeof footer === 'string') {
                    footerEl.innerHTML = footer;
                } else if (footer instanceof HTMLElement) {
                    footerEl.appendChild(footer);
                }
                card.appendChild(footerEl);
            }

            return card;
        }

        /**
         * Create table
         */
        static createTable(options = {}) {
            const {
                columns = [],
                data = [],
                selectable = false,
                sortable = true,
                className = ''
            } = options;

            const wrapper = document.createElement('div');
            wrapper.className = `table-wrapper ${className}`;
            wrapper.style.cssText = 'overflow-x: auto;';

            const table = document.createElement('table');
            table.className = 'data-table';
            table.style.cssText = `
                width: 100%;
                border-collapse: collapse;
                font-size: 14px;
            `;

            // Create header
            const thead = document.createElement('thead');
            const headerRow = document.createElement('tr');
            headerRow.style.cssText = `
                background: #f9fafb;
                border-bottom: 2px solid #e5e7eb;
            `;

            if (selectable) {
                const selectTh = document.createElement('th');
                selectTh.style.cssText = 'padding: 12px 16px; text-align: left;';
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.addEventListener('change', (e) => {
                    const checkboxes = table.querySelectorAll('tbody input[type="checkbox"]');
                    checkboxes.forEach(cb => cb.checked = e.target.checked);
                });
                selectTh.appendChild(checkbox);
                headerRow.appendChild(selectTh);
            }

            columns.forEach((col, index) => {
                const th = document.createElement('th');
                th.textContent = col.label || col.key;
                th.style.cssText = `
                    padding: 12px 16px;
                    text-align: left;
                    font-weight: 600;
                    color: #374151;
                    cursor: ${sortable ? 'pointer' : 'default'};
                `;

                if (sortable) {
                    th.addEventListener('click', () => {
                        // Emit sort event
                        const event = new CustomEvent('tableSort', {
                            detail: { column: col.key, index }
                        });
                        table.dispatchEvent(event);
                    });
                }

                headerRow.appendChild(th);
            });

            thead.appendChild(headerRow);
            table.appendChild(thead);

            // Create body
            const tbody = document.createElement('tbody');
            
            data.forEach((row, rowIndex) => {
                const tr = document.createElement('tr');
                tr.style.cssText = `
                    border-bottom: 1px solid #e5e7eb;
                    transition: background 0.2s;
                `;
                tr.addEventListener('mouseenter', () => {
                    tr.style.background = '#f9fafb';
                });
                tr.addEventListener('mouseleave', () => {
                    tr.style.background = 'transparent';
                });

                if (selectable) {
                    const selectTd = document.createElement('td');
                    selectTd.style.cssText = 'padding: 12px 16px;';
                    const checkbox = document.createElement('input');
                    checkbox.type = 'checkbox';
                    checkbox.dataset.rowIndex = rowIndex;
                    selectTd.appendChild(checkbox);
                    tr.appendChild(selectTd);
                }

                columns.forEach(col => {
                    const td = document.createElement('td');
                    td.style.cssText = 'padding: 12px 16px; color: #111827;';
                    
                    if (col.render) {
                        const rendered = col.render(row[col.key], row, rowIndex);
                        if (typeof rendered === 'string') {
                            td.innerHTML = rendered;
                        } else if (rendered instanceof HTMLElement) {
                            td.appendChild(rendered);
                        }
                    } else {
                        td.textContent = row[col.key] || '';
                    }
                    
                    tr.appendChild(td);
                });

                tbody.appendChild(tr);
            });

            table.appendChild(tbody);
            wrapper.appendChild(table);

            return {
                element: wrapper,
                table,
                getSelected: () => {
                    if (!selectable) return [];
                    const checked = table.querySelectorAll('tbody input[type="checkbox"]:checked');
                    return Array.from(checked).map(cb => parseInt(cb.dataset.rowIndex));
                }
            };
        }

        /**
         * Create form field
         */
        static createFormField(options = {}) {
            const {
                type = 'text',
                label = '',
                name = '',
                value = '',
                placeholder = '',
                required = false,
                disabled = false,
                options: selectOptions = [],
                validation = null,
                helpText = ''
            } = options;

            const wrapper = document.createElement('div');
            wrapper.className = 'form-field';
            wrapper.style.cssText = 'margin-bottom: 20px;';

            if (label) {
                const labelEl = document.createElement('label');
                labelEl.textContent = label + (required ? ' *' : '');
                labelEl.style.cssText = `
                    display: block;
                    margin-bottom: 6px;
                    font-size: 14px;
                    font-weight: 500;
                    color: #374151;
                `;
                wrapper.appendChild(labelEl);
            }

            let input;
            
            if (type === 'textarea') {
                input = document.createElement('textarea');
                input.rows = 4;
            } else if (type === 'select') {
                input = document.createElement('select');
                selectOptions.forEach(opt => {
                    const option = document.createElement('option');
                    option.value = opt.value;
                    option.textContent = opt.label;
                    if (opt.value === value) option.selected = true;
                    input.appendChild(option);
                });
            } else {
                input = document.createElement('input');
                input.type = type;
            }

            input.name = name;
            input.value = value;
            input.placeholder = placeholder;
            input.required = required;
            input.disabled = disabled;
            input.className = 'form-input';
            input.style.cssText = `
                width: 100%;
                padding: 10px 14px;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                font-size: 16px;
                font-family: inherit;
                transition: border-color 0.2s, box-shadow 0.2s;
                box-sizing: border-box;
            `;

            input.addEventListener('focus', () => {
                input.style.borderColor = '#3b82f6';
                input.style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.1)';
            });

            input.addEventListener('blur', () => {
                input.style.borderColor = '#e5e7eb';
                input.style.boxShadow = 'none';
                
                if (validation) {
                    const error = validation(input.value);
                    if (error) {
                        this.showFieldError(wrapper, error);
                    } else {
                        this.clearFieldError(wrapper);
                    }
                }
            });

            wrapper.appendChild(input);

            if (helpText) {
                const help = document.createElement('p');
                help.className = 'help-text';
                help.textContent = helpText;
                help.style.cssText = `
                    margin: 6px 0 0 0;
                    font-size: 13px;
                    color: #6b7280;
                `;
                wrapper.appendChild(help);
            }

            return { wrapper, input };
        }

        /**
         * Show field error
         */
        static showFieldError(fieldWrapper, message) {
            this.clearFieldError(fieldWrapper);
            
            const input = fieldWrapper.querySelector('input, textarea, select');
            if (input) {
                input.style.borderColor = '#ef4444';
            }

            const error = document.createElement('p');
            error.className = 'field-error';
            error.textContent = message;
            error.style.cssText = `
                margin: 6px 0 0 0;
                font-size: 13px;
                color: #ef4444;
            `;
            fieldWrapper.appendChild(error);
        }

        /**
         * Clear field error
         */
        static clearFieldError(fieldWrapper) {
            const error = fieldWrapper.querySelector('.field-error');
            if (error) error.remove();
            
            const input = fieldWrapper.querySelector('input, textarea, select');
            if (input) {
                input.style.borderColor = '#e5e7eb';
            }
        }

        /**
         * Create loading spinner
         */
        static createSpinner(size = 'medium', color = '#3b82f6') {
            const spinner = document.createElement('div');
            spinner.className = `spinner spinner-${size}`;
            
            const sizes = {
                small: '16px',
                medium: '32px',
                large: '48px'
            };
            
            const spinnerSize = sizes[size] || sizes.medium;
            
            spinner.style.cssText = `
                width: ${spinnerSize};
                height: ${spinnerSize};
                border: 3px solid rgba(0, 0, 0, 0.1);
                border-top-color: ${color};
                border-radius: 50%;
                animation: spin 0.8s linear infinite;
            `;

            return spinner;
        }

        /**
         * Create badge
         */
        static createBadge(text, variant = 'default') {
            const badge = document.createElement('span');
            badge.className = `badge badge-${variant}`;
            badge.textContent = text;

            const variants = {
                default: { bg: '#e5e7eb', color: '#374151' },
                primary: { bg: '#dbeafe', color: '#1e40af' },
                success: { bg: '#d1fae5', color: '#065f46' },
                warning: { bg: '#fef3c7', color: '#92400e' },
                danger: { bg: '#fee2e2', color: '#991b1b' },
                info: { bg: '#e0e7ff', color: '#3730a3' }
            };

            const style = variants[variant] || variants.default;
            
            badge.style.cssText = `
                display: inline-flex;
                align-items: center;
                padding: 4px 10px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 500;
                background: ${style.bg};
                color: ${style.color};
            `;

            return badge;
        }

        /**
         * Create progress bar
         */
        static createProgressBar(value = 0, options = {}) {
            const {
                max = 100,
                showLabel = true,
                color = '#3b82f6',
                height = '8px',
                animated = false
            } = options;

            const container = document.createElement('div');
            container.className = 'progress-bar-container';
            container.style.cssText = `
                width: 100%;
                background: #e5e7eb;
                border-radius: 9999px;
                overflow: hidden;
                height: ${height};
                position: relative;
            `;

            const bar = document.createElement('div');
            bar.className = 'progress-bar';
            const percentage = Math.min((value / max) * 100, 100);
            bar.style.cssText = `
                height: 100%;
                background: ${color};
                width: ${percentage}%;
                transition: width 0.3s ease;
                ${animated ? 'animation: progressPulse 2s ease-in-out infinite;' : ''}
            `;

            container.appendChild(bar);

            if (showLabel) {
                const label = document.createElement('span');
                label.className = 'progress-label';
                label.textContent = `${Math.round(percentage)}%`;
                label.style.cssText = `
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    font-size: 11px;
                    font-weight: 600;
                    color: #111827;
                    pointer-events: none;
                `;
                container.appendChild(label);
            }

            return {
                element: container,
                setValue: (newValue) => {
                    const newPercentage = Math.min((newValue / max) * 100, 100);
                    bar.style.width = `${newPercentage}%`;
                    if (showLabel) {
                        const label = container.querySelector('.progress-label');
                        if (label) label.textContent = `${Math.round(newPercentage)}%`;
                    }
                }
            };
        }

        /**
         * Create tabs
         */
        static createTabs(options = {}) {
            const {
                tabs = [],
                activeTab = 0,
                onChange = null
            } = options;

            const container = document.createElement('div');
            container.className = 'tabs-container';

            const tabList = document.createElement('div');
            tabList.className = 'tab-list';
            tabList.style.cssText = `
                display: flex;
                gap: 8px;
                border-bottom: 2px solid #e5e7eb;
                margin-bottom: 20px;
            `;

            const panels = [];

            tabs.forEach((tab, index) => {
                const button = document.createElement('button');
                button.className = 'tab-button';
                button.textContent = tab.label;
                button.style.cssText = `
                    padding: 12px 20px;
                    border: none;
                    background: none;
                    font-size: 15px;
                    font-weight: 500;
                    color: ${index === activeTab ? '#3b82f6' : '#6b7280'};
                    cursor: pointer;
                    position: relative;
                    transition: color 0.2s;
                    border-bottom: 2px solid ${index === activeTab ? '#3b82f6' : 'transparent'};
                    margin-bottom: -2px;
                `;

                button.addEventListener('click', () => {
                    // Update button styles
                    tabList.querySelectorAll('.tab-button').forEach(btn => {
                        btn.style.color = '#6b7280';
                        btn.style.borderBottomColor = 'transparent';
                    });
                    button.style.color = '#3b82f6';
                    button.style.borderBottomColor = '#3b82f6';

                    // Show/hide panels
                    panels.forEach((panel, i) => {
                        panel.style.display = i === index ? 'block' : 'none';
                    });

                    if (onChange) onChange(index, tab);
                });

                tabList.appendChild(button);

                // Create panel
                const panel = document.createElement('div');
                panel.className = 'tab-panel';
                panel.style.display = index === activeTab ? 'block' : 'none';
                
                if (typeof tab.content === 'string') {
                    panel.innerHTML = tab.content;
                } else if (tab.content instanceof HTMLElement) {
                    panel.appendChild(tab.content);
                }
                
                panels.push(panel);
            });

            container.appendChild(tabList);
            panels.forEach(panel => container.appendChild(panel));

            return container;
        }
    }

    // Add CSS animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        @keyframes fadeOut {
            from { opacity: 1; }
            to { opacity: 0; }
        }
        
        @keyframes slideInUp {
            from {
                transform: translateY(20px);
                opacity: 0;
            }
            to {
                transform: translateY(0);
                opacity: 1;
            }
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
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        @keyframes progressPulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
    `;
    document.head.appendChild(style);

    // Export
    window.UIComponents = UIComponents;

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = UIComponents;
    }

})(window);
