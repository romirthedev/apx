const { app, BrowserWindow, globalShortcut, ipcMain, screen } = require('electron');
const path = require('path');
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

  mainWindow.loadFile('src/main.html');
  
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
    width: width,
    height: height,
    x: 0,
    y: 0,
    frame: false,
    alwaysOnTop: true,
    skipTaskbar: true,
    resizable: false,
    transparent: true,
    show: false,
    focusable: true,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      backgroundThrottling: false
    }
  });

  overlayWindow.loadFile('src/overlay-oa.html');
  
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
  
  // Overlay no longer auto-hides on blur - stays visible for user
  overlayWindow.on('blur', () => {
    console.log('Overlay blur event - overlay will remain visible');
    // Removed auto-hide behavior - overlay stays on screen
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

function registerGlobalShortcuts() {
  // Register global shortcut for activation
  const shortcut = process.platform === 'darwin' ? 'Cmd+Space' : 'Ctrl+Space';
  
  globalShortcut.register(shortcut, () => {
    safeOverlayOperation((overlay) => {
      if (overlay.isVisible()) {
        overlay.hide();
      } else {
        overlay.show();
        overlay.focus();
        overlay.webContents.send('focus-input');
      }
    });
  });
  
  console.log(`Global shortcut registered: ${shortcut}`);
}

function startBackend() {
  const { spawn } = require('child_process');
  const backendPath = path.join(__dirname, '..', 'backend', 'main.py');
  
  let backendProcess;
  
  if (process.platform === 'win32') {
    backendProcess = spawn('python', [backendPath], { detached: false });
  } else {
    backendProcess = spawn('python3', [backendPath], { detached: false });
  }
  
  backendProcess.stdout.on('data', (data) => {
    console.log(`Backend: ${data}`);
  });
  
  backendProcess.stderr.on('data', (data) => {
    console.error(`Backend Error: ${data}`);
  });
  
  backendProcess.on('close', (code) => {
    console.log(`Backend process exited with code ${code}`);
  });
  
  // Cleanup on app exit
  app.on('before-quit', () => {
    if (backendProcess) {
      backendProcess.kill();
    }
  });
}

app.whenReady().then(() => {
  try {
    createMainWindow();
    createOverlayWindow();
    registerGlobalShortcuts();
    startBackend();
    
    // Wait a moment for backend to start
    setTimeout(() => {
      checkBackendHealth();
    }, 3000);
  } catch (error) {
    console.error('Error during app initialization:', error);
  }
}).catch((error) => {
  console.error('Failed to initialize app:', error);
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
    
    return response.data;
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
ipcMain.on('resize-overlay', (event, height) => {
  safeOverlayOperation((overlay) => {
    overlay.setSize(600, height);
  });
});

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
