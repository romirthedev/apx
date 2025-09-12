
import sys
import subprocess
import logging
import os
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ScreenTextReader:
    """
    A specialized Python tool for reading text from the screen, primarily designed for macOS.

    This class leverages system-level tools and OCR capabilities to extract text from
    full screen captures or specific defined areas. It aims to provide a robust
    and user-friendly interface for screen text extraction.

    The system lacks a direct capability to capture and process screen text (OCR)
    without external dependencies. This tool integrates with commonly used external
    libraries and system utilities to fulfill this requirement.

    Required Dependencies:
        - macOS operating system (primary target)
        - `screencapture` utility (built-in on macOS)
        - `tesseract` OCR engine (install via `brew install tesseract` on macOS)
        - `pytesseract` Python wrapper for Tesseract (install via `pip install pytesseract`)
        - `Pillow` for image manipulation (install via `pip install Pillow`)
    """

    def __init__(self):
        """
        Initializes the ScreenTextReader.
        Logs a warning if the script is not running on macOS, as functionality
        might be limited or require different dependencies on other platforms.
        """
        self.screenshot_temp_dir = "/tmp"  # Use /tmp for temporary screenshots
        if sys.platform != "darwin":
            logging.warning(
                "ScreenTextReader is primarily designed for macOS. "
                "Screen capture and OCR functionalities might be limited or "
                "require different implementations on other operating systems."
            )
        self._ensure_dependencies()

    def _ensure_dependencies(self) -> None:
        """
        Checks for the presence of required Python libraries.
        Logs an error if any are missing.
        """
        try:
            import pytesseract
            from PIL import Image
            logging.info("Required Python libraries (pytesseract, Pillow) found.")
        except ImportError as e:
            logging.error(f"Missing required Python library: {e}. Please install them: pip install pytesseract Pillow")
            # Raising an exception here might be too harsh for a tool that might be partially functional.
            # Instead, errors will be caught in the methods that use these libraries.

    def _run_command(self, command: List[str], timeout: int = 30) -> Dict[str, Any]:
        """
        Executes a shell command and returns structured output, with timeout and error handling.

        Args:
            command: A list of strings representing the command and its arguments.
            timeout: The maximum time in seconds to wait for the command to complete.

        Returns:
            A dictionary containing 'success' (bool), 'message' (str), and 'output' (str).
            If an error occurs, 'success' will be False, and 'message' will contain error details.
        """
        try:
            logging.debug(f"Executing command: {' '.join(command)}")
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            stdout, stderr = process.communicate(timeout=timeout)

            if process.returncode == 0:
                logging.info(f"Command executed successfully: {' '.join(command)}")
                return {"success": True, "message": "Command executed successfully.", "output": stdout.strip()}
            else:
                error_message = stderr.strip() if stderr else "Unknown error during command execution."
                logging.error(f"Command failed: {' '.join(command)} - {error_message}")
                return {"success": False, "message": f"Command execution failed: {error_message}", "output": ""}
        except FileNotFoundError:
            error_message = f"Command not found: '{command[0]}'. Please ensure it is installed and in your system's PATH."
            logging.error(error_message)
            return {"success": False, "message": error_message, "output": ""}
        except subprocess.TimeoutExpired:
            error_message = f"Command timed out after {timeout} seconds: {' '.join(command)}"
            logging.error(error_message)
            return {"success": False, "message": error_message, "output": ""}
        except Exception as e:
            logging.error(f"An unexpected error occurred while running command {' '.join(command)}: {e}")
            return {"success": False, "message": f"An unexpected error occurred: {e}", "output": ""}

    def _capture_screenshot(self, filename: str, area: Optional[tuple[int, int, int, int]] = None) -> Dict[str, Any]:
        """
        Captures a screenshot of the entire screen or a specific area.

        Args:
            filename: The name of the file to save the screenshot to (within self.screenshot_temp_dir).
            area: A tuple (x, y, width, height) defining the capture area. If None, captures the full screen.

        Returns:
            A dictionary with 'success' (bool) and 'message' (str).
        """
        full_path = os.path.join(self.screenshot_temp_dir, filename)
        if sys.platform == "darwin":
            command = ["screencapture"]
            if area:
                x, y, width, height = area
                command.extend(["-R", f"{x},{y},{width},{height}"])
            command.append(full_path)
            capture_result = self._run_command(command)
            if capture_result["success"]:
                logging.info(f"Screenshot saved to: {full_path}")
                return {"success": True, "message": f"Screenshot saved successfully to {full_path}.", "filepath": full_path}
            else:
                return {"success": False, "message": f"Failed to capture screen: {capture_result['message']}"}
        else:
            # Basic fallback for non-macOS platforms, might require different tools
            return {"success": False, "message": "Screen capture is not directly supported on this platform. Consider implementing platform-specific capture methods."}

    def _perform_ocr(self, image_path: str) -> Dict[str, Any]:
        """
        Performs Optical Character Recognition (OCR) on an image file.

        Args:
            image_path: The path to the image file.

        Returns:
            A dictionary with 'success' (bool), 'message' (str), and 'text' (str).
        """
        try:
            import pytesseract
            from PIL import Image
        except ImportError:
            error_msg = "Required libraries not found. Please install them: pip install pytesseract Pillow"
            logging.error(error_msg)
            return {"success": False, "message": error_msg, "text": ""}

        # Attempt to find tesseract executable. User might need to configure this.
        # Example: pytesseract.pytesseract.tesseract_cmd = r'/usr/local/bin/tesseract'
        # This line can be uncommented and adjusted if tesseract is not in PATH.
        # try:
        #     pytesseract.get_tesseract_version()
        # except pytesseract.TesseractNotFoundError:
        #     logging.warning("Tesseract executable not found in PATH. Please ensure Tesseract is installed and its path is configured.")
        #     return {"success": False, "message": "Tesseract OCR engine not found in PATH.", "text": ""}

        if not os.path.exists(image_path):
            error_msg = f"Image file not found at: {image_path}"
            logging.error(error_msg)
            return {"success": False, "message": error_msg, "text": ""}

        try:
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img)
            logging.info(f"Successfully performed OCR on {image_path}.")
            return {"success": True, "message": "OCR processed successfully.", "text": text.strip()}
        except pytesseract.TesseractNotFoundError:
            error_msg = "Tesseract OCR engine not found. Please install Tesseract (e.g., 'brew install tesseract' on macOS) and ensure it's in your PATH, or configure `pytesseract.tesseract_cmd`."
            logging.error(error_msg)
            return {"success": False, "message": error_msg, "text": ""}
        except Exception as e:
            logging.error(f"An error occurred during OCR processing for {image_path}: {e}")
            return {"success": False, "message": f"An error occurred during OCR processing: {e}", "text": ""}

    def _cleanup_screenshot(self, filepath: str) -> None:
        """
        Removes a temporary screenshot file.

        Args:
            filepath: The full path to the screenshot file to remove.
        """
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                logging.debug(f"Removed temporary screenshot file: {filepath}")
        except Exception as e:
            logging.warning(f"Failed to remove temporary screenshot file {filepath}: {e}")

    def read_full_screen_text(self) -> Dict[str, Any]:
        """
        Reads text from the entire screen using screencapture and Tesseract OCR.

        This method captures a screenshot of the entire screen and then uses
        Tesseract OCR to extract text.

        Returns:
            A dictionary with 'success' (bool), 'message' (str), and 'text' (str).
        """
        screenshot_filename = "full_screen_capture.png"
        capture_result = self._capture_screenshot(screenshot_filename)

        if not capture_result["success"]:
            return {"success": False, "message": capture_result["message"], "text": ""}

        image_path = capture_result["filepath"]
        ocr_result = self._perform_ocr(image_path)

        self._cleanup_screenshot(image_path)  # Clean up regardless of OCR success

        return {
            "success": ocr_result["success"],
            "message": f"Full screen text reading: {ocr_result['message']}",
            "text": ocr_result["text"]
        }

    def read_specific_area_text(self, x: int, y: int, width: int, height: int) -> Dict[str, Any]:
        """
        Reads text from a specific rectangular area of the screen.

        This method captures a screenshot of a defined region and then uses
        Tesseract OCR to extract text.

        Args:
            x: The x-coordinate of the top-left corner of the area.
            y: The y-coordinate of the top-left corner of the area.
            width: The width of the area.
            height: The height of the area.

        Returns:
            A dictionary with 'success' (bool), 'message' (str), and 'text' (str).
        """
        # Input Validation
        if not all(isinstance(arg, int) for arg in [x, y, width, height]):
            return {"success": False, "message": "Input coordinates and dimensions (x, y, width, height) must be integers.", "text": ""}
        if width <= 0 or height <= 0:
            return {"success": False, "message": "Width and height must be positive integers.", "text": ""}
        # Basic check for coordinates, though 'screencapture' might handle out-of-bounds gracefully.
        # More sophisticated screen resolution checks could be added if necessary.
        if x < 0 or y < 0:
             logging.warning("Negative coordinates provided for screen area capture. This might lead to unexpected results.")


        area_tuple = (x, y, width, height)
        screenshot_filename = f"area_{x}_{y}_{width}_{height}.png"
        capture_result = self._capture_screenshot(screenshot_filename, area=area_tuple)

        if not capture_result["success"]:
            return {"success": False, "message": capture_result["message"], "text": ""}

        image_path = capture_result["filepath"]
        ocr_result = self._perform_ocr(image_path)

        self._cleanup_screenshot(image_path)  # Clean up regardless of OCR success

        return {
            "success": ocr_result["success"],
            "message": f"Specific area text reading: {ocr_result['message']}",
            "text": ocr_result["text"]
        }


