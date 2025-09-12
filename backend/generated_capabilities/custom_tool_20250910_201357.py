
import qrcode
import os
from typing import Dict, Any, Optional
import sys

class QRCodeGenerator:
    """
    A specialized tool for generating QR codes and saving them to a specified location.
    This class is designed to be compatible across common operating systems and
    includes robust error handling and input validation.
    """

    def __init__(self):
        """
        Initializes the QRCodeGenerator.
        """
        pass

    def _get_desktop_path(self) -> str:
        """
        Determines the user's Desktop directory path, handling common OS variations.

        Returns:
            The absolute path to the user's Desktop directory.
        """
        if sys.platform.startswith('win'):
            # Windows
            desktop_path = os.path.join(os.environ['USERPROFILE'], 'Desktop')
        elif sys.platform.startswith('darwin'):
            # macOS
            desktop_path = os.path.join(os.path.expanduser("~"), 'Desktop')
        else:
            # Linux and other Unix-like systems
            desktop_path = os.path.join(os.path.expanduser("~"), 'Desktop')
        return desktop_path

    def generate_and_save_qr_code(
        self,
        url: str,
        filename: str = "qrcode.png",
        save_directory: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates a QR code for the given URL and saves it to a specified file.

        Args:
            url: The URL to encode in the QR code.
            filename: The name of the file to save the QR code as. Defaults to "qrcode.png".
            save_directory: The directory where the QR code image should be saved.
                            If None, it defaults to the user's Desktop directory.

        Returns:
            A dictionary containing the result of the operation:
            {
                'success': bool,
                'message': str,
                'filepath': Optional[str]  # The full path to the saved QR code if successful
            }
        """
        try:
            # --- Input Validation ---
            if not isinstance(url, str) or not url.strip():
                return {
                    'success': False,
                    'message': "Invalid input: URL cannot be empty and must be a string.",
                    'filepath': None
                }

            if not isinstance(filename, str) or not filename.strip():
                return {
                    'success': False,
                    'message': "Invalid input: Filename cannot be empty and must be a string.",
                    'filepath': None
                }

            if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                return {
                    'success': False,
                    'message': f"Invalid input: Filename must have a valid image extension (e.g., .png, .jpg). Provided: '{filename}'",
                    'filepath': None
                }

            # --- Determine Save Directory ---
            if save_directory is None:
                save_directory = self._get_desktop_path()
                print(f"Info: No save directory provided, defaulting to Desktop: '{save_directory}'")
            elif not isinstance(save_directory, str):
                return {
                    'success': False,
                    'message': "Invalid input: save_directory must be a string or None.",
                    'filepath': None
                }

            # --- Ensure Directory Exists ---
            try:
                os.makedirs(save_directory, exist_ok=True)
            except OSError as e:
                return {
                    'success': False,
                    'message': f"Error creating directory '{save_directory}': {e}",
                    'filepath': None
                }

            # --- Construct Full File Path ---
            full_filepath = os.path.join(save_directory, filename)

            # --- QR Code Generation ---
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(url)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            # --- Save the Image File ---
            img.save(full_filepath)

            return {
                'success': True,
                'message': f"QR code for '{url}' successfully saved to '{full_filepath}'.",
                'filepath': full_filepath
            }

        except qrcode.exceptions.DataOverflowError:
            return {
                'success': False,
                'message': f"Error: The provided URL is too long to be encoded in a QR code.",
                'filepath': None
            }
        except OSError as e:
            # Catch potential issues during file saving (permissions, disk full, etc.)
            return {
                'success': False,
                'message': f"File system error while saving QR code to '{full_filepath}': {e}",
                'filepath': None
            }
        except Exception as e:
            # Catch any other unexpected errors
            return {
                'success': False,
                'message': f"An unexpected error occurred during QR code generation or saving: {e}",
                'filepath': None
            }

if __name__ == '__main__':
    # Example usage for the specific user request:
    generator = QRCodeGenerator()
    user_url = "https://github.com/traehq/trae"
    user_filename = "github_final_test.png"

    print(f"--- Generating QR Code ---")
    print(f"URL: {user_url}")
    print(f"Filename: {user_filename}")
    print(f"--------------------------")

    result = generator.generate_and_save_qr_code(url=user_url, filename=user_filename)

    if result['success']:
        print(f"Status: SUCCESS")
        print(f"Message: {result['message']}")
        print(f"File saved at: {result.get('filepath')}")
    else:
        print(f"Status: FAILED")
        print(f"Error: {result['message']}")

    print("\n--- Testing with invalid inputs ---")

    # Test case: Empty URL
    empty_url_result = generator.generate_and_save_qr_code(url="", filename="test_empty_url.png")
    print(f"Test (empty URL): {empty_url_result['message']}")

    # Test case: Empty filename
    empty_filename_result = generator.generate_and_save_qr_code(url="https://example.com", filename="")
    print(f"Test (empty filename): {empty_filename_result['message']}")

    # Test case: Invalid filename extension
    invalid_ext_result = generator.generate_and_save_qr_code(url="https://example.com", filename="test.txt")
    print(f"Test (invalid extension): {invalid_ext_result['message']}")

    # Test case: Invalid save_directory type
    invalid_dir_type_result = generator.generate_and_save_qr_code(url="https://example.com", filename="test.png", save_directory=123)
    print(f"Test (invalid directory type): {invalid_dir_type_result['message']}")

    # Test case: Directory with no write permissions (might require manual setup to test)
    # For example, on Linux, try saving to /root/test.png without sudo.
    # This is harder to automate reliably across all systems without elevated privileges.
    # If you want to test this, create a directory where your user doesn't have write permissions.
    # print("\n--- Testing Write Permission (may require manual setup) ---")
    # try:
    #     no_permission_dir = "/non_existent_or_protected_dir" # Replace with a directory you know you can't write to
    #     os.makedirs(no_permission_dir, exist_ok=True) # Ensure it exists for the os.makedirs check
    #     no_permission_result = generator.generate_and_save_qr_code(
    #         url="https://example.com",
    #         filename="no_permission.png",
    #         save_directory=no_permission_dir
    #     )
    #     print(f"Test (no write permission): {no_permission_result['message']}")
    # except Exception as e:
    #     print(f"Could not reliably test no write permission scenario: {e}")

