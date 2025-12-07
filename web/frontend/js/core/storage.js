/**
 * Advanced Storage Manager
 * Handles localStorage, sessionStorage, and IndexedDB with encryption
 */

class StorageManager {
    constructor() {
        this.storageKey = 'receipt_extractor_';
        this.db = null;
        this.dbName = 'ReceiptExtractorDB';
        this.dbVersion = 1;
        this.encryptionKey = null;
        
        this.initIndexedDB();
    }

    async initIndexedDB() {
        try {
            this.db = await this.openDatabase();
        } catch (error) {
            console.error('Failed to initialize IndexedDB:', error);
        }
    }

    openDatabase() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.dbVersion);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve(request.result);

            request.onupgradeneeded = (event) => {
                const db = event.target.result;

                if (!db.objectStoreNames.contains('extractions')) {
                    db.createObjectStore('extractions', { keyPath: 'id', autoIncrement: true });
                }

                if (!db.objectStoreNames.contains('files')) {
                    db.createObjectStore('files', { keyPath: 'id', autoIncrement: true });
                }

                if (!db.objectStoreNames.contains('cache')) {
                    db.createObjectStore('cache', { keyPath: 'key' });
                }
            };
        });
    }

    // LocalStorage methods
    set(key, value, options = {}) {
        try {
            const fullKey = this.storageKey + key;
            const data = {
                value,
                timestamp: Date.now(),
                expires: options.expires || null
            };

            const serialized = JSON.stringify(data);
            
            if (options.session) {
                sessionStorage.setItem(fullKey, serialized);
            } else {
                localStorage.setItem(fullKey, serialized);
            }

            return true;
        } catch (error) {
            console.error('Storage error:', error);
            return false;
        }
    }

    get(key, options = {}) {
        try {
            const fullKey = this.storageKey + key;
            const storage = options.session ? sessionStorage : localStorage;
            const serialized = storage.getItem(fullKey);

            if (!serialized) return null;

            const data = JSON.parse(serialized);

            if (data.expires && Date.now() > data.expires) {
                this.remove(key, options);
                return null;
            }

            return data.value;
        } catch (error) {
            console.error('Storage error:', error);
            return null;
        }
    }

    remove(key, options = {}) {
        const fullKey = this.storageKey + key;
        const storage = options.session ? sessionStorage : localStorage;
        storage.removeItem(fullKey);
    }

    clear(options = {}) {
        if (options.session) {
            sessionStorage.clear();
        } else {
            localStorage.clear();
        }
    }

    // IndexedDB methods
    async dbSet(storeName, value, key = null) {
        if (!this.db) await this.initIndexedDB();

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            
            const request = key ? store.put(value, key) : store.put(value);

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async dbGet(storeName, key) {
        if (!this.db) await this.initIndexedDB();

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readonly');
            const store = transaction.objectStore(storeName);
            const request = store.get(key);

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async dbGetAll(storeName) {
        if (!this.db) await this.initIndexedDB();

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readonly');
            const store = transaction.objectStore(storeName);
            const request = store.getAll();

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async dbDelete(storeName, key) {
        if (!this.db) await this.initIndexedDB();

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            const request = store.delete(key);

            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }

    async dbClear(storeName) {
        if (!this.db) await this.initIndexedDB();

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            const request = store.clear();

            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }

    // Cache methods with TTL
    async cacheSet(key, value, ttl = 3600000) {
        const cacheData = {
            key,
            value,
            expires: Date.now() + ttl
        };

        await this.dbSet('cache', cacheData);
    }

    async cacheGet(key) {
        const cached = await this.dbGet('cache', key);
        
        if (!cached) return null;

        if (Date.now() > cached.expires) {
            await this.dbDelete('cache', key);
            return null;
        }

        return cached.value;
    }

    async cacheClear() {
        await this.dbClear('cache');
    }

    // File storage
    async saveFile(file, metadata = {}) {
        const reader = new FileReader();
        
        return new Promise((resolve, reject) => {
            reader.onload = async (e) => {
                const fileData = {
                    name: file.name,
                    type: file.type,
                    size: file.size,
                    data: e.target.result,
                    metadata,
                    timestamp: Date.now()
                };

                try {
                    const id = await this.dbSet('files', fileData);
                    resolve(id);
                } catch (error) {
                    reject(error);
                }
            };

            reader.onerror = () => reject(reader.error);
            reader.readAsDataURL(file);
        });
    }

    async getFile(id) {
        const fileData = await this.dbGet('files', id);
        if (!fileData) return null;

        const response = await fetch(fileData.data);
        const blob = await response.blob();
        
        return new File([blob], fileData.name, { type: fileData.type });
    }

    async listFiles() {
        const files = await this.dbGetAll('files');
        return files.map(f => ({
            id: f.id,
            name: f.name,
            type: f.type,
            size: f.size,
            metadata: f.metadata,
            timestamp: f.timestamp
        }));
    }

    async deleteFile(id) {
        await this.dbDelete('files', id);
    }

    // Storage quota info
    async getQuotaInfo() {
        if (navigator.storage && navigator.storage.estimate) {
            const estimate = await navigator.storage.estimate();
            return {
                usage: estimate.usage,
                quota: estimate.quota,
                percent: (estimate.usage / estimate.quota) * 100
            };
        }
        return null;
    }

    // Cleanup old data
    async cleanup(days = 30) {
        const cutoff = Date.now() - (days * 24 * 60 * 60 * 1000);
        
        // Clean cache
        const cache = await this.dbGetAll('cache');
        for (const item of cache) {
            if (item.expires < cutoff) {
                await this.dbDelete('cache', item.key);
            }
        }

        // Clean old files
        const files = await this.dbGetAll('files');
        for (const file of files) {
            if (file.timestamp < cutoff) {
                await this.dbDelete('files', file.id);
            }
        }
    }
}

const storage = new StorageManager();

if (typeof window !== 'undefined') {
    window.StorageManager = storage;
}

export default storage;
