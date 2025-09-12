
import os
import shutil
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

class FileManagerTool:
    """Tool for file and directory operations."""

    def __init__(self):
        self.safe_directories = [os.path.expanduser("~/Desktop"), os.path.expanduser("~/Documents"), os.path.expanduser("~/Downloads")]

    def _is_safe_path(self, path: str) -> bool:
        """Check if the path is in a safe directory."""
        if not path:
            return False
        try:
            abs_path = os.path.abspath(path)
            return any(abs_path.startswith(os.path.abspath(safe_dir)) for safe_dir in self.safe_directories)
        except Exception:
            return False

    def _validate_path_exists(self, path: str, is_directory: bool = False):
        """Validate if a path exists and is of the expected type."""
        if not path:
            raise ValueError("Path cannot be empty.")
        
        abs_path = os.path.abspath(path)
        
        if is_directory:
            if not os.path.isdir(abs_path):
                raise FileNotFoundError(f"Directory not found: {path}")
        else:
            if not os.path.exists(abs_path):
                raise FileNotFoundError(f"File or directory not found: {path}")
        
        return abs_path

    def create_directory(self, path: str) -> Dict[str, Any]:
        """Create a new directory."""
        try:
            if not path:
                return {"success": False, "error": "Directory path cannot be empty."}
                
            abs_path = self._validate_path_exists(path, is_directory=False)
            
            if not self._is_safe_path(abs_path):
                return {"success": False, "error": f"Operation not permitted. Path '{path}' is not within a safe directory."}
            
            os.makedirs(abs_path, exist_ok=True)
            return {
                "success": True,
                "path": abs_path,
                "message": f"Directory created: {abs_path}"
            }
        except FileNotFoundError as e:
            return {"success": False, "error": str(e)}
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": f"An unexpected error occurred: {str(e)}"}

    def list_files(self, directory: str) -> Dict[str, Any]:
        """List files in a directory with their sizes."""
        try:
            if not directory:
                return {"success": False, "error": "Directory path cannot be empty."}
                
            abs_directory = self._validate_path_exists(directory, is_directory=True)
            
            if not self._is_safe_path(abs_directory):
                return {"success": False, "error": f"Operation not permitted. Directory '{directory}' is not within a safe directory."}
            
            files_info = []
            for item_name in os.listdir(abs_directory):
                item_path = os.path.join(abs_directory, item_name)
                if os.path.isfile(item_path):
                    try:
                        size = os.path.getsize(item_path)
                        files_info.append({
                            "name": item_name,
                            "type": "file",
                            "size": size
                        })
                    except OSError:
                        # Handle cases where file size cannot be retrieved (e.g., permissions)
                        files_info.append({
                            "name": item_name,
                            "type": "file",
                            "size": None,
                            "error": "Could not retrieve file size."
                        })
                elif os.path.isdir(item_path):
                    files_info.append({
                        "name": item_name,
                        "type": "directory",
                        "size": None
                    })
            
            return {
                "success": True,
                "directory": abs_directory,
                "files": files_info,
                "count": len(files_info)
            }
        except FileNotFoundError as e:
            return {"success": False, "error": str(e)}
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": f"An unexpected error occurred: {str(e)}"}

    def find_largest_file(self, directory: str) -> Dict[str, Any]:
        """Find the largest file in a specified directory."""
        try:
            if not directory:
                return {"success": False, "error": "Directory path cannot be empty."}
                
            abs_directory = self._validate_path_exists(directory, is_directory=True)
            
            if not self._is_safe_path(abs_directory):
                return {"success": False, "error": f"Operation not permitted. Directory '{directory}' is not within a safe directory."}
            
            largest_file = None
            max_size = -1

            for item_name in os.listdir(abs_directory):
                item_path = os.path.join(abs_directory, item_name)
                if os.path.isfile(item_path):
                    try:
                        size = os.path.getsize(item_path)
                        if size > max_size:
                            max_size = size
                            largest_file = {
                                "name": item_name,
                                "path": item_path,
                                "size": size
                            }
                    except OSError:
                        # Skip files for which size cannot be retrieved
                        continue
            
            if largest_file:
                return {
                    "success": True,
                    "message": f"Largest file found in '{abs_directory}'.",
                    "file": largest_file
                }
            else:
                return {
                    "success": True,
                    "message": f"No files found in '{abs_directory}' or could not determine file sizes.",
                    "file": None
                }
        except FileNotFoundError as e:
            return {"success": False, "error": str(e)}
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": f"An unexpected error occurred: {str(e)}"}

    def copy_file(self, source: str, destination: str) -> Dict[str, Any]:
        """Copy a file from source to destination."""
        try:
            if not source:
                return {"success": False, "error": "Source file path cannot be empty."}
            if not destination:
                return {"success": False, "error": "Destination path cannot be empty."}
                
            abs_source = self._validate_path_exists(source, is_directory=False)
            abs_destination = self._validate_path_exists(destination, is_directory=False)
            
            if not self._is_safe_path(abs_source):
                return {"success": False, "error": f"Operation not permitted. Source file '{source}' is not within a safe directory."}

            # For destination, we need to check if the parent directory is safe, or if it's a file path within a safe directory.
            dest_dir = os.path.dirname(abs_destination)
            if not dest_dir: # If destination is a file name in current directory
                dest_dir = os.getcwd()

            if not self._is_safe_path(dest_dir):
                return {"success": False, "error": f"Operation not permitted. Destination path '{destination}' is not within a safe directory."}

            shutil.copy2(abs_source, abs_destination)
            return {
                "success": True,
                "source": abs_source,
                "destination": abs_destination,
                "message": f"File copied from '{abs_source}' to '{abs_destination}'"
            }
        except FileNotFoundError as e:
            return {"success": False, "error": str(e)}
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except OSError as e:
            return {"success": False, "error": f"File system error during copy: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"An unexpected error occurred: {str(e)}"}

