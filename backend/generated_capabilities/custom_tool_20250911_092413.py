
import os
import subprocess
import sys
from typing import Dict, Any, Optional

# Import necessary libraries for screen capture and OCR.
# These are external dependencies and will need to be installed.
try:
    from PIL import Image
    import pytesseract
except ImportError:
    print(
        "Error: Required libraries 'Pillow' and 'pytesseract' are not installed."
    )
    print("Please install them using: pip install Pillow pytesseract")
    sys.exit(1)

# --- Configuration ---
# You might need to set the Tesseract executable path if it's not in your PATH.
# Example: pytesseract.pytesseract.tesseract_cmd = r'/usr/local/bin/tesseract'
# You can find the path by running 'which tesseract' in your terminal.
# If Tesseract is installed via Homebrew, it's often in /usr/local/bin/tesseract
# or /opt/homebrew/bin/tesseract (for Apple Silicon Macs).
# We'll try to auto-detect it, but this might fail.

def find_tesseract_path():
    """Attempts to find the Tesseract executable path."""
    tesseract_cmd = "tesseract"
    try:
        # Try finding it in PATH
        result = subprocess.run(
            ["which", tesseract_cmd], capture_output=True, text=True, check=True
        )
        path = result.stdout.strip()
        print(f"Found Tesseract at: {path}")
        return path
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Common alternative paths
        common_paths = [
            "/usr/local/bin/tesseract",
            "/opt/homebrew/bin/tesseract",
            "/usr/bin/tesseract",
        ]
        for p in common_paths:
            if os.path.exists(p):
                print(f"Found Tesseract at: {p}")
                return p
        print(
            "Warning: Tesseract executable not found in standard locations."
            " Please set `pytesseract.pytesseract.tesseract_cmd` manually."
        )
        return None

# Set Tesseract command path if found
tesseract_path = find_tesseract_path()
if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path


