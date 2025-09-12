
import sys
import time
import io
from typing import Dict, Any, Optional, List, Tuple

# --- macOS Specific Imports ---
try:
    from AppKit import NSWorkspace, NSBitmapImageRep, NSImage
    from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, kCGNullWindowID, CGWindowListCreateImage, CGRect
except ImportError:
    if sys.platform == "darwin":
        raise ImportError("Could not import macOS specific modules. Please ensure PyObjC is installed (`pip install pyobjc`).")
    else:
        # Define dummy classes for non-macOS systems to allow import
        class DummyNSWorkspace:
            @staticmethod
            def sharedWorkspace(): return None
        class DummyNSBitmapImageRep:
            @staticmethod
            def alloc(): return DummyNSBitmapImageRep()
            def initWithCGImage_(self, cg_image): return self
            def representationUsingType_properties_(self, img_type, props): return None
        class DummyNSImage:
            @staticmethod
            def alloc(): return DummyNSImage()
            def initWithData_(self, data): return self
            def CGImageForProposedRect_context_hints_(self, rect, context, hints): return None
        class DummyCGWindowListCopyWindowInfo:
            def __init__(self, *args, **kwargs): pass
        class DummykCGWindowListOptionOnScreenOnly: pass
        class DummykCGNullWindowID: pass
        class DummyCGWindowListCreateImage:
            def __init__(self, *args, **kwargs): pass
        class DummyCGRect:
            def __init__(self, *args, **kwargs): pass

        NSWorkspace = DummyNSWorkspace
        NSBitmapImageRep = DummyNSBitmapImageRep
        NSImage = DummyNSImage
        CGWindowListCopyWindowInfo = DummyCGWindowListCopyWindowInfo
        kCGWindowListOptionOnScreenOnly = DummykCGWindowListOptionOnScreenOnly
        kCGNullWindowID = DummykCGNullWindowID
        CGWindowListCreateImage = DummyCGWindowListCreateImage
        CGRect = DummyCGRect
        print("Warning: This module is designed for macOS. Functionality will be limited on other platforms.", file=sys.stderr)

# --- OCR and Image Processing Imports ---
try:
    from PIL import Image
    import pytesseract
    from pytesseract import TesseractNotFoundError
except ImportError:
    TesseractNotFoundError = type("TesseractNotFoundError", (Exception,), {}) # Define a placeholder exception
    Image = None
    pytesseract = None
    print("Warning: Tesseract OCR or Pillow not found. Text recognition will not be available. Install them with `pip install pytesseract Pillow` and ensure Tesseract is installed on your system.", file=sys.stderr)

class ScreenTextReaderError(Exception):
    """Base exception for ScreenTextReader errors."""
    pass

class PlatformNotSupportedError(ScreenTextReaderError):
    """Raised when the platform is not supported."""
    pass

class DependencyNotAvailableError(ScreenTextReaderError):
    """Raised when a required dependency (Tesseract or Pillow) is not available."""
    pass

class WindowNotFoundError(ScreenTextReaderError):
    """Raised when a specific window cannot be found."""
    pass


