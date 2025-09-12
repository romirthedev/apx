
import datetime
import logging
import platform
import subprocess
import os
from typing import Dict, Any, Optional, List

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define a common temporary directory for screenshots
TEMP_DIR = os.path.join(os.path.expanduser("~"), "tmp_screen_ocr")
os.makedirs(TEMP_DIR, exist_ok=True)

class ScreenTextReader:
    """
    A specialized tool class for reading screen text on macOS.

    This class captures screenshots and, crucially, integrates with external OCR
    capabilities. It relies on AppleScript for screen capture and then delegates
    text recognition to a specified OCR engine. The default implementation
    assumes `tesseract` is installed and available in the system's PATH.
    """

    def __init__(self, ocr_engine_command: List[str] = ["tesseract", "-", "stdout"]) -> None:
        """
        Initializes the ScreenTextReader.

        Args:
            ocr_engine_command: A list representing the command and arguments
                                to execute the OCR engine. The placeholder '-'
                                is expected to be replaced by the path to the
                                captured image file, and 'stdout' indicates
                                that the output should be directed to standard output.
                                For example: ["tesseract", "-", "stdout"] for Tesseract.
                                Defaults to Tesseract.
        """
        if platform.system() != "Darwin":
            logging.warning("ScreenTextReader is primarily designed for macOS. Functionality might be limited or unavailable on other OS.")
            self.is_macos = False
        else:
            self.is_macos = True

        self.ocr_engine_command = ocr_engine_command
        self._check_ocr_engine_availability()
        logging.info("ScreenTextReader initialized.")

    def _check_ocr_engine_availability(self) -> None:
        """
        Checks if the configured OCR engine command is executable.
        """
        if not self.is_macos:
            logging.warning("Skipping OCR engine availability check as the OS is not macOS.")
            return

        try:
            # Create a dummy image file for testing OCR.
            dummy_image_path = os.path.join(TEMP_DIR, "dummy_test.png")
            # Using 'convert' from ImageMagick to create a simple image with text.
            # If ImageMagick is not installed, this check might fail or require
            # an alternative way to create a test image or just skip the check.
            # For now, we assume a basic image can be created or the user handles it.
            # A more robust check would involve creating a minimal PNG programmatically.

            # Simple check: attempt to run the command with a placeholder.
            # We replace '-' with a dummy path or stdin indicator if the command expects it.
            command_to_check = list(self.ocr_engine_command)
            try:
                first_arg_index = command_to_check.index("-") if "-" in command_to_check else -1
                if first_arg_index != -1:
                    # If '-' is present, it's likely expecting an input file.
                    # We'll try to run it without a real file, but with an argument that indicates stdin.
                    # This part is tricky as different OCR tools handle stdin differently.
                    # For Tesseract, '-' usually means stdin.
                    # Let's try to see if the command itself is found.
                    command_to_check[first_arg_index] = "/dev/null" # Placeholder for input

                subprocess.run(command_to_check, capture_output=True, text=True, check=True, timeout=10)
                logging.info(f"OCR engine '{' '.join(command_to_check)}' appears to be available.")
            except FileNotFoundError:
                logging.error(f"OCR engine command not found: '{command_to_check[0]}'. Please ensure it's installed and in your PATH.")
                raise
            except subprocess.CalledProcessError as e:
                logging.warning(f"OCR engine command '{' '.join(command_to_check)}' failed during availability check. Output: {e.stdout}, Error: {e.stderr}")
                logging.warning("This might indicate an issue with the OCR setup or the command arguments. Text extraction may fail.")
            except subprocess.TimeoutExpired:
                logging.warning(f"Timeout checking OCR engine '{' '.join(command_to_check)}'. Text extraction may fail.")
            except Exception as e:
                logging.error(f"An unexpected error occurred while checking OCR engine availability: {e}")
                raise

        except Exception as e:
            logging.error(f"Failed to initialize OCR engine check: {e}")
            # Depending on criticality, you might want to raise here or allow operation with a warning.
            # For now, we allow operation with a warning.


    def _run_applescript(self, script: str) -> subprocess.CompletedProcess:
        """
        Executes an AppleScript command and returns the result.

        Args:
            script: The AppleScript command as a string.

        Returns:
            A subprocess.CompletedProcess object containing the stdout, stderr,
            and returncode of the executed script.

        Raises:
            FileNotFoundError: If osascript command is not found.
            subprocess.TimeoutExpired: If the script execution times out.
            Exception: For other unexpected errors.
        """
        try:
            process = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                check=False,  # Don't raise an exception for non-zero exit codes
                timeout=30  # Set a reasonable timeout
            )
            return process
        except FileNotFoundError:
            logging.error("osascript command not found. Ensure AppleScript is available on your system.")
            raise
        except subprocess.TimeoutExpired:
            logging.error("AppleScript execution timed out.")
            raise
        except Exception as e:
            logging.error(f"An unexpected error occurred while running AppleScript: {e}")
            raise

    def _run_ocr_engine(self, image_path: str) -> Dict[str, Any]:
        """
        Executes the configured OCR engine command on the given image file.

        Args:
            image_path: The path to the image file to process.

        Returns:
            A dictionary containing the OCR result:
            - 'success': True if OCR was successful, False otherwise.
            - 'text': The extracted text (str) if successful, None otherwise.
            - 'message': A descriptive message about the OCR outcome.
        """
        if not self.is_macos:
            return {
                "success": False,
                "text": None,
                "message": "OCR functionality is only supported on macOS for this tool."
            }

        if not os.path.exists(image_path):
            return {
                "success": False,
                "text": None,
                "message": f"OCR error: Image file not found at {image_path}."
            }

        command = list(self.ocr_engine_command)
        try:
            # Replace placeholder for input file path.
            # This assumes the OCR command uses '-' to signify stdin for the input image file.
            # If your OCR tool uses a different placeholder or expects the file path directly,
            # you'll need to adjust this logic.
            try:
                input_placeholder_index = command.index("-")
                command[input_placeholder_index] = image_path
            except ValueError:
                # If '-' is not in the command, assume it expects the file path as the last argument or it's implicitly handled.
                # This is a common convention for many CLI tools.
                command.append(image_path)

            logging.info(f"Running OCR command: {' '.join(command)}")
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                timeout=60 # Increased timeout for OCR processing
            )

            if process.returncode == 0:
                extracted_text = process.stdout.strip()
                if not extracted_text:
                    return {
                        "success": True, # OCR ran, but no text found is still a success of the OCR process
                        "text": "",
                        "message": "OCR completed. No text was detected in the image."
                    }
                return {
                    "success": True,
                    "text": extracted_text,
                    "message": "Text extracted successfully by OCR engine."
                }
            else:
                error_message = f"OCR engine failed with return code {process.returncode}. Stderr: {process.stderr.strip()}. Stdout: {process.stdout.strip()}"
                logging.error(error_message)
                return {
                    "success": False,
                    "text": None,
                    "message": error_message
                }
        except FileNotFoundError:
            return {
                "success": False,
                "text": None,
                "message": f"OCR engine command not found: '{command[0]}'. Please ensure it is installed and in your system's PATH."
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "text": None,
                "message": f"OCR engine execution timed out after 60 seconds."
            }
        except Exception as e:
            logging.error(f"An unexpected error occurred during OCR execution: {e}")
            return {
                "success": False,
                "text": None,
                "message": f"An unexpected error occurred during OCR: {str(e)}"
            }

    def _capture_screenshot(self, crop_rect: Optional[tuple[int, int, int, int]] = None) -> tuple[str, datetime.datetime | None]:
        """
        Captures a screenshot (full screen or specific area) and saves it to a temporary file.

        Args:
            crop_rect: An optional tuple (x, y, width, height) for capturing a specific area.

        Returns:
            A tuple containing:
            - The path to the saved screenshot file (str).
            - The timestamp of the capture (datetime or None if failed).
            Returns (None, None) if capture fails.
        """
        timestamp = datetime.datetime.now()
        unique_id = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{os.getpid()}"
        image_filename = f"screenshot_{unique_id}.png"
        image_path = os.path.join(TEMP_DIR, image_filename)

        try:
            if crop_rect:
                x, y, width, height = crop_rect
                # Validate crop_rect coordinates
                if not all(isinstance(arg, int) and arg >= 0 for arg in [x, y, width, height]):
                    raise ValueError("Invalid input: x, y, width, and height must be non-negative integers.")
                
                # AppleScript command to capture a specific area
                applescript_command = f"""
                try
                    set imageFile to "{image_path}"
                    -- Use '-crop x,y,width,height' for screencapture
                    do shell script "screencapture -crop {x},{y},{width},{height} " & quoted form of imageFile
                    return "SUCCESS: Screenshot of area captured to " & imageFile
                on error errMsg number errNum
                    if errNum is -128 then return "CANCELLED: Screenshot operation cancelled by user."
                    if errNum is -1700 then return "ERROR: Scripting error: " & errMsg
                    if errNum is -1743 then return "ERROR: Permission denied. Please grant Screen Recording permissions to your terminal application."
                    if errMsg contains "command not found: screencapture" then return "ERROR: 'screencapture' command not found. Ensure it's accessible."
                    return "ERROR: An unexpected error occurred: " & errMsg & " (Error number: " & errNum & ")"
                end try
                """
            else:
                # AppleScript command to capture the entire screen
                applescript_command = f"""
                try
                    set imageFile to "{image_path}"
                    do shell script "screencapture " & quoted form of imageFile
                    return "SUCCESS: Full screen screenshot captured to " & imageFile
                on error errMsg number errNum
                    if errNum is -128 then return "CANCELLED: Screenshot operation cancelled by user."
                    if errNum is -1700 then return "ERROR: Scripting error: " & errMsg
                    if errNum is -1743 then return "ERROR: Permission denied. Please grant Screen Recording permissions to your terminal application."
                    return "ERROR: An unexpected error occurred: " & errMsg & " (Error number: " & errNum & ")"
                end try
                """

            process = self._run_applescript(applescript_command)
            stdout = process.stdout.strip()
            stderr = process.stderr.strip()

            if process.returncode == 0:
                if "SUCCESS:" in stdout:
                    logging.info(f"Screenshot saved to: {image_path}")
                    return image_path, timestamp
                elif "CANCELLED" in stdout:
                    logging.warning("Screenshot operation cancelled by user.")
                    return None, timestamp # Return timestamp even if cancelled for consistency
                else:
                    logging.error(f"AppleScript reported success but with unexpected output: {stdout}. Stderr: {stderr}")
                    return None, timestamp
            else:
                logging.error(f"AppleScript execution failed during screenshot. Stderr: {stderr}. Stdout: {stdout}")
                return None, timestamp
        except (FileNotFoundError, subprocess.TimeoutExpired, ValueError) as e:
            logging.error(f"Error during screenshot capture: {e}")
            return None, timestamp
        except Exception as e:
            logging.error(f"An unexpected error occurred during screenshot capture: {e}")
            return None, timestamp

    def read_full_screen_text(self) -> Dict[str, Any]:
        """
        Captures the entire screen, attempts to recognize text using the configured OCR engine, and returns the result.

        Returns:
            A dictionary containing the operation result:
            - 'success': True if text was successfully extracted, False otherwise.
            - 'message': A descriptive message about the operation's outcome.
            - 'text': The extracted text (str) if successful, None otherwise.
            - 'timestamp': The datetime when the screenshot was taken.
        """
        if not self.is_macos:
            return {
                "success": False,
                "message": "This feature is only supported on macOS.",
                "text": None,
                "timestamp": None
            }

        image_path, timestamp = self._capture_screenshot()

        if image_path is None:
            return {
                "success": False,
                "message": "Failed to capture screenshot.",
                "text": None,
                "timestamp": timestamp
            }

        ocr_result = self._run_ocr_engine(image_path)
        
        # Clean up the temporary screenshot file
        try:
            os.remove(image_path)
            logging.info(f"Removed temporary screenshot file: {image_path}")
        except OSError as e:
            logging.warning(f"Could not remove temporary screenshot file {image_path}: {e}")

        return {
            "success": ocr_result["success"],
            "message": f"Screenshot captured and processed. {ocr_result['message']}",
            "text": ocr_result["text"],
            "timestamp": timestamp
        }

    def read_specific_area_text(self, x: int, y: int, width: int, height: int) -> Dict[str, Any]:
        """
        Captures a specific area of the screen, attempts to recognize text using the configured OCR engine, and returns the result.

        Args:
            x: The x-coordinate of the top-left corner of the area.
            y: The y-coordinate of the top-left corner of the area.
            width: The width of the area.
            height: The height of the area.

        Returns:
            A dictionary containing the operation result:
            - 'success': True if text was successfully extracted, False otherwise.
            - 'message': A descriptive message about the operation's outcome.
            - 'text': The extracted text (str) if successful, None otherwise.
            - 'timestamp': The datetime when the screenshot was taken.
        """
        if not self.is_macos:
            return {
                "success": False,
                "message": "This feature is only supported on macOS.",
                "text": None,
                "timestamp": None
            }

        try:
            crop_rect = (x, y, width, height)
            image_path, timestamp = self._capture_screenshot(crop_rect=crop_rect)
        except ValueError as e: # Catch validation errors from _capture_screenshot
            return {
                "success": False,
                "message": f"Input validation error: {e}",
                "text": None,
                "timestamp": None
            }

        if image_path is None:
            return {
                "success": False,
                "message": "Failed to capture screenshot of the specified area.",
                "text": None,
                "timestamp": timestamp
            }

        ocr_result = self._run_ocr_engine(image_path)

        # Clean up the temporary screenshot file
        try:
            os.remove(image_path)
            logging.info(f"Removed temporary screenshot file: {image_path}")
        except OSError as e:
            logging.warning(f"Could not remove temporary screenshot file {image_path}: {e}")

        return {
            "success": ocr_result["success"],
            "message": f"Screenshot of area captured and processed. {ocr_result['message']}",
            "text": ocr_result["text"],
            "timestamp": timestamp
        }

    def cleanup_temp_files(self) -> None:
        """
        Removes all temporary screenshot files created by this tool.
        """
        logging.info(f"Cleaning up temporary directory: {TEMP_DIR}")
        try:
            for filename in os.listdir(TEMP_DIR):
                file_path = os.path.join(TEMP_DIR, filename)
                if os.path.isfile(file_path) and "screenshot_" in filename:
                    try:
                        os.remove(file_path)
                        logging.info(f"Removed: {file_path}")
                    except OSError as e:
                        logging.warning(f"Could not remove file {file_path}: {e}")
            logging.info("Temporary file cleanup complete.")
        except Exception as e:
            logging.error(f"Error during temporary file cleanup: {e}")


