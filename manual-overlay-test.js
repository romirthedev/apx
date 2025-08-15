// Test script to trigger overlay manually
// This simulates pressing Cmd+Space and sending a test command

const { app, BrowserWindow, ipcMain } = require('electron');

// Simulate overlay activation
setTimeout(() => {
  console.log('=== MANUAL OVERLAY TEST ===');
  console.log('Simulating Cmd+Space shortcut...');
  
  // Get the overlay window (should be created by main.js)
  const allWindows = BrowserWindow.getAllWindows();
  console.log('Available windows:', allWindows.length);
  
  const overlayWindow = allWindows.find(win => win.getTitle() === 'Cluely AI Assistant');
  
  if (overlayWindow) {
    console.log('✅ Found overlay window');
    
    // Show and focus the overlay
    overlayWindow.show();
    overlayWindow.focus();
    overlayWindow.webContents.send('focus-input');
    
    console.log('📱 Overlay should now be visible');
    console.log('Try typing "test" in the input field and pressing Enter');
    
    // Also test the IPC call directly
    setTimeout(() => {
      console.log('🧪 Testing IPC call directly...');
      
      // Simulate the send-command IPC call
      const mockEvent = { reply: (channel, data) => console.log('Reply:', channel, data) };
      
      // This should trigger the same code path as the overlay
      ipcMain.emit('handle', mockEvent, 'send-command', 'test command');
      
    }, 2000);
    
  } else {
    console.log('❌ Overlay window not found');
    console.log('Available windows:', allWindows.map(w => w.getTitle()));
  }
  
}, 3000);

console.log('Manual overlay test script loaded. Waiting 3 seconds...');
