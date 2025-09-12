
import qrcode
import os
from typing import Dict, Any, Optional

class QRCodeGeneratorTool:
    """
    A specialized tool for generating QR codes with enhanced error handling,
    input validation, and structured output, tailored for specific user requests.
    """

    def __init__(self):
        """
        Initializes the QRCodeGeneratorTool.
        """
        pass

    def generate_qr_code(self, url: str, filename: str) -> Dict[str, Any]:
        """
        Generates a QR code for a given URL and saves it to a specified filename.

        This method is designed to be flexible and handle various QR code generation
        requests. It includes robust error handling, input validation, and checks
        for write permissions before attempting to save the file.

        Args:
            url (str): The URL to encode in the QR code.
            filename (str): The desired name for the output PNG file.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the operation.
                            Keys include:
                            - 'success' (bool): True if the QR code was generated and saved successfully, False otherwise.
                            - 'message' (str): A descriptive message about the operation's outcome.
                            - 'filepath' (str, optional): The absolute path to the saved QR code image if successful.
        """
        # --- Input Validation ---
        if not isinstance(url, str) or not url:
            return {
                "success": False,
                "message": "Invalid input: URL must be a non-empty string.",
            }
        if not isinstance(filename, str) or not filename:
            return {
                "success": False,
                "message": "Invalid input: Filename must be a non-empty string.",
            }
        if not filename.lower().endswith(".png"):
            return {
                "success": False,
                "message": "Invalid input: Filename must end with '.png'.",
            }

        filepath: str = os.path.abspath(filename)
        output_directory: str = os.path.dirname(filepath)

        try:
            # --- Dependency Check ---
            try:
                import qrcode
                from PIL import Image
            except ImportError:
                return {
                    "success": False,
                    "message": "Error: Required libraries ('qrcode' and 'Pillow') are not installed. "
                               "Please install them using 'pip install qrcode[pil]'.",
                }

            # --- Permission Check ---
            if not os.access(output_directory, os.W_OK):
                return {
                    "success": False,
                    "message": f"Permission denied: Cannot write to the directory '{output_directory}'. "
                               f"Current working directory is '{os.getcwd()}'.",
                }

            # --- QR Code Generation ---
            qr = qrcode.QRCode(
                version=1,  # Controls the size of the QR Code, 1 is the smallest (21x21 matrix)
                error_correction=qrcode.constants.ERROR_CORRECT_L,  # L: ~7% errors can be corrected
                box_size=10,  # Controls how many pixels each "box" of the QR code is
                border=4,  # Controls how many boxes thick the border should be
            )
            qr.add_data(url)
            qr.make(fit=True)  # Ensure the data fits within the QR code version

            img = qr.make_image(fill_color="black", back_color="white")

            # --- File Saving ---
            img.save(filepath)

            return {
                "success": True,
                "message": f"QR code for '{url}' successfully generated and saved to '{filepath}'.",
                "filepath": filepath,
            }

        except Exception as e:
            # Catch any other unexpected errors during generation or saving
            return {
                "success": False,
                "message": f"An unexpected error occurred while generating or saving the QR code for '{url}': {e}",
            }

    def generate_github_qr_code(self) -> Dict[str, Any]:
        """
        Generates a QR code specifically for 'https://github.com' and saves it as 'github_qr.png'.

        This method is a convenience wrapper that directly addresses the user's
        specific request, using the more general `generate_qr_code` method internally.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the operation.
                            Keys include:
                            - 'success' (bool): True if the QR code was generated and saved successfully, False otherwise.
                            - 'message' (str): A descriptive message about the operation's outcome.
                            - 'filepath' (str, optional): The absolute path to the saved QR code image if successful.
        """
        github_url: str = "https://github.com"
        github_filename: str = "github_qr.png"
        return self.generate_qr_code(url=github_url, filename=github_filename)


if __name__ == '__main__':
    # Example usage demonstrating the specific request:
    print("--- Generating GitHub QR Code ---")
    tool = QRCodeGeneratorTool()
    result_github = tool.generate_github_qr_code()

    print(f"Operation Success: {result_github.get('success')}")
    print(f"Message: {result_github.get('message')}")
    if result_github.get('success'):
        print(f"File Path: {result_github.get('filepath')}")

    print("\n" + "="*30 + "\n")

    # Example usage demonstrating the more general function with custom inputs:
    print("--- Generating Custom QR Code ---")
    custom_url = "https://www.python.org"
    custom_filename = "python_org_qr.png"
    result_custom = tool.generate_qr_code(url=custom_url, filename=custom_filename)

    print(f"Operation Success: {result_custom.get('success')}")
    print(f"Message: {result_custom.get('message')}")
    if result_custom.get('success'):
        print(f"File Path: {result_custom.get('filepath')}")

    print("\n" + "="*30 + "\n")

    # Example of handling potential validation errors:
    print("--- Testing Input Validation ---")
    invalid_filename_result = tool.generate_qr_code(url="http://example.com", filename="myqr.jpg")
    print(f"Invalid Filename Test - Success: {invalid_filename_result.get('success')}")
    print(f"Message: {invalid_filename_result.get('message')}")

    empty_url_result = tool.generate_qr_code(url="", filename="empty_url_qr.png")
    print(f"Empty URL Test - Success: {empty_url_result.get('success')}")
    print(f"Message: {empty_url_result.get('message')}")

    # Example of handling potential permission issues (simulated)
    # To test this, you would typically need to create a directory and
    # remove write permissions for it, or run the script in an environment
    # where the current directory is not writable.
    # This example is commented out as it requires specific OS-level setup
    # to reliably demonstrate.
    # print("\n" + "="*30 + "\n")
    # print("--- Testing Permission Error Handling (Simulated) ---")
    # try:
    #     # Create a directory with read-only permissions (for owner, group, others)
    #     read_only_dir = "read_only_test_dir"
    #     os.makedirs(read_only_dir, mode=0o444)
    #     original_cwd = os.getcwd()
    #     os.chdir(read_only_dir)
    #
    #     permission_denied_result = tool.generate_github_qr_code()
    #     print(f"Permission Denied Test - Success: {permission_denied_result.get('success')}")
    #     print(f"Message: {permission_denied_result.get('message')}")
    #
    # finally:
    #     # Clean up: change back to original directory and remove the test directory
    #     os.chdir(original_cwd)
    #     if os.path.exists(read_only_dir):
    #         try:
    #             os.rmdir(read_only_dir)
    #         except OSError as e:
    #             print(f"Could not remove directory {read_only_dir}: {e}")
