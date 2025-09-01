import subprocess
import time
import logging
import platform
import psutil
from typing import List, Optional, Dict

logger = logging.getLogger(__name__)

class AppController:
    def __init__(self):
        self.platform = platform.system().lower()
        
        # Common application mappings
        self.app_mappings = {
            'chrome': ['Google Chrome', 'chrome', 'google-chrome'],
            'firefox': ['Firefox', 'firefox'],
            'safari': ['Safari', 'safari'],
            'code': ['Visual Studio Code', 'code', 'vscode'],
            'terminal': ['Terminal', 'terminal', 'gnome-terminal', 'konsole'],
            'finder': ['Finder', 'finder', 'nautilus', 'dolphin'],
            'calculator': ['Calculator', 'calculator', 'galculator'],
            'notes': ['Notes', 'notes', 'gedit', 'notepad'],
            'music': ['Music', 'Spotify', 'iTunes', 'rhythmbox'],
            'mail': ['Mail', 'Thunderbird', 'Evolution']
        }
    
    def launch_app(self, app_name: str) -> str:
        """Launch an application."""
        try:
            app_name = app_name.lower().strip()
            
            # Find the actual app name for this platform
            executable = self._find_app_executable(app_name)
            
            if not executable:
                return f"Application '{app_name}' not found"
            
            # Launch the application
            if self.platform == 'darwin':  # macOS
                subprocess.run(['open', '-a', executable], check=True)
            elif self.platform == 'windows':
                subprocess.Popen([executable])
            else:  # Linux
                subprocess.Popen([executable])
            
            return f"Launched {executable}"
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to launch app: {str(e)}")
            return f"Failed to launch {app_name}: {str(e)}"
        except Exception as e:
            logger.error(f"Error launching app: {str(e)}")
            return f"Error launching {app_name}: {str(e)}"
    
    def close_app(self, app_name: str) -> str:
        """Close an application."""
        try:
            app_name = app_name.lower().strip()
            
            # Find running processes
            processes = self._find_running_processes(app_name)
            
            if not processes:
                return f"No running instance of '{app_name}' found"
            
            # Terminate processes
            closed_count = 0
            for process in processes:
                try:
                    process.terminate()
                    process.wait(timeout=5)  # Wait up to 5 seconds for graceful shutdown
                    closed_count += 1
                except psutil.TimeoutExpired:
                    # Force kill if it doesn't close gracefully
                    process.kill()
                    closed_count += 1
                except Exception as e:
                    logger.warning(f"Failed to close process {process.pid}: {str(e)}")
            
            if closed_count > 0:
                return f"Closed {closed_count} instance(s) of {app_name}"
            else:
                return f"Failed to close {app_name}"
            
        except Exception as e:
            logger.error(f"Error closing app: {str(e)}")
            return f"Error closing {app_name}: {str(e)}"
    
    def switch_to_app(self, app_name: str) -> str:
        """Switch focus to an application."""
        try:
            app_name = app_name.lower().strip()
            
            # Find running processes
            processes = self._find_running_processes(app_name)
            
            if not processes:
                return f"No running instance of '{app_name}' found. Try launching it first."
            
            # Platform-specific window focusing
            if self.platform == 'darwin':  # macOS
                executable = self._find_app_executable(app_name)
                if executable:
                    subprocess.run(['osascript', '-e', f'tell application "{executable}" to activate'])
                    return f"Switched to {executable}"
            elif self.platform == 'linux':
                # Try using wmctrl if available
                try:
                    subprocess.run(['wmctrl', '-a', app_name], check=True)
                    return f"Switched to {app_name}"
                except (subprocess.CalledProcessError, FileNotFoundError):
                    return f"Unable to switch to {app_name}. Window manager tools not available."
            else:  # Windows
                # This would require more complex Windows API calls
                return f"Window switching not fully implemented for Windows yet"
            
            return f"Attempted to switch to {app_name}"
            
        except Exception as e:
            logger.error(f"Error switching to app: {str(e)}")
            return f"Error switching to {app_name}: {str(e)}"
    
    def list_running_apps(self) -> str:
        """List all running applications."""
        try:
            apps = []
            
            for process in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    if process.info['exe']:  # Has executable path
                        apps.append({
                            'name': process.info['name'],
                            'pid': process.info['pid'],
                            'exe': process.info['exe']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Group by application name
            app_groups = {}
            for app in apps:
                name = app['name']
                if name not in app_groups:
                    app_groups[name] = []
                app_groups[name].append(app)
            
            # Format output
            result = "Running Applications:\n\n"
            for name, instances in sorted(app_groups.items()):
                if len(instances) == 1:
                    result += f"• {name} (PID: {instances[0]['pid']})\n"
                else:
                    result += f"• {name} ({len(instances)} instances)\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Error listing apps: {str(e)}")
            return f"Error listing running applications: {str(e)}"
    
    def _find_app_executable(self, app_name: str) -> Optional[str]:
        """Find the executable name for an application."""
        # Check direct mapping
        if app_name in self.app_mappings:
            candidates = self.app_mappings[app_name]
        else:
            candidates = [app_name]
        
        # Platform-specific search
        for candidate in candidates:
            if self.platform == 'darwin':
                # Check if app exists in Applications folder
                app_path = f"/Applications/{candidate}.app"
                if subprocess.run(['test', '-d', app_path], capture_output=True).returncode == 0:
                    return candidate
            
            elif self.platform == 'windows':
                # Check if executable exists in PATH
                try:
                    subprocess.run(['where', candidate], check=True, capture_output=True)
                    return candidate
                except subprocess.CalledProcessError:
                    continue
            
            else:  # Linux
                # Check if executable exists in PATH
                try:
                    subprocess.run(['which', candidate], check=True, capture_output=True)
                    return candidate
                except subprocess.CalledProcessError:
                    continue
        
        return None
    
    def _find_running_processes(self, app_name: str) -> List[psutil.Process]:
        """Find running processes matching the app name."""
        processes = []
        
        # Get possible names
        if app_name in self.app_mappings:
            search_names = self.app_mappings[app_name] + [app_name]
        else:
            search_names = [app_name]
        
        # Search through running processes
        for process in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                process_name = process.info['name'].lower()
                
                # Check if process name matches any of our search names
                for search_name in search_names:
                    if search_name.lower() in process_name:
                        processes.append(process)
                        break
                
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return processes
    
    def get_app_info(self, app_name: str) -> str:
        """Get information about an application."""
        try:
            app_name = app_name.lower().strip()
            
            # Check if app is installed
            executable = self._find_app_executable(app_name)
            installed = executable is not None
            
            # Check if app is running
            processes = self._find_running_processes(app_name)
            running = len(processes) > 0
            
            info = []
            info.append(f"Application: {app_name}")
            info.append(f"Installed: {'Yes' if installed else 'No'}")
            if installed:
                info.append(f"Executable: {executable}")
            
            info.append(f"Running: {'Yes' if running else 'No'}")
            if running:
                info.append(f"Instances: {len(processes)}")
                for i, process in enumerate(processes):
                    info.append(f"  Instance {i+1}: PID {process.pid}")
            
            return "\n".join(info)
            
        except Exception as e:
            logger.error(f"Error getting app info: {str(e)}")
            return f"Error getting app info: {str(e)}"
