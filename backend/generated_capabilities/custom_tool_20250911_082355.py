
import os
import subprocess
import tempfile
import shutil
from typing import Dict, Any, Optional

class ScreenReader:
    """
    A specialized tool for reading text from the screen on macOS.

    This class leverages macOS's built-in accessibility features and command-line
    tools, along with external OCR engines like Tesseract, to capture and
    extract text from the screen.

    It offers two primary methods:
    1. `read_frontmost_window_text`: Retrieves accessible text from the
       currently active application window. This is not true OCR and relies
       on the application's accessibility support.
    2. `capture_and_ocr_screen_area`: Captures a specified region (or the
       entire screen) as an image and then uses an OCR engine (Tesseract)
       to extract text from that image. This is a more robust solution for
       reading arbitrary screen text but requires Tesseract to be installed.
    """

    def __init__(self):
        """
        Initializes the ScreenReader and checks for necessary dependencies.

        Raises:
            RuntimeError: If required macOS tools (osascript, screencapture,
                          pbpaste, pbcopy) are not found.
        """
        self._check_macos_dependencies()

    def _execute_command(self, command: list[str], use_shell: bool = False) -> Dict[str, Any]:
        """
        Executes a shell command and returns structured output.

        Args:
            command: A list of strings representing the command and its arguments.
            use_shell: If True, the command will be executed through the shell.

        Returns:
            A dictionary containing:
                - 'success' (bool): True if the command executed successfully, False otherwise.
                - 'message' (str): A descriptive message about the execution outcome.
                - 'stdout' (str): The standard output of the command.
                - 'stderr' (str): The standard error of the command.
        """
        try:
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,  # Don't raise exception on non-zero exit code
                shell=use_shell
            )
            if process.returncode == 0:
                return {
                    "success": True,
                    "message": "Command executed successfully.",
                    "stdout": process.stdout.strip(),
                    "stderr": process.stderr.strip(),
                }
            else:
                return {
                    "success": False,
                    "message": f"Command failed with exit code {process.returncode}.",
                    "stdout": process.stdout.strip(),
                    "stderr": process.stderr.strip(),
                }
        except FileNotFoundError:
            return {
                "success": False,
                "message": f"Error: Command '{command[0]}' not found. Please ensure it's installed and in your PATH.",
                "stdout": "",
                "stderr": "",
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"An unexpected error occurred while executing command: {e}",
                "stdout": "",
                "stderr": "",
            }

    def _check_macos_dependencies(self) -> None:
        """
        Checks for necessary macOS command-line tools required by the ScreenReader.

        Raises:
            RuntimeError: If required tools are not found.
        """
        required_tools = ["osascript", "screencapture", "pbpaste", "pbcopy"]
        for tool in required_tools:
            check_result = self._execute_command(["which", tool])
            if not check_result["success"]:
                raise RuntimeError(
                    f"Required tool '{tool}' not found. This tool requires macOS "
                    f"and its associated command-line utilities. Please ensure your "
                    f"environment is correctly set up."
                )

    def _check_ocr_dependency(self) -> Dict[str, Any]:
        """
        Checks if the Tesseract OCR engine is installed and available.

        Returns:
            A dictionary with the result of the check.
        """
        tesseract_check = self._execute_command(["which", "tesseract"])
        if not tesseract_check["success"]:
            return {
                "success": False,
                "message": "Tesseract OCR engine not found. For screen area OCR, please install Tesseract (e.g., via Homebrew: 'brew install tesseract').",
                "text": None,
            }
        return {"success": True, "message": "Tesseract found."}

    def _validate_coordinates(self, x: int, y: int, width: Optional[int], height: Optional[int]) -> Dict[str, Any]:
        """
        Validates the provided coordinates and dimensions for screen capture.

        Args:
            x: The x-coordinate of the top-left corner.
            y: The y-coordinate of the top-left corner.
            width: The width of the capture region.
            height: The height of the capture region.

        Returns:
            A dictionary containing 'success' (bool) and 'message' (str).
        """
        if not isinstance(x, int) or not isinstance(y, int):
            return {"success": False, "message": "x and y coordinates must be integers."}
        if width is not None and not isinstance(width, int):
            return {"success": False, "message": "Width must be an integer or None."}
        if height is not None and not isinstance(height, int):
            return {"success": False, "message": "Height must be an integer or None."}

        if width is not None and width <= 0:
            return {"success": False, "message": "Width must be a positive integer."}
        if height is not None and height <= 0:
            return {"success": False, "message": "Height must be a positive integer."}
        if x < 0 or y < 0:
            return {"success": False, "message": "x and y coordinates cannot be negative."}

        # Further validation could involve checking against screen dimensions,
        # but that requires platform-specific API calls or external tools not assumed here.
        # For now, we rely on screencapture to handle out-of-bounds requests gracefully.

        return {"success": True, "message": "Coordinates are valid."}

    def read_frontmost_window_text(self) -> Dict[str, Any]:
        """
        Reads accessible text from the frontmost application window using AppleScript.

        This method attempts to retrieve the text content of the currently active
        application window. Its success depends on the application and its
        accessibility support. This is NOT a full screen OCR solution.

        Returns:
            A dictionary with the following keys:
                - 'success' (bool): True if text was successfully retrieved, False otherwise.
                - 'message' (str): A descriptive message about the operation.
                - 'text' (Optional[str]): The extracted text from the window, or None if unsuccessful.
        """
        script = """
        tell application "System Events"
            if exists (first process whose frontmost is true) then
                set frontProcess to first process whose frontmost is true
                tell frontProcess
                    if exists (window 1) then
                        set win to window 1
                        -- Try to get text from various common accessibility attributes
                        -- Order matters: try more specific elements first
                        if (exists attribute "AXValue" of UI element 1 of win) then
                            return value of attribute "AXValue" of UI element 1 of win
                        else if (exists text area 1 of win) then
                            return value of attribute "AXValue" of text area 1 of win
                        else if (exists static text 1 of win) then
                            return value of attribute "AXValue" of static text 1 of win
                        else if (exists text of win) then
                            return text of win
                        else
                            return "No readily accessible text elements found in the frontmost window."
                        end if
                    else
                        return "No window found for the frontmost application."
                    end if
                end tell
            else
                return "No frontmost application found."
            end if
        end tell
        """
        result = self._execute_command(["osascript", "-e", script])

        if result["success"]:
            # AppleScript might return specific error strings if it can't find elements.
            # We need to differentiate between successful retrieval and an informative error message.
            error_messages = [
                "No readily accessible text elements found in the frontmost window.",
                "No window found for the frontmost application.",
                "No frontmost application found."
            ]
            if any(err in result["stdout"] for err in error_messages):
                return {
                    "success": False,
                    "message": f"Failed to retrieve text from frontmost window: {result['stdout']}",
                    "text": None,
                }
            else:
                # Handle cases where the script might have returned an empty string intentionally
                # or as a result of no text being present.
                return {
                    "success": True,
                    "message": "Successfully retrieved text from frontmost window.",
                    "text": result["stdout"] if result["stdout"] else "",
                }
        else:
            return {
                "success": False,
                "message": f"Error executing osascript command: {result['stderr']}",
                "text": None,
            }

    def capture_and_ocr_screen_area(
        self,
        x: int = 0,
        y: int = 0,
        width: Optional[int] = None,
        height: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Captures a specified area of the screen as an image and performs OCR on it.

        This method first checks for the Tesseract OCR engine. If available, it
        captures the specified screen region using `screencapture` and saves it
        to a temporary file. Then, it uses Tesseract to extract text from this
        image file.

        Args:
            x: The x-coordinate of the top-left corner of the capture region.
               Defaults to 0.
            y: The y-coordinate of the top-left corner of the capture region.
               Defaults to 0.
            width: The width of the capture region. If None, captures the full
                   screen width.
            height: The height of the capture region. If None, captures the full
                    screen height.

        Returns:
            A dictionary with the following keys:
                - 'success' (bool): True if text was successfully retrieved, False otherwise.
                - 'message' (str): A descriptive message about the operation.
                - 'text' (Optional[str]): The extracted text from the screen, or None if unsuccessful.
        """
        validation_result = self._validate_coordinates(x, y, width, height)
        if not validation_result["success"]:
            return {"success": False, "message": validation_result["message"], "text": None}

        ocr_dependency_check = self._check_ocr_dependency()
        if not ocr_dependency_check["success"]:
            return {
                "success": False,
                "message": ocr_dependency_check["message"],
                "text": None,
            }

        temp_dir = None
        try:
            temp_dir = tempfile.mkdtemp()
            image_filename = "screencapture.png"
            image_path = os.path.join(temp_dir, image_filename)

            # Construct the screencapture command
            screencapture_command = ["screencapture"]
            if width is not None and height is not None:
                # Use -R for rectangular region: x,y,width,height
                screencapture_command.extend(["-R", f"{x},{y},{width},{height}"])
            else:
                # Capture entire screen. -x disables sound feedback.
                screencapture_command.append("-x")

            screencapture_command.append(image_path) # Save to file

            # Execute screencapture to save the image
            capture_result = self._execute_command(screencapture_command)
            if not capture_result["success"]:
                return {
                    "success": False,
                    "message": f"Failed to capture screen area to image file. screencapture error: {capture_result['stderr']}",
                    "text": None,
                }

            # Execute Tesseract OCR on the captured image
            # Command: tesseract input_image_path output_base_path
            # 'stdout' as output_base_path redirects output to stdout.
            ocr_command = ["tesseract", image_path, "stdout"]
            ocr_result = self._execute_command(ocr_command)

            if ocr_result["success"]:
                return {
                    "success": True,
                    "message": "Successfully captured screen area and performed OCR.",
                    "text": ocr_result["stdout"],
                }
            else:
                return {
                    "success": False,
                    "message": f"OCR failed. Tesseract error: {ocr_result['stderr']}",
                    "text": None,
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"An unexpected error occurred during screen capture and OCR process: {e}",
                "text": None,
            }
        finally:
            # Clean up the temporary directory
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except OSError as e:
                    print(f"Warning: Could not remove temporary directory {temp_dir}: {e}")


# Example Usage (for testing purposes, not part of the module export)
if __name__ == "__main__":
    print("--- ScreenReader Tool Test ---")

    try:
        reader = ScreenReader()
        print("ScreenReader initialized successfully.")
    except RuntimeError as e:
        print(f"Initialization failed: {e}")
        exit(1)

    # --- Test 1: Reading frontmost window text ---
    print("\n--- Testing read_frontmost_window_text ---")
    print("Please ensure an application with visible text is frontmost (e.g., a text editor, browser window).")
    input("Press Enter to attempt reading text from the frontmost window...")

    frontmost_result = reader.read_frontmost_window_text()
    print(f"Success: {frontmost_result['success']}")
    print(f"Message: {frontmost_result['message']}")
    if frontmost_result["text"]:
        print("Text Found (first 500 chars):")
        print(frontmost_result["text"][:500] + "..." if len(frontmost_result["text"]) > 500 else frontmost_result["text"])
    elif frontmost_result["success"]:
        print("No text was found or extracted by the accessibility features.")

    # --- Test 2: Capturing and OCRing a screen area ---
    print("\n--- Testing capture_and_ocr_screen_area ---")
    print("This test requires Tesseract OCR to be installed.")
    print("It will attempt to capture a small area near the top-left corner of your screen.")
    print("Ensure there is clear text in the capture region.")

    # Define capture area: adjust x, y, width, height as needed for testing.
    # For example, to capture a typical menu bar or a specific UI element.
    test_x, test_y, test_width, test_height = 10, 10, 600, 300
    print(f"Attempting to capture area: x={test_x}, y={test_y}, width={test_width}, height={test_height}")
    input("Press Enter to perform OCR on the specified screen area...")

    ocr_result = reader.capture_and_ocr_screen_area(x=test_x, y=test_y, width=test_width, height=test_height)
    print(f"Success: {ocr_result['success']}")
    print(f"Message: {ocr_result['message']}")
    if ocr_result["text"]:
        print("OCR Text Found:")
        print(ocr_result["text"])
    elif ocr_result["success"]:
        print("OCR operation completed, but no text was detected in the captured area.")

    # --- Test 3: Full screen OCR ---
    print("\n--- Testing full screen OCR ---")
    print("This test captures the entire screen and performs OCR.")
    print("This may take a moment and could capture sensitive information if present.")
    input("Press Enter to proceed with full screen OCR...")

    full_screen_ocr_result = reader.capture_and_ocr_screen_area(width=None, height=None)
    print(f"Success: {full_screen_ocr_result['success']}")
    print(f"Message: {full_screen_ocr_result['message']}")
    if full_screen_ocr_result["text"]:
        print("Full Screen OCR Text Found (first 1000 chars):")
        print(full_screen_ocr_result["text"][:1000] + "..." if len(full_screen_ocr_result["text"]) > 1000 else full_screen_ocr_result["text"])
    elif full_screen_ocr_result["success"]:
        print("OCR operation completed for the full screen, but no text was detected.")

    # --- Test 4: Invalid Input Validation ---
    print("\n--- Testing Input Validation ---")
    print("Testing with invalid coordinates (negative width)...")
    invalid_input_result = reader.capture_and_ocr_screen_area(x=0, y=0, width=-100, height=100)
    print(f"Success: {invalid_input_result['success']}")
    print(f"Message: {invalid_input_result['message']}")

    print("Testing with invalid coordinates (non-integer height)...")
    invalid_input_result_2 = reader.capture_and_ocr_screen_area(x=0, y=0, width=100, height="abc")
    print(f"Success: {invalid_input_result_2['success']}")
    print(f"Message: {invalid_input_result_2['message']}")
