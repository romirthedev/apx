
import sys
import subprocess
import plistlib
import os
import tempfile
from typing import Dict, Any, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ScreenTextReader:
    """
    A specialized tool class for reading screen text on macOS.

    This class utilizes macOS's built-in accessibility features and command-line
    tools to capture screen content and extract text using OCR. It also
    provides functionality to retrieve window titles.
    """

    def __init__(self):
        """
        Initializes the ScreenTextReader.

        Raises:
            EnvironmentError: If the operating system is not macOS.
        """
        if sys.platform != "darwin":
            raise EnvironmentError("This class is designed for macOS only.")
        logging.info("ScreenTextReader initialized.")

    def _run_command(self, command: List[str], timeout: int = 15) -> Dict[str, Any]:
        """
        Executes a shell command and returns structured output with enhanced error handling.

        Args:
            command: A list of strings representing the command and its arguments.
            timeout: The maximum time in seconds to wait for the command to complete.

        Returns:
            A dictionary with 'success' (bool), 'message' (str), and 'output' (str) keys.
        """
        command_str = ' '.join(command)
        try:
            logging.debug(f"Running command: {command_str}")
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                timeout=timeout
            )
            logging.debug(f"Command '{command_str}' executed successfully.")
            return {
                "success": True,
                "message": "Command executed successfully.",
                "output": process.stdout.strip()
            }
        except FileNotFoundError:
            error_message = f"Error: Command not found: '{command[0]}'. Ensure it's installed and in your PATH."
            logging.error(error_message)
            return {
                "success": False,
                "message": error_message,
                "output": ""
            }
        except subprocess.CalledProcessError as e:
            error_message = f"Error executing command '{command_str}': {e.stderr.strip() or e.stdout.strip()}"
            logging.error(error_message)
            return {
                "success": False,
                "message": error_message,
                "output": ""
            }
        except subprocess.TimeoutExpired:
            error_message = f"Error: Command '{command_str}' timed out after {timeout} seconds."
            logging.error(error_message)
            return {
                "success": False,
                "message": error_message,
                "output": ""
            }
        except Exception as e:
            error_message = f"An unexpected error occurred while running command '{command_str}': {e}"
            logging.error(error_message, exc_info=True)
            return {
                "success": False,
                "message": error_message,
                "output": ""
            }

    def _is_tesseract_installed(self) -> bool:
        """Checks if Tesseract OCR is installed and accessible."""
        tesseract_check = self._run_command(["tesseract", "--version"])
        return tesseract_check["success"]

    def get_screen_text(self, region: Optional[tuple[int, int, int, int]] = None) -> Dict[str, Any]:
        """
        Captures a screenshot and extracts text from it using Tesseract OCR.

        Args:
            region: An optional tuple (x, y, width, height) to specify a
                    specific area of the screen to capture. If None, the
                    entire screen is captured.

        Returns:
            A dictionary with 'success' (bool), 'message' (str), and 'text' (str) keys.
            'text' will contain the extracted screen text if successful.
        """
        if not self._is_tesseract_installed():
            logging.warning("Tesseract OCR is not installed or accessible. Text extraction will not be possible.")
            return {
                "success": False,
                "message": "Tesseract OCR is required for screen text extraction but is not installed or accessible. Please install it (e.g., 'brew install tesseract').",
                "text": ""
            }

        # Use a temporary file for the screenshot
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_screenshot:
            screenshot_path = tmp_screenshot.name
            logging.debug(f"Using temporary file for screenshot: {screenshot_path}")

        capture_command = ["screencapture"]
        if region:
            if not (isinstance(region, tuple) and len(region) == 4 and all(isinstance(i, int) and i >= 0 for i in region)):
                logging.error(f"Invalid region format: {region}. Expected (x, y, width, height) with non-negative integers.")
                return {
                    "success": False,
                    "message": "Invalid region format. Expected a tuple of four non-negative integers (x, y, width, height).",
                    "text": ""
                }
            x, y, width, height = region
            capture_command.extend(["-R", f"{x},{y},{width},{height}"])
        capture_command.append(screenshot_path)

        # 1. Capture screenshot
        capture_result = self._run_command(capture_command)

        if not capture_result["success"]:
            logging.error(f"Failed to capture screen: {capture_result['message']}")
            self._cleanup_file(screenshot_path) # Clean up if capture failed
            return {
                "success": False,
                "message": f"Failed to capture screen: {capture_result['message']}",
                "text": ""
            }

        # 2. Attempt to extract text using Tesseract OCR
        # Using --psm 6 for default page segmentation, or 3 for fully automatic. 3 is often better.
        tesseract_command = ["tesseract", screenshot_path, "stdout", "--psm", "3", "-l", "eng"]
        ocr_result = self._run_command(tesseract_command)

        if ocr_result["success"] and ocr_result["output"]:
            logging.info("Screen text extracted successfully using Tesseract.")
            extracted_text = ocr_result["output"]
            self._cleanup_file(screenshot_path)
            return {
                "success": True,
                "message": "Screen text extracted successfully using Tesseract.",
                "text": extracted_text
            }
        else:
            error_msg = ocr_result.get('message', 'Tesseract OCR failed or returned no text.')
            logging.warning(f"Tesseract OCR failed or returned no text. {error_msg}")
            self._cleanup_file(screenshot_path)
            return {
                "success": False,
                "message": f"Tesseract OCR failed or returned no text. Ensure Tesseract is installed and accessible. Original error: {error_msg}",
                "text": ""
            }

    def get_window_titles(self) -> Dict[str, Any]:
        """
        Retrieves a list of all currently open window titles and their associated application names.

        This method uses AppleScript to query the running applications and their
        frontmost windows.

        Returns:
            A dictionary with 'success' (bool), 'message' (str), and 'titles' (List[str]) keys.
            'titles' will be a list of formatted strings (e.g., "Window Title (Application Name)")
            if successful.
        """
        # This AppleScript aims to get the title and application name for all visible windows.
        # It handles cases where an app might not have a front window or a title.
        script_source = """
        tell application "System Events"
            set window_list to {}
            set excluded_apps to {"SystemUIServer", "Dock", "Finder", "Activity Monitor", "Console", "Script Editor"} -- Apps that often have windows we don't need or are hard to parse
            
            repeat with proc in (processes whose visible is true)
                set proc_name to proc's name
                
                -- Skip excluded applications
                if proc_name is not in excluded_apps then
                    -- Attempt to get window titles, handle errors if no windows or titles
                    try
                        repeat with win in proc's windows
                            set win_title to win's title
                            if win_title is not "" then -- Only include if there's a title
                                set end of window_list to {proc_name, win_title}
                            end if
                        end repeat
                    on error errMsg number errorNumber
                        -- Ignore errors like "System Events got an error: -1728: Can't get window 1 of process \"AppName\"."
                        -- or "System Events got an error: -1743: The object \"window\" of the application \"AppName\" is not a variable."
                        if errorNumber is not -1728 and errorNumber is not -1743 then
                            log "Error processing windows for process " & proc_name & ": " & errMsg
                        end if
                    end try
                end if
            end repeat
            return window_list
        end tell
        """
        script_command = ["/usr/bin/osascript", "-e", script_source]
        result = self._run_command(script_command)

        if not result["success"]:
            logging.error(f"Failed to get window titles: {result['message']}")
            return {
                "success": False,
                "message": f"Failed to get window titles: {result['message']}",
                "titles": []
            }

        try:
            raw_output = result["output"]
            if not raw_output:
                logging.info("No visible windows with titles found.")
                return {
                    "success": True,
                    "message": "No visible windows with titles found.",
                    "titles": []
                }

            # The output is typically a string representation of a list of lists, e.g.,
            # "{Finder, Untitled}, {Finder, My Document}, {TextEdit, Untitled}"
            # However, osascript's output can be inconsistent. Let's parse it robustly.

            window_titles = []
            # A common format is: "AppName1,WindowTitle1,AppName2,WindowTitle2,..."
            # Or "{AppName1, WindowTitle1}, {AppName2, WindowTitle2}, ..."

            # Try parsing as a list of lists first
            try:
                parsed_list = plistlib.loads(f"<plist><array>{raw_output.replace('}, {', '}</key><key>').replace('{','<dict><key>').replace('}','</dict>').replace(',', '</key><string>')}</array></plist>".encode('utf-8'))
                for item in parsed_list:
                    if isinstance(item, dict) and len(item) == 2:
                        app_name = list(item.keys())[0]
                        window_title = list(item.values())[0]
                        if app_name and window_title and window_title.lower() not in ["untitled", "new document"]:
                             window_titles.append(f"{window_title} ({app_name})")
            except Exception:
                # If plist parsing fails, try a simpler string split
                logging.debug("Plist parsing failed, attempting string split for window titles.")
                entries = raw_output.strip('{}').split('}, {')
                for entry in entries:
                    parts = entry.split(',', 1)
                    if len(parts) == 2:
                        app_name = parts[0].strip()
                        window_title = parts[1].strip()
                        if app_name and window_title and window_title.lower() not in ["untitled", "new document"]:
                            window_titles.append(f"{window_title} ({app_name})")

            if window_titles:
                logging.info(f"Successfully retrieved {len(window_titles)} window titles.")
                return {
                    "success": True,
                    "message": "All visible window titles retrieved.",
                    "titles": window_titles
                }
            else:
                logging.warning("No specific window titles found after parsing, or all were generic.")
                return {
                    "success": True,
                    "message": "No specific window titles found, or all titles were generic (e.g., 'Untitled').",
                    "titles": []
                }
        except Exception as e:
            error_message = f"Error parsing window titles from osascript output: {e}"
            logging.error(error_message, exc_info=True)
            return {
                "success": False,
                "message": error_message,
                "titles": []
            }

    def _cleanup_file(self, file_path: str):
        """Safely removes a file if it exists."""
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logging.debug(f"Cleaned up file: {file_path}")
            except OSError as e:
                logging.warning(f"Error cleaning up file {file_path}: {e}")

    def cleanup(self):
        """
        Cleans up any temporary files created by the class.
        Currently cleans up the temporary screenshot file.
        """
        logging.info("Performing cleanup...")
        # This method might be called if get_screen_text fails early, so we can't assume
        # screenshot_path is available as an instance variable without more complex state management.
        # A better approach is to rely on tempfile context managers or pass paths around.
        # For now, we'll just log that cleanup is intended for temporary files.
        logging.info("Cleanup complete. Temporary screenshot files are managed by tempfile.")


