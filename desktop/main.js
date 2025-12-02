/**
 * =============================================================================
 * RECEIPT EXTRACTOR DESKTOP - Enterprise Electron Application
 * =============================================================================
 * 
 * Version:    3.0.0
 * Author:     Receipt Extractor Team
 * Platform:   Electron (Cross-platform Desktop)
 * 
 * Circular Exchange Framework Integration:
 * -----------------------------------------
 * Module ID: desktop-app.main
 * Description: Electron main process for desktop app with Python integration
 * Dependencies: [shared.models.model_manager, shared.config.settings]
 * Exports: [createWindow, runPythonExtraction, IPC handlers]
 * 
 * Note: The main process integrates with the Circular Exchange Framework
 * by spawning Python processes that are registered with the framework.
 * Configuration is shared via the electron-store and IPC messages.
 * 
 * Architecture:
 *   - Main Process: Node.js backend for file operations and Python integration
 *   - Renderer Process: HTML/CSS/JS frontend for user interface
 *   - IPC Communication: Secure inter-process messaging
 * 
 * Table of Contents:
 *   1. Module Imports & Configuration
 *   2. Application State
 *   3. Window Management
 *   4. Python Integration
 *   5. IPC Handlers - System
 *   6. IPC Handlers - Settings
 *   7. IPC Handlers - Models
 *   8. IPC Handlers - File Operations
 *   9. IPC Handlers - Extraction
 *   10. Data Export Utilities
 *   11. Application Lifecycle
 * 
 * =============================================================================
 */

/* =============================================================================
   1. MODULE IMPORTS & CONFIGURATION
   ============================================================================= */

const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');
const Store = require('electron-store');

/* =============================================================================
   2. APPLICATION STATE
   ============================================================================= */

const store = new Store();
let mainWindow;

const isDev = !app.isPackaged;
const EXTRACTION_TIMEOUT = 600000; // 10 minutes
const ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'];

/* =============================================================================
   3. WINDOW MANAGEMENT
   ============================================================================= */

/**
 * Log application information
 * @param {string} message - Log message
 * @param {*} data - Optional data to log
 */
function logInfo(message, data = null) {
    const prefix = `[Receipt Extractor Desktop ${isDev ? 'DEV' : 'PROD'}]`;
    if (data) {
        console.log(prefix, message, data);
    } else {
        console.log(prefix, message);
    }
}

/**
 * Create the main application window
 */
function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        minWidth: 1000,
        minHeight: 700,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        },
        title: 'Receipt Extractor - Desktop App',
        icon: path.join(__dirname, 'assets', 'icon.png')
    });

    const indexPath = isDev 
        ? path.join(__dirname, 'src', 'index.html')
        : path.join(app.getAppPath(), 'src', 'index.html');

    mainWindow.loadFile(indexPath);

    if (isDev) {
        mainWindow.webContents.openDevTools();
    }

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

/* =============================================================================
   4. PYTHON INTEGRATION
   ============================================================================= */

/**
 * Get the Python executable path
 * @returns {string} Python command to use
 */
function getPythonPath() {
    const pythonCommands = process.platform === 'win32' 
        ? ['python', 'python3', 'py']
        : ['python3', 'python'];

    if (store.has('pythonCommand')) {
        return store.get('pythonCommand');
    }

    return pythonCommands[0];
}

/* =============================================================================
   5. IPC HANDLERS - SYSTEM
   ============================================================================= */

/**
 * Check if Python is available on the system
 */
