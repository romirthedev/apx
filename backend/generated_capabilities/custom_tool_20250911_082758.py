
import sys
import subprocess
import json
from typing import Dict, Any, Optional, List
import os

class ScreenTextReader:
    """
    A specialized tool for reading text from the screen on macOS.

    This class utilizes macOS's built-in `screencapture` tool and an OCR library
    (like Tesseract) to capture and process screen content.
    """

    def __init__(self):
        """
        Initializes the ScreenTextReader.

        Raises:
            OSError: If the operating system is not macOS.
            FileNotFoundError: If essential system commands (`osascript`, `screencapture`) are not found.
        """
        if sys.platform != "darwin":
            raise OSError("This tool is only compatible with macOS.")

        # Pre-check essential system commands to fail early if they are not available
        self._check_command_availability(["/usr/bin/osascript", "/usr/sbin/screencapture"])

    def _check_command_availability(self, commands: List[str]):
        """
        Checks if a list of commands are available in the system's PATH.

        Args:
            commands: A list of command paths to check.

        Raises:
            FileNotFoundError: If any of the commands are not found.
        """
        for cmd in commands:
            if not os.path.exists(cmd):
                raise FileNotFoundError(f"Required command '{cmd}' not found. Please ensure it is installed and in your system's PATH.")

    def _run_command(self, command: List[str], input_data: Optional[bytes] = None) -> Dict[str, Any]:
        """
        Executes a shell command and returns structured output.

        Args:
            command: A list of strings representing the command and its arguments.
            input_data: Optional bytes to pass as stdin to the command.

        Returns:
            A dictionary containing 'success' (bool), 'message' (str), and 'output' (str or None).
        """
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE if input_data is not None else None,
                text=False  # Capture output as bytes initially for binary data like screenshots
            )
            stdout, stderr = process.communicate(input=input_data)

            if process.returncode == 0:
                return {"success": True, "message": "Command executed successfully.", "output": stdout}
            else:
                error_message = stderr.decode('utf-8', errors='ignore').strip()
                return {"success": False, "message": f"Command failed: {error_message}", "output": None}
        except FileNotFoundError:
            return {"success": False, "message": f"Command not found: {command[0]}", "output": None}
        except Exception as e:
            return {"success": False, "message": f"An unexpected error occurred: {e}", "output": None}

    def _get_accessibility_permissions(self) -> Dict[str, Any]:
        """
        Checks if the application has macOS accessibility permissions.
        If not, it provides instructions on how to grant them.

        Returns:
            A dictionary with 'success' (bool) and 'message' (str).
        """
        # A more reliable way to check is to attempt an action that requires permissions
        # and handle the potential error, or query system settings.
        # For simplicity here, we'll use osascript to simulate an interaction that
        # would likely fail or prompt if permissions are missing.
        # This is not a foolproof check but a common approach.
        check_script = """
        tell application "System Events"
            try
                set process_names to name of every process
                if process_names is not {} then
                    return "Permissions granted or prompt will appear."
                else
                    return "Error: Could not access process list. Permissions likely missing."
                end if
            on error msg number err
                if err is -1712 then -- User canceled session, typically means permissions missing
                    return "Error: User canceled session. Permissions likely missing."
                else if err is -1746 then -- Permissions error
                    return "Error: -1746 (Permissions error). Please grant Accessibility permissions."
                else
                    return "Error: An unknown AppleScript error occurred (" & err & "): " & msg
                end if
            end try
        end tell
        """
        result = self._run_command(["/usr/bin/osascript", "-e", check_script])

        if result["success"] and "Permissions granted" in result["output"]:
            return {"success": True, "message": "Accessibility permissions appear to be granted."}
        else:
            error_msg = result.get("message", "Unknown error during permission check.")
            if "Permissions likely missing" in error_msg or "Permissions error" in error_msg or "-1746" in error_msg:
                return {
                    "success": False,
                    "message": f"Accessibility permissions are required. Please grant them manually:\n"
                               f"1. Open System Settings.\n"
                               f"2. Go to 'Privacy & Security' > 'Accessibility'.\n"
                               f"3. Add '{os.path.basename(sys.executable)}' and enable it.\n"
                               f"Original error: {error_msg}"
                }
            else:
                return {"success": False, "message": f"An issue occurred while checking permissions: {result.get('message', 'Unknown error')}"}


    def _perform_ocr(self, image_data: bytes, lang: str = "eng", psm: int = 6) -> Dict[str, Any]:
        """
        Performs Optical Character Recognition on image data using Tesseract.

        Args:
            image_data: The raw image data (bytes) to perform OCR on.
            lang: The language code for OCR (default is 'eng' for English).
            psm: The Page Segmentation Mode for Tesseract.

        Returns:
            A dictionary with 'success' (bool), 'message' (str), and 'text' (str or None).
        """
        tesseract_path = "/usr/local/bin/tesseract" # Common path via Homebrew
        if not os.path.exists(tesseract_path):
            # Attempt to find tesseract in PATH if not in the default location
            try:
                tesseract_path = subprocess.check_output(["which", "tesseract"], text=True).strip()
            except subprocess.CalledProcessError:
                return {"success": False, "message": "tesseract command not found. Please install tesseract (e.g., 'brew install tesseract') and ensure it's in your PATH.", "text": None}

        ocr_command = [
            tesseract_path,
            "stdin",
            "stdout",
            "-l",
            lang,
            "--psm",
            str(psm)
        ]

        result = self._run_command(ocr_command, input_data=image_data)

        if result["success"]:
            return {"success": True, "message": "OCR processed successfully.", "text": result["output"].decode('utf-8', errors='ignore').strip()}
        else:
            return {"success": False, "message": f"Tesseract OCR failed: {result.get('message', 'Unknown error')}", "text": None}

    def read_entire_screen(self) -> Dict[str, Any]:
        """
        Reads all visible text from the entire screen.

        This method captures the screen and uses an OCR tool (Tesseract)
        to extract text. Requires Tesseract to be installed and accessible.

        Returns:
            A dictionary with 'success' (bool), 'message' (str), and 'text' (str or None).
        """
        permission_check = self._get_accessibility_permissions()
        if not permission_check["success"]:
            return {"success": False, "message": permission_check["message"], "text": None}

        # Capture the entire screen to stdout
        capture_command = [
            "/usr/sbin/screencapture",
            "-x",  # -x suppresses sound
            "-",   # Output to stdout
        ]

        capture_result = self._run_command(capture_command)
        if not capture_result["success"]:
            return {"success": False, "message": f"Screen capture failed: {capture_result.get('message', 'Unknown error')}", "text": None}

        # Perform OCR on the captured screenshot data
        ocr_result = self._perform_ocr(capture_result["output"])

        return {
            "success": ocr_result["success"],
            "message": ocr_result["message"],
            "text": ocr_result["text"]
        }

    def read_specific_area(self, x: int, y: int, width: int, height: int, lang: str = "eng", psm: int = 6) -> Dict[str, Any]:
        """
        Reads text from a specific rectangular area of the screen.

        Args:
            x: The x-coordinate of the top-left corner of the area.
            y: The y-coordinate of the top-left corner of the area.
            width: The width of the area.
            height: The height of the area.
            lang: The language code for OCR (default is 'eng').
            psm: The Page Segmentation Mode for Tesseract.

        Returns:
            A dictionary with 'success' (bool), 'message' (str), and 'text' (str or None).
        """
        if not all(isinstance(val, int) and val >= 0 for val in [x, y, width, height]):
            return {"success": False, "message": "Coordinates and dimensions must be non-negative integers.", "text": None}
        if width == 0 or height == 0:
            return {"success": False, "message": "Width and height must be greater than zero.", "text": None}

        permission_check = self._get_accessibility_permissions()
        if not permission_check["success"]:
            return {"success": False, "message": permission_check["message"], "text": None}

        # Capture the specific area to stdout
        capture_command = [
            "/usr/sbin/screencapture",
            "-x",  # Suppress sound
            "-R",
            f"{x},{y},{width},{height}",
            "-",   # Output to stdout
        ]

        capture_result = self._run_command(capture_command)
        if not capture_result["success"]:
            return {"success": False, "message": f"Screen capture failed: {capture_result.get('message', 'Unknown error')}", "text": None}

        # Perform OCR on the captured screenshot data
        ocr_result = self._perform_ocr(capture_result["output"], lang=lang, psm=psm)

        return {
            "success": ocr_result["success"],
            "message": ocr_result["message"],
            "text": ocr_result["text"]
        }

    def read_window_content(self, window_title_substring: Optional[str] = None, lang: str = "eng", psm: int = 6) -> Dict[str, Any]:
        """
        Reads text from specified visible windows.

        This method uses `osascript` to get window information and then `screencapture`
        to capture each window's content, followed by OCR.

        Args:
            window_title_substring: If provided, only windows containing this substring
                                    in their title will be processed. If None, attempts
                                    to process all visible windows.
            lang: The language code for OCR (default is 'eng').
            psm: The Page Segmentation Mode for Tesseract.

        Returns:
            A dictionary with 'success' (bool), 'message' (str), and 'windows' (list of dicts).
            Each dict in the 'windows' list contains 'title' and 'text'.
        """
        permission_check = self._get_accessibility_permissions()
        if not permission_check["success"]:
            return {"success": False, "message": permission_check["message"], "windows": []}

        # Get list of all accessible window UIDs, titles, positions, and sizes
        get_windows_script = """
        tell application "System Events"
            set window_info to {}
            set processes_to_check to (processes whose background only is false)
            repeat with proc in processes_to_check
                try
                    set process_name to name of proc
                    repeat with win in windows of proc
                        -- Skip sheets and popovers, which are usually not main content
                        if subrole of win is not "AXSheet" and subrole of win is not "AXPopover" then
                            set win_id to id of win
                            set win_title to name of win
                            set win_pos to position of win
                            set win_size to size of win
                            set end of window_info to {win_id, process_name, win_title, win_pos, win_size}
                        end if
                    end repeat
                on error
                    -- Ignore processes that we don't have permission to access or that cause errors
                end try
            end repeat
            return window_info
        end tell
        """
        # osascript returns a string representation of a list of lists.
        # We need to parse this carefully.
        result = self._run_command(["/usr/bin/osascript", "-e", get_windows_script])

        if not result["success"] or not result["output"]:
            return {"success": False, "message": f"Failed to retrieve window information: {result.get('message', 'Unknown error')}", "windows": []}

        try:
            # The output is a string like "{{123, 'app1', 'win1', {10, 20}, {300, 400}}, ...}"
            # We need to parse it into a Python list of lists.
            raw_output = result["output"].decode('utf-8', errors='ignore').strip()
            # Basic cleaning and conversion to a structure that json.loads can handle
            # Replace AppleScript list syntax with JSON-compatible syntax
            cleaned_output = raw_output.replace("}, {", "},{").replace("ui element", "\"ui element\"").replace("window", "\"window\"")
            # Convert AppleScript list of lists to JSON-like string
            # This is a bit fragile and might need adjustment for complex titles/names
            list_items = cleaned_output[2:-2].split('},{') # Remove outer {{ and }} and split items
            window_data_raw = []
            for item_str in list_items:
                parts = item_str.split(',')
                if len(parts) >= 5: # Expected: ID, process_name, title, position, size
                    win_id = int(parts[0].strip())
                    # Extract process name and title which might contain commas
                    process_name_start = item_str.find('\'') + 1
                    process_name_end = item_str.find('\'', process_name_start)
                    process_name = item_str[process_name_start:process_name_end]

                    win_title_start_idx = item_str.find('\'', process_name_end + 1) + 1
                    win_title_end_idx = item_str.find('\'', win_title_start_idx)
                    win_title = item_str[win_title_start_idx:win_title_end_idx]

                    # Extract position and size, which are also lists
                    pos_str_start = item_str.find('{', win_title_end_idx) + 1
                    pos_str_end = item_str.find('}', pos_str_start)
                    pos_parts = item_str[pos_str_start:pos_str_end].split(',')
                    win_pos = [int(p.strip()) for p in pos_parts] if len(pos_parts) == 2 else [0,0]

                    size_str_start = item_str.find('{', pos_str_end) + 1
                    size_str_end = item_str.find('}', size_str_start)
                    size_parts = item_str[size_str_start:size_str_end].split(',')
                    win_size = [int(s.strip()) for s in size_parts] if len(size_parts) == 2 else [0,0]

                    window_data_raw.append([win_id, process_name, win_title, win_pos, win_size])
                else:
                    print(f"Warning: Skipped malformed window data: {item_str}", file=sys.stderr)

        except Exception as e:
            return {"success": False, "message": f"Failed to parse window information: {e}\nRaw output: {result['output'].decode()}", "windows": []}


        processed_windows = []
        found_match = False

        for win_id, proc_name, win_title, win_pos, win_size in window_data_raw:
            # Skip windows that are not "visible" or have empty titles (like system dialogs we can't interact with)
            if not win_title or proc_name in ["Finder", "SystemUIServer", "NotificationCenter", "Spotlight", "Dock", "Activity Monitor"]:
                continue

            if window_title_substring is None or window_title_substring.lower() in win_title.lower():
                found_match = True
                try:
                    x, y = win_pos
                    width, height = win_size

                    # Ensure valid dimensions. macOS screens have limits.
                    # Clamp dimensions to avoid errors with screencapture or very large/small windows.
                    # This is a heuristic; actual screen bounds might be needed for perfect clamping.
                    effective_width = max(1, min(width, 4096)) # Arbitrary max width/height for safety
                    effective_height = max(1, min(height, 4096))
                    effective_x = max(0, x)
                    effective_y = max(0, y)

                    # Capture the window content using its bounding box
                    capture_command = [
                        "/usr/sbin/screencapture",
                        "-x",
                        "-R",
                        f"{effective_x},{effective_y},{effective_width},{effective_height}",
                        "-",
                    ]
                    capture_result = self._run_command(capture_command)

                    if not capture_result["success"]:
                        print(f"Warning: Could not capture window '{win_title}' (Process: {proc_name}): {capture_result.get('message', 'Unknown error')}", file=sys.stderr)
                        continue # Move to next window

                    # Perform OCR on the captured image data
                    ocr_result = self._perform_ocr(capture_result["output"], lang=lang, psm=psm)

                    if ocr_result["success"]:
                        processed_windows.append({
                            "title": f"{win_title} (Process: {proc_name})",
                            "text": ocr_result["text"]
                        })
                    else:
                        print(f"Warning: OCR failed for window '{win_title}' (Process: {proc_name}): {ocr_result.get('message', 'Unknown error')}", file=sys.stderr)

                except FileNotFoundError as e:
                    # This should ideally be caught by __init__, but defensive programming.
                    return {"success": False, "message": f"Dependency not found: {e}", "windows": []}
                except Exception as e:
                    print(f"Warning: An error occurred processing window '{win_title}' (Process: {proc_name}): {e}", file=sys.stderr)
                    continue

        if not found_match and window_title_substring:
            return {"success": False, "message": f"No windows found matching the title substring: '{window_title_substring}'.", "windows": []}
        if not processed_windows:
            return {"success": False, "message": "No readable text found in any accessible windows.", "windows": []}

        return {"success": True, "message": "Text from matching windows read successfully.", "windows": processed_windows}


