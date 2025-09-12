
import subprocess
import sys
import os
from typing import Dict, Any, Optional
import tempfile

class ScreenReader:
    """
    A specialized tool class for reading screen text.
    Currently supports macOS using `screencapture` and `textutil`.
    Future enhancements may include cross-platform support via libraries like `pyautogui` and `pytesseract`.
    """

    def __init__(self):
        """
        Initializes the ScreenReader.
        Checks for platform compatibility and required command-line tools.
        """
        self.platform = sys.platform
        self.is_macos = self.platform == "darwin"

        if not self.is_macos:
            print(
                "Warning: Screen reading is currently only fully supported on macOS. "
                "Consider installing 'pyautogui' and 'pytesseract' for cross-platform support.",
                file=sys.stderr
            )
        else:
            self._check_macos_dependencies()

    def _check_macos_dependencies(self):
        """
        Checks if the necessary command-line tools for macOS are available.
        """
        required_commands = ["screencapture", "textutil"]
        for cmd in required_commands:
            try:
                subprocess.run(
                    ["which", cmd],
                    capture_output=True,
                    check=True,
                    text=True
                )
            except (FileNotFoundError, subprocess.CalledProcessError):
                print(
                    f"Error: Required command-line tool '{cmd}' not found on macOS. "
                    "Please ensure it is installed and accessible in your PATH.",
                    file=sys.stderr
                )
                # Consider raising an exception or exiting if critical dependencies are missing
                # raise ImportError(f"Missing macOS dependency: {cmd}")

    def _run_command(self, command: list[str], input_data: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes a shell command and returns its output in a structured dictionary.

        Args:
            command: A list of strings representing the command and its arguments.
            input_data: Optional string data to be piped into the command's stdin.

        Returns:
            A dictionary containing 'success' (bool), 'message' (str), and 'output' (list[str] or None).
        """
        try:
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                encoding='utf-8',
                input=input_data
            )
            return {
                "success": True,
                "message": "Command executed successfully.",
                "output": process.stdout.strip().splitlines() if process.stdout else []
            }
        except FileNotFoundError:
            return {
                "success": False,
                "message": f"Error: Command '{command[0]}' not found. Ensure it's installed and in your PATH.",
                "output": None
            }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "message": f"Error executing command: {e.stderr.strip() or e.stdout.strip()}",
                "output": None
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"An unexpected error occurred: {e}",
                "output": None
            }

    def read_screen_text(self, capture_area: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
        """
        Reads visible text from the screen.

        On macOS, this method captures a screenshot of the entire screen or a specified area
        and then uses `textutil` to extract text from it.
        The accuracy of text extraction depends heavily on the image quality and
        the capabilities of the underlying text recognition engine.

        Args:
            capture_area: An optional dictionary specifying the capture area.
                          Keys: 'x', 'y', 'width', 'height' (integers).
                          If None, the entire screen is captured.

        Returns:
            A dictionary with the following keys:
            - 'success' (bool): True if the operation was successful, False otherwise.
            - 'message' (str): A descriptive message about the operation's outcome.
            - 'text' (Optional[str]): The extracted screen text if successful, None otherwise.
        """
        if not self.is_macos:
            return {
                "success": False,
                "message": "Screen text reading via `screencapture` and `textutil` is only supported on macOS.",
                "text": None
            }

        # Create a temporary file for the screenshot
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_image_file:
            temp_image_path = temp_image_file.name

        capture_command = ["screencapture"]

        if capture_area:
            # Validate capture area dimensions
            if not all(k in capture_area for k in ('x', 'y', 'width', 'height')):
                return {
                    "success": False,
                    "message": "Invalid 'capture_area' dictionary. It must contain 'x', 'y', 'width', and 'height'.",
                    "text": None
                }
            if not all(isinstance(v, int) and v >= 0 for v in capture_area.values()):
                return {
                    "success": False,
                    "message": "'capture_area' values (x, y, width, height) must be non-negative integers.",
                    "text": None
                }

            # Add coordinates for specific area capture
            capture_command.extend([
                "-R", f"{capture_area['x']},{capture_area['y']},{capture_area['width']},{capture_area['height']}"
            ])
            capture_command.append(temp_image_path)
        else:
            # Capture the entire screen (or primary display)
            capture_command.append(temp_image_path)

        # 1. Capture a screenshot
        capture_result = self._run_command(capture_command)

        if not capture_result["success"]:
            # Clean up the temporary file if capture failed
            if os.path.exists(temp_image_path):
                os.remove(temp_image_path)
            return {
                "success": False,
                "message": f"Failed to capture screen: {capture_result['message']}",
                "text": None
            }

        # 2. Use textutil to extract text from the captured image
        # `textutil -convert txt -inputformat png -output -` reads PNG and outputs to stdout as TXT
        textutil_command = ["textutil", "-convert", "txt", "-inputformat", "png", "-output", "-", temp_image_path]
        text_extraction_result = self._run_command(textutil_command)

        # Clean up the temporary image file regardless of extraction success
        try:
            if os.path.exists(temp_image_path):
                os.remove(temp_image_path)
        except OSError as e:
            print(f"Warning: Could not remove temporary file {temp_image_path}: {e}", file=sys.stderr)

        if not text_extraction_result["success"]:
            return {
                "success": False,
                "message": f"Failed to extract text from image: {text_extraction_result['message']}",
                "text": None
            }

        extracted_text = "\n".join(text_extraction_result["output"])

        return {
            "success": True,
            "message": "Screen text extracted successfully.",
            "text": extracted_text
        }

    def read_window_text(self, window_title_substring: str) -> Dict[str, Any]:
        """
        Reads text from a specific window on macOS.

        This method attempts to find a window containing the provided substring in its title
        and then extract text from it. This is a more complex operation and is
        currently simulated by providing information about the limitations.

        A robust implementation would typically involve:
        1. Using `osascript` to query window information (position, size, title).
        2. Using `screencapture` with the coordinates obtained from `osascript`.
        3. Processing the captured image with `textutil` or an OCR library.

        This implementation provides an informative message about the complexity and
        does not perform actual window targeting due to its intricate nature
        with standard command-line tools.

        Args:
            window_title_substring: A substring to match against window titles.

        Returns:
            A dictionary with the following keys:
            - 'success' (bool): True if the operation was successful, False otherwise.
            - 'message' (str): A descriptive message about the operation's outcome.
            - 'text' (Optional[str]): The extracted text from the targeted window if successful, None otherwise.
        """
        if not self.is_macos:
            return {
                "success": False,
                "message": "Targeting specific windows for text extraction is currently only supported on macOS.",
                "text": None
            }

        if not window_title_substring or not isinstance(window_title_substring, str):
            return {
                "success": False,
                "message": "Invalid input: 'window_title_substring' must be a non-empty string.",
                "text": None
            }

        # --- Explanation of advanced approach ---
        # To implement this properly, one would need to:
        # 1. Use `osascript` to get a list of running processes and their windows.
        #    Example: `osascript -e 'tell application "System Events" to get {name, title} of every window of every process whose background only is false'`
        # 2. Parse the output to find the desired window based on `window_title_substring`.
        # 3. If found, get its AXFrame (bounding box) using `osascript` again.
        #    Example: `osascript -e 'tell application "System Events" to get description of attribute "AXFrame" of window 1 of process "Finder"'`
        # 4. Extract 'x', 'y', 'width', 'height' from the AXFrame description.
        # 5. Call `read_screen_text` with the calculated `capture_area`.
        #
        # Due to the complexity and fragility of parsing osascript output and the
        # dependency on specific application structures, a full implementation is
        # beyond the scope of simple command-line tool integration without dedicated libraries.

        return {
            "success": False,
            "message": (
                f"Targeting window with title containing '{window_title_substring}' is not fully implemented. "
                "This feature requires advanced scripting (e.g., AppleScript) to identify window bounds, "
                "which is complex and application-dependent. Consider capturing the full screen or a specific region "
                "and processing the text manually, or explore dedicated macOS automation libraries."
            ),
            "text": None
        }

    def read_screen_with_ocr(self, capture_area: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
        """
        Reads screen text using OCR.

        This function is a placeholder for a more advanced implementation that
        would use a dedicated OCR library like Tesseract (via `pytesseract`).
        It currently provides a message indicating that this functionality is not yet implemented.

        Args:
            capture_area: An optional dictionary specifying the capture area.
                          Keys: 'x', 'y', 'width', 'height' (integers).
                          If None, the entire screen is captured.

        Returns:
            A dictionary with the following keys:
            - 'success' (bool): False, as this feature is not yet implemented.
            - 'message' (str): A descriptive message about the operation's outcome.
            - 'text' (None): Always None for this unimplemented feature.
        """
        return {
            "success": False,
            "message": (
                "OCR-based screen text reading (e.g., using Tesseract) is not yet implemented. "
                "This would require installing 'pytesseract' and Tesseract OCR engine."
            ),
            "text": None
        }

if __name__ == '__main__':
    # Example Usage
    print("--- Testing ScreenReader Tool ---")

    reader = ScreenReader()

    # Test reading full screen text on macOS
    if reader.is_macos:
        print("\n--- Testing read_screen_text (full screen) ---")
        result_full_screen = reader.read_screen_text()
        print(f"Success: {result_full_screen['success']}")
        print(f"Message: {result_full_screen['message']}")
        if result_full_screen['success'] and result_full_screen['text']:
            print("Extracted Text (first 200 chars):")
            print(result_full_screen['text'][:200] + "..." if result_full_screen['text'] else "No text extracted.")
        elif result_full_screen['success']:
            print("No text could be extracted from the screen (this might be expected on a blank screen or with minimal content).")

        print("\n--- Testing read_screen_text (specific area) ---")
        # Example: Capture a 200x100 area starting at (100, 100)
        # Note: This requires manual adjustment based on what's visible on your screen.
        # For this example, we'll assume a simple area; you might need to adapt it.
        test_area = {"x": 100, "y": 100, "width": 200, "height": 100}
        print(f"Attempting to capture area: {test_area}")
        result_partial_screen = reader.read_screen_text(capture_area=test_area)
        print(f"Success: {result_partial_screen['success']}")
        print(f"Message: {result_partial_screen['message']}")
        if result_partial_screen['success'] and result_partial_screen['text']:
            print("Extracted Text from Area:")
            print(result_partial_screen['text'])
        elif result_partial_screen['success']:
            print("No text could be extracted from the specified area.")


    # Test reading specific window text (will return informative message)
    print("\n--- Testing read_window_text (demonstration of limitation) ---")
    result_window = reader.read_window_text("System Preferences")
    print(f"Success: {result_window['success']}")
    print(f"Message: {result_window['message']}")
    if result_window['success']:
        print("Extracted Text:")
        print(result_window['text'])

    # Test unimplemented OCR feature
    print("\n--- Testing read_screen_with_ocr (not implemented) ---")
    result_ocr = reader.read_screen_with_ocr()
    print(f"Success: {result_ocr['success']}")
    print(f"Message: {result_ocr['message']}")

    # Example of invalid input for read_window_text
    print("\n--- Testing read_window_text with invalid input ---")
    result_invalid_window = reader.read_window_text("")
    print(f"Success: {result_invalid_window['success']}")
    print(f"Message: {result_invalid_window['message']}")

    # Example of invalid input for read_screen_text (capture_area)
    print("\n--- Testing read_screen_text with invalid capture_area ---")
    result_invalid_area = reader.read_screen_text(capture_area={"x": 10, "y": 10, "width": -50, "height": 100})
    print(f"Success: {result_invalid_area['success']}")
    print(f"Message: {result_invalid_area['message']}")
