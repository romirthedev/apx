const { app, BrowserWindow, globalShortcut, ipcMain, screen, nativeImage } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const Store = require('electron-store');
const axios = require('axios');

const store = new Store();
let mainWindow;
let overlayWindow;
let appIcon = null;
let allowOverlayHide = false; // Allow manual hide when toggling via shortcut
const APP_ICON_URL = 'https://framerusercontent.com/images/NqlkhOHNTp2xhwgwT22pu4pcPk.png?scale-down-to=512&width=1024&height=788';
const BACKEND_PORT = 8888;
const BACKEND_URL = `http://localhost:${BACKEND_PORT}`;

// Ensure app naming is consistent across platforms
// Note: macOS Dock hover label is determined by bundle name when packaged.
// We still set the name, about panel options, and window titles for consistency in dev.
try {
  app.setName('Apx');
} catch (_) {}
if (process.platform === 'win32') {
  try { app.setAppUserModelId('APX'); } catch (_) {}
}
if (process.platform === 'darwin') {
  try { app.setAboutPanelOptions({ applicationName: 'Apx' }); } catch (_) {}
}

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
    icon: appIcon || undefined,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  // Set explicit window title to ensure taskbar/hover shows "Apx" where applicable
  try { mainWindow.setTitle('Apx'); } catch (_) {}

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
    fullscreenable: false,
    minimizable: false,
    maximizable: false,
    closable: false,
    acceptFirstMouse: true,
    hasShadow: false,
    type: 'panel', // Makes it a floating panel
    visualEffectState: 'inactive', // Disable vibrancy to prevent edge aliasing
    icon: appIcon || undefined,
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

  try { overlayWindow.setTitle('Apx Overlay'); } catch (_) {}

  // Allow mouse events to pass through by default
  overlayWindow.setIgnoreMouseEvents(true, { forward: true });

  // Ensure overlay stays above fullscreen/kiosk windows
  try {
    overlayWindow.setAlwaysOnTop(true, 'screen-saver');
    overlayWindow.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });
    overlayWindow.setFullScreenable(false);
  } catch (e) {
    console.warn('Failed to apply full-screen overlay safeguards:', e);
  }

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
    overlayWindow.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });
  });

  // Prevent hide/minimize/close from removing overlay; auto-restore
  overlayWindow.on('hide', () => {
    if (allowOverlayHide) {
      console.log('Overlay hide allowed by user shortcut');
      // Reset flag after accepted hide
      allowOverlayHide = false;
      return;
    }
    console.log('Overlay hide event - restoring overlay');
    try {
      overlayWindow.showInactive();
      overlayWindow.setAlwaysOnTop(true, 'screen-saver');
      overlayWindow.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });
    } catch (e) {
      console.warn('Failed to restore overlay after hide:', e);
    }
  });

  overlayWindow.on('minimize', () => {
    console.log('Overlay minimize event - restoring overlay');
    try {
      overlayWindow.restore();
      overlayWindow.showInactive();
      overlayWindow.setAlwaysOnTop(true, 'screen-saver');
      overlayWindow.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });
    } catch (e) {
      console.warn('Failed to restore overlay after minimize:', e);
    }
  });

  overlayWindow.on('close', (e) => {
    console.log('Overlay close attempted - preventing and hiding instead');
    e.preventDefault();
    try {
      overlayWindow.hide();
    } catch (_) {}
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

  // IPC handler to move overlay window
  ipcMain.on('move-overlay-window', (event, direction) => {
    safeOverlayOperation((overlay) => {
      const [currentX, currentY] = overlay.getPosition();
      const step = 20;
      let newX = currentX;
      let newY = currentY;
      
      switch (direction) {
        case 'up':
          newY = Math.max(0, currentY - step);
          break;
        case 'down':
          newY = Math.min(screen.getPrimaryDisplay().workAreaSize.height - 100, currentY + step);
          break;
        case 'left':
          newX = Math.max(0, currentX - step);
          break;
        case 'right':
          newX = Math.min(screen.getPrimaryDisplay().workAreaSize.width - overlay.getBounds().width, currentX + step);
          break;
      }
      
      overlay.setPosition(newX, newY);
      console.log(`🎯 Moved overlay window: x=${newX}, y=${newY}`);
    });
  });

  // IPC handler for enhanced web search
  ipcMain.handle('enhanced-web-search', async (event, query) => {
    return new Promise((resolve) => {
      const pythonExecutable = resolvePythonExecutable();
      const scriptPath = path.join(__dirname, '..', 'backend', 'generated_capabilities', 'enhanced_web_search_automation.py');
      const process = spawn(pythonExecutable, [scriptPath, query]);

      let output = '';
      let errorOutput = '';

      process.stdout.on('data', (data) => {
        output += data.toString();
      });

      process.stderr.on('data', (data) => {
        errorOutput += data.toString();
      });

      process.on('close', (code) => {
        if (code === 0) {
          const lines = output.trim().split('\n');
          const resultLine = lines.find(line => line.startsWith('SUCCESS:'));
          
          if (resultLine) {
            const [, success, title, url, type] = resultLine.split(':');
            resolve({
              success: success === 'True',
              title: title || 'Search Result',
              opened_url: url || '',
              query_type: type || 'general'
            });
          } else {
            resolve({
              success: false,
              error: 'No valid result found'
            });
          }
        } else {
          console.error('Enhanced web search error:', errorOutput);
          resolve({
            success: false,
            error: errorOutput || 'Search process failed'
          });
        }
      });
      
      process.on('error', (error) => {
        console.error('Enhanced web search process error:', error);
        resolve({
          success: false,
          error: error.message
        });
      });
    });
  });
  
  // IPC handler for screen capture
  ipcMain.handle('capture-screen', async () => {
    try {
      const { desktopCapturer, nativeImage } = require('electron');
      const os = require('os');
      
      // Get screen sources
      const sources = await desktopCapturer.getSources({ 
        types: ['screen'],
        thumbnailSize: { width: 1920, height: 1080 }
      });
      
      if (sources.length === 0) {
        return { success: false, error: 'No screen sources found' };
      }
      
      // Get the primary screen source
      const primarySource = sources[0];
      const image = primarySource.thumbnail;
      
      // Create a temporary file path
      const timestamp = Date.now();
      const imagePath = path.join(os.tmpdir(), `screenshot_${timestamp}.png`);
      
      // Save the image to file
      const buffer = image.toPNG();
      fs.writeFileSync(imagePath, buffer);
      
      console.log(`Screenshot saved to: ${imagePath}`);
      
      return { 
        success: true, 
        imagePath: imagePath,
        source: primarySource.id 
      };
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
        // Allow manual hide
        allowOverlayHide = true;
        overlay.hide();
        // Return to passthrough while hidden
        try { overlay.setIgnoreMouseEvents(true, { forward: true }); } catch (_) {}
        // Safety reset in case 'hide' event doesn't fire
        setTimeout(() => { allowOverlayHide = false; }, 1500);
      } else {
        // Ensure the overlay is always on top and focused when shown
        overlay.setAlwaysOnTop(true, 'screen-saver');
        overlay.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });
        try { overlay.show(); } catch (_) { overlay.showInactive(); }
        try { overlay.focus(); } catch (_) { /* focus may be blocked by lockdown */ }
        overlay.webContents.send('focus-input');
        // Re-enable mouse events when shown for interaction
        overlay.setIgnoreMouseEvents(false);
      }
    });
  });
  
  // Register Cmd+R shortcut for context refresh
  const refreshShortcut = process.platform === 'darwin' ? 'Cmd+R' : 'Ctrl+R';
  
  globalShortcut.register(refreshShortcut, () => {
    console.log('🔄 Context refresh triggered via Cmd+R');
    // Clear local context storage
    store.set('context', []);
    
    // Notify backend to refresh context
    axios.post(`${BACKEND_URL}/refresh_context`, {}, {
      timeout: 5000,
      family: 4
    }).then(() => {
      console.log('✅ Context refreshed successfully');
      // Notify overlay about context refresh
      safeOverlayOperation((overlay) => {
        overlay.webContents.send('context-refreshed');
      });
    }).catch((error) => {
      console.error('❌ Error refreshing context:', error);
    });
  });
  
  console.log(`Global shortcuts registered: ${shortcut}, ${refreshShortcut}`);

  // Register a global shortcut for screenshot capture (works without overlay focus)
  const captureShortcut = process.platform === 'darwin' ? 'Cmd+Shift+C' : 'Ctrl+Shift+C';
  globalShortcut.register(captureShortcut, async () => {
    console.log('📸 Global screenshot capture triggered');
    try {
      const response = await axios.post(`${BACKEND_URL}/capture_screenshot`, {}, {
        timeout: 30000,
        family: 4
      });
      const data = response.data || {};
      safeOverlayOperation((overlay) => {
        overlay.setAlwaysOnTop(true, 'screen-saver');
        overlay.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });
        try { overlay.showInactive(); } catch (_) { overlay.show(); }
        overlay.webContents.send('overlay-screenshot-result', {
          success: !!data.success,
          text: data.text || '',
          error: data.error || null
        });
      });
    } catch (error) {
      console.error('Error during global screenshot capture:', error);
      safeOverlayOperation((overlay) => {
        overlay.webContents.send('overlay-screenshot-result', {
          success: false,
          text: '',
          error: error.message
        });
      });
    }
  });
  console.log(`Screenshot capture shortcut registered: ${captureShortcut}`);
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

