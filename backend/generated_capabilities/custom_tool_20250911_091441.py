
import sys
from typing import Dict, Any, Optional, List, Tuple

# Attempt to import necessary libraries, provide informative errors if missing.
try:
    from PIL import Image, ImageGrab
    import pytesseract
    # Import Quartz and AppKit for macOS-specific window information
    if sys.platform == "darwin":
        from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionAll, kCGWindowListOptionOnScreenOnly, kCGNullWindowID
        from AppKit import NSScreen
    else:
        # Mock these for non-darwin platforms to allow basic structure
        class MockCGWindow:
            def __init__(self, *args, **kwargs):
                pass
        CGWindowListCopyWindowInfo = MockCGWindow
        kCGWindowListOptionAll = 0
        kCGWindowListOptionOnScreenOnly = 0
        kCGNullWindowID = 0
        class MockNSScreen:
            frame = (0, 0, 800, 600) # Default for mock
        NSScreen = MockNSScreen()

except ImportError as e:
    error_messages = {
        "darwin": (
            f"Error importing required libraries: {e}\n"
            "On macOS, please ensure you have these libraries installed:\n"
            "pip install Pillow pytesseract pyobjc-framework-Quartz pyobjc-framework-AppKit\n"
            "You may also need to install Tesseract OCR engine separately if you haven't already.\n"
            "For Homebrew users: brew install tesseract"
        ),
        "other": (
            f"Error importing required libraries: {e}\n"
            "Please ensure you have these libraries installed:\n"
            "pip install Pillow pytesseract\n"
            "For screen capture and OCR on your platform, you might need additional libraries and setup.\n"
            "On Linux, consider 'scrot' and 'tesseract-ocr'. On Windows, 'mss' and 'pytesseract'."
        )
    }
    print(error_messages.get(sys.platform, error_messages["other"]), file=sys.stderr)
    sys.exit(1)


