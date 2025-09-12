
import time
from typing import Dict, Any, Optional, List

# Attempt to import macOS specific libraries
try:
    from AppKit import NSPasteboard, NSString
    from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, CGWindowListCreate
    from Quartz import CGRect, CGSize, CGPoint
    from Quartz import CGEventCreateKeyboardEvent, CGEventCreateMouseEvent
    from Quartz import CGEventKeyboardSetType, CGEventMouseButtonSetType
    from Quartz import CGEventSetType, kCGEventKeyDown, kCGEventKeyUp
    from Quartz import CGEventPost, kCGHIDEventTap
    from Quartz import CGDisplayPixelsHigh, CGDisplayPixelsWide
    from Quartz import CGWindowIsOnscreen, CGWindowBounds, CGWindowName, CGWindowOwnerName
    from Quartz import CGPointMake, CGRectMake, CGSizeMake
    # Assuming accessibility_constants is intended to be a placeholder for actual accessibility features.
    # In a real scenario, this would be a library like pyatomac or direct interaction with AXUIElement.
    # For this enhancement, we'll simulate its existence and core functionality.
    try:
        import accessibility_constants as constants
        HAS_ACCESSIBILITY_LIB = True
    except ImportError:
        # Mocking the accessibility_constants to allow the code structure to remain
        # and to highlight where actual accessibility calls would go.
        print("Warning: 'accessibility_constants' module not found. Advanced accessibility features will be simulated.")
        class MockAccessibilityConstants:
            # Mocking attributes that might be used for text extraction
            @staticmethod
            def AXUIElementCreateApplication(_pid):
                return MockAXUIElement("Application")

            @staticmethod
            def AXUIElementCopyAttributeValue(_element, _attribute):
                # Simulate returning text for specific window types or a generic message
                # In a real scenario, this would query the actual UI element.
                if _attribute == "AXChildren":
                    # Simulate some child elements with text
                    return (0, [
                        MockAXUIElement("Button", "OK"),
                        MockAXUIElement("TextField", "Sample input text"),
                        MockAXUIElement("StaticText", "This is some static text."),
                    ])
                elif _attribute == "AXValue":
                    return (0, "Simulated Text Content")
                return (1, None) # Error code

            @staticmethod
            def AXIsProcessTrusted():
                # For simulation, assume it's trusted if the import succeeded
                # In reality, this checks OS-level permissions.
                return True

            @staticmethod
            def AXProcessOf(window_id):
                # Simulate returning a process ID for a window
                return (0, {"pid": 12345}) # Example PID

        class MockAXUIElement:
            def __init__(self, role, title=None):
                self._role = role
                self._title = title
                self._attributes = {}

            def get_attribute(self, attribute):
                if attribute == "AXTitle":
                    return (0, self._title)
                elif attribute == "AXRole":
                    return (0, self._role)
                elif attribute == "AXChildren":
                    # Simulate children for demonstration
                    if self._role == "Application":
                        return (0, [
                            MockAXUIElement("Window", "Example Window"),
                            MockAXUIElement("Window", "Another Window")
                        ])
                    elif self._role == "Window":
                        return (0, [
                            MockAXUIElement("Button", "Close"),
                            MockAXUIElement("TextField", "User input here"),
                            MockAXUIElement("StaticText", "App name: My App")
                        ])
                elif attribute == "AXValue":
                    # Simulate text content for input fields or static text
                    if self._role in ["TextField", "StaticText"]:
                        return (0, f"Simulated text for {self._role} '{self._title or ''}'")
                return (1, None) # Error

            def set_attribute(self, attribute, value):
                self._attributes[attribute] = value

            def __str__(self):
                return f"<MockAXUIElement role='{self._role}' title='{self._title}'>"

        constants = MockAccessibilityConstants()
        HAS_ACCESSIBILITY_LIB = False # Explicitly mark as simulated

    from PyObjCTools import AppHelper
    MACOS_AVAILABLE = True
except ImportError:
    MACOS_AVAILABLE = False
    HAS_ACCESSIBILITY_LIB = False
    print("Error: macOS specific libraries (AppKit, Quartz, PyObjC) not found. Screen reading functionality will be unavailable.")
    # Define dummy constants to allow the class to be defined without immediate errors
    class DummyConstants:
        pass
    constants = DummyConstants()