async function loadAppIcon() {
  try {
    const response = await axios.get(APP_ICON_URL, { responseType: 'arraybuffer' });
    const buffer = Buffer.from(response.data);
    const image = nativeImage.createFromBuffer(buffer);
    if (image && !image.isEmpty()) {
      // Normalize to a centered square to avoid stretching in Dock/taskbar
      const { width, height } = image.getSize();
      let squareImage = image;
      if (width !== height) {
        const side = Math.min(width, height);
        const x = Math.max(0, Math.floor((width - side) / 2));
        const y = Math.max(0, Math.floor((height - side) / 2));
        squareImage = image.crop({ x, y, width: side, height: side });
      }
      // Resize to a standard icon size for consistency
      appIcon = squareImage.resize({ width: 512, quality: 'best' });
      if (process.platform === 'darwin' && app.dock) {
        try {
          app.dock.setIcon(appIcon);
          console.log('✅ Dock icon set from remote URL');
        } catch (e) {
          console.warn('⚠️ Failed to set Dock icon:', e.message);
        }
      }
    } else {
      console.warn('⚠️ Loaded app icon is empty or invalid');
    }
  } catch (error) {
    console.warn('⚠️ Failed to load app icon from URL:', error.message);
  }
}

app.whenReady().then(async () => {
  console.log('App is ready, initializing...');
  try {
    // Load remote app icon before creating windows so they inherit it
    await loadAppIcon();
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
ipcMain.handle('send-command', async (event, payload) => {
  const command = (typeof payload === 'string') ? payload : (payload && payload.command);
  const preferences = (payload && typeof payload === 'object') ? (payload.preferences || null) : null;
  console.log('Received command:', command);
  if (preferences) {
    console.log('Received preferences:', preferences);
  }
  
  try {
    console.log(`Sending to backend at ${BACKEND_URL}/command`);
    
    const response = await axios.post(`${BACKEND_URL}/command`, {
      command: command,
      context: store.get('context', []),
      preferences: preferences || undefined
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
    
    // Log the response for debugging
    console.log('Returning response to overlay:', {
      success: responseData.success,
      result: responseData.result ? responseData.result.substring(0, 100) + '...' : 'No result',
      response_type: responseData.response_type,
      is_ai_response: responseData.is_ai_response
    });
    
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

// Voice control: initialize voice system via backend
ipcMain.handle('voice-init', async () => {
  try {
    const url = `${BACKEND_URL}/api/voice/init`;
    const response = await axios.post(url, {}, { timeout: 30000, family: 4 });
    return response.data;
  } catch (error) {
    let msg = 'Failed to initialize voice system';
    if (error.code === 'ECONNREFUSED') msg = 'Backend service is not running';
    else if (error.code === 'ETIMEDOUT') msg = 'Backend service timed out during voice init';
    else if (error.response) msg = `Backend error: ${error.response.status} ${error.response.statusText}`;
    return { success: false, error: msg };
  }
});

// Voice control: start listening via backend
ipcMain.handle('voice-start', async () => {
  try {
    const url = `${BACKEND_URL}/api/voice/start`;
    const response = await axios.post(url, {}, { timeout: 30000, family: 4 });
    return response.data;
  } catch (error) {
    let msg = 'Failed to start voice listening';
    if (error.code === 'ECONNREFUSED') msg = 'Backend service is not running';
    else if (error.code === 'ETIMEDOUT') msg = 'Backend service timed out during voice start';
    else if (error.response) msg = `Backend error: ${error.response.status} ${error.response.statusText}`;
    return { success: false, error: msg };
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

// Provide backend URL to overlay via IPC so it can align ports reliably
ipcMain.handle('get-backend-url', () => {
  try {
    return BACKEND_URL;
  } catch (e) {
    console.error('Error retrieving BACKEND_URL:', e);
    return null;
  }
});

// Ensure backend is running and healthy; start if needed and wait briefly
ipcMain.handle('ensure-backend', async () => {
  try {
    await startBackend();
    // Poll health up to ~10 seconds
    let attempts = 0;
    const maxAttempts = 20;
    while (attempts < maxAttempts) {
      attempts += 1;
      const healthy = await isBackendHealthy();
      if (healthy) {
        return { success: true, url: BACKEND_URL };
      }
      await new Promise(res => setTimeout(res, 500));
    }
    return { success: false, error: 'Backend not healthy after retries' };
  } catch (e) {
    console.error('ensure-backend error:', e);
    return { success: false, error: e?.message || 'Unknown error' };
  }
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
