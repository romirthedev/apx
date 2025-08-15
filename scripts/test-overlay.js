#!/usr/bin/env node

const { app, BrowserWindow } = require('electron');
const path = require('path');

// Simple test overlay to debug display issues
function createTestOverlay() {
  const testWindow = new BrowserWindow({
    width: 600,
    height: 400,
    frame: false,
    alwaysOnTop: true,
    transparent: true,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  const testHTML = `
<!DOCTYPE html>
<html>
<head>
    <style>
        body { 
            margin: 0; 
            background: rgba(30, 30, 30, 0.95); 
            color: white; 
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            padding: 20px;
        }
        .test-result {
            background: rgba(76, 175, 80, 0.2);
            border-left: 3px solid #4caf50;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
        }
        .test-ai {
            background: rgba(156, 39, 176, 0.2);
            border-left: 3px solid #9c27b0;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
        }
        .test-ai::before {
            content: "🤖 AI Response";
            display: block;
            font-size: 12px;
            color: #9c27b0;
            font-weight: bold;
            margin-bottom: 8px;
        }
    </style>
</head>
<body>
    <h2>🧪 Cluely Overlay Test</h2>
    
    <div class="test-result">
        <strong>✅ Regular Response Test</strong><br>
        This is how a regular response should look. Green border, clean text.
    </div>
    
    <div class="test-ai">
        <strong>AI Response Test</strong><br>
        This is how an AI response should look. Purple border with robot icon.
        This text should be clearly visible and well-formatted.
    </div>
    
    <p><strong>Instructions:</strong></p>
    <ul>
        <li>If you can see this clearly, the overlay rendering works</li>
        <li>Both response boxes should be clearly visible</li>
        <li>Press Escape to close this test window</li>
    </ul>
    
    <script>
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                window.close();
            }
        });
        
        // Auto-close after 10 seconds
        setTimeout(() => {
            window.close();
        }, 10000);
    </script>
</body>
</html>
  `;

  testWindow.loadURL('data:text/html;charset=utf-8,' + encodeURIComponent(testHTML));
  
  testWindow.on('closed', () => {
    app.quit();
  });
}

app.whenReady().then(createTestOverlay);

app.on('window-all-closed', () => {
  app.quit();
});
