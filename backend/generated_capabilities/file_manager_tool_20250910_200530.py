
import os
import shutil
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from PIL import Image
import qrcode

class FileManagerTool:
    """Tool for file and directory operations and QR code generation with logos."""

    def __init__(self):
        # Define safe directories where files and directories can be created/modified
        self.safe_directories = [
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Documents"),
            os.path.expanduser("~") # Allow operations in the user's home directory
        ]
        # Ensure safe directories exist
        for directory in self.safe_directories:
            os.makedirs(directory, exist_ok=True)

    def _is_safe_path(self, path: str) -> bool:
        """Check if the path is within a safe directory or is the safe directory itself."""
        try:
            abs_path = os.path.abspath(path)
            # Check if the absolute path is directly within or is one of the safe directories
            for safe_dir in self.safe_directories:
                abs_safe_dir = os.path.abspath(safe_dir)
                if abs_path == abs_safe_dir or abs_path.startswith(abs_safe_dir + os.sep):
                    return True
            return False
        except Exception:
            # If any error occurs during path resolution, consider it unsafe
            return False

    def create_directory(self, path: str) -> Dict[str, Any]:
        """
        Create a new directory.

        Args:
            path: The path of the directory to create.

        Returns:
            A dictionary with operation status, path, and message or error.
        """
        if not path:
            return {"success": False, "error": "Directory path cannot be empty."}

        try:
            if not self._is_safe_path(path):
                return {"success": False, "error": f"Path '{path}' is not in a safe directory. Allowed directories are: {self.safe_directories}"}

            os.makedirs(path, exist_ok=True)
            return {
                "success": True,
                "path": os.path.abspath(path),
                "message": f"Directory created or already exists: {os.path.abspath(path)}"
            }
        except OSError as e:
            return {"success": False, "error": f"Failed to create directory '{path}': {e}"}
        except Exception as e:
            return {"success": False, "error": f"An unexpected error occurred while creating directory '{path}': {e}"}

    def list_files(self, directory: str) -> Dict[str, Any]:
        """
        List files and subdirectories in a given directory.

        Args:
            directory: The path of the directory to list.

        Returns:
            A dictionary with operation status, directory path, file list, and count, or an error.
        """
        if not directory:
            return {"success": False, "error": "Directory path cannot be empty."}

        try:
            if not self._is_safe_path(directory):
                return {"success": False, "error": f"Path '{directory}' is not in a safe directory. Allowed directories are: {self.safe_directories}"}

            if not os.path.isdir(directory):
                return {"success": False, "error": f"Path '{directory}' is not a valid directory."}

            items_list = []
            for item_name in os.listdir(directory):
                item_path = os.path.join(directory, item_name)
                item_info = {"name": item_name}
                if os.path.isdir(item_path):
                    item_info["type"] = "directory"
                elif os.path.isfile(item_path):
                    item_info["type"] = "file"
                    try:
                        item_info["size"] = os.path.getsize(item_path)
                    except OSError:
                        item_info["size"] = None # Handle potential errors in getting size
                else:
                    item_info["type"] = "other" # For symbolic links, etc.

                items_list.append(item_info)

            return {
                "success": True,
                "directory": os.path.abspath(directory),
                "files": items_list,
                "count": len(items_list)
            }
        except OSError as e:
            return {"success": False, "error": f"Failed to list files in directory '{directory}': {e}"}
        except Exception as e:
            return {"success": False, "error": f"An unexpected error occurred while listing files in '{directory}': {e}"}

    def copy_file(self, source: str, destination: str) -> Dict[str, Any]:
        """
        Copy a file from a source path to a destination path.

        Args:
            source: The path of the file to copy.
            destination: The path to copy the file to.

        Returns:
            A dictionary with operation status, source, destination, and message, or an error.
        """
        if not source:
            return {"success": False, "error": "Source file path cannot be empty."}
        if not destination:
            return {"success": False, "error": "Destination path cannot be empty."}

        try:
            # Validate source and destination paths
            if not self._is_safe_path(source):
                return {"success": False, "error": f"Source path '{source}' is not in a safe directory. Allowed directories are: {self.safe_directories}"}
            if not self._is_safe_path(destination):
                return {"success": False, "error": f"Destination path '{destination}' is not in a safe directory. Allowed directories are: {self.safe_directories}"}

            # Ensure source is a file
            if not os.path.isfile(source):
                return {"success": False, "error": f"Source path '{source}' is not a file."}

            # If destination is a directory, append source filename to it
            if os.path.isdir(destination):
                destination_path = os.path.join(destination, os.path.basename(source))
            else:
                destination_path = destination

            # Ensure the directory for the destination exists
            dest_dir = os.path.dirname(destination_path)
            if dest_dir and not os.path.exists(dest_dir):
                create_dir_result = self.create_directory(dest_dir)
                if not create_dir_result["success"]:
                    return create_dir_result # Propagate error from create_directory

            shutil.copy2(source, destination_path)
            return {
                "success": True,
                "source": os.path.abspath(source),
                "destination": os.path.abspath(destination_path),
                "message": f"File copied successfully from '{source}' to '{destination_path}'"
            }
        except FileNotFoundError:
            return {"success": False, "error": f"Source file not found at '{source}'."}
        except OSError as e:
            return {"success": False, "error": f"Failed to copy file from '{source}' to '{destination}': {e}"}
        except Exception as e:
            return {"success": False, "error": f"An unexpected error occurred while copying file '{source}': {e}"}

    def generate_qr_code_with_logo(self, data: str, output_path: str, logo_path: Optional[str] = None, qr_version: int = 1, qr_error_correction=qrcode.constants.ERROR_CORRECT_H, box_size: int = 10, border: int = 4) -> Dict[str, Any]:
        """
        Generate a QR code with an optional custom logo and save it as a PNG file.

        Args:
            data: The data to encode in the QR code (e.g., URL, text).
            output_path: The full path (including filename) to save the PNG QR code.
            logo_path: Optional. The path to the logo image file (e.g., PNG, JPG).
            qr_version: The version of the QR code (1 to 40). Higher means more data capacity.
            qr_error_correction: The error correction level (L, M, Q, H). H is highest.
            box_size: Controls how many pixels each "box" of the QR code is.
            border: Controls how many boxes thick the border should be.

        Returns:
            A dictionary with operation status, output path, and message, or an error.
        """
        if not data:
            return {"success": False, "error": "QR code data cannot be empty."}
        if not output_path:
            return {"success": False, "error": "Output path for QR code cannot be empty."}

        try:
            # Validate output path
            output_dir = os.path.dirname(output_path)
            if output_dir and not self._is_safe_path(output_dir):
                return {"success": False, "error": f"Output directory '{output_dir}' is not in a safe directory. Allowed directories are: {self.safe_directories}"}
            if not output_path.lower().endswith(".png"):
                return {"success": False, "error": "Output path must end with '.png' for PNG image format."}

            # Create QR code instance
            qr = qrcode.QRCode(
                version=qr_version,
                error_correction=qr_error_correction,
                box_size=box_size,
                border=border,
            )
            qr.add_data(data)
            qr.make(fit=True)

            # Create QR code image
            qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')

            # Embed logo if provided
            if logo_path:
                if not os.path.exists(logo_path):
                    return {"success": False, "error": f"Logo file not found at '{logo_path}'."}
                if not self._is_safe_path(logo_path):
                    return {"success": False, "error": f"Logo path '{logo_path}' is not in a safe directory. Allowed directories are: {self.safe_directories}"}

                try:
                    logo_img = Image.open(logo_path).convert('RGBA') # Ensure logo has alpha channel if present
                except Exception as e:
                    return {"success": False, "error": f"Failed to open logo image '{logo_path}': {e}"}

                # Calculate logo size to fit within QR code (e.g., 1/5th of QR code size)
                qr_width, qr_height = qr_img.size
                max_logo_size = qr_width // 5 # Adjust this ratio as needed
                logo_img.thumbnail((max_logo_size, max_logo_size))

                # Calculate position to center the logo
                logo_width, logo_height = logo_img.size
                pos_x = (qr_width - logo_width) // 2
                pos_y = (qr_height - logo_height) // 2

                # Paste the logo onto the QR code image
                # Use alpha_composite for proper blending if logo has transparency
                qr_img.paste(logo_img, (pos_x, pos_y), logo_img)

            # Ensure output directory exists before saving
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

            # Save the final QR code image
            qr_img.save(output_path, "PNG")

            return {
                "success": True,
                "output_path": os.path.abspath(output_path),
                "message": f"QR code with logo generated and saved to '{output_path}'"
            }

        except qrcode.exceptions.DataOverflowError:
            return {"success": False, "error": f"Data too long for QR code version {qr_version}. Consider increasing qr_version or reducing data."}
        except qrcode.exceptions.UnsupportedImageFormat as e:
            return {"success": False, "error": f"Unsupported image format for QR code generation: {e}"}
        except OSError as e:
            return {"success": False, "error": f"File system error when saving QR code to '{output_path}': {e}"}
        except Exception as e:
            return {"success": False, "error": f"An unexpected error occurred during QR code generation: {e}"}
