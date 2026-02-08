/**
 * Input Validation Utilities
 * Comprehensive validation for files, forms, and user inputs
 */

class Validators {
    /**
     * Validate image file
     */
    static validateImageFile(file, options = {}) {
        const {
            maxSize = 100 * 1024 * 1024, // 100MB default
            minSize = 1024, // 1KB minimum
            allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif', 'image/bmp', 'application/pdf'],
            allowedExtensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.pdf']
        } = options;

        const errors = [];

        // Check if file exists
        if (!file) {
            errors.push('No file provided');
            return { valid: false, errors };
        }

        // Check file type
        if (!allowedTypes.includes(file.type)) {
            errors.push(`Invalid file type: ${file.type}. Allowed types: ${allowedTypes.join(', ')}`);
        }

        // Check file extension
        const fileName = file.name.toLowerCase();
        const hasValidExtension = allowedExtensions.some(ext => fileName.endsWith(ext));
        if (!hasValidExtension) {
            errors.push(`Invalid file extension. Allowed extensions: ${allowedExtensions.join(', ')}`);
        }

        // Check file size
        if (file.size > maxSize) {
            errors.push(`File size (${this.formatFileSize(file.size)}) exceeds maximum allowed size (${this.formatFileSize(maxSize)})`);
        }

        if (file.size < minSize) {
            errors.push(`File size (${this.formatFileSize(file.size)}) is below minimum required size (${this.formatFileSize(minSize)})`);
        }

        // Check file name
        if (file.name.length > 255) {
            errors.push('File name is too long (max 255 characters)');
        }

        return {
            valid: errors.length === 0,
            errors,
            warnings: this.getFileWarnings(file, options)
        };
    }

    /**
     * Get file warnings (non-blocking issues)
     */
    static getFileWarnings(file, options = {}) {
        const warnings = [];
        const largeFileThreshold = options.largeFileThreshold || 10 * 1024 * 1024; // 10MB

        if (file.size > largeFileThreshold) {
            warnings.push(`Large file detected (${this.formatFileSize(file.size)}). Processing may take longer.`);
        }

        if (file.type === 'application/pdf') {
            warnings.push('PDF files may require additional processing time.');
        }

        return warnings;
    }

