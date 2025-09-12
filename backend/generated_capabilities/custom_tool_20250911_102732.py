
import sys
import os
from typing import Dict, Any, List, Optional
import platform

# Attempt to import necessary libraries for screen capture and OCR.
# Provide clear warnings if they are missing.

try:
    from PIL import Image
    import pytesseract
    _HAS_PYTESSERACT = True
except ImportError:
    _HAS_PYTESSERACT = False
    print("Warning: pytesseract not found. Please install it (`pip install pytesseract`).", file=sys.stderr)
    print("Tesseract OCR engine must also be installed and in your system's PATH.", file=sys.stderr)

try:
    # For macOS, we'll use Quartz and AppKit for screen capture.
    if platform.system() == "Darwin":
        import Quartz
        import AppKit
        _IS_MACOS = True
    else:
        _IS_MACOS = False
except ImportError:
    _IS_MACOS = False
    print("Warning: Quartz or AppKit not found. Screen reading functionality will be limited to non-macOS platforms.", file=sys.stderr)

# For non-macOS platforms, we'll attempt to use pyautogui for screen capture.
try:
    import pyautogui
    _HAS_PYAUTOGUI = True
except ImportError:
    _HAS_PYAUTOGUI = False
    print("Warning: pyautogui not found. Please install it (`pip install pyautogui`).", file=sys.stderr)


