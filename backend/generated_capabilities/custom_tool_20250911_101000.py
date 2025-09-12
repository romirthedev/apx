
import datetime
import os
import re
from typing import Dict, Any, Optional

try:
    from PIL import ImageGrab
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

class ScreenshotTool:
    """
    A specialized tool for capturing screenshots and saving them to disk.

    This class provides a safe and structured way to take screenshots,
    returning results as dictionaries with success status, messages, and data.
    It is designed with macOS compatibility in mind, leveraging Pillow for
    screen capture capabilities. This enhanced version includes improved
    input validation, error handling, and flexibility in saving.
    """

    def __init__(self, default_save_dir: Optional[str] = None) -> None:
        """
        Initializes the ScreenshotTool.

        Args:
            default_save_dir: The default directory to save screenshots to.
                              If None, the current working directory will be used.
                              This path will be validated and created if necessary.
        """
        self._default_save_dir = self._validate_and_prepare_directory(default_save_dir)
        if not PIL_AVAILABLE:
            print("Warning: Pillow library (PIL) is not installed. Screenshot functionality will be unavailable.")
            print("Please install it using: pip install Pillow")

    def _validate_and_prepare_directory(self, directory: Optional[str]) -> str:
        """
        Validates, normalizes, and ensures the existence of a save directory.

        Args:
            directory: The path to the directory to check/create.

        Returns:
            The absolute path to the validated and existing directory.

        Raises:
            ValueError: If the provided directory path is invalid or cannot be created.
        """
        if directory is None:
            target_dir = os.getcwd()
        else:
            target_dir = os.path.abspath(os.path.expanduser(directory))

        if not os.path.exists(target_dir):
            try:
                os.makedirs(target_dir, exist_ok=True)
                print(f"Info: Created directory for screenshots: '{target_dir}'")
            except OSError as e:
                raise ValueError(f"Error creating directory '{target_dir}': {e}") from e
        elif not os.path.isdir(target_dir):
            raise ValueError(f"The provided path '{target_dir}' is not a directory.")
        elif not os.access(target_dir, os.W_OK):
            raise ValueError(f"The directory '{target_dir}' is not writable.")

        return target_dir

    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitizes a filename to remove invalid characters and prevent path traversal.

        Args:
            filename: The original filename string.

        Returns:
            A safe filename string.
        """
        # Remove characters that are not alphanumeric, underscore, or hyphen
        safe_filename = re.sub(r'[^\w\-]', '', filename)
        # Prevent leading/trailing spaces or periods
        safe_filename = safe_filename.strip(' .')
        # Ensure filename is not empty after sanitization
        if not safe_filename:
            return f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return safe_filename

    def take_screenshot(self, filename: Optional[str] = None, save_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Takes a screenshot of the entire screen and saves it to a file.

        Args:
            filename: The desired name for the screenshot file (without extension).
                      If None, a timestamp-based filename will be generated.
                      The filename will be sanitized to ensure safety.
            save_dir: The directory where the screenshot should be saved.
                      If None, the default save directory initialized with the tool will be used.
                      If provided, this directory will be validated and created if necessary.

        Returns:
            A dictionary containing:
            - 'success' (bool): True if the screenshot was taken and saved successfully, False otherwise.
            - 'message' (str): A description of the outcome.
            - 'filepath' (str, optional): The absolute path to the saved screenshot if successful.
            - 'filename' (str, optional): The name of the saved screenshot file if successful.
        """
        if not PIL_AVAILABLE:
            return {
                "success": False,
                "message": "Pillow (PIL) library is not installed. Cannot take screenshot."
            }

        try:
            target_save_dir = self._validate_and_prepare_directory(save_dir if save_dir is not None else self._default_save_dir)
        except ValueError as e:
            return {
                "success": False,
                "message": f"Failed to prepare save directory: {e}"
            }

        if filename is None:
            base_filename = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        else:
            base_filename = self._sanitize_filename(filename)

        output_filename = f"{base_filename}.png"
        filepath = os.path.join(target_save_dir, output_filename)

        try:
            # ImageGrab.grab() captures the entire screen on supported platforms.
            img = ImageGrab.grab()
            if img is None:
                return {
                    "success": False,
                    "message": "Failed to capture screenshot. ImageGrab.grab() returned None."
                }
            img.save(filepath)
            return {
                "success": True,
                "message": f"Screenshot saved successfully to '{filepath}'",
                "filepath": filepath,
                "filename": output_filename
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error taking or saving screenshot: {e}",
                "filepath": None,
                "filename": None
            }

if __name__ == '__main__':
    # Example usage:

    # 1. Initialize with default save directory (current directory)
    print("--- Initializing ScreenshotTool with default save directory ---")
    try:
        tool = ScreenshotTool()
        result = tool.take_screenshot()
        if result["success"]:
            print(f"Screenshot saved: {result['filepath']}")
        else:
            print(f"Failed to take screenshot: {result['message']}")
    except ValueError as e:
        print(f"Initialization error: {e}")
    print("-" * 30)

    # 2. Initialize with a specific save directory
    custom_save_path = os.path.join("~", "Desktop", "MyScreenshotsTool")
    print(f"--- Initializing ScreenshotTool with custom save directory: {custom_save_path} ---")
    try:
        tool_custom_dir = ScreenshotTool(default_save_dir=custom_save_path)
        result_custom = tool_custom_dir.take_screenshot(filename="my_initial_shot")
        if result_custom["success"]:
            print(f"Screenshot saved: {result_custom['filepath']}")
        else:
            print(f"Failed to take screenshot: {result_custom['message']}")
    except ValueError as e:
        print(f"Initialization error: {e}")
    print("-" * 30)

    # 3. Take a screenshot and specify a different save directory, overriding default
    another_custom_path = os.path.join("~", "Documents", "ToolOutput")
    print(f"--- Taking screenshot and saving to a specified directory: {another_custom_path} ---")
    try:
        # Re-using tool_custom_dir for demonstration, but could initialize a new one
        result_specific_dir = tool_custom_dir.take_screenshot(save_dir=another_custom_path, filename="specific_location_shot")
        if result_specific_dir["success"]:
            print(f"Screenshot saved: {result_specific_dir['filepath']}")
        else:
            print(f"Failed to take screenshot: {result_specific_dir['message']}")
    except ValueError as e:
        print(f"Error taking screenshot: {e}")
    print("-" * 30)

    # 4. Example of invalid filename input
    print("--- Testing with an invalid filename ---")
    try:
        result_invalid_filename = tool_custom_dir.take_screenshot(filename="invalid/char*name?.png")
        if result_invalid_filename["success"]:
            print(f"Screenshot saved: {result_invalid_filename['filepath']}")
        else:
            print(f"Failed to take screenshot: {result_invalid_filename['message']}")
    except ValueError as e:
        print(f"Error taking screenshot: {e}")
    print("-" * 30)

    # 5. Example of error handling if directory is not writable (simulated)
    # This is hard to simulate reliably without elevated privileges or specific OS configurations.
    # A conceptual example would involve trying to save to a root directory without permissions.
    # The _validate_and_prepare_directory should catch this if permissions are insufficient.

    if not PIL_AVAILABLE:
        print("\nPillow is not installed. Please install it using 'pip install Pillow' to fully test the functionality.")
