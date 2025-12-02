/**
 * =============================================================================
 * CIRCULAR EXCHANGE COMPLIANT MODULE
 * =============================================================================
 * 
 * Module: desktop-app.preload
 * Path: desktop-app/preload.js
 * Description: Electron preload script - secure IPC bridge for renderer process
 * Compliance Version: 2.0.0
 * 
 * CIRCULAR EXCHANGE INTEGRATION:
 * This module is integrated with the Circular Information Exchange Framework.
 * It provides encapsulated, secure communication channels between the main
 * process and renderer, following TCP/IP-like protocol discipline for internal
 * message passing (request/response pattern via IPC invoke).
 * 
 * Dependencies: electron (contextBridge, ipcRenderer)
 * Exports: electronAPI (exposed to renderer via contextBridge)
 * 
 * GOVERNMENTAL STANDARDS COMPLIANCE:
 * - Security: Context isolation enabled, no direct Node.js exposure
 * - Accessibility: API supports screen reader announcements
 * - Data Handling: Structured message protocol for all IPC calls
 * - Reliability: Promise-based invoke pattern with error propagation
 * 
 * AI AGENT INSTRUCTIONS:
 * - Use PROJECT_CONFIG for all configuration values
 * - All IPC channels follow request/response pattern
 * - Use VariablePackages for shared state synchronization
 * - Subscribe to relevant change notifications from main process
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
