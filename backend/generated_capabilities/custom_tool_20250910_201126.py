
import qrcode
import os
import sys
from typing import Dict, Any

class QRCodeGenerator:
    """
    A specialized tool class for generating QR codes and saving them as image files.
    This class is designed to be compatible with macOS and includes robust error handling
    and input validation.
    """

    def __init__(self):
        """
        Initializes the QRCodeGenerator.
        """
        pass

    def _get_desktop_path(self) -> str | None:
        """
        Determines the user's Desktop path, attempting to be robust across different systems,
        though primarily targeting macOS as per context.

        Returns:
            str | None: The absolute path to the Desktop directory, or None if it cannot be found.
        """
        # Common macOS Desktop path
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        if os.path.isdir(desktop_path) and os.access(desktop_path, os.W_OK):
            return desktop_path

        # Fallback for other common configurations or less standard setups
        potential_paths = [
            os.path.join(os.path.expanduser("~"), "Documents", "Desktop"),
            os.path.join(os.path.expanduser("~"), "Public", "Desktop"), # Less common but possible
        ]
        for path in potential_paths:
            if os.path.isdir(path) and os.access(path, os.W_OK):
                return path

        # If still not found, try a more generic approach that might work on Windows/Linux
        # though the user request specified macOS context.
        try:
            from pathlib import Path
            desktop = Path.home() / "Desktop"
            if desktop.is_dir() and os.access(str(desktop), os.W_OK):
                return str(desktop)
        except ImportError:
            pass # pathlib is standard, but good to be safe.

        return None

    def generate_and_save_qr_code(self, url: str, filename: str = "qrcode.png") -> Dict[str, Any]:
        """
        Generates a QR code for the given URL and saves it as an image file
        on the user's Desktop.

        Args:
            url (str): The URL to encode in the QR code.
            filename (str, optional): The name of the output image file.
                                       Defaults to "qrcode.png".

        Returns:
            Dict[str, Any]: A dictionary containing the status of the operation:
                            {'success': bool, 'message': str, 'filepath': str or None}
        """
        # --- Input Validation ---
        if not url or not isinstance(url, str):
            return {"success": False, "message": "Invalid input: URL cannot be empty and must be a string.", "filepath": None}

        if not filename or not isinstance(filename, str):
            return {"success": False, "message": "Invalid input: Filename cannot be empty and must be a string.", "filepath": None}

        # Ensure filename has a valid image extension, default to PNG if not provided or invalid.
        valid_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']
        base, ext = os.path.splitext(filename)
        if not ext.lower() in valid_extensions:
            if ext: # If an extension was provided but invalid, inform the user and correct it.
                print(f"Warning: Invalid extension '{ext}' provided for filename. Defaulting to '.png'.", file=sys.stderr)
            filename = f"{base}.png"

        # --- Path Determination and Check ---
        desktop_path = self._get_desktop_path()
        if not desktop_path:
            return {"success": False, "message": "Error: Could not determine a writable Desktop path.", "filepath": None}

        output_filepath = os.path.join(desktop_path, filename)

        # --- QR Code Generation ---
        try:
            # The qrcode library can handle URLs up to a certain length based on version.
            # Version 1 has limited capacity. For longer URLs, a higher version is needed.
            # We can let qrcode library's make(fit=True) handle version selection.
            qr = qrcode.QRCode(
                version=None, # Let the library determine the optimal version
                error_correction=qrcode.constants.ERROR_CORRECT_L, # Low error correction for more data capacity
                box_size=10,
                border=4,
            )
            qr.add_data(url)
            qr.make(fit=True) # Automatically finds the smallest version that fits the data

            img = qr.make_image(fill_color="black", back_color="white")
            img.save(output_filepath)

            return {"success": True, "message": f"QR code for '{url}' saved successfully to: {output_filepath}", "filepath": output_filepath}

        except qrcode.exceptions.DataOverflowError:
            return {"success": False, "message": f"Error: The URL '{url}' is too long to be encoded in a QR code.", "filepath": None}
        except FileNotFoundError:
            # This exception is less likely with a valid desktop_path, but could occur if
            # the path becomes invalid between check and save.
            return {"success": False, "message": f"Error: The output path '{output_filepath}' is invalid or inaccessible.", "filepath": None}
        except PermissionError:
            return {"success": False, "message": f"Error: Permission denied to save file at '{output_filepath}'. Please check directory permissions.", "filepath": None}
        except IOError as e:
            return {"success": False, "message": f"Error: An I/O error occurred while saving the file: {e}", "filepath": None}
        except Exception as e:
            # Catch any other unexpected errors
            return {"success": False, "message": f"An unexpected error occurred during QR code generation or saving: {str(e)}", "filepath": None}

if __name__ == '__main__':
    # --- Fulfilling the specific user request ---
    print("Attempting to fulfill user request...")
    generator = QRCodeGenerator()
    user_url = "https://github.com/traehq/trae"
    user_filename = "github_test.png"

    result = generator.generate_and_save_qr_code(user_url, user_filename)

    print(f"Operation Status: {result['success']}")
    print(f"Message: {result['message']}")
    if result['filepath']:
        print(f"File saved at: {result['filepath']}")

    print("\n" + "="*30 + "\n")

    # --- Testing various scenarios and error handling ---
    print("--- Testing various scenarios and error handling ---")

    # Test case: Empty URL
    print("\nTesting empty URL:")
    result_empty_url = generator.generate_and_save_qr_code("", "test_empty_url.png")
    print(f"Result: {result_empty_url}")

    # Test case: Empty filename
    print("\nTesting empty filename:")
    result_empty_filename = generator.generate_and_save_qr_code("https://example.com", "")
    print(f"Result: {result_empty_filename}")

    # Test case: Invalid extension and default to .png
    print("\nTesting invalid extension (e.g., .txt):")
    result_invalid_ext = generator.generate_and_save_qr_code("https://example.com/test", "my_qr_code.txt")
    print(f"Result: {result_invalid_ext}")
    if result_invalid_ext['success']:
        print(f"Verify that the file '{os.path.basename(result_invalid_ext['filepath'])}' was saved as a PNG.")

    # Test case: Very long URL (will likely trigger DataOverflowError)
    print("\nTesting extremely long URL:")
    long_url_data = "https://github.com/traehq/trae/blob/main/README.md?plain=1" * 50 # Make it very long
    result_long_url = generator.generate_and_save_qr_code(long_url_data, "long_url_test.png")
    print(f"Result: {result_long_url}")

    # Test case: Invalid characters in filename (OS dependent, but `qrcode` might handle some)
    # For simplicity, we rely on OS to raise errors or `qrcode` to sanitize if needed.
    # A more robust check would involve OS-specific filename character validation.
    print("\nTesting filename with potential problematic characters (e.g., ':' on Windows):")
    # On macOS/Linux, ':' is invalid in filenames. On Windows it is also invalid.
    result_invalid_filename_chars = generator.generate_and_save_qr_code("https://example.com/filename", "invalid:filename.png")
    print(f"Result: {result_invalid_filename_chars}")


    # Test case: URL that is not a valid URL format (basic check)
    print("\nTesting non-URL string:")
    result_malformed_url = generator.generate_and_save_qr_code("this_is_not_a_url", "malformed_url_test.png")
    print(f"Result: {result_malformed_url}")
    # Note: The `qrcode` library itself doesn't strictly validate URL format,
    # it just encodes the string. A separate URL validation could be added if strictness is needed.
    # For this context, encoding any string is acceptable.

    print("\n--- End of tests ---")
