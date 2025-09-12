
import qrcode
from PIL import Image, UnidentifiedImageError
import os
from pathlib import Path
from typing import Dict, Any, Optional

class QRCodeGeneratorTool:
    """
    A tool for generating QR codes with custom logos.
    """

    def __init__(self, logo_path: Optional[Path] = None):
        """
        Initializes the QRCodeGeneratorTool.

        Args:
            logo_path: An optional Path object pointing to the logo image file.
                       If not provided, a default logo will be attempted to be found.
        """
        self.logo_path = logo_path

    def _find_default_logo(self) -> Optional[Path]:
        """
        Attempts to find a default logo image in common locations.
        This is a best-effort approach and might not find a logo.
        For robust usage, providing a logo_path during initialization is recommended.

        Returns:
            A Path object to a found logo, or None if no suitable logo is found.
        """
        possible_locations = [
            Path.home() / "Pictures" / "default_logo.png",
            Path.home() / "Pictures" / "logo.png",
            Path.home() / "Downloads" / "default_logo.png",
            Path.home() / "Downloads" / "logo.png",
            Path.cwd() / "default_logo.png",
            Path.cwd() / "logo.png",
        ]
        for loc in possible_locations:
            if loc.is_file():
                return loc
        return None

    def _get_desktop_path(self) -> Path:
        """
        Determines the user's Desktop path in a cross-platform way.
        """
        # On macOS and most Linux systems, this is usually "Desktop"
        desktop_path = Path.home() / "Desktop"
        if desktop_path.exists() and desktop_path.is_dir():
            return desktop_path
        
        # For Windows, it's typically in the user's profile
        windows_desktop_path = Path.home() / "OneDrive" / "Desktop"
        if windows_desktop_path.exists() and windows_desktop_path.is_dir():
            return windows_desktop_path
        
        # Fallback to a common location if neither is found (less common)
        return Path.home() / "Downloads"

    def generate_qr_with_logo(
        self,
        data: str,
        output_filename: str = "trae_qr_with_logo.png",
        output_directory: Optional[Path] = None,
        error_correction: int = qrcode.constants.ERROR_CORRECT_H,
        box_size: int = 10,
        border: int = 4,
        fill_color: str = "black",
        back_color: str = "white",
        logo_size_ratio: float = 0.25
    ) -> Dict[str, Any]:
        """
        Generates a QR code for the given data and embeds a custom logo.

        Args:
            data: The data to encode in the QR code (e.g., a URL).
            output_filename: The name of the output PNG file. Defaults to 'trae_qr_with_logo.png'.
            output_directory: The directory where the QR code will be saved.
                              If None, the user's Desktop will be used.
            error_correction: The error correction level for the QR code.
                              Options are ERROR_CORRECT_L, ERROR_CORRECT_M,
                              ERROR_CORRECT_Q, ERROR_CORRECT_H.
            box_size: The size of each box (pixel) in the QR code.
            border: The thickness of the border around the QR code.
            fill_color: The color of the QR code modules.
            back_color: The background color of the QR code.
            logo_size_ratio: The ratio of the logo's size to the QR code's size.

        Returns:
            A dictionary containing the status of the operation:
            {
                'success': bool,
                'message': str,
                'data': {
                    'output_path': str  # Path to the generated QR code file
                } | None
            }
        """
        # --- Input Validation ---
        if not isinstance(data, str) or not data.strip():
            return {"success": False, "message": "Data to encode cannot be empty or invalid.", "data": None}
        
        if not isinstance(output_filename, str) or not output_filename.endswith(".png"):
            return {"success": False, "message": "Output filename must be a string ending with '.png'.", "data": None}
        
        if not isinstance(error_correction, int) or error_correction not in [
            qrcode.constants.ERROR_CORRECT_L, qrcode.constants.ERROR_CORRECT_M,
            qrcode.constants.ERROR_CORRECT_Q, qrcode.constants.ERROR_CORRECT_H
        ]:
            return {"success": False, "message": "Invalid error correction level.", "data": None}
        
        if not isinstance(box_size, int) or box_size <= 0:
            return {"success": False, "message": "Box size must be a positive integer.", "data": None}
        
        if not isinstance(border, int) or border < 0:
            return {"success": False, "message": "Border must be a non-negative integer.", "data": None}
        
        if not isinstance(logo_size_ratio, (int, float)) or not (0 < logo_size_ratio <= 0.5):
            return {"success": False, "message": "Logo size ratio must be between 0 (exclusive) and 0.5 (inclusive).", "data": None}

        # --- Logo Handling ---
        resolved_logo_path: Optional[Path] = None
        if self.logo_path:
            if not isinstance(self.logo_path, Path):
                return {
                    "success": False,
                    "message": "Provided logo_path must be a Path object.",
                    "data": None,
                }
            if not self.logo_path.is_file():
                return {
                    "success": False,
                    "message": f"Provided logo file not found at: {self.logo_path}",
                    "data": None,
                }
            resolved_logo_path = self.logo_path
        else:
            resolved_logo_path = self._find_default_logo()
            if not resolved_logo_path:
                return {
                    "success": False,
                    "message": "No logo specified and no default logo found. Please provide a logo path for robust usage.",
                    "data": None,
                }
        
        # --- Determine Output Directory ---
        if output_directory is None:
            output_directory = self._get_desktop_path()
        elif not isinstance(output_directory, Path):
            return {
                "success": False,
                "message": "output_directory must be a Path object or None.",
                "data": None,
            }

        if not output_directory.is_dir():
            return {
                "success": False,
                "message": f"Output directory is not a valid directory: {output_directory}",
                "data": None,
            }

        # Ensure output path is absolute and safe
        output_path = (output_directory / output_filename).resolve()

        # Safety check: Prevent overwriting critical system files
        # This is a basic check, more advanced checks might be needed for production
        restricted_dirs = ["/System", "/bin", "/sbin", "/usr", "/etc", "/var"]
        if any(str(output_path).startswith(restricted_dir) for restricted_dir in restricted_dirs):
             return {
                "success": False,
                "message": f"Attempted to save to a restricted system directory: {output_path}",
                "data": None,
            }
        
        # Prevent overwriting the tool's own script or directories that might cause issues
        current_script_dir = Path(__file__).parent.resolve()
        if str(output_path).startswith(str(current_script_dir)):
            return {
                "success": False,
                "message": f"Attempted to save within the script's directory, which is not allowed: {output_path}",
                "data": None,
            }

        try:
            # 1. Create QR code instance
            qr = qrcode.QRCode(
                version=1,
                error_correction=error_correction,
                box_size=box_size,
                border=border,
            )
            qr.add_data(data)
            qr.make(fit=True)

            qr_img = qr.make_image(fill_color=fill_color, back_color=back_color).convert("RGB")

            # 2. Load and resize logo
            try:
                logo_img = Image.open(resolved_logo_path).convert("RGBA")
            except FileNotFoundError:
                return {
                    "success": False,
                    "message": f"Error: Logo file not found at '{resolved_logo_path}'.",
                    "data": None,
                }
            except UnidentifiedImageError:
                return {
                    "success": False,
                    "message": f"Error: Cannot identify image file '{resolved_logo_path}'. Ensure it's a valid image format.",
                    "data": None,
                }

            qr_width, qr_height = qr_img.size
            logo_max_width = int(qr_width * logo_size_ratio)
            logo_max_height = int(qr_height * logo_size_ratio)
            
            # Maintain aspect ratio while fitting within the max dimensions
            logo_img.thumbnail((logo_max_width, logo_max_height), Image.Resampling.LANCZOS)

            # 3. Calculate logo position (center)
            logo_width, logo_height = logo_img.size
            pos_x = (qr_width - logo_width) // 2
            pos_y = (qr_height - logo_height) // 2
            position = (pos_x, pos_y)

            # 4. Paste logo onto QR code
            # Use the logo's alpha channel as a mask for transparent pasting
            qr_img.paste(logo_img, position, logo_img)

            # 5. Save the QR code
            qr_img.save(output_path)

            return {
                "success": True,
                "message": f"QR code with logo saved successfully to {output_path}",
                "data": {"output_path": str(output_path)},
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"An unexpected error occurred during QR code generation: {e}",
                "data": None,
            }

