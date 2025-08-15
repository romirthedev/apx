import os
import platform
import logging
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path

logger = logging.getLogger(__name__)

class SecurityManager:
    def __init__(self):
        self.platform = platform.system().lower()
        self.required_permissions = self._get_required_permissions()
        
        # Risk levels for different command types
        self.risk_levels = {
            'low': ['read_file', 'list_dir', 'get_info'],
            'medium': ['write_file', 'create_dir', 'move_file'],
            'high': ['delete_file', 'run_script', 'system_command'],
            'critical': ['admin_command', 'network_access', 'app_control']
        }
        
        # Command confirmation cache (to avoid re-asking for similar commands)
        self.confirmation_cache = {}
        self.cache_duration = timedelta(minutes=5)
        
        # Dangerous patterns to always confirm
        self.dangerous_patterns = [
            'rm -rf', 'del /f', 'format', 'sudo rm',
            'chmod 777', 'chown', 'passwd',
            'curl', 'wget', 'ssh', 'scp',
            'systemctl', 'launchctl', 'service'
        ]
        
        # Safe directories where operations are always allowed
        self.safe_directories = [
            str(Path.home() / 'Desktop'),
            str(Path.home() / 'Documents'),
            str(Path.home() / 'Downloads'),
            '/tmp',
            '/var/tmp'
        ]

    def _get_required_permissions(self) -> List[str]:
        """Get list of required permissions based on platform."""
        base_permissions = [
            'file_system_access',
            'network_access',
            'process_control'
        ]
        
        if self.platform == 'darwin':  # macOS
            return base_permissions + [
                'accessibility_access',
                'screen_recording_access'
            ]
        elif self.platform == 'windows':
            return base_permissions + [
                'admin_privileges'
            ]
        elif self.platform == 'linux':
            return base_permissions + [
                'x11_access'
            ]
        
        return base_permissions
    
    def check_permissions(self) -> bool:
        """Check if all required permissions are available."""
        try:
            if self.platform == 'darwin':
                return self._check_macos_permissions()
            elif self.platform == 'windows':
                return self._check_windows_permissions()
            elif self.platform == 'linux':
                return self._check_linux_permissions()
            
            return True
            
        except Exception as e:
            logger.error(f"Permission check failed: {str(e)}")
            return False
    
    def _check_macos_permissions(self) -> bool:
        """Check macOS specific permissions."""
        # For now, return True as we'll handle permissions at runtime
        # In a production app, you'd check for:
        # - Accessibility permissions
        # - Screen recording permissions
        # - Full disk access
        return True
    
    def _check_windows_permissions(self) -> bool:
        """Check Windows specific permissions."""
        # Check if running with admin privileges
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False
    
    def _check_linux_permissions(self) -> bool:
        """Check Linux specific permissions."""
        # Check basic file system permissions
        return os.access('/tmp', os.W_OK)
    
    def request_permissions(self) -> Dict[str, bool]:
        """Request necessary permissions from the user."""
        results = {}
        
        for permission in self.required_permissions:
            try:
                if permission == 'accessibility_access' and self.platform == 'darwin':
                    results[permission] = self._request_macos_accessibility()
                elif permission == 'admin_privileges' and self.platform == 'windows':
                    results[permission] = self._request_windows_admin()
                else:
                    results[permission] = True
            except Exception as e:
                logger.error(f"Failed to request permission {permission}: {str(e)}")
                results[permission] = False
        
        return results
    
    def _request_macos_accessibility(self) -> bool:
        """Request accessibility permissions on macOS."""
        try:
            # This would typically show a system dialog
            # For now, just log the requirement
            logger.info("Accessibility permissions required on macOS")
            return True
        except Exception as e:
            logger.error(f"Failed to request accessibility permissions: {str(e)}")
            return False
    
    def _request_windows_admin(self) -> bool:
        """Request admin privileges on Windows."""
        try:
            import ctypes
            import sys
            
            if ctypes.windll.shell32.IsUserAnAdmin():
                return True
            else:
                # Re-run the program with admin rights
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, " ".join(sys.argv), None, 1
                )
                return False
        except Exception as e:
            logger.error(f"Failed to request admin privileges: {str(e)}")
            return False
    
    def is_safe_path(self, path: str) -> bool:
        """Check if a file path is safe to access."""
        # Prevent access to sensitive system directories
        dangerous_paths = [
            '/System',
            '/usr/bin',
            '/bin',
            'C:\\Windows\\System32',
            'C:\\Program Files',
            '/etc',
            '/root'
        ]
        
        normalized_path = os.path.normpath(path)
        
        for dangerous in dangerous_paths:
            if normalized_path.startswith(dangerous):
                return False
        
        return True
    
    def is_safe_command(self, command: str) -> bool:
        """Check if a command is safe to execute."""
        # Block potentially dangerous commands
        dangerous_commands = [
            'rm -rf /',
            'format',
            'del /f /s /q',
            'sudo rm',
            'chmod 777',
            'dd if=',
            'mkfs',
            'fdisk'
        ]
        
        command_lower = command.lower().strip()
        
        for dangerous in dangerous_commands:
            if dangerous in command_lower:
                return False
        
        return True
    
    def get_command_risk_level(self, command: str, action_type: str = None) -> str:
        """Determine the risk level of a command."""
        command_lower = command.lower()
        
        # Check for dangerous patterns first
        for pattern in self.dangerous_patterns:
            if pattern in command_lower:
                return 'critical'
        
        # Check by action type
        if action_type:
            for level, actions in self.risk_levels.items():
                if action_type in actions:
                    return level
        
        # Default risk assessment based on command content
        if any(word in command_lower for word in ['delete', 'remove', 'rm ', 'del ']):
            return 'high'
        elif any(word in command_lower for word in ['create', 'mkdir', 'write']):
            return 'medium'
        else:
            return 'low'
    
    def is_path_safe(self, path: str) -> bool:
        """Check if a file path is in a safe directory."""
        try:
            abs_path = os.path.abspath(path)
            
            # Check if path is in safe directories
            for safe_dir in self.safe_directories:
                if abs_path.startswith(os.path.abspath(safe_dir)):
                    return True
            
            # Check if it's in user's home directory (generally safer)
            home_dir = str(Path.home())
            if abs_path.startswith(home_dir):
                # But not in sensitive subdirectories
                sensitive_dirs = ['.ssh', '.config', '.local', 'Library']
                for sensitive in sensitive_dirs:
                    if f'/{sensitive}/' in abs_path or abs_path.endswith(f'/{sensitive}'):
                        return False
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking path safety: {str(e)}")
            return False
    
    def needs_confirmation(self, command: str, action_type: str = None, target_path: str = None) -> Dict[str, Any]:
        """Check if a command needs user confirmation."""
        risk_level = self.get_command_risk_level(command, action_type)
        
        # Generate cache key for this command
        cache_key = hashlib.md5(f"{command}:{action_type}:{target_path}".encode()).hexdigest()
        
        # Check cache first
        if cache_key in self.confirmation_cache:
            cache_time, confirmed = self.confirmation_cache[cache_key]
            if datetime.now() - cache_time < self.cache_duration and confirmed:
                return {
                    'needs_confirmation': False,
                    'risk_level': risk_level,
                    'reason': 'Recently confirmed'
                }
        
        # Determine if confirmation is needed
        needs_confirm = False
        reason = ""
        
        if risk_level in ['high', 'critical']:
            needs_confirm = True
            reason = f"High-risk operation ({risk_level})"
        elif target_path and not self.is_path_safe(target_path):
            needs_confirm = True
            reason = "Operation on sensitive system path"
        elif any(pattern in command.lower() for pattern in self.dangerous_patterns):
            needs_confirm = True
            reason = "Command contains dangerous patterns"
        
        return {
            'needs_confirmation': needs_confirm,
            'risk_level': risk_level,
            'reason': reason,
            'cache_key': cache_key
        }
    
    def confirm_action(self, cache_key: str, confirmed: bool):
        """Store user confirmation in cache."""
        self.confirmation_cache[cache_key] = (datetime.now(), confirmed)
    
    def validate_command_execution(self, command: str, action_type: str = None, target_path: str = None) -> Dict[str, Any]:
        """Comprehensive command validation before execution."""
        try:
            # Check permissions first
            if not self.check_permissions():
                return {
                    'allowed': False,
                    'reason': 'Insufficient system permissions',
                    'requires_setup': True
                }
            
            # Check if command needs confirmation
            confirmation_info = self.needs_confirmation(command, action_type, target_path)
            
            # For now, we'll allow all commands but log the risk assessment
            # In a production environment, you might want to block high-risk commands
            # until user confirmation is implemented in the UI
            
            return {
                'allowed': True,
                'risk_level': confirmation_info['risk_level'],
                'needs_confirmation': confirmation_info['needs_confirmation'],
                'confirmation_reason': confirmation_info.get('reason', ''),
                'cache_key': confirmation_info.get('cache_key', ''),
                'warnings': self._generate_warnings(command, action_type, target_path)
            }
            
        except Exception as e:
            logger.error(f"Command validation failed: {str(e)}")
            return {
                'allowed': False,
                'reason': f'Validation error: {str(e)}'
            }
    
    def _generate_warnings(self, command: str, action_type: str = None, target_path: str = None) -> List[str]:
        """Generate security warnings for the command."""
        warnings = []
        
        command_lower = command.lower()
        
        if 'sudo' in command_lower:
            warnings.append("Command requires administrator privileges")
        
        if any(pattern in command_lower for pattern in ['rm ', 'del ', 'delete']):
            warnings.append("Command will delete files or directories")
        
        if any(pattern in command_lower for pattern in ['curl', 'wget', 'http']):
            warnings.append("Command will access the internet")
        
        if target_path and not self.is_path_safe(target_path):
            warnings.append("Operation targets sensitive system directory")
        
        return warnings
