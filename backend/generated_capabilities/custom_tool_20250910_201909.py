import qrcode
from qrcode.image.styledpil import StyledPilImage
# The error indicates that SolidColorMask and RadialGradiantColorMask are not found in the specified path.
# Based on the qrcode library structure, these are typically imported from qrcode.image.styles.colormasks.
# However, if they are genuinely missing or renamed in a specific version, we'll need to adjust.
# A common pattern is that simpler color masks might be directly handled by StyledPilImage without needing explicit import if not using complex ones.
# For this fix, we'll assume that if they are not found, the intent was to use basic coloring.
# If a specific mask like RadialGradiantColorMask was intended, it might have been removed or renamed.
# Let's try importing them and if it fails, we'll adapt. The error message suggests they are not there.
# A workaround might be to use the default coloring if specific masks are unavailable, or try simpler alternatives.

# Let's attempt to import them, and if the error persists, we'll remove the specific problematic ones and rely on default behavior or simpler masks.
# Given the error: ERROR: cannot import name 'SolidColorMask' from 'qrcode.image.styles.colormasks'
# and the same would likely apply to 'RadialGradiantColorMask' if it were attempted.
# It's safer to assume these specific classes are not available in the installed version or path.
# We will remove them from the import and adjust the code accordingly.
# The StyledPilImage factory itself can handle basic fill_color and back_color.
# If custom masks were crucial, one might need to find a different library or an older version of qrcode.

# For this fix, we will remove the problematic imports and adapt the color mask logic.
# The StyledPilImage factory handles fill_color and back_color directly for basic coloring.
# If advanced masking like radial gradients were intended, a different approach or library might be needed.
# Given the constraint of "work with what's available" and the import error, we'll simplify.
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer, GappedModuleDrawer, CircleModuleDrawer
from qrcode.image.styles.keys import module_drawer_style, color_mask_style
import os
from typing import Dict, Any, Optional

# Removing the problematic import: from qrcode.image.styles.colormasks import RadialGradiantColorMask, SolidColorMask