class ScreenTextReader:
    """
    A tool class for reading text from the screen on macOS using OCR.

    This class utilizes macOS's Quartz and AppKit frameworks to capture
    screenshots of on-screen windows and then uses Tesseract OCR to extract
    text from these images.
    """

    def __init__(self, tesseract_cmd: Optional[str] = None):
        """
        Initializes the ScreenTextReader.

        Args:
            tesseract_cmd: Optional path to the Tesseract executable.
                           If None, pytesseract will try to find it in the system's PATH.

        Raises:
            PlatformNotSupportedError: If the script is not run on macOS.
            DependencyNotAvailableError: If Tesseract OCR or Pillow are not installed.
        """
        if sys.platform != "darwin":
            raise PlatformNotSupportedError("This tool is only supported on macOS.")

        self._tesseract_available = False
        self._pillow_available = False

        if Image is None or pytesseract is None:
            raise DependencyNotAvailableError("Tesseract OCR or Pillow library is not installed. Please install them with `pip install pytesseract Pillow` and ensure Tesseract is installed on your system.")
        else:
            self._pillow_available = True

        try:
            if tesseract_cmd:
                pytesseract.tesseract_cmd = tesseract_cmd
            pytesseract.get_tesseract_version()
            self._tesseract_available = True
        except TesseractNotFoundError:
            raise DependencyNotAvailableError("Tesseract OCR is not installed or not found in PATH. Please install Tesseract OCR from https://github.com/tesseract-ocr/tesseract and ensure its executable is in your system's PATH or specify its path via tesseract_cmd.")
        except Exception as e:
            raise ScreenTextReaderError(f"Error initializing Tesseract: {e}")

        self._last_error_message: str = ""


    def _get_window_list(self) -> List[Dict[str, Any]]:
        """Retrieves a list of on-screen windows with their information."""
        try:
            return CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID) or []
        except Exception as e:
            self._last_error_message = f"Error retrieving window list: {e}"
            print(f"Error retrieving window list: {e}", file=sys.stderr)
            return []

    def _capture_window_image(self, window_id: int, window_bounds: Tuple[int, int, int, int]) -> Optional[Image.Image]:
        """
        Captures a screenshot of a specific window using its bounds.

        Args:
            window_id: The ID of the window to capture.
            window_bounds: A tuple (x, y, width, height) representing the window's bounding box.

        Returns:
            A PIL Image object of the screenshot, or None if an error occurred.
        """
        if not self._pillow_available:
            self._last_error_message = "Pillow library is not available for image capture."
            return None

        try:
            # CGWindowListCreateImage expects CGRect which requires x, y, width, height
            bounds_rect = CGRect(window_bounds[0], window_bounds[1], window_bounds[2], window_bounds[3])
            image_ref = CGWindowListCreateImage(bounds_rect, kCGWindowListOptionOnScreenOnly, window_id, 0)

            if not image_ref:
                self._last_error_message = f"Failed to create CGImage for window ID: {window_id}"
                return None

            # Convert CGImage to PIL Image
            width = image_ref.width()
            height = image_ref.height()
            
            bitmap_rep = NSBitmapImageRep.alloc().initWithCGImage_(image_ref)
            if not bitmap_rep:
                self._last_error_message = f"Failed to create NSBitmapImageRep for window ID: {window_id}"
                return None

            data = bitmap_rep.representationUsingType_properties_(
                "NSPNGFileType", None # PNG is lossless and generally better for OCR
            )
            if not data:
                self._last_error_message = f"Failed to get image representation for window ID: {window_id}"
                return None

            pil_image = Image.open(io.BytesIO(data))
            return pil_image

        except Exception as e:
            self._last_error_message = f"Error capturing screenshot for window ID {window_id}: {e}"
            print(f"Error capturing screenshot for window ID {window_id}: {e}", file=sys.stderr)
            return None

    def _ocr_image(self, pil_image: Image.Image) -> Optional[str]:
        """
        Performs OCR on a PIL Image.

        Args:
            pil_image: The PIL Image object to process.

        Returns:
            The extracted text as a string, or None if OCR fails.
        """
        if not self._tesseract_available:
            self._last_error_message = "Tesseract OCR is not available for text recognition."
            return None

        try:
            # Ensure image is in RGB mode for Tesseract
            if pil_image.mode != "RGB":
                pil_image = pil_image.convert("RGB")

            # Basic preprocessing: convert to grayscale for potentially better OCR results
            # Invert colors if the background is typically dark and text is light
            # You might want to add more sophisticated preprocessing based on common cases
            processed_image = pil_image.convert("L") # Grayscale
            
            # You can add further image processing here if needed, e.g.,:
            # from PIL import ImageFilter
            # processed_image = processed_image.filter(ImageFilter.SHARPEN)
            # processed_image = processed_image.point(lambda p: p * 1.1) # Adjust brightness

            text = pytesseract.image_to_string(processed_image)
            return text.strip() if text else None
        except Exception as e:
            self._last_error_message = f"Error during OCR processing: {e}"
            print(f"Error during OCR processing: {e}", file=sys.stderr)
            return None

    def read_all_screen_text(self) -> Dict[str, Any]:
        """
        Reads text from all visible on-screen windows.

        Returns:
            A dictionary containing:
            - 'success': True if text was read successfully, False otherwise.
            - 'message': A string describing the outcome or error.
            - 'windows': A list of dictionaries, each representing a window
                         with 'window_id', 'title', 'owner', and 'text'.
                         'title' might be empty or generic for some windows.
                         'text' will be the extracted OCR text or None if not found.
        """
        result: Dict[str, Any] = {"success": False, "message": "", "windows": []}
        try:
            window_list_info = self._get_window_list()

            if not window_list_info:
                result["message"] = "No on-screen windows found."
                return result

            processed_count = 0
            for window_info in window_list_info:
                window_id = window_info.get('kCGWindowNumber')
                window_title = window_info.get('kCGWindowName')
                window_owner = window_info.get('kCGWindowOwnerName', 'Unknown App')
                window_bounds_dict = window_info.get('kCGWindowBounds')

                # Filter out invisible, tooltips, or windows without titles/bounds relevant for OCR
                if not window_id or not window_title or not window_bounds_dict:
                    continue
                
                # Ensure window_bounds are valid
                if not all(key in window_bounds_dict for key in ['X', 'Y', 'Width', 'Height']) or \
                   window_bounds_dict['Width'] <= 0 or window_bounds_dict['Height'] <= 0:
                    continue

                window_bounds_tuple = (
                    window_bounds_dict['X'],
                    window_bounds_dict['Y'],
                    window_bounds_dict['Width'],
                    window_bounds_dict['Height']
                )

                screenshot_pil = self._capture_window_image(window_id, window_bounds_tuple)
                extracted_text = None
                if screenshot_pil:
                    extracted_text = self._ocr_image(screenshot_pil)

                result["windows"].append({
                    "window_id": window_id,
                    "title": window_title,
                    "owner": window_owner,
                    "text": extracted_text
                })
                if extracted_text:
                    processed_count += 1

            if not result["windows"]:
                result["message"] = "No suitable windows found for text extraction."
            elif processed_count == 0:
                result["message"] = "Windows were found, but no text could be extracted from them."
            else:
                result["success"] = True
                result["message"] = f"Successfully processed {len(result['windows'])} windows. Text extracted from {processed_count}."

        except Exception as e:
            result["success"] = False
            result["message"] = f"An unexpected error occurred: {e}"
            print(f"Error in read_all_screen_text: {e}", file=sys.stderr)
            self._last_error_message = f"Unexpected error in read_all_screen_text: {e}"

        return result

    def read_specific_window_text(self, window_title_substring: str) -> Dict[str, Any]:
        """
        Reads text from the first visible on-screen window whose title
        contains the given substring.

        Args:
            window_title_substring: A substring to match against window titles.

        Returns:
            A dictionary containing:
            - 'success': True if text was read successfully, False otherwise.
            - 'message': A string describing the outcome or error.
            - 'window_id': The ID of the matched window, or None.
            - 'title': The title of the matched window, or None.
            - 'owner': The owner application of the matched window, or None.
            - 'text': The extracted OCR text, or None if not found.
        
        Raises:
            ValueError: If window_title_substring is empty.
        """
        if not window_title_substring:
            raise ValueError("window_title_substring cannot be empty.")

        result: Dict[str, Any] = {
            "success": False,
            "message": "",
            "window_id": None,
            "title": None,
            "owner": None,
            "text": None
        }
        try:
            window_list_info = self._get_window_list()

            if not window_list_info:
                result["message"] = "No on-screen windows found."
                return result

            found_window_id = None
            found_window_title = None
            found_window_owner = None
            found_window_bounds_dict = None

            for window_info in window_list_info:
                window_id = window_info.get('kCGWindowNumber')
                window_title = window_info.get('kCGWindowName')
                window_owner = window_info.get('kCGWindowOwnerName', 'Unknown App')
                window_bounds_dict = window_info.get('kCGWindowBounds')

                if window_id and window_title and window_title_substring in window_title:
                    # Prioritize windows with actual bounds and non-empty titles
                    if window_bounds_dict and window_bounds_dict.get('Width', 0) > 0 and window_bounds_dict.get('Height', 0) > 0:
                        found_window_id = window_id
                        found_window_title = window_title
                        found_window_owner = window_owner
                        found_window_bounds_dict = window_bounds_dict
                        break
            
            if found_window_id is None:
                result["message"] = f"No window found with title containing '{window_title_substring}'."
                return result

            window_bounds_tuple = (
                found_window_bounds_dict['X'],
                found_window_bounds_dict['Y'],
                found_window_bounds_dict['Width'],
                found_window_bounds_dict['Height']
            )

            screenshot_pil = self._capture_window_image(found_window_id, window_bounds_tuple)
            extracted_text = None
            if screenshot_pil:
                extracted_text = self._ocr_image(screenshot_pil)

            result["success"] = True
            result["message"] = f"Successfully read text from window '{found_window_title}'."
            result["window_id"] = found_window_id
            result["title"] = found_window_title
            result["owner"] = found_window_owner
            result["text"] = extracted_text

        except WindowNotFoundError:
            result["message"] = f"Window with title substring '{window_title_substring}' not found."
        except Exception as e:
            result["success"] = False
            result["message"] = f"An unexpected error occurred: {e}"
            print(f"Error in read_specific_window_text: {e}", file=sys.stderr)
            self._last_error_message = f"Unexpected error in read_specific_window_text: {e}"

        return result

    def read_desktop_text(self) -> Dict[str, Any]:
        """
        Reads text from the desktop background (entire screen).

        Returns:
            A dictionary containing:
            - 'success': True if text was read successfully, False otherwise.
            - 'message': A string describing the outcome or error.
            - 'text': The extracted OCR text from the desktop, or None if not found.
        """
        result: Dict[str, Any] = {"success": False, "message": "", "text": None}
        try:
            # Capture the entire screen
            # For entire screen capture, CGWindowListCreateImage should be called with kCGNullWindowID
            # and the first argument for rect should be None to capture the full screen.
            # However, the current implementation of _capture_window_image is tied to specific window bounds.
            # We'll adapt it slightly or create a dedicated function for full screen.
            
            # A simpler way for full screen capture might be to use Pillow directly if supported
            # or a more direct OS-level capture. For now, let's try to adapt CGWindowListCreateImage.

            # Option 1: Adapt _capture_window_image (might not be ideal for full screen)
            # We need to get the main screen's bounds. This is tricky with Quartz API directly.
            # Let's assume kCGNullWindowID with None rect captures the whole screen as intended.
            
            # The current _capture_window_image needs bounds. For full screen, we need the screen resolution.
            # A more robust way is to use a dedicated screenshot library if available or query screen bounds.
            
            # Let's use a slightly modified approach for full screen capture:
            # CGWindowListCreateImage(None, kCGWindowListOptionOnScreenOnly, kCGNullWindowID, 0) captures the whole screen.
            # We need to convert that CGImageRef to PIL Image.

            full_screen_image_ref = CGWindowListCreateImage(
                None, kCGWindowListOptionOnScreenOnly, kCGNullWindowID, 0
            )

            if not full_screen_image_ref:
                result["message"] = "Failed to capture desktop screenshot."
                self._last_error_message = "Failed to create CGImageRef for full screen."
                return result

            # Convert CGImage to PIL Image
            width = full_screen_image_ref.width()
            height = full_screen_image_ref.height()
            
            bitmap_rep = NSBitmapImageRep.alloc().initWithCGImage_(full_screen_image_ref)
            if not bitmap_rep:
                result["message"] = "Failed to capture desktop screenshot (bitmap rep failed)."
                self._last_error_message = "Failed to create NSBitmapImageRep for full screen."
                return result

            data = bitmap_rep.representationUsingType_properties_(
                "NSPNGFileType", None
            )
            if not data:
                result["message"] = "Failed to capture desktop screenshot (representation failed)."
                self._last_error_message = "Failed to get image representation for full screen."
                return result

            screenshot_pil = Image.open(io.BytesIO(data))

            if not screenshot_pil:
                result["message"] = "Failed to capture desktop screenshot (PIL open failed)."
                return result

            extracted_text = self._ocr_image(screenshot_pil)

            result["success"] = True
            result["message"] = "Successfully read text from desktop."
            result["text"] = extracted_text

        except Exception as e:
            result["success"] = False
            result["message"] = f"An unexpected error occurred: {e}"
            print(f"Error in read_desktop_text: {e}", file=sys.stderr)
            self._last_error_message = f"Unexpected error in read_desktop_text: {e}"

        return result

    def get_last_error_message(self) -> str:
        """Returns the last recorded error message."""
        return self._last_error_message

