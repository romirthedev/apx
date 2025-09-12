
import Quartz
import AppKit
import typing
import io
from PIL import Image
import pytesseract
import os

# Attempt to configure tesseract_cmd path.
# This is a common issue on macOS. Adjust if your tesseract installation differs.
# If you installed Tesseract via Homebrew, it's usually in /usr/local/bin/tesseract
# or potentially /opt/homebrew/bin/tesseract on Apple Silicon.
try:
    # Prefer a common path, but allow overriding via environment variable
    tesseract_path = os.environ.get("TESSERACT_CMD_PATH", "/usr/local/bin/tesseract")
    if not os.path.exists(tesseract_path):
        # Try another common path for Apple Silicon
        tesseract_path = os.environ.get("TESSERACT_CMD_PATH", "/opt/homebrew/bin/tesseract")

    if os.path.exists(tesseract_path):
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
    else:
        print(f"WARNING: Tesseract executable not found at '{tesseract_path}' or environment variable TESSERACT_CMD_PATH not set.")
        print("Please ensure Tesseract OCR is installed and accessible, or set the TESSERACT_CMD_PATH environment variable.")
except Exception as e:
    print(f"WARNING: Could not configure tesseract_cmd. OCR may not work. Error: {e}")


class ScreenReader:
    """
    A specialized tool for reading text from the screen on macOS,
    leveraging screen capture and OCR.
    """

    def __init__(self):
        """
        Initializes the ScreenReader.
        It checks for the presence of necessary OCR libraries.
        """
        self._check_dependencies()

    def _check_dependencies(self):
        """
        Checks if required OCR libraries and tools are available.
        """
        try:
            import PIL.Image
            import pytesseract
        except ImportError:
            raise ImportError(
                "Required libraries 'Pillow' and 'pytesseract' are not installed. "
                "Please install them using: pip install Pillow pytesseract"
            )

        try:
            # Attempt to run tesseract command to check if engine is accessible
            pytesseract.get_tesseract_version()
        except pytesseract.TesseractNotFoundError:
            raise RuntimeError(
                "Tesseract OCR engine not found. Please install Tesseract OCR. "
                "On macOS, you can often use: brew install tesseract. "
                "Ensure the tesseract executable is in your PATH or set TESSERACT_CMD_PATH environment variable."
            )
        except Exception as e:
            print(f"WARNING: An unexpected error occurred while checking Tesseract version: {e}")


    def read_screen_text(self, region: typing.Optional[typing.Tuple[int, int, int, int]] = None) -> typing.Dict[str, typing.Any]:
        """
        Reads visible text from a specified region or the entire current screen.

        This method captures the screen (or a specified region), converts it to an image,
        and then uses Optical Character Recognition (OCR) to extract text.

        Args:
            region (Optional[Tuple[int, int, int, int]]): A tuple representing the
                capture region (x, y, width, height). If None, the entire screen is captured.

        Returns:
            A dictionary containing:
            - 'success' (bool): True if text was read successfully, False otherwise.
            - 'message' (str): A message indicating the outcome of the operation.
            - 'text' (str, optional): The extracted text if 'success' is True.
        """
        try:
            # Validate region input
            if region is not None:
                if not isinstance(region, tuple) or len(region) != 4:
                    return {"success": False, "message": "Invalid region format. Expected (x, y, width, height)."}
                for val in region:
                    if not isinstance(val, (int, float)):
                        return {"success": False, "message": "Region coordinates and dimensions must be numbers."}
                if region[2] <= 0 or region[3] <= 0:
                    return {"success": False, "message": "Region width and height must be positive."}

            # Capture the screen or specified region
            screenshot_image_data = self._capture_screen(region=region)
            if not screenshot_image_data:
                return {"success": False, "message": "Failed to capture screen or specified region."}

            # Perform OCR on the screenshot
            extracted_text = self._perform_ocr(screenshot_image_data)

            if extracted_text is not None:
                return {"success": True, "message": "Screen text read successfully.", "text": extracted_text}
            else:
                return {"success": False, "message": "OCR failed to extract text from the captured image."}

        except ImportError as e:
            return {"success": False, "message": f"Dependency error: {e}"}
        except RuntimeError as e:
            return {"success": False, "message": f"Runtime error: {e}"}
        except Exception as e:
            # Catch any other unexpected errors
            return {"success": False, "message": f"An unexpected error occurred: {str(e)}"}

    def _capture_screen(self, region: typing.Optional[typing.Tuple[int, int, int, int]] = None) -> typing.Optional[bytes]:
        """
        Captures the entire screen or a specified region as image data (PNG).

        Args:
            region (Optional[Tuple[int, int, int, int]]): A tuple representing the
                capture region (x, y, width, height). If None, the entire screen is captured.

        Returns:
            Image data as bytes (PNG format), or None if an error occurs.
        """
        try:
            if region:
                # Capture a specific region
                capture_rect = Quartz.CGRectMake(region[0], region[1], region[2], region[3])
                desktop_image_ref = Quartz.CGWindowListCreateImage(
                    capture_rect,
                    Quartz.kCGWindowListOptionOnScreenOnly,
                    Quartz.kCGNullWindowID,  # Use 0 or kCGNullWindowID for any window
                    Quartz.kCGWindowImageDefault
                )
                if not desktop_image_ref:
                    # If region capture fails, it might be because the region is invalid or off-screen.
                    # Let's try capturing the whole screen and cropping as a fallback,
                    # though this might not be what the user intended if they provided a specific region.
                    print("WARNING: Failed to capture specific region. Attempting to capture full screen and crop.")
                    desktop_image_ref = Quartz.CGWindowListCreateImage(
                        Quartz.CGRectInfinite,
                        Quartz.kCGWindowListOptionOnScreenOnly,
                        Quartz.kCGNullWindowID,
                        Quartz.kCGWindowImageDefault
                    )
                    if desktop_image_ref:
                        # Crop the full screen image
                        full_screen_width = Quartz.CGImageGetWidth(desktop_image_ref)
                        full_screen_height = Quartz.CGImageGetHeight(desktop_image_ref)
                        
                        # Adjust region to be within screen bounds
                        x, y, width, height = region
                        x = max(0, x)
                        y = max(0, y)
                        width = min(width, full_screen_width - x)
                        height = min(height, full_screen_height - y)
                        
                        if width <= 0 or height <= 0:
                            print("ERROR: Adjusted region has zero or negative dimensions after cropping.")
                            return None

                        cropped_image_ref = Quartz.CGImageCreateWithImageInRect(desktop_image_ref, Quartz.CGRectMake(x, y, width, height))
                        if not cropped_image_ref:
                            print("ERROR: Failed to crop the full screen image.")
                            return None
                        desktop_image_ref = cropped_image_ref # Use the cropped image
                    else:
                        return None
            else:
                # Capture the entire screen
                desktop_image_ref = Quartz.CGWindowListCreateImage(
                    Quartz.CGRectInfinite,
                    Quartz.kCGWindowListOptionOnScreenOnly,
                    Quartz.kCGNullWindowID,
                    Quartz.kCGWindowImageDefault
                )

            if not desktop_image_ref:
                return None

            # Convert CGImageRef to NSImage, then to PNG data
            ns_image = AppKit.NSImage.alloc().initWithCGImage_size_(desktop_image_ref, None)
            if not ns_image:
                return None

            tiff_representation = ns_image.TIFFRepresentation()
            if not tiff_representation:
                return None

            pil_image = Image.open(io.BytesIO(tiff_representation))
            
            # Save to bytes as PNG
            buffer = io.BytesIO()
            pil_image.save(buffer, format="PNG")
            return buffer.getvalue()

        except Exception as e:
            print(f"Error capturing screen: {e}")
            return None

    def _perform_ocr(self, image_data: bytes) -> typing.Optional[str]:
        """
        Performs OCR on image data to extract text.

        Args:
            image_data: The image data (PNG bytes) to perform OCR on.

        Returns:
            The extracted text as a string, or None if OCR fails.
        """
        try:
            image = Image.open(io.BytesIO(image_data))
            # Use pytesseract to get string. It handles different image formats.
            # You can specify language with lang='eng' for English, etc.
            text = pytesseract.image_to_string(image, lang='eng')
            return text.strip()
        except pytesseract.TesseractNotFoundError:
            # This should ideally be caught in __init__, but as a safeguard:
            print("OCR engine not found. Please install Tesseract OCR.")
            return None
        except Exception as e:
            print(f"OCR processing error: {e}")
            return None