if __name__ == "__main__":
    try:
        reader = ScreenTextReader()

        print("--- Checking Accessibility Permissions ---")
        permission_status = reader._get_accessibility_permissions()
        print(json.dumps(permission_status, indent=2))
        if not permission_status["success"]:
            print("\nExiting due to missing accessibility permissions. Please grant them and re-run.")
            sys.exit(1)

        print("\n--- Reading entire screen ---")
        # For full screen without interaction, ensure '-i' is NOT used in screencapture command.
        # Current implementation uses '-x' to suppress sound and just captures.
        entire_screen_result = reader.read_entire_screen()
        print(json.dumps(entire_screen_result, indent=2))

        print("\n--- Reading a specific area (example: top-left 300x100 pixels) ---")
        # Ensure there's visible content in this area when you run it.
        area_result = reader.read_specific_area(x=0, y=0, width=300, height=100)
        print(json.dumps(area_result, indent=2))

        print("\n--- Reading content from a specific window (e.g., Terminal) ---")
        # Adjust "Terminal" to a window title you have open.
        window_result_specific = reader.read_window_content(window_title_substring="Terminal")
        print(json.dumps(window_result_specific, indent=2))

        print("\n--- Reading content from all visible windows ---")
        window_result_all = reader.read_window_content()
        print(json.dumps(window_result_all, indent=2))

    except OSError as e:
        print(f"Error initializing ScreenTextReader: {e}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during example execution: {e}")