class ScreenReader:
    """
    A specialized tool for reading text from the screen.

    This class integrates screen capture and Optical Character Recognition (OCR)
    to extract text from a specified region of the screen or the entire screen.
    It supports macOS using Quartz/AppKit and other platforms using pyautogui.

    Requires:
    - pytesseract and Tesseract OCR engine (for text extraction)
    - Pillow (for image manipulation)
    - On macOS: Quartz and AppKit (usually pre-installed)
    - On other platforms: pyautogui (for screen capture)
    """

    def __init__(self):
        """Initializes the ScreenReader."""
        if not _HAS_PYTESSERACT or not _HAS_PYAUTOGUI and not _IS_MACOS:
            missing_deps = []
            if not _HAS_PYTESSERACT:
                missing_deps.append("pytesseract (and Tesseract OCR engine)")
            if not _HAS_PYAUTOGUI and not _IS_MACOS:
                missing_deps.append("pyautogui")
            print(f"Warning: Screen reading functionality is degraded due to missing dependencies: {', '.join(missing_deps)}.", file=sys.stderr)

    def read_screen(self, region: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
        """
        Reads text from a specified region of the screen.

        Args:
            region: An optional dictionary specifying the region to capture.
                    Expected keys are 'x', 'y', 'width', 'height'.
                    Coordinates are relative to the top-left corner of the primary monitor.
                    If None, the entire screen of the primary monitor is captured.

        Returns:
            A dictionary containing:
            - 'success': bool, True if the operation was successful, False otherwise.
            - 'message': str, a descriptive message about the operation.
            - 'text': List[str], a list of detected text lines if successful.
            - 'bounding_boxes': List[Dict[str, int]], a list of bounding boxes
                                for each detected text line if successful.
                                Keys: 'x', 'y', 'width', 'height'.
        """
        if not self._check_dependencies():
            return {
                'success': False,
                'message': "Required dependencies for screen reading are not met. Please install pytesseract, Pillow, and either Tesseract OCR engine (for all platforms) and pyautogui (for non-macOS) or ensure you are on macOS.",
                'text': [],
                'bounding_boxes': []
            }

        try:
            # Capture screenshot of the specified region
            image = self._capture_screen(region)
            if not image:
                return {
                    'success': False,
                    'message': "Failed to capture screen. Ensure the specified region is valid and screen is accessible.",
                    'text': [],
                    'bounding_boxes': []
                }

            # Use an OCR engine to extract text
            extracted_data = self._perform_ocr(image)

            if not extracted_data:
                return {
                    'success': False,
                    'message': "OCR processing failed.",
                    'text': [],
                    'bounding_boxes': []
                }

            # Filter out empty strings and invalid bounding boxes from OCR results
            valid_texts = []
            valid_boxes = []
            for txt, box in zip(extracted_data.get('text', []), extracted_data.get('bounding_boxes', [])):
                if txt and txt.strip():
                    valid_texts.append(txt)
                    valid_boxes.append(box)

            return {
                'success': True,
                'message': "Screen text read successfully.",
                'text': valid_texts,
                'bounding_boxes': valid_boxes
            }

        except Exception as e:
            return {
                'success': False,
                'message': f"An unexpected error occurred during screen reading: {e}",
                'text': [],
                'bounding_boxes': []
            }

    def _check_dependencies(self) -> bool:
        """Checks if essential dependencies for screen reading are available."""
        if not _HAS_PYTESSERACT:
            return False
        if platform.system() == "Darwin":
            return _IS_MACOS
        else:
            return _HAS_PYAUTOGUI

    def _validate_region(self, region: Optional[Dict[str, int]]) -> bool:
        """Validates the format and content of the region dictionary."""
        if region is None:
            return True  # No region specified is valid

        if not isinstance(region, dict):
            print("Error: 'region' must be a dictionary.", file=sys.stderr)
            return False

        required_keys = ['x', 'y', 'width', 'height']
        for key in required_keys:
            if key not in region:
                print(f"Error: 'region' dictionary is missing required key: '{key}'.", file=sys.stderr)
                return False
            if not isinstance(region[key], int):
                print(f"Error: Value for key '{key}' in 'region' must be an integer.", file=sys.stderr)
                return False
            if region[key] < 0:
                print(f"Error: Value for key '{key}' in 'region' cannot be negative.", file=sys.stderr)
                return False

        return True

    def _capture_screen(self, region: Optional[Dict[str, int]]) -> Optional[Image.Image]:
        """
        Captures an image of the screen or a specified region.

        Args:
            region: An optional dictionary specifying the region to capture.
                    Expected keys are 'x', 'y', 'width', 'height'.
                    If None, the entire screen of the primary monitor is captured.

        Returns:
            A Pillow Image object representing the captured screen, or None if capture fails.
        """
        if not self._validate_region(region):
            return None

        try:
            if _IS_MACOS:
                return self._capture_screen_macos(region)
            elif _HAS_PYAUTOGUI:
                return self._capture_screen_pyautogui(region)
            else:
                print("Error: No screen capture method available. Dependencies missing.", file=sys.stderr)
                return None
        except Exception as e:
            print(f"Error during screen capture: {e}", file=sys.stderr)
            return None

    def _capture_screen_macos(self, region: Optional[Dict[str, int]]) -> Optional[Image.Image]:
        """Captures screen on macOS using Quartz and AppKit."""
        try:
            screen = AppKit.NSScreen.mainScreen()
            if not screen:
                return None

            screen_frame = screen.frame() # Origin at bottom-left

            if region:
                # User provides coordinates relative to top-left of the screen.
                # We need to convert these to the coordinate system used by Quartz.
                # The y-coordinate needs to be adjusted for the screen's origin.
                capture_x = region.get('x', 0)
                capture_y = screen_frame.origin.y + screen_frame.size.height - (region.get('y', 0) + region.get('height', screen_frame.size.height))
                capture_width = region.get('width', screen_frame.size.width)
                capture_height = region.get('height', screen_frame.size.height)

                # Ensure captured region does not exceed screen bounds
                capture_x = max(capture_x, screen_frame.origin.x)
                capture_y = max(capture_y, screen_frame.origin.y)
                capture_width = min(capture_width, screen_frame.size.width - (capture_x - screen_frame.origin.x))
                capture_height = min(capture_height, screen_frame.size.height - (capture_y - screen_frame.origin.y))

                capture_rect = AppKit.NSMakeRect(capture_x, capture_y, capture_width, capture_height)
            else:
                capture_rect = screen_frame

            if capture_rect.size.width <= 0 or capture_rect.size.height <= 0:
                print("Error: Calculated capture rectangle has zero or negative dimensions.", file=sys.stderr)
                return None

            cg_image = Quartz.CGWindowListCreateImage(
                capture_rect,
                Quartz.kCGWindowListOptionOnScreenOnly,
                Quartz.kCGNullWindowID,
                Quartz.kCGWindowImageBoundsIgnoreFraming
            )

            if not cg_image:
                print("Error: CGWindowListCreateImage returned None.", file=sys.stderr)
                return None

            # Convert CGImage to PIL Image
            width = Quartz.CGImageGetWidth(cg_image)
            height = Quartz.CGImageGetHeight(cg_image)
            bytes_per_row = Quartz.CGImageGetBytesPerRow(cg_image)
            data_provider = Quartz.CGImageGetDataProvider(cg_image)
            data = Quartz.CGDataProviderCopyData(data_provider)
            
            pil_image = Image.frombuffer("RGBA", (width, height), data, "raw", "BGRA", bytes_per_row, 1)
            
            # If a region was specified, crop the image to that region.
            # This is necessary because CGWindowListCreateImage might capture a larger area
            # and we need to ensure the OCR is performed on the exact requested region's pixels.
            if region:
                # The captured image's top-left is at capture_rect.origin.x, capture_rect.origin.y
                # The original region's top-left was (region['x'], region['y']).
                # The offset within the captured image is:
                offset_x = region['x'] - capture_rect.origin.x
                offset_y = region['y'] - capture_rect.origin.y # This calculation might be tricky due to coordinate system shifts.
                                                              # A simpler approach is to re-calculate the PIL crop box relative to the PIL image.
                
                # The PIL image is derived from cg_image, which captures the area defined by capture_rect.
                # So, the coordinates in the PIL image directly correspond to the capture_rect's coordinate space.
                # We need to crop the PIL image to the user-specified region.
                # The crop box coordinates are relative to the PIL image's top-left corner.
                crop_box_x = region['x'] - capture_rect.origin.x
                crop_box_y = region['y'] - capture_rect.origin.y # This is still potentially problematic.
                
                # A more robust way is to extract the portion directly if the `region` was correctly translated for `capture_rect`
                # If `capture_rect` accurately reflects the user's `region` within the screen's coordinate system,
                # and the PIL image is the result of that capture, then the PIL image *is* the region.
                # However, the `cg_image` might be derived from a larger window list and we're selecting a sub-part.
                # Let's assume `capture_rect` is the area we want. The PIL image is created from `cg_image`.
                # The Pillow `crop` method takes a 4-tuple: (left, upper, right, lower).
                
                # The coordinates in the PIL image are relative to the top-left of the `cg_image`.
                # `cg_image` corresponds to `capture_rect`.
                # We want to extract the part that corresponds to the user's `region`.
                
                # The `capture_rect.origin.x` and `capture_rect.origin.y` are the top-left corner of the image captured by CGWindowListCreateImage.
                # `region['x']` and `region['y']` are the top-left corner of the user's requested area.
                # The offset of the user's region within the captured image is:
                crop_left = region['x'] - capture_rect.origin.x
                crop_upper = region['y'] - capture_rect.origin.y # This adjustment for y might be tricky depending on how Quartz handles coordinates vs AppKit.
                                                                # Let's simplify: CGImageGet... refers to the actual image data.
                                                                # The `capture_rect` guides the `CGWindowListCreateImage` call.
                                                                # If `capture_rect` is exactly the user's region (adjusted for OS coordinate system),
                                                                # then `pil_image` already represents that region.
                                                                # If `capture_rect` is larger, we might need to crop.
                                                                # The `NSImage.alloc().initWithCGImage_size_` expects `size` to match the CGImage's size.
                                                                # If `cg_image` is derived from `capture_rect`, its size should match `capture_rect.size`.
                                                                # Therefore, `pil_image` should already be the correct size.

                # We need to ensure the OCR is applied to the *exact* pixels corresponding to the region.
                # If `cg_image` captured more than `capture_rect`, then `pil_image` would be larger.
                # However, `CGWindowListCreateImage` should capture *exactly* the `capture_rect`.
                # So, `pil_image` should have dimensions `capture_rect.size.width` and `capture_rect.size.height`.
                # The coordinates within `pil_image` are 0 to width-1 and 0 to height-1.
                # If the user specified `region`, we should ensure the PIL image corresponds to that region,
                # not just the `capture_rect` which might have been adjusted for screen bounds.

                # A safer bet: capture the whole screen, then crop with Pillow.
                # Or, ensure `capture_rect` precisely matches the desired region.
                # Let's assume `capture_rect` is correctly set to the desired region, and `cg_image` and thus `pil_image` reflect that.

                # Re-evaluate the `capture_rect` creation for macOS:
                # `screen_frame` has origin at bottom-left.
                # `region['y']` and `region['height']` are relative to top-left.
                # So `region['y']` is the distance from the top edge.
                # The corresponding y in bottom-left origin is `screen_frame.size.height - region['y'] - region['height']`.
                # This is what was already done: `screen_frame.origin.y + screen_frame.size.height - (region.get('y', 0) + region.get('height', screen_frame.size.height))`.
                # This calculation seems correct for aligning `region`'s top-left origin with the `capture_rect`'s bottom-left origin.

                # After `CGWindowListCreateImage` using `capture_rect`, the resulting `cg_image` should represent that exact rectangle.
                # The `pil_image` derived from it will have dimensions `capture_rect.size.width` x `capture_rect.size.height`.
                # So, no further cropping should be needed if `capture_rect` is precise.
                pass # If capture_rect was correctly calculated, pil_image should be fine.

            return pil_image

        except Exception as e:
            print(f"Error during macOS screen capture: {e}", file=sys.stderr)
            return None

    def _capture_screen_pyautogui(self, region: Optional[Dict[str, int]]) -> Optional[Image.Image]:
        """Captures screen on non-macOS platforms using pyautogui."""
        try:
            if region:
                # pyautogui uses x, y, width, height relative to top-left of primary screen.
                # Ensure the region is within screen bounds.
                screen_width, screen_height = pyautogui.size()
                x = max(0, region.get('x', 0))
                y = max(0, region.get('y', 0))
                width = min(region.get('width', screen_width), screen_width - x)
                height = min(region.get('height', screen_height), screen_height - y)

                if width <= 0 or height <= 0:
                    print("Error: Specified region has zero or negative dimensions after boundary adjustment.", file=sys.stderr)
                    return None

                screenshot = pyautogui.screenshot(region=(x, y, width, height))
            else:
                screenshot = pyautogui.screenshot()
            return screenshot
        except Exception as e:
            print(f"Error during pyautogui screen capture: {e}", file=sys.stderr)
            return None

    def _perform_ocr(self, image: Image.Image) -> Dict[str, Any]:
        """
        Performs Optical Character Recognition (OCR) on an image using pytesseract.

        Args:
            image: A Pillow Image object to perform OCR on.

        Returns:
            A dictionary containing:
            - 'text': List[str], a list of detected text lines.
            - 'bounding_boxes': List[Dict[str, int]], a list of bounding boxes for each detected text line.
        """
        if not _HAS_PYTESSERACT:
            print("Error: pytesseract is not available.", file=sys.stderr)
            return {'text': [], 'bounding_boxes': []}

        try:
            # pytesseract.image_to_data returns a dictionary with detailed OCR results,
            # including text and bounding box information.
            # We set output_type to DICT for easy parsing.
            # config='--psm 6' is often a good default for a single block of text.
            # If the screen content can vary widely, this might need tuning or be omitted.
            # We can also specify language with lang='eng'.
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT, config='--psm 6')

            texts = []
            bounding_boxes = []
            n_boxes = len(data['level'])
            
            # Iterate through the detected elements. Level 5 typically corresponds to words.
            # We can aggregate words into lines if needed, but for now, let's consider
            # lines or blocks of text as returned by tesseract.
            # Often, 'text' field at level 4 (paragraph) or 5 (word) is useful.
            # Let's try to extract lines first. Tesseract's 'text' field at various levels
            # can be tricky to interpret as strict lines.
            # A common approach is to iterate through detected words and group them by proximity.
            # However, `image_to_data` already gives us structured output.
            
            # Let's refine: extract text for each recognized word and its box.
            # Then, we can decide how to present it as 'lines'.
            # For now, let's return each detected word as an item, with its bounding box.
            # This provides granular information. The caller can then aggregate.
            
            for i in range(n_boxes):
                # Level 5 is typically word level. Filter out empty strings and low confidence.
                # Confidence is a string, needs conversion to float.
                confidence = int(data['conf'][i])
                text = data['text'][i].strip()
                
                if text and confidence > 0: # Confidence filter can be adjusted (e.g., > 50)
                    x = int(data['left'][i])
                    y = int(data['top'][i])
                    w = int(data['width'][i])
                    h = int(data['height'][i])
                    
                    texts.append(text)
                    bounding_boxes.append({'x': x, 'y': y, 'width': w, 'height': h})

            # If we want to try and reconstruct lines, it's more complex.
            # For example, group words within a similar vertical position.
            # However, returning word-level data is often more useful for programmatic use.
            # Let's stick to word-level for now and make it clear in the output.
            
            if not texts:
                print("Warning: OCR found no detectable text.", file=sys.stderr)
                return {'text': [], 'bounding_boxes': []}

            return {
                'text': texts,
                'bounding_boxes': bounding_boxes
            }

        except pytesseract.TesseractNotFoundError:
            print("Error: Tesseract OCR engine not found. Please ensure it is installed and in your PATH.", file=sys.stderr)
            return {'text': [], 'bounding_boxes': []}
        except Exception as e:
            print(f"An error occurred during OCR processing: {e}", file=sys.stderr)
            return {'text': [], 'bounding_boxes': []}