class ScreenReader:
    """
    A versatile tool for reading text from the screen, supporting both entire screen
    and specific window capture, with enhanced error handling and user guidance.

    This class leverages Pillow for screen capture and pytesseract for OCR.
    It also uses macOS's `screencapture` command-line utility and AppleScript
    for window management.
    """

    def __init__(self):
        """
        Initializes the ScreenReader and checks for necessary dependencies.
        """
        self.check_dependencies()
        self._check_accessibility_permissions()

    def check_dependencies(self):
        """
        Checks if required external libraries and tools are available.
        """
        try:
            from PIL import Image
            import pytesseract
            print("Pillow and pytesseract found.")
        except ImportError:
            print(
                "Error: Missing essential libraries. Please install Pillow and pytesseract:"
            )
            print("  pip install Pillow pytesseract")
            sys.exit(1)

        try:
            subprocess.run(
                ["screencapture", "-h"], capture_output=True, check=True
            )
            print("'screencapture' command found.")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(
                "Error: 'screencapture' command not found. This tool requires macOS."
            )
            sys.exit(1)

        try:
            subprocess.run(
                ["osascript", "-e", "delay 0.1"], capture_output=True, check=True
            )
            print("'osascript' command found.")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(
                "Error: 'osascript' command not found. This tool requires macOS."
            )
            sys.exit(1)

        if not pytesseract.pytesseract.tesseract_cmd:
            print(
                "Error: Tesseract OCR engine path is not configured."
                " Please ensure Tesseract is installed and accessible."
                " You might need to manually set `pytesseract.pytesseract.tesseract_cmd`."
            )
            sys.exit(1)

    def _check_accessibility_permissions(self) -> bool:
        """
        Checks if the necessary accessibility permissions are granted.

        On macOS, reading screen content requires accessibility permissions.
        This method attempts a more direct check. If permissions are not granted,
        subsequent operations will fail.

        Returns:
            bool: True if accessibility is likely enabled, False otherwise.
        """
        # A more robust check for accessibility permissions on macOS.
        # We try to execute a command that requires these permissions.
        # If it fails with a permission-related error, we assume it's not enabled.
        try:
            # Using `osascript` to interact with System Events, which requires accessibility.
            subprocess.run(
                [
                    "osascript",
                    "-e",
                    'tell application "System Events" to get name of every process',
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=5,  # Add a timeout to prevent hanging
            )
            print("Accessibility permissions appear to be granted.")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            error_msg = (
                "Accessibility permissions are not granted or Tesseract is not configured correctly."
            )
            if isinstance(e, subprocess.CalledProcessError):
                # Check for common error messages indicating permission denial
                if (
                    "UserWorld/com.apple.tccd" in e.stderr
                    or "The operation couldn't be completed" in e.stderr
                ):
                    error_msg = (
                        "Accessibility permissions are not granted. "
                        "Please enable them in System Settings > Privacy & Security > Accessibility "
                        "for your terminal application and any screen recording apps."
                    )
                else:
                    error_msg = f"Failed to check accessibility. Error: {e.stderr}"
            elif isinstance(e, subprocess.TimeoutExpired):
                error_msg = "Checking accessibility timed out. This often indicates permission issues or a slow system."
            else:
                error_msg = "Could not verify accessibility. 'osascript' command might be missing or Tesseract is misconfigured."

            print(f"Error: {error_msg}")
            return False

    def _capture_screenshot(self, region: Optional[tuple[int, int, int, int]] = None) -> Optional[str]:
        """
        Captures a screenshot of the entire screen or a specific region.

        Args:
            region (Optional[tuple[int, int, int, int]]): A tuple (x, y, width, height)
                                                         defining the region to capture.
                                                         If None, the entire screen is captured.

        Returns:
            Optional[str]: The path to the saved screenshot file, or None if capture failed.
        """
        temp_screenshot_path = "/tmp/screen_reader_temp_screenshot.png"
        try:
            cmd = ["screencapture", "-x"]  # -x: Don't play sound
            if region:
                x, y, width, height = region
                if not all(isinstance(val, int) and val >= 0 for val in region):
                    raise ValueError("Region coordinates and dimensions must be non-negative integers.")
                if width <= 0 or height <= 0:
                    raise ValueError("Region width and height must be positive.")
                cmd.extend(["-R", f"{x},{y},{width},{height}"])
            cmd.append(temp_screenshot_path)

            subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=10)
            if not os.path.exists(temp_screenshot_path):
                raise FileNotFoundError("Screenshot file was not created.")
            return temp_screenshot_path
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired, ValueError) as e:
            error_message = f"Failed to capture screenshot"
            if isinstance(e, ValueError):
                error_message += f": Invalid region specified - {e}"
            elif isinstance(e, FileNotFoundError):
                error_message += f": Screenshot file not found after command execution."
            elif isinstance(e, subprocess.TimeoutExpired):
                error_message += f": Operation timed out."
            else:
                error_message += f": {e}\nStderr: {getattr(e, 'stderr', 'N/A')}"
            print(f"Error: {error_message}")
            return None

    def _get_window_bounds(self, window_title_substring: str) -> Optional[tuple[int, int, int, int]]:
        """
        Uses AppleScript to find the bounds (x, y, width, height) of a window
        based on a substring of its title.

        Args:
            window_title_substring (str): A substring to match against window titles.

        Returns:
            Optional[tuple[int, int, int, int]]: The bounds of the window, or None if not found or error.
        """
        applescript_cmd = f'''
        tell application "System Events"
            set front_process to first process whose frontmost is true
            set window_list to windows of front_process
            set target_window to null
            repeat with w in window_list
                try
                    if name of w contains "{window_title_substring}" then
                        set target_window to w
                        exit repeat
                    end if
                on error
                    -- Ignore windows that cannot be accessed (e.g., security restrictions)
                end try
            end repeat

            if target_window is null then
                return "WINDOW_NOT_FOUND"
            else
                set window_pos to position of target_window
                set window_size to size of target_window
                return (item 1 of window_pos) & "," & (item 2 of window_pos) & "," & (item 1 of window_size) & "," & (item 2 of window_size)
            end if
        end tell
        '''
        try:
            process = subprocess.run(
                ["osascript", "-e", applescript_cmd],
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            )
            bounds_str = process.stdout.strip()

            if bounds_str == "WINDOW_NOT_FOUND":
                print(f"Error: No frontmost window found with title containing '{window_title_substring}'.")
                return None
            elif not bounds_str:
                print(f"Error: AppleScript returned empty output for window bounds.")
                return None

            x, y, width, height = map(int, bounds_str.split(","))
            return x, y, width, height

        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired, ValueError) as e:
            error_message = f"Failed to get window bounds for '{window_title_substring}'"
            if isinstance(e, subprocess.TimeoutExpired):
                error_message += ": Operation timed out."
            elif isinstance(e, subprocess.CalledProcessError):
                error_message += f": {e.stderr}"
            elif isinstance(e, ValueError):
                error_message += f": Could not parse bounds '{bounds_str}'"
            else:
                error_message += f": {e}"
            print(f"Error: {error_message}")
            return None

    def read_screen_text(self) -> Dict[str, Any]:
        """
        Reads all visible text content from the current screen using OCR.

        Returns:
            Dict[str, Any]: A dictionary containing the operation result.
                - 'success' (bool): True if text was successfully read, False otherwise.
                - 'message' (str): A descriptive message about the operation.
                - 'text' (str, optional): The extracted text if successful.
        """
        if not self._check_accessibility_permissions():
            return {
                'success': False,
                'message': "Accessibility permissions are not granted or Tesseract is not configured. Please check system settings and Tesseract installation.",
                'text': None
            }

        screenshot_path = self._capture_screenshot()
        if not screenshot_path:
            return {
                'success': False,
                'message': "Failed to capture the screen.",
                'text': None
            }

        extracted_text = self._perform_ocr(screenshot_path)

        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)

        if extracted_text is not None:
            if extracted_text.strip():
                return {
                    'success': True,
                    'message': "Screen text successfully read.",
                    'text': extracted_text
                }
            else:
                return {
                    'success': False,
                    'message': "No text detected on the screen.",
                    'text': None
                }
        else:
            return {
                'success': False,
                'message': "OCR failed to process the screenshot.",
                'text': None
            }

    def read_window_text(self, window_title_substring: str) -> Dict[str, Any]:
        """
        Reads text from a specific window based on a substring of its title.

        Args:
            window_title_substring (str): A substring that uniquely identifies
                                          the target window's title. Must be a non-empty string.

        Returns:
            Dict[str, Any]: A dictionary containing the operation result.
                - 'success' (bool): True if text was successfully read, False otherwise.
                - 'message' (str): A descriptive message about the operation.
                - 'text' (str, optional): The extracted text if successful.
        """
        if not isinstance(window_title_substring, str) or not window_title_substring:
            return {
                'success': False,
                'message': "Invalid input: 'window_title_substring' must be a non-empty string.",
                'text': None
            }

        if not self._check_accessibility_permissions():
            return {
                'success': False,
                'message': "Accessibility permissions are not granted or Tesseract is not configured. Please check system settings and Tesseract installation.",
                'text': None
            }

        window_bounds = self._get_window_bounds(window_title_substring)
        if not window_bounds:
            return {
                'success': False,
                'message': f"Could not find or access window with title substring: '{window_title_substring}'. Ensure it's open and frontmost.",
                'text': None
            }

        screenshot_path = self._capture_screenshot(region=window_bounds)
        if not screenshot_path:
            return {
                'success': False,
                'message': f"Failed to capture screenshot for window '{window_title_substring}'.",
                'text': None
            }

        extracted_text = self._perform_ocr(screenshot_path)

        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)

        if extracted_text is not None:
            if extracted_text.strip():
                return {
                    'success': True,
                    'message': f"Text from window '{window_title_substring}' successfully read.",
                    'text': extracted_text
                }
            else:
                return {
                    'success': False,
                    'message': f"No text detected in window '{window_title_substring}'.",
                    'text': None
                }
        else:
            return {
                'success': False,
                'message': f"OCR failed to process the screenshot of window '{window_title_substring}'.",
                'text': None
            }

    def _perform_ocr(self, image_path: str, lang: str = 'eng') -> Optional[str]:
        """
        Performs OCR on an image file.

        Args:
            image_path (str): Path to the image file.
            lang (str): Language code for OCR (e.g., 'eng' for English).

        Returns:
            Optional[str]: The extracted text, or None if OCR failed.
        """
        try:
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img, lang=lang)
            return text
        except pytesseract.TesseractNotFoundError:
            print(
                "Error: Tesseract is not installed or not in your PATH. "
                "Please install Tesseract OCR engine. "
                "On macOS with Homebrew: `brew install tesseract`"
            )
            return None
        except Exception as e:
            print(f"Error during OCR processing: {e}")
            return None

