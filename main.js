const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');
const Store = require('electron-store');

const store = new Store();
let mainWindow;
const isDev = !app.isPackaged;

// Constants
const EXTRACTION_TIMEOUT = 600000; // 10 minutes
const ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'];

// Diagnostic logging
function logInfo(message, data = null) {
  const prefix = `[Receipt Extractor ${isDev ? 'DEV' : 'PROD'}]`;
  if (data) {
    console.log(prefix, message, data);
  } else {
    console.log(prefix, message);
  }
}

function getPythonPath() {
  // Try multiple Python command names
  const pythonCommands = process.platform === 'win32'
    ? ['python', 'python3', 'py']
    : ['python3', 'python'];

  // Store the working python command
  if (store.has('pythonCommand')) {
    return store.get('pythonCommand');
  }

  return pythonCommands[0];
}

function getScriptPath(model = 'ocr') {
  const scriptName = model === 'ocr' ? 'extract_ocr.py' : 'extract_donut.py';
  let scriptPath;

  if (isDev) {
    scriptPath = path.join(__dirname, scriptName);
  } else {
    // In production, files are in resources/app/ (no asar compression)
    const possiblePaths = [
      path.join(app.getAppPath(), scriptName),
      path.join(process.resourcesPath, 'app', scriptName),
      path.join(__dirname, scriptName),
    ];

    for (const tryPath of possiblePaths) {
      if (fs.existsSync(tryPath)) {
        scriptPath = tryPath;
        break;
      }
    }

    if (!scriptPath) scriptPath = path.join(app.getAppPath(), scriptName);
  }

  return scriptPath;
}

async function checkPythonInstallation() {
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
          resolve({ success: true, command: cmd, version: versionOutput.trim() });
          return;
        }
      } catch (err) {
        logInfo(`Failed to check ${cmd}:`, err.message);
      }
    }

    resolve({ success: false });
  });
}

async function checkPythonDependencies() {
  return new Promise((resolve) => {
    const pythonPath = getPythonPath();
    const checkScript = `
import sys
try:
    import torch
    import transformers
    import PIL
    import cv2
    import numpy
    print("DEPS_OK")
    print(f"PyTorch: {torch.__version__}")
    print(f"Transformers: {transformers.__version__}")
except ImportError as e:
    print(f"DEPS_MISSING: {e}")
    sys.exit(1)
`;

    const pythonProcess = spawn(pythonPath, ['-c', checkScript]);
    let output = '';
    let error = '';

    pythonProcess.stdout.on('data', (data) => {
      output += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
      error += data.toString();
    });

    pythonProcess.on('close', (code) => {
      if (code === 0 && output.includes('DEPS_OK')) {
        logInfo('Python dependencies check: OK', output);
        resolve({ success: true, details: output });
      } else {
        logInfo('Python dependencies check: FAILED', error || output);
        resolve({ success: false, details: error || output });
      }
    });

    pythonProcess.on('error', (err) => {
      logInfo('Failed to run dependency check:', err.message);
      resolve({ success: false, error: err.message });
    });
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1200,
    minHeight: 700,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    backgroundColor: '#fafafa',
    autoHideMenuBar: true,
    show: false
  });

  mainWindow.loadFile(path.join(__dirname, 'index.html'));
  mainWindow.once('ready-to-show', () => mainWindow.show());
  if (isDev) mainWindow.webContents.openDevTools();
  mainWindow.on('closed', () => mainWindow = null);
}

