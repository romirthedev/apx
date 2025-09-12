
import subprocess
import json
import os
import tempfile
from typing import Dict, Any, Optional, Tuple

class ScreenReader:
    """
    A specialized Python tool class for reading text from the screen.
    This class leverages external command-line utilities for screen capture
    and OCR (Optical Character Recognition) to extract text from screenshots.

    Currently supports macOS via 'screencapture' and Tesseract OCR.
    Cross-platform support would require platform-specific capture tools.
    """

    def __init__(self):
        """
        Initializes the ScreenReader.
        Ensures that necessary command-line tools (screencapture and tesseract)
        are available. Raises an EnvironmentError if dependencies are missing.
        """
        self._check_dependencies()

    def _run_command(self, command: list[str], capture_output: bool = True, check_returncode: bool = True) -> Dict[str, Any]:
        """
        Executes a shell command and returns its output and status.

        Args:
            command: A list of strings representing the command and its arguments.
            capture_output: If True, capture stdout and stderr.
            check_returncode: If True, raise an exception for non-zero return codes.

        Returns:
            A dictionary with 'success' (bool), 'message' (str), and optionally
            'stdout' (str) and 'stderr' (str).
        """
        try:
            process_kwargs = {
                "stdout": subprocess.PIPE if capture_output else None,
                "stderr": subprocess.PIPE if capture_output else None,
                "text": True,
            }
            process = subprocess.Popen(command, **process_kwargs)

            if capture_output:
                stdout, stderr = process.communicate()
                if process.returncode != 0 and check_returncode:
                    return {"success": False, "message": f"Command failed: {stderr.strip()}", "stderr": stderr}
                return {"success": True, "message": "Command executed successfully.", "stdout": stdout, "stderr": stderr}
            else:
                process.wait() # Wait for the command to complete if not capturing output
                if process.returncode != 0 and check_returncode:
                    # Attempt to get stderr if it wasn't captured initially and an error occurred
                    # This is a fallback and might not always work if stderr was not piped.
                    return {"success": False, "message": f"Command failed with return code {process.returncode}"}
                return {"success": True, "message": "Command executed successfully."}

        except FileNotFoundError:
            return {"success": False, "message": f"Command not found: '{command[0]}'. Please ensure it is installed and in your PATH."}
        except Exception as e:
            return {"success": False, "message": f"An unexpected error occurred while running command '{' '.join(command)}': {str(e)}"}

    def _check_dependencies(self):
        """
        Checks if the required command-line tools (screencapture and tesseract)
        are available on the system. Raises an EnvironmentError if not found.
        """
        screencapture_check = self._run_command(["which", "screencapture"])
        if not screencapture_check["success"]:
            raise EnvironmentError(
                "System dependency 'screencapture' not found. "
                "This tool requires macOS and the built-in 'screencapture' utility. "
                "Please ensure you are on a macOS system."
            )

        tesseract_check = self._run_command(["which", "tesseract"])
        if not tesseract_check["success"]:
            raise EnvironmentError(
                "System dependency 'tesseract' not found. "
                "Please install Tesseract OCR. On macOS with Homebrew, run: 'brew install tesseract'"
            )

        # Check if tesseract has English language data
        lang_check = self._run_command(["tesseract", "--list-langs"])
        if lang_check["success"]:
            available_langs = lang_check.get("stdout", "").splitlines()
            if "eng" not in available_langs:
                print("Warning: Tesseract may not have English language data ('eng'). OCR accuracy might be affected.")
                print("You can install it by running 'brew install tesseract-lang' (macOS with Homebrew) or consult Tesseract documentation for your OS.")
        else:
            print(f"Warning: Could not list Tesseract languages. OCR might fail. Tesseract error: {lang_check.get('message')}")

    def _validate_region(self, region: Tuple[int, int, int, int]):
        """
        Validates the provided region tuple.

        Args:
            region: A tuple (x, y, width, height).

        Raises:
            ValueError: If the region is invalid.
        """
        if not isinstance(region, tuple) or len(region) != 4:
            raise ValueError("Region must be a tuple of four integers (x, y, width, height).")
        for val in region:
            if not isinstance(val, int):
                raise ValueError("All values in the region tuple must be integers.")
        x, y, w, h = region
        if w <= 0 or h <= 0:
            raise ValueError("Width and height of the region must be positive.")
        if x < 0 or y < 0:
            print(f"Warning: Region starts at negative coordinates (x={x}, y={y}). This might be unintentional.")

    def read_screen_text(self, region: Optional[Tuple[int, int, int, int]] = None) -> Dict[str, Any]:
        """
        Captures a screenshot of the entire screen or a specified region and
        extracts text from it using OCR.

        Args:
            region: An optional tuple (x, y, width, height) defining the capture
                    region. If None, the entire screen is captured.

        Returns:
            A dictionary with 'success' (bool), 'message' (str), and optionally
            'text' (str) containing the extracted text.
        """
        if region:
            try:
                self._validate_region(region)
            except ValueError as e:
                return {"success": False, "message": f"Invalid region provided: {e}"}

        screencapture_cmd = ["screencapture"]
        # The -R option expects x,y,width,height
        if region:
            x, y, w, h = region
            screencapture_cmd.extend(["-R", f"{x},{y},{w},{h}"])

        # Use a temporary file to store the screenshot
        temp_image_file = None
        try:
            # delete=False is important so the file isn't deleted immediately upon closing
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
                image_path = tf.name
                temp_image_file = image_path # Store path for cleanup

            screencapture_cmd.append(image_path)

            # Execute screencapture
            # We don't need to capture stdout/stderr from screencapture itself if it succeeds,
            # as its main output is the file. We only care about its return code.
            capture_result = self._run_command(screencapture_cmd, capture_output=True, check_returncode=True)

            if not capture_result["success"]:
                return {
                    "success": False,
                    "message": f"Failed to capture screen: {capture_result.get('message', 'Unknown error')}",
                    "stdout": capture_result.get("stdout"),
                    "stderr": capture_result.get("stderr")
                }

            # Verify the screenshot file was created and is not empty
            if not os.path.exists(image_path) or os.path.getsize(image_path) == 0:
                return {
                    "success": False,
                    "message": "Screenshot capture resulted in an empty or non-existent file.",
                    "filename": image_path
                }

            # OCR the captured image using Tesseract
            # 'stdout' tells tesseract to output to stdout instead of a file
            # '-l eng' specifies English language
            tesseract_cmd = ["tesseract", image_path, "stdout", "-l", "eng"]
            ocr_result = self._run_command(tesseract_cmd, capture_output=True, check_returncode=True)

            if not ocr_result["success"]:
                return {
                    "success": False,
                    "message": f"OCR failed: {ocr_result.get('message', 'Unknown error')}",
                    "stdout": ocr_result.get("stdout"),
                    "stderr": ocr_result.get("stderr")
                }

            extracted_text = ocr_result.get("stdout", "").strip()
            return {
                "success": True,
                "message": "Screen text successfully extracted.",
                "text": extracted_text
            }

        except Exception as e:
            return {"success": False, "message": f"An unexpected error occurred during screen reading process: {str(e)}"}
        finally:
            # Ensure the temporary image file is cleaned up
            if temp_image_file and os.path.exists(temp_image_file):
                os.remove(temp_image_file)

