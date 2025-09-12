
import subprocess
import sys
from typing import Dict, Any, Optional, List

# Define a type alias for the return dictionary
ResponseDict = Dict[str, Any]


class ScreenReader:
    """
    A specialized tool for reading text from the screen on macOS.

    This class utilizes macOS's built-in accessibility features to capture
    and process on-screen text. It is designed to be non-intrusive and
    does not modify system settings without explicit user action outside
    of its direct execution.

    The user's request to "read screen text" is interpreted as extracting
    all visible text content from the current screen. This implementation
    uses AppleScript to interact with System Events and access UI elements,
    which is generally more reliable for text extraction than image-based
    OCR for UI elements.

    Potential Enhancements (depending on deeper needs):
    - For applications that don't expose text easily via accessibility APIs,
      a fallback to image capture and OCR (using libraries like Pillow and pytesseract)
      could be considered, but this adds external dependencies and complexity.
    - More granular control over which windows or applications to scan.
    - Handling of dynamic content that might change during the scan.
    """

    def __init__(self) -> None:
        """
        Initializes the ScreenReader.

        Raises:
            RuntimeError: If the operating system is not macOS.
        """
        if sys.platform != "darwin":
            raise RuntimeError("This class is designed for macOS only.")
        self._check_osascript_availability()

    def _check_osascript_availability(self) -> None:
        """
        Checks if the 'osascript' command is available.

        Raises:
            RuntimeError: If 'osascript' is not found.
        """
        try:
            subprocess.run(["which", "osascript"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError(
                "Error: 'osascript' command not found. This tool requires macOS and its built-in scripting capabilities."
            )

    def _execute_applescript(self, script: str) -> ResponseDict:
        """
        Executes an AppleScript and returns its output.

        Args:
            script (str): The AppleScript code to execute.

        Returns:
            ResponseDict: A dictionary containing:
                - 'success' (bool): True if the operation was successful, False otherwise.
                - 'message' (str): A descriptive message about the operation's outcome.
                - 'output' (Optional[str]): The standard output from the script if successful.
                - 'error' (Optional[str]): The standard error from the script if an error occurred.
        """
        try:
            process = subprocess.Popen(
                ["osascript", "-e", script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                return {
                    "success": True,
                    "message": "AppleScript executed successfully.",
                    "output": stdout.strip(),
                    "error": None,
                }
            else:
                return {
                    "success": False,
                    "message": f"AppleScript execution failed.",
                    "output": None,
                    "error": stderr.strip(),
                }
        except FileNotFoundError:
            # This exception should ideally be caught by _check_osascript_availability,
            # but included for robustness.
            return {
                "success": False,
                "message": "Error: 'osascript' command not found. This tool requires macOS.",
                "output": None,
                "error": "osascript not found.",
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"An unexpected error occurred during AppleScript execution: {e}",
                "output": None,
                "error": str(e),
            }

    def read_screen_text(self) -> ResponseDict:
        """
        Reads all accessible text from the current screen.

        This method attempts to capture text from all active UI elements
        on the screen by iterating through accessible processes and their windows.

        Returns:
            ResponseDict: A dictionary containing:
                - 'success' (bool): True if the operation was successful, False otherwise.
                - 'message' (str): A descriptive message about the operation's outcome.
                - 'text' (Optional[str]): The combined text read from the screen if successful.
        """
        applescript_code = """
        set allText to ""
        tell application "System Events"
            set visibleProcesses to (processes where background only is false)
            repeat with proc in visibleProcesses
                try
                    tell proc
                        repeat with w in windows
                            -- Attempt to get the title of the window
                            try
                                set windowTitle to name of w
                                if windowTitle is not "" then
                                    set allText to allText & "Window: " & windowTitle & return & return
                                end if
                            on error
                                -- Ignore windows without titles
                            end try

                            -- Attempt to get text from all accessible UI elements within the window
                            -- This is a recursive traversal approach for broader coverage.
                            set uiElements to entire contents of w
                            set windowText to ""
                            repeat with element in uiElements
                                try
                                    -- Check if the element has a 'value' and it's not empty
                                    if exists (value of element) and (value of element is not "") then
                                        set elementValue to value of element as string
                                        if elementValue is not "" then
                                            set windowText to windowText & elementValue & " "
                                        end if
                                    end if
                                on error
                                    -- Ignore elements that don't have a 'value' attribute or other errors
                                end try
                            end repeat
                            if windowText is not "" then
                                set allText to allText & trim(windowText) & return & return
                            end if
                        end repeat
                    end tell
                on error
                    -- Ignore processes that are not accessible or have issues
                end try
            end repeat
        end tell

        -- Helper function to trim whitespace and newlines
        on trim(this_string)
            set ASTID to AppleScript's text item delimiters
            set AppleScript's text item delimiters to {return, space}
            set the items to text items of this_string
            set AppleScript's text item delimiters to ""
            set new_string to ""
            repeat with i from 1 to count of items
                set current_item to item i
                if current_item is not "" then
                    if new_string is not "" then
                        set new_string to new_string & " "
                    end if
                    set new_string to new_string & current_item
                end if
            end repeat
            set AppleScript's text item delimiters to ASTID
            return new_string
        end trim

        return trim(allText)
        """
        result = self._execute_applescript(applescript_code)

        if result["success"]:
            screen_text = result["output"]
            if screen_text:
                return {
                    "success": True,
                    "message": "Screen text read successfully.",
                    "text": screen_text,
                }
            else:
                return {
                    "success": False,
                    "message": "No accessible text found on the screen.",
                    "text": None,
                }
        else:
            return {
                "success": False,
                "message": f"Error reading screen text: {result['error']}",
                "text": None,
            }

    def read_focused_element_text(self) -> ResponseDict:
        """
        Reads the text from the currently focused UI element on the screen.

        This method attempts to identify the UI element that currently has keyboard focus
        and extract its text content.

        Returns:
            ResponseDict: A dictionary containing:
                - 'success' (bool): True if the operation was successful, False otherwise.
                - 'message' (str): A descriptive message about the operation's outcome.
                - 'text' (Optional[str]): The text from the focused element if successful.
        """
        applescript_code = """
        tell application "System Events"
            try
                -- Find the frontmost process that is not a background process
                set frontProcess to first process whose frontmost is true and background only is false

                tell frontProcess
                    -- Find the UI element that has keyboard focus
                    set focusedElement to first UI element whose focused is true

                    if (exists focusedElement) then
                        -- Return the value of the focused element, handling potential errors
                        try
                            return value of focusedElement as string
                        on error
                            return "Could not retrieve text from focused element."
                        end try
                    else
                        return "No focused element found."
                    end if
                end tell
            on error msg number errNum
                if errNum is -1728 then -- Element not found error
                    return "No focused element found."
                else
                    return "Error: " & msg
                end if
            end try
        end tell
        """
        result = self._execute_applescript(applescript_code)

        if result["success"]:
            result_text = result["output"]
            if result_text and not result_text.startswith(("No focused element found.", "Error:", "Could not retrieve text")):
                return {
                    "success": True,
                    "message": "Focused element text read successfully.",
                    "text": result_text,
                }
            elif result_text == "No focused element found.":
                return {
                    "success": False,
                    "message": "No focused element found on the screen.",
                    "text": None,
                }
            else:
                # This covers cases like "Could not retrieve text..." or other specific error messages from AppleScript
                return {
                    "success": False,
                    "message": result_text, # Use the error message from AppleScript
                    "text": None,
                }
        else:
            return {
                "success": False,
                "message": f"Error reading focused element text: {result['error']}",
                "text": None,
            }

    def read_window_title(self, process_name: Optional[str] = None) -> ResponseDict:
        """
        Reads the title of the window for a specified process or the frontmost window.

        Args:
            process_name (Optional[str]): The name of the process (e.g., "Google Chrome", "Finder").
                                         If None, it reads the title of the frontmost window.

        Returns:
            ResponseDict: A dictionary containing:
                - 'success' (bool): True if the operation was successful, False otherwise.
                - 'message' (str): A descriptive message about the operation's outcome.
                - 'title' (Optional[str]): The window title if found.
        """
        if process_name is None:
            # Get the frontmost window title if no process name is provided
            applescript_code = """
            tell application "System Events"
                try
                    set frontmostProcess to first process whose frontmost is true and background only is false
                    if exists (window 1 of frontmostProcess) then
                        return name of window 1 of frontmostProcess
                    else
                        return "No frontmost window found."
                    end if
                on error msg number errNum
                    return "Error: " & msg
                end try
            end tell
            """
        else:
            # Validate process_name input
            if not isinstance(process_name, str) or not process_name.strip():
                return {
                    "success": False,
                    "message": "Invalid input: Process name must be a non-empty string.",
                    "title": None,
                }
            applescript_code = f'''
            tell application "System Events"
                set windowTitle to ""
                set found to false
                repeat with proc in (processes where name of it is "{process_name}")
                    try
                        tell proc
                            if exists (window 1) then
                                set windowTitle to name of window 1
                                set found to true
                                exit repeat
                            end if
                        end tell
                    on error
                        -- Ignore processes that might not have a window or are inaccessible
                    end try
                end repeat
                if found then
                    return windowTitle
                else
                    return "No active window found for process '{process_name}'."
                end if
            end tell
            '''

        result = self._execute_applescript(applescript_code)

        if result["success"]:
            title = result["output"]
            if title and not title.startswith(("No active window found", "No frontmost window found", "Error:")):
                return {
                    "success": True,
                    "message": f"Window title retrieved successfully.",
                    "title": title,
                }
            elif title.startswith("No active window found") or title.startswith("No frontmost window found"):
                return {
                    "success": False,
                    "message": title, # Use the specific "not found" message
                    "title": None,
                }
            else:
                return {
                    "success": False,
                    "message": f"Could not retrieve window title: {title}",
                    "title": None,
                }
        else:
            return {
                "success": False,
                "message": f"Error reading window title: {result['error']}",
                "title": None,
            }

    def get_all_window_titles(self) -> ResponseDict:
        """
        Retrieves titles of all visible windows across all accessible processes.

        Returns:
            ResponseDict: A dictionary containing:
                - 'success' (bool): True if the operation was successful, False otherwise.
                - 'message' (str): A descriptive message about the operation's outcome.
                - 'titles' (Optional[List[str]]): A list of window titles if found.
        """
        applescript_code = '''
        tell application "System Events"
            set allTitles to {}
            set visibleProcesses to (processes where background only is false)
            repeat with proc in visibleProcesses
                try
                    tell proc
                        repeat with w in windows
                            try
                                set title of w to name of w
                                if title of w is not "" then
                                    set end of allTitles to title of w
                                end if
                            on error
                                -- Ignore windows that might not have a title or are inaccessible
                            end try
                        end repeat
                    end tell
                on error
                    -- Ignore processes that might not have a window or are inaccessible
                end try
            end repeat
            return allTitles
        end tell
        '''

        result = self._execute_applescript(applescript_code)

        if result["success"]:
            output_str = result["output"]
            titles = []
            if output_str:
                # AppleScript returns lists like {"Title1", "Title2", ...}
                # We need to parse this into a Python list.
                # Handle cases with no titles or malformed output.
                if output_str.startswith("{") and output_str.endswith("}"):
                    # Split by '", "' and then strip quotes from each element.
                    # This handles cases with single/multiple titles correctly.
                    titles_raw = output_str[1:-1].split('", "')
                    titles = [t.strip('"') for t in titles_raw if t.strip('"')]
                elif output_str: # Handle case where output is a single unquoted string (less common for lists)
                    titles.append(output_str)

            if titles:
                return {
                    "success": True,
                    "message": "All visible window titles retrieved.",
                    "titles": titles,
                }
            else:
                return {
                    "success": False,
                    "message": "No visible window titles found.",
                    "titles": [],
                }
        else:
            return {
                "success": False,
                "message": f"Error retrieving all window titles: {result['error']}",
                "titles": None,
            }

# Example Usage (optional, for testing purposes)
if __name__ == "__main__":
    # This part will only run when the script is executed directly, not imported.
    try:
        reader = ScreenReader()

        print("--- Reading all screen text ---")
        result_all = reader.read_screen_text()
        print(f"Success: {result_all['success']}")
        print(f"Message: {result_all['message']}")
        if result_all.get('text'):
            print(f"Text: {result_all['text'][:300]}...") # Print first 300 chars for brevity

        print("\n--- Reading focused element text ---")
        result_focused = reader.read_focused_element_text()
        print(f"Success: {result_focused['success']}")
        print(f"Message: {result_focused['message']}")
        if result_focused.get('text'):
            print(f"Text: {result_focused['text']}")

        print("\n--- Reading frontmost window title ---")
        result_frontmost = reader.read_window_title()
        print(f"Success: {result_frontmost['success']}")
        print(f"Message: {result_frontmost['message']}")
        if result_frontmost.get('title'):
            print(f"Title: {result_frontmost['title']}")

        print("\n--- Reading specific window title (e.g., Finder) ---")
        # You might need to adjust "Finder" based on your active applications
        # Or try "Google Chrome", "TextEdit", etc.
        result_finder = reader.read_window_title("Finder")
        print(f"Success: {result_finder['success']}")
        print(f"Message: {result_finder['message']}")
        if result_finder.get('title'):
            print(f"Title: {result_finder['title']}")

        print("\n--- Reading title for a non-existent process ---")
        result_nonexistent = reader.read_window_title("NonExistentApp123")
        print(f"Success: {result_nonexistent['success']}")
        print(f"Message: {result_nonexistent['message']}")
        if result_nonexistent.get('title'):
            print(f"Title: {result_nonexistent['title']}")

        print("\n--- Getting all window titles ---")
        result_all_titles = reader.get_all_window_titles()
        print(f"Success: {result_all_titles['success']}")
        print(f"Message: {result_all_titles['message']}")
        if result_all_titles.get('titles'):
            print(f"Titles: {result_all_titles['titles']}")

    except RuntimeError as e:
        print(f"Initialization Error: {e}")
    except Exception as e:
        print(f"An error occurred during example usage: {e}")