app.whenReady().then(async () => {
  logInfo('=== Application Starting ===');
  logInfo('isDev:', isDev);
  logInfo('App Path:', app.getAppPath());
  logInfo('Resources Path:', process.resourcesPath);
  logInfo('Platform:', process.platform);
  logInfo('Arch:', process.arch);

  // Check Python installation
  const pythonCheck = await checkPythonInstallation();

  if (!pythonCheck.success) {
    logInfo('Python check FAILED');
    const choice = dialog.showMessageBoxSync({
      type: 'error',
      title: 'Python Not Found',
      message: 'Python is required to run this application',
      detail:
        'Python 3.8 or higher must be installed and added to PATH.\n\n' +
        'Installation steps:\n' +
        '1. Download Python from: https://www.python.org/downloads/\n' +
        '2. Run the installer\n' +
        '3. CHECK "Add Python to PATH" during installation\n' +
        '4. Restart this application\n\n' +
        'The application will now start, but extraction will not work until Python is installed.',
      buttons: ['Continue Anyway', 'Exit'],
      defaultId: 0,
      cancelId: 1
    });

    if (choice === 1) {
      app.quit();
      return;
    }
  } else {
    logInfo('Python check OK:', pythonCheck.version);

    // Check Python dependencies
    const depsCheck = await checkPythonDependencies();

    if (!depsCheck.success) {
      logInfo('Dependencies check FAILED:', depsCheck.details);

      dialog.showMessageBox({
        type: 'warning',
        title: 'Python Dependencies Missing',
        message: 'Required Python packages are not installed',
        detail:
          'The following packages are required:\n' +
          '- torch (PyTorch)\n' +
          '- transformers\n' +
          '- pillow\n' +
          '- opencv-python\n' +
          '- numpy\n' +
          '- pytesseract (optional, for OCR)\n\n' +
          'To install dependencies:\n' +
          '1. Open Command Prompt (Windows) or Terminal (Mac/Linux)\n' +
          '2. Navigate to the app folder\n' +
          '3. Run: pip install -r requirements.txt\n\n' +
          'Or install individually:\n' +
          'pip install torch transformers pillow opencv-python numpy pytesseract\n\n' +
          'Extraction will not work until dependencies are installed.',
        buttons: ['OK']
      });
    } else {
      logInfo('Dependencies check OK');
    }
  }

  // Check if Python scripts exist
  try {
    const ocrScript = getScriptPath('ocr');
    const donutScript = getScriptPath('donut');

    logInfo('Checking Python scripts:');
    logInfo('OCR script:', ocrScript, 'exists:', fs.existsSync(ocrScript));
    logInfo('Donut script:', donutScript, 'exists:', fs.existsSync(donutScript));

    if (!fs.existsSync(ocrScript) || !fs.existsSync(donutScript)) {
      dialog.showMessageBox({
        type: 'error',
        title: 'Installation Error',
        message: 'Python scripts not found',
        detail:
          'The application installation appears to be corrupted.\n\n' +
          `Expected locations:\n` +
          `- ${ocrScript}\n` +
          `- ${donutScript}\n\n` +
          'Please reinstall the application.',
        buttons: ['OK']
      });
    }
  } catch (err) {
    logInfo('Error checking scripts:', err);
  }

  createWindow();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});

