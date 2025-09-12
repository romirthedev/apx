
import pyautogui
import pytesseract
from PIL import Image, UnidentifiedImageError
import io
import os
from typing import Dict, Any, Optional, Tuple, Union

class ScreenshotTextReader:
    """
    A specialized tool class for taking screenshots and reading text from them.

    This class leverages pyautogui for screen capturing and pytesseract for
    Optical Character Recognition (OCR). It aims to be robust, user-friendly,
    and handle errors gracefully.

    Attributes:
        tesseract_cmd (Optional[str]): The path to the Tesseract executable.
            If None, pytesseract will attempt to find it in the system's PATH.
    """

    def __init__(self, tesseract_cmd: Optional[str] = None):
        """
        Initializes the ScreenshotTextReader.

        Args:
            tesseract_cmd (str, optional): The path to the Tesseract executable.
                If not provided, pytesseract will attempt to find it in the system's PATH.
                On macOS, you might need to explicitly set this, e.g.,
                '/opt/homebrew/bin/tesseract' or '/usr/local/bin/tesseract'.
        """
        if tesseract_cmd:
            self.tesseract_cmd = tesseract_cmd
            pytesseract.tesseract_cmd = tesseract_cmd
        else:
            # Attempt to find tesseract path if not provided
            self.tesseract_cmd = self._find_tesseract_path()
            if self.tesseract_cmd:
                pytesseract.tesseract_cmd = self.tesseract_cmd
            else:
                print("Warning: Tesseract executable not found in PATH. Please specify 'tesseract_cmd' argument during initialization if you encounter TesseractNotFoundError.")

    def _find_tesseract_path(self) -> Optional[str]:
        """Attempts to find the Tesseract executable path."""
        if os.name == 'nt':  # Windows
            possible_paths = [
                os.path.join(os.environ.get("ProgramFiles", ""), "Tesseract-OCR", "tesseract.exe"),
                os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Tesseract-OCR", "tesseract.exe"),
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    return path
        elif os.name == 'posix':  # macOS and Linux
            for path_dir in os.environ.get('PATH', '').split(os.pathsep):
                tesseract_exec = os.path.join(path_dir, 'tesseract')
                if os.path.exists(tesseract_exec):
                    return tesseract_exec
        return None

    def take_screenshot(self, region: Optional[Tuple[int, int, int, int]] = None) -> Dict[str, Any]:
        """
        Takes a screenshot of the entire screen or a specified region.

        Args:
            region (tuple, optional): A tuple of (left, top, width, height)
                defining the area to capture. If None, the entire screen is captured.

        Returns:
            Dict[str, Any]: A dictionary containing:
                'success' (bool): True if the screenshot was taken successfully, False otherwise.
                'message' (str): A message describing the outcome.
                'image_bytes' (bytes, optional): The screenshot image as bytes if successful.
                'error' (str, optional): An error message if 'success' is False.
        """
        try:
            if region:
                if not (isinstance(region, tuple) and len(region) == 4 and all(isinstance(i, int) and i >= 0 for i in region)):
                    return {
                        'success': False,
                        'message': "Invalid region format. Expected (left, top, width, height) with non-negative integers.",
                        'error': "Invalid region format."
                    }
                # Ensure region does not exceed screen bounds (pyautogui handles some of this but explicit check is good)
                screen_width, screen_height = pyautogui.size()
                left, top, width, height = region
                if left < 0 or top < 0 or width <= 0 or height <= 0:
                     return {
                        'success': False,
                        'message': "Region dimensions must be positive and non-negative for left/top.",
                        'error': "Invalid region dimensions."
                    }
                # Adjust if region goes beyond screen (pyautogui might clip but this is more explicit)
                actual_width = min(width, screen_width - left)
                actual_height = min(height, screen_height - top)
                if actual_width <= 0 or actual_height <= 0:
                     return {
                        'success': False,
                        'message': "Region is outside of screen bounds or has zero dimension after adjustment.",
                        'error': "Region out of bounds."
                    }
                screenshot_img = pyautogui.screenshot(region=(left, top, actual_width, actual_height))
            else:
                screenshot_img = pyautogui.screenshot()

            img_byte_arr = io.BytesIO()
            # Ensure the image format is supported and consistent
            screenshot_img.save(img_byte_arr, format='PNG')
            image_bytes = img_byte_arr.getvalue()

            return {
                'success': True,
                'message': "Screenshot captured successfully.",
                'image_bytes': image_bytes
            }
        except pyautogui.FailSafeException:
            return {
                'success': False,
                'message': "Screenshot capture aborted due to user interruption (mouse moved to a corner).",
                'error': "User interruption during screenshot."
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"Failed to capture screenshot: {e}",
                'error': str(e)
            }

    def read_text_from_image(self, image_bytes: bytes, lang: str = 'eng') -> Dict[str, Any]:
        """
        Reads text from image bytes using OCR.

        Args:
            image_bytes (bytes): The image data in bytes.
            lang (str, optional): The language code for OCR. Defaults to 'eng' (English).

        Returns:
            Dict[str, Any]: A dictionary containing:
                'success' (bool): True if text was read successfully, False otherwise.
                'message' (str): A message describing the outcome.
                'text' (str, optional): The extracted text if successful.
                'error' (str, optional): An error message if 'success' is False.
        """
        if not isinstance(image_bytes, bytes) or not image_bytes:
            return {
                'success': False,
                'message': "Invalid image_bytes provided. Must be non-empty bytes.",
                'error': "Invalid image input."
            }

        try:
            image = Image.open(io.BytesIO(image_bytes))
            # Validate image data before OCR
            if not hasattr(image, 'mode') or not hasattr(image, 'size'):
                 return {
                    'success': False,
                    'message': "Invalid image data. Could not process.",
                    'error': "Corrupted or unsupported image format."
                }
            
            # You can add image preprocessing here if needed (e.g., Grayscale, Thresholding)
            # For example:
            # image = image.convert('L') # Convert to grayscale
            
            text = pytesseract.image_to_string(image, lang=lang)

            return {
                'success': True,
                'message': "Text extracted successfully from image.",
                'text': text.strip()
            }
        except UnidentifiedImageError:
            return {
                'success': False,
                'message': "Failed to identify image format. The provided bytes may not be a valid image.",
                'error': "Unidentified image format."
            }
        except pytesseract.TesseractNotFoundError:
            error_msg = "Tesseract OCR engine not found. Please ensure Tesseract is installed and its path is correctly configured."
            if self.tesseract_cmd:
                error_msg += f" Explicitly set tesseract_cmd to '{self.tesseract_cmd}'."
            else:
                error_msg += " Ensure 'tesseract' is in your system's PATH."
            return {
                'success': False,
                'message': error_msg,
                'error': "Tesseract not found."
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"Failed to read text from image: {e}",
                'error': str(e)
            }

    def capture_and_read_text(self, region: Optional[Tuple[int, int, int, int]] = None, lang: str = 'eng') -> Dict[str, Any]:
        """
        Takes a screenshot and reads text from it. This is the primary function
        for fulfilling the user request.

        Args:
            region (tuple, optional): A tuple of (left, top, width, height)
                defining the area to capture. If None, the entire screen is captured.
                Coordinates should be non-negative integers.
            lang (str, optional): The language code for OCR. Defaults to 'eng' (English).
                Ensure the language pack is installed for Tesseract.

        Returns:
            Dict[str, Any]: A dictionary containing:
                'success' (bool): True if the operation was successful, False otherwise.
                'message' (str): A message describing the outcome.
                'text' (str, optional): The extracted text if successful.
                'error' (str, optional): An error message if 'success' is False.
        """
        # Validate language input
        if not isinstance(lang, str) or not lang:
            return {
                'success': False,
                'message': "Invalid language code. Must be a non-empty string.",
                'error': "Invalid language code."
            }

        screenshot_result = self.take_screenshot(region=region)

        if not screenshot_result['success']:
            return {
                'success': False,
                'message': f"Screenshot failed: {screenshot_result.get('message', 'Unknown error')}",
                'error': screenshot_result.get('error', 'Unknown screenshot error')
            }

        image_bytes = screenshot_result.get('image_bytes')
        if not image_bytes:
            return {
                'success': False,
                'message': "Screenshot captured but no image data received.",
                'error': "Missing image data after screenshot."
            }

        read_text_result = self.read_text_from_image(image_bytes, lang=lang)

        if not read_text_result['success']:
            return {
                'success': False,
                'message': f"Text reading failed: {read_text_result.get('message', 'Unknown error')}",
                'error': read_text_result.get('error', 'Unknown text reading error')
            }

        return {
            'success': True,
            'message': "Screenshot and text reading completed successfully.",
            'text': read_text_result.get('text', '')
        }

# Example Usage (optional, for testing purposes, remove if not needed):
if __name__ == "__main__":
    # On macOS or Linux, you might need to specify the path to tesseract if it's not in your PATH.
    # For example, if installed via Homebrew on macOS:
    # tesseract_path = "/opt/homebrew/bin/tesseract"
    # Or on Linux:
    # tesseract_path = "/usr/bin/tesseract"
    # If you don't know, try running 'which tesseract' in your terminal.
    # If it's in your PATH, you can omit the tesseract_cmd argument.

    try:
        # Auto-detect tesseract path if not provided
        reader = ScreenshotTextReader()

        print("--- Taking full screenshot and reading text ---")
        full_screen_result = reader.capture_and_read_text()
        if full_screen_result['success']:
            print("Successfully read text from full screen:")
            print(full_screen_result['text'])
        else:
            print(f"Error: {full_screen_result['message']}")
            if 'error' in full_screen_result:
                print(f"Details: {full_screen_result['error']}")

        print("\n--- Taking screenshot of a specific region (example: top-left 300x200) ---")
        try:
            # Get screen resolution to define a sensible region
            screen_width, screen_height = pyautogui.size()
            example_region = (0, 0, min(300, screen_width), min(200, screen_height))
            print(f"Attempting to capture region: {example_region}")

            region_result = reader.capture_and_read_text(region=example_region)
            if region_result['success']:
                print(f"Successfully read text from region {example_region}:")
                print(region_result['text'])
            else:
                print(f"Error capturing/reading from region {example_region}: {region_result['message']}")
                if 'error' in region_result:
                    print(f"Details: {region_result['error']}")
        except Exception as e:
            print(f"An error occurred during region test: {e}")
            
        print("\n--- Testing invalid region input ---")
        invalid_region_result = reader.capture_and_read_text(region=(-10, 0, 100, 100))
        if not invalid_region_result['success']:
            print(f"Correctly handled invalid region: {invalid_region_result['message']}")
        else:
            print("Failed to catch invalid region.")

        print("\n--- Testing invalid image input ---")
        invalid_image_result = reader.read_text_from_image(b"not an image")
        if not invalid_image_result['success']:
            print(f"Correctly handled invalid image input: {invalid_image_result['message']}")
        else:
            print("Failed to catch invalid image input.")

    except ImportError:
        print("Please install required libraries: pip install pyautogui pytesseract Pillow")
    except Exception as e:
        print(f"An unexpected error occurred during example execution: {e}")
