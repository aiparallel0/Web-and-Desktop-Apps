/**
 * Form Validation System
 * Comprehensive validation with custom rules and error handling
 */

class Validator {
    constructor() {
        this.rules = new Map();
        this.customRules = new Map();
        this.messages = new Map();
        
        this.initializeDefaultRules();
        this.initializeDefaultMessages();
    }

    initializeDefaultRules() {
        this.rules.set('required', (value) => {
            if (value === null || value === undefined) return false;
            if (typeof value === 'string') return value.trim().length > 0;
            if (Array.isArray(value)) return value.length > 0;
            return true;
        });

        this.rules.set('email', (value) => {
            const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            return re.test(value);
        });

        this.rules.set('min', (value, min) => {
            if (typeof value === 'number') return value >= min;
            if (typeof value === 'string') return value.length >= min;
            if (Array.isArray(value)) return value.length >= min;
            return false;
        });

        this.rules.set('max', (value, max) => {
            if (typeof value === 'number') return value <= max;
            if (typeof value === 'string') return value.length <= max;
            if (Array.isArray(value)) return value.length <= max;
            return false;
        });

        this.rules.set('between', (value, min, max) => {
            const num = parseFloat(value);
            return num >= min && num <= max;
        });

        this.rules.set('alpha', (value) => {
            return /^[a-zA-Z]+$/.test(value);
        });

        this.rules.set('alphanumeric', (value) => {
            return /^[a-zA-Z0-9]+$/.test(value);
        });

        this.rules.set('numeric', (value) => {
            return /^[0-9]+$/.test(value);
        });

        this.rules.set('url', (value) => {
            try {
                new URL(value);
                return true;
            } catch {
                return false;
            }
        });

        this.rules.set('regex', (value, pattern) => {
            const re = new RegExp(pattern);
            return re.test(value);
        });

        this.rules.set('in', (value, ...options) => {
            return options.includes(value);
        });

        this.rules.set('notIn', (value, ...options) => {
            return !options.includes(value);
        });

        this.rules.set('confirmed', (value, confirmValue) => {
            return value === confirmValue;
        });

        this.rules.set('date', (value) => {
            const date = new Date(value);
            return date instanceof Date && !isNaN(date);
        });

        this.rules.set('before', (value, beforeDate) => {
            return new Date(value) < new Date(beforeDate);
        });

        this.rules.set('after', (value, afterDate) => {
            return new Date(value) > new Date(afterDate);
        });

        this.rules.set('creditCard', (value) => {
            const cleaned = value.replace(/\s/g, '');
            if (!/^[0-9]{13,19}$/.test(cleaned)) return false;
            
            let sum = 0;
            let isEven = false;
            
            for (let i = cleaned.length - 1; i >= 0; i--) {
                let digit = parseInt(cleaned[i]);
                
                if (isEven) {
                    digit *= 2;
                    if (digit > 9) digit -= 9;
                }
                
                sum += digit;
                isEven = !isEven;
            }
            
            return sum % 10 === 0;
        });

        this.rules.set('phone', (value) => {
            const cleaned = value.replace(/\D/g, '');
            return cleaned.length >= 10 && cleaned.length <= 15;
        });

        this.rules.set('zipCode', (value) => {
            return /^\d{5}(-\d{4})?$/.test(value);
        });

        this.rules.set('json', (value) => {
            try {
                JSON.parse(value);
                return true;
            } catch {
                return false;
            }
        });

        this.rules.set('file', (value) => {
            return value instanceof File;
        });

        this.rules.set('fileSize', (value, maxSize) => {
            if (!(value instanceof File)) return false;
            return value.size <= maxSize;
        });

        this.rules.set('fileType', (value, ...types) => {
            if (!(value instanceof File)) return false;
            return types.includes(value.type);
        });
    }