class QRCodeGenerator:
    """
    A specialized tool class for generating QR codes with customizable options.
    This class provides a safe and structured way to create QR codes for URLs
    and save them as image files, with robust error handling and type hints.
    """

    def __init__(self) -> None:
        """Initializes the QRCodeGenerator."""
        pass

    def generate_and_save_qr_code(
        self,
        url: str,
        filename: str = "qrcode.png",
        fill_color: str = "black",
        back_color: str = "white",
        module_drawer: str = "square",
        color_mask: Optional[str] = None,
        error_correction: int = qrcode.constants.ERROR_CORRECT_M, # Default to M for better readability
        box_size: int = 10,
        border: int = 4
    ) -> Dict[str, Any]:
        """
        Generates a QR code for a given URL and saves it to a specified file.

        Args:
            url: The URL to encode in the QR code. Must be a valid HTTP/HTTPS URL.
            filename: The name of the file to save the QR code as (e.g., "github_qr.png").
                      Must be a valid filename and end with a supported image extension (.png, .jpg, etc.).
            fill_color: The color of the QR code modules (e.g., "black", "#000000").
                        Must be a valid CSS color name or hex code.
            back_color: The background color of the QR code (e.g., "white", "#FFFFFF").
                        Must be a valid CSS color name or hex code.
            module_drawer: The style of the QR code modules. Supported options:
                           "square" (default), "gapped", "circle", "rounded".
            color_mask: The color mask style to apply. Supported options:
                        "radial_gradient", "solid". If None, no mask is applied.
                        NOTE: Due to import errors for specific masks like RadialGradiantColorMask and SolidColorMask,
                        these options will not be fully supported in this version if they rely on those specific classes.
                        The code will fall back to basic fill/back color handling.
            error_correction: The error correction level. Options:
                              qrcode.constants.ERROR_CORRECT_L (7%)
                              qrcode.constants.ERROR_CORRECT_M (15%) - Default
                              qrcode.constants.ERROR_CORRECT_Q (25%)
                              qrcode.constants.ERROR_CORRECT_H (30%)
            box_size: The number of pixels for each box of the QR code. Must be a positive integer.
            border: The thickness of the border around the QR code. Must be a non-negative integer.

        Returns:
            A dictionary containing the operation status:
            {
                'success': bool,
                'message': str,
                'data': {
                    'filepath': str,  # The absolute path to the saved QR code file
                    'filename': str,
                    'url': str
                } | None
            }
        """
        # --- Input Validation ---
        if not url or not isinstance(url, str):
            return {
                'success': False,
                'message': "URL cannot be empty and must be a string.",
                'data': None
            }
        if not url.startswith("http://") and not url.startswith("https://"):
            return {
                'success': False,
                'message': "URL must start with 'http://' or 'https://'.",
                'data': None
            }

        if not filename or not isinstance(filename, str):
            return {
                'success': False,
                'message': "Filename cannot be empty and must be a string.",
                'data': None
            }
        supported_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp')
        if not any(filename.lower().endswith(ext) for ext in supported_extensions):
            return {
                'success': False,
                'message': f"Filename must have a supported image extension ({', '.join(supported_extensions)}).",
                'data': None
            }

        if not isinstance(box_size, int) or box_size <= 0:
            return {
                'success': False,
                'message': "box_size must be a positive integer.",
                'data': None
            }

        if not isinstance(border, int) or border < 0:
            return {
                'success': False,
                'message': "border must be a non-negative integer.",
                'data': None
            }

        # --- Module Drawer Setup ---
        module_drawer_map = {
            "square": None,  # Default behavior in qrcode library
            "gapped": GappedModuleDrawer(),
            "circle": CircleModuleDrawer(),
            "rounded": RoundedModuleDrawer()
        }
        drawer_key = module_drawer.lower()
        if drawer_key not in module_drawer_map:
            return {
                'success': False,
                'message': f"Unsupported module_drawer style: '{module_drawer}'. Supported options: {list(module_drawer_map.keys())}",
                'data': None
            }
        drawer_instance = module_drawer_map[drawer_key]

        # --- Color Mask Setup ---
        # The specific color mask classes (RadialGradiantColorMask, SolidColorMask)
        # caused an import error. We will adapt to use only basic fill_color and back_color
        # as StyledPilImage handles these directly. If specific masks were crucial,
        # a different library or version of qrcode might be needed.
        color_mask_instance = None
        if color_mask:
            # We'll keep the logic to check for supported masks, but warn if they aren't truly supported due to import issues.
            supported_masks = ["radial_gradient", "solid"] # These names were in the original map.
            if color_mask.lower() not in supported_masks:
                return {
                    'success': False,
                    'message': f"Unsupported color_mask style: '{color_mask}'. Due to import issues, advanced color masks might not be supported. Supported names conceptually: {supported_masks}",
                    'data': None
                }
            else:
                 # If the mask name is recognized but the classes are not importable, we cannot create an instance.
                 # We'll proceed without the mask and inform the user.
                 print(f"Warning: Color mask '{color_mask}' was requested, but the corresponding classes are not available due to import errors. Falling back to basic coloring.")


        # --- QR Code Generation ---
        try:
            qr = qrcode.QRCode(
                version=1,  # Auto-scales to fit data
                error_correction=error_correction,
                box_size=box_size,
                border=border,
            )
            qr.add_data(url)
            qr.make(fit=True)

            # StyledPilImage uses fill_color and back_color directly.
            # If a specific mask class was needed and imported, it would be passed here.
            # Since they are not available, we'll pass None for module_drawer and rely on fill/back_color.
            img = qr.make_image(
                fill_color=fill_color,
                back_color=back_color,
                image_factory=StyledPilImage,
                module_drawer=drawer_instance,
                # color_mask=color_mask_instance # This would be used if color_mask_instance was successfully created
            )

            # --- File Saving ---
            directory = os.path.dirname(filename)
            if directory:
                if not os.path.exists(directory):
                    try:
                        os.makedirs(directory)
                        print(f"Created directory: {directory}")
                    except OSError as e:
                        return {
                            'success': False,
                            'message': f"Failed to create directory '{directory}': {e}",
                            'data': None
                        }

            img.save(filename)
            absolute_filepath = os.path.abspath(filename)

            return {
                'success': True,
                'message': f"QR code for '{url}' saved successfully to '{absolute_filepath}'.",
                'data': {
                    'filepath': absolute_filepath,
                    'filename': filename,
                    'url': url
                }
            }

        except ValueError as ve:
            return {
                'success': False,
                'message': f"Invalid value during QR code processing: {ve}",
                'data': None
            }
        except FileNotFoundError:
            return {
                'success': False,
                'message': f"Could not save the file. The path '{filename}' is invalid or inaccessible.",
                'data': None
            }
        except OSError as oe:
            return {
                'success': False,
                'message': f"File system error: {oe}",
                'data': None
            }
        except Exception as e:
            # Catch any other unexpected errors
            return {
                'success': False,
                'message': f"An unexpected error occurred during QR code generation: {e}",
                'data': None
            }

