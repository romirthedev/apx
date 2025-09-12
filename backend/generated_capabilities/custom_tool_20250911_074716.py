
import sys
import subprocess
import os
import tempfile
from typing import Dict, Any, Optional, Tuple

class ScreenReader:
    """
    A specialized tool class for reading text from the screen.

    This class utilizes external command-line tools to capture screen content
    and extract text using Optical Character Recognition (OCR). It aims to provide
    a safe, structured, and robust way to get screen text.

    Dependencies:
    - screencapture: For capturing screen content (usually built-in on macOS).
    - tesseract: For OCR. Installable via Homebrew: `brew install tesseract`.
    - ImageMagick (optional but recommended for pre-processing): `brew install imagemagick`.
    """

    def __init__(self):
        """
        Initializes the ScreenReader.

        Checks for necessary external dependencies and sets up temporary file handling.
        """
        self._dependencies_checked = False
        self._dependency_status: Dict[str, Any] = {"success": False, "message": "Dependencies not yet checked."}
        self._check_dependencies()

        # Use tempfile for safer temporary file management
        self.temp_dir = tempfile.mkdtemp(prefix="screen_reader_")

    def __del__(self):
        """Cleans up the temporary directory upon object destruction."""
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            try:
                for filename in os.listdir(self.temp_dir):
                    file_path = os.path.join(self.temp_dir, filename)
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                os.rmdir(self.temp_dir)
            except OSError as e:
                print(f"Warning: Could not clean up temporary directory {self.temp_dir}: {e}", file=sys.stderr)

    def _run_command(self, command: list[str], timeout: int = 60) -> Tuple[bool, str, str]:
        """
        Executes a shell command and returns its output, with timeout and error handling.

        Args:
            command: A list of strings representing the command and its arguments.
            timeout: The maximum time in seconds to wait for the command to complete.

        Returns:
            A tuple containing:
            - bool: True if the command executed successfully, False otherwise.
            - str: The standard output of the command, or an error message if
                   the command failed.
            - str: The standard error of the command, or an empty string if
                   there was no error.
        """
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate(timeout=timeout)
            if process.returncode == 0:
                return True, stdout, stderr
            else:
                return False, f"Command failed with return code {process.returncode}.\nStderr: {stderr}", stderr
        except FileNotFoundError:
            return False, f"Error: Command '{command[0]}' not found. Please ensure it is installed and in your system's PATH.", ""
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            return False, f"Command '{' '.join(command)}' timed out after {timeout} seconds.", stderr
        except Exception as e:
            return False, f"An unexpected error occurred while running command: {e}", ""

    def _check_dependencies(self) -> Dict[str, Any]:
        """
        Checks for the presence of required command-line tools.

        Required: 'screencapture', 'tesseract'.
        Recommended: 'convert' (from ImageMagick for pre-processing).
        """
        if self._dependencies_checked:
            return self._dependency_status

        dependencies = {
            "screencapture": "This is typically a built-in macOS command.",
            "tesseract": "For OCR. Install with: 'brew install tesseract'.",
            "convert": "For image pre-processing. Install with: 'brew install imagemagick'."
        }
        missing = []

        for dep, install_info in dependencies.items():
            command = ["which", dep]
            success, _, _ = self._run_command(command)
            if not success:
                missing.append(f"'{dep}' ({install_info})")

        if missing:
            self._dependency_status = {
                "success": False,
                "message": f"Missing required dependencies: {', '.join(missing)}."
            }
        else:
            self._dependency_status = {"success": True, "message": "All required dependencies are present."}

        self._dependencies_checked = True
        return self._dependency_status

    def _preprocess_image(self, image_path: str) -> Optional[str]:
        """
        Applies basic image pre-processing to improve OCR accuracy.
        Currently converts to grayscale and increases contrast.
        Requires ImageMagick's 'convert' command.

        Args:
            image_path: Path to the input image file.

        Returns:
            Path to the pre-processed image file, or None if pre-processing fails.
        """
        if not self._dependency_status.get("success") or "convert" not in self._run_command(["which", "convert"])[1]:
            # If dependencies aren't met or convert isn't found, return original path
            # for OCR to try its best without pre-processing.
            return image_path

        processed_image_path = os.path.join(self.temp_dir, f"processed_{os.path.basename(image_path)}")
        # Convert to grayscale, normalize contrast, and remove noise
        preprocess_command = [
            "convert", image_path,
            "-colorspace", "Gray",
            "-contrast-stretch", "0x0%", # Auto-adjust contrast
            "-normalize",
            "-deskew", "40%", # Attempt to deskew images
            "-unsharp", "0x0.75+0.75+0.008", # Sharpen slightly
            processed_image_path
        ]

        success, msg, _ = self._run_command(preprocess_command)
        if success:
            return processed_image_path
        else:
            print(f"Warning: Image pre-processing failed: {msg}. Proceeding with original image.", file=sys.stderr)
            return image_path # Fallback to original image if processing fails

    def _extract_text_from_image(self, image_path: str, lang: str = "eng") -> Dict[str, Any]:
        """
        Uses Tesseract OCR to extract text from an image file.

        Args:
            image_path: Path to the image file.
            lang: Language code for Tesseract (e.g., "eng", "fra").

        Returns:
            A dictionary containing 'success' (bool), 'message' (str), and 'text' (str, optional).
        """
        ocr_command = [
            "tesseract",
            image_path,
            "stdout",  # Output to standard output
            "-l", lang  # Specify language
        ]
        ocr_success, ocr_output, ocr_error = self._run_command(ocr_command)

        if not ocr_success:
            return {
                "success": False,
                "message": f"OCR failed. Tesseract returned an error.\nOutput:\n{ocr_output}\nError:\n{ocr_error}",
            }

        # Remove potential empty lines or leading/trailing whitespace
        extracted_text = ocr_output.strip()
        return {
            "success": True,
            "message": "Text extracted successfully.",
            "text": extracted_text
        }

    def _capture_screen_region_to_file(self, x: int, y: int, width: int, height: int) -> Tuple[bool, str, str]:
        """
        Captures a specific region of the screen and saves it to a temporary file.

        Args:
            x: The x-coordinate of the top-left corner of the region.
            y: The y-coordinate of the top-left corner of the region.
            width: The width of the region.
            height: The height of the region.

        Returns:
            A tuple containing:
            - bool: True if capture was successful, False otherwise.
            - str: Path to the saved image file, or an error message if failed.
            - str: Standard error output from the capture command.
        """
        image_filename = os.path.join(self.temp_dir, f"region_capture_{hash(self)}_{x}_{y}_{width}_{height}.png")
        capture_command = [
            "screencapture",
            "-R", f"{x},{y},{width},{height}",
            image_filename
        ]
        capture_success, capture_message, stderr = self._run_command(capture_command)

        if not capture_success:
            return False, capture_message, stderr
        return True, image_filename, ""

    def _capture_full_screen_to_file(self) -> Tuple[bool, str, str]:
        """
        Captures the entire screen and saves it to a temporary file.

        Returns:
            A tuple containing:
            - bool: True if capture was successful, False otherwise.
            - str: Path to the saved image file, or an error message if failed.
            - str: Standard error output from the capture command.
        """
        image_filename = os.path.join(self.temp_dir, f"full_screen_capture_{hash(self)}.png")
        capture_command = [
            "screencapture",
            image_filename
        ]
        capture_success, capture_message, stderr = self._run_command(capture_command)

        if not capture_success:
            return False, capture_message, stderr
        return True, image_filename, ""

    def _capture_active_window_to_file(self) -> Tuple[bool, str, str]:
        """
        Captures the active window and saves it to a temporary file.
        Note: This relies on macOS's screencapture tool which might not
        perfectly isolate only the window content without some background.
        A more robust solution might involve AppleScript or specific GUI automation frameworks.
        However, 'screencapture -i' provides an interactive way, but for programmatic
        use, capturing the full screen and then processing might be a fallback.
        This implementation attempts to use `screencapture -W` for active window.

        Returns:
            A tuple containing:
            - bool: True if capture was successful, False otherwise.
            - str: Path to the saved image file, or an error message if failed.
            - str: Standard error output from the capture command.
        """
        image_filename = os.path.join(self.temp_dir, f"active_window_capture_{hash(self)}.png")
        # The '-W' flag captures the active window. User might still need to click if prompted.
        # For fully programmatic, one might need to disable dialogs or use other methods.
        # We'll assume screencapture -W works without interaction for simplicity.
        capture_command = [
            "screencapture",
            "-W", # Capture the active window
            image_filename
        ]
        capture_success, capture_message, stderr = self._run_command(capture_command)

        if not capture_success:
            # Fallback to full screen capture if active window capture fails
            print("Warning: Direct active window capture failed. Falling back to full screen capture.", file=sys.stderr)
            return self._capture_full_screen_to_file()

        return True, image_filename, ""

    def read_screen_region(self, x: int, y: int, width: int, height: int, lang: str = "eng") -> Dict[str, Any]:
        """
        Reads text from a specific region of the screen.

        Args:
            x: The x-coordinate of the top-left corner of the region.
            y: The y-coordinate of the top-left corner of the region.
            width: The width of the region.
            height: The height of the region.
            lang: The language code for OCR (default is 'eng').

        Returns:
            A dictionary containing:
            - 'success' (bool): True if text was read successfully, False otherwise.
            - 'message' (str): A status message or error description.
            - 'text' (str, optional): The extracted text if successful.
            - 'image_path' (str, optional): The path to the temporary captured image file.
        """
        if not self._dependency_status["success"]:
            return self._dependency_status

        # Input validation
        if not all(isinstance(arg, int) for arg in [x, y, width, height]):
            return {"success": False, "message": "Invalid input types for coordinates and dimensions. Must be integers."}
        if width <= 0 or height <= 0:
            return {"success": False, "message": "Width and height must be positive integers."}
        if not isinstance(lang, str) or not lang:
            return {"success": False, "message": "Language code must be a non-empty string."}

        capture_success, image_path, capture_error = self._capture_screen_region_to_file(x, y, width, height)
        if not capture_success:
            return {"success": False, "message": f"Failed to capture screen region: {image_path}", "image_path": None}

        processed_image_path = self._preprocess_image(image_path)
        ocr_result = self._extract_text_from_image(processed_image_path, lang)

        # Clean up the processed image if it's different from the original
        if processed_image_path and os.path.exists(processed_image_path) and processed_image_path != image_path:
            try:
                os.remove(processed_image_path)
            except OSError as e:
                print(f"Warning: Could not remove temporary processed image file {processed_image_path}: {e}", file=sys.stderr)

        if not ocr_result["success"]:
            return {
                "success": False,
                "message": f"Failed to extract text from the captured region. {ocr_result['message']}",
                "image_path": image_path # Return original capture path for debugging
            }

        return {
            "success": True,
            "message": "Screen region text successfully extracted.",
            "text": ocr_result["text"],
            "image_path": image_path # Return the path to the raw captured image
        }

    def read_full_screen(self, lang: str = "eng") -> Dict[str, Any]:
        """
        Reads text from the entire current screen.

        Note: This will capture the entire screen. For accuracy, ensure the
        desired content is visible and not obscured.

        Args:
            lang: The language code for OCR (default is 'eng').

        Returns:
            A dictionary containing:
            - 'success' (bool): True if text was read successfully, False otherwise.
            - 'message' (str): A status message or error description.
            - 'text' (str, optional): The extracted text if successful.
            - 'image_path' (str, optional): The path to the temporary captured image file.
        """
        if not self._dependency_status["success"]:
            return self._dependency_status

        if not isinstance(lang, str) or not lang:
            return {"success": False, "message": "Language code must be a non-empty string."}

        capture_success, image_path, capture_error = self._capture_full_screen_to_file()
        if not capture_success:
            return {"success": False, "message": f"Failed to capture full screen: {image_path}", "image_path": None}

        processed_image_path = self._preprocess_image(image_path)
        ocr_result = self._extract_text_from_image(processed_image_path, lang)

        if processed_image_path and os.path.exists(processed_image_path) and processed_image_path != image_path:
            try:
                os.remove(processed_image_path)
            except OSError as e:
                print(f"Warning: Could not remove temporary processed image file {processed_image_path}: {e}", file=sys.stderr)

        if not ocr_result["success"]:
            return {
                "success": False,
                "message": f"Failed to extract text from the full screen. {ocr_result['message']}",
                "image_path": image_path
            }

        return {
            "success": True,
            "message": "Full screen text successfully extracted.",
            "text": ocr_result["text"],
            "image_path": image_path
        }

    def read_active_window(self, lang: str = "eng") -> Dict[str, Any]:
        """
        Reads text from the currently active window on macOS.

        This method attempts to capture the active window using `screencapture -W`
        and then uses Tesseract OCR to extract text. If `screencapture -W` fails,
        it falls back to capturing the full screen.

        Args:
            lang: The language code for OCR (default is 'eng').

        Returns:
            A dictionary containing:
            - 'success' (bool): True if text was read successfully, False otherwise.
            - 'message' (str): A status message or error description.
            - 'text' (str, optional): The extracted text if successful.
            - 'image_path' (str, optional): The path to the temporary captured image file.
        """
        if not self._dependency_status["success"]:
            return self._dependency_status

        if not isinstance(lang, str) or not lang:
            return {"success": False, "message": "Language code must be a non-empty string."}

        capture_success, image_path, capture_error = self._capture_active_window_to_file()

        if not capture_success:
            # The fallback message is already printed in _capture_active_window_to_file
            return {"success": False, "message": f"Failed to capture active window and full screen. {image_path}", "image_path": None}

        processed_image_path = self._preprocess_image(image_path)
        ocr_result = self._extract_text_from_image(processed_image_path, lang)

        if processed_image_path and os.path.exists(processed_image_path) and processed_image_path != image_path:
            try:
                os.remove(processed_image_path)
            except OSError as e:
                print(f"Warning: Could not remove temporary processed image file {processed_image_path}: {e}", file=sys.stderr)

        if not ocr_result["success"]:
            return {
                "success": False,
                "message": f"Failed to extract text from the active window capture. {ocr_result['message']}",
                "image_path": image_path
            }

        return {
            "success": True,
            "message": "Active window text successfully extracted.",
            "text": ocr_result["text"],
            "image_path": image_path
        }


