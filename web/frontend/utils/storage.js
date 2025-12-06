/**
 * Storage Utility for Receipt Extractor
 * Handles localStorage operations with error handling and type safety
 */

class Storage {
    /**
     * Get item from localStorage with JSON parsing
     * @param {string} key - Storage key
     * @param {*} defaultValue - Default value if key doesn't exist
     * @returns {*} Stored value or default
     */
    static get(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.error(`Error reading from localStorage (key: ${key}):`, error);
            return defaultValue;
        }
    }

    /**
     * Set item in localStorage with JSON stringification
     * @param {string} key - Storage key
     * @param {*} value - Value to store
     * @returns {boolean} Success status
     */
    static set(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            console.error(`Error writing to localStorage (key: ${key}):`, error);
            return false;
        }
    }

    /**
     * Remove item from localStorage
     * @param {string} key - Storage key
     */
    static remove(key) {
        try {
            localStorage.removeItem(key);
        } catch (error) {
            console.error(`Error removing from localStorage (key: ${key}):`, error);
        }
    }

    /**
     * Clear all items from localStorage
     */
    static clear() {
        try {
            localStorage.clear();
        } catch (error) {
            console.error('Error clearing localStorage:', error);
        }
    }

    /**
     * Check if key exists in localStorage
     * @param {string} key - Storage key
     * @returns {boolean} True if key exists
     */
    static has(key) {
        return localStorage.getItem(key) !== null;
    }

    /**
     * Get all keys in localStorage
     * @returns {string[]} Array of keys
     */
    static keys() {
        return Object.keys(localStorage);
    }

    // =========================================================================
    // DETECTION PREFERENCES
    // =========================================================================

    static KEYS = {
        DETECTION_PREFS: 'receipt_detection_preferences',
        EXTRACTION_COUNT: 'extraction_count',
        USER_SETTINGS: 'user_settings',
        RECENT_FILES: 'recent_files',
        FAVORITE_MODELS: 'favorite_models'
    };

    /**
     * Save detection preferences
     */
    static saveDetectionPreferences(prefs) {
        return this.set(this.KEYS.DETECTION_PREFS, {
            detectionMode: prefs.detectionMode || 'auto',
            deskewEnabled: prefs.deskewEnabled !== false,
            enhanceEnabled: prefs.enhanceEnabled !== false,
            previewEnabled: prefs.previewEnabled || false,
            timestamp: Date.now()
        });
    }

    /**
     * Load detection preferences
     */
    static loadDetectionPreferences() {
        return this.get(this.KEYS.DETECTION_PREFS, {
            detectionMode: 'auto',
            deskewEnabled: true,
            enhanceEnabled: true,
            previewEnabled: false
        });
    }

    /**
     * Get extraction count
     */
    static getExtractionCount() {
        return this.get(this.KEYS.EXTRACTION_COUNT, 0);
    }

    /**
     * Increment extraction count
     */
    static incrementExtractionCount() {
        const count = this.getExtractionCount();
        return this.set(this.KEYS.EXTRACTION_COUNT, count + 1);
    }

    /**
     * Save user settings
     */
    static saveUserSettings(settings) {
        const current = this.get(this.KEYS.USER_SETTINGS, {});
        return this.set(this.KEYS.USER_SETTINGS, { ...current, ...settings });
    }

    /**
     * Load user settings
     */
    static loadUserSettings() {
        return this.get(this.KEYS.USER_SETTINGS, {
            theme: 'light',
            language: 'en',
            autoSave: true,
            notifications: true
        });
    }

    /**
     * Add to recent files
     */
    static addRecentFile(fileInfo) {
        const recent = this.get(this.KEYS.RECENT_FILES, []);
        
        // Add to beginning
        recent.unshift({
            name: fileInfo.name,
            size: fileInfo.size,
            type: fileInfo.type,
            timestamp: Date.now()
        });
        
        // Keep only last 10
        const updated = recent.slice(0, 10);
        return this.set(this.KEYS.RECENT_FILES, updated);
    }

    /**
     * Get recent files
     */
    static getRecentFiles() {
        return this.get(this.KEYS.RECENT_FILES, []);
    }

    /**
     * Add favorite model
     */
    static addFavoriteModel(modelId) {
        const favorites = this.get(this.KEYS.FAVORITE_MODELS, []);
        if (!favorites.includes(modelId)) {
            favorites.push(modelId);
            return this.set(this.KEYS.FAVORITE_MODELS, favorites);
        }
        return false;
    }

    /**
     * Remove favorite model
     */
    static removeFavoriteModel(modelId) {
        const favorites = this.get(this.KEYS.FAVORITE_MODELS, []);
        const updated = favorites.filter(id => id !== modelId);
        return this.set(this.KEYS.FAVORITE_MODELS, updated);
    }

    /**
     * Get favorite models
     */
    static getFavoriteModels() {
        return this.get(this.KEYS.FAVORITE_MODELS, []);
    }

    /**
     * Check if model is favorited
     */
    static isModelFavorited(modelId) {
        const favorites = this.getFavoriteModels();
        return favorites.includes(modelId);
    }

    // =========================================================================
    // UTILITY METHODS
    // =========================================================================

    /**
     * Get storage usage info
     */
    static getUsageInfo() {
        let totalSize = 0;
        
        for (let key in localStorage) {
            if (localStorage.hasOwnProperty(key)) {
                totalSize += localStorage[key].length + key.length;
            }
        }
        
        return {
            usedBytes: totalSize,
            usedKB: (totalSize / 1024).toFixed(2),
            usedMB: (totalSize / 1024 / 1024).toFixed(2),
            itemCount: localStorage.length
        };
    }

    /**
     * Export all data
     */
    static exportAll() {
        const data = {};
        
        for (let key in localStorage) {
            if (localStorage.hasOwnProperty(key)) {
                try {
                    data[key] = JSON.parse(localStorage[key]);
                } catch (e) {
                    data[key] = localStorage[key];
                }
            }
        }
        
        return data;
    }

    /**
     * Import data
     */
    static importAll(data) {
        for (let key in data) {
            this.set(key, data[key]);
        }
    }

    /**
     * Clear app-specific data only
     */
    static clearAppData() {
        Object.values(this.KEYS).forEach(key => {
            this.remove(key);
        });
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Storage;
}

// Also attach to window for easy access
if (typeof window !== 'undefined') {
    window.Storage = Storage;
}
