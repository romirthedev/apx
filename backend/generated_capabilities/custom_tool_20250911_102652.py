
import platform
import sys
from typing import Dict, Any, Optional, List
import os

# Attempt to import necessary libraries for screen reading.
try:
    import pyautogui
    import pytesseract
    from PIL import ImageGrab, UnidentifiedImageError
except ImportError:
    print("Error: Required libraries are not installed.", file=sys.stderr)
    print("Please install them using: pip install pyautogui pytesseract Pillow", file=sys.stderr)
    print("For pytesseract, you may also need to install the Tesseract OCR engine:", file=sys.stderr)
    if platform.system() == "Darwin":  # macOS
        print("On macOS, install Tesseract OCR with Homebrew: brew install tesseract", file=sys.stderr)
    elif platform.system() == "Windows":
        print("On Windows, download the installer from: https://github.com/UB-Mannheim/tesseract/wiki", file=sys.stderr)
    else:  # Linux
        print("On Linux, install Tesseract OCR using your package manager (e.g., sudo apt-get install tesseract-ocr).", file=sys.stderr)
    sys.exit(1)


class ScreenTextReader:
    """
    A robust tool for reading text from the screen using OCR.

    This class leverages pyautogui for screen interaction and pytesseract for OCR.
    It includes enhanced error handling, input validation, and platform-specific
    configuration for Tesseract.
    """

    def __init__(self, pytesseract_cmd: Optional[str] = None):
        """
        Initializes the ScreenTextReader.

        Args:
            pytesseract_cmd: The explicit path to the Tesseract executable. If None,
                             pytesseract will attempt to find it in the system's PATH.
                             This is useful for non-standard Tesseract installations.
        """
        self.pytesseract_cmd = pytesseract_cmd
        self._configure_tesseract()

    def _configure_tesseract(self):
        """
        Configures the pytesseract command path, attempting to find it if not provided.
        Handles TesseractNotFoundError if the engine is not found.
        """
        if self.pytesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = self.pytesseract_cmd
            print(f"Using specified Tesseract command: {self.pytesseract_cmd}")
        else:
            try:
                # Try to get Tesseract version to check if it's accessible
                pytesseract.get_tesseract_version()
                print("Tesseract OCR engine found in PATH.")
            except pytesseract.TesseractNotFoundError:
                print("Tesseract OCR engine not found in system PATH.", file=sys.stderr)
                if platform.system() == "Darwin":  # macOS
                    default_tesseract_path = "/usr/local/bin/tesseract"
                    if os.path.exists(default_tesseract_path):
                        print(f"Attempting to use Tesseract from default Homebrew path: {default_tesseract_path}", file=sys.stderr)
                        pytesseract.pytesseract.tesseract_cmd = default_tesseract_path
                        try:
                            pytesseract.get_tesseract_version() # Re-check after setting path
                            print("Tesseract OCR engine configured successfully.")
                        except pytesseract.TesseractNotFoundError:
                            print("Error: Tesseract OCR engine not found even at default path.", file=sys.stderr)
                            print("Please ensure Tesseract is installed and accessible, or provide the 'pytesseract_cmd' argument.", file=sys.stderr)
                            sys.exit(1)
                    else:
                        print("Error: Tesseract OCR engine not found and default macOS path does not exist.", file=sys.stderr)
                        print("Please ensure Tesseract is installed and accessible, or provide the 'pytesseract_cmd' argument.", file=sys.stderr)
                        sys.exit(1)
                elif platform.system() == "Windows":
                    print("On Windows, you might need to add Tesseract to your system's PATH or specify 'pytesseract_cmd'.", file=sys.stderr)
                    print("Example: ScreenTextReader(pytesseract_cmd=r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe')", file=sys.stderr)
                    sys.exit(1)
                else: # Linux and other Unix-like systems
                    print("Ensure Tesseract OCR is installed and in your system's PATH.", file=sys.stderr)
                    sys.exit(1)
            except Exception as e:
                print(f"An unexpected error occurred during Tesseract configuration: {e}", file=sys.stderr)
                sys.exit(1)
        print("ScreenTextReader initialized.")

    def _validate_coordinates(self, left: int, top: int, width: int, height: int) -> bool:
        """
        Validates that the provided screen region coordinates are valid integers and non-negative.
        """
        if not all(isinstance(arg, int) for arg in [left, top, width, height]):
            print("Error: Coordinates (left, top, width, height) must be integers.", file=sys.stderr)
            return False
        if not all(arg >= 0 for arg in [left, top, width, height]):
            print("Error: Coordinates (left, top, width, height) must be non-negative.", file=sys.stderr)
            return False
        return True

    def read_screen_region(self, left: int, top: int, width: int, height: int, lang: str = 'eng') -> Dict[str, Any]:
        """
        Reads text from a specified rectangular region of the screen.

        Args:
            left: The x-coordinate of the top-left corner of the region.
            top: The y-coordinate of the top-left corner of the region.
            width: The width of the region.
            height: The height of the region.
            lang: The language code for Tesseract OCR (e.g., 'eng' for English).
                  Requires the corresponding language data to be installed for Tesseract.

        Returns:
            A dictionary with 'success' (bool), 'message' (str), and 'text' (str or None) fields.
        """
        if not self._validate_coordinates(left, top, width, height):
            return {
                "success": False,
                "message": "Invalid input: left, top, width, and height must be non-negative integers.",
                "text": None
            }

        try:
            # Capture the screen region. Pillow's ImageGrab is efficient for this.
            # Ensure the coordinates do not exceed screen bounds implicitly by capturing.
            # Pillow's grab might handle out-of-bounds gracefully, but it's good practice
            # to be aware of potential issues if precise bounds are critical.
            screenshot = ImageGrab.grab(bbox=(left, top, left + width, top + height))

            # Use pytesseract to extract text from the image.
            extracted_text = pytesseract.image_to_string(screenshot, lang=lang)

            return {
                "success": True,
                "message": f"Successfully read text from screen region ({left}, {top}, {width}, {height}).",
                "text": extracted_text.strip()
            }
        except pytesseract.TesseractNotFoundError:
            return {
                "success": False,
                "message": "Tesseract OCR engine not found. Please ensure it is installed and configured correctly.",
                "text": None
            }
        except UnidentifiedImageError:
            return {
                "success": False,
                "message": "Could not process the captured image. This might happen if the region is invalid or corrupted.",
                "text": None
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"An unexpected error occurred while reading screen region: {e}",
                "text": None
            }

    def read_full_screen(self, lang: str = 'eng') -> Dict[str, Any]:
        """
        Reads text from the entire screen.

        Args:
            lang: The language code for Tesseract OCR (e.g., 'eng' for English).

        Returns:
            A dictionary with 'success' (bool), 'message' (str), and 'text' (str or None) fields.
        """
        try:
            # Get screen dimensions using pyautogui
            screen_width, screen_height = pyautogui.size()

            # Capture the full screen
            screenshot = ImageGrab.grab(bbox=(0, 0, screen_width, screen_height))

            # Use pytesseract to extract text from the image.
            extracted_text = pytesseract.image_to_string(screenshot, lang=lang)

            return {
                "success": True,
                "message": "Successfully read text from the full screen.",
                "text": extracted_text.strip()
            }
        except pytesseract.TesseractNotFoundError:
            return {
                "success": False,
                "message": "Tesseract OCR engine not found. Please ensure it is installed and configured correctly.",
                "text": None
            }
        except UnidentifiedImageError:
            return {
                "success": False,
                "message": "Could not process the captured full screen image.",
                "text": None
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"An unexpected error occurred while reading the full screen: {e}",
                "text": None
            }

    def read_window_by_title(self, window_title: str, lang: str = 'eng') -> Dict[str, Any]:
        """
        Reads text from a specific window identified by its title.

        Note: This is an advanced feature and might not work reliably on all operating
        systems or for all types of windows (e.g., some modern UIs, headless applications).
        Requires `pygetwindow` to be installed: `pip install pygetwindow`.

        Args:
            window_title: The title of the window to capture.
            lang: The language code for Tesseract OCR (e.g., 'eng' for English).

        Returns:
            A dictionary with 'success' (bool), 'message' (str), and 'text' (str or None) fields.
        """
        try:
            import pygetwindow as gw
        except ImportError:
            return {
                "success": False,
                "message": "The 'pygetwindow' library is required for reading specific windows. Please install it: pip install pygetwindow",
                "text": None
            }

        try:
            target_window = gw.getWindowsWithTitle(window_title)
            if not target_window:
                return {
                    "success": False,
                    "message": f"No window found with the title: '{window_title}'",
                    "text": None
                }

            # Assuming the first found window is the one we want
            window = target_window[0]
            window.activate() # Attempt to bring the window to the foreground

            # Get window bounding box
            x, y, w, h = window.left, window.top, window.width, window.height

            # Slight adjustments might be needed for border/title bar if you want pure content
            # For simplicity, we capture the entire window bounds as returned by pygetwindow.
            # Consider excluding title bar height if necessary.

            # Capture the window region
            screenshot = ImageGrab.grab(bbox=(x, y, x + w, y + h))

            extracted_text = pytesseract.image_to_string(screenshot, lang=lang)

            return {
                "success": True,
                "message": f"Successfully read text from window '{window_title}'.",
                "text": extracted_text.strip()
            }
        except pytesseract.TesseractNotFoundError:
            return {
                "success": False,
                "message": "Tesseract OCR engine not found. Please ensure it is installed and configured correctly.",
                "text": None
            }
        except UnidentifiedImageError:
            return {
                "success": False,
                "message": "Could not process the captured window image.",
                "text": None
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"An error occurred while reading window '{window_title}': {e}",
                "text": None
            }


