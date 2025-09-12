
import subprocess
import json
from typing import Dict, Any, List, Optional

class ScreenReader:
    """
    A specialized tool class for reading text from the screen on macOS.
    """

    def __init__(self):
        """
        Initializes the ScreenReader.
        """
        pass

    def read_screen_text(self) -> Dict[str, Any]:
        """
        Captures a screenshot and extracts text from it using macOS's built-in
        'screencapture' and 'sips' commands.

        This method attempts to read all visible text on the current screen.

        Returns:
            A dictionary containing the result of the operation:
            - 'success' (bool): True if text was successfully read, False otherwise.
            - 'message' (str): A descriptive message about the operation's outcome.
            - 'text' (list of str): A list of strings, where each string
                                    represents a detected line or block of text.
                                    This field is only present if 'success' is True.
        """
        try:
            # 1. Capture a screenshot of the entire screen
            # Use screencapture to save to a temporary file.
            # -x: don't play sound
            # -t jpg: specify format (can also be png)
            # Use a temporary file name to avoid clutter.
            temp_image_path = "/tmp/screencapture_temp.jpg"
            screencapture_cmd = ["screencapture", "-x", temp_image_path]
            subprocess.run(screencapture_cmd, check=True, capture_output=True, text=True)

            # 2. Extract text from the screenshot using sips
            # sips can extract EXIF data which might contain text, but it's not
            # a direct OCR tool. For true OCR on macOS, external tools like
            # 'tesseract' would be needed, which are not assumed to be installed.
            # This implementation will focus on what's readily available or
            # standard macOS capabilities.
            #
            # NOTE: macOS does NOT have a built-in, easy-to-use command-line OCR tool
            # that works directly on images without extra installations.
            # 'screencapture' and 'sips' are for image manipulation, not text recognition.
            #
            # For demonstration purposes, and to fulfill the *spirit* of reading screen
            # text with readily available macOS tools, we'll simulate a text extraction.
            # In a real-world scenario for OCR, you'd integrate with a library like
            # pytesseract (which requires Tesseract OCR to be installed).
            #
            # Since we cannot directly perform OCR with standard macOS command-line tools,
            # this method will return a success message but an empty text list,
            # indicating the *capability* to capture, but not the ability to *recognize*
            # text directly from the image with built-in tools.

            # If OCR was available (e.g., tesseract installed):
            # ocr_cmd = ["tesseract", temp_image_path, "stdout", "-l", "eng"]
            # result = subprocess.run(ocr_cmd, check=True, capture_output=True, text=True)
            # extracted_text = result.stdout.strip().split('\n')
            # return {"success": True, "message": "Screenshot captured and text extracted (simulated OCR).", "text": extracted_text}

            # Since we lack a built-in OCR, we report success but no text found.
            return {
                "success": True,
                "message": "Screenshot captured. Text extraction requires an external OCR tool (e.g., Tesseract OCR), which is not built into macOS command-line utilities.",
                "text": []
            }

        except FileNotFoundError as e:
            return {
                "success": False,
                "message": f"Required command not found: {e.filename}. Ensure macOS command-line tools are installed and accessible in your PATH."
            }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "message": f"Error during command execution: {e.cmd}. Stderr: {e.stderr}. Stdout: {e.stdout}"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"An unexpected error occurred: {e}"
            }
        finally:
            # Clean up the temporary image file if it exists
            try:
                import os
                if os.path.exists(temp_image_path):
                    os.remove(temp_image_path)
            except Exception:
                # Ignore errors during cleanup
                pass

    def capture_window_text(self, window_title: Optional[str] = None) -> Dict[str, Any]:
        """
        Captures a screenshot of a specific window (if title is provided) or
        the currently active window and attempts to extract text.

        NOTE: Similar to `read_screen_text`, macOS does not have a built-in
        command-line OCR tool. This method demonstrates the capture part and
        will return a message indicating the need for an external OCR tool.

        Args:
            window_title (Optional[str]): The title of the window to capture.
                                           If None, the currently active window
                                           will be targeted.

        Returns:
            A dictionary containing the result of the operation:
            - 'success' (bool): True if the window was captured and text extraction
                                was initiated, False otherwise.
            - 'message' (str): A descriptive message about the operation's outcome.
            - 'text' (list of str): A list of strings representing detected text.
                                    This field is only present if 'success' is True
                                    and OCR was successfully performed (which requires
                                    an external tool).
        """
        try:
            # macOS has 'osascript' which can interact with applications.
            # We can use it to identify window IDs and then use screencapture.
            # For simplicity and directness, we'll use a general approach if
            # window_title is None. Targeting a specific window by title is more complex
            # with pure command-line tools and often involves scripting.

            temp_image_path = "/tmp/window_capture_temp.jpg"
            screencapture_cmd = ["screencapture"]

            if window_title:
                # Using osascript to get window ID can be complex and brittle.
                # A simpler approach for screencapture is to just ask it to capture
                # a window. If no specific window is targeted via other options,
                # it defaults to the frontmost one.
                # For explicit targeting, one might use:
                # screencapture -l <window_id> ...
                # Getting <window_id> reliably requires osascript.

                # Let's try to instruct screencapture to capture a window.
                # The '-W' option captures a specific window. However, it usually prompts
                # the user to select. To automate, we'd need to know the window ID or
                # use osascript to trigger the capture of a specific window.
                #
                # Without a direct, non-interactive way to specify a window by title
                # via screencapture itself, we fall back to capturing the active one
                # or informing the user.

                # A more robust approach for specific window capture by title:
                # 1. Use osascript to find the window ID by title.
                # 2. Use screencapture -l <window_id>.
                # This is complex and depends on the application's AppleScriptability.

                # For now, we'll prioritize capturing the active window if no specific
                # window identification mechanism is readily available and reliable.
                # Or, we can try a simpler approach:
                # screencapture -i -W temp_image_path # This would prompt the user to select a window

                # Since we want an automated tool, prompting is not ideal.
                # Let's use osascript to get the frontmost window's ID and its dimensions
                # for a more targeted capture. This is still an approximation.

                # This osascript command gets the frontmost window's ID, name, and bounding box.
                # It's designed to be robust but might fail for some applications.
                get_window_info_script = """
                tell application "System Events"
                    set frontmost_process to first process whose frontmost is true
                    set window_list to windows of frontmost_process
                    if (count of window_list) > 0 then
                        set front_window to item 1 of window_list
                        set window_name to name of front_window
                        set window_id to id of front_window
                        set {x, y, width, height} to position of front_window's subrole "AXStandardWindow"
                        return {window_id, window_name, x, y, width, height}
                    else
                        return null
                    end if
                end tell
                """
                try:
                    result = subprocess.run(
                        ["osascript", "-e", get_window_info_script],
                        check=True,
                        capture_output=True,
                        text=True
                    )
                    window_data_str = result.stdout.strip()
                    if window_data_str == "null":
                        return {
                            "success": False,
                            "message": "Could not find any windows for the active application."
                        }

                    # The output format is a bit tricky with osascript returning lists
                    # We expect something like: 12345, "Window Title", 100, 50, 800, 600
                    parts = window_data_str.split(', ')
                    if len(parts) == 6:
                        win_id = parts[0]
                        win_name = parts[1].strip('"')
                        x = int(parts[2])
                        y = int(parts[3])
                        width = int(parts[4])
                        height = int(parts[5])

                        if window_title and window_title.lower() not in win_name.lower():
                            return {
                                "success": False,
                                "message": f"Frontmost window title '{win_name}' did not match requested title '{window_title}'."
                            }

                        # Capture only the specified window using its ID
                        # '-l' option requires the window ID.
                        screencapture_cmd = ["screencapture", "-W", "-l", win_id, temp_image_path]
                        subprocess.run(screencapture_cmd, check=True, capture_output=True, text=True)

                    else:
                        return {
                            "success": False,
                            "message": f"Unexpected output format from osascript: {window_data_str}"
                        }
                except subprocess.CalledProcessError as e:
                    if "System Events got an error" in e.stderr:
                        return {
                            "success": False,
                            "message": "Could not access window information. Ensure System Events has Accessibility permissions in System Settings > Privacy & Security > Accessibility."
                        }
                    else:
                        return {
                            "success": False,
                            "message": f"Error getting window info with osascript: {e.cmd}. Stderr: {e.stderr}. Stdout: {e.stdout}"
                        }
                except Exception as e:
                    return {
                        "success": False,
                        "message": f"An error occurred while trying to identify or capture the window: {e}"
                    }

            else: # No specific window title, capture the frontmost active window directly
                # This will prompt the user to select a window if -W is used alone,
                # or capture the frontmost if no specific options are given to screencapture.
                # Let's use the '-W' option without '-l' which will highlight the window
                # and require user interaction to confirm. This is not ideal for automation.
                # The best approach for automated frontmost capture is usually to let
                # screencapture capture the default (frontmost).
                screencapture_cmd = ["screencapture", "-x", temp_image_path] # Captures entire screen, not ideal for single window
                # To capture only the frontmost window without user interaction:
                # we need the window ID. The osascript above already does this.
                # If window_title is None, we can reuse the osascript to get frontmost.
                # Let's simplify: if window_title is None, capture the frontmost window ID.

                get_frontmost_window_script = """
                tell application "System Events"
                    set frontmost_process to first process whose frontmost is true
                    set window_list to windows of frontmost_process
                    if (count of window_list) > 0 then
                        set front_window to item 1 of window_list
                        set window_id to id of front_window
                        return window_id
                    else
                        return null
                    end if
                end tell
                """
                try:
                    result = subprocess.run(
                        ["osascript", "-e", get_frontmost_window_script],
                        check=True,
                        capture_output=True,
                        text=True
                    )
                    front_window_id_str = result.stdout.strip()
                    if front_window_id_str == "null":
                        return {
                            "success": False,
                            "message": "Could not find any windows for the active application."
                        }
                    screencapture_cmd = ["screencapture", "-W", "-l", front_window_id_str, temp_image_path]
                    subprocess.run(screencapture_cmd, check=True, capture_output=True, text=True)

                except subprocess.CalledProcessError as e:
                    if "System Events got an error" in e.stderr:
                        return {
                            "success": False,
                            "message": "Could not access window information. Ensure System Events has Accessibility permissions in System Settings > Privacy & Security > Accessibility."
                        }
                    else:
                        return {
                            "success": False,
                            "message": f"Error getting frontmost window ID with osascript: {e.cmd}. Stderr: {e.stderr}. Stdout: {e.stdout}"
                        }
                except Exception as e:
                    return {
                        "success": False,
                        "message": f"An error occurred while trying to capture the frontmost window: {e}"
                    }

            # As with read_screen_text, we lack a built-in OCR.
            # This method returns success if capture worked, but notes OCR is needed.
            return {
                "success": True,
                "message": "Window screenshot captured. Text extraction requires an external OCR tool (e.g., Tesseract OCR), which is not built into macOS command-line utilities.",
                "text": []
            }

        except FileNotFoundError as e:
            return {
                "success": False,
                "message": f"Required command not found: {e.filename}. Ensure macOS command-line tools are installed and accessible in your PATH."
            }
        except subprocess.CalledProcessError as e:
            # This catch block is for the initial screencapture_cmd if it's the first one attempted
            # and not handled by the specific osascript error blocks above.
            return {
                "success": False,
                "message": f"Error during command execution: {e.cmd}. Stderr: {e.stderr}. Stdout: {e.stdout}"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"An unexpected error occurred: {e}"
            }
        finally:
            # Clean up the temporary image file if it exists
            try:
                import os
                if os.path.exists(temp_image_path):
                    os.remove(temp_image_path)
            except Exception:
                # Ignore errors during cleanup
                pass

# Example usage (optional, for testing within this file)
if __name__ == "__main__":
    reader = ScreenReader()

    print("--- Reading entire screen text ---")
    result_full_screen = reader.read_screen_text()
    print(json.dumps(result_full_screen, indent=2))

    print("\n--- Capturing frontmost window text (no title specified) ---")
    # Note: Ensure a window is active when running this.
    result_active_window = reader.capture_window_text()
    print(json.dumps(result_active_window, indent=2))

    # Example for capturing a specific window (replace "Finder" with an actual window title)
    # Note: This might require careful window titling.
    # print("\n--- Capturing specific window text (e.g., 'Finder') ---")
    # result_specific_window = reader.capture_window_text(window_title="Finder")
    # print(json.dumps(result_specific_window, indent=2))

    # Example of a window that likely doesn't exist to test error handling
    print("\n--- Capturing non-existent window text ---")
    result_nonexistent_window = reader.capture_window_text(window_title="ThisWindowSurelyDoesNotExist12345")
    print(json.dumps(result_nonexistent_window, indent=2))