ipcMain.handle('select-image', async (event) => {
  try {
    if (!mainWindow || mainWindow.isDestroyed()) {
      return { success: false, error: 'Window not available' };
    }

    const result = await dialog.showOpenDialog(mainWindow, {
      properties: ['openFile'],
      filters: [
        { name: 'Images', extensions: ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'tif'] },
        { name: 'All Files', extensions: ['*'] }
      ],
      title: 'Select Receipt Image'
    });

    if (result.canceled || !result.filePaths || result.filePaths.length === 0) {
      return { success: false, cancelled: true };
    }

    const filePath = result.filePaths[0];
    const ext = path.extname(filePath).toLowerCase();

    if (!ALLOWED_IMAGE_EXTENSIONS.includes(ext)) {
      return {
        success: false,
        error: 'Invalid file type',
        details: `Only image files are supported: ${ALLOWED_IMAGE_EXTENSIONS.join(', ')}`
      };
    }

    if (!fs.existsSync(filePath)) {
      return { success: false, error: 'File not found' };
    }

    return { success: true, path: filePath };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('get-file-stats', async (event, filePath) => {
  try {
    if (fs.existsSync(filePath)) {
      const stats = fs.statSync(filePath);
      return { success: true, size: stats.size };
    }
    return { success: false };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('extract-receipt', async (event, { imagePath, model, mode }) => {
  return new Promise((resolve) => {
    const pythonPath = getPythonPath();
    const scriptPath = getScriptPath(model);

    if (isDev) {
      console.log('[Main] Starting extraction...');
      console.log('[Main] Python:', pythonPath);
      console.log('[Main] Script:', scriptPath);
      console.log('[Main] Model:', model);
      console.log('[Main] Image:', imagePath);
      console.log('[Main] Mode:', mode);
    }

    if (!fs.existsSync(scriptPath)) {
      resolve({
        success: false,
        error: 'Python script not found',
        details: `Expected location: ${scriptPath}\n\nPlease reinstall the application.`
      });
      return;
    }

    const ext = path.extname(imagePath).toLowerCase();
    if (!ALLOWED_IMAGE_EXTENSIONS.includes(ext)) {
      resolve({
        success: false,
        error: 'Invalid file type',
        details: `Only image files are supported: ${ALLOWED_IMAGE_EXTENSIONS.join(', ')}`
      });
      return;
    }

    if (!fs.existsSync(imagePath)) {
      resolve({
        success: false,
        error: 'Image file not found',
        details: `The selected image could not be found:\n${imagePath}`
      });
      return;
    }

    const args = [scriptPath, imagePath];

    if (model !== 'ocr') {
      args.push('--model', model);
      if (mode === 'quality') {
        args.push('--quality');
      }
    }

    if (isDev) {
      console.log('[Main] Executing:', pythonPath, args.join(' '));
    }

    const pythonProcess = spawn(pythonPath, args, {
      env: {
        ...process.env,
        PYTHONUNBUFFERED: '1',
        PYTHONIOENCODING: 'utf-8'
      }
    });

    let timeoutId = setTimeout(() => {
      if (pythonProcess && !pythonProcess.killed) {
        pythonProcess.kill();
        resolve({
          success: false,
          error: 'Extraction timeout',
          details: `Process exceeded maximum time limit of ${EXTRACTION_TIMEOUT / 60000} minutes.\nPlease try a different model or smaller image.`
        });
      }
    }, EXTRACTION_TIMEOUT);

    let outputData = '';
    let errorData = '';
    let progressLog = [];

    pythonProcess.stdout.on('data', (data) => {
      const text = data.toString();
      outputData += text;
      progressLog.push(text);
      if (isDev) {
        console.log('[Python]', text.trim());
      }
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send('extraction-progress', text);
      }
    });

    pythonProcess.stderr.on('data', (data) => {
      const text = data.toString();
      errorData += text;
      progressLog.push(`ERROR: ${text}`);
      if (isDev) {
        console.error('[Python Error]', text.trim());
      }
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send('extraction-progress', `⚠️ ${text}`);
      }
    });

    pythonProcess.on('close', (code) => {
      clearTimeout(timeoutId);

      if (isDev) {
        console.log('[Main] Process exited with code:', code);
      }

      if (code === 0) {
        const baseName = path.basename(imagePath, path.extname(imagePath));
        const dirName = path.dirname(imagePath);
        
        let outputFile;
        if (model === 'ocr') {
          outputFile = path.join(dirName, `${baseName}_ocr.json`);
        } else {
          outputFile = mode === 'quality'
            ? path.join(dirName, `${baseName}_${model}_quality.json`)
            : path.join(dirName, `${baseName}_${model}.json`);
        }

        if (isDev) {
          console.log('[Main] Looking for output file:', outputFile);
        }

        if (fs.existsSync(outputFile)) {
          try {
            const resultData = JSON.parse(fs.readFileSync(outputFile, 'utf8'));

            if (isDev) {
              console.log('[Main] Successfully read results');
            }

            let itemCount = 0;
            if (resultData.item_count) {
              itemCount = resultData.item_count;
            } else if (resultData.best_result && resultData.best_result.receipt) {
              itemCount = resultData.best_result.receipt.item_count || 0;
            }

            if (isDev) {
              console.log('[Main] Item count:', itemCount);
            }
            
            resolve({
              success: true,
              data: resultData,
              log: progressLog.join('\n'),
              outputFile: outputFile,
              extractor: model
            });
          } catch (err) {
            if (isDev) {
              console.error('[Main] Failed to parse results:', err);
            }
            resolve({
              success: false,
              error: `Failed to parse results: ${err.message}`,
              log: progressLog.join('\n')
            });
          }
        } else {
          if (isDev) {
            console.error('[Main] Output file not found');
          }
          resolve({
            success: false,
            error: 'Output file not found',
            details: `Expected: ${outputFile}\n\nThe Python script may have failed.\nCheck console output for errors.`,
            log: progressLog.join('\n')
          });
        }
      } else {
        if (isDev) {
          console.error('[Main] Process failed with code:', code);
        }
        
        let errorMessage = `Process exited with code ${code}`;
        let errorDetails = errorData || outputData;
        
        if (errorData.includes('No module named')) {
          const moduleName = errorData.match(/No module named '([^']+)'/)?.[1];
          errorMessage = 'Missing Python Dependencies';
          errorDetails = `Required Python package '${moduleName}' is not installed.\n\n` +
                        'Please run:\n' +
                        `pip install ${moduleName}\n\n` +
                        'Or install all dependencies:\n' +
                        'pip install -r requirements.txt';
        } else if (errorData.toLowerCase().includes('tesseract') && errorData.includes('not found')) {
          errorMessage = 'Tesseract OCR Not Found';
          errorDetails = 'Tesseract OCR is not installed or not in PATH.\n\n' +
                        'Please install from:\n' +
                        'https://github.com/UB-Mannheim/tesseract/wiki\n\n' +
                        'Or use AI models instead.';
        } else if (errorData.toLowerCase().includes('python') && errorData.includes('not found')) {
          errorMessage = 'Python Not Found';
          errorDetails = 'Python is not installed or not in PATH.\n\n' +
                        'Please install Python 3.8+ from:\n' +
                        'https://www.python.org/downloads/';
        } else if (errorData.includes('Cannot access') || errorData.includes('401') || errorData.includes('403')) {
          errorMessage = 'Model Access Error';
          errorDetails = 'Cannot access the AI model.\n\n' +
                        'For PaliGemma: Accept license at https://huggingface.co/google/gemma-2b\n' +
                        'For AdamCodd: Request access from adamcoddml@gmail.com\n' +
                        'Use huggingface-cli login for authentication.\n\n' +
                        'Or try OCR or SROIE models instead.';
        }
        
        resolve({
          success: false,
          error: errorMessage,
          details: errorDetails,
          log: progressLog.join('\n')
        });
      }
    });

    pythonProcess.on('error', (err) => {
      clearTimeout(timeoutId);

      if (isDev) {
        console.error('[Main] Process error:', err);
      }

      let errorMessage = 'Failed to start Python';
      let errorDetails = err.message;

      if (err.code === 'ENOENT') {
        errorMessage = 'Python Not Found';
        errorDetails = 'Python is not installed or not in PATH.\n\n' +
                      'Please install Python 3.8+ from:\n' +
                      'https://www.python.org/downloads/\n\n' +
                      'Make sure to check "Add Python to PATH" during installation.';
      }

      resolve({
        success: false,
        error: errorMessage,
        details: errorDetails,
        log: progressLog.join('\n')
      });
    });
  });
});

ipcMain.handle('save-results', async (event, { data, defaultPath }) => {
  try {
    if (!mainWindow || mainWindow.isDestroyed()) {
      return { success: false, error: 'Window not available' };
    }
    
    const result = await dialog.showSaveDialog(mainWindow, {
      defaultPath: defaultPath || 'receipt_extraction.json',
      filters: [
        { name: 'JSON Files', extensions: ['json'] },
        { name: 'All Files', extensions: ['*'] }
      ]
    });

    if (result.canceled || !result.filePath) {
      return { success: false, cancelled: true };
    }
    
    fs.writeFileSync(result.filePath, JSON.stringify(data, null, 2));
    return { success: true, path: result.filePath };
  } catch (err) {
    if (isDev) {
      console.error('[Main] Save error:', err);
    }
    return { success: false, error: err.message };
  }
});

ipcMain.handle('get-settings', () => {
  return store.get('settings', {
    lastModel: 'ocr',
    aiMode: 'fast'
  });
});

ipcMain.handle('save-settings', (event, settings) => {
  if (isDev) {
    console.log('[Main] Saving settings:', settings);
  }
  store.set('settings', settings);
  return { success: true };
});

ipcMain.handle('check-dependencies', async () => {
  const pythonCheck = await checkPythonInstallation();

  if (!pythonCheck.success) {
    return {
      python: false,
      pythonVersion: null,
      dependencies: false,
      scripts: false,
      message: 'Python not found. Please install Python 3.8 or higher.'
    };
  }

  const depsCheck = await checkPythonDependencies();
  const ocrScript = getScriptPath('ocr');
  const donutScript = getScriptPath('donut');
  const scriptsExist = fs.existsSync(ocrScript) && fs.existsSync(donutScript);

  return {
    python: true,
    pythonVersion: pythonCheck.version,
    pythonCommand: pythonCheck.command,
    dependencies: depsCheck.success,
    dependencyDetails: depsCheck.details || depsCheck.error,
    scripts: scriptsExist,
    scriptPaths: {
      ocr: ocrScript,
      donut: donutScript
    },
    message: depsCheck.success
      ? 'All dependencies are installed and working!'
      : 'Python is installed but some dependencies are missing.'
  };
});

ipcMain.handle('get-diagnostics', async () => {
  logInfo('Running full diagnostics...');

  const pythonCheck = await checkPythonInstallation();
  const depsCheck = pythonCheck.success ? await checkPythonDependencies() : { success: false };

  const ocrScript = getScriptPath('ocr');
  const donutScript = getScriptPath('donut');

  const diagnostics = {
    app: {
      version: app.getVersion(),
      isDev: isDev,
      appPath: app.getAppPath(),
      resourcesPath: process.resourcesPath,
    },
    system: {
      platform: process.platform,
      arch: process.arch,
      nodeVersion: process.versions.node,
      electronVersion: process.versions.electron,
      chromeVersion: process.versions.chrome,
    },
    python: {
      found: pythonCheck.success,
      command: pythonCheck.command || 'not found',
      version: pythonCheck.version || 'not found',
    },
    dependencies: {
      installed: depsCheck.success,
      details: depsCheck.details || depsCheck.error || 'not checked',
    },
    scripts: {
      ocr: {
        path: ocrScript,
        exists: fs.existsSync(ocrScript),
      },
      donut: {
        path: donutScript,
        exists: fs.existsSync(donutScript),
      },
    },
  };

  logInfo('Diagnostics complete:', diagnostics);
  return diagnostics;
});
