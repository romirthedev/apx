// Direct overlay test to debug display issues
const { app, BrowserWindow, ipcMain } = require('electron');
const axios = require('axios');
const path = require('path');

const BACKEND_URL = 'http://localhost:8888';

app.whenReady().then(() => {
  // Create a test overlay window with dev tools
  const testWindow = new BrowserWindow({
    width: 800,
    height: 600,
    show: true,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  // Open dev tools immediately
  testWindow.webContents.openDevTools();
  
  // Load the overlay
  testWindow.loadFile(path.join(__dirname, '..', 'src', 'overlay.html'));
  
  // Add our test IPC handler
  ipcMain.handle('send-command', async (event, command) => {
    console.log('🧪 Test IPC received command:', command);
    
    try {
      const response = await axios.post(`${BACKEND_URL}/command`, {
        command: command,
        context: []
      }, {
        timeout: 10000
      });
      
      console.log('🧪 Test IPC backend response:', response.data);
      return response.data;
    } catch (error) {
      console.error('🧪 Test IPC error:', error.message);
      return {
        success: false,
        error: error.message,
        result: 'Failed to connect to backend'
      };
    }
  });

  // Handle resizing
  ipcMain.on('resize-overlay', (event, height) => {
    console.log('🧪 Test resize requested:', height);
    testWindow.setSize(800, Math.max(600, height));
  });

  // Wait for window to load, then run automatic tests
  testWindow.webContents.once('dom-ready', () => {
    console.log('🧪 Test window loaded, running automatic tests...');
    
    // Test 1: Manual test command
    setTimeout(() => {
      console.log('🧪 Simulating "test" command...');
      testWindow.webContents.executeJavaScript(`
        document.getElementById('commandInput').value = 'test';
        document.getElementById('commandInput').dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter'}));
      `);
    }, 2000);

    // Test 2: Real backend command
    setTimeout(() => {
      console.log('🧪 Simulating "help" command...');
      testWindow.webContents.executeJavaScript(`
        document.getElementById('commandInput').value = 'help';
        document.getElementById('commandInput').dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter'}));
      `);
    }, 8000);

    // Test 3: Check DOM state
    setTimeout(() => {
      console.log('🧪 Checking DOM state...');
      testWindow.webContents.executeJavaScript(`
        console.log('=== DOM DEBUG ===');
        const container = document.getElementById('resultContainer');
        const content = document.getElementById('resultContent');
        const text = document.getElementById('resultText');
        
        console.log('Result Container:', {
          display: container.style.display,
          visibility: container.style.visibility,
          opacity: container.style.opacity,
          classList: container.classList.toString(),
          offsetHeight: container.offsetHeight,
          scrollHeight: container.scrollHeight
        });
        
        console.log('Result Content:', {
          innerHTML: content.innerHTML.length,
          classList: content.classList.toString(),
          offsetHeight: content.offsetHeight
        });
        
        console.log('Result Text:', {
          innerHTML: text.innerHTML.length,
          textContent: text.textContent.length,
          innerTextPreview: text.textContent.substring(0, 100)
        });
        
        // Force show result for debugging
        container.style.display = 'block';
        container.style.visibility = 'visible';
        container.style.opacity = '1';
        container.style.height = 'auto';
        container.style.backgroundColor = 'red'; // Make it visible
        
        console.log('=== FORCED DISPLAY ===');
      `);
    }, 12000);
  });
});

app.on('window-all-closed', () => {
  app.quit();
});
