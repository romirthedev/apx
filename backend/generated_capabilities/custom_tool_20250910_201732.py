
import qrcode
import os
from typing import Dict, Any

class QRCodeGenerator:
    """
    A specialized tool class for generating QR codes.
    This class provides methods to create QR codes for given data and save them
    as image files. It includes error handling and returns structured results.
    """

    def __init__(self):
        """
        Initializes the QRCodeGenerator.
        """
        pass

    def generate_and_save_qr(self, url: str, filename: str) -> Dict[str, Any]:
        """
        Generates a QR code for a given URL and saves it to a specified file.

        Args:
            url: The URL for which to generate the QR code.
            filename: The name of the file (including extension, e.g., 'qr_code.png')
                      to save the QR code image. The path is relative to the
                      current working directory.

        Returns:
            A dictionary containing the operation status:
            - 'success' (bool): True if the QR code was generated and saved successfully,
                                False otherwise.
            - 'message' (str): A descriptive message about the operation's outcome.
            - 'filepath' (str, optional): The absolute path to the saved QR code file
                                           if successful.
        """
        if not url or not isinstance(url, str) or not url.strip():
            return {
                "success": False,
                "message": "Invalid URL provided. URL must be a non-empty string."
            }
        if not filename or not isinstance(filename, str) or not filename.strip():
            return {
                "success": False,
                "message": "Invalid filename provided. Filename must be a non-empty string."
            }

        # Ensure the filename has a common image extension if not provided
        valid_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp']
        base_filename, ext = os.path.splitext(filename)
        if not ext.lower() in valid_extensions:
            original_filename_for_message = filename
            filename = f"{base_filename}.png"
            print(f"Warning: Invalid or missing image extension in filename '{original_filename_for_message}'. Appending '.png': '{filename}'")

        # Check if the directory exists and is writable if a path is specified
        directory = os.path.dirname(filename)
        if directory:
            if not os.path.exists(directory):
                try:
                    os.makedirs(directory)
                    print(f"Created directory: '{directory}'")
                except OSError as e:
                    return {
                        "success": False,
                        "message": f"Failed to create directory '{directory}': {e}"
                    }
            elif not os.access(directory, os.W_OK):
                return {
                    "success": False,
                    "message": f"Directory '{directory}' is not writable."
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

            img.save(filename)
            absolute_filepath = os.path.abspath(filename)

            return {
                "success": True,
                "message": f"QR code for '{url}' successfully saved to '{filename}'.",
                "filepath": absolute_filepath
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"An error occurred while generating or saving the QR code: {e}"
            }

def main_handler():
    """
    Handles the specific user request: Create a QR code for https://github.com
    and save it as github_qr.png.
    """
    qr_generator = QRCodeGenerator()
    url_to_encode = "https://github.com"
    output_filename = "github_qr.png"

    print(f"Attempting to create QR code for: {url_to_encode}")
    print(f"Saving QR code as: {output_filename}")

    result = qr_generator.generate_and_save_qr(url_to_encode, output_filename)

    if result["success"]:
        print(f"\nSuccessfully generated QR code!")
        print(f"Message: {result['message']}")
        print(f"Filepath: {result.get('filepath')}")
    else:
        print(f"\nFailed to generate QR code.")
        print(f"Error: {result['message']}")

if __name__ == "__main__":
    main_handler()
