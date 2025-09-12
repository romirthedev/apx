
import os
import shutil
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

class FileManagerTool:
    """Tool for file and directory operations."""
    
    def __init__(self, safe_directories: Optional[List[str]] = None):
        """
        Initializes the FileManagerTool.

        Args:
            safe_directories: A list of absolute paths considered safe for operations.
                              If None, defaults to user's Desktop and Documents.
        """
        if safe_directories is None:
            self.safe_directories = [os.path.expanduser("~/Desktop"), os.path.expanduser("~/Documents")]
        else:
            self.safe_directories = [os.path.abspath(d) for d in safe_directories]
            
        # Ensure all provided safe directories exist
        for d in self.safe_directories:
            if not os.path.exists(d):
                print(f"Warning: Safe directory '{d}' does not exist. It will be created if necessary by operations.")

    def _is_safe_path(self, path: str) -> bool:
        """Check if the path is within any of the safe directories."""
        try:
            abs_path = os.path.abspath(path)
            return any(abs_path.startswith(safe_dir) for safe_dir in self.safe_directories)
        except Exception as e:
            print(f"Error checking safe path '{path}': {e}")
            return False

    def _validate_path_exists(self, path: str, is_dir: bool = False, is_file: bool = False) -> bool:
        """
        Validates if a path exists and matches the expected type (directory or file).

        Args:
            path: The path to validate.
            is_dir: If True, checks if the path is a directory.
            is_file: If True, checks if the path is a file.

        Returns:
            True if the path is valid, False otherwise.
        """
        try:
            if not os.path.exists(path):
                return False
            if is_dir and not os.path.isdir(path):
                return False
            if is_file and not os.path.isfile(path):
                return False
            return True
        except Exception as e:
            print(f"Error validating path '{path}': {e}")
            return False

    def create_directory(self, path: str) -> Dict[str, Any]:
        """
        Create a new directory.

        Args:
            path: The path for the new directory.

        Returns:
            A dictionary indicating success or failure with relevant details.
        """
        if not path or not isinstance(path, str):
            return {"success": False, "error": "Invalid path provided. Path must be a non-empty string."}

        if not self._is_safe_path(path):
            return {"success": False, "error": f"Operation denied: Path '{path}' is not within a safe directory."}
        
        try:
            os.makedirs(path, exist_ok=True)
            return {
                "success": True,
                "path": os.path.abspath(path),
                "message": f"Directory created or already exists: {os.path.abspath(path)}"
            }
        except OSError as e:
            return {"success": False, "error": f"Failed to create directory '{path}': {e}"}
        except Exception as e:
            return {"success": False, "error": f"An unexpected error occurred during directory creation: {e}"}

    def list_files(self, directory: str) -> Dict[str, Any]:
        """
        List files and subdirectories within a given directory.

        Args:
            directory: The path to the directory to list.

        Returns:
            A dictionary containing the list of files/directories or an error message.
        """
        if not directory or not isinstance(directory, str):
            return {"success": False, "error": "Invalid directory provided. Directory must be a non-empty string."}

        if not self._is_safe_path(directory):
            return {"success": False, "error": f"Operation denied: Directory '{directory}' is not within a safe directory."}

        if not self._validate_path_exists(directory, is_dir=True):
            return {"success": False, "error": f"Directory not found or is not a directory: '{directory}'"}

        try:
            items = os.listdir(directory)
            files_info = []
            for item_name in items:
                item_path = os.path.join(directory, item_name)
                try:
                    if os.path.isdir(item_path):
                        files_info.append({
                            "name": item_name,
                            "type": "directory"
                        })
                    elif os.path.isfile(item_path):
                        files_info.append({
                            "name": item_name,
                            "type": "file",
                            "size": os.path.getsize(item_path)
                        })
                except OSError as e:
                    print(f"Warning: Could not access metadata for '{item_path}': {e}")
                    files_info.append({
                        "name": item_name,
                        "type": "unknown",
                        "error": f"Could not access metadata: {e}"
                    })
            
            return {
                "success": True,
                "directory": os.path.abspath(directory),
                "items": files_info,
                "count": len(files_info)
            }
        except OSError as e:
            return {"success": False, "error": f"Failed to list directory contents for '{directory}': {e}"}
        except Exception as e:
            return {"success": False, "error": f"An unexpected error occurred during directory listing: {e}"}
    
    def count_files(self, directory: str) -> Dict[str, Any]:
        """
        Counts the number of files (not directories) within a given directory.

        Args:
            directory: The path to the directory to count files in.

        Returns:
            A dictionary containing the count of files or an error message.
        """
        if not directory or not isinstance(directory, str):
            return {"success": False, "error": "Invalid directory provided. Directory must be a non-empty string."}

        if not self._is_safe_path(directory):
            return {"success": False, "error": f"Operation denied: Directory '{directory}' is not within a safe directory."}

        if not self._validate_path_exists(directory, is_dir=True):
            return {"success": False, "error": f"Directory not found or is not a directory: '{directory}'"}

        try:
            file_count = 0
            for item_name in os.listdir(directory):
                item_path = os.path.join(directory, item_name)
                if os.path.isfile(item_path):
                    file_count += 1
            
            return {
                "success": True,
                "directory": os.path.abspath(directory),
                "file_count": file_count
            }
        except OSError as e:
            return {"success": False, "error": f"Failed to count files in directory '{directory}': {e}"}
        except Exception as e:
            return {"success": False, "error": f"An unexpected error occurred during file counting: {e}"}

    def copy_file(self, source: str, destination: str) -> Dict[str, Any]:
        """
        Copy a file from source to destination.

        Args:
            source: The path to the source file.
            destination: The path to the destination file or directory.

        Returns:
            A dictionary indicating success or failure with relevant details.
        """
        if not source or not isinstance(source, str):
            return {"success": False, "error": "Invalid source path provided. Source must be a non-empty string."}
        if not destination or not isinstance(destination, str):
            return {"success": False, "error": "Invalid destination path provided. Destination must be a non-empty string."}

        if not self._is_safe_path(source):
            return {"success": False, "error": f"Operation denied: Source path '{source}' is not within a safe directory."}
        if not self._is_safe_path(destination):
            return {"success": False, "error": f"Operation denied: Destination path '{destination}' is not within a safe directory."}

        if not self._validate_path_exists(source, is_file=True):
            return {"success": False, "error": f"Source file not found or is not a file: '{source}'"}
        
        # Ensure the destination directory exists if destination is a file path
        dest_dir = os.path.dirname(destination)
        if dest_dir and not self._is_safe_path(dest_dir):
            return {"success": False, "error": f"Operation denied: Destination directory '{dest_dir}' is not within a safe directory."}
        if dest_dir and not self._validate_path_exists(dest_dir, is_dir=True):
            # Attempt to create the destination directory if it doesn't exist
            create_dir_result = self.create_directory(dest_dir)
            if not create_dir_result["success"]:
                return {"success": False, "error": f"Failed to create destination directory '{dest_dir}': {create_dir_result['error']}"}

        try:
            shutil.copy2(source, destination)
            return {
                "success": True,
                "source": os.path.abspath(source),
                "destination": os.path.abspath(destination),
                "message": f"File copied successfully from '{source}' to '{destination}'"
            }
        except OSError as e:
            return {"success": False, "error": f"Failed to copy file from '{source}' to '{destination}': {e}"}
        except Exception as e:
            return {"success": False, "error": f"An unexpected error occurred during file copy: {e}"}

    def delete_file(self, path: str) -> Dict[str, Any]:
        """
        Deletes a file.

        Args:
            path: The path to the file to delete.

        Returns:
            A dictionary indicating success or failure.
        """
        if not path or not isinstance(path, str):
            return {"success": False, "error": "Invalid path provided. Path must be a non-empty string."}
        
        if not self._is_safe_path(path):
            return {"success": False, "error": f"Operation denied: Path '{path}' is not within a safe directory."}

        if not self._validate_path_exists(path, is_file=True):
            return {"success": False, "error": f"File not found or is not a file: '{path}'"}

        try:
            os.remove(path)
            return {
                "success": True,
                "path": os.path.abspath(path),
                "message": f"File deleted successfully: {os.path.abspath(path)}"
            }
        except OSError as e:
            return {"success": False, "error": f"Failed to delete file '{path}': {e}"}
        except Exception as e:
            return {"success": False, "error": f"An unexpected error occurred during file deletion: {e}"}

    def delete_directory(self, path: str, recursive: bool = False) -> Dict[str, Any]:
        """
        Deletes a directory.

        Args:
            path: The path to the directory to delete.
            recursive: If True, deletes the directory and all its contents.
                       If False, only deletes empty directories.

        Returns:
            A dictionary indicating success or failure.
        """
        if not path or not isinstance(path, str):
            return {"success": False, "error": "Invalid path provided. Path must be a non-empty string."}
        
        if not self._is_safe_path(path):
            return {"success": False, "error": f"Operation denied: Path '{path}' is not within a safe directory."}

        if not self._validate_path_exists(path, is_dir=True):
            return {"success": False, "error": f"Directory not found or is not a directory: '{path}'"}

        try:
            if recursive:
                shutil.rmtree(path)
                message = f"Directory and its contents deleted recursively: {os.path.abspath(path)}"
            else:
                os.rmdir(path)
                message = f"Empty directory deleted: {os.path.abspath(path)}"
            
            return {
                "success": True,
                "path": os.path.abspath(path),
                "message": message
            }
        except OSError as e:
            if not recursive and "Directory not empty" in str(e):
                return {"success": False, "error": f"Directory '{path}' is not empty. Use recursive=True to delete it and its contents. Error: {e}"}
            return {"success": False, "error": f"Failed to delete directory '{path}': {e}"}
        except Exception as e:
            return {"success": False, "error": f"An unexpected error occurred during directory deletion: {e}"}