# --- Example Usage ---
if __name__ == "__main__":
    try:
        print("Initializing ScreenTextReader...")
        # If Tesseract is not in your PATH, specify the path:
        # reader = ScreenTextReader(tesseract_cmd='/usr/local/bin/tesseract')
        reader = ScreenTextReader()
        print("ScreenTextReader initialized successfully.")

        print("\n--- Reading text from all visible windows ---")
        all_windows_data = reader.read_all_screen_text()
        print(f"Success: {all_windows_data.get('success', False)}")
        print(f"Message: {all_windows_data.get('message', 'N/A')}")
        if all_windows_data.get('success'):
            for window in all_windows_data.get('windows', []):
                print(f"  - Window ID: {window.get('window_id')}, Title: '{window.get('title')}', Owner: '{window.get('owner')}'")
                text_preview = window.get('text', '')
                if text_preview and len(text_preview) > 100:
                    print(f"    Text: {text_preview[:100]}...")
                else:
                    print(f"    Text: {text_preview}")
        print("-" * 30)

        # Replace 'Finder' with a substring of a currently open window's title for testing
        # e.g., 'Terminal', 'Google Chrome', 'System Settings'
        target_window_substring = 'Finder' 
        print(f"\n--- Reading text from a specific window (title containing '{target_window_substring}') ---")
        try:
            specific_window_data = reader.read_specific_window_text(target_window_substring)
            print(f"Success: {specific_window_data.get('success', False)}")
            print(f"Message: {specific_window_data.get('message', 'N/A')}")
            if specific_window_data.get('success'):
                print(f"  Window ID: {specific_window_data.get('window_id')}")
                print(f"  Title: '{specific_window_data.get('title')}'")
                print(f"  Owner: '{specific_window_data.get('owner')}'")
                text_preview = specific_window_data.get('text', '')
                if text_preview and len(text_preview) > 100:
                    print(f"  Text: {text_preview[:100]}...")
                else:
                    print(f"  Text: {text_preview}")
        except ValueError as ve:
            print(f"Input Error: {ve}")
        except WindowNotFoundError as wnfe:
            print(f"Window Error: {wnfe}")
        print("-" * 30)

        print("\n--- Reading text from the desktop ---")
        desktop_data = reader.read_desktop_text()
        print(f"Success: {desktop_data.get('success', False)}")
        print(f"Message: {desktop_data.get('message', 'N/A')}")
        if desktop_data.get('success'):
            text_preview = desktop_data.get('text', '')
            if text_preview and len(text_preview) > 100:
                print(f"  Text: {text_preview[:100]}...")
            else:
                print(f"  Text: {text_preview}")
        print("-" * 30)

    except PlatformNotSupportedError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except DependencyNotAvailableError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ScreenTextReaderError as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred during initialization or execution: {e}", file=sys.stderr)
        sys.exit(1)