if __name__ == '__main__':
    print("--- Enhancing ScreenReader Tool ---")

    # --- Dependency Check ---
    # This will exit if dependencies are not met during instantiation
    try:
        reader = ScreenReader()
    except SystemExit:
        print("\nExiting due to missing dependencies.")
        sys.exit(1)

    # --- Example Usage ---

    print("\n--- Testing read_screen_text ---")
    print("Attempting to read text from the entire screen...")
    result_screen = reader.read_screen_text()
    print(f"Success: {result_screen['success']}")
    print(f"Message: {result_screen['message']}")
    if result_screen['success']:
        print("\n--- Extracted Screen Text (First 500 chars) ---")
        print(result_screen['text'][:500])
        if len(result_screen['text']) > 500:
            print("...")
        print("--------------------------------------------")

    print("\n--- Testing read_window_text ---")
    # IMPORTANT: Replace "Finder" with a substring of a currently open and frontmost window title.
    # Examples: "Terminal", "Google Chrome", "Safari", "Notes", "TextEdit"
    # If you have a window titled "my_project - bash", use "bash" or "my_project".
    target_window_title = "Finder"
    print(f"Attempting to read text from a window with title containing: '{target_window_title}'")
    result_window = reader.read_window_text(target_window_title)
    print(f"Success: {result_window['success']}")
    print(f"Message: {result_window['message']}")
    if result_window['success']:
        print(f"\n--- Extracted Text from '{target_window_title}' (First 500 chars) ---")
        print(result_window['text'][:500])
        if len(result_window['text']) > 500:
            print("...")
        print("----------------------------------------------------")

    print("\n--- Test Complete ---")
    print("\nTroubleshooting Tips:")
    print("1. Ensure Tesseract OCR is installed: `brew install tesseract` (or your package manager).")
    print("2. Ensure language data is installed for Tesseract: `brew install tesseract-lang`.")
    print("3. Verify Tesseract executable path: If it's not auto-detected, manually set `pytesseract.pytesseract.tesseract_cmd`.")
    print("4. Grant Accessibility Permissions: Go to System Settings > Privacy & Security > Accessibility and enable permissions for your terminal application (e.g., iTerm, Terminal.app) and any relevant screen recording or automation tools.")
    print("5. For `read_window_text`, ensure the target window is open and frontmost (actively selected).")
    print("6. OCR accuracy depends on screen resolution, font clarity, and image quality.")
