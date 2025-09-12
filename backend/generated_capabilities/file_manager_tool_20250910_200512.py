
import os
import shutil
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

# Attempt to import necessary libraries, provide informative errors if missing
try:
    import qrcode
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    raise ImportError(
        "This tool requires the 'qrcode' and 'Pillow' libraries. "
        "Please install them using: pip install qrcode[pil] Pillow"
    )

class FileManagerTool:
    """Tool for file and directory operations and QR code generation with logos."""

    def __init__(self):
        # Define safe directories for file operations
        self.safe_directories = [
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Documents"),
            os.path.expanduser("~") # Allow operations in the user's home directory
        ]
        # Ensure safe directories exist, create if not
        for directory in self.safe_directories:
            if not os.path.exists(directory):
                try:
                    os.makedirs(directory, exist_ok=True)
                except Exception as e:
                    print(f"Warning: Could not create safe directory {directory}: {e}")

    def _is_safe_path(self, path: str) -> bool:
        """Check if the path is within one of the defined safe directories."""
        try:
            abs_path = os.path.abspath(path)
            return any(abs_path.startswith(os.path.abspath(safe_dir)) for safe_dir in self.safe_directories)
        except Exception as e:
            print(f"Error checking safe path {path}: {e}")
            return False

    def create_directory(self, path: str) -> Dict[str, Any]:
        """
        Create a new directory.

        Args:
            path (str): The path for the new directory.

        Returns:
            Dict[str, Any]: A dictionary indicating success or failure with details.
        """
        if not path:
            return {"success": False, "error": "Directory path cannot be empty."}

        if not self._is_safe_path(path):
            return {"success": False, "error": f"Operation denied: Path '{path}' is not within a safe directory. Safe directories include: {self.safe_directories}"}

        try:
            os.makedirs(path, exist_ok=True)
            return {
                "success": True,
                "path": os.path.abspath(path),
                "message": f"Directory created successfully: '{os.path.abspath(path)}'"
            }
        except OSError as e:
            return {"success": False, "error": f"Failed to create directory '{path}': {e}"}
        except Exception as e:
            return {"success": False, "error": f"An unexpected error occurred while creating directory '{path}': {e}"}

    def list_files(self, directory: str) -> Dict[str, Any]:
        """
        List files and subdirectories within a given directory.

        Args:
            directory (str): The path to the directory to list.

        Returns:
            Dict[str, Any]: A dictionary containing file listing or an error message.
        """
        if not directory:
            return {"success": False, "error": "Directory path cannot be empty."}

        if not self._is_safe_path(directory):
            return {"success": False, "error": f"Operation denied: Path '{directory}' is not within a safe directory. Safe directories include: {self.safe_directories}"}

        if not os.path.isdir(directory):
            return {"success": False, "error": f"The provided path '{directory}' is not a valid directory."}

        try:
            files_list = []
            for item_name in os.listdir(directory):
                item_path = os.path.join(directory, item_name)
                item_info = {
                    "name": item_name,
                    "path": os.path.abspath(item_path),
                    "type": "directory" if os.path.isdir(item_path) else "file",
                }
                if os.path.isfile(item_path):
                    try:
                        item_info["size"] = os.path.getsize(item_path)
                    except OSError:
                        item_info["size"] = "N/A (permission error)"
                files_list.append(item_info)

            return {
                "success": True,
                "directory": os.path.abspath(directory),
                "files": files_list,
                "count": len(files_list),
                "message": f"Listed {len(files_list)} items in '{os.path.abspath(directory)}'."
            }
        except OSError as e:
            return {"success": False, "error": f"Failed to list directory '{directory}': {e}"}
        except Exception as e:
            return {"success": False, "error": f"An unexpected error occurred while listing directory '{directory}': {e}"}

    def copy_file(self, source: str, destination: str) -> Dict[str, Any]:
        """
        Copy a file from a source path to a destination path.

        Args:
            source (str): The path of the file to copy.
            destination (str): The path where the file should be copied to.

        Returns:
            Dict[str, Any]: A dictionary indicating success or failure with details.
        """
        if not source:
            return {"success": False, "error": "Source file path cannot be empty."}
        if not destination:
            return {"success": False, "error": "Destination path cannot be empty."}

        if not self._is_safe_path(source):
            return {"success": False, "error": f"Operation denied: Source path '{source}' is not within a safe directory."}

        # Destination path validation: if it's a directory, join with source filename.
        # If it's a file, ensure its directory is safe.
        dest_dir = os.path.dirname(destination)
        if not dest_dir: # If destination is just a filename, assume current directory or home directory.
            dest_dir = os.path.expanduser("~")
            destination = os.path.join(dest_dir, destination)

        if not self._is_safe_path(dest_dir):
            return {"success": False, "error": f"Operation denied: Destination directory '{dest_dir}' is not within a safe directory."}

        if not os.path.isfile(source):
            return {"success": False, "error": f"Source path '{source}' is not a valid file."}

        try:
            # Ensure destination directory exists
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            shutil.copy2(source, destination)
            return {
                "success": True,
                "source": os.path.abspath(source),
                "destination": os.path.abspath(destination),
                "message": f"File copied successfully from '{os.path.abspath(source)}' to '{os.path.abspath(destination)}'."
            }
        except FileNotFoundError:
            return {"success": False, "error": f"Source file not found at '{source}'."}
        except PermissionError:
            return {"success": False, "error": f"Permission denied when trying to copy '{source}' to '{destination}'."}
        except OSError as e:
            return {"success": False, "error": f"Failed to copy file: {e}"}
        except Exception as e:
            return {"success": False, "error": f"An unexpected error occurred during file copy: {e}"}

    def generate_qr_code_with_logo(
        self,
        data: str,
        output_filename: str,
        logo_path: Optional[str] = None,
        error_correction: str = "M",
        box_size: int = 10,
        border: int = 4,
        fill_color: str = "black",
        back_color: str = "white"
    ) -> Dict[str, Any]:
        """
        Generates a QR code with optional custom logo embedding and saves it as a PNG file.

        Args:
            data (str): The data to encode in the QR code.
            output_filename (str): The desired filename for the output PNG image (e.g., "my_qr.png").
            logo_path (Optional[str]): Path to the logo image file (PNG, JPG). If None, no logo is embedded.
            error_correction (str): The error correction level ('L', 'M', 'Q', 'H'). Defaults to 'M'.
            box_size (int): The size of each box (pixel) in the QR code. Defaults to 10.
            border (int): The thickness of the border around the QR code. Defaults to 4.
            fill_color (str): The color of the QR code modules. Defaults to 'black'.
            back_color (str): The background color of the QR code. Defaults to 'white'.

        Returns:
            Dict[str, Any]: A dictionary indicating success or failure with details.
        """
        if not data:
            return {"success": False, "error": "QR code data cannot be empty."}
        if not output_filename:
            return {"success": False, "error": "Output filename cannot be empty."}
        if not output_filename.lower().endswith(".png"):
            return {"success": False, "error": "Output filename must end with '.png'."}

        # Determine the safe directory for the output file
        output_dir = os.path.dirname(output_filename)
        if not output_dir:
            output_dir = os.path.expanduser("~") # Default to home directory if no directory specified
            output_filename = os.path.join(output_dir, output_filename)

        if not self._is_safe_path(output_dir):
            return {"success": False, "error": f"Operation denied: Output directory '{output_dir}' is not within a safe directory. Safe directories include: {self.safe_directories}"}

        # Validate error correction level
        valid_error_correction = {
            'L': qrcode.constants.ERROR_CORRECT_L,
            'M': qrcode.constants.ERROR_CORRECT_M,
            'Q': qrcode.constants.ERROR_CORRECT_Q,
            'H': qrcode.constants.ERROR_CORRECT_H
        }
        ec_level = valid_error_correction.get(error_correction.upper())
        if ec_level is None:
            return {"success": False, "error": f"Invalid error correction level '{error_correction}'. Must be one of 'L', 'M', 'Q', 'H'."}

        # Validate color inputs
        try:
            Image.new("RGB", (1, 1), back_color)
            Image.new("RGB", (1, 1), fill_color)
        except ValueError:
            return {"success": False, "error": "Invalid color format. Please use standard color names or hex codes (e.g., 'red', '#00FF00')."}

        # Validate box_size and border
        if not isinstance(box_size, int) or box_size <= 0:
            return {"success": False, "error": "Box size must be a positive integer."}
        if not isinstance(border, int) or border < 0:
            return {"success": False, "error": "Border size must be a non-negative integer."}

        # Validate logo path if provided
        if logo_path and not os.path.isfile(logo_path):
            return {"success": False, "error": f"Logo file not found at '{logo_path}'."}

        try:
            # Initialize QR code generator
            qr = qrcode.QRCode(
                version=1,
                error_correction=ec_level,
                box_size=box_size,
                border=border,
            )
            qr.add_data(data)
            qr.make(fit=True)

            # Create QR code image
            img_qr = qr.make_image(fill_color=fill_color, back_color=back_color).convert("RGBA")

            # Embed logo if provided
            if logo_path:
                try:
                    logo = Image.open(logo_path).convert("RGBA")

                    # Calculate logo size - aim for a reasonable percentage of QR code size
                    qr_width, qr_height = img_qr.size
                    max_logo_size = min(qr_width, qr_height) // 4 # Logo will be at most 1/4 of QR code size
                    logo.thumbnail((max_logo_size, max_logo_size), Image.Resampling.LANCZOS)

                    # Calculate position to center the logo
                    logo_width, logo_height = logo.size
                    pos_x = (qr_width - logo_width) // 2
                    pos_y = (qr_height - logo_height) // 2
                    position = (pos_x, pos_y)

                    # Paste the logo onto the QR code image
                    # Use alpha_composite for proper transparency handling
                    img_qr.paste(logo, position, logo)

                except FileNotFoundError:
                    return {"success": False, "error": f"Logo file not found at '{logo_path}'. Cannot embed logo."}
                except Exception as e:
                    return {"success": False, "error": f"Failed to process or embed logo '{logo_path}': {e}. Ensure it's a valid image file."}

            # Save the final QR code image
            img_qr.save(output_filename)
            return {
                "success": True,
                "message": f"QR code generated and saved successfully to '{os.path.abspath(output_filename)}'.",
                "output_path": os.path.abspath(output_filename)
            }
        except qrcode.exceptions.DataOverflowError:
            return {"success": False, "error": "Data too long for QR code version. Try a higher version or shorter data."}
        except Exception as e:
            return {"success": False, "error": f"An unexpected error occurred during QR code generation: {e}"}

