
import qrcode
from PIL import Image
import os
import sys
from typing import Dict, Any, Optional

class QRCodeGenerator:
    """
    A specialized tool for generating QR codes with custom logos.

    This class provides methods to create QR codes for a given URL, embed a
    custom logo, and save the resulting image. It's designed for safe
    operations and compatibility with macOS and Windows.
    """

    def __init__(self):
        """
        Initializes the QRCodeGenerator.
        """
        pass

    def _get_desktop_path(self) -> Optional[str]:
        """
        Safely determines the user's Desktop path for common operating systems.

        Returns:
            str: The absolute path to the Desktop directory, or None if not found.
        """
        try:
            if sys.platform.startswith('win'):
                desktop_path = os.path.join(os.environ['USERPROFILE'], 'Desktop')
            elif sys.platform.startswith('darwin'):
                desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            else:  # Linux and other Unix-like systems
                desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")

            if os.path.isdir(desktop_path):
                return desktop_path
            else:
                # Fallback for systems where Desktop might not be named exactly that
                potential_paths = [
                    os.path.join(os.path.expanduser("~"), "Descargas"), # Portuguese for Downloads
                    os.path.join(os.path.expanduser("~"), "Downloads"), # English for Downloads
                    os.path.join(os.path.expanduser("~"), "Bureau"),    # French for Desktop
                    os.path.join(os.path.expanduser("~"), "Escritorio"), # Spanish for Desktop
                ]
                for path in potential_paths:
                    if os.path.isdir(path):
                        return path
                return None
        except Exception:
            return None

    def generate_qr_with_logo(
        self,
        url: str = "https://trae.ai",
        logo_path: Optional[str] = None,
        output_filename: str = "trae_qr_with_logo.png",
        error_correction: int = qrcode.constants.ERROR_CORRECT_H,
        box_size: int = 10,
        border: int = 4,
        logo_size_ratio: float = 0.25
    ) -> Dict[str, Any]:
        """
        Generates a QR code for a given URL with an optional custom logo.

        Args:
            url (str): The URL to encode in the QR code. Defaults to "https://trae.ai".
            logo_path (Optional[str]): The absolute or relative path to the logo image file.
                                      If None, no logo will be embedded. Defaults to None.
            output_filename (str): The desired name for the output QR code image file.
                                   Defaults to "trae_qr_with_logo.png".
            error_correction (int): The error correction level for the QR code.
                                    Defaults to ERROR_CORRECT_H (high).
            box_size (int): The size of each box (pixel) in the QR code. Defaults to 10.
            border (int): The thickness of the border around the QR code. Defaults to 4.
            logo_size_ratio (float): The ratio of the logo's size to the QR code's size.
                                     Must be between 0 and 1. Defaults to 0.25.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the operation.
                            'success' (bool): True if successful, False otherwise.
                            'message' (str): A descriptive message about the operation.
                            'filepath' (Optional[str]): The absolute path to the saved QR code image if successful.
        """
        desktop_path = self._get_desktop_path()
        if not desktop_path:
            return {
                "success": False,
                "message": "Could not determine a suitable Desktop or Downloads path.",
                "filepath": None
            }

        # Resolve logo path to an absolute path if it's relative
        absolute_logo_path = None
        if logo_path:
            absolute_logo_path = os.path.abspath(logo_path)

        output_filepath = os.path.join(desktop_path, output_filename)

        # --- Input Validation ---
        if not url:
            return {
                "success": False,
                "message": "URL cannot be empty.",
                "filepath": None
            }
        if not isinstance(url, str):
            return {
                "success": False,
                "message": "URL must be a string.",
                "filepath": None
            }
        if logo_path is not None and not isinstance(logo_path, str):
            return {
                "success": False,
                "message": "logo_path must be a string path or None.",
                "filepath": None
            }
        if absolute_logo_path and not os.path.isfile(absolute_logo_path):
            return {
                "success": False,
                "message": f"Logo file not found at: {absolute_logo_path}",
                "filepath": None
            }
        if not isinstance(output_filename, str) or not output_filename.strip():
            return {
                "success": False,
                "message": "output_filename must be a non-empty string.",
                "filepath": None
            }
        if not isinstance(logo_size_ratio, (int, float)) or not (0 < logo_size_ratio < 1):
            return {
                "success": False,
                "message": "logo_size_ratio must be a float between 0 and 1.",
                "filepath": None
            }
        if not isinstance(box_size, int) or box_size <= 0:
            return {
                "success": False,
                "message": "box_size must be a positive integer.",
                "filepath": None
            }
        if not isinstance(border, int) or border < 0:
            return {
                "success": False,
                "message": "border must be a non-negative integer.",
                "filepath": None
            }

        try:
            # 1. Generate QR Code
            qr = qrcode.QRCode(
                version=None,
                error_correction=error_correction,
                box_size=box_size,
                border=border,
            )
            qr.add_data(url)
            qr.make(fit=True)

            qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

            # 2. Prepare Logo
            logo_img = None
            if absolute_logo_path:
                try:
                    logo_img = Image.open(absolute_logo_path).convert("RGBA")
                except FileNotFoundError:
                    return {
                        "success": False,
                        "message": f"Logo file not found at: {absolute_logo_path}",
                        "filepath": None
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "message": f"Error opening logo image '{absolute_logo_path}': {e}",
                        "filepath": None
                    }

                # Calculate logo size
                qr_width, qr_height = qr_img.size
                max_logo_width = int(qr_width * logo_size_ratio)
                max_logo_height = int(qr_height * logo_size_ratio)
                logo_img.thumbnail((max_logo_width, max_logo_height), Image.Resampling.LANCZOS) # Use LANCZOS for better resizing

                # Calculate position to center the logo
                logo_x = (qr_width - logo_img.width) // 2
                logo_y = (qr_height - logo_img.height) // 2

            # 3. Combine QR Code and Logo
            if logo_img:
                # Create a transparent background for the QR code to paste the logo onto
                # This ensures the logo doesn't obscure QR code modules if the logo has transparency.
                qr_img_with_logo = qr_img.copy()

                # Paste the logo onto the QR code. The logo's alpha channel will handle transparency.
                qr_img_with_logo.paste(logo_img, (logo_x, logo_y), logo_img)
                final_img_to_save = qr_img_with_logo
            else:
                final_img_to_save = qr_img

            # 4. Save the Image
            final_img_to_save.save(output_filepath)

            return {
                "success": True,
                "message": f"QR code for '{url}' with logo saved successfully to '{output_filepath}'.",
                "filepath": os.path.abspath(output_filepath)
            }

        except FileNotFoundError:
            return {
                "success": False,
                "message": f"Could not save QR code. Directory might not exist or lack permissions: {desktop_path}",
                "filepath": None
            }
        except ImportError:
            return {
                "success": False,
                "message": "Required libraries 'qrcode' and 'Pillow' are not installed. Please install them using 'pip install qrcode[pil]'.",
                "filepath": None
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"An unexpected error occurred: {e}",
                "filepath": None
            }