class ScreenReader:
    """
    A specialized tool for reading text from the screen.

    This class provides functionality to capture a portion of the screen
    and extract text from it using OCR. It is primarily designed for macOS
    due to its reliance on Quartz for window information.
    """

    def __init__(self, tesseract_cmd: Optional[str] = None):
        """
        Initializes the ScreenReader.

        Args:
            tesseract_cmd (Optional[str]): The path to the Tesseract executable.
                If not provided, pytesseract will try to find it in the system's PATH.
        """
        if sys.platform != "darwin":
            print("Warning: This ScreenReader is optimized for macOS. Cross-platform "
                  "window identification and capture might be limited.", file=sys.stderr)

        if tesseract_cmd:
            try:
                pytesseract.get_tesseract_version(tesseract_cmd=tesseract_cmd)
                pytesseract.tesseract_cmd = tesseract_cmd
            except pytesseract.TesseractNotFoundError:
                raise pytesseract.TesseractNotFoundError(
                    f"Tesseract executable not found at the specified path: {tesseract_cmd}. "
                    "Please ensure it's installed and the path is correct."
                )
        else:
            try:
                pytesseract.get_tesseract_version()
            except pytesseract.TesseractNotFoundError:
                raise pytesseract.TesseractNotFoundError(
                    "Tesseract OCR engine not found. Please install it and ensure it's "
                    "in your system's PATH or specify the 'tesseract_cmd' argument."
                )

    def _get_all_windows_info(self) -> List[Dict[str, Any]]:
        """
        Retrieves information about all visible windows on the screen.

        This method uses the Quartz API on macOS to get a list of window dictionaries.
        On other platforms, it returns an empty list as window information is not
        readily available through the current imports.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, where each dictionary contains information
                                  about a window. Returns an empty list if an error occurs or on non-darwin platforms.
        """
        if sys.platform != "darwin":
            return []
        try:
            # kCGWindowListOptionOnScreenOnly ensures we only get windows that are actually visible.
            # kCGWindowListOptionAll is used to get information about all windows.
            window_list = CGWindowListCopyWindowInfo(
                kCGWindowListOptionOnScreenOnly | kCGWindowListOptionAll, kCGNullWindowID
            )
            return window_list if window_list else []
        except Exception as e:
            print(f"Error retrieving window list: {e}", file=sys.stderr)
            return []

    def _capture_and_ocr_window(self, window_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Captures the screen region of a given window and extracts text using OCR.

        Args:
            window_info (Dict[str, Any]): A dictionary containing information about the window,
                                           including its bounds and title.

        Returns:
            Optional[Dict[str, Any]]: A dictionary containing the window's title, bounds,
                                      and extracted text if successful, otherwise None.
        """
        try:
            # Filter out windows that are not applicable for text extraction
            # (e.g., docks, menu bars, or invisible windows).
            # Basic checks include presence of title, a valid layer, and bounds.
            if (
                "kCGWindowName" in window_info
                and window_info["kCGWindowName"]
                and window_info["kCGWindowLayer"] == 0  # Typically foreground windows
                and window_info.get("kCGWindowBounds")
            ):
                window_title = window_info["kCGWindowName"]
                window_bounds = window_info["kCGWindowBounds"]

                # Ensure bounds are integers and valid
                try:
                    x, y, width, height = (
                        int(window_bounds["X"]),
                        int(window_bounds["Y"]),
                        int(window_bounds["Width"]),
                        int(window_bounds["Height"]),
                    )
                except (ValueError, TypeError):
                    print(f"Skipping window '{window_title}': Invalid bounds format.", file=sys.stderr)
                    return None

                # Only attempt to capture if the window has a reasonable size
                if width <= 0 or height <= 0:
                    # print(f"Skipping window '{window_title}': Invalid dimensions ({width}x{height}).", file=sys.stderr)
                    return None

                # Capture the screen region corresponding to the window
                # Adjusting bounds for potential screen scaling or Retina displays might be needed
                # For now, we use direct bounds.
                img = ImageGrab.grab(bbox=(x, y, x + width, y + height))

                # Use pytesseract to extract text from the image
                text = pytesseract.image_to_string(img)

                return {
                    "window_title": window_title,
                    "bounds": {"x": x, "y": y, "width": width, "height": height},
                    "text": text.strip() if text else ""
                }
        except pytesseract.TesseractNotFoundError:
            # This exception should ideally be caught during initialization, but as a safeguard:
            raise
        except Exception as e:
            # Continue processing other windows even if one fails
            print(f"Could not process window '{window_info.get('kCGWindowName', 'Unnamed')}': {e}", file=sys.stderr)
            return None
        return None

    def get_all_screen_text(self) -> Dict[str, Any]:
        """
        Reads text from all visible windows on the screen.

        This method iterates through all detected windows, captures their
        content (if possible), and extracts text using OCR. This functionality
        is primarily for macOS.

        Returns:
            Dict[str, Any]: A dictionary containing the operation's status.
                On success, it includes 'success': True and a 'windows_data' field
                which is a list of dictionaries, each representing a window with
                its title and extracted text.
                On failure, it includes 'success': False and an 'message' field
                describing the error.
        """
        if sys.platform != "darwin":
            return {
                "success": False,
                "message": "Screen text reading functionality is currently only supported on macOS.",
                "windows_data": []
            }

        windows_info = self._get_all_windows_info()
        if not windows_info:
            return {
                "success": False,
                "message": "Could not retrieve information about any visible windows on macOS.",
                "windows_data": []
            }

        all_windows_data = []
        for window in windows_info:
            processed_data = self._capture_and_ocr_window(window)
            if processed_data and processed_data["text"]:  # Only add if text was extracted
                all_windows_data.append(processed_data)

        if not all_windows_data:
            return {
                "success": False,
                "message": "No extractable text found from any visible windows on macOS.",
                "windows_data": []
            }

        return {
            "success": True,
            "message": f"Successfully extracted text from {len(all_windows_data)} window(s) on macOS.",
            "windows_data": all_windows_data
        }

    def get_specific_window_text(self, window_title_substring: str) -> Dict[str, Any]:
        """
        Reads text from a specific window based on a substring of its title.

        Args:
            window_title_substring (str): A substring to match against window titles.
                The search is case-insensitive.

        Returns:
            Dict[str, Any]: A dictionary containing the operation's status.
                On success, it includes 'success': True and a 'window_data' field
                which is a dictionary representing the found window with its
                title, bounds, and extracted text.
                On failure, it includes 'success': False and an 'message' field
                describing the error. If multiple windows match, it returns the first one found.
        """
        if not isinstance(window_title_substring, str):
            return {
                "success": False,
                "message": "Invalid input: 'window_title_substring' must be a string.",
                "window_data": None
            }
        if not window_title_substring:
            return {
                "success": False,
                "message": "Invalid input: 'window_title_substring' cannot be empty. Please provide a title or part of a title to search for.",
                "window_data": None
            }

        if sys.platform != "darwin":
            return {
                "success": False,
                "message": "Specific window text reading functionality is currently only supported on macOS.",
                "window_data": None
            }

        windows_info = self._get_all_windows_info()
        if not windows_info:
            return {
                "success": False,
                "message": "Could not retrieve information about any visible windows on macOS.",
                "window_data": None
            }

        matching_windows = []
        for window in windows_info:
            if (
                "kCGWindowName" in window
                and window["kCGWindowName"]
                and window_title_substring.lower() in window["kCGWindowName"].lower()
                and window["kCGWindowLayer"] == 0
                and window.get("kCGWindowBounds")
            ):
                matching_windows.append(window)

        if not matching_windows:
            return {
                "success": False,
                "message": f"No window found on macOS with title containing '{window_title_substring}'.",
                "window_data": None
            }

        # For simplicity, process the first matching window found.
        # More sophisticated logic could be added to handle multiple matches if needed.
        target_window = matching_windows[0]

        processed_data = self._capture_and_ocr_window(target_window)

        if processed_data and processed_data["text"]:
            return {
                "success": True,
                "message": f"Successfully extracted text from window '{processed_data['window_title']}' on macOS.",
                "window_data": processed_data
            }
        elif processed_data and not processed_data["text"]:
            return {
                "success": False,
                "message": f"Window '{target_window.get('kCGWindowName', 'Unnamed')}' found, but no extractable text was detected.",
                "window_data": {
                    "window_title": processed_data["window_title"],
                    "bounds": processed_data["bounds"],
                    "text": ""
                }
            }
        else:
            # This case would be if _capture_and_ocr_window returned None due to errors or invalid data
            return {
                "success": False,
                "message": f"Error processing the matched window '{target_window.get('kCGWindowName', 'Unnamed')}' on macOS. It might have invalid dimensions or an uncapturable region.",
                "window_data": None
            }

# Compatibility with older versions of Pillow that might not have ImageGrab directly
# This ensures the code works across different Pillow installations.
try:
    from PIL import ImageGrab
except ImportError:
    try:
        from PIL.ImageGrab import grab as ImageGrab_grab
        # Create a mock object that has a 'grab' method
        ImageGrab = type('ImageGrabModule', (object,), {'grab': ImageGrab_grab})()
    except ImportError:
        print("Error: Could not import ImageGrab from Pillow. Ensure Pillow is installed correctly.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    # Example usage:
    print("--- Testing ScreenReader ---")

    try:
        # You might need to specify the tesseract command if it's not in your PATH
        # For example, on macOS with Homebrew:
        # reader = ScreenReader(tesseract_cmd="/opt/homebrew/bin/tesseract")
        reader = ScreenReader()
    except pytesseract.TesseractNotFoundError as e:
        print(f"Initialization Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred during initialization: {e}", file=sys.stderr)
        sys.exit(1)


    # 1. Get text from all windows (macOS only)
    print("\nAttempting to read text from all visible windows...")
    all_text_result = reader.get_all_screen_text()

    if all_text_result["success"]:
        print(f"Successfully retrieved text from {len(all_text_result['windows_data'])} window(s):")
        for i, win_data in enumerate(all_text_result["windows_data"]):
            print(f"\n--- Window {i+1} ---")
            print(f"Title: {win_data['window_title']}")
            print(f"Bounds: {win_data['bounds']}")
            print(f"Text:\n{win_data['text'][:500]}{'...' if len(win_data['text']) > 500 else ''}") # Print first 500 chars
    else:
        print(f"Failed to read text from all windows: {all_text_result['message']}")

    # 2. Get text from a specific window (e.g., the Terminal if it's open)
    print("\nAttempting to read text from a specific window (e.g., 'Terminal')...")
    specific_text_result = reader.get_specific_window_text("Terminal")

    if specific_text_result["success"]:
        print("Successfully retrieved text from specific window:")
        win_data = specific_text_result["window_data"]
        print(f"Title: {win_data['window_title']}")
        print(f"Bounds: {win_data['bounds']}")
        print(f"Text:\n{win_data['text'][:500]}{'...' if len(win_data['text']) > 500 else ''}")
    else:
        print(f"Failed to read text from specific window: {specific_text_result['message']}")

    # 3. Test with a non-existent window title
    print("\nAttempting to read text from a non-existent window ('NoSuchAppXYZ123')...")
    non_existent_result = reader.get_specific_window_text("NoSuchAppXYZ123")
    if not non_existent_result["success"]:
        print(f"Correctly failed to find non-existent window: {non_existent_result['message']}")
    else:
        print("Unexpectedly found a window that shouldn't exist.")

    # 4. Test with an empty string for window title substring (should fail due to validation)
    print("\nAttempting to read text with an empty window title substring ('')...")
    empty_title_result = reader.get_specific_window_text("")
    if not empty_title_result["success"]:
        print(f"Correctly failed with empty search string: {empty_title_result['message']}")
    else:
        print("Unexpectedly succeeded with an empty search string.")

    # 5. Test with a non-string input
    print("\nAttempting to read text with a non-string input (e.g., 123)...")
    non_string_result = reader.get_specific_window_text(123) # type: ignore
    if not non_string_result["success"]:
        print(f"Correctly failed with non-string input: {non_string_result['message']}")
    else:
        print("Unexpectedly succeeded with non-string input.")
