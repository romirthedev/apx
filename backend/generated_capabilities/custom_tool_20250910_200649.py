
import qrcode
import os
from pathlib import Path
from typing import Dict, Any, Union

class QRCodeTool:
    """
    A specialized tool class for generating and managing QR codes.
    This class provides methods to create QR codes from given data and save them
    to a specified location, with robust error handling and structured return values.
    It is designed to be compatible with macOS.
    """

    def __init__(self):
        """Initializes the QRCodeTool."""
        pass

    def generate_qr_code(self, data: str, filename: str, directory: Union[str, Path]) -> Dict[str, Any]:
        """
        Generates a QR code for the given data and saves it to the specified filename
        in the provided directory.

        Args:
            data (str): The data to encode in the QR code.
            filename (str): The name of the file to save the QR code image as (e.g., 'my_qr.png').
            directory (Union[str, Path]): The directory where the QR code image will be saved.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the operation.
                            Keys include:
                            - 'success' (bool): True if the operation was successful, False otherwise.
                            - 'message' (str): A descriptive message about the outcome.
                            - 'filepath' (str, optional): The full path to the generated QR code file
                                                          if successful.
        """
        if not data:
            return {'success': False, 'message': "Error: Data to encode cannot be empty."}
        if not filename:
            return {'success': False, 'message': "Error: Filename cannot be empty."}
        if not directory:
            return {'success': False, 'message': "Error: Directory cannot be empty."}

        try:
            output_dir = Path(directory)
            if not output_dir.exists():
                try:
                    output_dir.mkdir(parents=True, exist_ok=True)
                    print(f"Created directory: {output_dir}")
                except OSError as e:
                    return {'success': False, 'message': f"Error: Could not create directory '{output_dir}': {e}"}
            elif not output_dir.is_dir():
                return {'success': False, 'message': f"Error: '{output_dir}' exists but is not a directory."}

            full_filepath = output_dir / filename

            # Generate the QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            # Save the QR code image
            img.save(full_filepath)

            return {
                'success': True,
                'message': f"QR code successfully generated and saved to {full_filepath}",
                'filepath': str(full_filepath)
            }

        except FileNotFoundError:
            return {
                'success': False,
                'message': f"Error: Could not find the specified directory to save the file: {directory}"
            }
        except PermissionError:
            return {
                'success': False,
                'message': f"Error: Permission denied to write to the directory: {directory}. "
                           "Please check your file system permissions."
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"An unexpected error occurred during QR code generation: {e}"
            }

    def generate_github_qr_to_desktop(self) -> Dict[str, Any]:
        """
        Generates a QR code for 'https://github.com/traehq/trae' and saves it
        as 'github_qr.png' on the user's Desktop.

        This method specifically handles the user's request and ensures the file
        is saved in a standard user directory on macOS. It leverages the
        `generate_qr_code` method for flexibility and robustness.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the operation.
                            Keys include:
                            - 'success' (bool): True if the operation was successful, False otherwise.
                            - 'message' (str): A descriptive message about the outcome.
                            - 'filepath' (str, optional): The full path to the generated QR code file
                                                          if successful.
        """
        data_to_encode = 'https://github.com/traehq/trae'
        filename = 'github_qr.png'

        # Determine the user's desktop path safely for macOS
        try:
            home_dir = Path.home()
            desktop_path = home_dir / 'Desktop'

            if not desktop_path.is_dir():
                return {
                    'success': False,
                    'message': f"Desktop directory not found at {desktop_path}. Cannot save QR code."
                }
        except Exception as e:
            return {
                'success': False,
                'message': f"Error: Could not determine user's desktop path: {e}"
            }

        return self.generate_qr_code(data=data_to_encode, filename=filename, directory=desktop_path)

if __name__ == '__main__':
    # Example usage:
    qr_tool = QRCodeTool()

    # --- Specific User Request ---
    print("Executing specific user request: Generate GitHub QR code to Desktop.")
    result_github = qr_tool.generate_github_qr_to_desktop()
    print(result_github)
    if result_github['success']:
        print(f"QR code for GitHub saved to: {result_github['filepath']}")
        print(f"Please check your Desktop for '{os.path.basename(result_github['filepath'])}'")
    else:
        print(f"Failed to generate GitHub QR code: {result_github['message']}")

    print("\n" + "="*50 + "\n")

    # --- General Purpose Example ---
    print("Executing general purpose QR code generation.")
    custom_data = "https://www.example.com"
    custom_filename = "example_website_qr.png"
    # Using a temporary directory for demonstration, or you could specify a known path
    custom_directory = Path("./temp_qrcodes") # Creates a 'temp_qrcodes' folder in the current directory

    result_custom = qr_tool.generate_qr_code(data=custom_data, filename=custom_filename, directory=custom_directory)
    print(result_custom)
    if result_custom['success']:
        print(f"Custom QR code saved to: {result_custom['filepath']}")
    else:
        print(f"Failed to generate custom QR code: {result_custom['message']}")

    print("\n" + "="*50 + "\n")

    # --- Error Handling Examples ---
    print("Demonstrating error handling:")
    print("1. Empty data:")
    error_result_1 = qr_tool.generate_qr_code("", "empty_data.png", "./temp_qrcodes")
    print(error_result_1)

    print("\n2. Empty filename:")
    error_result_2 = qr_tool.generate_qr_code("some data", "", "./temp_qrcodes")
    print(error_result_2)

    print("\n3. Invalid directory path (non-existent file instead of dir):")
    # Assuming 'invalid_path_test.txt' does not exist or is a file
    error_result_3 = qr_tool.generate_qr_code("some data", "invalid_dir.png", "./invalid_path_test.txt/qr_code")
    print(error_result_3)

    # To test permission error, you would need to manually set restrictive permissions on a directory.
    # For example, on macOS/Linux:
    # mkdir /tmp/no_write_access
    # chmod 555 /tmp/no_write_access # Read/execute only
    # print("\n4. Permission denied (requires manual setup):")
    # error_result_4 = qr_tool.generate_qr_code("some data", "permission_test.png", "/tmp/no_write_access")
    # print(error_result_4)
    # os.chmod("/tmp/no_write_access", 0o755) # Restore permissions
    # shutil.rmtree("/tmp/no_write_access")