ipcMain.handle('check-python', async () => {
    return new Promise(async (resolve) => {
        const pythonCommands = process.platform === 'win32'
            ? ['python', 'python3', 'py']
            : ['python3', 'python'];

        for (const cmd of pythonCommands) {
            try {
                const testProcess = spawn(cmd, ['--version']);
                let versionOutput = '';

                testProcess.stdout.on('data', (data) => {
                    versionOutput += data.toString();
                });

                testProcess.stderr.on('data', (data) => {
                    versionOutput += data.toString();
                });

                const result = await new Promise((res) => {
                    testProcess.on('error', () => res(false));
                    testProcess.on('close', (code) => {
                        if (code === 0) {
                            logInfo(`Found Python: ${cmd}`, versionOutput.trim());
                            store.set('pythonCommand', cmd);
                            res(true);
                        } else {
                            res(false);
                        }
                    });
                });

                if (result) {
                    resolve({
                        success: true,
                        command: cmd,
                        version: versionOutput.trim()
                    });
                    return;
                }
            } catch (error) {
                continue;
            }
        }

        resolve({
            success: false,
            error: 'Python not found. Please install Python 3.8+ and add it to PATH.'
        });
    });
});

/**
 * Check all dependencies
 */
ipcMain.handle('check-dependencies', async () => {
    try {
        const pythonCheck = await new Promise((resolve) => {
            const pythonCommands = process.platform === 'win32'
                ? ['python', 'python3', 'py']
                : ['python3', 'python'];
            let pythonFound = false;

            const checkNext = async (index) => {
                if (index >= pythonCommands.length) {
                    resolve(pythonFound);
                    return;
                }

                try {
                    const testProcess = spawn(pythonCommands[index], ['--version']);
                    testProcess.on('error', () => checkNext(index + 1));
                    testProcess.on('close', (code) => {
                        if (code === 0) {
                            pythonFound = true;
                            resolve(true);
                        } else {
                            checkNext(index + 1);
                        }
                    });
                } catch (error) {
                    checkNext(index + 1);
                }
            };

            checkNext(0);
        });

        if (!pythonCheck) {
            return {
                python: false,
                dependencies: false,
                message: 'Python not found. Please install Python 3.8+'
            };
        }

        return {
            python: true,
            dependencies: true,
            message: 'All dependencies ready'
        };
    } catch (error) {
        logInfo('Error checking dependencies:', error);
        return {
            python: false,
            dependencies: false,
            message: 'Error checking dependencies'
        };
    }
});

/**
 * Get diagnostic information
 */
ipcMain.handle('get-diagnostics', async () => {
    try {
        const pythonCmd = getPythonPath();
        return {
            platform: process.platform,
            pythonCommand: pythonCmd,
            isDev: isDev,
            appPath: app.getAppPath()
        };
    } catch (error) {
        logInfo('Error getting diagnostics:', error);
        return { error: error.message };
    }
});

/* =============================================================================
   6. IPC HANDLERS - SETTINGS
   ============================================================================= */

/**
 * Get application settings
 */
ipcMain.handle('get-settings', async () => {
    try {
        const settings = {
            lastModel: store.get('lastModel', 'ocr'),
            aiMode: store.get('aiMode', 'fast')
        };
        return settings;
    } catch (error) {
        logInfo('Error getting settings:', error);
        return {
            lastModel: 'ocr',
            aiMode: 'fast'
        };
    }
});

/**
 * Save application settings
 */
ipcMain.handle('save-settings', async (event, settings) => {
    try {
        if (settings.lastModel) {
            store.set('lastModel', settings.lastModel);
        }
        if (settings.aiMode) {
            store.set('aiMode', settings.aiMode);
        }
        return { success: true };
    } catch (error) {
        logInfo('Error saving settings:', error);
        return { success: false, error: error.message };
    }
});

/* =============================================================================
   7. IPC HANDLERS - MODELS
   ============================================================================= */

/**
 * Get available models configuration
 */
ipcMain.handle('get-models', async () => {
    try {
        const configPath = path.join(__dirname, '..', 'shared', 'config', 'models_config.json');
        const configData = fs.readFileSync(configPath, 'utf-8');
        const config = JSON.parse(configData);

        const models = Object.values(config.available_models).map(model => ({
            id: model.id,
            name: model.name,
            type: model.type,
            description: model.description,
            requires_auth: model.requires_auth || false,
            capabilities: model.capabilities || {}
        }));

        return {
            success: true,
            models: models,
            default_model: config.default_model
        };
    } catch (error) {
        logInfo('Error loading models config:', error);
        return {
            success: false,
            error: 'Failed to load models configuration'
        };
    }
});