# Example usage (optional, for testing purposes)
if __name__ == "__main__":
    try:
        reader = ScreenTextReader()

        print("--- Testing Screen Text Extraction ---")
        # Example: Capture the whole screen
        print("Capturing entire screen...")
        text_result_full = reader.get_screen_text()
        if text_result_full["success"]:
            print("\n--- Full Screen Text ---")
            print(text_result_full["text"] if text_result_full["text"] else "No text detected on the full screen.")
        else:
            print(f"\nError getting full screen text: {text_result_full['message']}")

        # Example: Capture a specific region (adjust coordinates as needed)
        # You might need to manually determine coordinates or use another tool for this.
        # For demonstration, let's assume a small area.
        # On a typical Retina display, coordinates might be higher.
        # Be careful with these coordinates; they are illustrative.
        example_region = (100, 100, 400, 150) # x, y, width, height
        print(f"\nCapturing region: {example_region}...")
        text_result_region = reader.get_screen_text(region=example_region)
        if text_result_region["success"]:
            print(f"\n--- Text from Region {example_region} ---")
            print(text_result_region["text"] if text_result_region["text"] else "No text detected in the specified region.")
        else:
            print(f"\nError getting text from region {example_region}: {text_result_region['message']}")

        print("\n--- Testing Window Title Retrieval ---")
        window_titles_result = reader.get_window_titles()
        if window_titles_result["success"]:
            print("\n--- Window Titles ---")
            if window_titles_result["titles"]:
                for title in window_titles_result["titles"]:
                    print(f"- {title}")
            else:
                print("No titles found.")
        else:
            print(f"\nError getting window titles: {window_titles_result['message']}")

    except EnvironmentError as e:
        print(f"Environment Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during execution: {e}")
        logging.error("An uncaught exception occurred.", exc_info=True)
    finally:
        # Cleanup is handled by context managers for temp files,
        # but explicit cleanup can still be useful for other resources if added later.
        pass # No explicit cleanup needed for temporary files managed by `with tempfile.NamedTemporaryFile`.