if __name__ == "__main__":
    # Example Usage
    # Ensure you have installed the dependencies:
    # pip install pytesseract Pillow
    # On macOS, install Tesseract with: brew install tesseract

    print("--- Screen Text Reader Tool Example ---")

    reader = ScreenTextReader()

    # --- Example 1: Read text from the full screen ---
    print("\n--- Attempting to read text from the full screen ---")
    full_screen_result = reader.read_full_screen_text()
    if full_screen_result["success"]:
        print("Successfully read text from the full screen:")
        print("---------------------------------------------")
        print(full_screen_result["text"])
        print("---------------------------------------------")
    else:
        print(f"Error reading full screen text: {full_screen_result['message']}")
        print("Please ensure Tesseract is installed and in your PATH, or configure pytesseract.tesseract_cmd.")

    # --- Example 2: Read text from a specific area ---
    # IMPORTANT: Adjust these coordinates to an area on your screen that contains text.
    # If the specified area is empty or contains no readable text, the result will be an empty string.
    print("\n--- Attempting to read text from a specific area ---")
    # Example coordinates for a region (e.g., top-left, 300 pixels wide, 150 pixels high)
    # You might need to experiment to find suitable coordinates for your screen.
    area_x, area_y, area_width, area_height = 100, 100, 400, 200
    print(f"Targeting area: x={area_x}, y={area_y}, width={area_width}, height={area_height}")
    specific_area_result = reader.read_specific_area_text(area_x, area_y, area_width, area_height)

    if specific_area_result["success"]:
        print(f"Successfully read text from the specific area:")
        print("---------------------------------------------")
        print(specific_area_result["text"])
        print("---------------------------------------------")
    else:
        print(f"Error reading specific area text: {specific_area_result['message']}")

    # --- Example 3: Input Validation ---
    print("\n--- Testing input validation for specific area ---")
    print("Attempting to read text with invalid dimensions (negative width)...")
    invalid_area_result_negative = reader.read_specific_area_text(100, 100, -50, 100)
    if not invalid_area_result_negative["success"]:
        print(f"Correctly handled invalid input (negative width): {invalid_area_result_negative['message']}")

    print("\nAttempting to read text with non-integer coordinates...")
    invalid_area_result_type = reader.read_specific_area_text(100.5, 100, 50, 100)
    if not invalid_area_result_type["success"]:
        print(f"Correctly handled invalid input (non-integer coordinate): {invalid_area_result_type['message']}")

    print("\n--- Screen Text Reader Tool Example Finished ---")
