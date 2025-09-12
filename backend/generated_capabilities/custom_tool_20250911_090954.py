
import os
import sys
from typing import Dict, Any, Optional, List
import platform

# Attempt to import the necessary macOS frameworks
try:
    from AppKit import NSWorkspace, NSRunningApplication, NSApplication
    from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, kCGWindowListExcludeDesktopElements, CGWindowListCopyImage, kCGWindowImageBoundsKey
    from CoreGraphics import CGRect, CGImageRef
    from PIL import Image
    import io
    import numpy as np
    _MACOS_AVAILABLE = True
    _PIL_AVAILABLE = True
except ImportError:
    _MACOS_AVAILABLE = False
    _PIL_AVAILABLE = False
    # Define dummy classes/functions if macOS frameworks are not available
    class NSWorkspace:
        @staticmethod
        def sharedWorkspace():
            return None
    class NSRunningApplication:
        @staticmethod
        def currentApplication():
            return None
    class NSApplication:
        pass
    def CGWindowListCopyWindowInfo(*args, **kwargs):
        return None
    class CGRect:
        pass
    kCGWindowListOptionOnScreenOnly = 0
    kCGWindowListExcludeDesktopElements = 0
    def CGWindowListCopyImage(*args, **kwargs):
        return None
    kCGWindowImageBoundsKey = None
    CGImageRef = None # Dummy type
    class Image:
        @staticmethod
        def fromarray(*args, **kwargs):
            raise NotImplementedError
    class io:
        class BytesIO:
            pass
    class np:
        @staticmethod
        def array(*args, **kwargs):
            raise NotImplementedError

# Attempt to import pyobjc-framework-vision for OCR
try:
    from vision import VNImageRequestHandler, VNRecognizeTextRequest, VNTextRecognitionObservation
    _VISION_AVAILABLE = True
except ImportError:
    _VISION_AVAILABLE = False

class ScreenReaderError(Exception):
    """Custom exception for screen reader errors."""
    pass

