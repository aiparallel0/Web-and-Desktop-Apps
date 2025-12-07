/**
 * Form Validator
 * Comprehensive client-side form validation with custom rules and real-time feedback
 */

class FormValidator {
    constructor(form, rules = {}, options = {}) {
        this.form = typeof form === 'string' ? document.querySelector(form) : form;
        this.rules = rules;
        this.options = {
            validateOnBlur: true,
            validateOnInput: false,
            showErrors: true,
            scrollToError: true,
            errorClass: 'form-error',
            errorMessageClass: 'form-error-message',
            ...options
        };
        
        this.errors = {};
        this.touched = {};
        this.isSubmitting = false;

        if (this.form) {
            this.init();
        }
    }

    /**
     * Initialize validator
     */
    init() {
        // Prevent default form submission
        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSubmit(e);
        });

        // Add validation listeners to fields
        Object.keys(this.rules).forEach(fieldName => {
            const field = this.getField(fieldName);
            if (!field) return;

            if (this.options.validateOnBlur) {
                field.addEventListener('blur', () => {
                    this.touched[fieldName] = true;
                    this.validateField(fieldName);
                });
            }

            if (this.options.validateOnInput) {
                field.addEventListener('input', () => {
                    if (this.touched[fieldName]) {
                        this.validateField(fieldName);
                    }
                });
            }
        });
    }

    /**
     * Get form field
     */
    getField(fieldName) {
        return this.form.querySelector(`[name="${fieldName}"]`);
    }

    /**
     * Get field value
     */
    getFieldValue(fieldName) {
        const field = this.getField(fieldName);
        if (!field) return '';

        if (field.type === 'checkbox') {
            return field.checked;
        } else if (field.type === 'radio') {
            const checked = this.form.querySelector(`[name="${fieldName}"]:checked`);
            return checked ? checked.value : '';
        } else {
            return field.value.trim();
        }
    }

    /**
     * Validate single field
     */
    validateField(fieldName) {
        const fieldRules = this.rules[fieldName];
        if (!fieldRules) return true;

        const value = this.getFieldValue(fieldName);
        const errors = [];

        // Required validation
        if (fieldRules.required) {
            const message = typeof fieldRules.required === 'string' 
                ? fieldRules.required 
                : 'This field is required';
            
            if (typeof value === 'boolean') {
                if (!value) errors.push(message);
            } else if (!value) {
                errors.push(message);
            }
        }

        // If field is empty and not required, skip other validations
        if (!value && !fieldRules.required) {
            this.clearFieldError(fieldName);
            return true;
        }

        // Min length validation
        if (fieldRules.minLength && value.length < fieldRules.minLength) {
            const message = fieldRules.minLengthMessage || 
                `Minimum ${fieldRules.minLength} characters required`;
            errors.push(message);
        }

        // Max length validation
        if (fieldRules.maxLength && value.length > fieldRules.maxLength) {
            const message = fieldRules.maxLengthMessage || 
                `Maximum ${fieldRules.maxLength} characters allowed`;
            errors.push(message);
        }

        // Min value validation
        if (fieldRules.min !== undefined) {
            const numValue = parseFloat(value);
            if (numValue < fieldRules.min) {
                const message = fieldRules.minMessage || 
                    `Minimum value is ${fieldRules.min}`;
                errors.push(message);
            }
        }

        // Max value validation
        if (fieldRules.max !== undefined) {
            const numValue = parseFloat(value);
            if (numValue > fieldRules.max) {
                const message = fieldRules.maxMessage || 
                    `Maximum value is ${fieldRules.max}`;
                errors.push(message);
            }
        }

        // Email validation
        if (fieldRules.email) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                const message = fieldRules.emailMessage || 'Invalid email address';
                errors.push(message);
            }
        }

        // URL validation
        if (fieldRules.url) {
            const urlRegex = /^https?:\/\/.+/i;
            if (!urlRegex.test(value)) {
                const message = fieldRules.urlMessage || 'Invalid URL';
                errors.push(message);
            }
        }

        // Pattern validation
        if (fieldRules.pattern) {
            const regex = new RegExp(fieldRules.pattern);
            if (!regex.test(value)) {
                const message = fieldRules.patternMessage || 'Invalid format';
                errors.push(message);
            }
        }

        // Match validation (for password confirmation, etc.)
        if (fieldRules.match) {
            const matchValue = this.getFieldValue(fieldRules.match);
            if (value !== matchValue) {
                const message = fieldRules.matchMessage || 'Values do not match';
                errors.push(message);
            }
        }

        // Custom validation function
        if (fieldRules.custom) {
            const customError = fieldRules.custom(value, this.getFormData());
            if (customError) {
                errors.push(customError);
            }
        }

        // Update errors
        if (errors.length > 0) {
            this.errors[fieldName] = errors[0]; // Show first error
            this.showFieldError(fieldName, errors[0]);
            return false;
        } else {
            this.clearFieldError(fieldName);
            return true;
        }
    }

    /**
     * Validate all fields
     */
    validateAll() {
        this.errors = {};
        let isValid = true;

        Object.keys(this.rules).forEach(fieldName => {
            this.touched[fieldName] = true;
            const fieldValid = this.validateField(fieldName);
            if (!fieldValid) {
                isValid = false;
            }
        });

        return isValid;
    }

    /**
     * Show field error
     */
    showFieldError(fieldName, message) {
        if (!this.options.showErrors) return;

        const field = this.getField(fieldName);
        if (!field) return;

        // Add error class to field
        field.classList.add(this.options.errorClass);

        // Find or create error message element
        let errorEl = field.parentElement.querySelector(`.${this.options.errorMessageClass}`);
        
        if (!errorEl) {
            errorEl = document.createElement('div');
            errorEl.className = this.options.errorMessageClass;
            errorEl.style.cssText = `
                color: #DC2626;
                font-size: 13px;
                margin-top: 4px;
            `;
            field.parentElement.appendChild(errorEl);
        }

        errorEl.textContent = message;
        errorEl.setAttribute('role', 'alert');
    }

    /**
     * Clear field error
     */
    clearFieldError(fieldName) {
        delete this.errors[fieldName];

        const field = this.getField(fieldName);
        if (!field) return;

        // Remove error class
        field.classList.remove(this.options.errorClass);

        // Remove error message
        const errorEl = field.parentElement.querySelector(`.${this.options.errorMessageClass}`);
        if (errorEl) {
            errorEl.remove();
        }
    }

    /**
     * Clear all errors
     */
    clearAllErrors() {
        Object.keys(this.errors).forEach(fieldName => {
            this.clearFieldError(fieldName);
        });
        this.errors = {};
    }

    /**
     * Get form data
     */
    getFormData() {
        const data = {};
        Object.keys(this.rules).forEach(fieldName => {
            data[fieldName] = this.getFieldValue(fieldName);
        });
        return data;
    }

    /**
     * Set form data
     */
    setFormData(data) {
        Object.keys(data).forEach(fieldName => {
            const field = this.getField(fieldName);
            if (!field) return;

            if (field.type === 'checkbox') {
                field.checked = !!data[fieldName];
            } else if (field.type === 'radio') {
                const radio = this.form.querySelector(`[name="${fieldName}"][value="${data[fieldName]}"]`);
                if (radio) radio.checked = true;
            } else {
                field.value = data[fieldName];
            }
        });
    }

    /**
     * Reset form
     */
    reset() {
        this.form.reset();
        this.clearAllErrors();
        this.touched = {};
        this.isSubmitting = false;
    }

    /**
     * Handle form submission
     */
    async handleSubmit(e) {
        if (this.isSubmitting) return;

        const isValid = this.validateAll();

        if (!isValid) {
            // Scroll to first error
            if (this.options.scrollToError) {
                const firstErrorField = Object.keys(this.errors)[0];
                const field = this.getField(firstErrorField);
                if (field) {
                    field.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    field.focus();
                }
            }
            return;
        }

        // Call onSubmit callback if provided
        if (this.options.onSubmit) {
            this.isSubmitting = true;
            try {
                await this.options.onSubmit(this.getFormData(), e);
            } catch (error) {
                console.error('Form submission error:', error);
            } finally {
                this.isSubmitting = false;
            }
        }
    }

    /**
     * Get errors
     */
    getErrors() {
        return { ...this.errors };
    }

    /**
     * Check if field has error
     */
    hasError(fieldName) {
        return !!this.errors[fieldName];
    }

    /**
     * Check if form is valid
     */
    isValid() {
        return Object.keys(this.errors).length === 0;
    }

    /**
     * Destroy validator
     */
    destroy() {
        this.clearAllErrors();
        this.form = null;
        this.rules = {};
        this.errors = {};
        this.touched = {};
    }
}

