/**
 * =============================================================================
 * RECEIPT EXTRACTOR DESKTOP - Preload Script
 * =============================================================================
 * 
 * This script runs in a privileged context before the renderer process loads.
 * It safely exposes Node.js and Electron APIs to the renderer via contextBridge.
 * 
 * Version:    3.0.0
 * Author:     Receipt Extractor Team
 * 
 * =============================================================================
 */

const { contextBridge, ipcRenderer } = require('electron');

/**
 * Expose protected methods that allow the renderer process to use
 * the ipcRenderer without exposing the entire object
 */
contextBridge.exposeInMainWorld('electronAPI', {
    // Image selection
    selectImage: () => ipcRenderer.invoke('select-image'),
    selectImages: () => ipcRenderer.invoke('select-images'),
    
    // Receipt extraction
    extractReceipt: (options) => ipcRenderer.invoke('extract-receipt', options),
    
    // Progress monitoring
    onProgress: (callback) => {
        ipcRenderer.on('extraction-progress', (event, data) => callback(data));
    },
    
    // Results handling
    saveResults: (data) => ipcRenderer.invoke('save-results', data),
    
    // Settings management
    getSettings: () => ipcRenderer.invoke('get-settings'),
    saveSettings: (settings) => ipcRenderer.invoke('save-settings', settings),
    
    // System checks
    checkDependencies: () => ipcRenderer.invoke('check-dependencies'),
    getDiagnostics: () => ipcRenderer.invoke('get-diagnostics'),
    
    // File operations
    getFileStats: (filePath) => ipcRenderer.invoke('get-file-stats', filePath),
    
    // Model management
    getModels: () => ipcRenderer.invoke('get-models')
});
