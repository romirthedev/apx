import pytesseract
from PIL import Image, UnidentifiedImageError
import io
import os
from typing import Dict, Any, Optional, Tuple

# Conditional import for mss
try:
    import mss
    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False
    print("Warning: 'mss' library not found. Screenshot capturing will be disabled.")
    # Define a placeholder for mss if it's not available to avoid NameError
    class MockMSS:
        def __enter__(self): return self
        def __exit__(self, exc_type, exc_val, exc_tb): pass
        def grab(self, monitor_area): raise NotImplementedError("mss library is not available.")
        @property
        def monitors(self): raise NotImplementedError("mss library is not available.")
        class ScreenShotError(Exception): pass
    mss = MockMSS()


class ScreenshotTextExtractor:
    """
    A specialized tool class for taking screenshots and extracting text from them.
    Designed for compatibility across different operating systems, with specific
    considerations for macOS Tesseract installation paths.
    """

    def __init__(self, tesseract_cmd: Optional[str] = None):
        """
        Initializes the ScreenshotTextExtractor.

        Args:
            tesseract_cmd: Optional path to the Tesseract executable.
                           If not provided, Tesseract will be searched in the system's PATH.
                           On macOS, Tesseract is typically installed via Homebrew,
                           and its path might be something like '/opt/homebrew/bin/tesseract'
                           for Apple Silicon or '/usr/local/bin/tesseract' for Intel Macs.
        """
        self.tesseract_available: bool = False
        self.monitor_selection: Optional[Dict[str, int]] = None
        self.init_tesseract(tesseract_cmd)

    def init_tesseract(self, tesseract_cmd: Optional[str]) -> None:
        """
        Initializes Tesseract path and checks for its availability.
        """
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
            try:
                pytesseract.get_tesseract_version()
                self.tesseract_available = True
            except pytesseract.TesseractNotFoundError:
                print(f"Warning: Provided Tesseract command '{tesseract_cmd}' not found. Tesseract may not be available.")
            except Exception as e:
                print(f"Warning: Error initializing Tesseract with provided command '{tesseract_cmd}': {e}")
        else:
            # Attempt to find tesseract if not specified
            common_paths = [
                '/opt/homebrew/bin/tesseract',  # macOS Apple Silicon
                '/usr/local/bin/tesseract',     # macOS Intel, Linux
                '/usr/bin/tesseract'            # Linux
            ]
            found_path = None
            for path in common_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    found_path = path
                    break

            if found_path:
                try:
                    pytesseract.get_tesseract_version()
                    self.tesseract_available = True
                    print(f"Tesseract found at: {found_path}")
                except pytesseract.TesseractNotFoundError:
                    print(f"Warning: Tesseract found at '{found_path}' but executable is not valid or accessible.")
                except Exception as e:
                    print(f"Warning: Error initializing Tesseract from '{found_path}': {e}")
            else:
                try:
                    # Let pytesseract try to find it in PATH as a last resort
                    pytesseract.get_tesseract_version()
                    self.tesseract_available = True
                    print("Tesseract found in system PATH.")
                except pytesseract.TesseractNotFoundError:
                    print("Warning: Tesseract OCR is not installed or not found in your system's PATH. "
                          "Please install Tesseract (e.g., via Homebrew: 'brew install tesseract') "
                          "or provide the correct path to its executable using the 'tesseract_cmd' argument.")
                except Exception as e:
                    print(f"Warning: An unexpected error occurred while checking for Tesseract in PATH: {e}")


    def _validate_tesseract(self) -> Dict[str, Any]:
        """
        Internal method to check if Tesseract OCR is available.

        Returns:
            A dictionary indicating the success of the Tesseract check.
        """
        if not self.tesseract_available:
            return {
                "success": False,
                "message": "Tesseract OCR is not available. Please install Tesseract or specify the correct path."
            }
        return {"success": True, "message": "Tesseract OCR is available."}

    def _validate_region(self, top: int, left: int, width: int, height: int) -> bool:
        """
        Validates the input for a monitor region.
        """
        if not all(isinstance(arg, int) for arg in [top, left, width, height]):
            return False
        if top < 0 or left < 0 or width <= 0 or height <= 0:
            return False
        return True

    def set_monitor_region(self, top: int, left: int, width: int, height: int) -> Dict[str, Any]:
        """
        Sets a specific region of the screen to capture.

        Args:
            top: The top coordinate of the region.
            left: The left coordinate of the region.
            width: The width of the region.
            height: The height of the region.

        Returns:
            A dictionary indicating the success of setting the monitor region.
        """
        if not self._validate_region(top, left, width, height):
            return {
                "success": False,
                "message": "Invalid input for monitor region. All values must be non-negative integers, "
                           "and width/height must be positive."
            }

        self.monitor_selection = {"top": top, "left": left, "width": width, "height": height}
        return {
            "success": True,
            "message": "Monitor region set successfully.",
            "region": self.monitor_selection
        }

    def clear_monitor_region(self) -> Dict[str, Any]:
        """
        Clears any previously set monitor region, causing the tool to capture the entire screen.

        Returns:
            A dictionary indicating the success of clearing the monitor region.
        """
        self.monitor_selection = None
        return {"success": True, "message": "Monitor region cleared. Entire screen will be captured."}

    def _capture_screenshot(self) -> Dict[str, Any]:
        """
        Captures the screenshot based on the configured monitor region.

        Returns:
            A dictionary containing the screenshot image data (as bytes) on success,
            or an error message on failure.
        """
        if not MSS_AVAILABLE:
            return {"success": False, "message": "'mss' library is not available. Cannot capture screenshots."}

        try:
            with mss.mss() as sct:
                if self.monitor_selection:
                    monitor_area = self.monitor_selection
                else:
                    # Use the primary monitor if no region is set.
                    # mss.monitors[0] is the virtual desktop, mss.monitors[1] is the primary monitor.
                    if len(sct.monitors) < 2:
                        return {"success": False, "message": "No primary monitor detected."}
                    monitor_area = sct.monitors[1] # Default to primary monitor

                # Ensure monitor dimensions are valid for grabbing
                if monitor_area["width"] <= 0 or monitor_area["height"] <= 0:
                    return {
                        "success": False,
                        "message": f"Invalid monitor dimensions for capture: {monitor_area}. Ensure a valid region or monitor is selected."
                    }

                sct_img = sct.grab(monitor_area)

                # Convert to PIL Image
                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

                # Save to a byte buffer
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG')
                img_bytes = img_byte_arr.getvalue()

                return {
                    "success": True,
                    "message": "Screenshot captured successfully.",
                    "image_bytes": img_bytes,
                    "dimensions": {"width": img.width, "height": img.height}
                }
        except mss.ScreenShotError as e:
            return {"success": False, "message": f"Error capturing screenshot: {e}"}
        except Exception as e:
            return {"success": False, "message": f"An unexpected error occurred during screenshot capture: {e}"}

    def extract_text_from_screenshot(self) -> Dict[str, Any]:
        """
        Takes a screenshot and extracts text from it using Tesseract OCR.

        Returns:
            A dictionary containing the extracted text and other relevant information
            on success, or an error message on failure.
            On success, the dictionary will contain:
            - 'success': True
            - 'message': "Text extracted successfully."
            - 'text': The extracted text string.
            - 'image_bytes': The raw PNG bytes of the screenshot.
            - 'dimensions': Dictionary with 'width' and 'height' of the screenshot.
        """
        tesseract_check = self._validate_tesseract()
        if not tesseract_check["success"]:
            return tesseract_check

        if not MSS_AVAILABLE:
            return {"success": False, "message": "'mss' library is not available. Cannot capture screenshots."}

        screenshot_result = self._capture_screenshot()
        if not screenshot_result["success"]:
            return screenshot_result

        image_bytes = screenshot_result["image_bytes"]

        try:
            # Open image from bytes
            img = Image.open(io.BytesIO(image_bytes))

            # Extract text
            text = pytesseract.image_to_string(img)

            return {
                "success": True,
                "message": "Text extracted successfully.",
                "text": text,
                "image_bytes": image_bytes,
                "dimensions": screenshot_result.get("dimensions", {})
            }
        except UnidentifiedImageError:
            return {
                "success": False,
                "message": "Failed to open the captured image. The image data might be corrupted."
            }
        except pytesseract.TesseractNotFoundError:
            # This should ideally be caught by _validate_tesseract, but included as a safeguard.
            return {
                "success": False,
                "message": "Tesseract OCR executable not found. Ensure Tesseract is installed and in your PATH or specify its location."
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"An error occurred during text extraction: {e}"
            }

    def capture_and_save_screenshot(self, filepath: str) -> Dict[str, Any]:
        """
        Captures a screenshot and saves it to the specified file path.

        Args:
            filepath: The full path where the screenshot image should be saved.
                      Supported formats depend on PIL (e.g., PNG, JPG).

        Returns:
            A dictionary indicating the success of the operation.
        """
        if not filepath or not isinstance(filepath, str):
            return {"success": False, "message": "Invalid filepath provided. Please provide a valid string path."}

        if not MSS_AVAILABLE:
            return {"success": False, "message": "'mss' library is not available. Cannot capture screenshots."}

        screenshot_result = self._capture_screenshot()
        if not screenshot_result["success"]:
            return screenshot_result

        image_bytes = screenshot_result["image_bytes"]

        try:
            # Ensure the directory exists
            dir_name = os.path.dirname(filepath)
            if dir_name and not os.path.exists(dir_name):
                os.makedirs(dir_name)

            with open(filepath, "wb") as f:
                f.write(image_bytes)
            return {
                "success": True,
                "message": f"Screenshot saved successfully to {filepath}.",
                "filepath": filepath
            }
        except IOError as e:
            return {"success": False, "message": f"Error saving screenshot to {filepath}: {e}"}
        except Exception as e:
            return {"success": False, "message": f"An unexpected error occurred during saving: {e}"}

    def get_monitor_info(self) -> Dict[str, Any]:
        """
        Retrieves information about available monitors.

        Returns:
            A dictionary containing monitor information or an error message.
        """
        if not MSS_AVAILABLE:
            return {"success": False, "message": "'mss' library is not available. Cannot retrieve monitor information."}

        try:
            with mss.mss() as sct:
                monitors_info = []
                for i, monitor in enumerate(sct.monitors):
                    # Monitor 0 is the virtual desktop encompassing all displays.
                    # We are interested in individual physical monitors.
                    if i > 0:
                        monitors_info.append({
                            "id": i,
                            "name": f"Monitor {i}",
                            "top": monitor["top"],
                            "left": monitor["left"],
                            "width": monitor["width"],
                            "height": monitor["height"],
                            "is_primary": (i == 1) # Typically, monitor 1 is the primary
                        })
                if not monitors_info:
                    return {"success": False, "message": "No physical monitors detected."}
                return {"success": True, "message": "Monitor information retrieved.", "monitors": monitors_info}
        except Exception as e:
            return {"success": False, "message": f"Error retrieving monitor information: {e}"}


