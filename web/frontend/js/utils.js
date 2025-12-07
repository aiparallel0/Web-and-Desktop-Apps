/**
 * Utility Functions Library
 * Comprehensive collection of helper functions and utilities
 * @version 2.0.0
 */

(function(window) {
    'use strict';

    /**
     * String Utilities
     */
    const StringUtils = {
        /**
         * Capitalize first letter
         */
        capitalize(str) {
            if (!str) return '';
            return str.charAt(0).toUpperCase() + str.slice(1);
        },

        /**
         * Capitalize all words
         */
        capitalizeWords(str) {
            if (!str) return '';
            return str.split(' ').map(word => this.capitalize(word)).join(' ');
        },

        /**
         * Convert to title case
         */
        toTitleCase(str) {
            if (!str) return '';
            const smallWords = ['a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor', 'on', 'at', 'to', 'by', 'in'];
            const words = str.toLowerCase().split(' ');
            
            return words.map((word, index) => {
                if (index === 0 || !smallWords.includes(word)) {
                    return this.capitalize(word);
                }
                return word;
            }).join(' ');
        },

        /**
         * Convert to slug
         */
        toSlug(str) {
            if (!str) return '';
            return str
                .toLowerCase()
                .replace(/[^\w\s-]/g, '')
                .replace(/[\s_-]+/g, '-')
                .replace(/^-+|-+$/g, '');
        },

        /**
         * Truncate string
         */
        truncate(str, length = 50, suffix = '...') {
            if (!str || str.length <= length) return str;
            return str.substring(0, length - suffix.length) + suffix;
        },

        /**
         * Truncate at word boundary
         */
        truncateWords(str, maxWords = 10, suffix = '...') {
            if (!str) return '';
            const words = str.split(' ');
            if (words.length <= maxWords) return str;
            return words.slice(0, maxWords).join(' ') + suffix;
        },

        /**
         * Strip HTML tags
         */
        stripHTML(str) {
            if (!str) return '';
            const div = document.createElement('div');
            div.innerHTML = str;
            return div.textContent || div.innerText || '';
        },

        /**
         * Escape HTML
         */
        escapeHTML(str) {
            if (!str) return '';
            const div = document.createElement('div');
            div.textContent = str;
            return div.innerHTML;
        },

        /**
         * Unescape HTML
         */
        unescapeHTML(str) {
            if (!str) return '';
            const div = document.createElement('div');
            div.innerHTML = str;
            return div.textContent || div.innerText || '';
        },

        /**
         * Count words
         */
        countWords(str) {
            if (!str) return 0;
            return str.trim().split(/\s+/).length;
        },

        /**
         * Generate random string
         */
        randomString(length = 10, chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789') {
            let result = '';
            for (let i = 0; i < length; i++) {
                result += chars.charAt(Math.floor(Math.random() * chars.length));
            }
            return result;
        },

        /**
         * Pad string
         */
        pad(str, length, char = ' ', right = false) {
            str = String(str);
            const padding = char.repeat(Math.max(0, length - str.length));
            return right ? str + padding : padding + str;
        },

        /**
         * Remove extra whitespace
         */
        normalizeWhitespace(str) {
            if (!str) return '';
            return str.replace(/\s+/g, ' ').trim();
        },

        /**
         * Reverse string
         */
        reverse(str) {
            if (!str) return '';
            return str.split('').reverse().join('');
        },

        /**
         * Check if string contains
         */
        contains(str, search, caseSensitive = false) {
            if (!str || !search) return false;
            if (caseSensitive) {
                return str.includes(search);
            }
            return str.toLowerCase().includes(search.toLowerCase());
        },

        /**
         * Replace all occurrences
         */
        replaceAll(str, find, replace) {
            if (!str) return '';
            return str.split(find).join(replace);
        },

        /**
         * Convert camelCase to snake_case
         */
        camelToSnake(str) {
            if (!str) return '';
            return str.replace(/([A-Z])/g, '_$1').toLowerCase().replace(/^_/, '');
        },

        /**
         * Convert snake_case to camelCase
         */
        snakeToCamel(str) {
            if (!str) return '';
            return str.replace(/_([a-z])/g, (match, letter) => letter.toUpperCase());
        },

        /**
         * Convert kebab-case to camelCase
         */
        kebabToCamel(str) {
            if (!str) return '';
            return str.replace(/-([a-z])/g, (match, letter) => letter.toUpperCase());
        }
    };

    /**
     * Number Utilities
     */
    const NumberUtils = {
        /**
         * Format number with commas
         */
        format(num, decimals = 0) {
            if (typeof num !== 'number') return num;
            return num.toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
        },

        /**
         * Format as currency
         */
        formatCurrency(num, currency = 'USD', locale = 'en-US') {
            if (typeof num !== 'number') return num;
            return new Intl.NumberFormat(locale, {
                style: 'currency',
                currency: currency
            }).format(num);
        },

        /**
         * Format as percentage
         */
        formatPercentage(num, decimals = 1) {
            if (typeof num !== 'number') return num;
            return `${(num * 100).toFixed(decimals)}%`;
        },

        /**
         * Format file size
         */
        formatFileSize(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        },

        /**
         * Clamp number between min and max
         */
        clamp(num, min, max) {
            return Math.min(Math.max(num, min), max);
        },

        /**
         * Generate random number
         */
        random(min = 0, max = 1) {
            return Math.random() * (max - min) + min;
        },

        /**
         * Generate random integer
         */
        randomInt(min, max) {
            return Math.floor(this.random(min, max + 1));
        },

        /**
         * Round to decimal places
         */
        round(num, decimals = 0) {
            const factor = Math.pow(10, decimals);
            return Math.round(num * factor) / factor;
        },

        /**
         * Check if number is in range
         */
        inRange(num, min, max) {
            return num >= min && num <= max;
        },

        /**
         * Calculate percentage
         */
        percentage(part, whole) {
            if (whole === 0) return 0;
            return (part / whole) * 100;
        },

        /**
         * Convert to ordinal
         */
        toOrdinal(num) {
            const s = ['th', 'st', 'nd', 'rd'];
            const v = num % 100;
            return num + (s[(v - 20) % 10] || s[v] || s[0]);
        },

        /**
         * Sum array of numbers
         */
        sum(numbers) {
            return numbers.reduce((acc, num) => acc + num, 0);
        },

        /**
         * Average of array
         */
        average(numbers) {
            if (numbers.length === 0) return 0;
            return this.sum(numbers) / numbers.length;
        },

        /**
         * Median of array
         */
        median(numbers) {
            const sorted = [...numbers].sort((a, b) => a - b);
            const mid = Math.floor(sorted.length / 2);
            return sorted.length % 2 === 0
                ? (sorted[mid - 1] + sorted[mid]) / 2
                : sorted[mid];
        }
    };

    /**
     * Date Utilities
     */
    const DateUtils = {
        /**
         * Format date
         */
        format(date, format = 'YYYY-MM-DD') {
            const d = new Date(date);
            const map = {
                'YYYY': d.getFullYear(),
                'MM': String(d.getMonth() + 1).padStart(2, '0'),
                'DD': String(d.getDate()).padStart(2, '0'),
                'HH': String(d.getHours()).padStart(2, '0'),
                'mm': String(d.getMinutes()).padStart(2, '0'),
                'ss': String(d.getSeconds()).padStart(2, '0')
            };

            return format.replace(/YYYY|MM|DD|HH|mm|ss/g, match => map[match]);
        },

        /**
         * Relative time (e.g., "2 hours ago")
         */
        relativeTime(date) {
            const d = new Date(date);
            const now = new Date();
            const seconds = Math.floor((now - d) / 1000);

            if (seconds < 60) return 'just now';
            if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes ago`;
            if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`;
            if (seconds < 604800) return `${Math.floor(seconds / 86400)} days ago`;
            if (seconds < 2592000) return `${Math.floor(seconds / 604800)} weeks ago`;
            if (seconds < 31536000) return `${Math.floor(seconds / 2592000)} months ago`;
            return `${Math.floor(seconds / 31536000)} years ago`;
        },

        /**
         * Add days to date
         */
        addDays(date, days) {
            const d = new Date(date);
            d.setDate(d.getDate() + days);
            return d;
        },

        /**
         * Add months to date
         */
        addMonths(date, months) {
            const d = new Date(date);
            d.setMonth(d.getMonth() + months);
            return d;
        },

        /**
         * Add years to date
         */
        addYears(date, years) {
            const d = new Date(date);
            d.setFullYear(d.getFullYear() + years);
            return d;
        },

        /**
         * Get day of week
         */
        getDayOfWeek(date) {
            const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
            return days[new Date(date).getDay()];
        },

        /**
         * Get month name
         */
        getMonthName(date) {
            const months = ['January', 'February', 'March', 'April', 'May', 'June',
                          'July', 'August', 'September', 'October', 'November', 'December'];
            return months[new Date(date).getMonth()];
        },

        /**
         * Is today
         */
        isToday(date) {
            const d = new Date(date);
            const today = new Date();
            return d.toDateString() === today.toDateString();
        },

        /**
         * Is past
         */
        isPast(date) {
            return new Date(date) < new Date();
        },

        /**
         * Is future
         */
        isFuture(date) {
            return new Date(date) > new Date();
        },

        /**
         * Difference in days
         */
        diffInDays(date1, date2) {
            const d1 = new Date(date1);
            const d2 = new Date(date2);
            const diffTime = Math.abs(d2 - d1);
            return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        }
    };

    /**
     * Array Utilities
     */
    const ArrayUtils = {
        /**
         * Chunk array
         */
        chunk(array, size) {
            const chunks = [];
            for (let i = 0; i < array.length; i += size) {
                chunks.push(array.slice(i, i + size));
            }
            return chunks;
        },

        /**
         * Shuffle array
         */
        shuffle(array) {
            const shuffled = [...array];
            for (let i = shuffled.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
            }
            return shuffled;
        },

        /**
         * Unique values
         */
        unique(array) {
            return [...new Set(array)];
        },

        /**
         * Remove duplicates by key
         */
        uniqueBy(array, key) {
            const seen = new Set();
            return array.filter(item => {
                const k = typeof key === 'function' ? key(item) : item[key];
                if (seen.has(k)) return false;
                seen.add(k);
                return true;
            });
        },

        /**
         * Flatten array
         */
        flatten(array) {
            return array.flat(Infinity);
        },

        /**
         * Group by key
         */
        groupBy(array, key) {
            return array.reduce((groups, item) => {
                const k = typeof key === 'function' ? key(item) : item[key];
                (groups[k] = groups[k] || []).push(item);
                return groups;
            }, {});
        },

        /**
         * Sort by key
         */
        sortBy(array, key, direction = 'asc') {
            return [...array].sort((a, b) => {
                const aVal = typeof key === 'function' ? key(a) : a[key];
                const bVal = typeof key === 'function' ? key(b) : b[key];
                
                if (aVal < bVal) return direction === 'asc' ? -1 : 1;
                if (aVal > bVal) return direction === 'asc' ? 1 : -1;
                return 0;
            });
        },

        /**
         * Random item
         */
        randomItem(array) {
            return array[Math.floor(Math.random() * array.length)];
        },

        /**
         * Sample items
         */
        sample(array, count) {
            const shuffled = this.shuffle(array);
            return shuffled.slice(0, count);
        },

        /**
         * Intersection
         */
        intersection(array1, array2) {
            const set2 = new Set(array2);
            return array1.filter(item => set2.has(item));
        },

        /**
         * Difference
         */
        difference(array1, array2) {
            const set2 = new Set(array2);
            return array1.filter(item => !set2.has(item));
        },

        /**
         * Remove falsy values
         */
        compact(array) {
            return array.filter(Boolean);
        },

        /**
         * Count occurrences
         */
        countBy(array, key) {
            return array.reduce((counts, item) => {
                const k = typeof key === 'function' ? key(item) : item[key];
                counts[k] = (counts[k] || 0) + 1;
                return counts;
            }, {});
        },

        /**
         * Partition array
         */
        partition(array, predicate) {
            return array.reduce((result, item) => {
                result[predicate(item) ? 0 : 1].push(item);
                return result;
            }, [[], []]);
        }
    };

    /**
     * Object Utilities
     */
    const ObjectUtils = {
        /**
         * Deep clone
         */
        clone(obj) {
            return JSON.parse(JSON.stringify(obj));
        },

        /**
         * Deep merge
         */
        merge(target, ...sources) {
            if (!sources.length) return target;
            const source = sources.shift();

            if (this.isObject(target) && this.isObject(source)) {
                for (const key in source) {
                    if (this.isObject(source[key])) {
                        if (!target[key]) Object.assign(target, { [key]: {} });
                        this.merge(target[key], source[key]);
                    } else {
                        Object.assign(target, { [key]: source[key] });
                    }
                }
            }

            return this.merge(target, ...sources);
        },

        /**
         * Check if object
         */
        isObject(item) {
            return item && typeof item === 'object' && !Array.isArray(item);
        },

        /**
         * Get nested value
         */
        get(obj, path, defaultValue = undefined) {
            const keys = path.split('.');
            let result = obj;

            for (const key of keys) {
                if (result == null) return defaultValue;
                result = result[key];
            }

            return result !== undefined ? result : defaultValue;
        },

        /**
         * Set nested value
         */
        set(obj, path, value) {
            const keys = path.split('.');
            const lastKey = keys.pop();
            let current = obj;

            for (const key of keys) {
                if (!(key in current)) {
                    current[key] = {};
                }
                current = current[key];
            }

            current[lastKey] = value;
            return obj;
        },

        /**
         * Pick properties
         */
        pick(obj, keys) {
            return keys.reduce((result, key) => {
                if (key in obj) {
                    result[key] = obj[key];
                }
                return result;
            }, {});
        },

        /**
         * Omit properties
         */
        omit(obj, keys) {
            const result = { ...obj };
            keys.forEach(key => delete result[key]);
            return result;
        },

        /**
         * Is empty
         */
        isEmpty(obj) {
            return Object.keys(obj).length === 0;
        },

        /**
         * Transform keys
         */
        mapKeys(obj, fn) {
            return Object.entries(obj).reduce((result, [key, value]) => {
                result[fn(key)] = value;
                return result;
            }, {});
        },

        /**
         * Transform values
         */
        mapValues(obj, fn) {
            return Object.entries(obj).reduce((result, [key, value]) => {
                result[key] = fn(value);
                return result;
            }, {});
        }
    };

    /**
     * DOM Utilities
     */
    const DOMUtils = {
        /**
         * Select element
         */
        $(selector) {
            return document.querySelector(selector);
        },

        /**
         * Select all elements
         */
        $$(selector) {
            return Array.from(document.querySelectorAll(selector));
        },

        /**
         * Add event listener
         */
        on(element, event, handler, options) {
            if (typeof element === 'string') {
                element = this.$(element);
            }
            if (element) {
                element.addEventListener(event, handler, options);
            }
        },

        /**
         * Remove event listener
         */
        off(element, event, handler) {
            if (typeof element === 'string') {
                element = this.$(element);
            }
            if (element) {
                element.removeEventListener(event, handler);
            }
        },

        /**
         * Add class
         */
        addClass(element, className) {
            if (typeof element === 'string') {
                element = this.$(element);
            }
            if (element) {
                element.classList.add(className);
            }
        },

        /**
         * Remove class
         */
        removeClass(element, className) {
            if (typeof element === 'string') {
                element = this.$(element);
            }
            if (element) {
                element.classList.remove(className);
            }
        },

        /**
         * Toggle class
         */
        toggleClass(element, className) {
            if (typeof element === 'string') {
                element = this.$(element);
            }
            if (element) {
                element.classList.toggle(className);
            }
        },

        /**
         * Has class
         */
        hasClass(element, className) {
            if (typeof element === 'string') {
                element = this.$(element);
            }
            return element ? element.classList.contains(className) : false;
        },

        /**
         * Get/set attribute
         */
        attr(element, name, value) {
            if (typeof element === 'string') {
                element = this.$(element);
            }
            if (!element) return null;

            if (value === undefined) {
                return element.getAttribute(name);
            }
            element.setAttribute(name, value);
        },

        /**
         * Show element
         */
        show(element) {
            if (typeof element === 'string') {
                element = this.$(element);
            }
            if (element) {
                element.style.display = '';
            }
        },

        /**
         * Hide element
         */
        hide(element) {
            if (typeof element === 'string') {
                element = this.$(element);
            }
            if (element) {
                element.style.display = 'none';
            }
        },

        /**
         * Toggle visibility
         */
        toggle(element) {
            if (typeof element === 'string') {
                element = this.$(element);
            }
            if (element) {
                element.style.display = element.style.display === 'none' ? '' : 'none';
            }
        },

        /**
         * Scroll to element
         */
        scrollTo(element, options = {}) {
            if (typeof element === 'string') {
                element = this.$(element);
            }
            if (element) {
                element.scrollIntoView({
                    behavior: options.smooth ? 'smooth' : 'auto',
                    block: options.block || 'start',
                    ...options
                });
            }
        },

        /**
         * Get element offset
         */
        offset(element) {
            if (typeof element === 'string') {
                element = this.$(element);
            }
            if (!element) return { top: 0, left: 0 };

            const rect = element.getBoundingClientRect();
            return {
                top: rect.top + window.pageYOffset,
                left: rect.left + window.pageXOffset
            };
        },

        /**
         * Is in viewport
         */
        isInViewport(element) {
            if (typeof element === 'string') {
                element = this.$(element);
            }
            if (!element) return false;

            const rect = element.getBoundingClientRect();
            return (
                rect.top >= 0 &&
                rect.left >= 0 &&
                rect.bottom <= window.innerHeight &&
                rect.right <= window.innerWidth
            );
        }
    };

    /**
     * URL Utilities
     */
    const URLUtils = {
        /**
         * Get query parameters
         */
        getParams() {
            const params = {};
            const searchParams = new URLSearchParams(window.location.search);
            for (const [key, value] of searchParams) {
                params[key] = value;
            }
            return params;
        },

        /**
         * Get single parameter
         */
        getParam(name) {
            const params = new URLSearchParams(window.location.search);
            return params.get(name);
        },

        /**
         * Update URL parameter
         */
        updateParam(name, value) {
            const url = new URL(window.location);
            url.searchParams.set(name, value);
            window.history.pushState({}, '', url);
        },

        /**
         * Remove URL parameter
         */
        removeParam(name) {
            const url = new URL(window.location);
            url.searchParams.delete(name);
            window.history.pushState({}, '', url);
        },

        /**
         * Build query string
         */
        buildQueryString(params) {
            return new URLSearchParams(params).toString();
        },

        /**
         * Parse URL
         */
        parse(url) {
            const parsed = new URL(url, window.location.origin);
            return {
                protocol: parsed.protocol,
                hostname: parsed.hostname,
                port: parsed.port,
                pathname: parsed.pathname,
                search: parsed.search,
                hash: parsed.hash,
                params: Object.fromEntries(parsed.searchParams)
            };
        }
    };

    /**
     * Async Utilities
     */
    const AsyncUtils = {
        /**
         * Sleep/delay
         */
        sleep(ms) {
            return new Promise(resolve => setTimeout(resolve, ms));
        },

        /**
         * Debounce function
         */
        debounce(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },

        /**
         * Throttle function
         */
        throttle(func, limit) {
            let inThrottle;
            return function executedFunction(...args) {
                if (!inThrottle) {
                    func(...args);
                    inThrottle = true;
                    setTimeout(() => inThrottle = false, limit);
                }
            };
        },

        /**
         * Retry function
         */
        async retry(fn, maxAttempts = 3, delay = 1000) {
            for (let attempt = 1; attempt <= maxAttempts; attempt++) {
                try {
                    return await fn();
                } catch (error) {
                    if (attempt === maxAttempts) throw error;
                    await this.sleep(delay * attempt);
                }
            }
        },

        /**
         * Timeout promise
         */
        timeout(promise, ms) {
            return Promise.race([
                promise,
                new Promise((_, reject) =>
                    setTimeout(() => reject(new Error('Timeout')), ms)
                )
            ]);
        }
    };

    /**
     * Storage Utilities
     */
    const StorageUtils = {
        /**
         * Set localStorage with expiry
         */
        setWithExpiry(key, value, ttl) {
            const item = {
                value: value,
                expiry: Date.now() + ttl
            };
            localStorage.setItem(key, JSON.stringify(item));
        },

        /**
         * Get localStorage with expiry check
         */
        getWithExpiry(key) {
            const itemStr = localStorage.getItem(key);
            if (!itemStr) return null;

            try {
                const item = JSON.parse(itemStr);
                if (Date.now() > item.expiry) {
                    localStorage.removeItem(key);
                    return null;
                }
                return item.value;
            } catch {
                return null;
            }
        },

        /**
         * Get storage size
         */
        getSize() {
            let total = 0;
            for (const key in localStorage) {
                if (localStorage.hasOwnProperty(key)) {
                    total += localStorage[key].length + key.length;
                }
            }
            return total;
        },

        /**
         * Clear expired items
         */
        clearExpired() {
            for (const key in localStorage) {
                if (localStorage.hasOwnProperty(key)) {
                    try {
                        const item = JSON.parse(localStorage[key]);
                        if (item.expiry && Date.now() > item.expiry) {
                            localStorage.removeItem(key);
                        }
                    } catch {
                        // Skip non-JSON items
                    }
                }
            }
        }
    };

    // Export all utilities
    window.Utils = {
        string: StringUtils,
        number: NumberUtils,
        date: DateUtils,
        array: ArrayUtils,
        object: ObjectUtils,
        dom: DOMUtils,
        url: URLUtils,
        async: AsyncUtils,
        storage: StorageUtils
    };

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = window.Utils;
    }

})(window);
