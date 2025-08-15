import json
import logging
import os
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ActionLogger:
    def __init__(self, log_file: str = "action_log.json"):
        self.log_file = log_file
        self.ensure_log_file_exists()
    
    def ensure_log_file_exists(self):
        """Ensure the log file exists."""
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w') as f:
                json.dump([], f)
    
    def log_action(self, command: str, result: str, success: bool, metadata: Dict[str, Any] = None):
        """Log an action to the action log file."""
        try:
            action_entry = {
                'timestamp': datetime.now().isoformat(),
                'command': command,
                'result': result,
                'success': success,
                'metadata': metadata or {}
            }
            
            # Read existing logs
            with open(self.log_file, 'r') as f:
                logs = json.load(f)
            
            # Add new entry
            logs.append(action_entry)
            
            # Keep only last 1000 entries
            if len(logs) > 1000:
                logs = logs[-1000:]
            
            # Write back to file
            with open(self.log_file, 'w') as f:
                json.dump(logs, f, indent=2)
            
            logger.info(f"Logged action: {command} -> {success}")
            
        except Exception as e:
            logger.error(f"Failed to log action: {str(e)}")
    
    def get_recent_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent log entries."""
        try:
            with open(self.log_file, 'r') as f:
                logs = json.load(f)
            
            return logs[-limit:] if logs else []
            
        except Exception as e:
            logger.error(f"Failed to retrieve logs: {str(e)}")
            return []
    
    def clear_logs(self):
        """Clear all log entries."""
        try:
            with open(self.log_file, 'w') as f:
                json.dump([], f)
            logger.info("Cleared action logs")
        except Exception as e:
            logger.error(f"Failed to clear logs: {str(e)}")
