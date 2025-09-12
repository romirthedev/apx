import io
import sys
import platform
from typing import Dict, Union, Any

# Try to import necessary libraries, provide specific error handling if not found
try:
    from PIL import Image
    import pytesseract
except ImportError:
    error_message = (
        "Required libraries 'Pillow' and 'pytesseract' not found. "
        "Please install them using pip: pip install Pillow pytesseract"
    )
    if sys.platform == "darwin":
        error_message += "\nOn macOS, you may also need to install tesseract OCR: brew install tesseract"
    raise ImportError(error_message)

# Try to import platform-specific screenshot library
try:
    if sys.platform == "darwin":
        from mss import mss
        from mss.exception import ScreenShotError
    elif sys.platform.startswith("linux") or sys.platform.startswith("win"):
        import pyscreenshot as ImageGrab
    else:
        raise RuntimeError(
            f"Unsupported platform: {sys.platform}. This tool supports macOS, Linux, and Windows."
        )
except ImportError as e:
    if sys.platform == "darwin":
        raise ImportError(
            "macOS screenshot library 'mss' not found. "
            "Install it using pip: pip install mss"
        ) from e
    elif sys.platform.startswith("linux") or sys.platform.startswith("win"):
        raise ImportError(
            "Screenshot library 'pyscreenshot' not found. "
            "Install it using pip: pip install pyscreenshot"
        ) from e
    else:
        raise e # Re-raise the RuntimeError if it was for unsupported platform