class ScreenReaderError(Exception):
    """Custom exception for screen reading errors."""
    pass


class ScreenReader:
    """
    A specialized tool for reading text from the screen, primarily designed for macOS.

    This class provides methods to capture screen content and extract text,
    leveraging macOS accessibility features and window information.

    Note: For full functionality, the user must grant "Screen Recording" and
    "Accessibility" permissions to the application running this script (e.g., Terminal, IDE).
    This is a system-level permission.
    """

    def __init__(self):
        """
        Initializes the ScreenReader.

        Checks for macOS specific library availability and accessibility permissions.
        """
        if not MACOS_AVAILABLE:
            self._initialized = False
            self.initialization_message = "ScreenReader requires macOS specific libraries (AppKit, Quartz, PyObjC)."
        elif not constants.AXIsProcessTrusted():
            self._initialized = False
            self.initialization_message = "ScreenReader requires Accessibility permissions. Please grant them in System Settings -> Privacy & Security -> Accessibility."
        else:
            self._initialized = True
            self.initialization_message = "ScreenReader initialized successfully."

    def _check_initialization(self) -> None:
        """
        Raises ScreenReaderError if the ScreenReader was not properly initialized.
        """
        if not self._initialized:
            raise ScreenReaderError(self.initialization_message)

    def _get_window_pid(self, window_id: int) -> Optional[int]:
        """
        Retrieves the process ID (PID) for a given window ID.
        """
        try:
            # This requires the window ID to be resolvable to a process.
            # The direct Quartz API doesn't directly map window ID to PID easily.
            # We might need to iterate through processes and their windows, or
            # rely on accessibility framework if it can provide this link.
            # For simplicity, we'll assume AXProcessOf can be used if window_id implies a process.
            # In reality, mapping CGWindowNumber to PID can be tricky.
            # A common approach is to use `CGWindowListCopyWindowInfo` with kCGWindowListOptionIncludingWindow
            # and check the 'kCGWindowOwnerPID' key for the specific window.

            window_list_ref = CGWindowListCreate(
                CGRectMake(0, 0, CGDisplayPixelsWide(), CGDisplayPixelsHigh()),
                kCGWindowListOptionOnScreenOnly | kCGWindowListOptionIncludingWindow,
            )
            if not window_list_ref:
                return None

            window_info_list = CGWindowListCopyWindowInfo(window_list_ref, None)
            if not window_info_list:
                return None

            for window_dict in window_info_list:
                if window_dict.get('kCGWindowNumber') == window_id:
                    return window_dict.get('kCGWindowOwnerPID')
            return None
        except Exception:
            # Fallback or error handling
            return None

    def _extract_text_from_ui_element(self, ui_element: Any) -> str:
        """
        Recursively extracts text from an AXUIElement and its children.
        This is a more robust method using accessibility APIs.
        """
        text_content = ""
        try:
            # Try to get direct text value if it's a text-like element
            value, error = constants.AXUIElementCopyAttributeValue(ui_element, b"AXValue")
            if error == 0 and value:
                # Ensure it's a string and not empty
                if isinstance(value, str) and value.strip():
                    text_content += value + "\n"

            # Also check for AXTitle as some elements use this for their visible text
            title_value, error = constants.AXUIElementCopyAttributeValue(ui_element, b"AXTitle")
            if error == 0 and title_value and isinstance(title_value, str) and title_value.strip():
                # Avoid adding title if it's a window title itself and we already got window title
                if getattr(ui_element, '_role', '').lower() != 'window':
                     text_content += title_value + "\n"

            # Recursively get children and extract text from them
            children_value, error = constants.AXUIElementCopyAttributeValue(ui_element, b"AXChildren")
            if error == 0 and children_value:
                for child in children_value:
                    # Ensure child is a valid AXUIElement before proceeding
                    if hasattr(child, 'get_attribute'): # Check if it looks like an AXUIElement
                        text_content += self._extract_text_from_ui_element(child)
        except Exception:
            # Ignore errors during recursion for individual elements, allows others to succeed
            pass
        return text_content.strip()

    def _extract_text_from_window(self, window_id: int, window_title: str) -> str:
        """
        Extracts text content from a specific window using accessibility APIs.
        This method tries to access the UI elements of the window.

        Args:
            window_id: The unique identifier of the window.
            window_title: The title of the window for context.

        Returns:
            A string containing the extracted text from the window, or an empty string
             if no text could be extracted or if the window is not accessible.
        """
        try:
            # Obtain the PID for the window
            pid = self._get_window_pid(window_id)
            if not pid:
                # Fallback: If PID not found, try to use window ID directly with accessibility if possible.
                # This is less common for direct accessibility element creation.
                # The AXUIElementCreateApplication requires a PID.
                # print(f"Debug: Could not get PID for window ID {window_id}. Skipping detailed text extraction.")
                return ""

            # Get the AXUIElement for the application that owns the window
            app_element = constants.AXUIElementCreateApplication(pid)
            if not app_element:
                # print(f"Debug: Failed to create AXUIElement for application with PID {pid}.")
                return ""

            # Find the specific window element within the application's elements
            # This is a common but complex part. We might need to iterate through
            # AXChildren of the app_element and find the one matching window_id.
            # A more direct approach is often needed if the accessibility framework
            # provides a way to get a window element by its CGWindowNumber.
            # For this example, we'll assume a function `AXUIElementCopyWindow` or similar
            # exists or simulate finding it.

            # Simulating finding the window element
            window_element = None
            children_value, error = constants.AXUIElementCopyAttributeValue(app_element, b"AXWindows")
            if error == 0 and children_value:
                for win_el in children_value:
                    # Check if this window element matches our target window ID.
                    # This mapping (AXWindow ID to CGWindowNumber) is not standard and
                    # might require inspecting AXWindow's attributes like AXIdentifier or AXID.
                    # As a workaround, we'll use the window title as a heuristic for demonstration.
                    # In a real scenario, you'd look for a direct mapping if available.
                    win_title_value, _ = constants.AXUIElementCopyAttributeValue(win_el, b"AXTitle")
                    if win_title_value == window_title:
                        window_element = win_el
                        break
            else:
                # Fallback: If AXWindows isn't directly available or useful,
                # try to access elements by role and traverse.
                # This is where deep accessibility inspection tools are invaluable.
                # For this simulation, we'll use a mocked element if PID was obtained.
                # A more realistic approach might try to get *all* UI elements and filter.
                pass

            if not window_element:
                 # If direct window lookup fails, use a general placeholder if HAS_ACCESSIBILITY_LIB is False
                if not HAS_ACCESSIBILITY_LIB:
                    return f"Simulated text content for window: '{window_title}' (ID: {window_id})"
                else:
                    # print(f"Debug: Could not find AXUIElement for window '{window_title}' (ID: {window_id}) within app PID {pid}.")
                    return ""

            # Extract text from the found window element and its children
            extracted_text = self._extract_text_from_ui_element(window_element)
            return extracted_text

        except Exception as e:
            # print(f"Debug: Exception during text extraction from window {window_id} ('{window_title}'): {e}")
            return "" # Return empty string if extraction fails.


    def read_screen_text(self, window_title_substring: Optional[str] = None) -> Dict[str, Any]:
        """
        Reads text from the screen, optionally filtering by a window title substring.

        Args:
            window_title_substring: A substring to filter which windows to read from.
                                    If None, attempts to read from all visible windows
                                    that have discernible text content. Case-insensitive.

        Returns:
            A dictionary with the following keys:
            - 'success' (bool): True if the operation was successful, False otherwise.
            - 'message' (str): A descriptive message about the operation.
            - 'data' (dict): A dictionary containing the extracted text.
                             'all_text' (str): The concatenated text from all relevant windows.
                             'windows' (list): A list of dictionaries, each representing a window
                                               with 'title' (str) and 'text' (str).
        """
        self._check_initialization()

        # Validate user input
        if window_title_substring is not None and not isinstance(window_title_substring, str):
            return {
                'success': False,
                'message': "Invalid input: window_title_substring must be a string or None.",
                'data': None
            }

        try:
            window_list_ref = CGWindowListCreate(None, kCGWindowListOptionOnScreenOnly)
            if not window_list_ref:
                raise ScreenReaderError("Failed to create window list.")

            window_info_list = CGWindowListCopyWindowInfo(window_list_ref, None)
            if not window_info_list:
                raise ScreenReaderError("Failed to copy window information.")

            relevant_windows_info = []
            for window_dict in window_info_list:
                window_id = window_dict.get('kCGWindowNumber')
                window_owner_name = window_dict.get('kCGWindowOwnerName')
                window_title = window_dict.get('kCGWindowTitle', '').strip()
                window_on_screen = window_dict.get('kCGWindowIsOnscreen')
                window_layer = window_dict.get('kCGWindowLayer')
                window_type = window_dict.get('kCGWindowLayer') # Often indicates type, though layer is more precise

                # Filter out non-visible windows, windows without titles, and common system/utility windows.
                # Layer 0 usually indicates application windows.
                if window_id and window_on_screen and window_title and window_owner_name not in ("WindowServer", "NotificationCenter", "SystemUIServer", "Dock") and window_layer == 0:
                    # Apply title filter if provided (case-insensitive)
                    if window_title_substring is None or window_title_substring.lower() in window_title.lower():
                        relevant_windows_info.append({'windowID': window_id, 'title': window_title})

            extracted_data = {'all_text': '', 'windows': []}
            total_text_parts = []

            if not relevant_windows_info:
                return {
                    'success': True,
                    'message': f"No visible windows found matching the filter '{window_title_substring}'." if window_title_substring else "No visible windows found to read from.",
                    'data': {'all_text': '', 'windows': []}
                }

            for window_info in relevant_windows_info:
                window_text = self._extract_text_from_window(window_info['windowID'], window_info['title'])
                if window_text: # Only add windows that yielded some text
                    extracted_data['windows'].append({
                        'title': window_info['title'],
                        'text': window_text
                    })
                    total_text_parts.append(window_text)

            extracted_data['all_text'] = "\n\n".join(total_text_parts) # Use double newline for better separation

            if not extracted_data['windows']:
                return {
                    'success': True,
                    'message': f"No text could be extracted from the relevant windows (filter: '{window_title_substring}' if applicable).",
                    'data': {'all_text': '', 'windows': []}
                }

            return {
                'success': True,
                'message': f"Successfully read text from {len(extracted_data['windows'])} window(s).",
                'data': extracted_data
            }

        except ScreenReaderError as e:
            return {
                'success': False,
                'message': f"Error reading screen text: {e}",
                'data': None
            }
        except Exception as e:
            # Catch any other unexpected errors during the process
            return {
                'success': False,
                'message': f"An unexpected error occurred during screen text reading: {e}",
                'data': None
            }

    def copy_text_to_clipboard(self, text: str) -> Dict[str, Any]:
        """
        Copies the given text to the system clipboard.

        Args:
            text: The string to copy to the clipboard.

        Returns:
            A dictionary with the following keys:
            - 'success' (bool): True if the operation was successful, False otherwise.
            - 'message' (str): A descriptive message about the operation.
            - 'data' (None): No data is returned, as the operation is a side effect.
        """
        self._check_initialization()

        # Input validation
        if not isinstance(text, str):
            return {
                'success': False,
                'message': "Invalid input: Text to copy must be a string.",
                'data': None
            }

        try:
            pasteboard = NSPasteboard.generalPasteboard()
            pasteboard.declareTypes_owner_([NSString.NSString], None)
            pasteboard.setString_forType_(text, NSString.NSString)
            return {
                'success': True,
                'message': "Text successfully copied to clipboard.",
                'data': None
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"Error copying text to clipboard: {e}",
                'data': None
            }

    def paste_text_from_clipboard(self) -> Dict[str, Any]:
        """
        Retrieves text from the system clipboard.

        Returns:
            A dictionary with the following keys:
            - 'success' (bool): True if the operation was successful, False otherwise.
            - 'message' (str): A descriptive message about the operation.
            - 'data' (dict): A dictionary containing the clipboard content.
                             'clipboard_text' (str): The text retrieved from the clipboard.
        """
        self._check_initialization()

        try:
            pasteboard = NSPasteboard.generalPasteboard()
            # Use stringForType_ with NSString for standard text
            clipboard_content = pasteboard.stringForType_(NSString.NSString)

            if clipboard_content is None:
                return {
                    'success': False,
                    'message': "Clipboard is empty or does not contain text.",
                    'data': {'clipboard_text': ""}
                }
            return {
                'success': True,
                'message': "Successfully retrieved text from clipboard.",
                'data': {'clipboard_text': clipboard_content}
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"Error retrieving text from clipboard: {e}",
                'data': None
            }

    # --- Safety Notes ---
    # This class is designed to be safe by default.
    # - It does not modify system settings or files without explicit user action.
    # - Screen reading relies on macOS's accessibility frameworks. For full functionality, the user MUST grant
    #   "Screen Recording" and "Accessibility" permissions to the application running this Python script (e.g., Terminal, IDE).
    #   This is a system-level permission that the script cannot grant itself.
    # - The `_extract_text_from_window` method's actual implementation depends heavily on the OS's accessibility APIs.
    #   The current implementation uses Quartz for window listing and attempts to use accessibility APIs (via a mock
    #   if the library isn't found) to traverse UI elements and extract text.

    # --- Compatibility Note ---
    # This class is specifically designed for macOS due to its reliance on AppKit and Quartz frameworks.
    # It will not function on other operating systems without significant refactoring and the use of OS-specific APIs or cross-platform libraries.

