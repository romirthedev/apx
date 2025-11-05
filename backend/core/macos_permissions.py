"""
macOS Permissions and Security Manager
Handles Full Disk Access, Accessibility, and Screen Recording permissions
"""

import os
import subprocess
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class MacOSPermissionsManager:
    def __init__(self):
        self.required_permissions = {
            'full_disk_access': False,
            'accessibility': False,
            'screen_recording': False,
            'automation': False
        }
    
    def check_all_permissions(self) -> Dict[str, Any]:
        """Check all required macOS permissions."""
        try:
            results = {
                'all_granted': True,
                'permissions': {},
                'missing': [],
                'instructions': []
            }
            
            # Check Full Disk Access
            fda_status = self._check_full_disk_access()
            results['permissions']['full_disk_access'] = fda_status
            if not fda_status:
                results['all_granted'] = False
                results['missing'].append('Full Disk Access')
                results['instructions'].append(
                    "1. Open System Settings → Privacy & Security → Full Disk Access"
                    "2. Click the '+' button and add Apex"
                )
            
            # Check Accessibility
            accessibility_status = self._check_accessibility()
            results['permissions']['accessibility'] = accessibility_status
            if not accessibility_status:
                results['all_granted'] = False
                results['missing'].append('Accessibility')
                results['instructions'].append(
                    "1. Open System Settings → Privacy & Security → Accessibility"
                    "2. Click the '+' button and add Apex"
                )
            
            # Check Screen Recording
            screen_recording_status = self._check_screen_recording()
            results['permissions']['screen_recording'] = screen_recording_status
            if not screen_recording_status:
                results['all_granted'] = False
                results['missing'].append('Screen Recording')
                results['instructions'].append(
                    "1. Open System Settings → Privacy & Security → Screen Recording"
                    "2. Check the box next to Apex"
                )
            
            # Check Automation
            automation_status = self._check_automation()
            results['permissions']['automation'] = automation_status
            if not automation_status:
                results['all_granted'] = False
                results['missing'].append('Automation')
                results['instructions'].append(
                    "1. Open System Settings → Privacy & Security → Automation"
                    "2. Allow Apex to control other applications"
                )
            
            return results
            
        except Exception as e:
            logger.error(f"Error checking permissions: {str(e)}")
            return {
                'all_granted': False,
                'error': str(e),
                'permissions': {},
                'missing': ['Unknown'],
                'instructions': ['Unable to check permissions. Please check manually.']
            }
    
    def _check_full_disk_access(self) -> bool:
        """Check if app has Full Disk Access."""
        try:
            # Try to read a protected file that requires Full Disk Access
            protected_paths = [
                os.path.expanduser("~/Library/Safari/History.db"),
                os.path.expanduser("~/Library/Mail"),
                "/Library/Application Support"
            ]
            
            for path in protected_paths:
                if os.path.exists(path):
                    try:
                        # Try to list contents or read file
                        if os.path.isdir(path):
                            os.listdir(path)
                        else:
                            with open(path, 'r') as f:
                                f.read(1)
                        return True
                    except PermissionError:
                        continue
            
            return False
            
        except Exception:
            return False
    
    def _check_accessibility(self) -> bool:
        """Check if app has Accessibility permissions."""
        try:
            # Try to use AppleScript to test accessibility
            script = '''
            tell application "System Events"
                try
                    get name of first process
                    return "true"
                on error
                    return "false"
                end try
            end tell
            '''
            
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            return result.stdout.strip() == "true"
            
        except Exception:
            return False
    
    def _check_screen_recording(self) -> bool:
        """Check if app has Screen Recording permissions."""
        try:
            # Try to take a screenshot
            result = subprocess.run(
                ['screencapture', '-t', 'png', '/tmp/apex_test_screenshot.png'],
                capture_output=True,
                timeout=5
            )
            
            # Clean up test file
            try:
                os.remove('/tmp/apex_test_screenshot.png')
            except:
                pass
            
            return result.returncode == 0
            
        except Exception:
            return False
    
    def _check_automation(self) -> bool:
        """Check if app has Automation permissions."""
        try:
            # Try to control another application
            script = '''
            tell application "Finder"
                try
                    get name
                    return "true"
                on error
                    return "false"
                end try
            end tell
            '''
            
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            return result.stdout.strip() == "true"
            
        except Exception:
            return False
    
    def request_permissions(self) -> str:
        """Guide user through requesting necessary permissions."""
        try:
            check_result = self.check_all_permissions()
            
            if check_result['all_granted']:
                return "✅ All required permissions are already granted!"
            
            instructions = [
                "🔐 APEX REQUIRES SYSTEM PERMISSIONS",
                "=" * 50,
                "",
                "For full computer control, Apex needs these macOS permissions:",
                ""
            ]
            
            for i, instruction in enumerate(check_result['instructions'], 1):
                instructions.append(f"{i}. {instruction}")
                instructions.append("")
            
            instructions.extend([
                "⚠️  IMPORTANT SECURITY NOTES:",
                "• These permissions give Apex full control over your Mac",
                "• All actions are logged for security",
                "• You can revoke permissions anytime in System Settings",
                "• Apex uses AI to understand commands safely",
                "",
                "🔄 After granting permissions, restart Apex for changes to take effect."
            ])
            
            return "\\n".join(instructions)
            
        except Exception as e:
            logger.error(f"Error generating permission instructions: {str(e)}")
            return f"❌ Error checking permissions: {str(e)}"
    
    def open_system_preferences(self, section: str = "") -> str:
        """Open macOS System Settings to the specified section."""
        try:
            if section == "privacy":
                # Open Privacy & Security section
                subprocess.run([
                    'open', 
                    'x-apple.systempreferences:com.apple.preference.security?Privacy'
                ])
                return "✅ Opened Privacy & Security settings"
            elif section == "accessibility":
                subprocess.run([
                    'open',
                    'x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility'
                ])
                return "✅ Opened Accessibility settings"
            elif section == "screen_recording":
                subprocess.run([
                    'open',
                    'x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture'
                ])
                return "✅ Opened Screen Recording settings"
            elif section == "full_disk_access":
                subprocess.run([
                    'open',
                    'x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles'
                ])
                return "✅ Opened Full Disk Access settings"
            else:
                subprocess.run(['open', '/System/Library/PreferencePanes/Security.prefPane'])
                return "✅ Opened System Settings"
                
        except Exception as e:
            logger.error(f"Error opening System Settings: {str(e)}")
            return f"❌ Failed to open System Settings: {str(e)}"
    
    def create_launch_daemon(self) -> str:
        """Create a launchd daemon for always-on operation."""
        try:
            daemon_plist = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.apex.daemon</string>
    <key>ProgramArguments</key>
    <array>
        <string>{os.path.abspath(__file__)}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>{os.path.dirname(os.path.abspath(__file__))}</string>
</dict>
</plist>'''
            
            daemon_path = os.path.expanduser("~/Library/LaunchAgents/com.apex.daemon.plist")
            os.makedirs(os.path.dirname(daemon_path), exist_ok=True)
            
            with open(daemon_path, 'w') as f:
                f.write(daemon_plist)
            
            # Load the daemon
            subprocess.run(['launchctl', 'load', daemon_path])
            
            return f"✅ Created launch daemon at {daemon_path}"
            
        except Exception as e:
            logger.error(f"Error creating launch daemon: {str(e)}")
            return f"❌ Failed to create launch daemon: {str(e)}"
