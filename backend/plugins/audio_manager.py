"""Audio Manager Plugin - Handle audio transcription and processing using Gemini AI"""

import logging
import base64
import json
import threading
import time
import queue
# Removed: import subprocess, tempfile, os (no longer needed for audio functionality)
from typing import Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)

class AudioManager:
    def __init__(self):
        self.is_initialized = True
        self.use_gemini = True  # Default to Gemini for audio analysis
        self.is_continuous_capture_active = False
        self.continuous_capture_thread = None
        self.audio_queue = queue.Queue()
        self.capture_callback = None
        self.system_prompt = (
            "Provide direct answers only. After your answer, add 2-3 sentences of brief reasoning or helpful context. "
            "For mathematical expressions, use proper LaTeX formatting with $ for inline math and $$ for display math (e.g., $x^2$, $$\\frac{d}{dx}(x^n) = nx^{n-1}$$). "
            "Use clear formatting with appropriate markdown for structure, but avoid excessive styling. "
            "You are an AI assistant that analyzes audio content. Provide accurate transcriptions and descriptions of audio clips."
        )
        
        # Initialize Gemini AI for audio analysis
        self.gemini_ai = None
        try:
            from core.gemini_ai import GeminiAI
            from utils.config import Config
            config = Config()
            gemini_api_key = config.get('apis.gemini.api_key')
            if gemini_api_key:
                self.gemini_ai = GeminiAI(gemini_api_key)
                logger.info("Gemini AI initialized for audio analysis")
            else:
                logger.warning("Gemini API key not found. Audio analysis will be limited.")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini AI: {e}")
            self.gemini_ai = None
        
        # Try to import pyaudio for system audio capture
        try:
            import pyaudio
            self.pyaudio = pyaudio
            self.system_audio_available = True
            logger.info("System audio capture initialized successfully")
        except ImportError:
            logger.warning("PyAudio not available. System audio capture will be limited.")
            self.system_audio_available = False
    
    def analyze_audio_from_base64(self, data: str, mime_type: str = "audio/webm") -> Dict[str, Any]:
        """Analyze audio from base64 data using Gemini AI.
        
        Args:
            data: Base64 encoded audio data
            mime_type: MIME type of the audio (e.g., 'audio/webm', 'audio/mp3')
            
        Returns:
            Dictionary with analysis results
        """
        try:
            if not self.gemini_ai:
                return {
                    "success": False,
                    "error": "Gemini AI not available",
                    "text": ""
                }
            
            # Create audio part for Gemini
            audio_part = {
                "inline_data": {
                    "data": data,
                    "mime_type": mime_type
                }
            }
            
            # Create prompt for audio analysis
            prompt = f"{self.system_prompt}\n\nDescribe this audio clip in a short, concise answer. Focus on transcribing any speech content."
            
            # Generate content using Gemini
            result = self.gemini_ai.model.generate_content([prompt, audio_part])
            text = result.text
            
            return {
                "success": True,
                "text": text,
                "timestamp": int(time.time() * 1000),
                "using_gemini": True
            }
            
        except Exception as e:
            logger.error(f"Error analyzing audio from base64: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": ""
            }
    
    def transcribe_audio(self, audio_data: str, use_gemini: bool = True) -> Dict[str, Any]:
        """Transcribe audio data to text using Gemini AI.
        
        Args:
            audio_data: Base64 encoded audio data
            use_gemini: Whether to use Gemini model for transcription (default True)
            
        Returns:
            Dictionary with transcription results
        """
        # Use the new Gemini-based analysis method
        return self.analyze_audio_from_base64(audio_data, "audio/webm")

    
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
    
    def start_continuous_capture(self, callback: Callable[[str], None], chunk_duration: int = 3) -> Dict[str, Any]:
        """Start continuous audio capture for real-time transcription.
        
        Args:
            callback: Function to call with each audio chunk (base64 encoded)
            chunk_duration: Duration of each audio chunk in seconds
            
        Returns:
            Dictionary with operation status
        """
        try:
            if self.is_continuous_capture_active:
                return {
                    "success": False,
                    "error": "Continuous capture already active"
                }
            
            if not self.system_audio_available:
                return {
                    "success": False,
                    "error": "System audio capture not available"
                }
            
            self.capture_callback = callback
            self.is_continuous_capture_active = True
            
            # Start the continuous capture thread
            self.continuous_capture_thread = threading.Thread(
                target=self._continuous_capture_worker,
                args=(chunk_duration,),
                daemon=True
            )
            self.continuous_capture_thread.start()
            
            logger.info(f"Started continuous audio capture with {chunk_duration}s chunks")
            return {
                "success": True,
                "message": "Continuous capture started"
            }
            
        except Exception as e:
            logger.error(f"Error starting continuous capture: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def stop_continuous_capture(self) -> Dict[str, Any]:
        """Stop continuous audio capture.
        
        Returns:
            Dictionary with operation status
        """
        try:
            if not self.is_continuous_capture_active:
                return {
                    "success": False,
                    "error": "Continuous capture not active"
                }
            
            self.is_continuous_capture_active = False
            self.capture_callback = None
            
            # Wait for thread to finish
            if self.continuous_capture_thread and self.continuous_capture_thread.is_alive():
                self.continuous_capture_thread.join(timeout=2.0)
            
            logger.info("Stopped continuous audio capture")
            return {
                "success": True,
                "message": "Continuous capture stopped"
            }
            
        except Exception as e:
            logger.error(f"Error stopping continuous capture: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _continuous_capture_worker(self, chunk_duration: int):
        """Worker thread for continuous audio capture.
        
        Args:
            chunk_duration: Duration of each audio chunk in seconds
        """
        try:
            import pyaudio
            import wave
            import io
            import base64
            
            # Initialize PyAudio
            p = self.pyaudio.PyAudio()
            
            # Set parameters for audio capture
            FORMAT = pyaudio.paInt16
            CHANNELS = 1
            RATE = 44100
            CHUNK = 1024
            
            # For macOS system audio capture, we need to use a virtual audio device
            # This is a simplified implementation that captures microphone audio
            # In production, you would need to install and configure a virtual audio driver
            # like BlackHole or SoundFlower to capture system audio
            
            # Try to find the best input device (preferably one that can capture system audio)
            input_device_index = None
            for i in range(p.get_device_count()):
                device_info = p.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:
                    device_name = device_info['name'].lower()
                    # Look for virtual audio devices that might capture system audio
                    if any(keyword in device_name for keyword in ['blackhole', 'soundflower', 'virtual', 'aggregate']):
                        input_device_index = i
                        logger.info(f"Using audio device: {device_info['name']}")
                        break
            
            if input_device_index is None:
                # Fall back to default input device
                logger.info("Using default input device (microphone only)")
            
            # Open stream for recording
            stream = p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                input_device_index=input_device_index,
                frames_per_buffer=CHUNK
            )
            
            logger.info("Continuous audio capture started")
            
            while self.is_continuous_capture_active:
                try:
                    # Record audio chunk
                    frames = []
                    for i in range(0, int(RATE / CHUNK * chunk_duration)):
                        if not self.is_continuous_capture_active:
                            break
                        data = stream.read(CHUNK, exception_on_overflow=False)
                        frames.append(data)
                    
                    if not self.is_continuous_capture_active:
                        break
                    
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
                    
                    # Call the callback with the audio data
                    if self.capture_callback and audio_data:
                        self.capture_callback(audio_data)
                    
                except Exception as chunk_error:
                    logger.error(f"Error in continuous capture chunk: {str(chunk_error)}")
                    time.sleep(0.1)  # Brief pause before retrying
            
            # Clean up
            stream.stop_stream()
            stream.close()
            p.terminate()
            
        except Exception as e:
            logger.error(f"Error in continuous capture worker: {str(e)}")
            self.is_continuous_capture_active = False
    
    def get_system_audio_setup_info(self) -> Dict[str, Any]:
        """Get information about system audio setup for macOS.
        
        Returns:
            Dictionary with setup information and recommendations
        """
        try:
            import pyaudio
            p = self.pyaudio.PyAudio()
            
            devices = []
            virtual_devices = []
            
            for i in range(p.get_device_count()):
                device_info = p.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:
                    devices.append({
                        'index': i,
                        'name': device_info['name'],
                        'channels': device_info['maxInputChannels']
                    })
                    
                    device_name = device_info['name'].lower()
                    if any(keyword in device_name for keyword in ['blackhole', 'soundflower', 'virtual', 'aggregate']):
                        virtual_devices.append(device_info['name'])
            
            p.terminate()
            
            return {
                "success": True,
                "available_devices": devices,
                "virtual_devices": virtual_devices,
                "has_virtual_audio": len(virtual_devices) > 0,
                "recommendation": (
                    "Virtual audio device detected. System audio capture should work." 
                    if virtual_devices else 
                    "No virtual audio device detected. Install BlackHole or SoundFlower for system audio capture."
                )
            }
            
        except Exception as e:
            logger.error(f"Error getting audio setup info: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }