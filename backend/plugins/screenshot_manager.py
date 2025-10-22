"""Screenshot Manager Plugin - Handle screenshot capture and AI analysis"""

import subprocess
import tempfile
import os
import base64
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ScreenshotManager:
    def __init__(self):
        self.is_initialized = True
        
        # Initialize Gemini AI for screenshot analysis
        self.gemini_ai = None
        try:
            from core.gemini_ai import GeminiAI
            from utils.config import Config
            config = Config()
            gemini_api_key = config.get('apis.gemini.api_key')
            if gemini_api_key:
                self.gemini_ai = GeminiAI(gemini_api_key)
                logger.info("Gemini AI initialized for screenshot analysis")
            else:
                logger.warning("Gemini API key not found. Screenshot analysis will be limited.")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini AI: {e}")
            self.gemini_ai = None
    
    def capture_screenshot_and_analyze(self) -> Dict[str, Any]:
        """Capture a screenshot and analyze it with AI to answer questions on screen
        
        Returns:
            Dictionary with analysis results or error information
        """
        try:
            if not self.gemini_ai:
                return {
                    "success": False,
                    "error": "Gemini AI not available for screenshot analysis"
                }
            
            # Create temporary file for screenshot
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                temp_path = temp_file.name
            
            try:
                # Capture screenshot using macOS screencapture command
                result = subprocess.run(
                    ['screencapture', '-x', temp_path],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode != 0:
                    return {
                        "success": False,
                        "error": f"Screenshot capture failed: {result.stderr}"
                    }
                
                # Read and encode the screenshot
                with open(temp_path, 'rb') as img_file:
                    image_data = img_file.read()
                    image_base64 = base64.b64encode(image_data).decode('utf-8')
                
                # Create the prompt for AI analysis
                prompt = (
                    "Provide the direct answer to the question(s) on the screen. Look carefully at the image and identify any questions, problems, or tasks that need to be answered or solved. "
                    "After your answer, add 2-3 sentences of brief reasoning or helpful context. For programming problems, include time complexity and Big O notation at the end. "
                    "For mathematical expressions, use proper LaTeX formatting with $ for inline math and $$ for display math (e.g., $x^2$, $$\\frac{d}{dx}(x^n) = nx^{n-1}$$). "
                    "Use clear formatting with appropriate markdown for structure, but avoid excessive styling."
                )
                
                # Send to Gemini AI for analysis
                import google.generativeai as genai
                
                # Create image part for Gemini
                image_part = {
                    "mime_type": "image/png",
                    "data": image_base64
                }
                
                # Generate content with image and prompt
                response = self.gemini_ai.model.generate_content([prompt, image_part])
                
                if response and response.text:
                    logger.info("Screenshot analysis completed successfully")
                    return {
                        "success": True,
                        "text": response.text,
                        "message": "Screenshot captured and analyzed successfully"
                    }
                else:
                    return {
                        "success": False,
                        "error": "No response from AI analysis"
                    }
                    
            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Screenshot capture timed out"
            }
        except Exception as e:
            logger.error(f"Error in screenshot analysis: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }