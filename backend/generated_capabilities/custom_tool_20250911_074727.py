
import platform
import subprocess
import json
from typing import Dict, Any, Optional, List

class ScreenReader:
    """
    A specialized tool class for reading text from the screen on macOS.

    This class utilizes system-level tools to capture screen content and
    extract text from it. It is designed to be safe and does not modify
    system settings without explicit user action.
    """

    def __init__(self):
        """
        Initializes the ScreenReader.

        Checks if the operating system is macOS. If not, it raises an
        exception as this class is specific to macOS.
        """
        if platform.system() != "Darwin":
            raise EnvironmentError("ScreenReader is only compatible with macOS.")

    def _run_command(self, command: List[str]) -> Dict[str, Any]:
        """
        Executes a shell command and captures its output.

        Args:
            command: A list of strings representing the command and its arguments.

        Returns:
            A dictionary containing 'success' (bool), 'message' (str), and
            'output' (list of str if successful, None otherwise).
        """
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                encoding='utf-8'
            )
            return {
                "success": True,
                "message": "Command executed successfully.",
                "output": result.stdout.strip().splitlines()
            }
        except FileNotFoundError:
            return {
                "success": False,
                "message": f"Error: Command '{command[0]}' not found. Please ensure necessary tools are installed.",
                "output": None
            }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "message": f"Error executing command: {e}\nStderr: {e.stderr}",
                "output": None
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"An unexpected error occurred: {e}",
                "output": None
            }

    def read_screen_text(self) -> Dict[str, Any]:
        """
        Captures the entire screen and attempts to extract text using OCR.

        This method uses macOS's built-in `screencapture` command to take a
        screenshot and then pipes it to `textutil` for text extraction.

        Returns:
            A dictionary with the following keys:
            - 'success' (bool): True if text extraction was successful, False otherwise.
            - 'message' (str): A descriptive message about the operation.
            - 'text' (Optional[str]): The extracted text from the screen if successful.
        """
        # Step 1: Capture the screen as an image file (temporary)
        # We'll pipe the output directly to textutil to avoid creating a temp file.
        screencapture_command = ["screencapture", "-i", "-"] # -i for interactive selection, - for stdout

        # Step 2: Pipe the screenshot output to textutil for text extraction
        # textutil -stdin -stdout -format txt can read from stdin and output plain text.
        textutil_command = ["textutil", "-stdin", "-stdout", "-format", "txt"]

        try:
            # Use Popen to create a pipeline
            screencapture_process = subprocess.Popen(
                screencapture_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8'
            )
            textutil_process = subprocess.Popen(
                textutil_command,
                stdin=screencapture_process.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8'
            )

            # Allow screencapture to finish and close its stdout pipe
            screencapture_process.stdout.close()

            # Get the output from textutil
            stdout, stderr = textutil_process.communicate()

            # Check for errors from both processes
            screencapture_error = screencapture_process.wait()
            textutil_error = textutil_process.returncode

            if screencapture_error != 0:
                return {
                    "success": False,
                    "message": f"Error capturing screen: screencapture exited with code {screencapture_error}. Stderr: {screencapture_process.stderr.read()}",
                    "text": None
                }

            if textutil_error != 0:
                return {
                    "success": False,
                    "message": f"Error extracting text: textutil exited with code {textutil_error}. Stderr: {stderr}",
                    "text": None
                }

            return {
                "success": True,
                "message": "Screen text read successfully.",
                "text": stdout.strip()
            }

        except FileNotFoundError as e:
            return {
                "success": False,
                "message": f"Error: Required command not found. Please ensure 'screencapture' and 'textutil' are available. Details: {e}",
                "text": None
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"An unexpected error occurred during screen reading: {e}",
                "text": None
            }

    def read_selected_area_text(self) -> Dict[str, Any]:
        """
        Allows the user to select an area of the screen and reads the text from it.

        This method uses the interactive mode of `screencapture` which prompts
        the user to select an area. The selected area's image is then processed
        by `textutil` for text extraction.

        Returns:
            A dictionary with the following keys:
            - 'success' (bool): True if text extraction was successful, False otherwise.
            - 'message' (str): A descriptive message about the operation.
            - 'text' (Optional[str]): The extracted text from the selected area if successful.
        """
        # This method is essentially the same as read_screen_text with -i flag,
        # but we explicitly name it to be more descriptive for the user.
        # The -i flag for screencapture itself handles the interactive selection.
        return self.read_screen_text()

# Example Usage (optional, for testing purposes)
if __name__ == "__main__":
    try:
        reader = ScreenReader()

        print("--- Reading entire screen text ---")
        result_all = reader.read_screen_text()
        print(json.dumps(result_all, indent=2))

        print("\n--- Reading selected area text ---")
        print("Please select an area on your screen when prompted by the cursor.")
        result_selected = reader.read_selected_area_text()
        print(json.dumps(result_selected, indent=2))

    except EnvironmentError as e:
        print(f"Initialization Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
