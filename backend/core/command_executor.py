import os
import subprocess
import logging
import time
import json
import shutil
import platform
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Union
import tempfile
import webbrowser

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    from AppKit import NSWorkspace, NSAppleScript
    APPKIT_AVAILABLE = True
except ImportError:
    APPKIT_AVAILABLE = False

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False

logger = logging.getLogger(__name__)

class CommandExecutor:
    """Executes commands on macOS based on structured action plans."""
    
    def __init__(self, sandbox_mode: bool = True):
        """Initialize the CommandExecutor.
        
        Args:
            sandbox_mode: If True, restricts potentially dangerous operations
        """
        self.current_directory = os.path.expanduser("~")
        self.sandbox_mode = sandbox_mode
        self.last_result = None
        self.task_history = []
        
        # Define safe directories for file operations when in sandbox mode
        self.safe_directories = [
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Documents"),
            os.path.expanduser("~/Downloads"),
            tempfile.gettempdir()
        ]
    
    def execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single action based on its type.
        
        Args:
            action: Dictionary with action details
            
        Returns:
            Dictionary with execution results
        """
        action_type = action.get('type')
        parameters = action.get('parameters', {})
        
        start_time = time.time()
        result = {
            'success': False,
            'output': '',
            'error': '',
            'action_type': action_type,
            'execution_time': 0
        }
        
        try:
            # File operations
            if action_type == 'create_file':
                result = self._handle_create_file(parameters)
            elif action_type == 'find_file':
                result = self._handle_find_file(parameters)
            elif action_type in ['file_open', 'open_file']:
                result = self._handle_open_file(parameters)
            elif action_type in ['file_edit', 'edit_file']:
                result = self._handle_edit_file(parameters)
            elif action_type in ['file_delete', 'delete_file']:
                result = self._handle_delete_file(parameters)
            
            # App control
            elif action_type in ['open_app', 'app_launch']:
                result = self._handle_open_app(parameters)
            elif action_type in ['close_app', 'app_close']:
                result = self._handle_close_app(parameters)
                
            # Web operations
            elif action_type in ['navigate_url', 'web_browse']:
                result = self._handle_navigate_url(parameters)
            elif action_type == 'web_search':
                result = self._handle_web_search(parameters)
                
            # System control
            elif action_type == 'run_command':
                result = self._handle_run_command(parameters)
            elif action_type == 'get_system_info':
                result = self._handle_get_system_info(parameters)
            elif action_type == 'get_date':
                result = self._handle_get_date(parameters)
            elif action_type == 'take_screenshot':
                result = self._handle_take_screenshot(parameters)
                
            # Input simulation
            elif action_type == 'type_text':
                result = self._handle_type_text(parameters)
            elif action_type == 'press_keys':
                result = self._handle_press_keys(parameters)
            elif action_type == 'click_coordinates':
                result = self._handle_click_coordinates(parameters)
            
            # Default fallback
            else:
                result['error'] = f"Unknown action type: {action_type}"
            
        except Exception as e:
            logger.error(f"Error executing {action_type}: {str(e)}")
            result['error'] = f"Error executing {action_type}: {str(e)}"
        
        result['execution_time'] = time.time() - start_time
        
        # Record action in history
        self.task_history.append({
            'action': action,
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
        
        return result
    
    def execute_plan(self, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute a series of actions as a plan.
        
        Args:
            actions: List of action dictionaries
            
        Returns:
            Dictionary with plan execution results
        """
        overall_result = {
            'success': True,
            'results': [],
            'error': '',
            'total_execution_time': 0,
            'completed_actions': 0,
            'failed_actions': 0
        }
        
        start_time = time.time()
        
        for i, action in enumerate(actions):
            logger.info(f"Executing action {i+1}/{len(actions)}: {action.get('type')}")
            
            # Execute the action
            result = self.execute_action(action)
            overall_result['results'].append(result)
            
            # Update counters
            if result['success']:
                overall_result['completed_actions'] += 1
            else:
                overall_result['failed_actions'] += 1
                overall_result['success'] = False
                
            # If a critical action fails, we might want to stop the plan
            if not result['success'] and action.get('critical', False):
                logger.warning(f"Critical action failed: {action.get('type')}")
                overall_result['error'] = f"Critical action failed: {action.get('type')}"
                break
        
        overall_result['total_execution_time'] = time.time() - start_time
        
        return overall_result
    
    def _is_path_safe(self, path: str) -> bool:
        """Check if a file path is within safe directories when in sandbox mode.
        
        Args:
            path: File path to check
            
        Returns:
            Boolean indicating if path is safe
        """
        if not self.sandbox_mode:
            return True
            
        path = os.path.abspath(os.path.expanduser(path))
        
        for safe_dir in self.safe_directories:
            if path.startswith(safe_dir):
                return True
                
        return False
    
    def _run_shell_command(self, command: str, timeout: int = 30, shell: bool = True) -> Tuple[bool, str, str]:
        """Run a shell command safely.
        
        Args:
            command: Command to execute
            timeout: Timeout in seconds
            shell: Whether to use shell execution
            
        Returns:
            Tuple of (success, output, error)
        """
        # Check for dangerous commands in sandbox mode
        dangerous_patterns = [
            r'rm\s+-rf\s+/', 
            r'sudo\s+rm', 
            r'chmod\s+777', 
            r'mkfs', 
            r'dd\s+if=',
            r'>\s+/dev/',
            r':\(\)\s+{\s+:\|\:',  # Fork bomb pattern
        ]
        
        if self.sandbox_mode:
            for pattern in dangerous_patterns:
                if re.search(pattern, command):
                    return False, "", f"Potentially dangerous command blocked in sandbox mode: {command}"
        
        try:
            result = subprocess.run(
                command, 
                shell=shell, 
                capture_output=True, 
                text=True,
                timeout=timeout
            )
            
            success = result.returncode == 0
            output = result.stdout
            error = result.stderr
            
            return success, output, error
            
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return False, "", f"Error executing command: {str(e)}"
    
    # File operations
    def _handle_create_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a file with specified content.
        
        Args:
            params: Parameters including path and content
            
        Returns:
            Result dictionary
        """
        result = {
            'success': False,
            'output': '',
            'error': ''
        }
        
        path = params.get('path') or params.get('file_path') or params.get('filename', '')
        content = params.get('content', '')
        
        if not path:
            result['error'] = "No file path specified"
            return result
            
        # Expand user directory if needed
        path = os.path.expanduser(path)
        
        # Check if path is safe
        if not self._is_path_safe(path):
            result['error'] = f"Path not in allowed directories: {path}"
            return result
        
        try:
            # Create directory if it doesn't exist
            directory = os.path.dirname(path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            
            # Write content to file
            with open(path, 'w') as file:
                file.write(content)
            
            result['success'] = True
            result['output'] = f"File created: {path}"
            
        except Exception as e:
            result['error'] = f"Failed to create file: {str(e)}"
        
        return result
    
    def _handle_find_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Find files matching pattern.
        
        Args:
            params: Parameters including pattern and path
            
        Returns:
            Result dictionary
        """
        result = {
            'success': False,
            'output': '',
            'error': '',
            'files': []
        }
        
        pattern = params.get('pattern') or params.get('query', '*')
        search_path = params.get('path', '~')
        search_path = os.path.expanduser(search_path)
        
        # Limit search to safe directories in sandbox mode
        if self.sandbox_mode and not self._is_path_safe(search_path):
            search_path = os.path.expanduser('~')
        
        try:
            # Use find command for more efficient search
            command = f"find '{search_path}' -name '{pattern}' -type f 2>/dev/null | head -50"
            success, output, error = self._run_shell_command(command)
            
            if success:
                files = [f for f in output.strip().split('\n') if f]
                result['files'] = files
                result['success'] = True
                
                if len(files) > 0:
                    result['output'] = f"Found {len(files)} files matching '{pattern}'."
                else:
                    result['output'] = f"No files found matching '{pattern}'."
            else:
                result['error'] = error or "File search failed"
                
        except Exception as e:
            result['error'] = f"Error searching for files: {str(e)}"
        
        return result
    
    def _handle_open_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Open a file with the default application.
        
        Args:
            params: Parameters including file path
            
        Returns:
            Result dictionary
        """
        result = {
            'success': False,
            'output': '',
            'error': ''
        }
        
        path = params.get('path') or params.get('file_path') or params.get('filename', '')
        
        if not path:
            result['error'] = "No file path specified"
            return result
            
        path = os.path.expanduser(path)
        
        # Check if path is safe and file exists
        if not self._is_path_safe(path):
            result['error'] = f"Path not in allowed directories: {path}"
            return result
            
        if not os.path.exists(path):
            result['error'] = f"File not found: {path}"
            return result
        
        try:
            if APPKIT_AVAILABLE:
                workspace = NSWorkspace.sharedWorkspace()
                success = workspace.openFile_(path)
                
                if success:
                    result['success'] = True
                    result['output'] = f"File opened: {path}"
                else:
                    result['error'] = f"Failed to open file with default application"
            else:
                # Fallback to open command
                command = f"open '{path}'"
                success, output, error = self._run_shell_command(command)
                
                if success:
                    result['success'] = True
                    result['output'] = f"File opened: {path}"
                else:
                    result['error'] = error or "Failed to open file"
                
        except Exception as e:
            result['error'] = f"Error opening file: {str(e)}"
        
        return result
    
    def _handle_edit_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Edit a file with specified content.
        
        Args:
            params: Parameters including path and content
            
        Returns:
            Result dictionary
        """
        result = {
            'success': False,
            'output': '',
            'error': ''
        }
        
        path = params.get('path') or params.get('file_path') or params.get('filename', '')
        content = params.get('content', '')
        append = params.get('append', False)
        
        if not path:
            result['error'] = "No file path specified"
            return result
            
        path = os.path.expanduser(path)
        
        # Check if path is safe
        if not self._is_path_safe(path):
            result['error'] = f"Path not in allowed directories: {path}"
            return result
        
        try:
            # Create directory if it doesn't exist
            directory = os.path.dirname(path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            
            # Write or append content to file
            mode = 'a' if append else 'w'
            with open(path, mode) as file:
                file.write(content)
            
            result['success'] = True
            action = "updated" if os.path.exists(path) and not append else "appended to" if append else "created"
            result['output'] = f"File {action}: {path}"
            
        except Exception as e:
            result['error'] = f"Failed to edit file: {str(e)}"
        
        return result
    
    def _handle_delete_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a file.
        
        Args:
            params: Parameters including file path
            
        Returns:
            Result dictionary
        """
        result = {
            'success': False,
            'output': '',
            'error': ''
        }
        
        path = params.get('path') or params.get('file_path') or params.get('filename', '')
        
        if not path:
            result['error'] = "No file path specified"
            return result
            
        path = os.path.expanduser(path)
        
        # Check if path is safe and file exists
        if not self._is_path_safe(path):
            result['error'] = f"Path not in allowed directories: {path}"
            return result
            
        if not os.path.exists(path):
            result['error'] = f"File not found: {path}"
            return result
        
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            
            result['success'] = True
            result['output'] = f"Deleted: {path}"
                
        except Exception as e:
            result['error'] = f"Error deleting file: {str(e)}"
        
        return result
    
    # App control
    def _handle_open_app(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Open an application.
        
        Args:
            params: Parameters including app name
            
        Returns:
            Result dictionary
        """
        result = {
            'success': False,
            'output': '',
            'error': ''
        }
        
        app_name = params.get('app') or params.get('name', '')
        
        if not app_name:
            result['error'] = "No application name specified"
            return result
        
        try:
            if APPKIT_AVAILABLE:
                workspace = NSWorkspace.sharedWorkspace()
                apps = workspace.runningApplications()
                
                # Check if app is already running
                for running_app in apps:
                    if app_name.lower() in running_app.localizedName().lower():
                        # App is already running, activate it
                        success = workspace.launchApplication_(app_name)
                        if success:
                            result['success'] = True
                            result['output'] = f"Application activated: {app_name}"
                            return result
                
                # App is not running, launch it
                success = workspace.launchApplication_(app_name)
                
                if success:
                    result['success'] = True
                    result['output'] = f"Application launched: {app_name}"
                else:
                    # Try using open command as fallback
                    command = f"open -a '{app_name}'"
                    success, output, error = self._run_shell_command(command)
                    
                    if success:
                        result['success'] = True
                        result['output'] = f"Application launched: {app_name}"
                    else:
                        result['error'] = error or f"Failed to launch application: {app_name}"
            else:
                # Fallback to open command
                command = f"open -a '{app_name}'"
                success, output, error = self._run_shell_command(command)
                
                if success:
                    result['success'] = True
                    result['output'] = f"Application launched: {app_name}"
                else:
                    result['error'] = error or f"Failed to launch application: {app_name}"
                
        except Exception as e:
            result['error'] = f"Error opening application: {str(e)}"
        
        return result
    
    def _handle_close_app(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Close an application.
        
        Args:
            params: Parameters including app name
            
        Returns:
            Result dictionary
        """
        result = {
            'success': False,
            'output': '',
            'error': ''
        }
        
        app_name = params.get('app') or params.get('name', '')
        
        if not app_name:
            result['error'] = "No application name specified"
            return result
        
        try:
            # Try using AppleScript to quit the application gracefully
            script = f'tell application "{app_name}" to quit'
            
            if APPKIT_AVAILABLE:
                script_obj = NSAppleScript.alloc().initWithSource_(script)
                _, error_info = script_obj.executeAndReturnError_(None)
                
                if error_info:
                    # Try using pkill as fallback
                    command = f"pkill -x '{app_name}'"
                    success, output, error = self._run_shell_command(command)
                    
                    if success:
                        result['success'] = True
                        result['output'] = f"Application closed: {app_name}"
                    else:
                        result['error'] = error or f"Failed to close application: {app_name}"
                else:
                    result['success'] = True
                    result['output'] = f"Application closed: {app_name}"
            else:
                # Try osascript
                command = f"osascript -e 'tell application \"{app_name}\" to quit'"
                success, output, error = self._run_shell_command(command)
                
                if success:
                    result['success'] = True
                    result['output'] = f"Application closed: {app_name}"
                else:
                    # Try using pkill as fallback
                    command = f"pkill -x '{app_name}'"
                    success, output, error = self._run_shell_command(command)
                    
                    if success:
                        result['success'] = True
                        result['output'] = f"Application closed: {app_name}"
                    else:
                        result['error'] = error or f"Failed to close application: {app_name}"
                
        except Exception as e:
            result['error'] = f"Error closing application: {str(e)}"
        
        return result
    
    # Web operations
    def _handle_navigate_url(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Navigate to a URL in the default browser.
        
        Args:
            params: Parameters including URL
            
        Returns:
            Result dictionary
        """
        result = {
            'success': False,
            'output': '',
            'error': ''
        }
        
        url = params.get('url', '')
        
        if not url:
            result['error'] = "No URL specified"
            return result
        
        # Ensure URL has http/https prefix
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        try:
            # Use webbrowser module to open URL
            browser_opened = webbrowser.open(url)
            
            if browser_opened:
                result['success'] = True
                result['output'] = f"Opened URL: {url}"
            else:
                # Try using open command as fallback
                command = f"open '{url}'"
                success, output, error = self._run_shell_command(command)
                
                if success:
                    result['success'] = True
                    result['output'] = f"Opened URL: {url}"
                else:
                    result['error'] = error or f"Failed to open URL: {url}"
                
        except Exception as e:
            result['error'] = f"Error navigating to URL: {str(e)}"
        
        return result
    
    def _handle_web_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform a web search.
        
        Args:
            params: Parameters including query
            
        Returns:
            Result dictionary
        """
        result = {
            'success': False,
            'output': '',
            'error': ''
        }
        
        query = params.get('query', '')
        search_engine = params.get('engine', 'google').lower()
        
        if not query:
            result['error'] = "No search query specified"
            return result
        
        try:
            # Create search URL based on engine
            if search_engine == 'google':
                url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            elif search_engine == 'bing':
                url = f"https://www.bing.com/search?q={query.replace(' ', '+')}"
            elif search_engine == 'duckduckgo':
                url = f"https://duckduckgo.com/?q={query.replace(' ', '+')}"
            else:
                url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            
            # Navigate to the search URL
            browser_opened = webbrowser.open(url)
            
            if browser_opened:
                result['success'] = True
                result['output'] = f"Searched for: {query} using {search_engine}"
            else:
                # Try using open command as fallback
                command = f"open '{url}'"
                success, output, error = self._run_shell_command(command)
                
                if success:
                    result['success'] = True
                    result['output'] = f"Searched for: {query} using {search_engine}"
                else:
                    result['error'] = error or f"Failed to perform web search"
                
        except Exception as e:
            result['error'] = f"Error performing web search: {str(e)}"
        
        return result
    
    # System operations
    def _handle_run_command(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run a shell command.
        
        Args:
            params: Parameters including command
            
        Returns:
            Result dictionary
        """
        result = {
            'success': False,
            'output': '',
            'error': ''
        }
        
        command = params.get('command', '')
        timeout = params.get('timeout', 30)
        
        if not command:
            result['error'] = "No command specified"
            return result
        
        try:
            success, output, error = self._run_shell_command(command, timeout=timeout)
            
            result['success'] = success
            result['output'] = output
            result['error'] = error
                
        except Exception as e:
            result['error'] = f"Error running command: {str(e)}"
        
        return result
    
    def _handle_get_system_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get system information.
        
        Args:
            params: Parameters specifying what info to get
            
        Returns:
            Result dictionary
        """
        result = {
            'success': False,
            'output': '',
            'error': '',
            'system_info': {}
        }
        
        info_type = params.get('type', 'basic')
        
        try:
            system_info = {
                'os': platform.system(),
                'os_version': platform.version(),
                'hostname': platform.node(),
                'python_version': platform.python_version(),
                'architecture': platform.machine()
            }
            
            if PSUTIL_AVAILABLE:
                # Add more detailed system info if psutil is available
                system_info.update({
                    'cpu_percent': psutil.cpu_percent(interval=0.1),
                    'memory_percent': psutil.virtual_memory().percent,
                    'disk_usage': {
                        'total': psutil.disk_usage('/').total,
                        'used': psutil.disk_usage('/').used,
                        'free': psutil.disk_usage('/').free,
                        'percent': psutil.disk_usage('/').percent
                    }
                })
            
            # Get uptime info
            if PSUTIL_AVAILABLE:
                uptime_seconds = int(time.time() - psutil.boot_time())
                days, remainder = divmod(uptime_seconds, 86400)
                hours, remainder = divmod(remainder, 3600)
                minutes, seconds = divmod(remainder, 60)
                system_info['uptime'] = f"{days}d {hours}h {minutes}m {seconds}s"
            
            result['system_info'] = system_info
            result['success'] = True
            
            # Format output based on info type
            if info_type == 'basic':
                result['output'] = f"System: {system_info['os']} {system_info['os_version']} ({system_info['architecture']})"
            else:
                # Format detailed output
                output_lines = [f"System Information:"]
                output_lines.append(f"OS: {system_info['os']} {system_info['os_version']}")
                output_lines.append(f"Hostname: {system_info['hostname']}")
                output_lines.append(f"Architecture: {system_info['architecture']}")
                
                if PSUTIL_AVAILABLE:
                    output_lines.append(f"CPU Usage: {system_info['cpu_percent']}%")
                    output_lines.append(f"Memory Usage: {system_info['memory_percent']}%")
                    output_lines.append(f"Disk Usage: {system_info['disk_usage']['percent']}%")
                    output_lines.append(f"Uptime: {system_info['uptime']}")
                
                result['output'] = "\n".join(output_lines)
                
        except Exception as e:
            result['error'] = f"Error getting system info: {str(e)}"
        
        return result
    
    def _handle_get_date(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get current date and time.
        
        Args:
            params: Parameters including format
            
        Returns:
            Result dictionary
        """
        result = {
            'success': False,
            'output': '',
            'error': ''
        }
        
        date_format = params.get('format', '%Y-%m-%d %H:%M:%S')
        
        try:
            current_time = datetime.now()
            formatted_time = current_time.strftime(date_format)
            
            result['success'] = True
            result['output'] = formatted_time
            result['datetime'] = {
                'year': current_time.year,
                'month': current_time.month,
                'day': current_time.day,
                'hour': current_time.hour,
                'minute': current_time.minute,
                'second': current_time.second,
                'iso': current_time.isoformat()
            }
                
        except Exception as e:
            result['error'] = f"Error getting date: {str(e)}"
        
        return result
    
    def _handle_take_screenshot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Take a screenshot.
        
        Args:
            params: Parameters including output path
            
        Returns:
            Result dictionary
        """
        result = {
            'success': False,
            'output': '',
            'error': '',
            'screenshot_path': ''
        }
        
        output_path = params.get('output_path', '')
        region = params.get('region', None)  # Format: [x, y, width, height]
        
        # If no output path specified, create one in ~/Desktop
        if not output_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = os.path.expanduser(f"~/Desktop/screenshot_{timestamp}.png")
        else:
            output_path = os.path.expanduser(output_path)
        
        # Check if path is safe
        if not self._is_path_safe(output_path):
            result['error'] = f"Path not in allowed directories: {output_path}"
            return result
        
        try:
            if PYAUTOGUI_AVAILABLE:
                # Take screenshot using pyautogui
                if region:
                    try:
                        x, y, width, height = region
                        screenshot = pyautogui.screenshot(region=(x, y, width, height))
                    except:
                        screenshot = pyautogui.screenshot()
                else:
                    screenshot = pyautogui.screenshot()
                
                # Create directory if it doesn't exist
                directory = os.path.dirname(output_path)
                if directory and not os.path.exists(directory):
                    os.makedirs(directory)
                
                # Save screenshot
                screenshot.save(output_path)
                result['success'] = True
                result['output'] = f"Screenshot saved to: {output_path}"
                result['screenshot_path'] = output_path
                
            else:
                # Use screencapture command on macOS
                command = f"screencapture '{output_path}'"
                if region:
                    try:
                        x, y, width, height = region
                        command = f"screencapture -R{x},{y},{width},{height} '{output_path}'"
                    except:
                        pass
                
                success, output, error = self._run_shell_command(command)
                
                if success:
                    result['success'] = True
                    result['output'] = f"Screenshot saved to: {output_path}"
                    result['screenshot_path'] = output_path
                else:
                    result['error'] = error or "Failed to take screenshot"
                
        except Exception as e:
            result['error'] = f"Error taking screenshot: {str(e)}"
        
        return result
    
    # Input simulation
    def _handle_type_text(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Type text using keyboard.
        
        Args:
            params: Parameters including text
            
        Returns:
            Result dictionary
        """
        result = {
            'success': False,
            'output': '',
            'error': ''
        }
        
        text = params.get('text', '')
        
        if not text:
            result['error'] = "No text specified"
            return result
        
        try:
            if PYAUTOGUI_AVAILABLE:
                pyautogui.write(text)
                result['success'] = True
                result['output'] = f"Text typed: {text[:30]}..." if len(text) > 30 else f"Text typed: {text}"
            else:
                # No fallback available for typing
                result['error'] = "PyAutoGUI not available for typing text"
                
        except Exception as e:
            result['error'] = f"Error typing text: {str(e)}"
        
        return result
    
    def _handle_press_keys(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Press key combinations.
        
        Args:
            params: Parameters including keys
            
        Returns:
            Result dictionary
        """
        result = {
            'success': False,
            'output': '',
            'error': ''
        }
        
        keys = params.get('keys', [])
        
        if isinstance(keys, str):
            keys = [keys]
        
        if not keys:
            result['error'] = "No keys specified"
            return result
        
        try:
            if PYAUTOGUI_AVAILABLE:
                pyautogui.hotkey(*keys)
                result['success'] = True
                result['output'] = f"Keys pressed: {'+'.join(keys)}"
            else:
                # No fallback available for key presses
                result['error'] = "PyAutoGUI not available for pressing keys"
                
        except Exception as e:
            result['error'] = f"Error pressing keys: {str(e)}"
        
        return result
    
    def _handle_click_coordinates(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Click at specified coordinates.
        
        Args:
            params: Parameters including x and y
            
        Returns:
            Result dictionary
        """
        result = {
            'success': False,
            'output': '',
            'error': ''
        }
        
        x = params.get('x', 0)
        y = params.get('y', 0)
        button = params.get('button', 'left').lower()
        
        try:
            if PYAUTOGUI_AVAILABLE:
                if button == 'right':
                    pyautogui.rightClick(x, y)
                elif button == 'middle':
                    pyautogui.middleClick(x, y)
                else:
                    pyautogui.click(x, y)
                
                result['success'] = True
                result['output'] = f"{button.capitalize()} click at coordinates ({x}, {y})"
            else:
                # No fallback available for clicking
                result['error'] = "PyAutoGUI not available for clicking"
                
        except Exception as e:
            result['error'] = f"Error clicking at coordinates: {str(e)}"
        
        return result
