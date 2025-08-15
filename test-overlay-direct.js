const { app, BrowserWindow, ipcMain } = require('electron');

app.whenReady().then(() => {
  const testWindow = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  testWindow.loadFile('src/overlay-oa.html');
  testWindow.webContents.openDevTools();
  
  console.log('Test overlay window created');
  
  // Simulate a test command after 2 seconds
  setTimeout(() => {
    console.log('Sending test command to overlay');
    testWindow.webContents.send('process-command', 'test command');
  }, 2000);
});

app.on('window-all-closed', () => {
  app.quit();
});
