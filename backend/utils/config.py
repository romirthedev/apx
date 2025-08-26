import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class Config:
    def __init__(self, config_file: Optional[str] = None):
        if config_file:
            self.config_file = Path(config_file)
        else:
            # Default config location
            self.config_file = Path.home() / '.cluely' / 'config.json'
        
        self.config_file.parent.mkdir(exist_ok=True)
        
        # Default configuration
        self.default_config = {
            "app": {
                "name": "Cluely",
                "version": "1.0.0",
                "debug": False,
                "auto_start": True
            },
            "server": {
                "host": "localhost",
                "port": 8889,
                "timeout": 30
            },
            "shortcuts": {
                "activate": "Cmd+Space" if os.name == 'posix' else "Ctrl+Space",
                "close": "Escape"
            },
            "ui": {
                "theme": "dark",
                "opacity": 0.95,
                "always_on_top": True,
                "start_minimized": True
            },
            "security": {
                "enable_logging": True,
                "log_file": "action_log.json",
                "max_log_entries": 1000,
                "require_confirmation": {
                    "file_deletion": True,
                    "system_commands": True,
                    "script_execution": True
                },
                "blocked_commands": [
                    "rm -rf /",
                    "format",
                    "del /f /s /q C:\\",
                    "sudo rm -rf"
                ],
                "safe_directories_only": False,
                "allowed_directories": [
                    "~/Documents",
                    "~/Downloads",
                    "~/Desktop"
                ]
            },
            "plugins": {
                "file_manager": {
                    "enabled": True,
                    "default_editor": "auto"
                },
                "app_controller": {
                    "enabled": True,
                    "app_timeout": 10
                },
                "web_controller": {
                    "enabled": True,
                    "download_directory": "~/Downloads",
                    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                },
                "script_runner": {
                    "enabled": True,
                    "timeout": 30,
                    "allowed_extensions": [".py", ".sh", ".bash", ".zsh", ".js"]
                },
                "system_info": {
                    "enabled": True
                }
            },
            "apis": {
                "gemini": {
                    "api_key": "AIzaSyAu6qCWPMMNxeaxLz_DFCk0HyjfGFSnLQ8",
                    "model": "gemini-2.5-flash",
                    "enabled": True
                },
                "weather": {
                    "provider": "",
                    "api_key": "",
                    "default_location": ""
                },
                "search": {
                    "default_engine": "google",
                    "engines": {
                        "google": "https://www.google.com/search?q=",
                        "duckduckgo": "https://duckduckgo.com/?q=",
                        "bing": "https://www.bing.com/search?q="
                    }
                }
            }
        }
        
        config_exists = self.config_file.exists()
        self.config = self.load_config()
        # Ensure Gemini API key and enabled status are set from the user's input
        self.config['apis']['gemini']['api_key'] = 'AIzaSyAu6qCWPMMNxeaxLz_DFCk0HyjfGFSnLQ8'
        self.config['apis']['gemini']['model'] = 'gemini-2.5-flash'
        self.config['apis']['gemini']['enabled'] = True
        
        # Save config only if it was newly created (i.e., did not exist before loading)
        if not config_exists:
            self.save_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                
                # Merge with defaults to ensure all keys exist
                config = self._deep_merge(self.default_config.copy(), loaded_config)
                logger.info("Configuration loaded successfully")
                return config
            else:
                # Create default config file but don't save it automatically unless explicitly told to
                logger.info("Using default configuration as file does not exist")
                return self.default_config.copy()
                
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
            logger.info("Using default configuration")
            return self.default_config.copy()
    
    def save_config(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Save configuration to file."""
        try:
            config_to_save = config or self.config
            
            with open(self.config_file, 'w') as f:
                json.dump(config_to_save, f, indent=2, sort_keys=True)
            
            logger.info("Configuration saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error saving config: {str(e)}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'server.port')."""
        try:
            keys = key.split('.')
            value = self.config
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
            
        except Exception:
            return default
    
    def set(self, key: str, value: Any) -> bool:
        """Set configuration value using dot notation."""
        try:
            keys = key.split('.')
            config = self.config
            
            # Navigate to the parent of the target key
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            # Set the value
            config[keys[-1]] = value
            
            # Save to file
            return self.save_config()
            
        except Exception as e:
            logger.error(f"Error setting config value: {str(e)}")
            return False
    
    def reset_to_defaults(self) -> bool:
        """Reset configuration to defaults."""
        try:
            self.config = self.default_config.copy()
            return self.save_config()
        except Exception as e:
            logger.error(f"Error resetting config: {str(e)}")
            return False
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get_config_file_path(self) -> str:
        """Get the path to the configuration file."""
        return str(self.config_file)
    
    def validate_config(self) -> Dict[str, str]:
        """Validate configuration and return any errors."""
        errors = {}
        
        # Validate server port
        port = self.get('server.port')
        if not isinstance(port, int) or port < 1024 or port > 65535:
            errors['server.port'] = 'Port must be an integer between 1024 and 65535'
        
        # Validate timeout values
        timeout = self.get('server.timeout')
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            errors['server.timeout'] = 'Timeout must be a positive number'
        
        # Validate plugin timeouts
        script_timeout = self.get('plugins.script_runner.timeout')
        if not isinstance(script_timeout, (int, float)) or script_timeout <= 0:
            errors['plugins.script_runner.timeout'] = 'Script timeout must be a positive number'
        
        # Validate directories
        download_dir = self.get('plugins.web_controller.download_directory')
        if download_dir:
            expanded_dir = Path(download_dir).expanduser()
            if not expanded_dir.parent.exists():
                errors['plugins.web_controller.download_directory'] = 'Download directory parent does not exist'
        
        return errors
    
    def export_config(self, file_path: str) -> bool:
        """Export configuration to a file."""
        try:
            export_path = Path(file_path)
            export_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(export_path, 'w') as f:
                json.dump(self.config, f, indent=2, sort_keys=True)
            
            logger.info(f"Configuration exported to {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting config: {str(e)}")
            return False
    
    def import_config(self, file_path: str) -> bool:
        """Import configuration from a file."""
        try:
            import_path = Path(file_path)
            
            if not import_path.exists():
                logger.error(f"Config file not found: {import_path}")
                return False
            
            with open(import_path, 'r') as f:
                imported_config = json.load(f)
            
            # Validate imported config
            if not isinstance(imported_config, dict):
                logger.error("Invalid config format")
                return False
            
            # Merge with current config
            self.config = self._deep_merge(self.config, imported_config)
            
            # Save merged config
            success = self.save_config()
            
            if success:
                logger.info(f"Configuration imported from {import_path}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error importing config: {str(e)}")
            return False
    
    def get_gemini_api_key(self) -> Optional[str]:
        """Get the Gemini API key from config or environment variable, with debug logging."""
        # First try environment variable
        api_key = os.environ.get('GEMINI_API_KEY')
        if api_key:
            logger.debug(f"Gemini API key found in environment variable: {api_key[:6]}... (truncated)")
            return api_key
        
        # Then try config file - directly access config structure first
        try:
            if 'apis' in self.config and 'gemini' in self.config['apis'] and 'api_key' in self.config['apis']['gemini']:
                api_key = self.config['apis']['gemini']['api_key']
                logger.debug(f"Gemini API key found in config['apis']['gemini']: {api_key[:6]}... (truncated)")
                return api_key
        except Exception as e:
            logger.error(f"Error accessing Gemini API key in config: {str(e)}")
        
        # Fall back to dot notation for backward compatibility
        api_key = self.get('apis.gemini.api_key')
        if api_key:
            logger.debug(f"Gemini API key found via dot notation 'apis.gemini.api_key': {api_key[:6]}... (truncated)")
            return api_key
        api_key = self.get('ai.gemini_api_key')
        if api_key:
            logger.debug(f"Gemini API key found via dot notation 'ai.gemini_api_key': {api_key[:6]}... (truncated)")
            return api_key
        api_key = self.get('api_keys.gemini')
        if api_key:
            logger.debug(f"Gemini API key found via dot notation 'api_keys.gemini': {api_key[:6]}... (truncated)")
            return api_key
        
        logger.warning("Gemini API key not found in environment or config!")
        return None
