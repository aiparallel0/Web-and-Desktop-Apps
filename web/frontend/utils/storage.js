/**
 * Storage Manager - LocalStorage and SessionStorage wrapper
 * Provides type-safe storage with encryption support
 */

class StorageManager {
    constructor(storageType = 'localStorage', prefix = 'receipt_extractor_') {
        this.storage = storageType === 'sessionStorage' ? sessionStorage : localStorage;
        this.prefix = prefix;
        this.encryptionKey = null;
    }

    /**
     * Set encryption key for sensitive data
     */
    setEncryptionKey(key) {
        this.encryptionKey = key;
    }

    /**
     * Generate storage key with prefix
     */
    getKey(key) {
        return `${this.prefix}${key}`;
    }

    /**
     * Set item in storage
     */
    set(key, value, options = {}) {
        try {
            const storageKey = this.getKey(key);
            let data = {
                value,
                timestamp: Date.now(),
                type: typeof value
            };

            if (options.expiresIn) {
                data.expiresAt = Date.now() + options.expiresIn;
            }

            if (options.encrypt && this.encryptionKey) {
                data = this.encrypt(data);
            }

            this.storage.setItem(storageKey, JSON.stringify(data));
            return true;
        } catch (error) {
            console.error('Storage set error:', error);
            
            // Handle quota exceeded
            if (error.name === 'QuotaExceededError') {
                this.clearExpired();
                try {
                    this.storage.setItem(this.getKey(key), JSON.stringify({ value, timestamp: Date.now() }));
                    return true;
                } catch (e) {
                    console.error('Storage still full after cleanup');
                }
            }
            return false;
        }
    }

    /**
     * Get item from storage
     */
    get(key, defaultValue = null) {
        try {
            const storageKey = this.getKey(key);
            const item = this.storage.getItem(storageKey);

            if (!item) {
                return defaultValue;
            }

            let data = JSON.parse(item);

            // Decrypt if needed
            if (data.encrypted && this.encryptionKey) {
                data = this.decrypt(data);
            }

            // Check expiration
            if (data.expiresAt && Date.now() > data.expiresAt) {
                this.remove(key);
                return defaultValue;
            }

            return data.value;
        } catch (error) {
            console.error('Storage get error:', error);
            return defaultValue;
        }
    }

    /**
     * Remove item from storage
     */
    remove(key) {
        try {
            this.storage.removeItem(this.getKey(key));
            return true;
        } catch (error) {
            console.error('Storage remove error:', error);
            return false;
        }
    }

    /**
     * Check if key exists
     */
    has(key) {
        return this.storage.getItem(this.getKey(key)) !== null;
    }

    /**
     * Clear all items with prefix
     */
    clear() {
        try {
            const keys = this.keys();
            keys.forEach(key => this.remove(key));
            return true;
        } catch (error) {
            console.error('Storage clear error:', error);
            return false;
        }
    }

    /**
     * Get all keys with prefix
     */
    keys() {
        const keys = [];
        for (let i = 0; i < this.storage.length; i++) {
            const key = this.storage.key(i);
            if (key && key.startsWith(this.prefix)) {
                keys.push(key.substring(this.prefix.length));
            }
        }
        return keys;
    }

    /**
     * Get all items as object
     */
    getAll() {
        const items = {};
        const keys = this.keys();
        keys.forEach(key => {
            items[key] = this.get(key);
        });
        return items;
    }

    /**
     * Clear expired items
     */
    clearExpired() {
        const keys = this.keys();
        let cleared = 0;

        keys.forEach(key => {
            try {
                const storageKey = this.getKey(key);
                const item = this.storage.getItem(storageKey);
                if (item) {
                    const data = JSON.parse(item);
                    if (data.expiresAt && Date.now() > data.expiresAt) {
                        this.remove(key);
                        cleared++;
                    }
                }
            } catch (e) {
                // Ignore errors
            }
        });

        console.log(`Cleared ${cleared} expired items`);
        return cleared;
    }

    /**
     * Get storage size
     */
    getSize() {
        let size = 0;
        const keys = this.keys();
        
        keys.forEach(key => {
            const storageKey = this.getKey(key);
            const item = this.storage.getItem(storageKey);
            if (item) {
                size += item.length + storageKey.length;
            }
        });

        return size;
    }

