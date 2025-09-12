import mss
import mss.tools
import pytesseract
from PIL import Image
from typing import Dict, Any, Optional
from io import BytesIO
import sys

class ScreenshotTextExtractor:
    """
    A specialized tool class for taking screenshots and extracting text from them.
    This class is designed to be cross-platform (Windows, macOS, Linux) by
    leveraging mss for screenshots and pytesseract for OCR.
    """

    def __init__(self, tesseract_cmd: Optional[str] = None):
        """
        Initializes the ScreenshotTextExtractor.

        Args:
            tesseract_cmd (Optional[str]): The path to the Tesseract executable.
                                           If None, Tesseract is expected to be in the system's PATH.
                                           On macOS, this might be '/usr/local/bin/tesseract' if installed via Homebrew.
                                           On Windows, it might be 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'.
        """
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        else:
            # Attempt to find tesseract executable if not provided and not in PATH
            try:
                pytesseract.get_tesseract_version()
            except pytesseract.TesseractNotFoundError:
                print(
                    "Warning: Tesseract executable not found in PATH. "
                    "Please install Tesseract OCR and ensure it's in your PATH, or "
                    "provide the path to the executable using the 'tesseract_cmd' argument "
                    "during initialization.",
                    file=sys.stderr
                )
                # This will cause an error later if tesseract is truly not found.
                # It's better to let pytesseract raise the error when used.

    def _get_monitor_geometry(self, monitor_number: int) -> Dict[str, int]:
        """
        Retrieves the geometry of a specific monitor.

        Args:
            monitor_number (int): The 1-based index of the monitor to capture.

        Returns:
            Dict[str, int]: A dictionary representing the monitor's bounding box
                            {'top': int, 'left': int, 'width': int, 'height': int}.

        Raises:
            ValueError: If the monitor_number is invalid.
            mss.exception.ScreenShotError: If there's an issue accessing monitor information.
        """
        try:
            with mss.mss() as sct:
                if not (1 <= monitor_number <= len(sct.monitors) - 1): # Adjust for 'all displays' monitor
                    raise ValueError(f"Invalid monitor number. Available monitors: 1 to {len(sct.monitors) - 1}.")
                # mss.monitors[0] is all displays combined. Real monitors start from index 1.
                monitor = sct.monitors[monitor_number]
                return monitor
        except mss.exception.ScreenShotError as e:
            # If mss is not installed or has issues, provide a fallback or raise
            print(f"Error using mss: {e}. Please ensure mss is installed correctly.", file=sys.stderr)
            raise

    def take_screenshot(self, monitor_number: int = 1) -> Dict[str, Any]:
        """
        Takes a screenshot of the specified monitor and returns its bytes.

        Args:
            monitor_number (int): The number of the monitor to capture (1-based index).
                                  Defaults to 1 (primary monitor).

        Returns:
            Dict[str, Any]: A dictionary containing the screenshot data.
                            On success: {'success': True, 'message': 'Screenshot captured successfully.', 'image_bytes': bytes}
                            On failure: {'success': False, 'message': 'Error message.'}
        """
        try:
            monitor_geometry = self._get_monitor_geometry(monitor_number)

            with mss.mss() as sct:
                sct_img = sct.grab(monitor_geometry)

                # Convert to PIL Image
                img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)

                # Save to bytes
                img_byte_arr = BytesIO()
                img.save(img_byte_arr, format='PNG')
                image_bytes = img_byte_arr.getvalue()

                return {
                    'success': True,
                    'message': 'Screenshot captured successfully.',
                    'image_bytes': image_bytes
                }
        except ValueError as ve:
            return {'success': False, 'message': str(ve)}
        except mss.exception.ScreenShotError as e:
            return {'success': False, 'message': f"MSS error capturing screenshot: {e}"}
        except Exception as e:
            return {'success': False, 'message': f"An unexpected error occurred during screenshot capture: {e}"}

    def extract_text_from_image_bytes(self, image_bytes: bytes, lang: str = 'eng') -> Dict[str, Any]:
        """
        Extracts text from raw image bytes using Tesseract OCR.

        Args:
            image_bytes (bytes): The raw bytes of the image.
            lang (str): The language code for Tesseract OCR (e.g., 'eng' for English).
                        Multiple languages can be specified by separating them with '+', e.g., 'eng+fra'.

        Returns:
            Dict[str, Any]: A dictionary containing the extracted text.
                            On success: {'success': True, 'message': 'Text extracted successfully.', 'text': str, 'language': str}
                            On failure: {'success': False, 'message': 'Error message.'}
        """
        if not image_bytes:
            return {'success': False, 'message': 'No image data provided.'}

        if not lang or not isinstance(lang, str):
            return {'success': False, 'message': 'Invalid language parameter. Must be a non-empty string (e.g., "eng").'}

        try:
            img = Image.open(BytesIO(image_bytes))
            # Add preprocessing steps for better OCR accuracy
            # Convert to grayscale
            img = img.convert('L')
            # Optional: Apply thresholding, despeckling, etc. for improved results
            # For example:
            # from PIL import ImageFilter
            # img = img.filter(ImageFilter.SHARPEN)
            # img = img.point(lambda x: 0 if x < 128 else 255, '1') # simple binary thresholding

            text = pytesseract.image_to_string(img, lang=lang)
            return {
                'success': True,
                'message': 'Text extracted successfully.',
                'text': text.strip(),
                'language': lang
            }
        except pytesseract.TesseractNotFoundError:
            return {
                'success': False,
                'message': "Tesseract is not installed or not in your PATH. "
                           "Please install Tesseract OCR and ensure it's accessible. "
                           "On macOS, you can install it via Homebrew: 'brew install tesseract'. "
                           "On Windows, download from https://github.com/UB-Mannheim/tesseract/wiki "
                           "and add its installation directory to your PATH or specify 'tesseract_cmd'."
            }
        except Image.UnidentifiedImageError:
            return {'success': False, 'message': 'Could not identify image file. Ensure image_bytes are valid and not corrupted.'}
        except ValueError as ve:
            return {'success': False, 'message': f"Invalid image data or configuration: {ve}"}
        except Exception as e:
            return {'success': False, 'message': f"An error occurred during text extraction: {e}"}

    def capture_and_extract_text(self, monitor_number: int = 1, lang: str = 'eng') -> Dict[str, Any]:
        """
        Takes a screenshot of the specified monitor and extracts text from it.

        Args:
            monitor_number (int): The number of the monitor to capture (1-based index).
                                  Defaults to 1 (primary monitor).
            lang (str): The language code for Tesseract OCR (e.g., 'eng' for English).
                        Multiple languages can be specified by separating them with '+', e.g., 'eng+fra'.

        Returns:
            Dict[str, Any]: A dictionary containing the results.
                            On success: {'success': True, 'message': 'Screenshot and text extraction successful.', 'image_bytes': bytes, 'text': str, 'language': str}
                            On failure: {'success': False, 'message': 'Error message.'}
        """
        # Validate monitor number early
        try:
            self._get_monitor_geometry(monitor_number)
        except ValueError as ve:
            return {'success': False, 'message': str(ve)}
        except mss.exception.ScreenShotError as e:
            return {'success': False, 'message': f"Error accessing monitor information: {e}"}

        # Validate language parameter early
        if not lang or not isinstance(lang, str):
            return {'success': False, 'message': 'Invalid language parameter. Must be a non-empty string (e.g., "eng").'}

        print(f"Attempting to capture screenshot of monitor {monitor_number}...")
        screenshot_result = self.take_screenshot(monitor_number=monitor_number)
        if not screenshot_result['success']:
            return screenshot_result
        print("Screenshot captured successfully.")

        image_bytes = screenshot_result.get('image_bytes')
        if not image_bytes:
            return {'success': False, 'message': 'Screenshot captured but no image data was retrieved. This is an internal error.'}

        print(f"Attempting to extract text from screenshot using language '{lang}'...")
        text_extraction_result = self.extract_text_from_image_bytes(image_bytes=image_bytes, lang=lang)
        if not text_extraction_result['success']:
            return text_extraction_result
        print("Text extraction successful.")

        # Combine results
        combined_result = {
            'success': True,
            'message': 'Screenshot and text extraction successful.',
            'image_bytes': image_bytes,
            'text': text_extraction_result.get('text'),
            'language': text_extraction_result.get('language')
        }
        return combined_result

