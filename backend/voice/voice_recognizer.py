"""
Voice Recognition module for continuous speech-to-text conversion.

Uses speech_recognition library with optimizations for real-time processing.
"""

import asyncio
import logging
import speech_recognition as sr
import threading
import queue
from typing import Optional, Callable
import time
import tempfile
import os

# Try to import whisper for offline recognition
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

logger = logging.getLogger(__name__)

class VoiceRecognizer:
    """Handles continuous voice recognition with real-time processing."""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self.is_ready = False
        self.is_listening = False
        self.audio_queue = queue.Queue()
        self.recognition_thread = None
        
        # Configure recognition settings for natural conversation
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 1.2  # Increased pause threshold for natural speech
        self.recognizer.phrase_threshold = 0.3
        
        # Enhanced pause detection settings
        self.conversation_pause_threshold = 3.0  # Seconds of silence to end conversation turn (Siri-like)
        self.max_phrase_duration = 30.0  # Maximum duration for a single phrase
        self.accumulated_audio_frames = []
        self.last_audio_time = 0
        self.is_accumulating = False
        
        # Disable Whisper for now to avoid segmentation fault
        self.whisper_model = None
        
        logger.info("VoiceRecognizer initialized")
    
    async def initialize(self) -> bool:
        """Initialize the voice recognizer and microphone."""
        try:
            # Initialize microphone with specific sample rate for better compatibility
            self.microphone = sr.Microphone(sample_rate=16000, chunk_size=1024)
            
            # Adjust for ambient noise
            logger.info("Adjusting for ambient noise...")
            with self.microphone as source:
                # Set sample rate for the recognizer
                source.SAMPLE_RATE = 16000
                source.CHUNK = 1024
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
            # Set optimized settings for stable Siri-like behavior
            self.recognizer.energy_threshold = 400  # Balanced threshold to avoid false triggers
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 1.0  # Slightly longer pause detection for stability
            
            logger.info(f"Energy threshold set to: {self.recognizer.energy_threshold}")
            
            self.is_ready = True
            logger.info("Voice recognizer initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize voice recognizer: {e}")
            return False
    
    async def listen(self) -> Optional[str]:
        """Listen for voice input and return transcribed text."""
        if not self.is_ready:
            logger.warning("Voice recognizer not ready")
            return None
        
        try:
            # Listen for audio with timeout
            with self.microphone as source:
                # Listen with a short timeout to keep the loop responsive
                audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
            
            # Recognize speech using Google's service (you can switch to offline later)
            text = self.recognizer.recognize_google(audio)
            
            if text:
                logger.debug(f"Recognized: {text}")
                return text.strip()
            
        except sr.WaitTimeoutError:
            # Normal timeout, no speech detected
            return None
        except sr.UnknownValueError:
            # Speech was unintelligible
            logger.debug("Could not understand audio")
            return None
        except sr.RequestError as e:
            logger.error(f"Recognition service error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in voice recognition: {e}")
            return None
        
        return None
    
    def start_natural_listening(self, callback: Callable[[str], None]):
        """Start natural conversation listening with pause detection (like Siri)."""
        if self.is_listening:
            logger.warning("Already listening")
            return
        
        self.is_listening = True
        self.accumulated_audio_frames = []
        self.is_accumulating = False
        
        def listen_naturally():
            """Background thread function for natural conversation listening."""
            try:
                with self.microphone as source:
                    logger.info("Starting natural conversation listening")
                    
                    while self.is_listening:
                        try:
                            # Listen for audio with optimized timeout for stable microphone behavior
                            audio = self.recognizer.listen(
                                source, 
                                timeout=1.0,  # Longer timeout to reduce frequent mic state changes
                                phrase_time_limit=None  # No limit on phrase length
                            )
                            
                            current_time = time.time()
                            
                            # If we're not accumulating, start a new conversation turn
                            if not self.is_accumulating:
                                self.accumulated_audio_frames = []
                                self.is_accumulating = True
                                self.last_audio_time = current_time
                                logger.info("🎤 Started listening - audio detected")
                            
                            # Add audio to accumulated frames
                            logger.debug("🔊 Audio chunk received, accumulating...")
                            self.accumulated_audio_frames.append(audio)
                            self.last_audio_time = current_time
                            
                            # Check if we should process the accumulated audio
                            # (either max duration reached or we'll check for pause in the next timeout)
                            if current_time - self.last_audio_time >= self.max_phrase_duration:
                                self._process_accumulated_audio(callback)
                                
                        except sr.WaitTimeoutError:
                            # Check if we have accumulated audio and enough silence has passed
                            if self.is_accumulating:
                                silence_duration = time.time() - self.last_audio_time
                                if silence_duration >= self.conversation_pause_threshold:
                                    logger.info(f"🎤 Detected conversation pause ({silence_duration:.1f}s), processing accumulated audio")
                                    self._process_accumulated_audio(callback)
                                else:
                                    logger.debug(f"🔇 Silence detected ({silence_duration:.1f}s), waiting for {self.conversation_pause_threshold}s threshold")
                            else:
                                logger.debug("🎧 Microphone listening, waiting for speech...")
                            continue
                            
                        except Exception as e:
                            logger.error(f"Error in natural listening: {e}")
                            time.sleep(0.1)
                            
            except Exception as e:
                logger.error(f"Error setting up natural listening: {e}")
                self.is_listening = False
        
        self.recognition_thread = threading.Thread(target=listen_naturally, daemon=True)
        self.recognition_thread.start()
        logger.info("Started natural conversation listening")
    
    def _process_accumulated_audio(self, callback: Callable[[str], None]):
        """Process accumulated audio frames as a complete conversation turn."""
        if not self.accumulated_audio_frames:
            return
        
        try:
            # Combine all accumulated audio frames
            combined_audio = self._combine_audio_frames(self.accumulated_audio_frames)
            
            # Reset accumulation state
            self.accumulated_audio_frames = []
            self.is_accumulating = False
            
            # Process the combined audio in a separate thread
            threading.Thread(
                target=self._process_audio,
                args=(combined_audio, callback),
                daemon=True
            ).start()
            
        except Exception as e:
            logger.error(f"Error processing accumulated audio: {e}")
            self.accumulated_audio_frames = []
            self.is_accumulating = False
    
    def _combine_audio_frames(self, audio_frames):
        """Combine multiple audio frames into a single audio object."""
        if not audio_frames:
            return None
        
        if len(audio_frames) == 1:
            return audio_frames[0]
        
        try:
            # Combine frame data from all audio objects
            combined_frame_data = b''
            sample_rate = audio_frames[0].sample_rate
            sample_width = audio_frames[0].sample_width
            
            for audio in audio_frames:
                combined_frame_data += audio.frame_data
            
            # Create new AudioData object with combined frames
            combined_audio = sr.AudioData(combined_frame_data, sample_rate, sample_width)
            return combined_audio
            
        except Exception as e:
            logger.error(f"Error combining audio frames: {e}")
            # Fallback to first frame if combination fails
            return audio_frames[0]
    
    def start_continuous_listening(self, callback: Callable[[str], None]):
        """Start continuous listening in background thread."""
        if self.is_listening:
            logger.warning("Already listening")
            return
        
        self.is_listening = True
        
        def listen_continuously():
            """Background thread function for continuous listening."""
            try:
                # Use the microphone context manager once for the entire listening session
                with self.microphone as source:
                    logger.info("Starting continuous listening session")
                    while self.is_listening:
                        try:
                            # Listen for audio without using context manager again
                            audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                            
                            # Process in background
                            threading.Thread(
                                target=self._process_audio,
                                args=(audio, callback),
                                daemon=True
                            ).start()
                            
                        except sr.WaitTimeoutError:
                            continue
                        except Exception as e:
                            logger.error(f"Unexpected error in voice recognition: {e}")
                            time.sleep(0.1)  # Short pause before retrying
                            
            except Exception as e:
                logger.error(f"Error setting up continuous listening: {e}")
                self.is_listening = False
        
        self.recognition_thread = threading.Thread(target=listen_continuously, daemon=True)
        self.recognition_thread.start()
        logger.info("Started continuous listening")
    
    def _process_audio(self, audio, callback: Callable[[str], None]):
        """Process audio in background thread."""
        try:
            # Log audio details for debugging
            logger.debug(f"Processing audio: {len(audio.frame_data)} bytes, "
                        f"sample_rate={audio.sample_rate}, sample_width={audio.sample_width}")
            
            # Try Google recognition with proper language setting
            text = self.recognizer.recognize_google(audio, language='en-US')
            if text and text.strip():
                logger.info(f"Voice recognition successful: {text.strip()}")
                callback(text.strip())
                return
        except sr.UnknownValueError:
            logger.debug("Could not understand audio - speech may be unclear or too quiet")
            pass  # Ignore unintelligible audio
        except sr.RequestError as e:
            logger.warning(f"Google recognition service error: {e}")
            # Try with FLAC conversion as fallback
            try:
                logger.debug("Trying FLAC conversion fallback...")
                # Convert audio to FLAC format for better compatibility
                flac_data = audio.get_flac_data(
                    convert_rate=16000,  # 16kHz sample rate
                    convert_width=2      # 16-bit samples
                )
                # Create new AudioData with FLAC data
                flac_audio = sr.AudioData(flac_data, 16000, 2)
                text = self.recognizer.recognize_google(flac_audio, language='en-US')
                if text and text.strip():
                    logger.info(f"Voice recognition successful (FLAC): {text.strip()}")
                    callback(text.strip())
            except Exception as flac_error:
                logger.error(f"FLAC conversion fallback failed: {flac_error}")
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            # Try with original audio as final fallback
            try:
                logger.debug("Trying basic recognition fallback...")
                text = self.recognizer.recognize_google(audio)
                if text and text.strip():
                    logger.info(f"Voice recognition successful (basic): {text.strip()}")
                    callback(text.strip())
            except Exception as fallback_error:
                logger.debug(f"All recognition methods failed: {fallback_error}")
    
    def _recognize_with_whisper(self, audio) -> Optional[str]:
        """Use Whisper for offline speech recognition."""
        if self.whisper_model is None:
            return None
        
        try:
            # Convert audio to temporary WAV file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = temp_file.name
                
            # Write audio data to temporary file
            with open(temp_path, "wb") as f:
                f.write(audio.get_wav_data())
            
            # Use Whisper to transcribe
            result = self.whisper_model.transcribe(temp_path)
            text = result.get("text", "").strip()
            
            # Clean up temporary file
            os.unlink(temp_path)
            
            return text if text else None
            
        except Exception as e:
            logger.error(f"Whisper recognition error: {e}")
            return None
    
    async def stop(self):
        """Stop voice recognition."""
        self.is_listening = False
        if self.recognition_thread and self.recognition_thread.is_alive():
            self.recognition_thread.join(timeout=2)
        logger.info("Voice recognition stopped")
    
    def stop_listening(self):
        """Stop continuous listening (synchronous version)."""
        self.is_listening = False
        if self.recognition_thread and self.recognition_thread.is_alive():
            self.recognition_thread.join(timeout=2)
        logger.info("Voice recognition stopped")
    
    def set_sensitivity(self, energy_threshold: int = 300):
        """Adjust microphone sensitivity."""
        self.recognizer.energy_threshold = energy_threshold
        logger.info(f"Energy threshold set to {energy_threshold}")
    
    def calibrate(self, duration: float = 2.0):
        """Calibrate microphone for current environment."""
        if not self.microphone:
            logger.warning("Microphone not initialized")
            return
        
        try:
            with self.microphone as source:
                logger.info(f"Calibrating microphone for {duration} seconds...")
                self.recognizer.adjust_for_ambient_noise(source, duration=duration)
            logger.info("Microphone calibration complete")
        except Exception as e:
            logger.error(f"Calibration failed: {e}")