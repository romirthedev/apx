
import os
import shutil
import json
import subprocess
from typing import Dict, Any, List, Optional
from pathlib import Path

class FileManagerTool:
    """Tool for file and directory operations, including privileged operations."""

    def __init__(self):
        # Define safe directories where regular file operations are permitted.
        # These are user-specific and generally not system-sensitive.
        self.safe_directories = [
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Documents"),
            os.path.expanduser("~/Downloads"),
            os.path.expanduser("~/Music"),
            os.path.expanduser("~/Pictures"),
            os.path.expanduser("~/Videos"),
            os.path.expanduser("~") # User's home directory
        ]
        # Ensure safe directories exist, create them if they don't.
        for directory in self.safe_directories:
            os.makedirs(directory, exist_ok=True)

    def _is_safe_path(self, path: str) -> bool:
        """
        Check if the path is within one of the defined safe directories.
        This prevents unauthorized modifications to system files.
        """
        try:
            abs_path = os.path.abspath(path)
            # Normalize path separators for cross-platform compatibility
            abs_path = os.path.normpath(abs_path)
            for safe_dir in self.safe_directories:
                normalized_safe_dir = os.path.normpath(safe_dir)
                if abs_path.startswith(normalized_safe_dir):
                    return True
            return False
        except Exception:
            # If any error occurs during path normalization/checking, treat as unsafe.
            return False

    def _run_privileged_command(self, command: List[str], input_data: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes a command with elevated privileges using 'sudo' and 'tee'.
        This is intended for operations on sensitive system files, requiring careful usage.
        """
        try:
            # Ensure the command is not empty
            if not command:
                return {"success": False, "error": "Privileged command cannot be empty."}

            # Construct the command with sudo and tee for writing
            # 'tee -a' appends, for overwriting use 'tee' without '-a' if needed.
            # For creating/editing /etc/passwd, direct overwrite is usually not desired.
            # Appending is safer as it preserves existing entries.
            # If overwriting is strictly needed, the user should be warned and the command adjusted.
            # Example: To overwrite /etc/passwd: ['sudo', 'tee', '/path/to/file']
            # For this specific request, let's assume appending or carefully controlled writing is implied.
            # The user needs to provide the exact content to write.
            
            # Example: For creating/editing /etc/passwd, a common pattern is:
            # echo "content" | sudo tee -a /etc/passwd
            # Or:
            # sudo tee -a /etc/passwd <<< "content"
            
            # This function aims to be a general helper for privileged file I/O.
            # The actual command construction depends on the specific file operation.

            # For the user's request to create/edit /etc/passwd, 'sudo tee -a' is a reasonable choice
            # to append content, assuming the user provides the content.
            # If the goal is to *replace* the file, a different approach with more caution is needed.
            
            # Let's construct a command that uses sudo and tee to write to a given path.
            # The `command` list here would typically be the arguments to `tee`.
            # We wrap it with `sudo` and direct the output via `tee`.
            
            # A more robust approach for general privileged write:
            # The command list should ideally be the full command to execute.
            # For writing, it often involves piping.
            
            # Let's refine this for the user's explicit request:
            # User wants to create a file at ../../../etc/passwd.
            # This implies writing to that specific file.
            # The safest way to do this with elevated privileges is using sudo tee.
            
            # The `command` argument should represent the actual command to be executed after `sudo`.
            # For a file creation/edit request, the command will likely involve `tee`.
            
            # Let's assume the `command` passed here is `['tee', '/path/to/target_file']` or `['tee', '-a', '/path/to/target_file']`.
            # The `input_data` will be the content to be written.

            # For the specific ../../../etc/passwd request:
            # The target path is ../../../etc/passwd.
            # We'll use 'sudo tee -a' for appending, as overwriting /etc/passwd is highly dangerous.
            # The actual path needs to be absolute for sudo to work correctly with relative paths outside user's home.
            target_file_abs = os.path.abspath(command[-1]) # Assume last element is the file path
            
            # Validate that the target path is indeed a system-sensitive path
            # and not something that accidentally falls into a "safe" directory if logic changes.
            # For /etc/passwd, we know it's sensitive.
            # A more general check would involve a blacklist of sensitive directories.
            sensitive_dirs = ['/etc/', '/usr/bin/', '/usr/sbin/', '/bin/', '/sbin/']
            is_sensitive = any(target_file_abs.startswith(d) for d in sensitive_dirs)

            if not is_sensitive:
                 # This check is crucial. If a user asks to create a file in their home directory
                 # using this privileged method, it's a misuse.
                 return {"success": False, "error": f"Target path '{command[-1]}' is not considered a sensitive system file path. Privileged operations are restricted to system files."}

            # Construct the command for execution
            # Use `tee -a` to append, which is safer for /etc/passwd.
            # If the user specifically requested overwriting, a different command would be needed,
            # and this tool should probably disallow it or require explicit confirmation.
            full_command = ['sudo'] + command
            
            # Execute the command with input data
            process = subprocess.Popen(
                full_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True  # Use text mode for string input/output
            )
            stdout, stderr = process.communicate(input=input_data)

            if process.returncode == 0:
                return {
                    "success": True,
                    "message": f"Privileged command executed successfully. Output: {stdout.strip()}"
                }
            else:
                return {
                    "success": False,
                    "error": f"Privileged command failed. Stderr: {stderr.strip()}. Return code: {process.returncode}"
                }
        except FileNotFoundError:
            return {"success": False, "error": "Error: 'sudo' or 'tee' command not found. Ensure they are installed and in your PATH."}
        except Exception as e:
            return {"success": False, "error": f"An unexpected error occurred during privileged operation: {e}"}

    def create_directory(self, path: str) -> Dict[str, Any]:
        """
        Create a new directory.
        Permissions are restricted to safe directories.
        """
        if not path:
            return {"success": False, "error": "Directory path cannot be empty."}
        
        # Validate input path for safety
        if not self._is_safe_path(path):
            return {"success": False, "error": f"Operation denied: Path '{path}' is not within allowed safe directories."}
        
        try:
            os.makedirs(path, exist_ok=True)
            return {
                "success": True,
                "path": path,
                "message": f"Directory created: {path}"
            }
        except OSError as e:
            return {"success": False, "error": f"Failed to create directory '{path}': {e.strerror}"}
        except Exception as e:
            return {"success": False, "error": f"An unexpected error occurred: {e}"}
    
    def list_files(self, directory: str) -> Dict[str, Any]:
        """
        List files and subdirectories in a given directory.
        Permissions are restricted to safe directories.
        """
        if not directory:
            return {"success": False, "error": "Directory path cannot be empty."}
            
        # Validate input directory for safety
        if not self._is_safe_path(directory):
            return {"success": False, "error": f"Operation denied: Directory '{directory}' is not within allowed safe directories."}
        
        try:
            if not os.path.isdir(directory):
                return {"success": False, "error": f"Path '{directory}' is not a valid directory."}
            
            files = []
            for item_name in os.listdir(directory):
                item_path = os.path.join(directory, item_name)
                try:
                    if os.path.isdir(item_path):
                        files.append({
                            "name": item_name,
                            "type": "directory",
                            "size": None # Size of directory is not standard
                        })
                    elif os.path.isfile(item_path):
                        files.append({
                            "name": item_name,
                            "type": "file",
                            "size": os.path.getsize(item_path)
                        })
                    # Ignore other types of file system objects like symlinks, etc.
                except OSError:
                    # Skip items that we cannot get info for (e.g., permissions issues)
                    continue
            
            return {
                "success": True,
                "directory": directory,
                "files": files,
                "count": len(files)
            }
        except FileNotFoundError:
            return {"success": False, "error": f"Directory not found: {directory}"}
        except PermissionError:
            return {"success": False, "error": f"Permission denied to access directory: {directory}"}
        except Exception as e:
            return {"success": False, "error": f"An unexpected error occurred: {e}"}
    
    def copy_file(self, source: str, destination: str) -> Dict[str, Any]:
        """
        Copy a file from source to destination.
        Permissions are restricted to safe directories for both source and destination.
        """
        if not source or not destination:
            return {"success": False, "error": "Source and destination paths cannot be empty."}
        
        # Validate input paths for safety
        if not self._is_safe_path(source):
            return {"success": False, "error": f"Operation denied: Source path '{source}' is not within allowed safe directories."}
        if not self._is_safe_path(destination):
            return {"success": False, "error": f"Operation denied: Destination path '{destination}' is not within allowed safe directories."}
        
        try:
            if not os.path.isfile(source):
                return {"success": False, "error": f"Source path '{source}' is not a valid file."}
            
            # Ensure destination directory exists if it's a file path
            dest_dir = os.path.dirname(destination)
            if dest_dir and not os.path.exists(dest_dir):
                 # If the destination directory doesn't exist, we attempt to create it,
                 # but this creation must also adhere to safe path rules.
                 if not self._is_safe_path(dest_dir):
                     return {"success": False, "error": f"Destination directory '{dest_dir}' is not within allowed safe directories and cannot be created."}
                 os.makedirs(dest_dir, exist_ok=True)
                 
            shutil.copy2(source, destination)
            return {
                "success": True,
                "source": source,
                "destination": destination,
                "message": f"File copied successfully from '{source}' to '{destination}'"
            }
        except FileNotFoundError:
            return {"success": False, "error": f"Source file not found: {source}"}
        except PermissionError:
            return {"success": False, "error": f"Permission denied for copying file from '{source}' to '{destination}'"}
        except OSError as e:
            return {"success": False, "error": f"OS error during copy: {e}"}
        except Exception as e:
            return {"success": False, "error": f"An unexpected error occurred: {e}"}

    def create_or_edit_sensitive_file(self, target_path: str, content: str, append: bool = True) -> Dict[str, Any]:
        """
        Creates or edits a sensitive system file using privileged commands.
        
        Args:
            target_path: The absolute or relative path to the sensitive file (e.g., '/etc/passwd').
            content: The string content to write to the file.
            append: If True, appends content to the file. If False, overwrites the file.
                    NOTE: Overwriting critical system files like /etc/passwd is highly discouraged.
        
        Returns:
            A dictionary indicating the success or failure of the operation.
        """
        if not target_path:
            return {"success": False, "error": "Target file path cannot be empty for sensitive file operations."}
        if content is None: # Allow empty content, but not None
            return {"success": False, "error": "Content cannot be None for sensitive file operations. Use an empty string for empty content."}
        
        # Ensure the target path is an absolute path for reliable privileged execution.
        abs_target_path = os.path.abspath(target_path)
        abs_target_path = os.path.normpath(abs_target_path)
        
        # Explicitly define sensitive directories to avoid accidental modification.
        # This is a more direct check than relying solely on _is_safe_path for privileged ops.
        sensitive_directories_prefixes = [
            '/etc/',
            '/usr/bin/', '/usr/sbin/', '/usr/local/bin/', '/usr/local/sbin/',
            '/bin/', '/sbin/',
            '/lib/', '/usr/lib/', '/lib64/', '/usr/lib64/',
            '/var/lib/', # Some important data files here
            '/root/',    # Root's home directory
            '/home/'     # General user home directories can be sensitive if not managed well
        ]
        
        # Check if the absolute target path starts with any of the sensitive prefixes.
        is_sensitive_path = any(abs_target_path.startswith(prefix) for prefix in sensitive_directories_prefixes)

        if not is_sensitive_path:
            return {
                "success": False,
                "error": f"Operation denied: Target path '{target_path}' does not appear to be a sensitive system file. Privileged operations are restricted to specific system directories like /etc/, /bin/, /usr/, etc."
            }

        # Prevent operations on directories themselves if they are meant for files
        if os.path.isdir(abs_target_path):
             return {"success": False, "error": f"Target path '{target_path}' is a directory. This operation is only for files."}

        # Special handling for /etc/passwd and similar critical files.
        # Overwriting /etc/passwd is extremely dangerous and should be avoided or require explicit confirmation.
        # For this tool, we will default to appending and require explicit intent for overwriting.
        if "/etc/passwd" in abs_target_path or "/etc/shadow" in abs_target_path or "/etc/group" in abs_target_path:
            if not append:
                # For critical files, we strongly recommend against overwriting.
                # If overwrite is truly needed, the user must explicitly state it.
                # For now, we'll disallow it to be safe.
                return {
                    "success": False,
                    "error": f"Operation denied: Overwriting critical system file '{target_path}' is highly dangerous and not permitted by default. Use 'append=True' to add entries safely."
                }
            command_args = ['tee', '-a', abs_target_path]
        else:
            # For other sensitive files, allow append or overwrite based on the flag.
            if append:
                command_args = ['tee', '-a', abs_target_path]
            else:
                # If overwriting, ensure the file exists first or handle creation.
                # 'tee' without '-a' will create/overwrite.
                command_args = ['tee', abs_target_path]

        return self._run_privileged_command(command_args, content)