class ScreenReader:
    """
    A specialized tool for reading screen text on macOS.

    This class provides functionality to capture screenshots and extract text
    from visible windows using Optical Character Recognition (OCR).
    """

    def __init__(self) -> None:
        """Initializes the ScreenReader."""
        if platform.system() != "Darwin":
            raise ScreenReaderError("This tool is currently only supported on macOS.")
        if not _MACOS_AVAILABLE:
            raise ScreenReaderError("Required macOS frameworks (AppKit, Quartz, CoreGraphics) are not available. Please ensure you have pyobjc installed.")
        if not _PIL_AVAILABLE:
            raise ScreenReaderError("Pillow library is not available. Please install it (`pip install Pillow`).")
        if not _VISION_AVAILABLE:
            print("Warning: Vision framework not found. OCR functionality will be limited. Please ensure pyobjc-framework-vision is installed correctly.", file=sys.stderr)

    def _get_visible_window_info(self) -> List[Dict[str, Any]]:
        """
        Retrieves information about all visible windows on the screen.

        Returns:
            A list of dictionaries, where each dictionary contains information
            about a visible window. Returns an empty list if no windows are found
            or if an error occurs.
        """
        try:
            window_list = CGWindowListCopyWindowInfo(
                kCGWindowListOptionOnScreenOnly | kCGWindowListExcludeDesktopElements,
                kCGNullWindowID
            )
            if window_list is None:
                return []

            windows_info = []
            for window_dict in window_list:
                window_info = dict(window_dict)
                # Filter out windows that are not actual applications or have no bounds
                # 'kCGWindowLayer' == 0 typically indicates a regular application window
                if ('kCGWindowOwnerName' in window_info and
                        'kCGWindowBounds' in window_info and
                        window_info.get('kCGWindowLayer') == 0 and
                        window_info.get('kCGWindowName')): # Ensure window has a name
                    bounds = window_info['kCGWindowBounds']
                    if bounds and isinstance(bounds, dict) and all(k in bounds for k in ['X', 'Y', 'Width', 'Height']):
                        windows_info.append(window_info)
            return windows_info

        except Exception as e:
            print(f"Error retrieving window information: {e}", file=sys.stderr)
            return []

    def get_window_titles(self) -> Dict[str, Any]:
        """
        Retrieves the titles of all visible application windows.

        Returns:
            A dictionary with 'success' (bool), 'message' (str), and 'titles' (list of str).
        """
        try:
            window_info_list = self._get_visible_window_info()
            titles = [
                f"{info['kCGWindowOwnerName']} - {info['kCGWindowName']}"
                for info in window_info_list
                if info.get('kCGWindowName') and info.get('kCGWindowOwnerName')
            ]
            return {
                "success": True,
                "message": f"Successfully retrieved {len(titles)} window titles.",
                "titles": titles
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"An error occurred while retrieving window titles: {e}",
                "titles": []
            }

    def _capture_window_image(self, window_id: int) -> Optional[bytes]:
        """
        Captures an image of a specific window by its ID.

        Args:
            window_id: The unique ID of the window to capture.

        Returns:
            The image data as PNG bytes, or None if the capture fails.
        """
        try:
            # Capture the window image
            image = CGWindowListCopyImage(
                CGRect(0, 0, 0, 0), # Placeholder bounds, actual bounds are extracted from window_info
                kCGWindowListOptionOnScreenOnly | kCGWindowListExcludeDesktopElements,
                window_id
            )

            if image is None:
                print(f"Failed to capture image for window ID {window_id}: CGWindowListCopyImage returned None.", file=sys.stderr)
                return None

            # Convert CGImageRef to PIL Image and then to PNG bytes
            # This part requires bridging CGImageRef to something PIL can understand.
            # A common approach is to get image data via Core Graphics utilities.
            # For simplicity and robustness, we'll use a method that's often available
            # with `pyobjc-framework-quartz` and `Pillow`.

            # Get the size and data provider from the CGImageRef
            width = image.width()
            height = image.height()
            DataProvider = image.dataProvider()
            Data = DataProvider.data()
            img_data_bytes = Data.bytes().tobytes() # Get raw bytes

            # Create a PIL Image from raw bytes. Assuming RGBA format.
            pil_image = Image.frombytes("RGBA", (width, height), img_data_bytes)

            # Save the PIL Image to a PNG in memory
            buffer = io.BytesIO()
            pil_image.save(buffer, format="PNG")
            return buffer.getvalue()

        except Exception as e:
            print(f"Error capturing image for window ID {window_id}: {e}", file=sys.stderr)
            return None

    def _get_ocr_text_from_image(self, image_data: bytes) -> Optional[str]:
        """
        Performs OCR on image data to extract text using the Vision framework.

        Args:
            image_data: The image data as bytes (PNG format expected).

        Returns:
            The extracted text as a string, or None if OCR fails or Vision is unavailable.
        """
        if not _VISION_AVAILABLE:
            print("Vision framework not available. Cannot perform OCR.", file=sys.stderr)
            return None

        try:
            # Create a VNImageRequestHandler from the image data
            handler = VNImageRequestHandler(data=image_data, options={})

            # Create a text recognition request
            request = VNRecognizeTextRequest()

            # Configure the request to return observations with string values
            request.recognitionLevel = 'accurate' # 'fast' or 'accurate'
            request.usesLanguageCorrection = True

            # Perform the request
            results = handler.perform([request])

            # Extract the text from the observations
            extracted_text = ""
            if results:
                for observation in results:
                    if isinstance(observation, VNTextRecognitionObservation):
                        # Concatenate all recognized strings
                        extracted_text += "".join(observation.strings()) + "\n"

            if not extracted_text.strip():
                return None # No text found
            return extracted_text.strip()

        except Exception as e:
            print(f"Error during OCR processing: {e}", file=sys.stderr)
            return None

    def read_specific_window_text(self, window_title_substring: str) -> Dict[str, Any]:
        """
        Reads text from a specific window identified by a substring in its title.

        This method will attempt to find a window whose title contains the
        provided substring, capture its content, and perform OCR.

        Args:
            window_title_substring: A string that should be present in the
                                    target window's title (case-insensitive).

        Returns:
            A dictionary with 'success' (bool), 'message' (str), and 'text' (str).
            'text' will contain the extracted text if successful, otherwise None.
        """
        if not window_title_substring:
            return {
                "success": False,
                "message": "Window title substring cannot be empty.",
                "text": None
            }

        try:
            window_info_list = self._get_visible_window_info()
            target_window_info = None

            for info in window_info_list:
                full_title = f"{info.get('kCGWindowOwnerName', '')} - {info.get('kCGWindowName', '')}"
                if window_title_substring.lower() in full_title.lower():
                    target_window_info = info
                    break

            if not target_window_info:
                return {
                    "success": False,
                    "message": f"No window found with title containing '{window_title_substring}'.",
                    "text": None
                }

            window_id = target_window_info.get('kCGWindowNumber')
            if not window_id:
                return {
                    "success": False,
                    "message": "Found window, but its ID is missing.",
                    "text": None
                }

            print(f"Attempting to capture image for window: {target_window_info.get('kCGWindowOwnerName')} - {target_window_info.get('kCGWindowName')} (ID: {window_id})", file=sys.stderr)
            image_data = self._capture_window_image(window_id)

            if image_data is None:
                return {
                    "success": False,
                    "message": f"Failed to capture image for window '{target_window_info.get('kCGWindowName')}'. Image capture might not be fully implemented or supported for this window type.",
                    "text": None
                }

            extracted_text = self._get_ocr_text_from_image(image_data)

            if extracted_text is None:
                if not _VISION_AVAILABLE:
                    return {
                        "success": False,
                        "message": f"Successfully captured image for window '{target_window_info.get('kCGWindowName')}', but Vision framework is not available for OCR.",
                        "text": None
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Successfully captured image for window '{target_window_info.get('kCGWindowName')}', but OCR failed to detect any text or encountered an error.",
                        "text": None
                    }

            return {
                "success": True,
                "message": f"Successfully extracted text from window '{target_window_info.get('kCGWindowName')}'.",
                "text": extracted_text
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"An unexpected error occurred while reading text from a specific window: {e}",
                "text": None
            }

    def read_all_screen_text(self) -> Dict[str, Any]:
        """
        Reads text from all visible windows on the screen.

        This method will attempt to iterate through all visible windows,
        capture their content, and perform OCR on each. The results will be
        aggregated.

        Note: This is a resource-intensive operation and OCR accuracy may vary.
        Requires a working implementation of image capture and OCR.

        Returns:
            A dictionary with 'success' (bool), 'message' (str), and 'all_text' (dict).
            'all_text' is a dictionary mapping window titles to their extracted text details.
        """
        try:
            window_info_list = self._get_visible_window_info()
            results = {}
            success_count = 0
            failure_count = 0

            if not window_info_list:
                return {
                    "success": True,
                    "message": "No visible windows found to read text from.",
                    "all_text": {}
                }

            for info in window_info_list:
                window_title = f"{info.get('kCGWindowOwnerName', '')} - {info.get('kCGWindowName', '')}"
                window_id = info.get('kCGWindowNumber')

                if not window_id:
                    results[window_title] = {
                        "success": False,
                        "message": "Window ID missing.",
                        "text": None
                    }
                    failure_count += 1
                    continue

                image_data = self._capture_window_image(window_id)
                if image_data is None:
                    results[window_title] = {
                        "success": False,
                        "message": "Failed to capture image.",
                        "text": None
                    }
                    failure_count += 1
                    continue

                extracted_text = self._get_ocr_text_from_image(image_data)
                if extracted_text is None:
                    if not _VISION_AVAILABLE:
                        message = "Vision framework not available for OCR."
                    else:
                        message = "OCR failed to detect any text or encountered an error."
                    results[window_title] = {
                        "success": False,
                        "message": message,
                        "text": None
                    }
                    failure_count += 1
                    continue

                results[window_title] = {
                    "success": True,
                    "message": "Successfully extracted text.",
                    "text": extracted_text
                }
                success_count += 1

            message = f"Processed {len(window_info_list)} windows: {success_count} successful, {failure_count} failed."
            return {
                "success": success_count > 0,
                "message": message,
                "all_text": results
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"An unexpected error occurred while reading all screen text: {e}",
                "all_text": {}
            }

