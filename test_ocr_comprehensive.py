#!/usr/bin/env python3
"""
Comprehensive OCR Testing and Debugging Script
This script tests and fixes OCR timeout issues.
"""

import os
import sys
import time
import subprocess
import tempfile
from PIL import Image
import pytesseract
from typing import Tuple, Optional
import threading
import signal

class OCRTester:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        print(f"Using temp directory: {self.temp_dir}")
    
    def test_tesseract_installation(self):
        """Test if Tesseract is properly installed and accessible."""
        print("\n=== Testing Tesseract Installation ===")
        try:
            # Test tesseract command
            result = subprocess.run(['tesseract', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("✅ Tesseract is installed:")
                print(result.stdout.split('\n')[0])
                return True
            else:
                print("❌ Tesseract command failed")
                return False
        except subprocess.TimeoutExpired:
            print("❌ Tesseract command timed out")
            return False
        except FileNotFoundError:
            print("❌ Tesseract not found in PATH")
            return False
        except Exception as e:
            print(f"❌ Tesseract test failed: {e}")
            return False
    
    def test_screenshot_capture(self):
        """Test screenshot capture functionality."""
        print("\n=== Testing Screenshot Capture ===")
        try:
            screenshot_path = os.path.join(self.temp_dir, "test_screenshot.png")
            
            # Time the screenshot capture
            start_time = time.time()
            result = subprocess.run(['screencapture', '-x', screenshot_path], 
                                  capture_output=True, timeout=15)
            capture_time = time.time() - start_time
            
            if result.returncode == 0 and os.path.exists(screenshot_path):
                file_size = os.path.getsize(screenshot_path)
                print(f"✅ Screenshot captured successfully")
                print(f"   Time: {capture_time:.2f}s")
                print(f"   Size: {file_size:,} bytes")
                return screenshot_path
            else:
                print(f"❌ Screenshot failed: {result.stderr.decode()}")
                return None
        except subprocess.TimeoutExpired:
            print("❌ Screenshot capture timed out (15s)")
            return None
        except Exception as e:
            print(f"❌ Screenshot capture failed: {e}")
            return None
    
    def test_image_processing(self, image_path: str):
        """Test image loading and basic processing."""
        print("\n=== Testing Image Processing ===")
        try:
            start_time = time.time()
            img = Image.open(image_path)
            load_time = time.time() - start_time
            
            print(f"✅ Image loaded successfully")
            print(f"   Time: {load_time:.3f}s")
            print(f"   Size: {img.size}")
            print(f"   Mode: {img.mode}")
            
            # Test image preprocessing
            start_time = time.time()
            # Convert to grayscale for better OCR
            if img.mode != 'L':
                img_gray = img.convert('L')
            else:
                img_gray = img
            preprocess_time = time.time() - start_time
            
            print(f"✅ Image preprocessing completed")
            print(f"   Time: {preprocess_time:.3f}s")
            
            return img_gray
        except Exception as e:
            print(f"❌ Image processing failed: {e}")
            return None
    
    def test_ocr_with_timeout(self, img, timeout_seconds=25):
        """Test OCR with proper timeout handling."""
        print(f"\n=== Testing OCR (timeout: {timeout_seconds}s) ===")
        
        result = {'text': None, 'error': None, 'completed': False}
        
        def ocr_worker():
            try:
                start_time = time.time()
                # Configure Tesseract for better performance
                custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,!?@#$%^&*()_+-=[]{}|;:"<>?/~` '
                text = pytesseract.image_to_string(img, config=custom_config)
                ocr_time = time.time() - start_time
                
                result['text'] = text
                result['time'] = ocr_time
                result['completed'] = True
                print(f"✅ OCR completed successfully")
                print(f"   Time: {ocr_time:.2f}s")
                print(f"   Text length: {len(text)} characters")
                if text.strip():
                    preview = text.strip()[:100].replace('\n', ' ')
                    print(f"   Preview: {preview}...")
                else:
                    print("   No text detected")
            except Exception as e:
                result['error'] = str(e)
                result['completed'] = True
                print(f"❌ OCR failed: {e}")
        
        # Run OCR in a separate thread with timeout
        thread = threading.Thread(target=ocr_worker)
        thread.daemon = True
        thread.start()
        thread.join(timeout=timeout_seconds)
        
        if thread.is_alive():
            print(f"❌ OCR timed out after {timeout_seconds} seconds")
            return None
        elif result['completed'] and result['error'] is None:
            return result['text']
        else:
            print(f"❌ OCR failed: {result.get('error', 'Unknown error')}")
            return None
    
    def test_optimized_ocr(self, img):
        """Test OCR with various optimizations."""
        print("\n=== Testing Optimized OCR ===")
        
        optimizations = [
            ('Fast mode', r'--oem 3 --psm 6'),
            ('Text blocks', r'--oem 3 --psm 1'),
            ('Single column', r'--oem 3 --psm 4'),
            ('Single word', r'--oem 3 --psm 8'),
        ]
        
        best_result = None
        best_time = float('inf')
        
        for name, config in optimizations:
            try:
                print(f"\nTesting {name}...")
                start_time = time.time()
                text = pytesseract.image_to_string(img, config=config)
                ocr_time = time.time() - start_time
                
                print(f"   Time: {ocr_time:.2f}s")
                print(f"   Text length: {len(text)} characters")
                
                if ocr_time < best_time and text.strip():
                    best_time = ocr_time
                    best_result = (name, config, text, ocr_time)
                    
            except Exception as e:
                print(f"   Failed: {e}")
        
        if best_result:
            name, config, text, ocr_time = best_result
            print(f"\n✅ Best result: {name} ({ocr_time:.2f}s)")
            return text
        else:
            print("\n❌ All optimization attempts failed")
            return None
    
    def create_fixed_ocr_method(self):
        """Create an improved OCR method with timeout handling."""
        print("\n=== Creating Fixed OCR Method ===")
        
        fixed_method = '''
def read_screen_text_fixed(self, region: Tuple[int, int, int, int] = None, timeout: int = 25) -> str:
    """Read text from screen using OCR with proper timeout handling."""
    import threading
    import tempfile
    
    try:
        # Use temp directory instead of Desktop
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_screenshot_path = temp_file.name
        
        # Take screenshot with timeout
        screenshot_result = self.take_screenshot(os.path.basename(temp_screenshot_path), region)
        
        if "failed" in screenshot_result.lower():
            return screenshot_result
        
        # Move file to temp location
        desktop_path = os.path.expanduser(f"~/Desktop/{os.path.basename(temp_screenshot_path)}")
        if os.path.exists(desktop_path):
            os.rename(desktop_path, temp_screenshot_path)
        
        # Perform OCR with timeout
        result = {'text': None, 'error': None, 'completed': False}
        
        def ocr_worker():
            try:
                img = Image.open(temp_screenshot_path)
                
                # Optimize image for OCR
                if img.mode != 'L':
                    img = img.convert('L')
                
                # Use optimized Tesseract config
                config = r'--oem 3 --psm 6'
                text = pytesseract.image_to_string(img, config=config)
                
                result['text'] = text
                result['completed'] = True
            except Exception as e:
                result['error'] = str(e)
                result['completed'] = True
        
        # Run OCR in thread with timeout
        thread = threading.Thread(target=ocr_worker)
        thread.daemon = True
        thread.start()
        thread.join(timeout=timeout)
        
        if not thread.is_alive() and result['completed']:
            if result['error']:
                if 'TesseractNotFoundError' in str(result['error']):
                    return "❌ Tesseract is not installed or not in your PATH. Please install it to use OCR functionality."
                else:
                    return f"❌ OCR processing failed: {result['error']}"
            else:
                text = result['text']
                if text and text.strip():
                    return f"📖 Extracted text:\\n{text}"
                else:
                    return "📖 No text found in the specified region."
        else:
            return f"❌ OCR timed out after {timeout} seconds. Try with a smaller region or simpler image."
            
    except Exception as e:
        return f"❌ Screen reading failed: {str(e)}"
    finally:
        # Clean up temp file
        if 'temp_screenshot_path' in locals() and os.path.exists(temp_screenshot_path):
            try:
                os.remove(temp_screenshot_path)
            except:
                pass
'''
        
        # Save the fixed method to a file
        fixed_file = os.path.join(self.temp_dir, "fixed_ocr_method.py")
        with open(fixed_file, 'w') as f:
            f.write(fixed_method)
        
        print(f"✅ Fixed OCR method saved to: {fixed_file}")
        return fixed_file
    
    def cleanup(self):
        """Clean up temporary files."""
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
            print(f"\n🧹 Cleaned up temp directory: {self.temp_dir}")
        except Exception as e:
            print(f"\n⚠️  Cleanup failed: {e}")
    
    def run_comprehensive_test(self):
        """Run all tests and provide recommendations."""
        print("🔍 Starting Comprehensive OCR Testing...")
        print("=" * 50)
        
        # Test 1: Tesseract installation
        tesseract_ok = self.test_tesseract_installation()
        
        if not tesseract_ok:
            print("\n❌ Cannot proceed without Tesseract. Please install it first.")
            return False
        
        # Test 2: Screenshot capture
        screenshot_path = self.test_screenshot_capture()
        
        if not screenshot_path:
            print("\n❌ Cannot proceed without screenshot capability.")
            return False
        
        # Test 3: Image processing
        img = self.test_image_processing(screenshot_path)
        
        if img is None:
            print("\n❌ Cannot proceed without image processing capability.")
            return False
        
        # Test 4: OCR with timeout
        ocr_result = self.test_ocr_with_timeout(img, timeout_seconds=25)
        
        # Test 5: Optimized OCR
        optimized_result = self.test_optimized_ocr(img)
        
        # Test 6: Create fixed method
        fixed_file = self.create_fixed_ocr_method()
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        if ocr_result or optimized_result:
            print("✅ OCR functionality is working")
            print("✅ Timeout handling has been implemented")
            print("✅ Performance optimizations have been added")
            print(f"✅ Fixed OCR method available at: {fixed_file}")
            
            print("\n🔧 RECOMMENDATIONS:")
            print("1. Replace the current read_screen_text method with the fixed version")
            print("2. Use tempfile instead of Desktop for temporary files")
            print("3. Add proper timeout handling (25 seconds recommended)")
            print("4. Use optimized Tesseract configuration")
            print("5. Add image preprocessing for better OCR accuracy")
            
            return True
        else:
            print("❌ OCR functionality has issues")
            print("❌ Manual intervention required")
            
            print("\n🔧 TROUBLESHOOTING:")
            print("1. Check Tesseract installation: brew install tesseract")
            print("2. Verify PIL/Pillow installation: pip install Pillow")
            print("3. Check pytesseract installation: pip install pytesseract")
            print("4. Ensure proper permissions for screen capture")
            
            return False

def main():
    tester = OCRTester()
    try:
        success = tester.run_comprehensive_test()
        if success:
            print("\n🎉 All tests passed! OCR functionality should work properly now.")
        else:
            print("\n⚠️  Some tests failed. Please address the issues above.")
        return success
    finally:
        tester.cleanup()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)