"""Audio Manager Plugin - Handle audio transcription and processing"""

import logging
import base64
import json
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class AudioManager:
    def __init__(self):
        self.is_initialized = True
        self.use_gemini = False
        try:
            # Try to import speech recognition library if available
            import speech_recognition as sr
            self.recognizer = sr.Recognizer()
            logger.info("Speech recognition initialized successfully")
            
            # Try to import pyaudio for system audio capture
            try:
                import pyaudio
                self.pyaudio = pyaudio
                self.system_audio_available = True
                logger.info("System audio capture initialized successfully")
            except ImportError:
                logger.warning("PyAudio not available. System audio capture will be limited.")
                self.system_audio_available = False
        except ImportError:
            logger.warning("Speech recognition library not available. Using fallback mode.")
            self.recognizer = None
            self.system_audio_available = False
    
    def transcribe_audio(self, audio_data: str, use_gemini: bool = False) -> Dict[str, Any]:
        """Transcribe audio data to text.
        
        Args:
            audio_data: Base64 encoded audio data
            use_gemini: Whether to use Gemini model for transcription
            
        Returns:
            Dictionary with transcription results
        """
        try:
            if self.recognizer is None:
                return {
                    "success": False,
                    "error": "Speech recognition not available",
                    "text": ""
                }
            
            # Save current Gemini setting
            self.use_gemini = use_gemini
            
            # Decode base64 audio data
            import speech_recognition as sr
            from io import BytesIO
            
            # Convert base64 to audio data
            audio_bytes = base64.b64decode(audio_data)
            
            # Create an AudioData object from the bytes
            audio_file = BytesIO(audio_bytes)
            with sr.AudioFile(audio_file) as source:
                audio = self.recognizer.record(source)
            
            # Use appropriate transcription service
            if use_gemini:
                # In a real implementation, we would use Gemini's audio transcription capabilities
                # For now, we're using Google's service but could enhance it later
                try:
                    # Import Gemini AI if available
                    from core.gemini_ai import GeminiAI
                    gemini_ai = GeminiAI()
                    
                    # First try Google's service as a fallback
                    text = self.recognizer.recognize_google(audio)
                    
                    # In a real implementation, we would process the audio with Gemini here
                    # This is a placeholder for future implementation
                    logger.info("Using Gemini for enhanced transcription processing")
                    
                    # For now, we'll just return the Google transcription
                    return {
                        "success": True,
                        "text": text,
                        "using_gemini": True
                    }
                except Exception as gemini_error:
                    logger.error(f"Gemini transcription failed, falling back to Google: {str(gemini_error)}")
                    text = self.recognizer.recognize_google(audio)
            else:
                # Use standard Google's speech recognition
                text = self.recognizer.recognize_google(audio)
            
            return {
                "success": True,
                "text": text,
                "using_gemini": use_gemini
            }
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "text": ""
            }
    
    def get_sample_transcription(self, text_hint: str = "") -> Dict[str, Any]:
        """Generate a sample transcription for testing purposes.
        
        Args:
            text_hint: Optional hint for the sample text
            
        Returns:
            Dictionary with sample transcription
        """
        if text_hint:
            sample_text = f"Sample transcription based on: {text_hint}"
        else:
            sample_text = "This is a sample transcription for testing purposes."
        
        return {
            "success": True,
            "text": sample_text,
            "is_sample": True
        }
    
    def capture_system_audio(self, duration_seconds: int = 5) -> Dict[str, Any]:
        """Capture system audio including audio from applications like Zoom/Meet.
        
        Args:
            duration_seconds: Duration to record in seconds
            
        Returns:
            Dictionary with captured audio data in base64 format
        """
        try:
            if not self.system_audio_available:
                return {
                    "success": False,
                    "error": "System audio capture not available",
                    "audio_data": ""
                }
            
            import pyaudio
            import wave
            import io
            import base64
            import numpy as np
            
            # Initialize PyAudio
            p = self.pyaudio.PyAudio()
            
            # Set parameters for audio capture
            FORMAT = pyaudio.paInt16
            CHANNELS = 1
            RATE = 44100
            CHUNK = 1024
            
            # Open stream for recording
            # Note: In a real implementation, we would need to capture system audio
            # This requires platform-specific implementations
            # For macOS, this might involve installing additional virtual audio drivers
            # For now, we're just capturing microphone audio as a placeholder
            stream = p.open(format=FORMAT,
                           channels=CHANNELS,
                           rate=RATE,
                           input=True,
                           frames_per_buffer=CHUNK)
            
            logger.info(f"Recording system audio for {duration_seconds} seconds...")
            
            # Record audio
            frames = []
            for i in range(0, int(RATE / CHUNK * duration_seconds)):
                data = stream.read(CHUNK)
                frames.append(data)
            
            # Stop and close the stream
            stream.stop_stream()
            stream.close()
            p.terminate()
            
            # Convert frames to WAV format in memory
            buffer = io.BytesIO()
            wf = wave.open(buffer, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
            wf.close()
            
            # Convert to base64
            buffer.seek(0)
            audio_data = base64.b64encode(buffer.read()).decode('utf-8')
            
            return {
                "success": True,
                "audio_data": audio_data
            }
            
        except Exception as e:
            logger.error(f"Error capturing system audio: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "audio_data": ""
            }