if __name__ == '__main__':
    # Example Usage (will only run if the script is executed directly)

    # --- IMPORTANT FOR macOS USERS AND OTHERS ---
    # You might need to explicitly set the path to tesseract if it's not in your PATH.
    # If you installed tesseract via Homebrew on an Apple Silicon Mac, it's likely:
    # tesseract_path = '/opt/homebrew/bin/tesseract'
    # For Intel Macs, it might be:
    # tesseract_path = '/usr/local/bin/tesseract'
    # If unsure, run `which tesseract` in your terminal.
    # If tesseract is in your PATH, you can leave tesseract_path as None.

    tesseract_path = None # Set this to the correct path if needed, e.g., '/opt/homebrew/bin/tesseract'

    extractor = ScreenshotTextExtractor(tesseract_cmd=tesseract_path)

    # Check Tesseract availability before proceeding
    if not extractor.tesseract_available:
        print("\n--- Tesseract OCR is not available. Please follow the instructions above to install or configure it. ---")
    
    if not MSS_AVAILABLE:
        print("\n--- 'mss' library is not available. Screenshot functionality is disabled. ---")

    if extractor.tesseract_available and MSS_AVAILABLE:
        # 1. Get monitor information
        print("--- Getting monitor information ---")
        monitor_info_result = extractor.get_monitor_info()
        if monitor_info_result["success"]:
            print(f"Message: {monitor_info_result['message']}")
            for monitor in monitor_info_result["monitors"]:
                print(f"  - {monitor['name']}: Width={monitor['width']}, Height={monitor['height']}, Primary={monitor['is_primary']}")
        else:
            print(f"Error: {monitor_info_result['message']}\n")

        # 2. Extract text from the entire screen
        print("\n--- Extracting text from entire screen ---")
        result_full_screen = extractor.extract_text_from_screenshot()
        if result_full_screen["success"]:
            print(f"Message: {result_full_screen['message']}")
            print(f"Extracted Text:\n'{result_full_screen['text'][:300]}...'\n") # Print first 300 chars
            # To save the image:
            save_result = extractor.capture_and_save_screenshot("fullscreen_capture.png")
            print(f"Save result: {save_result['message']}\n")
        else:
            print(f"Error: {result_full_screen['message']}\n")

        # 3. Set a specific region and extract text
        print("\n--- Extracting text from a specific region ---")
        # Define a region (e.g., a 400x300 rectangle starting at 100, 100 pixels from the top-left)
        # You might need to adjust these values based on your screen resolution and what you want to capture.
        # If you ran get_monitor_info, you can use those dimensions.
        # Example: for a 1920x1080 screen, a central area could be top=400, left=760, width=400, height=280
        region_top, region_left, region_width, region_height = 100, 100, 600, 400
        region_settings = extractor.set_monitor_region(top=region_top, left=region_left, width=region_width, height=region_height)
        print(f"Region set result: {region_settings['message']}")

        if region_settings["success"]:
            result_region = extractor.extract_text_from_screenshot()
            if result_region["success"]:
                print(f"Message: {result_region['message']}")
                print(f"Extracted Text (from region):\n'{result_region['text'][:300]}...'\n")
                # To save the image of the region:
                save_region_result = extractor.capture_and_save_screenshot("region_capture.png")
                print(f"Save region result: {save_region_result['message']}\n")
            else:
                print(f"Error: {result_region['message']}\n")
        else:
            print(f"Failed to set region: {region_settings['message']}\n")


        # 4. Clear the region and go back to full screen
        print("\n--- Clearing region and capturing full screen again ---")
        clear_result = extractor.clear_monitor_region()
        print(f"Clear region result: {clear_result['message']}")

        result_after_clear = extractor.extract_text_from_screenshot()
        if result_after_clear["success"]:
            print(f"Message: {result_after_clear['message']}")
            print(f"Extracted Text (after clear):\n'{result_after_clear['text'][:300]}...'\n")
        else:
            print(f"Error: {result_after_clear['message']}\n")

        # 5. Example of saving a screenshot to a specific directory
        print("\n--- Saving a screenshot to a specific directory ---")
        save_dir = "screenshots"
        save_filepath = os.path.join(save_dir, "my_screenshot_in_subdir.png")
        save_result_subdir = extractor.capture_and_save_screenshot(save_filepath)
        if save_result_subdir["success"]:
            print(f"Success: {save_result_subdir['message']}")
        else:
            print(f"Error: {save_result_subdir['message']}")

        # 6. Example of invalid input for region
        print("\n--- Testing invalid region input ---")
        invalid_region_result = extractor.set_monitor_region(top=-10, left=100, width=200, height=200)
        print(f"Invalid region test result: {invalid_region_result['message']}")
        invalid_region_result_2 = extractor.set_monitor_region(top=100, left=100, width=0, height=200)
        print(f"Invalid region test result 2: {invalid_region_result_2['message']}")