
import qrcode
import os
from typing import Dict, Any, Optional

class QRCodeGenerator:
    """
    A specialized tool class for generating QR codes and saving them to files.
    This class handles QR code creation for a given URL and saves the output
    as a PNG image, with enhanced error handling and input validation.
    """

    def __init__(self) -> None:
        """
        Initializes the QRCodeGenerator.
        """
        pass

    def generate_and_save_qr_code(self, url: str, filename: str) -> Dict[str, Any]:
        """
        Generates a QR code for the given URL and saves it to a PNG file.

        Args:
            url: The URL to encode in the QR code.
            filename: The name of the file to save the QR code image to (e.g., 'my_qr.png').

        Returns:
            A dictionary containing the result of the operation:
            - 'success' (bool): True if the operation was successful, False otherwise.
            - 'message' (str): A message describing the outcome of the operation.
            - 'filepath' (str, optional): The absolute path to the saved QR code file
                                          if successful.
        """
        # 1. Input Validation
        if not isinstance(url, str) or not url.strip():
            return {
                'success': False,
                'message': "Invalid input: URL must be a non-empty string."
            }
        if not isinstance(filename, str) or not filename.strip():
            return {
                'success': False,
                'message': "Invalid input: Filename must be a non-empty string."
            }
        if not filename.lower().endswith(".png"):
            return {
                'success': False,
                'message': "Invalid input: Filename must end with '.png' for PNG image format."
            }
        
        # 2. Enhanced Error Handling for Directory Creation
        try:
            directory = os.path.dirname(filename)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True) # exist_ok=True prevents error if dir already exists
        except OSError as e:
            return {
                'success': False,
                'message': f"Failed to create directory '{directory}': {e}"
            }

        # 3. QR Code Generation
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

            img.save(filename)
            absolute_filepath = os.path.abspath(filename)

            return {
                'success': True,
                'message': f"QR code for '{url}' successfully saved to '{absolute_filepath}'.",
                'filepath': absolute_filepath
            }

        # 4. General Exception Handling for QR Code Operations
        except qrcode.exceptions.DataOverflowError:
            return {
                'success': False,
                'message': f"QR code generation failed: The provided URL is too long for the QR code version. Try a shorter URL or a different library configuration."
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"An unexpected error occurred during QR code generation or saving: {e}"
            }

def main() -> None:
    """
    Example usage of the QRCodeGenerator class, specifically addressing the user request.
    """
    generator = QRCodeGenerator()
    
    # User request: Create a QR code for https://github.com and save it as github_qr.png
    url_to_encode = "https://github.com"
    output_filename = "github_qr.png"

    print(f"Attempting to generate QR code for: {url_to_encode}")
    print(f"Saving to file: {output_filename}")

    result = generator.generate_and_save_qr_code(url_to_encode, output_filename)

    print(f"\nOperation Result: {result}")

    # --- Additional examples for robust testing ---

    print("\n--- Testing edge cases and potential errors ---")

    # Example of an invalid filename extension
    print("\nTesting invalid filename extension...")
    result_invalid_filename = generator.generate_and_save_qr_code(url_to_encode, "github_qr.jpg")
    print(f"Result: {result_invalid_filename}")

    # Example of an empty URL
    print("\nTesting empty URL...")
    result_empty_url = generator.generate_and_save_qr_code("", "test_empty_url.png")
    print(f"Result: {result_empty_url}")
    
    # Example of an empty filename
    print("\nTesting empty filename...")
    result_empty_filename = generator.generate_and_save_qr_code(url_to_encode, "")
    print(f"Result: {result_empty_filename}")

    # Example of trying to save in a non-existent directory (will be created)
    print("\nTesting saving into a new directory...")
    new_dir_filename = "output_qrs/github_qr_in_dir.png"
    result_new_dir = generator.generate_and_save_qr_code(url_to_encode, new_dir_filename)
    print(f"Result: {result_new_dir}")
    if result_new_dir['success']:
        print(f"Verified file exists at: {os.path.abspath(new_dir_filename)}")

    # Example of a very long URL that might cause DataOverflowError (depends on qrcode library limits)
    # This is illustrative, actual limit might vary.
    print("\nTesting a very long URL (potential DataOverflowError)...")
    long_url = "https://this.is.a.very.long.url.that.might.exceed.the.qr.code.capacity.for.simple.versions.let's.see.if.it.breaks.https://github.com/very/long/path/with/many/segments/and/parameters?id=12345&name=test&value=example&query=this+is+a+test+query"
    result_long_url = generator.generate_and_save_qr_code(long_url, "long_url_qr.png")
    print(f"Result: {result_long_url}")


if __name__ == "__main__":
    main()