if __name__ == '__main__':
    from io import BytesIO
    import sys
    import os

    # --- Configuration ---
    # On macOS, Tesseract is often installed via Homebrew.
    # If pytesseract.TesseractNotFoundError occurs, uncomment the line below
    # and set the correct path to your Tesseract executable.
    # Example for Homebrew on macOS:
    # tesseract_path = '/usr/local/bin/tesseract'
    # Example for Windows (adjust path as needed):
    # tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    tesseract_path = None # Assumes tesseract is in PATH

    # --- Initialization ---
    try:
        extractor = ScreenshotTextExtractor(tesseract_cmd=tesseract_path)
    except Exception as e:
        print(f"Error initializing ScreenshotTextExtractor: {e}")
        print("Please ensure Tesseract OCR is installed and its executable is in your system's PATH, or provide the correct path.")
        sys.exit(1)

    # --- Example Usage ---
    print("--- Welcome to the Screenshot and Text Extractor Tool ---")
    print("This tool will take a screenshot and attempt to extract text from it.")
    print("Ensure Tesseract OCR is installed and configured correctly.")

    # Get available monitors
    try:
        with mss.mss() as sct:
            num_monitors = len(sct.monitors) - 1 # Exclude the 'all displays' monitor at index 0
            print(f"\nDetected {num_monitors} display(s).")
            for i, mon in enumerate(sct.monitors):
                if i > 0: # Skip the all-displays monitor
                    print(f"  Monitor {i}: Resolution {mon['width']}x{mon['height']} at ({mon['left']}, {mon['top']})")
    except mss.exception.ScreenShotError as e:
        print(f"Could not detect monitors using mss: {e}")
        print("Please ensure mss is installed correctly and has the necessary permissions to access display information.")
        num_monitors = 0 # Indicate no monitors detected
    except Exception as e:
        print(f"An unexpected error occurred while detecting monitors: {e}")
        num_monitors = 0

    selected_monitor = 1
    if num_monitors > 1:
        while True:
            try:
                monitor_input = input(f"Enter the monitor number to capture (1-{num_monitors}, default is 1): ")
                if not monitor_input:
                    selected_monitor = 1
                    break
                selected_monitor = int(monitor_input)
                if 1 <= selected_monitor <= num_monitors:
                    break
                else:
                    print(f"Invalid input. Please enter a number between 1 and {num_monitors}.")
            except ValueError:
                print("Invalid input. Please enter a number.")
    elif num_monitors == 0:
        print("No monitors detected. Cannot proceed with screenshot.")
        sys.exit(1)
    else:
        print("Using primary monitor (1).")


    language = input("Enter the language for OCR (e.g., 'eng', 'fra', 'eng+fra', default is 'eng'): ")
    if not language:
        language = 'eng'

    print(f"\n--- Capturing Monitor {selected_monitor} and Extracting Text ({language}) ---")

    # Using the combined function
    full_result = extractor.capture_and_extract_text(monitor_number=selected_monitor, lang=language)

    if full_result['success']:
        print("\n--- Operation Successful ---")
        print(f"Extracted Text ({full_result.get('language')}):\n---\n{full_result['text']}\n---")

        # Ask user if they want to save the screenshot
        save_img = input("Do you want to save the captured screenshot? (y/N): ").lower()
        if save_img == 'y':
            output_filename = "captured_screenshot.png"
            try:
                with open(output_filename, "wb") as f:
                    f.write(full_result['image_bytes'])
                print(f"Screenshot saved successfully to '{output_filename}'")
            except IOError as e:
                print(f"Error saving screenshot: {e}")
    else:
        print("\n--- Operation Failed ---")
        print(f"Error: {full_result['message']}")
        sys.exit(1) # Exit with an error code if the main operation failed

    print("\n--- Testing Edge Cases ---")

    print("\nTesting with an invalid monitor number:")
    invalid_monitor_result = extractor.take_screenshot(monitor_number=999)
    print(f"Result: {invalid_monitor_result}")

    print("\nTesting with invalid language parameter:")
    invalid_lang_result = extractor.capture_and_extract_text(lang="")
    print(f"Result: {invalid_lang_result}")

    print("\nTesting with empty image bytes for extraction:")
    empty_img_result = extractor.extract_text_from_image_bytes(image_bytes=b'', lang='eng')
    print(f"Result: {empty_img_result}")

    print("\n--- End of Tool Execution ---")