/* =============================================================================
   8. IPC HANDLERS - FILE OPERATIONS
   ============================================================================= */

/**
 * Get file statistics
 */
ipcMain.handle('get-file-stats', async (event, filePath) => {
    try {
        const stats = fs.statSync(filePath);
        return {
            success: true,
            size: stats.size,
            modified: stats.mtime
        };
    } catch (error) {
        logInfo('Error getting file stats:', error);
        return { success: false, error: error.message };
    }
});

/**
 * Select a single image file
 */
ipcMain.handle('select-image', async () => {
    const result = await dialog.showOpenDialog(mainWindow, {
        properties: ['openFile'],
        filters: [
            { name: 'Images', extensions: ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'tif'] }
        ]
    });

    if (result.canceled) {
        return { success: false, canceled: true };
    }

    const filePath = result.filePaths[0];
    const stats = fs.statSync(filePath);

    return {
        success: true,
        canceled: false,
        path: filePath,
        size: stats.size,
        name: path.basename(filePath)
    };
});

/**
 * Select multiple image files
 */
ipcMain.handle('select-images', async () => {
    const result = await dialog.showOpenDialog(mainWindow, {
        properties: ['openFile', 'multiSelections'],
        filters: [
            { name: 'Images', extensions: ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'tif'] }
        ]
    });

    if (result.canceled) {
        return { canceled: true };
    }

    const files = result.filePaths.map(filePath => {
        const stats = fs.statSync(filePath);
        return {
            path: filePath,
            size: stats.size,
            name: path.basename(filePath)
        };
    });

    return { canceled: false, files: files };
});

/* =============================================================================
   9. IPC HANDLERS - EXTRACTION
   ============================================================================= */

/**
 * Extract receipt data from an image
 */
ipcMain.handle('extract-receipt', async (event, options) => {
    return new Promise((resolve) => {
        const pythonCmd = getPythonPath();
        const scriptPath = path.join(__dirname, 'process_receipt.py');
        const imagePath = options.imagePath || options;
        const modelId = options.model || options.modelId;

        logInfo(`Extracting receipt from: ${imagePath}`);
        logInfo(`Using model: ${modelId || 'default'}`);

        const args = [scriptPath, imagePath];
        if (modelId) {
            args.push(modelId);
        }

        const pythonProcess = spawn(pythonCmd, args);
        let outputData = '';
        let errorData = '';

        pythonProcess.stdout.on('data', (data) => {
            outputData += data.toString();
        });

        pythonProcess.stderr.on('data', (data) => {
            errorData += data.toString();
        });

        const timeout = setTimeout(() => {
            pythonProcess.kill();
            resolve({
                success: false,
                error: 'Extraction timeout (10 minutes exceeded)'
            });
        }, EXTRACTION_TIMEOUT);

        pythonProcess.on('close', (code) => {
            clearTimeout(timeout);

            if (code !== 0) {
                logInfo('Python process failed:', errorData);
                resolve({
                    success: false,
                    error: errorData || 'Extraction failed'
                });
                return;
            }

            try {
                let result = null;
                const lines = outputData.split('\n');

                // Find JSON output in the lines
                for (let i = lines.length - 1; i >= 0; i--) {
                    const line = lines[i].trim();
                    if (line.startsWith('{')) {
                        try {
                            result = JSON.parse(line);
                            break;
                        } catch (e) {
                            // Try accumulating lines
                            let accumulated = line;
                            for (let j = i + 1; j < lines.length; j++) {
                                accumulated += '\n' + lines[j];
                                try {
                                    result = JSON.parse(accumulated);
                                    break;
                                } catch (e2) {
                                    continue;
                                }
                            }
                            if (result) break;
                        }
                    }
                }

                if (result) {
                    resolve(result);
                } else {
                    resolve({
                        success: false,
                        error: 'Failed to parse extraction result'
                    });
                }
            } catch (error) {
                logInfo('Parse error:', error);
                resolve({
                    success: false,
                    error: 'Invalid JSON response from extraction'
                });
            }
        });

        pythonProcess.on('error', (error) => {
            clearTimeout(timeout);
            logInfo('Process error:', error);
            resolve({
                success: false,
                error: `Failed to start Python: ${error.message}`
            });
        });
    });
});