// Validation helpers
const ValidationRules = {
    /**
     * Email validation rule
     */
    email(message = 'Invalid email address') {
        return {
            email: true,
            emailMessage: message
        };
    },

    /**
     * Required validation rule
     */
    required(message = 'This field is required') {
        return {
            required: message
        };
    },

    /**
     * Min length validation rule
     */
    minLength(length, message) {
        return {
            minLength: length,
            minLengthMessage: message || `Minimum ${length} characters required`
        };
    },

    /**
     * Max length validation rule
     */
    maxLength(length, message) {
        return {
            maxLength: length,
            maxLengthMessage: message || `Maximum ${length} characters allowed`
        };
    },

    /**
     * Password validation rule
     */
    password(options = {}) {
        const {
            minLength = 8,
            requireUppercase = true,
            requireLowercase = true,
            requireNumber = true,
            requireSpecial = false
        } = options;

        return {
            minLength,
            custom: (value) => {
                if (requireUppercase && !/[A-Z]/.test(value)) {
                    return 'Password must contain an uppercase letter';
                }
                if (requireLowercase && !/[a-z]/.test(value)) {
                    return 'Password must contain a lowercase letter';
                }
                if (requireNumber && !/\d/.test(value)) {
                    return 'Password must contain a number';
                }
                if (requireSpecial && !/[!@#$%^&*]/.test(value)) {
                    return 'Password must contain a special character';
                }
                return null;
            }
        };
    },

    /**
     * Match validation rule (for password confirmation)
     */
    match(fieldName, message) {
        return {
            match: fieldName,
            matchMessage: message || 'Values do not match'
        };
    },

    /**
     * URL validation rule
     */
    url(message = 'Invalid URL') {
        return {
            url: true,
            urlMessage: message
        };
    },

    /**
     * Pattern validation rule
     */
    pattern(regex, message = 'Invalid format') {
        return {
            pattern: regex,
            patternMessage: message
        };
    },

    /**
     * Range validation rule
     */
    range(min, max, message) {
        return {
            min,
            max,
            minMessage: message || `Value must be between ${min} and ${max}`,
            maxMessage: message || `Value must be between ${min} and ${max}`
        };
    },

    /**
     * Custom validation rule
     */
    custom(validator, message = 'Validation failed') {
        return {
            custom: (value, formData) => {
                const valid = validator(value, formData);
                return valid ? null : message;
            }
        };
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { FormValidator, ValidationRules };
}
