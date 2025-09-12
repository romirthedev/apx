
import os
import shutil
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

try:
    import qrcode
    from PIL import Image
    QRCODE_ENABLED = True
except ImportError:
    QRCODE_ENABLED = False

class FileManagerTool:
    """Tool for file and directory operations, including QR code generation with logos."""

    def __init__(self):
        self.safe_directories = [os.path.expanduser("~/Desktop"), os.path.expanduser("~/Documents")]
        # Ensure the safe directories exist
        for directory in self.safe_directories:
            os.makedirs(directory, exist_ok=True)

    def _is_safe_path(self, path: str) -> bool:
        """Check if the path is in a safe directory."""
        if not path:
            return False
        try:
            abs_path = os.path.abspath(path)
            return any(abs_path.startswith(os.path.abspath(safe_dir)) for safe_dir in self.safe_directories)
        except Exception as e:
            print(f"Error checking safe path '{path}': {e}")
            return False

    def create_directory(self, path: str) -> Dict[str, Any]:
        """Create a new directory."""
        if not path:
            return {"success": False, "error": "Directory path cannot be empty."}

        try:
            if not self._is_safe_path(path):
                return {"success": False, "error": f"Path '{path}' is not in a permitted save directory (e.g., Desktop, Documents)."}

            os.makedirs(path, exist_ok=True)
            return {
                "success": True,
                "path": path,
                "message": f"Directory created or already exists: {path}"
            }
        except OSError as e:
            return {"success": False, "error": f"OS error while creating directory '{path}': {e}"}
        except Exception as e:
            return {"success": False, "error": f"An unexpected error occurred while creating directory '{path}': {e}"}

    def list_files(self, directory: str) -> Dict[str, Any]:
        """List files in a directory."""
        if not directory:
            return {"success": False, "error": "Directory path cannot be empty."}

        try:
            if not self._is_safe_path(directory):
                return {"success": False, "error": f"Path '{directory}' is not in a permitted save directory (e.g., Desktop, Documents)."}

            if not os.path.isdir(directory):
                return {"success": False, "error": f"Directory '{directory}' does not exist."}

            files = []
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                try:
                    if os.path.isdir(item_path):
                        files.append({
                            "name": item,
                            "type": "directory",
                            "size": None
                        })
                    elif os.path.isfile(item_path):
                        files.append({
                            "name": item,
                            "type": "file",
                            "size": os.path.getsize(item_path)
                        })
                except OSError as e:
                    files.append({
                        "name": item,
                        "type": "unknown",
                        "error": f"Could not access details: {e}"
                    })

            return {
                "success": True,
                "directory": directory,
                "files": files,
                "count": len(files)
            }
        except OSError as e:
            return {"success": False, "error": f"OS error while listing directory '{directory}': {e}"}
        except Exception as e:
            return {"success": False, "error": f"An unexpected error occurred while listing directory '{directory}': {e}"}

    def copy_file(self, source: str, destination: str) -> Dict[str, Any]:
        """Copy a file from source to destination."""
        if not source:
            return {"success": False, "error": "Source file path cannot be empty."}
        if not destination:
            return {"success": False, "error": "Destination path cannot be empty."}

        try:
            if not (self._is_safe_path(source) and self._is_safe_path(destination)):
                return {"success": False, "error": "Source or destination path is not in a permitted save directory (e.g., Desktop, Documents)."}

            if not os.path.isfile(source):
                return {"success": False, "error": f"Source path '{source}' is not a valid file."}

            # Ensure the destination directory exists if it's a path to a file
            dest_dir = os.path.dirname(destination)
            if dest_dir and not os.path.exists(dest_dir):
                self.create_directory(dest_dir) # Attempt to create directory if it doesn't exist

            shutil.copy2(source, destination)
            return {
                "success": True,
                "source": source,
                "destination": destination,
                "message": f"File copied successfully from '{source}' to '{destination}'"
            }
        except FileNotFoundError:
            return {"success": False, "error": f"Source file '{source}' not found."}
        except OSError as e:
            return {"success": False, "error": f"OS error while copying file from '{source}' to '{destination}': {e}"}
        except Exception as e:
            return {"success": False, "error": f"An unexpected error occurred while copying file from '{source}' to '{destination}': {e}"}

    def generate_qr_code_with_logo(self, data: str, output_path: str, logo_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a QR code with an optional custom logo and save it as a PNG file.

        Args:
            data (str): The data to be encoded in the QR code.
            output_path (str): The full path to save the generated PNG file.
            logo_path (Optional[str]): The path to the logo image file to embed.

        Returns:
            Dict[str, Any]: A dictionary indicating success or failure with a message or error.
        """
        if not QRCODE_ENABLED:
            return {"success": False, "error": "QR code generation with logos requires 'qrcode' and 'Pillow' libraries. Please install them (`pip install qrcode[pil] Pillow`)."}

        if not data:
            return {"success": False, "error": "QR code data cannot be empty."}
        if not output_path:
            return {"success": False, "error": "Output path for the QR code cannot be empty."}
        if not output_path.lower().endswith(".png"):
            return {"success": False, "error": "Output path must be a .png file."}

        if not self._is_safe_path(output_path):
            return {"success": False, "error": f"Output path '{output_path}' is not in a permitted save directory (e.g., Desktop, Documents)."}

        if logo_path and not os.path.isfile(logo_path):
            return {"success": False, "error": f"Logo file '{logo_path}' not found or is not a file."}
        
        if logo_path and not self._is_safe_path(logo_path):
            return {"success": False, "error": f"Logo path '{logo_path}' is not in a permitted save directory (e.g., Desktop, Documents)."}

        try:
            # --- QR Code Generation ---
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction to accommodate logo
                box_size=10,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)

            qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')

            # --- Logo Embedding ---
            if logo_path:
                try:
                    logo_img = Image.open(logo_path)

                    # Calculate logo size to fit within the QR code
                    qr_width, qr_height = qr_img.size
                    max_logo_size = min(qr_width, qr_height) // 4 # Logo should not cover more than ~1/4 of QR code area

                    logo_img.thumbnail((max_logo_size, max_logo_size))
                    logo_width, logo_height = logo_img.size

                    # Calculate position to center the logo
                    pos_x = (qr_width - logo_width) // 2
                    pos_y = (qr_height - logo_height) // 2

                    # Paste the logo onto the QR code
                    qr_img.paste(logo_img, (pos_x, pos_y), logo_img if logo_img.mode == 'RGBA' else None)

                except FileNotFoundError:
                    return {"success": False, "error": f"Logo file '{logo_path}' not found."}
                except Exception as e:
                    return {"success": False, "error": f"Error processing logo image '{logo_path}': {e}"}

            # --- Saving the Image ---
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                self.create_directory(output_dir)

            qr_img.save(output_path)

            return {
                "success": True,
                "message": f"QR code with logo saved successfully to '{output_path}'",
                "output_path": output_path
            }

        except FileNotFoundError:
             return {"success": False, "error": f"Input file not found. Ensure QR code data and logo paths are correct."}
        except OSError as e:
            return {"success": False, "error": f"OS error while saving QR code to '{output_path}': {e}"}
        except Exception as e:
            return {"success": False, "error": f"An unexpected error occurred during QR code generation: {e}"}

