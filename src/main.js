const { app, BrowserWindow, globalShortcut, ipcMain, screen } = require('electron');
const path = require('path');
const fs = require('fs');
const Store = require('electron-store');
const axios = require('axios');

const store = new Store();
let mainWindow;
let overlayWindow;
const BACKEND_PORT = 8888;
const BACKEND_URL = `http://localhost:${BACKEND_PORT}`;

// Utility functions for safe window operations
function safeOverlayOperation(operation) {
  if (overlayWindow && !overlayWindow.isDestroyed()) {
    try {
      return operation(overlayWindow);
    } catch (error) {
      console.error('Error performing overlay operation:', error);
      return false;
    }
  }
  return false;
}

function safeMainWindowOperation(operation) {
  if (mainWindow && !mainWindow.isDestroyed()) {
    try {
      return operation(mainWindow);
    } catch (error) {
      console.error('Error performing main window operation:', error);
      return false;
    }
  }
  return false;
}

// Ensure single instance
const gotTheLock = app.requestSingleInstanceLock();

if (!gotTheLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    safeOverlayOperation((overlay) => {
      if (overlay.isMinimized()) overlay.restore();
      overlay.focus();
      overlay.show();
    });
  });
}

function createMainWindow() {
  if (!app.isReady()) {
    console.error('Cannot create main window - app is not ready');
    return;
  }
  
  mainWindow = new BrowserWindow({
    width: 400,
    height: 300,
    show: false,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  mainWindow.loadFile(path.join(__dirname, 'main.html'));
  
  if (process.argv.includes('--dev')) {
    mainWindow.webContents.openDevTools();
  }
  
  // Handle main window closed
  mainWindow.on('closed', () => {
    console.log('Main window closed');
    mainWindow = null;
  });
}

function createOverlayWindow() {
  if (!app.isReady()) {
    console.error('Cannot create overlay window - app is not ready');
    return;
  }
  
  const primaryDisplay = screen.getPrimaryDisplay();
  const { width, height } = primaryDisplay.workAreaSize;
  
  overlayWindow = new BrowserWindow({
    width: 700, // Match the width from overlay-unified.html
    height: 500,
    x: (width - 700) / 2, // Center horizontally
    y: 100, // Position near top of screen
    frame: false,
    alwaysOnTop: true,
    skipTaskbar: true,
    resizable: false,
    transparent: true,
    show: false,
    focusable: true,
    hasShadow: true,
    type: 'panel', // Makes it a floating panel
    visualEffectState: 'active', // Enables vibrancy effect
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      backgroundThrottling: false,
      // Enable audio capture permissions
      webSecurity: false,
      allowRunningInsecureContent: false,
      enableWebSQL: false,
      autoplayPolicy: 'no-user-gesture-required' // Allow audio without user gesture
    }
  });

  // Allow mouse events to pass through by default
  overlayWindow.setIgnoreMouseEvents(true, { forward: true });

  overlayWindow.loadFile(path.join(__dirname, 'overlay-unified.html'));
  
  // Listen for response state changes (for potential future features)
  ipcMain.on('overlay-showing-response', (event, showing) => {
    console.log('Overlay response state changed:', showing ? 'SHOWING' : 'HIDDEN');
  });

  // Handle overlay window errors
  overlayWindow.webContents.on('crashed', () => {
    console.error('Overlay window crashed, recreating...');
    setTimeout(() => {
      if (!overlayWindow || overlayWindow.isDestroyed()) {
        createOverlayWindow();
      }
    }, 1000);
  });
  
  overlayWindow.webContents.on('unresponsive', () => {
    console.warn('Overlay window became unresponsive');
  });
  
  overlayWindow.webContents.on('responsive', () => {
    console.log('Overlay window became responsive again');
  });
  
  // Keep overlay visible and on top when switching apps
  overlayWindow.on('blur', () => {
    console.log('Overlay blur event - ensuring overlay stays visible and on top');
    overlayWindow.setAlwaysOnTop(true, 'screen-saver');
    overlayWindow.setVisibleOnAllWorkspaces(true);
  });

  if (process.argv.includes('--dev')) {
    overlayWindow.webContents.openDevTools();
  }
  
  // Handle overlay window closed
  overlayWindow.on('closed', () => {
    console.log('Overlay window closed');
    overlayWindow = null;
  });
}

function registerIpcHandlers() {
  // IPC handler to toggle mouse event ignoring
  ipcMain.on('set-ignore-mouse-events', (event, ignore, options) => {
    if (overlayWindow && !overlayWindow.isDestroyed()) {
      overlayWindow.setIgnoreMouseEvents(ignore, options);
    }
  });

  // IPC handler to trigger screen capture and OCR
  ipcMain.handle('capture-and-ocr', async () => {
    try {
      const response = await axios.post(`${BACKEND_URL}/command`, {
        command: 'read screen text',
        context: store.get('context', [])
      }, {
        timeout: 30000,
        family: 4
      });
      
      if (response.data.success) {
        return {
          success: true,
          text: response.data.result
        };
      } else {
        return {
          success: false,
          error: response.data.error || 'OCR failed'
        };
      }
    } catch (error) {
      console.error('Error during screen capture and OCR:', error);
      return {
        success: false,
        error: error.message
      };
    }
  });
  
  // IPC handler for screen capture
  ipcMain.handle('capture-screen', async () => {
    try {
      const { desktopCapturer } = require('electron');
      const sources = await desktopCapturer.getSources({ types: ['screen'] });
      if (sources.length > 0) {
        return { success: true, source: sources[0].id };
      } else {
        return { success: false, error: 'No screen sources found' };
      }
    } catch (error) {
      console.error('Error capturing screen:', error);
      return { success: false, error: error.message };
    }
  });
  
  // IPC handler for audio transcription
  ipcMain.handle('transcribe-audio', async (event, audioData) => {
    try {
      // Send audio data to backend for processing
      const response = await axios.post(`${BACKEND_URL}/transcribe_audio`, {
        audio_data: audioData
      }, {
        timeout: 10000 // 10 second timeout
      });
      
      return response.data;
    } catch (error) {
      console.error('Error during audio transcription:', error);
      return { success: false, error: error.message };
    }
  });
}

function registerGlobalShortcuts() {
  // Register global shortcut for activation
  const shortcut = process.platform === 'darwin' ? 'Cmd+Space' : 'Ctrl+Space';
  
  globalShortcut.register(shortcut, () => {
    safeOverlayOperation((overlay) => {
      if (overlay.isVisible()) {
        overlay.hide();
      } else {
        // Ensure the overlay is always on top and focused when shown
        overlay.setAlwaysOnTop(true, 'screen-saver');
        overlay.setVisibleOnAllWorkspaces(true);
        overlay.show();
        overlay.focus();
        overlay.webContents.send('focus-input');
        // Re-enable mouse events when shown for interaction
        overlay.setIgnoreMouseEvents(false);
      }
    });
  });
  
  console.log(`Global shortcut registered: ${shortcut}`);
}

function resolvePythonExecutable() {
  // Prefer project virtualenv python if present
  const venvPython = path.join(__dirname, '..', '.venv', 'bin', 'python');
  if (process.platform !== 'win32' && fs.existsSync(venvPython)) {
    console.log(`Using virtualenv Python: ${venvPython}`);
    return venvPython;
  }
  // Fallbacks
  if (process.platform === 'win32') return 'python';
  return 'python3';
}

async function isBackendHealthy() {
  try {
    await axios.get(`${BACKEND_URL}/health`, { family: 4, timeout: 2000 });
    return true;
  } catch (e) {
    return false;
  }
}

async function startBackend() {
  const { spawn } = require('child_process');
  const backendPath = path.join(__dirname, '..', 'backend', 'main.py');

  if (await isBackendHealthy()) {
    console.log(`Backend already healthy at ${BACKEND_URL}; not spawning a new one.`);
    return;
  }

  const pythonExec = resolvePythonExecutable();
  const projectRoot = path.join(__dirname, '..');
  console.log(`Spawning backend: ${pythonExec} ${backendPath} --port ${String(BACKEND_PORT)} (cwd=${projectRoot})`);
  try {
    if (pythonExec.startsWith('/') && !fs.existsSync(pythonExec)) {
      console.error(`Python executable not found at ${pythonExec}`);
    }
    if (!fs.existsSync(backendPath)) {
      console.error(`Backend entry not found at ${backendPath}`);
    }
  } catch (e) {
    console.error('Preflight check error:', e);
  }

  let backendProcess = spawn(
    pythonExec,
    [backendPath, '--port', String(BACKEND_PORT)],
    { detached: false, cwd: projectRoot }
  );

  backendProcess.on('error', (err) => {
    console.error('Failed to spawn backend process:', err);
  });

  backendProcess.stdout.on('data', (data) => {
    console.log(`Backend: ${data}`);
  });

  backendProcess.stderr.on('data', (data) => {
    console.error(`Backend Error: ${data}`);
  });

  let exitTimer = setTimeout(() => { exitTimer = null; }, 2000);
  backendProcess.on('close', (code) => {
    console.log(`Backend process exited with code ${code}`);
    // Quick-fail fallback: try alternate executables if it died immediately
    if (exitTimer !== null) {
      const alternates = process.platform === 'win32' ? ['python'] : ['python3', 'python'];
      for (const alt of alternates) {
        if (alt === pythonExec) continue;
        console.warn(`Retrying backend spawn with alternate executable: ${alt}`);
        backendProcess = spawn(
          alt,
          [backendPath, '--port', String(BACKEND_PORT)],
          { detached: false, cwd: projectRoot }
        );
        backendProcess.on('error', (err) => {
          console.error('Failed to spawn backend process (alternate):', err);
        });
        backendProcess.stdout.on('data', (data) => console.log(`Backend: ${data}`));
        backendProcess.stderr.on('data', (data) => console.error(`Backend Error: ${data}`));
        backendProcess.on('close', (code2) => console.log(`Backend process (alternate ${alt}) exited with code ${code2}`));
        break;
      }
    }
  });

  // Cleanup on app exit
  app.on('before-quit', () => {
    try {
      if (backendProcess && !backendProcess.killed) {
        backendProcess.kill();
      }
    } catch (e) {
      console.error('Error killing backend process on quit:', e);
    }
  });

  // Poll backend health a few times and log result
  let attempts = 0;
  const maxAttempts = 10;
  const interval = setInterval(async () => {
    attempts += 1;
    const healthy = await isBackendHealthy();
    console.log(`Backend health check attempt ${attempts}/${maxAttempts}: ${healthy ? 'healthy' : 'not yet'}`);
    if (healthy || attempts >= maxAttempts) {
      clearInterval(interval);
    }
  }, 500);
}

app.whenReady().then(async () => {
  console.log('App is ready, initializing...');
  try {
    console.log('Creating main window...');
    createMainWindow();
    console.log('Creating overlay window...');
    createOverlayWindow();
    console.log('Registering global shortcuts...');
    registerGlobalShortcuts();
    console.log('Registering IPC handlers...');
    registerIpcHandlers();
    console.log('Starting backend...');
    await startBackend();
    console.log('Backend startup completed');
    
    // Wait a moment for backend to start
    setTimeout(() => {
      checkBackendHealth();
    }, 3000);
  } catch (error) {
    console.error('Error during app initialization:', error);
    console.error('Stack trace:', error.stack);
  }
}).catch((error) => {
  console.error('Failed to initialize app:', error);
  console.error('Stack trace:', error.stack);
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  // Only create windows if app is ready
  if (!app.isReady()) {
    return;
  }
  
  if (BrowserWindow.getAllWindows().length === 0) {
    createMainWindow();
    createOverlayWindow();
  } else {
    // Ensure overlay window exists
    if (!overlayWindow || overlayWindow.isDestroyed()) {
      createOverlayWindow();
    }
    // Ensure main window exists
    if (!mainWindow || mainWindow.isDestroyed()) {
      createMainWindow();
    }
  }
});

app.on('will-quit', () => {
  globalShortcut.unregisterAll();
});

// IPC handlers
ipcMain.handle('send-command', async (event, command) => {
  console.log('Received command:', command);
  
  try {
    console.log(`Sending to backend at ${BACKEND_URL}/command`);
    
    const response = await axios.post(`${BACKEND_URL}/command`, {
      command: command,
      context: store.get('context', [])
    }, {
      timeout: 30000, // 30 second timeout
      family: 4 // Force IPv4
    });
    
    console.log('Backend response status:', response.status);
    console.log('Backend response data:', response.data);
    
    // Update context
    if (response.data.context) {
      store.set('context', response.data.context);
    }
    
    const responseData = response.data;
    if (responseData.response_type === 'chat') {
      overlayWindow.webContents.send('overlay-chat-response', responseData);
    } else if (responseData.response_type === 'action') {
      overlayWindow.webContents.send('overlay-action-response', responseData);
    }
    return responseData;
  } catch (error) {
    console.error('Error sending command to backend:', error);
    
    let errorMessage = 'Failed to connect to backend service';
    let suggestion = 'Please ensure the backend service is running with: npm run backend';
    
    if (error.code === 'ECONNREFUSED') {
      errorMessage = 'Backend service is not running';
    } else if (error.code === 'ETIMEDOUT') {
      errorMessage = 'Backend service is not responding (timeout)';
      suggestion = 'The backend may be overloaded or stuck';
    } else if (error.response) {
      errorMessage = `Backend error: ${error.response.status} - ${error.response.statusText}`;
      if (error.response.data && error.response.data.error) {
        suggestion = error.response.data.error;
      }
    }
    
    return { 
      success: false, 
      error: errorMessage,
      result: suggestion
    };
  }
});

// Handle command confirmation
ipcMain.handle('send-command-confirmation', async (event, data) => {
  console.log('Received command confirmation:', data);
  
  try {
    console.log(`Sending confirmation to backend at ${BACKEND_URL}/command/confirm`);
    
    const response = await axios.post(`${BACKEND_URL}/command/confirm`, {
      cache_key: data.cache_key,
      confirmed: data.confirmed,
      original_command: data.original_command,
      context: data.context || []
    }, {
      timeout: 30000, // 30 second timeout
      family: 4 // Force IPv4
    });
    
    console.log('Backend confirmation response status:', response.status);
    console.log('Backend confirmation response data:', response.data);
    
    return response.data;
  } catch (error) {
    console.error('Error sending confirmation to backend:', error);
    
    let errorMessage = 'Failed to confirm command with backend service';
    let suggestion = 'Please ensure the backend service is running';
    
    if (error.code === 'ECONNREFUSED') {
      errorMessage = 'Backend service is not running';
    } else if (error.code === 'ETIMEDOUT') {
      errorMessage = 'Backend service is not responding (timeout)';
      suggestion = 'The backend may be overloaded or stuck';
    } else if (error.response) {
      errorMessage = `Backend error: ${error.response.status} - ${error.response.statusText}`;
      if (error.response.data && error.response.data.error) {
        suggestion = error.response.data.error;
      }
    }
    
    return { 
      success: false, 
      error: errorMessage,
      result: suggestion
    };
  }
});

ipcMain.handle('get-settings', () => {
  return store.get('settings', {
    theme: 'dark',
    autoStart: true,
    shortcuts: {
      activate: process.platform === 'darwin' ? 'Cmd+Space' : 'Ctrl+Space'
    }
  });
});

ipcMain.handle('save-settings', (event, settings) => {
  store.set('settings', settings);
  return true;
});

ipcMain.handle('clear-context', () => {
  store.set('context', []);
  return true;
});

// Handle overlay resizing
// ipcMain.on('resize-overlay', (event, height) => {
//   safeOverlayOperation((overlay) => {
//     overlay.setSize(600, height);
//   });
// });

async function checkBackendHealth() {
  try {
    await axios.get(`${BACKEND_URL}/health`, {
      family: 4 // Force IPv4
    });
    console.log('Backend is healthy');
  } catch (error) {
    console.error('Backend health check failed:', error.message);
  }
}
