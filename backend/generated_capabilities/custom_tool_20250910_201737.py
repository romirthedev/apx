
import qrcode
import os
from typing import Dict, Any, Union
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class QRCodeGenerator:
    """
    A specialized tool class for generating QR codes and saving them as image files.
    This class provides methods to create QR codes for given URLs and handle
    potential errors during the process.
    """

    def __init__(self, default_qr_filename: str = "default_qr.png"):
        """
        Initializes the QRCodeGenerator.

        Args:
            default_qr_filename: The default filename to use if none is provided.
        """
        self.default_qr_filename = default_qr_filename

    def _validate_url(self, url: str) -> bool:
        """
        Validates if the provided string is a non-empty URL.
        A more robust validation could involve checking for valid URL schemes.
        """
        if not url or not isinstance(url, str):
            logging.error("URL validation failed: URL must be a non-empty string.")
            return False
        # Basic check for common URL schemes, can be extended
        if not (url.startswith("http://") or url.startswith("https://")):
            logging.warning(f"URL '{url}' does not start with http:// or https://. Proceeding, but it might not be a valid web URL.")
        return True

    def _validate_filename(self, filename: str) -> bool:
        """
        Validates if the provided filename is a non-empty string and has a common image extension.
        """
        if not filename or not isinstance(filename, str):
            logging.error("Filename validation failed: Filename must be a non-empty string.")
            return False
        allowed_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']
        if not any(filename.lower().endswith(ext) for ext in allowed_extensions):
            logging.warning(f"Filename '{filename}' does not have a common image extension. Appending '.png'.")
            filename += ".png"
        return True, filename

    def generate_and_save_qr_code(self, url: str, filename: str = None) -> Dict[str, Union[bool, str, Any]]:
        """
        Generates a QR code for the given URL and saves it to a specified file.

        Args:
            url: The URL for which to generate the QR code.
            filename: The name of the file to save the QR code image (e.g., 'my_qr.png').
                      If None, the default filename is used.

        Returns:
            A dictionary containing:
            - 'success': A boolean indicating if the operation was successful.
            - 'message': A string message describing the outcome.
            - 'filepath': The absolute path to the saved QR code image if successful.
                          Otherwise, None.
        """
        if not self._validate_url(url):
            return {
                'success': False,
                'message': "Invalid URL provided. URL cannot be empty and must be a string.",
                'filepath': None
            }

        if filename is None:
            filename = self.default_qr_filename
            logging.info(f"No filename provided, using default: {self.default_qr_filename}")

        is_valid_filename, filename = self._validate_filename(filename)
        if not is_valid_filename:
            return {
                'success': False,
                'message': "Invalid filename provided. Filename cannot be empty and must have a valid image extension.",
                'filepath': None
            }

        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(url)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            # Ensure the directory exists if filename includes a path
            directory = os.path.dirname(filename)
            if directory and not os.path.exists(directory):
                try:
                    os.makedirs(directory)
                    logging.info(f"Created directory: {directory}")
                except OSError as e:
                    logging.error(f"Error creating directory '{directory}': {e}")
                    return {
                        'success': False,
                        'message': f"Error creating directory '{directory}': {e}",
                        'filepath': None
                    }

            img.save(filename)
            absolute_filepath = os.path.abspath(filename)
            logging.info(f"QR code successfully generated and saved to '{absolute_filepath}'.")
            return {
                'success': True,
                'message': f"QR code for '{url}' successfully saved to '{absolute_filepath}'.",
                'filepath': absolute_filepath
            }

        except Exception as e:
            logging.exception(f"An unexpected error occurred while generating or saving the QR code for URL '{url}' to '{filename}': {e}")
            return {
                'success': False,
                'message': f"An unexpected error occurred: {e}",
                'filepath': None
            }

    def create_github_qr_code(self) -> Dict[str, Union[bool, str, Any]]:
        """
        Generates a QR code for 'https://github.com' and saves it as 'github_qr.png'.

        This is a convenience method tailored to the specific user request.

        Returns:
            A dictionary containing the result of the generate_and_save_qr_code operation.
        """
        logging.info("Executing specific user request: Create QR code for GitHub.")
        url = "https://github.com"
        filename = "github_qr.png"
        return self.generate_and_save_qr_code(url, filename)

if __name__ == '__main__':
    # Example usage:
    # Initialize the generator with a default filename
    generator = QRCodeGenerator(default_qr_filename="generic_qr.png")

    # 1. Handle the specific user request: Create a QR code for https://github.com and save it as github_qr.png
    print("--- Handling Specific User Request ---")
    result_github = generator.create_github_qr_code()
    print(f"Result: {result_github}\n")

    # 2. Example of generating a QR code for another URL with a custom filename
    print("--- Example: Custom QR Code ---")
    custom_url = "https://www.python.org"
    custom_filename = "python_org_qr.png"
    result_custom = generator.generate_and_save_qr_code(custom_url, custom_filename)
    print(f"Result: {result_custom}\n")

    # 3. Example of generating a QR code using the default filename
    print("--- Example: Default Filename ---")
    result_default = generator.generate_and_save_qr_code("https://example.com")
    print(f"Result: {result_default}\n")

    # 4. Example of handling an error: empty URL
    print("--- Example: Error Handling (Empty URL) ---")
    error_result_empty_url = generator.generate_and_save_qr_code("", "invalid_qr.png")
    print(f"Result: {error_result_empty_url}\n")

    # 5. Example of handling an error: invalid filename (missing extension) - handled by appending .png
    print("--- Example: Filename Validation (Missing Extension) ---")
    result_missing_ext = generator.generate_and_save_qr_code("https://example.com/test", "my_qrcode")
    print(f"Result: {result_missing_ext}\n")

    # 6. Example of handling an error: empty filename
    print("--- Example: Error Handling (Empty Filename) ---")
    error_result_empty_filename = generator.generate_and_save_qr_code("https://example.com", "")
    print(f"Result: {error_result_empty_filename}\n")

    # 7. Example with a subdirectory
    print("--- Example: Saving to a Subdirectory ---")
    result_subdir = generator.generate_and_save_qr_code("https://docs.python.org", "output_qrs/python_docs.png")
    print(f"Result: {result_subdir}\n")

    # 8. Example with a non-standard URL scheme (will warn but proceed)
    print("--- Example: Non-Standard URL Scheme ---")
    result_non_standard_url = generator.generate_and_save_qr_code("ftp://example.com/file.txt", "ftp_qr.png")
    print(f"Result: {result_non_standard_url}\n")