if __name__ == "__main__":
    # Example Usage:
    # To run this example, you need a logo file.
    # Replace 'path/to/your/logo.png' with the actual path to your logo.
    # If you don't have a logo, the generator will still work without it.

    generator = QRCodeGenerator()

    # --- Case 1: User Request - Create QR for 'https://trae.ai' with a logo to Desktop ---
    print("--- Executing User Request: QR for 'https://trae.ai' with logo to Desktop ---")

    # Attempt to find or create a placeholder logo for demonstration
    demo_logo_path = None
    potential_logo_names = ['logo.png', 'company_logo.png', 'icon.png', 'app_icon.png']
    found_logo = False

    # Check if a logo exists in the current directory or common paths
    for logo_name in potential_logo_names:
        if os.path.exists(logo_name):
            demo_logo_path = logo_name
            found_logo = True
            print(f"Using existing logo found at: {os.path.abspath(demo_logo_path)}")
            break

    # If no logo found, create a simple dummy logo
    if not found_logo:
        dummy_logo_filename = "temp_trae_logo_placeholder.png"
        try:
            if not os.path.exists(dummy_logo_filename):
                dummy_img = Image.new('RGBA', (150, 150), color=(70, 130, 180, 200)) # Steel Blue with transparency
                # Add some text to the dummy logo
                from PIL import ImageDraw, ImageFont
                draw = ImageDraw.Draw(dummy_img)
                try:
                    # Try to load a common font
                    font = ImageFont.truetype("arial.ttf", 30)
                except IOError:
                    font = ImageFont.load_default() # Fallback to default font
                draw.text((10, 60), "TRAE", fill=(255, 255, 255), font=font)
                dummy_img.save(dummy_logo_filename)
                demo_logo_path = dummy_logo_filename
                print(f"Created a temporary placeholder logo at: {os.path.abspath(demo_logo_path)}")
        except ImportError:
            print("Pillow (PIL) is required to create a placeholder logo. Please install it: pip install Pillow")
            print("Skipping QR generation with logo.")
        except Exception as e:
            print(f"Could not create placeholder logo: {e}")
            print("Skipping QR generation with logo.")

    if demo_logo_path:
        user_request_result = generator.generate_qr_with_logo(
            url="https://trae.ai",
            logo_path=demo_logo_path,
            output_filename="trae_qr_with_logo.png"
        )
        print(user_request_result)
        print("-" * 60)

        # Clean up the dummy logo if it was created for this run
        if demo_logo_path == dummy_logo_filename and os.path.exists(dummy_logo_filename):
            try:
                os.remove(dummy_logo_filename)
                print(f"Removed temporary placeholder logo: {dummy_logo_filename}")
            except Exception as e:
                print(f"Error removing temporary placeholder logo: {e}")

    else:
        print("Could not find or create a logo. Skipping QR generation with logo.")
        print("-" * 60)

    # --- Case 2: Default URL, no logo specified ---
    print("--- Generating QR code with default URL and no logo ---")
    result_no_logo = generator.generate_qr_with_logo()
    print(result_no_logo)
    print("-" * 60)

    # --- Case 3: Using custom parameters and a valid logo (if found) ---
    print("--- Generating QR code with custom parameters and a logo ---")
    if demo_logo_path and os.path.exists(demo_logo_path): # Re-check if demo_logo_path is still valid
        custom_params_result = generator.generate_qr_with_logo(
            url="https://trae.ai/about",
            logo_path=demo_logo_path,
            output_filename="custom_trae_qr.png",
            box_size=15,
            border=2,
            logo_size_ratio=0.3,
            error_correction=qrcode.constants.ERROR_CORRECT_Q # Medium error correction
        )
        print(custom_params_result)
        print("-" * 60)
    else:
        print("No valid logo found for custom parameter test. Skipping.")
        print("-" * 60)


    # --- Case 4: Error handling - Invalid logo path ---
    print("--- Testing error handling: Invalid logo path ---")
    result_invalid_logo = generator.generate_qr_with_logo(logo_path="/non/existent/logo.jpg")
    print(result_invalid_logo)
    print("-" * 60)

    # --- Case 5: Error handling - Empty URL ---
    print("--- Testing error handling: Empty URL ---")
    result_empty_url = generator.generate_qr_with_logo(url="")
    print(result_empty_url)
    print("-" * 60)

    # --- Case 6: Error handling - Invalid logo_size_ratio ---
    print("--- Testing error handling: Invalid logo_size_ratio ---")
    result_invalid_ratio = generator.generate_qr_with_logo(logo_size_ratio=1.5)
    print(result_invalid_ratio)
    print("-" * 60)

    # --- Case 7: Error handling - Invalid box_size ---
    print("--- Testing error handling: Invalid box_size ---")
    result_invalid_box_size = generator.generate_qr_with_logo(box_size=0)
    print(result_invalid_box_size)
    print("-" * 60)

    # Clean up any remaining dummy logo if it was created and not yet removed
    if 'dummy_logo_filename' in locals() and os.path.exists(dummy_logo_filename):
        try:
            os.remove(dummy_logo_filename)
            print(f"Cleaned up remaining temporary placeholder logo: {dummy_logo_filename}")
        except Exception as e:
            print(f"Error during final cleanup of temporary placeholder logo: {e}")
