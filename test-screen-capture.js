const { ipcRenderer } = require('electron');

// Test screen capture functionality
async function testScreenCapture() {
    console.log('Testing screen capture functionality...');
    
    try {
        // Test the capture-and-ocr IPC handler
        const result = await ipcRenderer.invoke('capture-and-ocr');
        console.log('Screen capture result:', result);
        
        if (result && result.success) {
            console.log('✅ Screen capture with OCR successful!');
            console.log('OCR Text:', result.text);
        } else {
            console.log('❌ Screen capture failed:', result);
        }
    } catch (error) {
        console.error('❌ Error during screen capture test:', error);
    }
}

// Test when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', testScreenCapture);
} else {
    testScreenCapture();
}

console.log('Screen capture test script loaded');