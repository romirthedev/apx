"""
Enhanced macOS System Controller
Provides full OS-level control using AppleScript and Accessibility APIs
"""

import subprocess
import os
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)

class MacOSSystemController:
    def __init__(self):
        self.platform = "darwin"
    
    def execute_applescript(self, script: str) -> Tuple[bool, str]:
        """Execute AppleScript and return success status and output."""
        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            success = result.returncode == 0
            output = result.stdout.strip() if success else result.stderr.strip()
            
            return success, output
            
        except subprocess.TimeoutExpired:
            return False, "Script execution timed out"
        except Exception as e:
            return False, f"Script execution failed: {str(e)}"
    
    def click_at_coordinates(self, x: int, y: int) -> str:
        """Click at specific screen coordinates."""
        try:
            script = f'''
            tell application "System Events"
                click at {{{x}, {y}}}
            end tell
            '''
            
            success, output = self.execute_applescript(script)
            
            if success:
                return f"✅ Clicked at coordinates ({x}, {y})"
            else:
                return f"❌ Failed to click: {output}"
                
        except Exception as e:
            return f"❌ Click failed: {str(e)}"
    
    def type_text(self, text: str) -> str:
        """Type text using system events."""
        try:
            # Escape special characters for AppleScript
            escaped_text = text.replace('"', '\\"').replace('\\', '\\\\')
            
            script = f'''
            tell application "System Events"
                keystroke "{escaped_text}"
            end tell
            '''
            
            success, output = self.execute_applescript(script)
            
            if success:
                return f"✅ Typed text: {text[:50]}..."
            else:
                return f"❌ Failed to type text: {output}"
                
        except Exception as e:
            return f"❌ Text input failed: {str(e)}"
    
    def press_key_combination(self, keys: List[str]) -> str:
        """Press key combination (e.g., ['command', 'c'] for Cmd+C)."""
        try:
            # Map common key names
            key_mapping = {
                'cmd': 'command',
                'ctrl': 'control',
                'alt': 'option',
                'shift': 'shift',
                'space': 'space',
                'enter': 'return',
                'tab': 'tab',
                'esc': 'escape'
            }
            
            # Convert keys to AppleScript format
            applescript_keys = []
            for key in keys:
                mapped_key = key_mapping.get(key.lower(), key.lower())
                applescript_keys.append(mapped_key)
            
            if len(applescript_keys) == 1:
                script = f'''
                tell application "System Events"
                    key code (ASCII number "{applescript_keys[0]}")
                end tell
                '''
            else:
                modifiers = applescript_keys[:-1]
                main_key = applescript_keys[-1]
                modifier_str = ' down, '.join(modifiers) + ' down'
                
                script = f'''
                tell application "System Events"
                    keystroke "{main_key}" using {{{modifier_str}}}
                end tell
                '''
            
            success, output = self.execute_applescript(script)
            
            if success:
                return f"✅ Pressed key combination: {'+'.join(keys)}"
            else:
                return f"❌ Failed to press keys: {output}"
                
        except Exception as e:
            return f"❌ Key press failed: {str(e)}"
    
    def get_window_info(self, app_name: str = "") -> str:
        """Get information about windows for specified app or all apps."""
        try:
            if app_name:
                script = f'''
                tell application "System Events"
                    tell application process "{app_name}"
                        set windowList to ""
                        repeat with w in windows
                            set windowList to windowList & (name of w) & "\\n"
                        end repeat
                        return windowList
                    end tell
                end tell
                '''
            else:
                script = '''
                tell application "System Events"
                    set windowList to ""
                    repeat with proc in application processes
                        if visible of proc is true then
                            set procName to name of proc
                            repeat with w in windows of proc
                                set windowList to windowList & procName & ": " & (name of w) & "\\n"
                            end repeat
                        end if
                    end repeat
                    return windowList
                end tell
                '''
            
            success, output = self.execute_applescript(script)
            
            if success:
                if output:
                    return f"🪟 Window information:\\n{output}"
                else:
                    return "🪟 No windows found"
            else:
                return f"❌ Failed to get window info: {output}"
                
        except Exception as e:
            return f"❌ Window info failed: {str(e)}"
    
    def control_window(self, app_name: str, action: str, window_name: str = "") -> str:
        """Control windows (minimize, maximize, close, focus)."""
        try:
            if window_name:
                target = f'window "{window_name}" of application process "{app_name}"'
            else:
                target = f'front window of application process "{app_name}"'
            
            if action.lower() == "minimize":
                script = f'''
                tell application "System Events"
                    tell {target}
                        click button 2
                    end tell
                end tell
                '''
            elif action.lower() == "maximize":
                script = f'''
                tell application "System Events"
                    tell {target}
                        click button 3
                    end tell
                end tell
                '''
            elif action.lower() == "close":
                script = f'''
                tell application "System Events"
                    tell {target}
                        click button 1
                    end tell
                end tell
                '''
            elif action.lower() == "focus":
                script = f'''
                tell application "{app_name}" to activate
                tell application "System Events"
                    tell {target}
                        perform action "AXRaise"
                    end tell
                end tell
                '''
            else:
                return f"❌ Unknown window action: {action}"
            
            success, output = self.execute_applescript(script)
            
            if success:
                return f"✅ {action.title()}d window for {app_name}"
            else:
                return f"❌ Failed to {action} window: {output}"
                
        except Exception as e:
            return f"❌ Window control failed: {str(e)}"
    
    def take_screenshot(self, filename: str = "", region: Tuple[int, int, int, int] = None) -> str:
        """Take a screenshot of the screen or a specific region."""
        try:
            if not filename:
                timestamp = int(time.time())
                filename = f"screenshot_{timestamp}.png"
            
            # Ensure .png extension
            if not filename.endswith('.png'):
                filename += '.png'
            
            # Full path
            full_path = os.path.expanduser(f"~/Desktop/{filename}")
            
            # Build screencapture command
            cmd = ['screencapture']
            
            if region:
                x, y, width, height = region
                cmd.extend(['-R', f"{x},{y},{width},{height}"])
            
            cmd.append(full_path)
            
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            
            if result.returncode == 0:
                return f"✅ Screenshot saved: {filename}"
            else:
                return f"❌ Screenshot failed: {result.stderr.decode()}"
                
        except Exception as e:
            return f"❌ Screenshot failed: {str(e)}"
    
    def read_screen_text(self, region: Tuple[int, int, int, int] = None, timeout: int = 25) -> str:
        """Read text from screen using OCR with proper timeout handling."""
        import threading
        import tempfile
        
        try:
            # Use temp directory instead of Desktop
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                temp_screenshot_path = temp_file.name
            
            # Take screenshot with timeout
            screenshot_result = self.take_screenshot(os.path.basename(temp_screenshot_path), region)
            
            if "failed" in screenshot_result.lower():
                return screenshot_result
            
            # Move file to temp location
            desktop_path = os.path.expanduser(f"~/Desktop/{os.path.basename(temp_screenshot_path)}")
            if os.path.exists(desktop_path):
                os.rename(desktop_path, temp_screenshot_path)
            
            # Perform OCR with timeout
            result = {'text': None, 'error': None, 'completed': False}
            
            def ocr_worker():
                try:
                    img = Image.open(temp_screenshot_path)
                    
                    # Optimize image for OCR
                    if img.mode != 'L':
                        img = img.convert('L')
                    
                    # Use optimized Tesseract config (fixed quotation issue)
                    config = r'--oem 3 --psm 6'
                    text = pytesseract.image_to_string(img, config=config)
                    
                    result['text'] = text
                    result['completed'] = True
                except Exception as e:
                    result['error'] = str(e)
                    result['completed'] = True
            
            # Run OCR in thread with timeout
            thread = threading.Thread(target=ocr_worker)
            thread.daemon = True
            thread.start()
            thread.join(timeout=timeout)
            
            if not thread.is_alive() and result['completed']:
                if result['error']:
                    if 'TesseractNotFoundError' in str(result['error']):
                        return "❌ Tesseract is not installed or not in your PATH. Please install it to use OCR functionality."
                    else:
                        return f"❌ OCR processing failed: {result['error']}"
                else:
                    text = result['text']
                    if text and text.strip():
                        return f"📖 Extracted text:\n{text}"
                    else:
                        return "📖 No text found in the specified region."
            else:
                return f"❌ OCR timed out after {timeout} seconds. Try with a smaller region or simpler image."
                
        except Exception as e:
            return f"❌ Screen reading failed: {str(e)}"
        finally:
            # Clean up temp file
            if 'temp_screenshot_path' in locals() and os.path.exists(temp_screenshot_path):
                try:
                    os.remove(temp_screenshot_path)
                except:
                    pass
    
    def execute_shell_command(self, command: str, safe_mode: bool = True) -> str:
        """Execute shell command with safety checks."""
        try:
            # Safety checks
            if safe_mode:
                dangerous_commands = [
                    'rm -rf /', 'sudo rm', 'format', 'del /f', 'rmdir /s',
                    'kill -9', 'sudo shutdown', 'sudo reboot'
                ]
                
                if any(dangerous in command.lower() for dangerous in dangerous_commands):
                    return "❌ Dangerous command blocked for safety"
            
            # Execute command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                return f"✅ Command executed:\\n{output}" if output else "✅ Command executed successfully"
            else:
                return f"❌ Command failed: {result.stderr.strip()}"
                
        except subprocess.TimeoutExpired:
            return "❌ Command timed out"
        except Exception as e:
            return f"❌ Command execution failed: {str(e)}"
    
    def automate_workflow(self, steps: List[Dict[str, Any]]) -> str:
        """Execute a series of automation steps."""
        try:
            results = []
            
            for i, step in enumerate(steps, 1):
                step_type = step.get('type', '')
                step_data = step.get('data', {})
                
                result = f"Step {i}: "
                
                if step_type == 'click':
                    x, y = step_data.get('x', 0), step_data.get('y', 0)
                    result += self.click_at_coordinates(x, y)
                    
                elif step_type == 'type':
                    text = step_data.get('text', '')
                    result += self.type_text(text)
                    
                elif step_type == 'key':
                    keys = step_data.get('keys', [])
                    result += self.press_key_combination(keys)
                    
                elif step_type == 'wait':
                    duration = step_data.get('seconds', 1)
                    time.sleep(duration)
                    result += f"✅ Waited {duration} seconds"
                    
                elif step_type == 'app':
                    app_name = step_data.get('name', '')
                    action = step_data.get('action', 'activate')
                    
                    script = f'tell application "{app_name}" to {action}'
                    success, output = self.execute_applescript(script)
                    
                    if success:
                        result += f"✅ {action.title()}d {app_name}"
                    else:
                        result += f"❌ Failed to {action} {app_name}: {output}"
                
                else:
                    result += f"❌ Unknown step type: {step_type}"
                
                results.append(result)
                
                # Add delay between steps
                if 'delay' in step:
                    time.sleep(step['delay'])
                else:
                    time.sleep(0.5)  # Default delay
            
            return "🤖 Workflow completed:\\n" + "\\n".join(results)
            
        except Exception as e:
            return f"❌ Workflow execution failed: {str(e)}"
