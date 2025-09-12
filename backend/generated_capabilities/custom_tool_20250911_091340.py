
import subprocess
import os
from typing import Dict, Any, Optional

class ScreenReader:
    """
    A specialized tool class for reading text from the screen on macOS.

    This class leverages macOS's built-in accessibility features and command-line
    tools to capture and extract text from the visible screen content.
    It provides functionality to read all screen text or text from a specific window.

    For robust OCR, consider integrating a dedicated OCR library like pytesseract
    along with the Tesseract OCR engine. This implementation relies on AppleScript
    for UI element text extraction, which might not capture all types of text
    (e.g., text within images).
    """

    def __init__(self):
        """
        Initializes the ScreenReader.
        Checks for the availability of 'osascript'.
        """
        self.osascript_available = self._check_osascript()
        if not self.osascript_available:
            print("Warning: 'osascript' command not found. Screen reading functionality will be limited.")

    def _check_osascript(self) -> bool:
        """Checks if the 'osascript' command is available."""
        try:
            subprocess.run(
                ["osascript", "-e", "return true"],
                capture_output=True,
                text=True,
                check=True,
                encoding='utf-8'
            )
            return True
        except FileNotFoundError:
            return False
        except subprocess.CalledProcessError:
            return False

    def _run_applescript(self, script: str) -> Dict[str, Any]:
        """
        Executes an AppleScript and returns the result.

        Args:
            script (str): The AppleScript code to execute.

        Returns:
            A dictionary containing the execution result:
            - 'success' (bool): True if the execution was successful, False otherwise.
            - 'message' (str): A descriptive message about the outcome.
            - 'output' (str): The standard output from the script if successful.
        """
        if not self.osascript_available:
            return {
                "success": False,
                "message": "Error: 'osascript' command is not available on this system. Cannot execute AppleScript.",
                "output": ""
            }

        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                check=True,
                encoding='utf-8'
            )
            return {
                "success": True,
                "message": "AppleScript executed successfully.",
                "output": result.stdout.strip()
            }
        except FileNotFoundError:
            # This should ideally be caught by _check_osascript, but as a fallback.
            return {
                "success": False,
                "message": "Error: 'osascript' command not found. Ensure you are running on macOS.",
                "output": ""
            }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "message": f"Error executing AppleScript: {e.stderr.strip()}",
                "output": ""
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"An unexpected error occurred during AppleScript execution: {e}",
                "output": ""
            }

    def read_screen_text(self) -> Dict[str, Any]:
        """
        Reads all visible text from the current screen by attempting to extract
        text from accessible UI elements.

        This method relies on AppleScript to interact with macOS accessibility APIs.
        It might not capture text from images or applications that do not expose
        their UI elements properly.

        Returns:
            A dictionary containing the result:
            - 'success' (bool): True if the operation was successful, False otherwise.
            - 'message' (str): A descriptive message about the operation's outcome.
            - 'text' (str): The extracted text from the screen if successful.
        """
        script_content = """
        set screen_text to ""
        try
            tell application "System Events"
                -- Iterate through all processes
                repeat with p in (processes whose background only is false)
                    try
                        tell p
                            -- Iterate through all windows of the process
                            repeat with w in windows
                                try
                                    -- Attempt to get the entire contents of the window
                                    set window_elements to entire contents of w
                                    repeat with elem in window_elements
                                        try
                                            -- Extract AXValue if it exists and is not missing
                                            if exists attribute "AXValue" of elem then
                                                set val to value of attribute "AXValue" of elem
                                                if val is not missing value then
                                                    set screen_text to screen_text & (val as text) & "\\n"
                                                end if
                                            end if
                                        on error
                                            -- Ignore elements that don't have AXValue or cause errors
                                        end try
                                    end repeat
                                on error
                                    -- Ignore windows that cannot be accessed or processed
                                end try
                            end repeat
                        end tell
                    on error
                        -- Ignore processes that cannot be accessed
                    end try
                end repeat
            end tell
        on error errMsg number errorNumber
            return "Error: " & errMsg & " (Code: " & errorNumber & ")"
        end try
        return screen_text
        """
        script_result = self._run_applescript(script_content)

        if not script_result["success"]:
            return {
                "success": False,
                "message": f"Failed to read screen text: {script_result['message']}",
                "text": ""
            }

        extracted_text = script_result["output"]

        if not extracted_text:
            return {
                "success": False,
                "message": "No text was found on the screen or could be extracted.",
                "text": ""
            }

        return {
            "success": True,
            "message": "Successfully read screen text.",
            "text": extracted_text
        }

    def read_specific_window_text(self, window_title_substring: str) -> Dict[str, Any]:
        """
        Reads text from a specific window identified by a substring in its title.

        This method is more targeted than `read_screen_text` but its effectiveness
        is highly dependent on the application and how it exposes its UI elements
        to accessibility services. It might not capture all text from all applications.

        Args:
            window_title_substring (str): A substring that uniquely identifies
                                          the target window's title. Must not be empty.

        Returns:
            A dictionary containing the result:
            - 'success' (bool): True if the operation was successful, False otherwise.
            - 'message' (str): A descriptive message about the operation's outcome.
            - 'text' (str): The extracted text from the specified window if successful.
        """
        if not window_title_substring or not isinstance(window_title_substring, str):
            return {
                "success": False,
                "message": "Invalid input: 'window_title_substring' must be a non-empty string.",
                "text": ""
            }

        # Ensure proper escaping for AppleScript string literals
        escaped_title_substring = window_title_substring.replace('"', '\\"')

        script_template = f"""
        set target_window to null
        set found_window to false

        try
            tell application "System Events"
                -- Get the frontmost process first, then search its windows
                set front_process to first process whose frontmost is true
                tell front_process
                    repeat with w in windows
                        if name of w contains "{escaped_title_substring}" then
                            set target_window to w
                            set found_window to true
                            exit repeat
                        end if
                    end repeat
                end tell
            end tell
        on error errMsg number errorNumber
            return "Error accessing System Events: " & errMsg & " (Code: " & errorNumber & ")"
        end try

        if not found_window then
            return "Error: Window with title containing '{window_title_substring}' not found among frontmost application's windows."
        end if

        -- Now process the found window
        set window_text to ""
        try
            tell application "System Events"
                tell target_window
                    set ui_elements to entire contents
                    repeat with elem in ui_elements
                        try
                            if exists attribute "AXValue" of elem then
                                set val to value of attribute "AXValue" of elem
                                if val is not missing value then
                                    set window_text to window_text & (val as text) & "\\n"
                                end if
                            end if
                        on error
                            -- Ignore elements that don't have AXValue or cause errors
                        end try
                    end repeat
                end tell
            end tell
        on error errMsg number errorNumber
            return "Error processing window content: " & errMsg & " (Code: " & errorNumber & ")"
        end try
        return window_text
        """

        script_result = self._run_applescript(script_template)

        if not script_result["success"]:
            return {
                "success": False,
                "message": f"Failed to read specific window text: {script_result['message']}",
                "text": ""
            }

        extracted_text = script_result["output"]

        if extracted_text.startswith("Error:"):
            return {
                "success": False,
                "message": extracted_text,
                "text": ""
            }
        elif not extracted_text:
            return {
                "success": False,
                "message": f"No extractable text was found in the window titled '{window_title_substring}'. It might be empty or inaccessible.",
                "text": ""
            }
        else:
            return {
                "success": True,
                "message": f"Successfully read text from window containing '{window_title_substring}'.",
                "text": extracted_text
            }

    def read_screen_with_ocr(self, image_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Reads text from the screen or a specified image file using OCR.

        This method requires the 'pyautogui' and 'pytesseract' libraries to be
        installed, along with the Tesseract OCR engine.

        Args:
            image_path (Optional[str]): Path to an image file. If None, a screenshot
                                        of the entire screen will be taken.

        Returns:
            A dictionary containing the result:
            - 'success' (bool): True if the operation was successful, False otherwise.
            - 'message' (str): A descriptive message about the operation's outcome.
            - 'text' (str): The extracted text from the screen/image if successful.
        """
        try:
            import pyautogui
            import pytesseract
            from PIL import Image
        except ImportError:
            return {
                "success": False,
                "message": "OCR functionality requires 'pyautogui', 'pytesseract', and 'Pillow' to be installed. Please install them ('pip install pyautogui pytesseract Pillow').",
                "text": ""
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"An error occurred while importing OCR dependencies: {e}",
                "text": ""
            }

        try:
            if image_path:
                if not os.path.exists(image_path):
                    return {
                        "success": False,
                        "message": f"Error: Image file not found at '{image_path}'.",
                        "text": ""
                    }
                img = Image.open(image_path)
                message_suffix = f"from image '{os.path.basename(image_path)}'"
            else:
                # Capture a screenshot of the entire screen
                screenshot = pyautogui.screenshot()
                img = screenshot
                message_suffix = "from screen"

            # Perform OCR
            extracted_text = pytesseract.image_to_string(img)

            if not extracted_text.strip():
                return {
                    "success": False,
                    "message": f"No text could be extracted {message_suffix} using OCR. Ensure the image contains clear text.",
                    "text": ""
                }

            return {
                "success": True,
                "message": f"Successfully extracted text {message_suffix} using OCR.",
                "text": extracted_text.strip()
            }

        except FileNotFoundError:
            return {
                "success": False,
                "message": "Error: Tesseract OCR engine not found. Please ensure Tesseract is installed and in your system's PATH.",
                "text": ""
            }
        except pytesseract.TesseractNotFoundError:
            return {
                "success": False,
                "message": "Error: Tesseract OCR engine not found. Please ensure Tesseract is installed and in your system's PATH.",
                "text": ""
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"An unexpected error occurred during OCR processing: {e}",
                "text": ""
            }

if __name__ == '__main__':
    print("Initializing ScreenReader...")
    reader = ScreenReader()

    print("\n--- Reading all screen text (using AppleScript accessibility) ---")
    result_all = reader.read_screen_text()
    print(f"Success: {result_all['success']}")
    print(f"Message: {result_all['message']}")
    if result_all['success']:
        print("Extracted Text (first 200 chars):\n" + result_all['text'][:200] + "..." if len(result_all['text']) > 200 else result_all['text'])

    print("\n--- Reading text from a specific window (e.g., Finder) ---")
    # IMPORTANT: Replace "Finder" with a substring of a window title that is
    # currently open and has text you want to read.
    # For example, if you have a document open named "MyDocument.txt", you could use "MyDocument".
    # If a dialog box is open, try to match part of its title.
    # For demonstration, let's assume "Finder" is a common open window.
    # You might need to adjust this based on what's actually open on your screen.
    # For a more reliable test, open a text editor and save a file with a unique name.
    # Then, use that unique name or a part of it here.
    target_window_title = "Finder" # Change this to a relevant open window title
    print(f"Attempting to read from a window containing '{target_window_title}'...")
    result_window = reader.read_specific_window_text(target_window_title)
    print(f"Success: {result_window['success']}")
    print(f"Message: {result_window['message']}")
    if result_window['success']:
        print("Extracted Text (first 200 chars):\n" + result_window['text'][:200] + "..." if len(result_window['text']) > 200 else result_window['text'])

    print("\n--- Attempting to read from a non-existent window ---")
    result_nonexistent = reader.read_specific_window_text("NonExistentWindow12345")
    print(f"Success: {result_nonexistent['success']}")
    print(f"Message: {result_nonexistent['message']}")
    if result_nonexistent['success']:
        print("Extracted Text:\n" + result_nonexistent['text'])

    # --- OCR Example ---
    print("\n--- Reading screen text using OCR (requires Tesseract, pyautogui, Pillow) ---")
    print("Note: This will take a screenshot and perform OCR. Results depend on Tesseract's accuracy.")

    # You can either capture the current screen or provide a path to an image file.
    # To test with an image, save an image with text (e.g., a screenshot you took earlier)
    # and provide its path to read_screen_with_ocr.
    # Example: result_ocr_image = reader.read_screen_with_ocr(image_path="path/to/your/image.png")

    result_ocr_screen = reader.read_screen_with_ocr()
    print(f"Success: {result_ocr_screen['success']}")
    print(f"Message: {result_ocr_screen['message']}")
    if result_ocr_screen['success']:
        print("Extracted Text (first 200 chars):\n" + result_ocr_screen['text'][:200] + "..." if len(result_ocr_screen['text']) > 200 else result_ocr_screen['text'])

    # Example of reading from a specific image file (uncomment and provide a valid path)
    # try:
    #     # Create a dummy image for testing if no image path is provided
    #     dummy_img_path = "test_ocr_image.png"
    #     from PIL import Image, ImageDraw, ImageFont
    #     img_test = Image.new('RGB', (300, 100), color = (255, 255, 255))
    #     d = ImageDraw.Draw(img_test)
    #     try:
    #         # Try to use a common font
    #         font = ImageFont.truetype("arial.ttf", 20)
    #     except IOError:
    #         # Fallback if arial.ttf is not found
    #         font = ImageFont.load_default()
    #     d.text((10,10), "This is a test for OCR.", fill=(0,0,0), font=font)
    #     img_test.save(dummy_img_path)
    #     print(f"\n--- Reading from a specific image file: {dummy_img_path} ---")
    #     result_ocr_image = reader.read_screen_with_ocr(image_path=dummy_img_path)
    #     print(f"Success: {result_ocr_image['success']}")
    #     print(f"Message: {result_ocr_image['message']}")
    #     if result_ocr_image['success']:
    #         print("Extracted Text:\n" + result_ocr_image['text'])
    #     os.remove(dummy_img_path) # Clean up dummy image
    # except ImportError:
    #     print("\nSkipping image file OCR test: Pillow not installed.")
    # except Exception as e:
    #     print(f"\nError during dummy image creation or OCR test: {e}")
