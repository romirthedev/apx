# Cluely Overlay Debugging Guide

## 🔍 **Testing the Overlay Response Display**

I've added debugging features to help identify the overlay display issue:

### **Quick Tests**

1. **Test Basic Overlay Display**:
   ```bash
   electron scripts/test-overlay.js
   ```
   This should show a test window with example responses.

2. **Test Command Input with Debug**:
   - Start: `npm run electron-dev`
   - Press `Cmd+Space` to open overlay
   - Type: `test` and press Enter
   - This should show a test response without hitting the backend

3. **Test Backend Connection**:
   ```bash
   npm run test-backend
   ```

### **Debug Console Messages**

With the enhanced logging, you should see these console messages:

```
Processing command: [your command]
Sending command to backend...
Backend response: [response object]
Processing successful response...
Response details: [length, isAiResponse, method]
showResult called: [text preview, type, isAiResponse]
Result container display: block
Result container visibility: visible
```

### **Common Issues & Fixes**

#### **Issue 1: Result Container Not Showing**
- **Check**: Open Electron dev tools (View → Developer → Developer Tools)
- **Look for**: Console errors or warnings
- **Fix**: Try the `test` command first

#### **Issue 2: Overlay Closes Too Fast**
- **Check**: Auto-hide timeout (10s for AI, 5s for regular)
- **Fix**: Responses now stay longer, and overlay won't close immediately

#### **Issue 3: Backend Not Responding**
- **Check**: `curl http://localhost:8888/health`
- **Fix**: Restart with `npm run backend`

#### **Issue 4: Styling Issues**
- **Check**: Result containers should have colored borders
- **Fix**: Enhanced CSS with forced visibility

### **Manual Testing Steps**

1. **Start both services**:
   ```bash
   # Terminal 1
   npm run backend
   
   # Terminal 2  
   npm run electron-dev
   ```

2. **Test simple command**:
   - Press `Cmd+Space`
   - Type: `test`
   - Should see green test response

3. **Test AI command**:
   - Press `Cmd+Space`
   - Type: `What do you think about technology?`
   - Should see purple AI response with 🤖 icon

4. **Test rule-based command**:
   - Press `Cmd+Space`
   - Type: `help`
   - Should see green response with help menu

### **Expected Behavior**

✅ **Working Correctly**:
- Overlay opens with `Cmd+Space`
- Input field is focused and ready
- Typing `test` shows immediate response
- AI commands show purple responses with typing effect
- Console shows detailed debug logs
- Responses stay visible for 5-10 seconds

❌ **Still Broken**:
- No response visible after pressing Enter
- Overlay closes immediately
- Console shows errors
- Backend responses but overlay doesn't update

### **Next Steps**

If the issue persists after these fixes:

1. **Check the console**: Look for JavaScript errors
2. **Try the test command**: See if basic display works
3. **Verify window resizing**: Check if overlay grows when showing results
4. **Test backend directly**: Use `npm run test-backend`

The enhanced debugging should help pinpoint exactly where the display is failing!