if __name__ == '__main__':
    # Example usage:
    print("--- Testing ScreenTextReader ---")

    # Initialize with default Tesseract command (ensure tesseract is installed)
    # If you have a different OCR engine or a specific command, provide it:
    # reader = ScreenTextReader(ocr_engine_command=["/path/to/your/ocr", "-i", "-", "-o", "stdout"])
    try:
        reader = ScreenTextReader()
    except Exception as e:
        print(f"Failed to initialize ScreenTextReader: {e}")
        print("Please ensure 'osascript' is available and your OCR engine (default: tesseract) is installed and in PATH.")
        exit(1)


    # Test reading full screen
    print("\nReading full screen...")
    result_full = reader.read_full_screen_text()
    print(f"Result: {result_full}")

    # Test reading specific area (example: a 200x100 area at 100,150)
    # Note: You might need to adjust these coordinates based on your screen setup.
    # Ensure the area is visible and contains text.
    print("\nReading specific area (x=100, y=150, width=200, height=100)...")
    result_area = reader.read_specific_area_text(x=100, y=150, width=200, height=100)
    print(f"Result: {result_area}")

    # Test with invalid input for specific area
    print("\nTesting with invalid input for specific area (negative x)...")
    result_invalid = reader.read_specific_area_text(x=-10, y=100, width=200, height=100)
    print(f"Result: {result_invalid}")

    print("\nTesting with invalid input for specific area (non-integer width)...")
    result_invalid_type = reader.read_specific_area_text(x=10, y=100, width=200.5, height=100)
    print(f"Result: {result_invalid_type}")


    # If running on a non-macOS system, the initial warning will be logged.
    # The functions will also return a "not supported" message.
    if platform.system() != "Darwin":
        print("\n--- Testing on non-macOS (simulated) ---")
        # Re-initialize to simulate the warning for non-mac
        try:
            non_mac_reader = ScreenTextReader()
            result_full_non_mac = non_mac_reader.read_full_screen_text()
            print(f"Full screen read result (non-mac): {result_full_non_mac}")
            result_area_non_mac = non_mac_reader.read_specific_area_text(10, 10, 100, 50)
            print(f"Specific area read result (non-mac): {result_area_non_mac}")
        except Exception as e:
            print(f"Failed to initialize ScreenTextReader on non-mac: {e}")

    # Clean up any leftover temporary files
    print("\nRunning cleanup...")
    reader.cleanup_temp_files()
    print("--- Test Complete ---")
