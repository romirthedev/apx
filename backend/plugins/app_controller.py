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
        
        # Initialize app state tracking
        self.running_apps = {}
        self.focused_app = None
        self.app_windows = {}
        
        # Platform-specific initialization
        if self.platform == 'darwin':
            self._init_macos()
        elif self.platform == 'windows':
            self._init_windows()
        else:
            self._init_linux()
    
        # Enhanced application mappings with metadata
        self.app_mappings = {
            'chrome': {
                'names': ['Google Chrome', 'chrome', 'google-chrome'],
                'protocols': ['http', 'https'],
                'file_types': ['.html', '.htm'],
                'default_args': ['--new-window'],
                'category': 'browser'
            },
            'firefox': {
                'names': ['Firefox', 'firefox'],
                'protocols': ['http', 'https'],
                'file_types': ['.html', '.htm'],
                'default_args': ['-new-window'],
                'category': 'browser'
            },
            'safari': {
                'names': ['Safari', 'safari'],
                'protocols': ['http', 'https'],
                'file_types': ['.html', '.htm'],
                'default_args': [],
                'category': 'browser'
            },
            'code': {
                'names': ['Visual Studio Code', 'code', 'vscode'],
                'protocols': ['vscode'],
                'file_types': ['.txt', '.md', '.py', '.js', '.html', '.css', '.json'],
                'default_args': ['--new-window'],
                'category': 'editor'
            },
            'terminal': {
                'names': ['Terminal', 'terminal', 'gnome-terminal', 'konsole'],
                'protocols': [],
                'file_types': [],
                'default_args': [],
                'category': 'system'
            },
            'finder': {
                'names': ['Finder', 'finder', 'nautilus', 'dolphin'],
                'protocols': ['file'],
                'file_types': [],
                'default_args': [],
                'category': 'system'
            },
            'calculator': {
                'names': ['Calculator', 'calculator', 'galculator'],
                'protocols': [],
                'file_types': [],
                'default_args': [],
                'category': 'utility'
            },
            'notes': {
                'names': ['Notes', 'notes', 'gedit', 'notepad'],
                'protocols': [],
                'file_types': ['.txt', '.md', '.rtf'],
                'default_args': [],
                'category': 'productivity'
            },
            'music': {
                'names': ['Music', 'Spotify', 'iTunes', 'rhythmbox'],
                'protocols': ['spotify'],
                'file_types': ['.mp3', '.m4a', '.wav', '.flac'],
                'default_args': [],
                'category': 'media'
            },
            'mail': {
                'names': ['Mail', 'Thunderbird', 'Evolution'],
                'protocols': ['mailto'],
                'file_types': ['.eml'],
                'default_args': [],
                'category': 'communication'
            }
        }
        
        # Initialize app state tracking
        self.running_apps = {}
        self.focused_app = None
        self.app_windows = {}
        
        # Platform-specific initialization
        if self.platform == 'darwin':
            self._init_macos()
        elif self.platform == 'windows':
            self._init_windows()
        else:
            self._init_linux()
    
    def _init_macos(self):
        """Initialize macOS-specific functionality."""
        try:
            # Set up AppleScript command templates
            self.as_templates = {
                'activate': 'tell application "{}" to activate',
                'quit': 'tell application "{}" to quit',
                'hide': 'tell application "{}" to hide',
                'show': 'tell application "{}" to reopen',
                'get_windows': 'tell application "{}" to get windows',
                'window_bounds': 'tell application "{}" to get bounds of window {}',
                'set_bounds': 'tell application "{}" to set bounds of window {} to {{{}, {}, {}, {}}}'
            }
        except Exception as e:
            logger.error(f"Failed to initialize macOS support: {str(e)}")
    
    def _init_windows(self):
        """Initialize Windows-specific functionality."""
        try:
            # Import Windows-specific modules only if needed
            import win32gui
            import win32con
            import win32process
            
            self.win32_modules = {
                'gui': win32gui,
                'con': win32con,
                'process': win32process
            }
        except ImportError:
            logger.warning("Windows support modules not available")
    
    def _init_linux(self):
        """Initialize Linux-specific functionality."""
        try:
            # Check for window manager tools
            self.wm_tools = {
                'wmctrl': subprocess.run(['which', 'wmctrl'], capture_output=True).returncode == 0,
                'xdotool': subprocess.run(['which', 'xdotool'], capture_output=True).returncode == 0,
                'gdbus': subprocess.run(['which', 'gdbus'], capture_output=True).returncode == 0
            }
        except Exception as e:
            logger.error(f"Failed to initialize Linux support: {str(e)}")
    
    def launch_app(self, app_name: str, file_path: str = None, url: str = None) -> str:
        """Launch an application with optional file or URL.
        
        Args:
            app_name: Name of the application to launch
            file_path: Optional file path to open with the application
            url: Optional URL to open with the application
        """
        try:
            app_name = app_name.lower().strip()
            
            # Get app configuration
            app_config = self._get_app_config(app_name)
            if not app_config:
                return f"Application '{app_name}' not found"
            
            # Find executable
            executable = self._find_app_executable(app_config['names'])
            if not executable:
                return f"Executable for '{app_name}' not found"
            
            # Prepare launch arguments
            args = [executable] + app_config['default_args']
            
            # Handle file or URL if provided
            if file_path:
                if not any(file_path.endswith(ext) for ext in app_config['file_types']):
                    logger.warning(f"File type may not be supported by {app_name}")
                args.append(file_path)
            elif url:
                if not any(url.startswith(f"{proto}://") for proto in app_config['protocols']):
                    logger.warning(f"Protocol may not be supported by {app_name}")
                args.append(url)
            
            # Platform-specific launch
            if self.platform == 'darwin':
                if file_path or url:
                    subprocess.run(['open', '-a', executable, *(file_path or url)], check=True)
                else:
                    subprocess.run(['open', '-a', executable], check=True)
            else:
                process = subprocess.Popen(args)
                self.running_apps[app_name] = process.pid
            
            # Update state tracking
            self._update_app_state(app_name, 'launched')
            
            return f"Launched {app_name}" + (f" with {file_path or url}" if file_path or url else "")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to launch app: {str(e)}")
            return f"Failed to launch {app_name}: {str(e)}"
        except Exception as e:
            logger.error(f"Error launching app: {str(e)}")
            return f"Error launching {app_name}: {str(e)}"
    
    def close_app(self, app_name: str, force: bool = False) -> str:
        """Close an application.
        
        Args:
            app_name: Name of the application to close
            force: Whether to force-quit the application
        """
        try:
            app_name = app_name.lower().strip()
            
            # Get app configuration
            app_config = self._get_app_config(app_name)
            if not app_config:
                return f"Application '{app_name}' not found"
            
            # Platform-specific closing
            if self.platform == 'darwin' and not force:
                try:
                    subprocess.run(['osascript', '-e', self.as_templates['quit'].format(app_config['names'][0])])
                    self._update_app_state(app_name, 'closed')
                    return f"Closed {app_name}"
                except subprocess.CalledProcessError:
                    logger.warning(f"Graceful close failed for {app_name}, attempting force quit")
                    force = True
            
            # Force quit if needed or on other platforms
            processes = self._find_running_processes(app_name)
            if not processes:
                return f"No running instance of '{app_name}' found"
            
            closed_count = 0
            for process in processes:
                try:
                    if force:
                        process.kill()
                    else:
                        process.terminate()
                        process.wait(timeout=5)
                    closed_count += 1
                except psutil.TimeoutExpired:
                    process.kill()
                    closed_count += 1
                except Exception as e:
                    logger.warning(f"Failed to close process {process.pid}: {str(e)}")
            
            if closed_count > 0:
                self._update_app_state(app_name, 'closed')
                return f"Closed {closed_count} instance(s) of {app_name}"
            
            return f"Failed to close {app_name}"
            
        except Exception as e:
            logger.error(f"Error closing app: {str(e)}")
            return f"Error closing {app_name}: {str(e)}"
    
    def switch_to_app(self, app_name: str, new_window: bool = False) -> str:
        """Switch focus to an application.
        
        Args:
            app_name: Name of the application to switch to
            new_window: Whether to open a new window if none exists
        """
        try:
            app_name = app_name.lower().strip()
            
            # Get app configuration
            app_config = self._get_app_config(app_name)
            if not app_config:
                return f"Application '{app_name}' not found"
            
            # Check if app is running
            processes = self._find_running_processes(app_name)
            if not processes:
                if new_window:
                    return self.launch_app(app_name)
                return f"No running instance of '{app_name}' found. Try launching it first."
            
            # Platform-specific window focusing
            if self.platform == 'darwin':
                subprocess.run(['osascript', '-e', self.as_templates['activate'].format(app_config['names'][0])])
                self.focused_app = app_name
                return f"Switched to {app_name}"
                
            elif self.platform == 'linux':
                if self.wm_tools['wmctrl']:
                    try:
                        subprocess.run(['wmctrl', '-a', app_config['names'][0]], check=True)
                        self.focused_app = app_name
                        return f"Switched to {app_name}"
                    except subprocess.CalledProcessError:
                        pass
                
                if self.wm_tools['xdotool']:
                    try:
                        # Try using xdotool as fallback
                        subprocess.run(['xdotool', 'search', '--name', app_config['names'][0], 'windowactivate'], check=True)
                        self.focused_app = app_name
                        return f"Switched to {app_name}"
                    except subprocess.CalledProcessError:
                        pass
                        
                return f"Unable to switch to {app_name}. Window manager tools not available."
                
            elif self.platform == 'windows' and hasattr(self, 'win32_modules'):
                try:
                    # Use Win32 API to find and activate window
                    def callback(hwnd, extra):
                        if self.win32_modules['gui'].IsWindowVisible(hwnd):
                            title = self.win32_modules['gui'].GetWindowText(hwnd)
                            if any(name.lower() in title.lower() for name in app_config['names']):
                                self.win32_modules['gui'].SetForegroundWindow(hwnd)
                                return False
                        return True
                    
                    self.win32_modules['gui'].EnumWindows(callback, None)
                    self.focused_app = app_name
                    return f"Switched to {app_name}"
                except Exception as e:
                    logger.error(f"Failed to switch windows: {str(e)}")
            
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
    
    def _find_app_executable(self, app_names: List[str]) -> Optional[str]:
        """Find the executable name for an application.
        
        Args:
            app_names: List of possible names for the application
            
        Returns:
            Name of the executable or None if not found
        """
        for app_name in app_names:
            if self.platform == 'darwin':
                # Check if app exists in Applications folder
                app_path = f"/Applications/{app_name}.app"
                if subprocess.run(['test', '-d', app_path], capture_output=True).returncode == 0:
                    return app_name
            
            elif self.platform == 'windows':
                # Check if executable exists in PATH
                try:
                    subprocess.run(['where', app_name], check=True, capture_output=True)
                    return app_name
                except subprocess.CalledProcessError:
                    continue
            
            else:  # Linux
                # Check if executable exists in PATH
                try:
                    subprocess.run(['which', app_name], check=True, capture_output=True)
                    return app_name
                except subprocess.CalledProcessError:
                    continue
        
        return None
    
    def _find_running_processes(self, app_name: str) -> List[psutil.Process]:
        """Find running processes matching the app name.
        
        Args:
            app_name: Name of the application to find
            
        Returns:
            List of running processes for the application
        """
        processes = []
        
        # Get app configuration
        app_config = self._get_app_config(app_name)
        if not app_config:
            return []
        
        # Get all possible names
        search_names = app_config['names']
        
        # Search through running processes
        for process in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                process_name = process.info['name'].lower()
                
                # Check if process name matches any of our search names
                if any(name.lower() in process_name for name in search_names):
                    processes.append(process)
                
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