if __name__ == "__main__":
    print("Initializing ScreenReader...")
    reader = ScreenReader()

    # Check dependencies first
    dep_status = reader._check_dependencies()
    print(f"Dependency Check: Success={dep_status['success']}, Message='{dep_status['message']}'")

    if dep_status["success"]:
        print("\n--- Reading Full Screen ---")
        full_screen_result = reader.read_full_screen()
        print(f"Success: {full_screen_result.get('success')}")
        print(f"Message: {full_screen_result.get('message')}")
        if full_screen_result.get('success'):
            print(f"Extracted Text (first 200 chars):\n{full_screen_result.get('text', 'N/A')[:200]}...")
            print(f"Temporary Image Path: {full_screen_result.get('image_path', 'N/A')}")

        print("\n--- Reading Specific Region ---")
        # Example: Capture a 400x200 region starting at (50, 50)
        # Ensure this region is visible on your screen when running this example.
        print("Attempting to read region at x=50, y=50, width=400, height=200. Please ensure this area is visible.")
        region_result = reader.read_screen_region(x=50, y=50, width=400, height=200)
        print(f"Success: {region_result.get('success')}")
        print(f"Message: {region_result.get('message')}")
        if region_result.get('success'):
            print(f"Extracted Text (first 200 chars):\n{region_result.get('text', 'N/A')[:200]}...")
            print(f"Temporary Image Path: {region_result.get('image_path', 'N/A')}")

        print("\n--- Reading Active Window ---")
        print("Please make sure the window you want to read is active.")
        active_window_result = reader.read_active_window()
        print(f"Success: {active_window_result.get('success')}")
        print(f"Message: {active_window_result.get('message')}")
        if active_window_result.get('success'):
            print(f"Extracted Text (first 200 chars):\n{active_window_result.get('text', 'N/A')[:200]}...")
            print(f"Temporary Image Path: {active_window_result.get('image_path', 'N/A')}")

        print("\n--- Testing Invalid Region (negative width) ---")
        invalid_region_result = reader.read_screen_region(x=100, y=100, width=-50, height=100)
        print(f"Success: {invalid_region_result.get('success')}")
        print(f"Message: {invalid_region_result.get('message')}")

        print("\n--- Testing Invalid Input Type ---")
        invalid_input_result = reader.read_screen_region(x=100.5, y=100, width=50, height=100)
        print(f"Success: {invalid_input_result.get('success')}")
        print(f"Message: {invalid_input_result.get('message')}")
    else:
        print("\nSkipping examples due to missing dependencies. Please install them.")