    /**
     * Get storage size in human readable format
     */
    getSizeFormatted() {
        const size = this.getSize();
        const units = ['B', 'KB', 'MB', 'GB'];
        let unitIndex = 0;
        let calcSize = size;

        while (calcSize >= 1024 && unitIndex < units.length - 1) {
            calcSize /= 1024;
            unitIndex++;
        }

        return `${calcSize.toFixed(2)} ${units[unitIndex]}`;
    }

    /**
     * Simple encryption (for demonstration - use proper encryption in production)
     */
    encrypt(data) {
        if (!this.encryptionKey) {
            return data;
        }

        // Simple XOR encryption (NOT secure for production)
        const str = JSON.stringify(data);
        let encrypted = '';
        
        for (let i = 0; i < str.length; i++) {
            const charCode = str.charCodeAt(i) ^ this.encryptionKey.charCodeAt(i % this.encryptionKey.length);
            encrypted += String.fromCharCode(charCode);
        }

        return {
            encrypted: true,
            data: btoa(encrypted)
        };
    }

    /**
     * Simple decryption
     */
    decrypt(encryptedData) {
        if (!this.encryptionKey || !encryptedData.encrypted) {
            return encryptedData;
        }

        const encrypted = atob(encryptedData.data);
        let decrypted = '';

        for (let i = 0; i < encrypted.length; i++) {
            const charCode = encrypted.charCodeAt(i) ^ this.encryptionKey.charCodeAt(i % this.encryptionKey.length);
            decrypted += String.fromCharCode(charCode);
        }

        return JSON.parse(decrypted);
    }

    /**
     * Export storage data
     */
    export() {
        const data = this.getAll();
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `storage-export-${Date.now()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    /**
     * Import storage data
     */
    async import(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            
            reader.onload = (e) => {
                try {
                    const data = JSON.parse(e.target.result);
                    let imported = 0;
                    
                    for (const [key, value] of Object.entries(data)) {
                        if (this.set(key, value)) {
                            imported++;
                        }
                    }
                    
                    resolve(imported);
                } catch (error) {
                    reject(error);
                }
            };
            
            reader.onerror = reject;
            reader.readAsText(file);
        });
    }
}

/**
 * Specialized storage managers
 */
class UserPreferences extends StorageManager {
    constructor() {
        super('localStorage', 'user_prefs_');
    }

    setTheme(theme) {
        return this.set('theme', theme);
    }

    getTheme() {
        return this.get('theme', 'light');
    }

    setLanguage(lang) {
        return this.set('language', lang);
    }

    getLanguage() {
        return this.get('language', 'en');
    }

    setModelPreference(modelId) {
        return this.set('preferred_model', modelId);
    }

    getModelPreference() {
        return this.get('preferred_model', 'ocr_tesseract');
    }

    setDetectionSettings(settings) {
        return this.set('detection_settings', settings);
    }

    getDetectionSettings() {
        return this.get('detection_settings', {
            mode: 'auto',
            deskewEnabled: true,
            enhanceEnabled: true
        });
    }

    setRecentFiles(files) {
        // Keep only last 10 files
        const recentFiles = files.slice(-10);
        return this.set('recent_files', recentFiles);
    }

    getRecentFiles() {
        return this.get('recent_files', []);
    }

    addRecentFile(file) {
        const recent = this.getRecentFiles();
        const fileInfo = {
            name: file.name,
            size: file.size,
            type: file.type,
            timestamp: Date.now()
        };
        
        recent.push(fileInfo);
        return this.setRecentFiles(recent);
    }
}

class SessionCache extends StorageManager {
    constructor() {
        super('sessionStorage', 'cache_');
    }

    cacheResult(key, result, ttl = 300000) { // 5 minutes default
        return this.set(key, result, { expiresIn: ttl });
    }

    getCachedResult(key) {
        return this.get(key);
    }
}

// Create singleton instances
const storage = new StorageManager();
const userPrefs = new UserPreferences();
const sessionCache = new SessionCache();

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { 
        StorageManager, 
        UserPreferences, 
        SessionCache,
        storage,
        userPrefs,
        sessionCache
    };
}

window.StorageManager = StorageManager;
window.UserPreferences = UserPreferences;
window.SessionCache = SessionCache;
window.storage = storage;
window.userPrefs = userPrefs;
window.sessionCache = sessionCache;
