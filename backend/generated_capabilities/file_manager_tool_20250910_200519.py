
import os
import shutil
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from qrcode import QRCode, constants
from PIL import Image, ImageDraw, ImageFont

class FileManagerTool:
    """Tool for file and directory operations."""

    def __init__(self):
        # Expanded safe directories to include a general downloads folder as well.
        self.safe_directories = [
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Documents"),
            os.path.expanduser("~/Downloads")
        ]

    def _is_safe_path(self, path: str) -> bool:
        """Check if the path is in a safe directory."""
        try:
            abs_path = os.path.abspath(path)
            # Ensure the path is within one of the allowed parent directories.
            return any(abs_path.startswith(safe_dir) for safe_dir in self.safe_directories)
        except Exception as e:
            print(f"Error checking safe path '{path}': {e}")
            return False

    def create_directory(self, path: str) -> Dict[str, Any]:
        """Create a new directory."""
        if not path:
            return {"success": False, "error": "Directory path cannot be empty."}
        try:
            if not self._is_safe_path(path):
                return {"success": False, "error": f"Path '{path}' is not within a safe directory. Allowed directories: {self.safe_directories}"}

            os.makedirs(path, exist_ok=True)
            return {
                "success": True,
                "path": path,
                "message": f"Directory created: {path}"
            }
        except OSError as e:
            return {"success": False, "error": f"OS error creating directory '{path}': {e}"}
        except Exception as e:
            return {"success": False, "error": f"An unexpected error occurred creating directory '{path}': {str(e)}"}

    def list_files(self, directory: str) -> Dict[str, Any]:
        """List files in a directory."""
        if not directory:
            return {"success": False, "error": "Directory path cannot be empty."}
        try:
            if not self._is_safe_path(directory):
                return {"success": False, "error": f"Path '{directory}' is not within a safe directory. Allowed directories: {self.safe_directories}"}

            if not os.path.isdir(directory):
                return {"success": False, "error": f"Path '{directory}' is not a valid directory."}

            files_list = []
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                try:
                    if os.path.isdir(item_path):
                        files_list.append({
                            "name": item,
                            "type": "directory"
                        })
                    elif os.path.isfile(item_path):
                        files_list.append({
                            "name": item,
                            "type": "file",
                            "size": os.path.getsize(item_path)
                        })
                except OSError as e:
                    print(f"Could not access item '{item_path}': {e}")
                    files_list.append({
                        "name": item,
                        "type": "unknown",
                        "error": f"Could not access: {e}"
                    })

            return {
                "success": True,
                "directory": directory,
                "files": files_list,
                "count": len(files_list)
            }
        except OSError as e:
            return {"success": False, "error": f"OS error listing directory '{directory}': {e}"}
        except Exception as e:
            return {"success": False, "error": f"An unexpected error occurred listing directory '{directory}': {str(e)}"}

    def copy_file(self, source: str, destination: str) -> Dict[str, Any]:
        """Copy a file from source to destination."""
        if not source or not destination:
            return {"success": False, "error": "Source and destination paths cannot be empty."}
        try:
            if not (self._is_safe_path(source) and self._is_safe_path(destination)):
                return {"success": False, "error": f"Source '{source}' or destination '{destination}' is not within a safe directory. Allowed directories: {self.safe_directories}"}

            if not os.path.isfile(source):
                return {"success": False, "error": f"Source path '{source}' is not a valid file."}

            # Ensure destination directory exists
            dest_dir = os.path.dirname(destination)
            if dest_dir and not os.path.exists(dest_dir):
                self.create_directory(dest_dir) # Attempt to create it if it doesn't exist

            shutil.copy2(source, destination)
            return {
                "success": True,
                "source": source,
                "destination": destination,
                "message": f"File copied from {source} to {destination}"
            }
        except FileNotFoundError:
            return {"success": False, "error": f"Source file not found: {source}"}
        except shutil.SameFileError:
            return {"success": False, "error": f"Source and destination are the same file: {source}"}
        except OSError as e:
            return {"success": False, "error": f"OS error copying file from '{source}' to '{destination}': {e}"}
        except Exception as e:
            return {"success": False, "error": f"An unexpected error occurred copying file from '{source}' to '{destination}': {str(e)}"}

    def generate_qr_code_with_logo(
        self,
        data: str,
        logo_path: str,
        output_filename: str = "qrcode_with_logo.png",
        output_dir: str = ".",
        qr_version: Optional[int] = None,
        qr_error_correction: int = constants.ERROR_CORRECT_H,
        qr_box_size: int = 10,
        qr_border: int = 4,
        logo_size_ratio: float = 0.25
    ) -> Dict[str, Any]:
        """
        Generates a QR code with a custom logo embedded.

        Args:
            data (str): The data to encode in the QR code.
            logo_path (str): The path to the logo image file.
            output_filename (str): The name of the output PNG file. Defaults to "qrcode_with_logo.png".
            output_dir (str): The directory to save the QR code in. Defaults to current directory.
            qr_version (Optional[int]): Controls the size of the QR Code matrix (1 to 40).
                                       If None, the library automatically determines the smallest size.
            qr_error_correction (int): The error correction level. Options:
                                       constants.ERROR_CORRECT_L (approx. 7% recovery)
                                       constants.ERROR_CORRECT_M (approx. 15% recovery)
                                       constants.ERROR_CORRECT_Q (approx. 25% recovery)
                                       constants.ERROR_CORRECT_H (approx. 30% recovery)
                                       Defaults to ERROR_CORRECT_H for better logo embedding.
            qr_box_size (int): Controls how many pixels each "box" of the QR code is. Defaults to 10.
            qr_border (int): Controls how many boxes thick the border should be. Defaults to 4.
            logo_size_ratio (float): The ratio of the logo size to the QR code size. Defaults to 0.25 (25%).

        Returns:
            Dict[str, Any]: A dictionary containing the success status, output path, and a message or error.
        """
        if not data:
            return {"success": False, "error": "QR code data cannot be empty."}
        if not logo_path:
            return {"success": False, "error": "Logo path cannot be empty."}
        if not output_filename:
            return {"success": False, "error": "Output filename cannot be empty."}
        if not output_filename.lower().endswith(".png"):
            return {"success": False, "error": "Output filename must be a .png file."}
        if logo_size_ratio <= 0 or logo_size_ratio >= 1:
            return {"success": False, "error": "Logo size ratio must be between 0 and 1 (exclusive)."}

        full_output_path = os.path.join(output_dir, output_filename)

        try:
            if not self._is_safe_path(output_dir):
                return {"success": False, "error": f"Output directory '{output_dir}' is not within a safe directory. Allowed directories: {self.safe_directories}"}
            if not self._is_safe_path(logo_path):
                return {"success": False, "error": f"Logo path '{logo_path}' is not within a safe directory. Allowed directories: {self.safe_directories}"}

            if not os.path.exists(logo_path):
                return {"success": False, "error": f"Logo file not found at '{logo_path}'."}
            if not os.path.isfile(logo_path):
                return {"success": False, "error": f"Logo path '{logo_path}' is not a file."}

            # --- QR Code Generation ---
            qr = QRCode(
                version=qr_version,
                error_correction=qr_error_correction,
                box_size=qr_box_size,
                border=qr_border,
            )
            qr.add_data(data)
            qr.make(fit=True)

            qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')

            # --- Logo Embedding ---
            logo_img = Image.open(logo_path)

            # Calculate logo size
            qr_width, qr_height = qr_img.size
            logo_max_width = int(qr_width * logo_size_ratio)
            logo_max_height = int(qr_height * logo_size_ratio)

            logo_img.thumbnail((logo_max_width, logo_max_height))
            logo_w, logo_h = logo_img.size

            # Calculate position to paste the logo (center)
            pos_x = (qr_width - logo_w) // 2
            pos_y = (qr_height - logo_h) // 2

            # Paste the logo onto the QR code image
            # Use the logo's alpha channel as a mask if it exists for transparency
            if logo_img.mode == 'RGBA':
                qr_img.paste(logo_img, (pos_x, pos_y), logo_img)
            else:
                qr_img.paste(logo_img, (pos_x, pos_y))

            # --- Save the final image ---
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)

            qr_img.save(full_output_path)

            return {
                "success": True,
                "output_path": full_output_path,
                "message": f"QR code with logo generated and saved to '{full_output_path}'"
            }

        except FileNotFoundError:
            return {"success": False, "error": f"Logo file not found at '{logo_path}'."}
        except OSError as e:
            return {"success": False, "error": f"OS error during image processing or saving '{full_output_path}': {e}"}
        except ImportError:
            return {"success": False, "error": "Required libraries 'qrcode' and 'Pillow' are not installed. Please install them using: pip install qrcode[pil] Pillow"}
        except Exception as e:
            return {"success": False, "error": f"An unexpected error occurred during QR code generation: {str(e)}"}