class ScreenshotTextReader:
    """
    A versatile tool class for taking screenshots and reading text from them.

    Supports macOS using 'mss' and Linux/Windows using 'pyscreenshot'.
    Leverages 'pytesseract' for optical character recognition (OCR) to extract text.
    """

    def __init__(self) -> None:
        """
        Initializes the ScreenshotTextReader.

        Ensures that the tesseract executable is accessible.
        """
        try:
            # Check if tesseract is installed and accessible.
            pytesseract.get_tesseract_version()
        except pytesseract.TesseractNotFoundError:
            error_msg = (
                "Tesseract OCR is not installed or not found in your PATH. "
                "Please install it and ensure it's accessible."
            )
            if sys.platform == "darwin":
                error_msg += "\nOn macOS, you can install it using Homebrew: 'brew install tesseract'."
            elif sys.platform.startswith("linux"):
                error_msg += "\nOn Debian/Ubuntu, you can install it using: 'sudo apt-get install tesseract-ocr'."
            elif sys.platform.startswith("win"):
                error_msg += "\nOn Windows, download and install Tesseract from the official GitHub repository or a package manager."
            error_msg += "\nIf installed elsewhere, you may need to set the TESSDATA_PREFIX environment variable."
            raise EnvironmentError(error_msg)
        except Exception as e:
            self._handle_error(
                f"An unexpected error occurred while initializing Tesseract: {e}"
            )

    def _handle_error(self, message: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Internal helper to create a standardized error response dictionary.

        Args:
            message: A descriptive error message.
            data: Optional additional data to include in the error response.

        Returns:
            A dictionary representing the error response.
        """
        return {
            "success": False,
            "message": message,
            "data": data if data is not None else {},
        }

    def _handle_success(self, message: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Internal helper to create a standardized success response dictionary.

        Args:
            message: A descriptive success message.
            data: The relevant data to include in the success response.

        Returns:
            A dictionary representing the success response.
        """
        return {
            "success": True,
            "message": message,
            "data": data,
        }

    def _validate_region(self, region: Dict[str, int], monitor_bounds: Dict[str, int]) -> Union[Dict[str, int], None]:
        """
        Validates a user-provided region against monitor boundaries.

        Args:
            region: A dictionary specifying the capture region ('top', 'left', 'width', 'height').
            monitor_bounds: A dictionary with the boundaries of the current monitor ('top', 'left', 'width', 'height').

        Returns:
            The validated region dictionary if valid, otherwise None.
        """
        if not all(k in region for k in ("top", "left", "width", "height")):
            return None  # Indicate validation failure

        if region["width"] <= 0 or region["height"] <= 0:
            return None  # Indicate validation failure

        # Ensure region is within monitor boundaries
        if region["top"] < monitor_bounds["top"] or \
           region["left"] < monitor_bounds["left"] or \
           region["top"] + region["height"] > monitor_bounds["top"] + monitor_bounds["height"] or \
           region["left"] + region["width"] > monitor_bounds["left"] + monitor_bounds["width"]:
            return None  # Indicate validation failure

        return region

    def take_and_read_screenshot(self, region: Dict[str, int] = None) -> Dict[str, Any]:
        """
        Takes a screenshot of the entire screen or a specified region and reads the text from it.

        Args:
            region (Optional[Dict[str, int]]): A dictionary specifying the capture region.
                Expected keys are 'top', 'left', 'width', 'height'.
                If None, the entire primary screen is captured.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the operation.
                On success:
                    {
                        "success": True,
                        "message": "Screenshot and text extraction successful.",
                        "data": {
                            "text": "Extracted text content...",
                        }
                    }
                On failure:
                    {
                        "success": False,
                        "message": "Error description.",
                        "data": {}
                    }
        """
        try:
            sct_img_bytes = None
            monitor_bounds = {}

            if sys.platform == "darwin":
                with mss() as sct:
                    # 0 is all monitors, 1 is the primary monitor
                    monitor = sct.monitors[1]
                    monitor_bounds = {
                        "top": monitor["top"],
                        "left": monitor["left"],
                        "width": monitor["width"],
                        "height": monitor["height"],
                    }

                    if region:
                        validated_region = self._validate_region(region, monitor_bounds)
                        if validated_region is None:
                            return self._handle_error(
                                "Invalid region provided. Ensure 'top', 'left', 'width', 'height' are positive and within monitor boundaries."
                            )
                        capture_area = validated_region
                    else:
                        capture_area = monitor_bounds

                    img_raw = sct.grab(capture_area)
                    sct_img_bytes = img_raw.rgb  # Use RGB bytes for PIL

            elif sys.platform.startswith("linux") or sys.platform.startswith("win"):
                try:
                    # For pyscreenshot, bbox is (left, top, right, bottom)
                    if region:
                        bbox = (region["left"], region["top"], region["left"] + region["width"], region["top"] + region["height"])
                        img = ImageGrab.grab(bbox=bbox)
                    else:
                        img = ImageGrab.grab() # Full screen

                    # Convert PIL Image to bytes for pytesseract
                    with io.BytesIO() as output:
                        img.save(output, format="PNG") # Save as PNG for consistent format
                        sct_img_bytes = output.getvalue()
                    
                    # Basic check for positive dimensions, actual boundary check is complex with pyscreenshot
                    if region:
                        if region["width"] <= 0 or region["height"] <= 0:
                            return self._handle_error("Region width and height must be positive values.")
                    
                except Exception as e:
                    return self._handle_error(f"Failed to capture screenshot using pyscreenshot: {e}. Ensure a backend like Pillow is installed and screen sharing is enabled if necessary.")

            if sct_img_bytes is None:
                return self._handle_error("Screenshot capture failed to produce image data.")

            # Convert image bytes to PIL Image
            img = Image.open(io.BytesIO(sct_img_bytes))

            # Use pytesseract to extract text
            text = pytesseract.image_to_string(img)

            # Clean up potentially empty text
            cleaned_text = text.strip()

            return self._handle_success(
                "Screenshot and text extraction successful.",
                {
                    "text": cleaned_text,
                },
            )

        except ScreenShotError as e:
            return self._handle_error(f"macOS screenshot error: {e}")
        except pytesseract.TesseractError as e:
            return self._handle_error(f"Tesseract OCR failed: {e}")
        except Exception as e:
            # Catch any other unexpected exceptions
            return self._handle_error(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    try:
        reader = ScreenshotTextReader()

        # Example 1: Take screenshot of the entire screen and read text
        print("--- Attempting to read text from the entire screen ---")
        result_full = reader.take_and_read_screenshot()
        if result_full["success"]:
            print("Full screen text extraction successful:")
            print(f"Extracted Text:\n---\n{result_full['data']['text']}\n---")
        else:
            print(f"Full screen text extraction failed: {result_full['message']}")

        print("\n" + "="*50 + "\n")

        # Example 2: Take screenshot of a specific region and read text
        # Note: Adjust these coordinates based on your screen resolution and desired region.
        print("--- Attempting to read text from a specific region ---")
        custom_region = {
            "top": 100,
            "left": 100,
            "width": 400,
            "height": 300,
        }
        result_region = reader.take_and_read_screenshot(region=custom_region)
        if result_region["success"]:
            print("Region text extraction successful:")
            print(f"Extracted Text:\n---\n{result_region['data']['text']}\n---")
        else:
            print(f"Region text extraction failed: {result_region['message']}")

        print("\n" + "="*50 + "\n")

        # Example 3: Invalid region - negative width
        print("--- Attempting with an invalid region (negative width) ---")
        invalid_region_neg_width = {"top": 100, "left": 100, "width": -10, "height": 50}
        result_invalid_neg = reader.take_and_read_screenshot(region=invalid_region_neg_width)
        if not result_invalid_neg["success"]:
            print(f"Invalid region handling successful (as expected): {result_invalid_neg['message']}")
        else:
            print("Error: Invalid region test failed to report an error.")

        print("\n" + "="*50 + "\n")

        # Example 4: Invalid region - missing key
        print("--- Attempting with an invalid region (missing key) ---")
        invalid_region_missing_key = {"top": 100, "width": 50, "height": 50}
        result_invalid_key = reader.take_and_read_screenshot(region=invalid_region_missing_key)
        if not result_invalid_key["success"]:
            print(f"Invalid region handling successful (as expected): {result_invalid_key['message']}")
        else:
            print("Error: Invalid region test failed to report an error.")

    except ImportError as e:
        print(f"Critical Error: {e}", file=sys.stderr)
        print("Please ensure you have installed all required libraries.", file=sys.stderr)
    except EnvironmentError as e:
        print(f"Critical Error: {e}", file=sys.stderr)
        print("Please ensure Tesseract OCR is installed and configured correctly.", file=sys.stderr)
    except RuntimeError as e:
        print(f"Critical Error: {e}", file=sys.stderr)
    except Exception as e:
        print(f"An unhandled error occurred during example execution: {e}", file=sys.stderr)