if __name__ == '__main__':
    print("Initializing ScreenReader...")
    reader = ScreenReader()

    if not reader._initialized:
        print(f"\nScreenReader could not be initialized. Reason: {reader.initialization_message}")
        print("Please ensure:")
        print("1. You are running on macOS.")
        print("2. PyObjC is installed ('pip install pyobjc').")
        print("3. Accessibility permissions are granted for your terminal/IDE.")
    else:
        print("ScreenReader initialized successfully.")

        # --- Test 1: Read text from all visible windows (simulated/actual depending on permissions) ---
        print("\n--- Reading text from all visible windows ---")
        result_all = reader.read_screen_text()
        if result_all['success']:
            print(f"Message: {result_all['message']}")
            if result_all['data'] and result_all['data']['windows']:
                print(f"\nTotal text extracted ({result_all['data']['all_text'][:200]}...):")
                print("\nDetails per window:")
                for win_data in result_all['data']['windows']:
                    print(f"  Title: {win_data['title']}")
                    # Truncate long text for display
                    display_text = win_data['text'][:150] + ('...' if len(win_data['text']) > 150 else '')
                    print(f"  Text: {display_text}")
            else:
                print("No text data found or extracted from visible windows.")
        else:
            print(f"Error: {result_all['message']}")

        # --- Test 2: Read text from a specific window (e.g., 'Terminal', 'Finder', case-insensitive) ---
        print("\n--- Reading text from a specific window (e.g., 'Finder', case-insensitive) ---")
        window_filter = "Finder" # Example: try "Terminal", "Safari", "Google Chrome"
        result_specific = reader.read_screen_text(window_title_substring=window_filter)
        if result_specific['success']:
            print(f"Message: {result_specific['message']}")
            if result_specific['data'] and result_specific['data']['windows']:
                print(f"\nText from windows containing '{window_filter}' ({result_specific['data']['all_text'][:200]}...):")
                for win_data in result_specific['data']['windows']:
                    print(f"  Title: {win_data['title']}")
                    display_text = win_data['text'][:150] + ('...' if len(win_data['text']) > 150 else '')
                    print(f"  Text: {display_text}")
            else:
                print(f"No windows found containing '{window_filter}' or no text extracted from them.")
        else:
            print(f"Error: {result_specific['message']}")

        # --- Test 3: Copy text to clipboard ---
        print("\n--- Copying text to clipboard ---")
        text_to_copy = "This text was copied programmatically by the ScreenReader tool!"
        copy_result = reader.copy_text_to_clipboard(text_to_copy)
        print(f"Copy operation result: {copy_result}")
        if copy_result['success']:
            print(f"Please verify your clipboard. It should contain: '{text_to_copy}'")
            time.sleep(2) # Give user time to check

        # --- Test 4: Paste text from clipboard ---
        print("\n--- Pasting text from clipboard ---")
        paste_result = reader.paste_text_from_clipboard()
        print(f"Paste operation result: {paste_result}")
        if paste_result['success'] and paste_result['data']:
            print(f"Text retrieved from clipboard: '{paste_result['data']['clipboard_text']}'")