if __name__ == '__main__':
    # Example Usage (for testing purposes)
    print("Initializing ScreenReader...")
    try:
        reader = ScreenReader()

        print("\n--- Getting Window Titles ---")
        titles_result = reader.get_window_titles()
        print(f"Success: {titles_result['success']}")
        print(f"Message: {titles_result['message']}")
        if titles_result['success']:
            print("Titles:")
            if titles_result['titles']:
                for title in titles_result['titles']:
                    print(f"- {title}")
            else:
                print("  No titles found.")

        print("\n--- Reading Text from a Specific Window (e.g., 'Terminal') ---")
        # Replace 'Terminal' with a window title that is currently open on your system
        # Example: If you have a Finder window open, you can use 'Finder'
        # Example: If you have a browser tab open, you can use the browser name
        # Ensure the substring is present in the window's full title.
        # For instance, if a window title is "My Document - TextEdit", "TextEdit" would work.
        window_to_find = "TextEdit" # Change this to a window title that's likely open
        print(f"Searching for window containing '{window_to_find}'...")
        specific_window_result = reader.read_specific_window_text(window_to_find)
        print(f"Success: {specific_window_result['success']}")
        print(f"Message: {specific_window_result['message']}")
        if specific_window_result['success']:
            print(f"Extracted Text:\n---\n{specific_window_result['text']}\n---")
        elif not _VISION_AVAILABLE:
             print("OCR is not functional because the Vision framework is not available.")


        print("\n--- Reading Text from All Visible Windows ---")
        all_screen_result = reader.read_all_screen_text()
        print(f"Success: {all_screen_result['success']}")
        print(f"Message: {all_screen_result['message']}")
        if all_screen_result['success']:
            if all_screen_result['all_text']:
                for title, content in all_screen_result['all_text'].items():
                    print(f"\nWindow: {title}")
                    print(f"  Status: {'Success' if content['success'] else 'Failed'}")
                    print(f"  Message: {content['message']}")
                    if content['success']:
                        print(f"  Extracted Text:\n  ---\n  {content['text']}\n  ---")
            else:
                print("  No text could be extracted from any window.")
        if not _VISION_AVAILABLE:
             print("\nNote: OCR is not functional because the Vision framework is not available.")

    except ScreenReaderError as e:
        print(f"Initialization Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during example execution: {e}")
