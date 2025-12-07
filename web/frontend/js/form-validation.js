/**
 * Form Validation and Utilities
 * Comprehensive form validation, handling, and utility functions
 * @version 2.0.0
 */

(function(window) {
    'use strict';

    /**
     * Form Validator Class
     */
    class FormValidator {
        constructor(formElement, rules = {}) {
            this.form = formElement;
            this.rules = rules;
            this.errors = new Map();
            this.touched = new Set();
            this.listeners = new Map();
            this.customValidators = new Map();
            this.init();
        }

        /**
         * Initialize validator
         */
        init() {
            if (!this.form) return;

            // Add form submission handler
            this.form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleSubmit();
            });

            // Add real-time validation
            this.form.querySelectorAll('input, textarea, select').forEach(field => {
                // Validate on blur
                field.addEventListener('blur', () => {
                    this.touched.add(field.name);
                    this.validateField(field);
                });

                // Validate on input (with debounce)
                let debounceTimer;
                field.addEventListener('input', () => {
                    clearTimeout(debounceTimer);
                    debounceTimer = setTimeout(() => {
                        if (this.touched.has(field.name)) {
                            this.validateField(field);
                        }
                    }, 300);
                });
            });
        }

        /**
         * Validate field
         */
        validateField(field) {
            const fieldName = field.name || field.id;
            if (!fieldName) return true;

            const fieldRules = this.rules[fieldName];
            if (!fieldRules) return true;

            const value = this.getFieldValue(field);
            const errors = [];

            // Apply each rule
            Object.entries(fieldRules).forEach(([ruleName, ruleValue]) => {
                const validator = this.getValidator(ruleName);
                
                if (validator) {
                    const result = validator(value, ruleValue, field);
                    if (result !== true) {
                        errors.push(result);
                    }
                }
            });

            // Update errors map
            if (errors.length > 0) {
                this.errors.set(fieldName, errors);
                this.showFieldError(field, errors[0]);
                this.emit('fieldInvalid', { field: fieldName, errors });
            } else {
                this.errors.delete(fieldName);
                this.clearFieldError(field);
                this.emit('fieldValid', { field: fieldName });
            }

            return errors.length === 0;
        }

        /**
         * Get field value
         */
        getFieldValue(field) {
            if (field.type === 'checkbox') {
                return field.checked;
            } else if (field.type === 'radio') {
                const checkedRadio = this.form.querySelector(`input[name="${field.name}"]:checked`);
                return checkedRadio ? checkedRadio.value : '';
            } else if (field.type === 'file') {
                return field.files;
            }
            return field.value;
        }

        /**
         * Get validator function
         */
        getValidator(ruleName) {
            // Check custom validators first
            if (this.customValidators.has(ruleName)) {
                return this.customValidators.get(ruleName);
            }

            // Built-in validators
            const validators = {
                required: (value) => {
                    if (typeof value === 'boolean') return value;
                    if (value instanceof FileList) return value.length > 0 || 'This field is required';
                    return (value && value.toString().trim() !== '') || 'This field is required';
                },

                email: (value) => {
                    if (!value) return true;
                    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                    return emailRegex.test(value) || 'Please enter a valid email address';
                },

                url: (value) => {
                    if (!value) return true;
                    try {
                        new URL(value);
                        return true;
                    } catch {
                        return 'Please enter a valid URL';
                    }
                },

                minLength: (value, min) => {
                    if (!value) return true;
                    return value.length >= min || `Minimum length is ${min} characters`;
                },

                maxLength: (value, max) => {
                    if (!value) return true;
                    return value.length <= max || `Maximum length is ${max} characters`;
                },

                min: (value, min) => {
                    if (!value) return true;
                    const num = parseFloat(value);
                    return num >= min || `Minimum value is ${min}`;
                },

                max: (value, max) => {
                    if (!value) return true;
                    const num = parseFloat(value);
                    return num <= max || `Maximum value is ${max}`;
                },

                pattern: (value, pattern) => {
                    if (!value) return true;
                    const regex = new RegExp(pattern);
                    return regex.test(value) || 'Please match the required format';
                },

                match: (value, fieldName) => {
                    const matchField = this.form.querySelector(`[name="${fieldName}"]`);
                    if (!matchField) return true;
                    return value === matchField.value || 'Fields do not match';
                },

                numeric: (value) => {
                    if (!value) return true;
                    return !isNaN(value) || 'Please enter a valid number';
                },

                alphanumeric: (value) => {
                    if (!value) return true;
                    return /^[a-zA-Z0-9]+$/.test(value) || 'Only letters and numbers are allowed';
                },

                alpha: (value) => {
                    if (!value) return true;
                    return /^[a-zA-Z]+$/.test(value) || 'Only letters are allowed';
                },

                phone: (value) => {
                    if (!value) return true;
                    const phoneRegex = /^[\d\s\-\+\(\)]+$/;
                    return phoneRegex.test(value) || 'Please enter a valid phone number';
                },

                date: (value) => {
                    if (!value) return true;
                    const date = new Date(value);
                    return !isNaN(date.getTime()) || 'Please enter a valid date';
                },

                minDate: (value, minDate) => {
                    if (!value) return true;
                    const date = new Date(value);
                    const min = new Date(minDate);
                    return date >= min || `Date must be on or after ${minDate}`;
                },

                maxDate: (value, maxDate) => {
                    if (!value) return true;
                    const date = new Date(value);
                    const max = new Date(maxDate);
                    return date <= max || `Date must be on or before ${maxDate}`;
                },

                fileSize: (files, maxSize) => {
                    if (!files || files.length === 0) return true;
                    for (let file of files) {
                        if (file.size > maxSize) {
                            return `File size must be less than ${this.formatFileSize(maxSize)}`;
                        }
                    }
                    return true;
                },

                fileType: (files, allowedTypes) => {
                    if (!files || files.length === 0) return true;
                    const types = Array.isArray(allowedTypes) ? allowedTypes : [allowedTypes];
                    
                    for (let file of files) {
                        const isAllowed = types.some(type => {
                            if (type.endsWith('/*')) {
                                return file.type.startsWith(type.split('/')[0] + '/');
                            }
                            return file.type === type;
                        });
                        
                        if (!isAllowed) {
                            return `File type must be one of: ${types.join(', ')}`;
                        }
                    }
                    return true;
                },

                strongPassword: (value) => {
                    if (!value) return true;
                    const hasLength = value.length >= 8;
                    const hasUpper = /[A-Z]/.test(value);
                    const hasLower = /[a-z]/.test(value);
                    const hasNumber = /[0-9]/.test(value);
                    const hasSpecial = /[^a-zA-Z0-9]/.test(value);

                    const checks = [hasLength, hasUpper, hasLower, hasNumber, hasSpecial];
                    const passed = checks.filter(Boolean).length;

                    if (passed < 4) {
                        return 'Password must include: uppercase, lowercase, number, and special character';
                    }
                    return true;
                },

                creditCard: (value) => {
                    if (!value) return true;
                    // Luhn algorithm
                    const cleaned = value.replace(/\s/g, '');
                    if (!/^\d+$/.test(cleaned)) return 'Please enter a valid credit card number';

                    let sum = 0;
                    let isEven = false;

                    for (let i = cleaned.length - 1; i >= 0; i--) {
                        let digit = parseInt(cleaned[i]);

                        if (isEven) {
                            digit *= 2;
                            if (digit > 9) {
                                digit -= 9;
                            }
                        }

                        sum += digit;
                        isEven = !isEven;
                    }

                    return (sum % 10 === 0) || 'Please enter a valid credit card number';
                },

                zipCode: (value) => {
                    if (!value) return true;
                    // US zip code (5 or 9 digits)
                    const zipRegex = /^\d{5}(-\d{4})?$/;
                    return zipRegex.test(value) || 'Please enter a valid zip code';
                },

                username: (value) => {
                    if (!value) return true;
                    const usernameRegex = /^[a-zA-Z0-9_-]{3,16}$/;
                    return usernameRegex.test(value) || 'Username must be 3-16 characters (letters, numbers, _, -)';
                }
            };

            return validators[ruleName];
        }

        /**
         * Add custom validator
         */
        addValidator(name, validatorFunction) {
            this.customValidators.set(name, validatorFunction);
        }

        /**
         * Validate all fields
         */
        validateAll() {
            this.errors.clear();
            
            this.form.querySelectorAll('input, textarea, select').forEach(field => {
                this.touched.add(field.name || field.id);
                this.validateField(field);
            });

            const isValid = this.errors.size === 0;
            this.emit('formValidated', { isValid, errors: Array.from(this.errors.entries()) });
            
            return isValid;
        }

        /**
         * Handle form submission
         */
        async handleSubmit() {
            const isValid = this.validateAll();

            if (isValid) {
                const formData = this.getFormData();
                this.emit('formSubmit', formData);
            } else {
                this.emit('formInvalid', { errors: Array.from(this.errors.entries()) });
                
                // Focus first invalid field
                const firstError = Array.from(this.errors.keys())[0];
                const field = this.form.querySelector(`[name="${firstError}"]`);
                if (field) field.focus();
            }
        }

        /**
         * Get form data
         */
        getFormData() {
            const data = {};
            const formData = new FormData(this.form);

            for (let [key, value] of formData.entries()) {
                // Handle multiple values (checkboxes)
                if (data[key]) {
                    if (!Array.isArray(data[key])) {
                        data[key] = [data[key]];
                    }
                    data[key].push(value);
                } else {
                    data[key] = value;
                }
            }

            return data;
        }

        /**
         * Show field error
         */
        showFieldError(field, message) {
            this.clearFieldError(field);

            // Add error class to field
            field.classList.add('is-invalid');
            field.style.borderColor = '#ef4444';

            // Create error message element
            const errorEl = document.createElement('div');
            errorEl.className = 'field-error';
            errorEl.textContent = message;
            errorEl.style.cssText = `
                margin-top: 6px;
                font-size: 13px;
                color: #ef4444;
            `;

            // Insert after field or after field wrapper
            const wrapper = field.closest('.form-field, .form-group');
            if (wrapper) {
                wrapper.appendChild(errorEl);
            } else {
                field.parentNode.insertBefore(errorEl, field.nextSibling);
            }
        }

        /**
         * Clear field error
         */
        clearFieldError(field) {
            field.classList.remove('is-invalid');
            field.style.borderColor = '';

            // Remove error message
            const wrapper = field.closest('.form-field, .form-group');
            const errorEl = wrapper ? wrapper.querySelector('.field-error') : field.parentNode.querySelector('.field-error');
            
            if (errorEl) {
                errorEl.remove();
            }
        }

        /**
         * Reset form
         */
        reset() {
            this.form.reset();
            this.errors.clear();
            this.touched.clear();
            
            // Clear all error displays
            this.form.querySelectorAll('input, textarea, select').forEach(field => {
                this.clearFieldError(field);
            });

            this.emit('formReset');
        }

        /**
         * Set field value
         */
        setFieldValue(fieldName, value) {
            const field = this.form.querySelector(`[name="${fieldName}"]`);
            if (!field) return;

            if (field.type === 'checkbox') {
                field.checked = Boolean(value);
            } else if (field.type === 'radio') {
                const radio = this.form.querySelector(`[name="${fieldName}"][value="${value}"]`);
                if (radio) radio.checked = true;
            } else {
                field.value = value;
            }
        }

        /**
         * Get field value
         */
        getFieldValueByName(fieldName) {
            const field = this.form.querySelector(`[name="${fieldName}"]`);
            return field ? this.getFieldValue(field) : null;
        }

        /**
         * Disable form
         */
        disable() {
            this.form.querySelectorAll('input, textarea, select, button').forEach(el => {
                el.disabled = true;
            });
        }

        /**
         * Enable form
         */
        enable() {
            this.form.querySelectorAll('input, textarea, select, button').forEach(el => {
                el.disabled = false;
            });
        }

        /**
         * Format file size
         */
        formatFileSize(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }

        /**
         * Event emitter
         */
        on(event, callback) {
            if (!this.listeners.has(event)) {
                this.listeners.set(event, new Set());
            }
            this.listeners.get(event).add(callback);
        }

        off(event, callback) {
            if (this.listeners.has(event)) {
                this.listeners.get(event).delete(callback);
            }
        }

        emit(event, data) {
            if (this.listeners.has(event)) {
                this.listeners.get(event).forEach(callback => {
                    try {
                        callback(data);
                    } catch (error) {
                        console.error(`Error in event listener for ${event}:`, error);
                    }
                });
            }
        }
    }

    /**
     * Form Builder
     */
    class FormBuilder {
        constructor() {
            this.fields = [];
        }

        /**
         * Add text field
         */
        addTextField(options = {}) {
            this.fields.push({
                type: 'text',
                label: options.label || 'Text Field',
                name: options.name || 'textField',
                placeholder: options.placeholder || '',
                required: options.required || false,
                value: options.value || '',
                ...options
            });
            return this;
        }

        /**
         * Add email field
         */
        addEmailField(options = {}) {
            this.fields.push({
                type: 'email',
                label: options.label || 'Email',
                name: options.name || 'email',
                placeholder: options.placeholder || 'your@email.com',
                required: options.required || false,
                value: options.value || '',
                ...options
            });
            return this;
        }

        /**
         * Add password field
         */
        addPasswordField(options = {}) {
            this.fields.push({
                type: 'password',
                label: options.label || 'Password',
                name: options.name || 'password',
                placeholder: options.placeholder || '',
                required: options.required || false,
                ...options
            });
            return this;
        }

        /**
         * Add textarea
         */
        addTextarea(options = {}) {
            this.fields.push({
                type: 'textarea',
                label: options.label || 'Text Area',
                name: options.name || 'textarea',
                placeholder: options.placeholder || '',
                required: options.required || false,
                rows: options.rows || 4,
                value: options.value || '',
                ...options
            });
            return this;
        }

        /**
         * Add select field
         */
        addSelect(options = {}) {
            this.fields.push({
                type: 'select',
                label: options.label || 'Select',
                name: options.name || 'select',
                required: options.required || false,
                options: options.options || [],
                value: options.value || '',
                ...options
            });
            return this;
        }

        /**
         * Add checkbox
         */
        addCheckbox(options = {}) {
            this.fields.push({
                type: 'checkbox',
                label: options.label || 'Checkbox',
                name: options.name || 'checkbox',
                checked: options.checked || false,
                ...options
            });
            return this;
        }

        /**
         * Add radio group
         */
        addRadioGroup(options = {}) {
            this.fields.push({
                type: 'radio',
                label: options.label || 'Radio Group',
                name: options.name || 'radioGroup',
                options: options.options || [],
                value: options.value || '',
                ...options
            });
            return this;
        }

        /**
         * Add file field
         */
        addFileField(options = {}) {
            this.fields.push({
                type: 'file',
                label: options.label || 'File',
                name: options.name || 'file',
                accept: options.accept || '*',
                multiple: options.multiple || false,
                ...options
            });
            return this;
        }

        /**
         * Add custom HTML
         */
        addCustomHTML(html) {
            this.fields.push({
                type: 'custom',
                html: html
            });
            return this;
        }

        /**
         * Build form
         */
        build(containerIdOrElement) {
            const container = typeof containerIdOrElement === 'string'
                ? document.getElementById(containerIdOrElement)
                : containerIdOrElement;

            if (!container) {
                console.error('Container not found');
                return null;
            }

            const form = document.createElement('form');
            form.className = 'auto-form';
            form.style.cssText = 'max-width: 600px;';

            this.fields.forEach(field => {
                const fieldEl = this.createField(field);
                if (fieldEl) {
                    form.appendChild(fieldEl);
                }
            });

            container.innerHTML = '';
            container.appendChild(form);

            return form;
        }

        /**
         * Create field element
         */
        createField(field) {
            if (field.type === 'custom') {
                const div = document.createElement('div');
                div.innerHTML = field.html;
                return div.firstElementChild;
            }

            const wrapper = document.createElement('div');
            wrapper.className = 'form-field';
            wrapper.style.cssText = 'margin-bottom: 20px;';

            // Label
            if (field.label && field.type !== 'checkbox') {
                const label = document.createElement('label');
                label.textContent = field.label + (field.required ? ' *' : '');
                label.style.cssText = `
                    display: block;
                    margin-bottom: 6px;
                    font-size: 14px;
                    font-weight: 500;
                    color: #374151;
                `;
                wrapper.appendChild(label);
            }

            // Input element
            let input;

            switch (field.type) {
                case 'textarea':
                    input = document.createElement('textarea');
                    input.rows = field.rows;
                    break;

                case 'select':
                    input = document.createElement('select');
                    field.options.forEach(opt => {
                        const option = document.createElement('option');
                        option.value = opt.value;
                        option.textContent = opt.label;
                        if (opt.value === field.value) {
                            option.selected = true;
                        }
                        input.appendChild(option);
                    });
                    break;

                case 'checkbox':
                    const checkboxWrapper = document.createElement('div');
                    checkboxWrapper.style.cssText = 'display: flex; align-items: center; gap: 8px;';
                    
                    input = document.createElement('input');
                    input.type = 'checkbox';
                    input.checked = field.checked;
                    
                    const checkboxLabel = document.createElement('label');
                    checkboxLabel.textContent = field.label + (field.required ? ' *' : '');
                    checkboxLabel.style.cssText = 'font-size: 14px; color: #374151; cursor: pointer;';
                    
                    checkboxWrapper.appendChild(input);
                    checkboxWrapper.appendChild(checkboxLabel);
                    wrapper.appendChild(checkboxWrapper);
                    break;

                case 'radio':
                    field.options.forEach(opt => {
                        const radioWrapper = document.createElement('div');
                        radioWrapper.style.cssText = 'display: flex; align-items: center; gap: 8px; margin-bottom: 8px;';
                        
                        const radio = document.createElement('input');
                        radio.type = 'radio';
                        radio.name = field.name;
                        radio.value = opt.value;
                        radio.checked = opt.value === field.value;
                        
                        const radioLabel = document.createElement('label');
                        radioLabel.textContent = opt.label;
                        radioLabel.style.cssText = 'font-size: 14px; color: #374151; cursor: pointer;';
                        
                        radioWrapper.appendChild(radio);
                        radioWrapper.appendChild(radioLabel);
                        wrapper.appendChild(radioWrapper);
                    });
                    return wrapper;

                default:
                    input = document.createElement('input');
                    input.type = field.type;
            }

            if (input && field.type !== 'checkbox') {
                input.name = field.name;
                input.placeholder = field.placeholder || '';
                input.required = field.required || false;

                if (field.value !== undefined && field.type !== 'file') {
                    input.value = field.value;
                }

                if (field.accept) input.accept = field.accept;
                if (field.multiple) input.multiple = field.multiple;

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
                });

                if (field.type !== 'checkbox') {
                    wrapper.appendChild(input);
                }
            }

            // Help text
            if (field.helpText) {
                const help = document.createElement('p');
                help.textContent = field.helpText;
                help.style.cssText = `
                    margin: 6px 0 0 0;
                    font-size: 13px;
                    color: #6b7280;
                `;
                wrapper.appendChild(help);
            }

            return wrapper;
        }

        /**
         * Clear fields
         */
        clear() {
            this.fields = [];
            return this;
        }
    }

    /**
     * Form Auto-Save
     */
    class FormAutoSave {
        constructor(formElement, options = {}) {
            this.form = formElement;
            this.storageKey = options.storageKey || 'form_autosave_' + (this.form.id || 'default');
            this.debounceDelay = options.debounceDelay || 1000;
            this.exclude = options.exclude || [];
            this.debounceTimer = null;
            this.init();
        }

        init() {
            if (!this.form) return;

            // Load saved data
            this.load();

            // Setup auto-save
            this.form.addEventListener('input', () => {
                clearTimeout(this.debounceTimer);
                this.debounceTimer = setTimeout(() => {
                    this.save();
                }, this.debounceDelay);
            });

            // Clear on submit
            this.form.addEventListener('submit', () => {
                this.clear();
            });
        }

        save() {
            const data = {};
            const formData = new FormData(this.form);

            for (let [key, value] of formData.entries()) {
                if (!this.exclude.includes(key)) {
                    data[key] = value;
                }
            }

            localStorage.setItem(this.storageKey, JSON.stringify(data));
            console.log('Form auto-saved');
        }

        load() {
            try {
                const saved = localStorage.getItem(this.storageKey);
                if (!saved) return;

                const data = JSON.parse(saved);
                
                Object.entries(data).forEach(([key, value]) => {
                    const field = this.form.querySelector(`[name="${key}"]`);
                    if (field && !this.exclude.includes(key)) {
                        if (field.type === 'checkbox') {
                            field.checked = Boolean(value);
                        } else if (field.type !== 'file') {
                            field.value = value;
                        }
                    }
                });

                console.log('Form data loaded from auto-save');
            } catch (error) {
                console.error('Error loading auto-saved data:', error);
            }
        }

        clear() {
            localStorage.removeItem(this.storageKey);
        }
    }

    // Export
    window.FormValidator = FormValidator;
    window.FormBuilder = FormBuilder;
    window.FormAutoSave = FormAutoSave;

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = { FormValidator, FormBuilder, FormAutoSave };
    }

})(window);