if __name__ == '__main__':
    # Example usage:
    reader = ScreenReader()

    print("--- Reading entire screen ---")
    result_full = reader.read_screen_text()

    if result_full['success']:
        print("Successfully read entire screen text:")
        print(result_full['text'])
    else:
        print(f"Failed to read entire screen text: {result_full['message']}")

    print("\n--- Reading a specific region (example: top-left 200x100 pixels) ---")
    # Define a region: (x, y, width, height)
    # This is a hypothetical region; adjust based on your screen resolution and desired content.
    # For a real test, you might want to ensure there's visible text in this region.
    example_region = (0, 0, 200, 100)
    result_region = reader.read_screen_text(region=example_region)

    if result_region['success']:
        print(f"Successfully read text from region {example_region}:")
        print(result_region['text'])
    else:
        print(f"Failed to read text from region {example_region}: {result_region['message']}")

    print("\n--- Testing invalid region input ---")
    invalid_region_result = reader.read_screen_text(region="invalid")
    print(f"Result for invalid region input: {invalid_region_result}")

    invalid_region_result_2 = reader.read_screen_text(region=(10, 20))
    print(f"Result for invalid region input (wrong tuple size): {invalid_region_result_2}")

    invalid_region_result_3 = reader.read_screen_text(region=(10, 20, -50, 100))
    print(f"Result for invalid region input (negative width): {invalid_region_result_3}")
