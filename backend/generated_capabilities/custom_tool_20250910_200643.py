
import qrcode
import os
from typing import Dict, Any, Optional

class QRCodeGenerator:
    """
    A specialized tool class for generating and saving QR codes with robust error handling
    and user-friendly features.
    """

    def __init__(self):
        """
        Initializes the QRCodeGenerator.
        """
        pass

    def _get_desktop_path(self) -> Optional[str]:
        """
        Attempts to reliably find the user's Desktop directory across different operating systems.

        Returns:
            The absolute path to the Desktop directory, or None if it cannot be found.
        """
        try:
            # Standard path for Linux/macOS
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            if os.path.isdir(desktop_path):
                return desktop_path

            # Fallback for Windows
            if os.name == 'nt':
                desktop_path = os.path.join(os.environ['USERPROFILE'], 'Desktop')
                if os.path.isdir(desktop_path):
                    return desktop_path
        except Exception:
            # Catch any unexpected errors during path discovery
            pass
        return None

    def generate_and_save_qr_code(
        self,
        data: str,
        filename: str,
        output_directory: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates a QR code for the given data and saves it to a file.

        Args:
            data: The string data to encode in the QR code. Must not be empty.
            filename: The name of the file to save the QR code as (e.g., 'my_qr.png').
                      Must not be empty and should ideally include an image extension.
            output_directory: The directory where the QR code should be saved.
                              If None, the user's Desktop directory will be used.
                              If the Desktop directory cannot be found, an error will be returned.

        Returns:
            A dictionary containing the status of the operation:
            {'success': bool, 'message': str, 'filepath': str | None}
        """
        # --- Input Validation ---
        if not isinstance(data, str) or not data.strip():
            return {'success': False, 'message': "Validation Error: Data to encode cannot be empty or whitespace.", 'filepath': None}
        if not isinstance(filename, str) or not filename.strip():
            return {'success': False, 'message': "Validation Error: Filename cannot be empty or whitespace.", 'filepath': None}

        # Ensure filename has a valid image extension
        valid_extensions = ['.png', '.jpg', '.jpeg', '.gif']
        normalized_filename = filename.strip()
        has_valid_extension = any(normalized_filename.lower().endswith(ext) for ext in valid_extensions)

        if not has_valid_extension:
            normalized_filename += '.png' # Default to PNG if no extension or invalid one is provided

        # --- Determine Output Directory ---
        target_directory = output_directory
        if target_directory is None:
            target_directory = self._get_desktop_path()
            if target_directory is None:
                return {'success': False, 'message': "Error: Could not automatically determine the Desktop directory. Please specify an output_directory.", 'filepath': None}
        else:
            # If a directory is provided, ensure it's a valid directory
            if not isinstance(target_directory, str) or not target_directory.strip():
                return {'success': False, 'message': "Validation Error: Provided output_directory must be a non-empty string.", 'filepath': None}
            if not os.path.isdir(target_directory):
                return {'success': False, 'message': f"Validation Error: Output directory '{target_directory}' does not exist.", 'filepath': None}

        filepath = os.path.join(target_directory, normalized_filename)

        # --- Prevent Overwriting ---
        if os.path.exists(filepath):
            # In a more advanced tool, you might offer to overwrite or rename.
            # For this specific request and current context, preventing overwrite is safer.
            return {'success': False, 'message': f"Error: File '{filepath}' already exists. To avoid data loss, please choose a different filename or location.", 'filepath': None}

        # --- QR Code Generation ---
        try:
            qr = qrcode.QRCode(
                version=1,  # Controls the size of the QR Code. Version 1 is the smallest (21x21).
                error_correction=qrcode.constants.ERROR_CORRECT_L, # L = ~7% correction, M = ~15%, Q = ~25%, H = ~30%
                box_size=10, # Controls how many pixels each "box" of the QR code is.
                border=4,    # Controls how many boxes thick the border should be.
            )
            qr.add_data(data)
            qr.make(fit=True) # Automatically finds the best version and size

            img = qr.make_image(fill_color="black", back_color="white")

            # --- Saving the QR Code ---
            img.save(filepath)

            return {'success': True, 'message': f"QR code successfully generated and saved to '{filepath}'.", 'filepath': filepath}

        except qrcode.exceptions.DataOverflowError:
            return {'success': False, 'message': "Error: The provided data is too long for the QR code version. Consider shortening the data or allowing a larger QR code version if applicable.", 'filepath': None}
        except Exception as e:
            # Catch any other unexpected errors during QR code generation or saving
            return {'success': False, 'message': f"An unexpected error occurred during QR code generation or saving: {e}", 'filepath': None}

if __name__ == '__main__':
    generator = QRCodeGenerator()

    # --- Specific User Request ---
    print("--- Executing Specific User Request ---")
    user_data = 'https://github.com/traehq/trae'
    user_filename = 'github_qr.png'

    result = generator.generate_and_save_qr_code(data=user_data, filename=user_filename)
    print(result)
    print("-" * 30)

    # --- Additional Examples Demonstrating Features ---

    # Example: Generating to a specific, existing directory
    print("--- Example: Generating to Current Directory ---")
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        result_in_current_dir = generator.generate_and_save_qr_code(
            data="This is a test QR code in the current directory.",
            filename="test_qr_in_current_dir.png",
            output_directory=current_dir
        )
        print(result_in_current_dir)
    except Exception as e:
        print(f"Could not perform current directory example: {e}")
    print("-" * 30)

    # Example: Error handling for empty data
    print("--- Example: Error Handling for Empty Data ---")
    result_empty_data = generator.generate_and_save_qr_code(data="", filename="empty_data.png")
    print(result_empty_data)
    print("-" * 30)

    # Example: Error handling for empty filename
    print("--- Example: Error Handling for Empty Filename ---")
    result_empty_filename = generator.generate_and_save_qr_code(data="Some Data", filename="")
    print(result_empty_filename)
    print("-" * 30)

    # Example: Error handling for non-existent output directory
    print("--- Example: Error Handling for Non-existent Output Directory ---")
    result_non_existent_dir = generator.generate_and_save_qr_code(
        data="Test",
        filename="non_existent.png",
        output_directory="/path/to/a/directory/that/does/not/exist"
    )
    print(result_non_existent_dir)
    print("-" * 30)

    # Example: Error handling for existing file (run this after the first specific request)
    print("--- Example: Error Handling for Existing File ---")
    result_existing_file = generator.generate_and_save_qr_code(data="Attempting to overwrite", filename='github_qr.png')
    print(result_existing_file)
    print("-" * 30)

    # Example: Generating with a filename without an extension
    print("--- Example: Generating with Filename Without Extension ---")
    result_no_extension = generator.generate_and_save_qr_code(data="No extension test", filename="no_extension_qr")
    print(result_no_extension)
    print("-" * 30)