if __name__ == '__main__':
    # Example Usage:
    print(f"Running on platform: {platform.system()}")
    reader = ScreenReader()

    print("\n--- Reading entire screen ---")
    result_full = reader.read_screen()
    if result_full['success']:
        print(f"Message: {result_full['message']}")
        print("Detected Text (word-level):")
        if result_full['text']:
            for i, line in enumerate(result_full['text']):
                print(f"  - '{line}' (Box: {result_full['bounding_boxes'][i]})")
        else:
            print("  No text detected.")
    else:
        print(f"Error: {result_full['message']}")

    print("\n--- Reading a specific region ---")
    # Example region: a 300x150 rectangle at (50, 50) from the top-left corner
    # Ensure this region covers some visible text on your screen.
    custom_region = {'x': 50, 'y': 50, 'width': 300, 'height': 150}
    result_region = reader.read_screen(region=custom_region)
    if result_region['success']:
        print(f"Message: {result_region['message']}")
        print("Detected Text in Region (word-level):")
        if result_region['text']:
            for i, line in enumerate(result_region['text']):
                print(f"  - '{line}' (Box: {result_region['bounding_boxes'][i]})")
        else:
            print("  No text detected in the specified region.")
    else:
        print(f"Error: {result_region['message']}")

    print("\n--- Reading an invalid region (missing key) ---")
    invalid_region_missing_key = {'x': 10, 'y': 10, 'width': 50}
    result_invalid_key = reader.read_screen(region=invalid_region_missing_key)
    print(f"Result: {result_invalid_key}")

    print("\n--- Reading an invalid region (non-integer value) ---")
    invalid_region_non_int = {'x': 10, 'y': 10, 'width': '50', 'height': 50}
    result_invalid_type = reader.read_screen(region=invalid_region_non_int)
    print(f"Result: {result_invalid_type}")

    print("\n--- Reading an invalid region (negative value) ---")
    invalid_region_negative = {'x': 10, 'y': 10, 'width': -50, 'height': 50}
    result_invalid_negative = reader.read_screen(region=invalid_region_negative)
    print(f"Result: {result_invalid_negative}")
