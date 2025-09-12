
import qrcode
import os
import sys
from typing import Dict, Any, Optional

class QRCodeGeneratorTool:
    """
    A specialized tool for generating QR codes and saving them to a specified location.
    This class is designed to be compatible with macOS and includes robust error handling.
    """

    def __init__(self):
        """
        Initializes the QRCodeGeneratorTool.
        """
        pass

    def get_desktop_path(self) -> str:
        """
        Determines the user's desktop path in a platform-independent manner.
        Raises:
            OSError: If the desktop path cannot be determined.
        """
        if sys.platform == "win32":
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        elif sys.platform == "darwin":
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        elif sys.platform.startswith("linux"):
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        else:
            raise OSError("Unsupported operating system. Cannot determine desktop path.")
        
        if not os.path.exists(desktop_path):
            raise OSError(f"Desktop directory not found at '{desktop_path}'. Please ensure it exists.")
        return desktop_path

    def validate_url(self, url: str) -> bool:
        """
        Validates if the provided string is a valid URL.
        This is a basic validation and might not cover all edge cases.
        """
        if not isinstance(url, str) or not url.strip():
            return False
        # A more robust URL validation could be implemented here using regex or a library
        # For this example, we'll check for basic http/https structure
        return url.startswith("http://") or url.startswith("https://")

    def validate_filename(self, filename: str) -> bool:
        """
        Validates if the provided filename is safe to use.
        Removes potentially problematic characters.
        """
        if not isinstance(filename, str) or not filename.strip():
            return False
        
        # Basic sanitization: remove characters that are typically problematic in filenames
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
            
        # Ensure the filename has a common image extension
        if not (filename.lower().endswith(".png") or filename.lower().endswith(".jpg") or filename.lower().endswith(".jpeg")):
            filename += ".png" # Default to .png if no extension is found or recognized
            
        return filename.strip() != "" # Ensure filename is not empty after sanitization

    def generate_qr_code(self, url: str, filename: str, save_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Generates a QR code for the given URL and saves it with the specified filename.

        Args:
            url (str): The URL to encode in the QR code.
            filename (str): The name of the file to save the QR code as (e.g., 'my_qr.png').
            save_dir (Optional[str]): The directory to save the QR code in. If None,
                                      it defaults to the user's Desktop.

        Returns:
            Dict[str, Any]: A dictionary containing the status of the operation.
                            Keys include:
                            - 'success' (bool): True if the operation was successful, False otherwise.
                            - 'message' (str): A descriptive message about the operation's outcome.
                            - 'file_path' (Optional[str]): The absolute path to the saved QR code image if successful.
        """
        if not self.validate_url(url):
            return {
                "success": False,
                "message": f"Invalid URL provided: '{url}'. Please provide a valid URL starting with http:// or https://.",
                "file_path": None
            }

        if not self.validate_filename(filename):
            return {
                "success": False,
                "message": f"Invalid filename provided: '{filename}'. Filename contains invalid characters or is empty.",
                "file_path": None
            }

        try:
            if save_dir is None:
                save_dir = self.get_desktop_path()
            
            # Ensure the directory exists before saving
            os.makedirs(save_dir, exist_ok=True)

            full_path = os.path.join(save_dir, filename)

            # Use segno for potentially better handling and more options, or stick to qrcode if preferred
            # For this enhancement, we'll stick to qrcode as per initial context, but acknowledge segno's existence.
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(url)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            img.save(full_path)

            return {
                "success": True,
                "message": f"QR code for '{url}' generated and saved to '{os.path.abspath(full_path)}'.",
                "file_path": os.path.abspath(full_path)
            }

        except OSError as e:
            return {
                "success": False,
                "message": f"Error accessing or creating directory '{save_dir}': {e}",
                "file_path": None
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"An unexpected error occurred while generating the QR code: {e}",
                "file_path": None
            }

    def generate_github_qr_code(self) -> Dict[str, Any]:
        """
        Generates a QR code for the specific GitHub repository URL
        and saves it as 'github_test.png' on the user's Desktop,
        as per the user's request.

        Returns:
            Dict[str, Any]: A dictionary containing the status of the operation.
                            Keys include:
                            - 'success' (bool): True if the operation was successful, False otherwise.
                            - 'message' (str): A descriptive message about the operation's outcome.
                            - 'file_path' (Optional[str]): The absolute path to the saved QR code image if successful.
        """
        user_request_url = "https://github.com/traehq/trae"
        user_request_filename = "github_test.png"
        
        # Call the more general generate_qr_code method with specific parameters
        return self.generate_qr_code(url=user_request_url, filename=user_request_filename)

if __name__ == "__main__":
    # Example usage based on the user's specific request:
    generator = QRCodeGeneratorTool()
    
    print("Generating QR code for GitHub repository as requested...")
    result = generator.generate_github_qr_code()

    if result["success"]:
        print(f"\nSuccess: {result['message']}")
        print(f"File path: {result['file_path']}")
    else:
        print(f"\nFailure: {result['message']}")

    # Example of using the general method for a different request
    # print("\nGenerating a different QR code...")
    # custom_result = generator.generate_qr_code(
    #     url="https://www.example.com",
    #     filename="example_qr.png",
    #     save_dir="/tmp" # Example of saving to a different directory
    # )
    # if custom_result["success"]:
    #     print(f"Success: {custom_result['message']}")
    # else:
    #     print(f"Failure: {custom_result['message']}")