/**
 * Save extraction results to file
 */
ipcMain.handle('save-results', async (event, options) => {
    const data = options.data || options;
    const defaultPath = options.defaultPath || `receipt_${Date.now()}.json`;
    const format = options.format || 'json';

    const result = await dialog.showSaveDialog(mainWindow, {
        defaultPath: defaultPath,
        filters: [
            { name: 'JSON', extensions: ['json'] },
            { name: 'Text', extensions: ['txt'] },
            { name: 'CSV', extensions: ['csv'] }
        ]
    });

    if (result.canceled) {
        return { canceled: true };
    }

    try {
        let content;
        const fileFormat = result.filePath.split('.').pop().toLowerCase();

        switch (fileFormat) {
            case 'json':
                content = JSON.stringify(data, null, 2);
                break;
            case 'txt':
                content = formatAsText(data);
                break;
            case 'csv':
                content = formatAsCSV(data);
                break;
            default:
                content = JSON.stringify(data, null, 2);
        }

        fs.writeFileSync(result.filePath, content, 'utf-8');
        return { success: true, path: result.filePath };
    } catch (error) {
        logInfo('Save error:', error);
        return { success: false, error: error.message };
    }
});

/* =============================================================================
   10. DATA EXPORT UTILITIES
   ============================================================================= */

/**
 * Format extraction data as plain text
 * @param {Object} data - Extraction data
 * @returns {string} Formatted text
 */
function formatAsText(data) {
    let text = '=== RECEIPT EXTRACTION ===\n\n';

    text += '--- Store Information ---\n';
    text += `Name: ${data.store?.name || '-'}\n`;
    text += `Address: ${data.store?.address || '-'}\n`;
    text += `Phone: ${data.store?.phone || '-'}\n\n`;

    text += '--- Transaction Details ---\n';
    text += `Date: ${data.date || '-'}\n`;
    text += `Total: $${data.totals?.total || '-'}\n\n`;

    if (data.items && data.items.length > 0) {
        text += '--- Line Items ---\n';
        data.items.forEach((item, index) => {
            text += `${index + 1}. ${item.name} - $${item.total_price}\n`;
        });
    }

    text += `\n--- Extraction Info ---\n`;
    text += `Model: ${data.model}\n`;

    return text;
}

/**
 * Format extraction data as CSV
 * @param {Object} data - Extraction data
 * @returns {string} CSV formatted string
 */
function formatAsCSV(data) {
    let csv = 'Item,Quantity,Price\n';

    if (data.items && data.items.length > 0) {
        data.items.forEach(item => {
            const quantity = item.quantity || 1;
            const price = item.total_price || '0.00';
            csv += `"${item.name}",${quantity},${price}\n`;
        });
    }

    csv += '\nStore Information\n';
    csv += `Name,${data.store?.name || ''}\n`;
    csv += `Address,${data.store?.address || ''}\n`;

    csv += '\nTransaction\n';
    csv += `Date,${data.date || ''}\n`;
    csv += `Total,${data.totals?.total || ''}\n`;

    return csv;
}

/* =============================================================================
   11. APPLICATION LIFECYCLE
   ============================================================================= */

app.on('ready', () => {
    createWindow();
    logInfo('Application started');
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (mainWindow === null) {
        createWindow();
    }
});