# Example Usage (optional, for demonstration purposes)
if __name__ == "__main__":
    print("Initializing ScreenTextReader...")
    try:
        # On macOS, Tesseract is typically installed via Homebrew at /usr/local/bin/tesseract
        # If you installed it elsewhere, provide the correct path.
        # If you installed it and it's in your PATH, you can omit the argument.
        # For Windows, you might need: ScreenTextReader(pytesseract_cmd=r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe')
        screen_reader = ScreenTextReader()

        print("\n--- Reading a specific screen region (example: top-left 100x50) ---")
        # This region might not contain significant text, it's for demonstration.
        region_result = screen_reader.read_screen_region(left=0, top=0, width=100, height=50)
        print(f"Result: {region_result}")

        print("\n--- Reading the full screen ---")
        # Be aware that reading the full screen can be slow and produce a lot of output.
        full_screen_result = screen_reader.read_full_screen()
        if full_screen_result['success']:
            print(f"Result (first 500 chars): {full_screen_result['text'][:500]}...")
        else:
            print(f"Error reading full screen: {full_screen_result['message']}")
        print(f"Success: {full_screen_result['success']}")

        print("\n--- Reading a specific window (example: 'Terminal' or 'Command Prompt') ---")
        # This will only work if a window with this title is open and pygetwindow is installed.
        # You might need to adjust 'Terminal' to match the exact title of your terminal application.
        try:
            import pygetwindow as gw
            window_titles_to_try = ["Terminal", "iTerm", "Command Prompt", "PowerShell", "Windows PowerShell"]
            found_window_title = None
            for title in window_titles_to_try:
                if gw.getWindowsWithTitle(title):
                    found_window_title = title
                    break

            if found_window_title:
                window_result = screen_reader.read_window_by_title(found_window_title)
                if window_result['success']:
                    print(f"Text from '{found_window_title}' window (first 300 chars): {window_result['text'][:300]}...")
                else:
                    print(f"Error reading window '{found_window_title}': {window_result['message']}")
                print(f"Success: {window_result['success']}")
            else:
                print("Could not find a common terminal window to test 'read_window_by_title'. Skipping test.")
        except ImportError:
            print("Skipping window reading test: 'pygetwindow' library not installed.")
        except Exception as e:
            print(f"An error occurred during the window reading test: {e}")


    except (ImportError, FileNotFoundError) as e:
        print(f"\nCritical error during initialization: {e}", file=sys.stderr)
        print("Please ensure all prerequisites are installed and Tesseract OCR is configured correctly.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nAn unexpected error occurred during example execution: {e}", file=sys.stderr)
        sys.exit(1)
