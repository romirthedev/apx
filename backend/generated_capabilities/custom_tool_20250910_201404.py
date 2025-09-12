
import qrcode
import os
from typing import Dict, Any, Optional

class QRCodeGenerator:
    """
    A specialized tool for generating QR codes and saving them to a specified location.
    Designed for compatibility with macOS and includes robust error handling.
    """

    def __init__(self) -> None:
        """Initializes the QRCodeGenerator."""
        self.desktop_path: str = os.path.join(os.path.expanduser("~"), "Desktop")
        os.makedirs(self.desktop_path, exist_ok=True)

    def _validate_url(self, url: str) -> bool:
        """Validates if the provided URL is not empty and potentially looks like a URL."""
        if not url:
            return False
        # A more sophisticated URL validation could be added here if needed,
        # e.g., using urlparse, but for QR generation, a non-empty string is often sufficient.
        return True

    def _validate_filename(self, filename: str) -> bool:
        """Validates the filename for emptiness and acceptable extensions."""
        if not filename:
            return False
        supported_extensions = ('.png', '.jpg', '.jpeg', '.bmp')
        if not filename.lower().endswith(supported_extensions):
            return False
        return True

    def generate_qr_code(self, url: str, filename: str = "qrcode.png", output_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Generates a QR code for a given URL and saves it as an image file.

        Args:
            url: The URL to encode in the QR code.
            filename: The desired name for the output image file (e.g., "my_qr.png").
            output_dir: An optional directory to save the QR code. If None, it defaults to the Desktop.

        Returns:
            A dictionary containing the result of the operation:
            {'success': bool, 'message': str, 'data': { 'filepath': str } | None}
        """
        if not self._validate_url(url):
            return {"success": False, "message": "URL cannot be empty.", "data": None}
        if not self._validate_filename(filename):
            return {"success": False, "message": "Invalid filename or extension. Supported formats are .png, .jpg, .jpeg, .bmp", "data": None}

        target_directory = output_dir if output_dir else self.desktop_path
        os.makedirs(target_directory, exist_ok=True) # Ensure target directory exists
        full_filepath = os.path.join(target_directory, filename)

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
            img.save(full_filepath)

            return {"success": True, "message": f"QR code generated and saved to {full_filepath}", "data": {"filepath": full_filepath}}

        except qrcode.exceptions.DataOverflowError:
            return {"success": False, "message": f"The provided URL is too long for the QR code version. Try a shorter URL.", "data": None}
        except FileNotFoundError:
            return {"success": False, "message": f"The specified output directory does not exist: {target_directory}", "data": None}
        except PermissionError:
            return {"success": False, "message": f"Permission denied to write to the specified location: {full_filepath}", "data": None}
        except Exception as e:
            return {"success": False, "message": f"An unexpected error occurred during QR code generation: {str(e)}", "data": None}

    def create_specific_github_qr_for_desktop(self) -> Dict[str, Any]:
        """
        Creates a QR code for the specific GitHub URL (https://github.com/traehq/trae)
        and saves it as 'github_final_test.png' on the user's Desktop.
        This method directly addresses the user's specific request.

        Returns:
            A dictionary containing the result of the operation, as described in
            generate_qr_code.
        """
        url_to_encode = "https://github.com/traehq/trae"
        output_filename = "github_final_test.png"
        # Explicitly use the default output_dir (Desktop) by not providing it
        return self.generate_qr_code(url_to_encode, output_filename)

if __name__ == "__main__":
    generator = QRCodeGenerator()

    # --- Handling the Specific User Request ---
    print("--- Executing Specific User Request ---")
    print("Creating QR code for https://github.com/traehq/trae and saving as github_final_test.png on Desktop...")
    specific_request_result = generator.create_specific_github_qr_for_desktop()
    print(f"Result: {specific_request_result}")
    print("---------------------------------------")

    # --- Example of generating a custom QR code ---
    print("\n--- Example: Custom QR Code Generation ---")
    custom_url = "https://www.python.org"
    custom_filename = "python_org_qr.png"
    print(f"Generating QR code for '{custom_url}' as '{custom_filename}' on Desktop...")
    custom_result = generator.generate_qr_code(custom_url, custom_filename)
    print(f"Result: {custom_result}")
    print("-----------------------------------------")

    # --- Example with a custom output directory ---
    print("\n--- Example: QR Code to a Specific Directory ---")
    temp_dir = "temp_qr_codes"
    os.makedirs(temp_dir, exist_ok=True)
    custom_dir_url = "https://www.example.com"
    custom_dir_filename = "example_in_subdir.png"
    print(f"Generating QR code for '{custom_dir_url}' as '{custom_dir_filename}' in '{temp_dir}/'...")
    custom_dir_result = generator.generate_qr_code(custom_dir_url, custom_dir_filename, output_dir=temp_dir)
    print(f"Result: {custom_dir_result}")
    print("-----------------------------------------------")


    # --- Error Handling Examples ---
    print("\n--- Error Handling Examples ---")

    # Invalid URL
    print("\nAttempting to generate QR code with an empty URL...")
    empty_url_result = generator.generate_qr_code("", "empty_url_test.png")
    print(f"Result: {empty_url_result}")

    # Invalid filename extension
    print("\nAttempting to generate QR code with an invalid filename extension...")
    invalid_ext_result = generator.generate_qr_code("https://example.com", "invalid_extension.txt")
    print(f"Result: {invalid_ext_result}")

    # Filename too long (though qrcode library handles data length, not filename length)
    # This is more about potential OS limits or conceptual error for QR codes.
    # The qrcode library's DataOverflowError is more relevant for URL length.
    print("\nAttempting to generate QR code with URL too long for QR code version...")
    long_url = "https://this.is.a.very.long.url.that.will.exceed.the.maximum.capacity.of.a.single.qr.code.version.1.to.test.the.error.handling.for.data.overflow.and.ensure.that.the.tool.gracefully.handles.such.situations.by.returning.an.appropriate.error.message.to.the.user.so.they.can.take.corrective.action.like.shortening.the.url.or.using.a.more.complex.qr.code.version.if.supported.by.the.library.and.application.constraints."
    long_url_result = generator.generate_qr_code(long_url, "long_url_test.png")
    print(f"Result: {long_url_result}")

    # Trying to save to a non-existent directory without create_missing_dirs=True
    # (Note: generate_qr_code now ensures the directory exists, so this specific error is less likely unless permissions are an issue)
    # For demonstration, let's simulate a permission error if possible or a path issue.
    # On most systems, Desktop is writable. A more robust test would involve tempfile or mocking.
    print("\nAttempting to generate QR code to a potentially inaccessible location (simulated)...")
    # This might not fail with PermissionError unless actually lacking permissions.
    # We'll try to save it to a deeply nested path that might not exist by default.
    # The `os.makedirs` within the function should handle path creation.
    # A more direct PermissionError would require specific OS setup.
    try:
        # Temporarily create a scenario where directory creation fails due to permissions or path issues
        # This is hard to reliably simulate cross-platform without OS-specific setup.
        # The current implementation with os.makedirs(..., exist_ok=True) is quite robust.
        # A PermissionError would typically occur if the user running the script doesn't have write access
        # to the Desktop or the specified output_dir.
        if os.path.exists("/root/non_writable_dir"): # Example of a generally non-writable dir on Unix-like systems
            permission_error_result = generator.generate_qr_code("https://test.com", "perm_test.png", output_dir="/root/non_writable_dir")
            print(f"Result (simulated permission issue): {permission_error_result}")
        else:
            print("Skipping simulated permission error test as '/root/non_writable_dir' does not exist or is not a good test case.")
    except Exception as e:
        print(f"Could not fully simulate permission error test: {e}")

    print("---------------------------------")

    # Clean up temporary directory if created
    if os.path.exists(temp_dir):
        try:
            os.rmdir(temp_dir)
            print(f"\nCleaned up temporary directory: {temp_dir}")
        except OSError as e:
            print(f"\nCould not clean up temporary directory {temp_dir}: {e}")

