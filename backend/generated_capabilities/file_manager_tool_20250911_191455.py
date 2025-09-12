
import os
import shutil
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

class FileManagerTool:
    """Tool for file and directory operations, including file counting."""

    def __init__(self):
        self.safe_directories = [os.path.expanduser("~/Desktop"), os.path.expanduser("~/Documents")]
        # Ensure safe directories exist
        for safe_dir in self.safe_directories:
            os.makedirs(safe_dir, exist_ok=True)

    def _is_safe_path(self, path: str) -> bool:
        """Check if the path is in a safe directory."""
        if not path:
            return False
        try:
            abs_path = os.path.abspath(path)
            return any(abs_path.startswith(os.path.abspath(safe_dir)) for safe_dir in self.safe_directories)
        except Exception:
            return False

    def _validate_directory(self, directory: str) -> Dict[str, Any]:
        """Validates if a given path is a directory and is safe."""
        if not directory:
            return {"success": False, "error": "Directory path cannot be empty."}
        if not self._is_safe_path(directory):
            return {"success": False, "error": f"Access denied: '{directory}' is not within a permitted safe directory."}
        if not os.path.isdir(directory):
            return {"success": False, "error": f"Invalid path: '{directory}' is not a directory or does not exist."}
        return {"success": True}

    def create_directory(self, path: str) -> Dict[str, Any]:
        """Create a new directory.

        Args:
            path: The path for the new directory.

        Returns:
            A dictionary indicating success or failure with details.
        """
        if not path:
            return {"success": False, "error": "Directory path cannot be empty."}

        if not self._is_safe_path(path):
            return {"success": False, "error": f"Access denied: '{path}' is not within a permitted safe directory."}

        try:
            os.makedirs(path, exist_ok=True)
            return {
                "success": True,
                "path": path,
                "message": f"Directory created successfully: '{path}'"
            }
        except OSError as e:
            return {"success": False, "error": f"OS error creating directory '{path}': {e}"}
        except Exception as e:
            return {"success": False, "error": f"An unexpected error occurred while creating directory '{path}': {e}"}

    def list_files(self, directory: str) -> Dict[str, Any]:
        """List files and subdirectories in a given directory.

        Args:
            directory: The path to the directory to list.

        Returns:
            A dictionary containing a list of files and directories, their types, sizes, and a count.
        """
        validation_result = self._validate_directory(directory)
        if not validation_result["success"]:
            return validation_result

        try:
            items = []
            for item_name in os.listdir(directory):
                item_path = os.path.join(directory, item_name)
                item_info: Dict[str, Any] = {
                    "name": item_name,
                    "type": "directory" if os.path.isdir(item_path) else "file",
                }
                if item_info["type"] == "file":
                    try:
                        item_info["size"] = os.path.getsize(item_path)
                    except OSError:
                        item_info["size"] = None # Handle cases where size cannot be retrieved
                items.append(item_info)

            return {
                "success": True,
                "directory": directory,
                "files": items,
                "count": len(items)
            }
        except OSError as e:
            return {"success": False, "error": f"OS error listing directory '{directory}': {e}"}
        except Exception as e:
            return {"success": False, "error": f"An unexpected error occurred while listing directory '{directory}': {e}"}

    def count_files(self, directory: str, recursive: bool = False) -> Dict[str, Any]:
        """Count the number of files in a given directory.

        Args:
            directory: The path to the directory to count files in.
            recursive: If True, counts files in subdirectories as well.

        Returns:
            A dictionary with the total count of files.
        """
        validation_result = self._validate_directory(directory)
        if not validation_result["success"]:
            return validation_result

        file_count = 0
        try:
            if recursive:
                for root, _, files in os.walk(directory):
                    # Ensure we are still within a safe path if walking recursively
                    if not self._is_safe_path(root):
                        return {"success": False, "error": f"Access denied during recursive scan: '{root}' is not within a permitted safe directory."}
                    file_count += len(files)
            else:
                for item_name in os.listdir(directory):
                    item_path = os.path.join(directory, item_name)
                    if os.path.isfile(item_path):
                        file_count += 1

            return {
                "success": True,
                "directory": directory,
                "recursive": recursive,
                "file_count": file_count
            }
        except OSError as e:
            return {"success": False, "error": f"OS error counting files in '{directory}': {e}"}
        except Exception as e:
            return {"success": False, "error": f"An unexpected error occurred while counting files in '{directory}': {e}"}

    def copy_file(self, source: str, destination: str) -> Dict[str, Any]:
        """Copy a file from source to destination.

        Args:
            source: The path to the source file.
            destination: The path to the destination.

        Returns:
            A dictionary indicating success or failure with details.
        """
        if not source or not destination:
            return {"success": False, "error": "Source and destination paths cannot be empty."}

        if not self._is_safe_path(source):
            return {"success": False, "error": f"Access denied: Source path '{source}' is not within a permitted safe directory."}
        if not self._is_safe_path(destination):
            return {"success": False, "error": f"Access denied: Destination path '{destination}' is not within a permitted safe directory."}

        if not os.path.isfile(source):
            return {"success": False, "error": f"Invalid source: '{source}' is not a file or does not exist."}

        try:
            # Ensure destination directory exists
            dest_dir = os.path.dirname(destination)
            if dest_dir and not os.path.exists(dest_dir):
                create_dir_result = self.create_directory(dest_dir)
                if not create_dir_result["success"]:
                    return create_dir_result # Return error from create_directory

            shutil.copy2(source, destination)
            return {
                "success": True,
                "source": source,
                "destination": destination,
                "message": f"File copied successfully from '{source}' to '{destination}'"
            }
        except OSError as e:
            return {"success": False, "error": f"OS error copying file from '{source}' to '{destination}': {e}"}
        except Exception as e:
            return {"success": False, "error": f"An unexpected error occurred while copying file from '{source}' to '{destination}': {e}"}

    def delete_file(self, file_path: str) -> Dict[str, Any]:
        """Delete a file.

        Args:
            file_path: The path to the file to delete.

        Returns:
            A dictionary indicating success or failure.
        """
        if not file_path:
            return {"success": False, "error": "File path cannot be empty."}

        if not self._is_safe_path(file_path):
            return {"success": False, "error": f"Access denied: File path '{file_path}' is not within a permitted safe directory."}

        if not os.path.isfile(file_path):
            return {"success": False, "error": f"Invalid path: '{file_path}' is not a file or does not exist."}

        try:
            os.remove(file_path)
            return {
                "success": True,
                "file_path": file_path,
                "message": f"File deleted successfully: '{file_path}'"
            }
        except OSError as e:
            return {"success": False, "error": f"OS error deleting file '{file_path}': {e}"}
        except Exception as e:
            return {"success": False, "error": f"An unexpected error occurred while deleting file '{file_path}': {e}"}

    def delete_directory(self, directory_path: str) -> Dict[str, Any]:
        """Delete a directory and its contents.

        Args:
            directory_path: The path to the directory to delete.

        Returns:
            A dictionary indicating success or failure.
        """
        if not directory_path:
            return {"success": False, "error": "Directory path cannot be empty."}

        if not self._is_safe_path(directory_path):
            return {"success": False, "error": f"Access denied: Directory path '{directory_path}' is not within a permitted safe directory."}

        if not os.path.isdir(directory_path):
            return {"success": False, "error": f"Invalid path: '{directory_path}' is not a directory or does not exist."}

        # Optional: Add a confirmation step or a warning for deleting directories
        # For safety, let's prevent deleting the root of safe directories unless explicitly allowed with a flag
        if os.path.abspath(directory_path) in [os.path.abspath(sd) for sd in self.safe_directories]:
             return {"success": False, "error": "Deletion of root safe directories is not allowed for safety reasons."}


        try:
            shutil.rmtree(directory_path)
            return {
                "success": True,
                "directory_path": directory_path,
                "message": f"Directory deleted successfully: '{directory_path}'"
            }
        except OSError as e:
            return {"success": False, "error": f"OS error deleting directory '{directory_path}': {e}"}
        except Exception as e:
            return {"success": False, "error": f"An unexpected error occurred while deleting directory '{directory_path}': {e}"}