    initializeDefaultMessages() {
        this.messages.set('required', 'This field is required');
        this.messages.set('email', 'Please enter a valid email address');
        this.messages.set('min', 'Must be at least {0} characters');
        this.messages.set('max', 'Must not exceed {0} characters');
        this.messages.set('between', 'Must be between {0} and {1}');
        this.messages.set('alpha', 'Must contain only letters');
        this.messages.set('alphanumeric', 'Must contain only letters and numbers');
        this.messages.set('numeric', 'Must be a number');
        this.messages.set('url', 'Please enter a valid URL');
        this.messages.set('confirmed', 'Values do not match');
        this.messages.set('date', 'Please enter a valid date');
        this.messages.set('creditCard', 'Please enter a valid credit card number');
        this.messages.set('phone', 'Please enter a valid phone number');
        this.messages.set('zipCode', 'Please enter a valid ZIP code');
        this.messages.set('json', 'Please enter valid JSON');
        this.messages.set('file', 'Please select a file');
        this.messages.set('fileSize', 'File size must not exceed {0} bytes');
        this.messages.set('fileType', 'File type must be one of: {0}');
    }

    /**
     * Validate single value
     */
    validate(value, rules) {
        if (typeof rules === 'string') {
            rules = rules.split('|');
        }

        const errors = [];

        for (const ruleStr of rules) {
            const [ruleName, ...params] = ruleStr.split(':');
            const rule = this.rules.get(ruleName) || this.customRules.get(ruleName);

            if (!rule) {
                console.warn(`Unknown validation rule: ${ruleName}`);
                continue;
            }

            const args = params.length > 0 ? params[0].split(',') : [];
            const isValid = rule(value, ...args);

            if (!isValid) {
                const message = this.getMessage(ruleName, args);
                errors.push(message);
            }
        }

        return {
            valid: errors.length === 0,
            errors
        };
    }

    /**
     * Validate form data
     */
    validateForm(data, schema) {
        const errors = {};
        let isValid = true;

        for (const [field, rules] of Object.entries(schema)) {
            const value = data[field];
            const result = this.validate(value, rules);

            if (!result.valid) {
                errors[field] = result.errors;
                isValid = false;
            }
        }

        return {
            valid: isValid,
            errors
        };
    }

    /**
     * Add custom validation rule
     */
    addRule(name, validator, message) {
        this.customRules.set(name, validator);
        if (message) {
            this.messages.set(name, message);
        }
        return this;
    }

    /**
     * Get error message
     */
    getMessage(ruleName, params = []) {
        let message = this.messages.get(ruleName) || `Validation failed for ${ruleName}`;
        
        params.forEach((param, index) => {
            message = message.replace(`{${index}}`, param);
        });

        return message;
    }

    /**
     * Set custom message
     */
    setMessage(ruleName, message) {
        this.messages.set(ruleName, message);
        return this;
    }

    /**
     * Validate form element
     */
    validateElement(element) {
        const rules = element.getAttribute('data-validate');
        if (!rules) return { valid: true, errors: [] };

        return this.validate(element.value, rules);
    }

    /**
     * Attach validation to form
     */
    attachToForm(form, schema, options = {}) {
        const { onSubmit, showErrors = true } = options;

        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            const formData = new FormData(form);
            const data = Object.fromEntries(formData);

            const result = this.validateForm(data, schema);

            if (showErrors) {
                this.displayErrors(form, result.errors);
            }

            if (result.valid && onSubmit) {
                await onSubmit(data);
            }
        });

        // Real-time validation
        form.querySelectorAll('[data-validate]').forEach(element => {
            element.addEventListener('blur', () => {
                const field = element.name;
                const rules = schema[field];
                if (!rules) return;

                const result = this.validate(element.value, rules);
                
                if (showErrors) {
                    this.displayFieldError(element, result.errors);
                }
            });
        });
    }

    /**
     * Display validation errors
     */
    displayErrors(form, errors) {
        // Clear existing errors
        form.querySelectorAll('.error-message').forEach(el => el.remove());
        form.querySelectorAll('.error').forEach(el => el.classList.remove('error'));

        // Display new errors
        for (const [field, messages] of Object.entries(errors)) {
            const element = form.querySelector(`[name="${field}"]`);
            if (element) {
                this.displayFieldError(element, messages);
            }
        }
    }

    /**
     * Display field error
     */
    displayFieldError(element, errors) {
        // Remove existing error
        const existingError = element.parentElement.querySelector('.error-message');
        if (existingError) {
            existingError.remove();
        }
        element.classList.remove('error');

        // Add new error if any
        if (errors.length > 0) {
            element.classList.add('error');
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            errorDiv.textContent = errors[0];
            element.parentElement.appendChild(errorDiv);
        }
    }
}

const validator = new Validator();

if (typeof window !== 'undefined') {
    window.Validator = validator;
}

export default validator;