if __name__ == "__main__":
    # --- Helper to create a dummy logo for testing ---
    def create_dummy_logo(filepath: Path, color: str = 'red', size: tuple = (60, 30)):
        try:
            if not filepath.parent.exists():
                filepath.parent.mkdir(parents=True, exist_ok=True)
            img = Image.new('RGBA', size, color=color)
            img.save(filepath)
            print(f"Created dummy logo at {filepath}")
            return True
        except Exception as e:
            print(f"Could not create dummy logo at {filepath}: {e}")
            return False

    # --- User Request Simulation ---
    print("--- Simulating User Request: Create QR for 'https://trae.ai' with custom logo on Desktop ---")

    # Define output path and filename as per user request
    user_output_filename = "trae_qr_with_logo.png"
    user_output_directory = Path.home() / "Desktop"
    user_data = "https://trae.ai"

    # Attempt to find any available logo image.
    # For this specific request, we'll prioritize creating a dummy if none exist,
    # as the request states "Use any available logo image."
    
    # First, try to find a logo
    logo_finder = QRCodeGeneratorTool()
    found_logo_path = logo_finder._find_default_logo() # Use internal helper for demonstration

    if not found_logo_path:
        print("No default logo found. Attempting to create a dummy logo for demonstration.")
        # Create a dummy logo in the current directory for this example
        dummy_logo_path_for_request = Path("./dummy_trae_logo.png")
        if create_dummy_logo(dummy_logo_path_for_request):
            # Initialize tool with the created dummy logo
            tool_for_request = QRCodeGeneratorTool(logo_path=dummy_logo_path_for_request)
            
            # Generate QR code
            result_user_request = tool_for_request.generate_qr_with_logo(
                data=user_data,
                output_filename=user_output_filename,
                output_directory=user_output_directory
            )
            
            print("\n--- Result of User Request Simulation ---")
            print(result_user_request)

            if result_user_request['success']:
                print(f"\nSuccess! Please check your Desktop for '{user_output_filename}'.")
                # Clean up dummy logo created for this specific request
                try:
                    os.remove(dummy_logo_path_for_request)
                    print(f"Cleaned up dummy logo: {dummy_logo_path_for_request}")
                except Exception as e:
                    print(f"Error cleaning up dummy logo: {e}")
            else:
                print("\nFailed to generate QR code for the user request.")
        else:
            print("\nCould not create a dummy logo, so the user request could not be fulfilled.")
            print("Please ensure you have write permissions in the current directory or provide a valid logo path.")
    else:
        print(f"Found a logo at: {found_logo_path}. Using this logo.")
        tool_for_request = QRCodeGeneratorTool(logo_path=found_logo_path)
        
        # Generate QR code
        result_user_request = tool_for_request.generate_qr_with_logo(
            data=user_data,
            output_filename=user_output_filename,
            output_directory=user_output_directory
        )
        
        print("\n--- Result of User Request Simulation ---")
        print(result_user_request)
        
        if result_user_request['success']:
            print(f"\nSuccess! Please check your Desktop for '{user_output_filename}'.")
        else:
            print("\nFailed to generate QR code for the user request.")


    # --- Additional Test Cases for Robustness ---
    print("\n--- Additional Test Cases ---")

    # Test case 1: No logo provided, no default logo found (should fail gracefully)
    print("\nTest Case 1: No logo, no default.")
    tool_no_logo = QRCodeGeneratorTool()
    result_no_logo = tool_no_logo.generate_qr_with_logo(
        data="https://example.com",
        output_filename="no_logo_test.png",
        output_directory=Path.home() / "Desktop"
    )
    print(result_no_logo)

    # Test case 2: Invalid logo path
    print("\nTest Case 2: Invalid logo path.")
    invalid_logo_tool = QRCodeGeneratorTool(logo_path=Path("/path/to/nonexistent/logo.jpg"))
    result_invalid_logo = invalid_logo_tool.generate_qr_with_logo(data="https://example.com")
    print(result_invalid_logo)

    # Test case 3: Empty data
    print("\nTest Case 3: Empty data.")
    # Use the tool initialized for the user request, assuming it has a valid logo or fallback
    result_empty_data = tool_for_request.generate_qr_with_logo(data="", output_filename="empty_data.png")
    print(result_empty_data)

    # Test case 4: Invalid output filename
    print("\nTest Case 4: Invalid output filename.")
    result_invalid_filename = tool_for_request.generate_qr_with_logo(
        data="https://example.com",
        output_filename="qr_code.jpg" # Incorrect extension
    )
    print(result_invalid_filename)

    # Test case 5: Invalid logo size ratio
    print("\nTest Case 5: Invalid logo size ratio.")
    result_invalid_ratio = tool_for_request.generate_qr_with_logo(
        data="https://example.com",
        logo_size_ratio=1.0 # Too large
    )
    print(result_invalid_ratio)

    # Test case 6: Saving to a potentially restricted directory (should be caught)
    print("\nTest Case 6: Saving to restricted directory.")
    result_restricted = tool_for_request.generate_qr_with_logo(
        data="https://example.com",
        output_filename="forbidden_qr.png",
        output_directory=Path("/System/Library") # Example restricted path
    )
    print(result_restricted)