if __name__ == '__main__':
    # Example Usage
    try:
        reader = ScreenReader()

        # --- Example 1: Read text from the entire screen ---
        print("--- Attempting to read text from the entire screen ---")
        result_full = reader.read_screen_text()
        if result_full["success"]:
            print("\nSuccessfully extracted text from the full screen.")
            print("--- Extracted Text ---")
            print(result_full["text"] if result_full["text"] else "[No text detected]")
            print("--------------------")
        else:
            print(f"Error reading full screen text: {result_full['message']}")
            if "stderr" in result_full:
                print(f"Stderr: {result_full['stderr']}")

        print("\n" + "="*50 + "\n")

        # --- Example 2: Read text from a specific region ---
        # NOTE: To make this truly useful, you would need to know the coordinates
        # of a region containing visible text on your screen.
        # You might need to use a separate tool to find these coordinates.
        # The values (x, y, width, height) are illustrative.
        # For demonstration, we'll try a small arbitrary region.
        # If this region is empty or contains no text, the output will be empty.

        # Example: Coordinates that might capture a small portion of the taskbar or a corner.
        # You would adjust these based on what you want to capture.
        # A common use case might be to capture a specific dialog box or menu.
        sample_region = (100, 100, 300, 150) # x, y, width, height
        print(f"--- Attempting to read text from a specific region: {sample_region} ---")
        print(" (Adjust region coordinates for your specific screen content)")

        result_region = reader.read_screen_text(region=sample_region)
        if result_region["success"]:
            print(f"\nSuccessfully extracted text from region {sample_region}.")
            print("--- Extracted Text ---")
            print(result_region["text"] if result_region["text"] else "[No text detected]")
            print("--------------------")
        else:
            print(f"Error reading region text: {result_region['message']}")
            if "stderr" in result_region:
                print(f"Stderr: {result_region['stderr']}")

        print("\n" + "="*50 + "\n")

        # --- Example 3: Invalid Region Input ---
        print("--- Attempting to read text with an invalid region input ---")
        invalid_region_input = (100, 100, -50, 50) # Negative width
        print(f"Testing with invalid region: {invalid_region_input}")
        result_invalid_region = reader.read_screen_text(region=invalid_region_input)
        if not result_invalid_region["success"]:
            print(f"Correctly caught error for invalid region: {result_invalid_region['message']}")
        else:
            print(f"Did not catch error for invalid region as expected.")


    except EnvironmentError as e:
        print(f"\nEnvironment Setup Error: {e}")
        print("\nPlease ensure that:")
        print("1. You are running this script on a macOS system.")
        print("2. The 'screencapture' command-line utility is available (it's built-in on macOS).")
        print("3. Tesseract OCR is installed. If not, install it using Homebrew: 'brew install tesseract'")
        print("   Also consider installing language packs: 'brew install tesseract-lang'")
    except Exception as e:
        print(f"\nAn unexpected error occurred during script execution: {e}")