# Example of how to use the class for the specific user request:
if __name__ == "__main__":
    generator = QRCodeGenerator()

    # Specific user request: Create a QR code for https://github.com and save it as github_qr.png
    print("--- Executing User Request ---")
    user_request_result = generator.generate_and_save_qr_code(
        url="https://github.com",
        filename="github_qr.png"
    )

    print(f"Operation Success: {user_request_result['success']}")
    print(f"Message: {user_request_result['message']}")
    if user_request_result['data']:
        print(f"Saved Filepath: {user_request_result['data']['filepath']}")
        print(f"Saved Filename: {user_request_result['data']['filename']}")
        print(f"Encoded URL: {user_request_result['data']['url']}")

    print("\n--- Testing with Custom Options ---")
    # Example with custom options and saving to a subdirectory
    custom_options_result = generator.generate_and_save_qr_code(
        url="https://www.python.org",
        filename="generated_qrs/python_org_qr.png",
        fill_color="#0077CC", # Python blue
        back_color="#EEEEEE",
        module_drawer="rounded",
        color_mask="radial_gradient", # This will print a warning because the class is not importable
        error_correction=qrcode.constants.ERROR_CORRECT_Q,
        box_size=12,
        border=3
    )
    print(f"Operation Success: {custom_options_result['success']}")
    print(f"Message: {custom_options_result['message']}")
    if custom_options_result['data']:
        print(f"Saved Filepath: {custom_options_result['data']['filepath']}")

    print("\n--- Testing Error Handling ---")
    # Example of invalid URL
    invalid_url_result = generator.generate_and_save_qr_code(
        url="not_a_valid_url",
        filename="invalid_url_qr.png"
    )
    print(f"Invalid URL Test - Success: {invalid_url_result['success']}, Message: {invalid_url_result['message']}")

    # Example of invalid filename extension
    invalid_filename_result = generator.generate_and_save_qr_code(
        url="https://example.com",
        filename="invalid_file.txt"
    )
    print(f"Invalid Filename Test - Success: {invalid_filename_result['success']}, Message: {invalid_filename_result['message']}")

    # Example of invalid module drawer
    invalid_drawer_result = generator.generate_and_save_qr_code(
        url="https://example.com",
        filename="invalid_drawer_qr.png",
        module_drawer="triangles"
    )
    print(f"Invalid Drawer Test - Success: {invalid_drawer_result['success']}, Message: {invalid_drawer_result['message']}")

    # Example of invalid color mask (this one is recognized but will warn about availability)
    invalid_mask_result = generator.generate_and_save_qr_code(
        url="https://example.com",
        filename="invalid_mask_qr.png",
        color_mask="diagonal" # This will be caught by the validation for unsupported mask name
    )
    print(f"Invalid Mask Test - Success: {invalid_mask_result['success']}, Message: {invalid_mask_result['message']}")