    /**
     * Format file size for display
     */
    static formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
    }

    /**
     * Validate extraction settings
     */
    static validateExtractionSettings(settings) {
        const errors = [];

        // Validate model ID
        if (!settings.modelId || typeof settings.modelId !== 'string') {
            errors.push('Invalid or missing model ID');
        }

        // Validate detection mode
        const validModes = ['auto', 'manual', 'line', 'column'];
        if (!validModes.includes(settings.detectionMode)) {
            errors.push(`Invalid detection mode: ${settings.detectionMode}. Must be one of: ${validModes.join(', ')}`);
        }

        // Validate manual regions if provided
        if (settings.manualRegions) {
            if (!Array.isArray(settings.manualRegions)) {
                errors.push('Manual regions must be an array');
            } else {
                settings.manualRegions.forEach((region, idx) => {
                    if (!this.isValidRegion(region)) {
                        errors.push(`Invalid region at index ${idx}`);
                    }
                });
            }
        }

        return {
            valid: errors.length === 0,
            errors
        };
    }

    /**
     * Validate a region object
     */
    static isValidRegion(region) {
        return region
            && typeof region.x === 'number'
            && typeof region.y === 'number'
            && typeof region.width === 'number'
            && typeof region.height === 'number'
            && region.x >= 0
            && region.y >= 0
            && region.width > 0
            && region.height > 0;
    }

    /**
     * Validate email address
     */
    static validateEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return {
            valid: emailRegex.test(email),
            errors: emailRegex.test(email) ? [] : ['Invalid email address format']
        };
    }

    /**
     * Validate URL
     */
    static validateUrl(url) {
        try {
            new URL(url);
            return { valid: true, errors: [] };
        } catch (e) {
            return { valid: false, errors: ['Invalid URL format'] };
        }
    }

    /**
     * Validate required field
     */
    static validateRequired(value, fieldName = 'Field') {
        const isEmpty = value === null
            || value === undefined
            || (typeof value === 'string' && value.trim() === '')
            || (Array.isArray(value) && value.length === 0);

        return {
            valid: !isEmpty,
            errors: isEmpty ? [`${fieldName} is required`] : []
        };
    }

    /**
     * Validate string length
     */
    static validateLength(value, min, max, fieldName = 'Field') {
        const errors = [];
        const length = value ? value.length : 0;

        if (min !== undefined && length < min) {
            errors.push(`${fieldName} must be at least ${min} characters`);
        }

        if (max !== undefined && length > max) {
            errors.push(`${fieldName} must not exceed ${max} characters`);
        }

        return {
            valid: errors.length === 0,
            errors
        };
    }

    /**
     * Validate number range
     */
    static validateRange(value, min, max, fieldName = 'Field') {
        const errors = [];
        const num = Number(value);

        if (isNaN(num)) {
            errors.push(`${fieldName} must be a number`);
            return { valid: false, errors };
        }

        if (min !== undefined && num < min) {
            errors.push(`${fieldName} must be at least ${min}`);
        }

        if (max !== undefined && num > max) {
            errors.push(`${fieldName} must not exceed ${max}`);
        }

        return {
            valid: errors.length === 0,
            errors
        };
    }

    /**
     * Validate pattern (regex)
     */
    static validatePattern(value, pattern, fieldName = 'Field', errorMessage = null) {
        const regex = typeof pattern === 'string' ? new RegExp(pattern) : pattern;
        const valid = regex.test(value);

        return {
            valid,
            errors: valid ? [] : [errorMessage || `${fieldName} format is invalid`]
        };
    }

    /**
     * Sanitize filename
     */
    static sanitizeFilename(filename) {
        return filename
            .replace(/[^a-zA-Z0-9._-]/g, '_')
            .replace(/_{2,}/g, '_')
            .substring(0, 255);
    }

    /**
     * Sanitize HTML to prevent XSS
     */
    static sanitizeHtml(html) {
        const div = document.createElement('div');
        div.textContent = html;
        return div.innerHTML;
    }

    /**
     * Validate form data
     */
    static validateForm(formData, rules) {
        const errors = {};
        let isValid = true;

        for (const [field, fieldRules] of Object.entries(rules)) {
            const value = formData[field];
            const fieldErrors = [];

            for (const rule of fieldRules) {
                const result = rule.validator(value, rule.params);
                if (!result.valid) {
                    fieldErrors.push(...result.errors);
                    isValid = false;
                }
            }

            if (fieldErrors.length > 0) {
                errors[field] = fieldErrors;
            }
        }

        return {
            valid: isValid,
            errors
        };
    }

    /**
     * Create validation rule
     */
    static rule(validator, params = {}) {
        return { validator, params };
    }
}

/**
 * Pre-defined validation rules
 */
const ValidationRules = {
    required: (fieldName) => Validators.rule(
        (value) => Validators.validateRequired(value, fieldName)
    ),

    email: () => Validators.rule(
        (value) => Validators.validateEmail(value)
    ),

    url: () => Validators.rule(
        (value) => Validators.validateUrl(value)
    ),

    minLength: (min, fieldName) => Validators.rule(
        (value) => Validators.validateLength(value, min, undefined, fieldName)
    ),

    maxLength: (max, fieldName) => Validators.rule(
        (value) => Validators.validateLength(value, undefined, max, fieldName)
    ),

    length: (min, max, fieldName) => Validators.rule(
        (value) => Validators.validateLength(value, min, max, fieldName)
    ),

    min: (min, fieldName) => Validators.rule(
        (value) => Validators.validateRange(value, min, undefined, fieldName)
    ),

    max: (max, fieldName) => Validators.rule(
        (value) => Validators.validateRange(value, undefined, max, fieldName)
    ),

    range: (min, max, fieldName) => Validators.rule(
        (value) => Validators.validateRange(value, min, max, fieldName)
    ),

    pattern: (pattern, fieldName, errorMessage) => Validators.rule(
        (value) => Validators.validatePattern(value, pattern, fieldName, errorMessage)
    )
};

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { Validators, ValidationRules };
}

window.Validators = Validators;
window.ValidationRules = ValidationRules;
