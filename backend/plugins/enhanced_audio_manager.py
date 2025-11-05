"""Enhanced Audio Manager Plugin - Advanced audio capture with speaker diarization and system audio support"""

import logging
import base64
import json
import threading
import time
import queue
import numpy as np
import io
import wave
from typing import Dict, Any, Optional, Callable, List, Tuple
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)

class EnhancedAudioManager:
    def __init__(self):
        self.is_initialized = True
        self.use_gemini = True
        self.is_continuous_capture_active = False
        self.continuous_capture_thread = None
        self.audio_queue = queue.Queue()
        self.capture_callback = None
        
        # Speaker diarization components
        self.speaker_embeddings = {}  # Store speaker voice embeddings
        self.speaker_profiles = {}    # Persistent speaker profiles
        self.current_speakers = []    # Active speakers in current session
        
        # Audio processing parameters
        self.sample_rate = 44100
        self.chunk_size = 1024
        self.channels = 1
        self.vad_threshold = 0.01  # Voice Activity Detection threshold
        
        # Initialize components
        self._init_gemini_ai()
        self._init_audio_system()
        self._init_speaker_diarization()
        
    def _init_gemini_ai(self):
        """Initialize Gemini AI for audio analysis"""
        self.gemini_ai = None
        try:
            from core.gemini_ai import GeminiAI
            from utils.config import Config
            config = Config()
            gemini_api_key = config.get('apis.gemini.api_key')
            if gemini_api_key:
                self.gemini_ai = GeminiAI(gemini_api_key)
                logger.info("Gemini AI initialized for enhanced audio analysis")
            else:
                logger.warning("Gemini API key not found. Audio analysis will be limited.")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini AI: {e}")
            self.gemini_ai = None
    
    def _init_audio_system(self):
        """Initialize audio system with enhanced capabilities"""
        try:
            import pyaudio
            self.pyaudio = pyaudio
            self.system_audio_available = True
            logger.info("Enhanced audio system initialized successfully")
            
            # Check for virtual audio devices
            self._detect_virtual_audio_devices()
            
        except ImportError:
            logger.warning("PyAudio not available. Enhanced audio capture will be limited.")
            self.system_audio_available = False
    
    def _init_speaker_diarization(self):
        """Initialize speaker diarization system"""
        try:
            # Try to import required libraries for speaker diarization
            import librosa
            import sklearn
            self.speaker_diarization_available = True
            logger.info("Speaker diarization system initialized")
        except ImportError:
            logger.warning("Speaker diarization libraries not available. Install librosa and scikit-learn for full functionality.")
            self.speaker_diarization_available = False
    
    def _detect_virtual_audio_devices(self) -> List[Dict[str, Any]]:
        """Detect available virtual audio devices for system audio capture"""
        virtual_devices = []
        
        if not self.system_audio_available:
            return virtual_devices
        
        try:
            p = self.pyaudio.PyAudio()
            
            for i in range(p.get_device_count()):
                device_info = p.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:
                    device_name = device_info['name'].lower()
                    # Look for virtual audio devices
                    if any(keyword in device_name for keyword in ['blackhole', 'soundflower', 'virtual', 'aggregate', 'loopback']):
                        virtual_devices.append({
                            'index': i,
                            'name': device_info['name'],
                            'channels': device_info['maxInputChannels'],
                            'sample_rate': device_info['defaultSampleRate']
                        })
                        logger.info(f"Found virtual audio device: {device_info['name']}")
            
            p.terminate()
            
        except Exception as e:
            logger.error(f"Error detecting virtual audio devices: {e}")
        
        return virtual_devices
    
    def get_system_audio_setup_guide(self) -> Dict[str, Any]:
        """Provide setup guide for system audio capture on macOS"""
        virtual_devices = self._detect_virtual_audio_devices()
        
        setup_guide = {
            "has_virtual_audio": len(virtual_devices) > 0,
            "virtual_devices": virtual_devices,
            "setup_instructions": {
                "blackhole_install": [
                    "1. Download BlackHole from: https://github.com/ExistentialAudio/BlackHole",
                    "2. Install the .pkg file and restart your Mac",
                    "3. Go to System Preferences > Sound > Input",
                    "4. Select 'BlackHole 2ch' as input device",
                    "5. Create an Aggregate Device in Audio MIDI Setup to capture both system and mic audio"
                ],
                "aggregate_device_setup": [
                    "1. Open Audio MIDI Setup (Applications > Utilities)",
                    "2. Click '+' and select 'Create Aggregate Device'",
                    "3. Check both 'BlackHole 2ch' and your microphone",
                    "4. Set this aggregate device as your system input",
                    "5. Restart Apex backend to detect the new device"
                ]
            },
            "current_status": "Ready for system audio capture" if virtual_devices else "Virtual audio device required"
        }
        
        return setup_guide
    
    def apply_voice_activity_detection(self, audio_data: np.ndarray) -> bool:
        """Apply Voice Activity Detection to determine if audio contains speech"""
        try:
            # Calculate RMS energy
            rms_energy = np.sqrt(np.mean(audio_data ** 2))
            
            # Simple VAD based on energy threshold
            has_voice = rms_energy > self.vad_threshold
            
            # Additional checks for more sophisticated VAD
            if has_voice:
                # Check for spectral characteristics of speech
                # This is a simplified version - in production, use more advanced VAD
                zero_crossing_rate = np.mean(np.abs(np.diff(np.sign(audio_data))))
                has_voice = has_voice and zero_crossing_rate > 0.01
            
            return has_voice
            
        except Exception as e:
            logger.error(f"Error in VAD: {e}")
            return True  # Default to processing if VAD fails
    
    def enhance_audio_quality(self, audio_data: np.ndarray) -> np.ndarray:
        """Apply audio enhancement techniques"""
        try:
            # Remove DC offset
            audio_data = audio_data - np.mean(audio_data)

            # Normalize audio
            if np.max(np.abs(audio_data)) > 0:
                audio_data = audio_data / np.max(np.abs(audio_data)) * 0.8
            
            # Noise reduction: high-pass filter + simple spectral gating
            # Remove very low frequencies that are typically noise
            if len(audio_data) > 100:
                from scipy import signal
                # High-pass to remove hum/rumble
                b, a = signal.butter(3, 80, btype='high', fs=self.sample_rate)
                audio_hp = signal.filtfilt(b, a, audio_data)

                # Spectral gate: estimate noise floor and attenuate
                try:
                    import numpy as np
                    # STFT
                    frame_size = 1024
                    hop = 256
                    window = np.hanning(frame_size)
                    # Pad to full frames
                    pad_len = ((len(audio_hp) - frame_size) // hop + 2) * hop + frame_size
                    padded = np.pad(audio_hp, (0, max(0, pad_len - len(audio_hp))), mode='constant')
                    frames = []
                    for i in range(0, len(padded) - frame_size + 1, hop):
                        frames.append(padded[i:i+frame_size] * window)
                    frames = np.stack(frames, axis=0)
                    spec = np.fft.rfft(frames, axis=1)
                    mag = np.abs(spec)

                    # Noise estimate from quiet percentile per bin
                    noise_floor = np.percentile(mag, 10, axis=0)
                    # Thresholding with soft attenuation
                    threshold = noise_floor * 1.5
                    attenuation = 0.2
                    mask = mag >= threshold
                    mag_denoised = np.where(mask, mag, mag * attenuation)
                    # Reconstruct with original phase
                    phase = np.angle(spec)
                    spec_denoised = mag_denoised * np.exp(1j * phase)
                    frames_denoised = np.fft.irfft(spec_denoised, axis=1)

                    # Overlap-add
                    out = np.zeros(len(padded))
                    win_norm = np.zeros(len(padded))
                    for i in range(frames_denoised.shape[0]):
                        start = i * hop
                        out[start:start+frame_size] += frames_denoised[i] * window
                        win_norm[start:start+frame_size] += window ** 2
                    win_norm[win_norm == 0] = 1.0
                    audio_nr = out / win_norm
                    audio_data = audio_nr[:len(audio_hp)]
                except Exception:
                    # Fallback to only high-pass if STFT fails
                    audio_data = audio_hp
            
            # Automatic gain control
            target_rms = 0.1
            current_rms = np.sqrt(np.mean(audio_data ** 2))
            if current_rms > 0:
                gain = target_rms / current_rms
                gain = np.clip(gain, 0.1, 3.0)  # Limit gain range
                audio_data = audio_data * gain

            # Soft limiter to avoid clipping
            audio_data = np.tanh(audio_data)
            
            return audio_data
            
        except Exception as e:
            logger.error(f"Error enhancing audio: {e}")
            return audio_data  # Return original if enhancement fails
    
    def extract_speaker_embedding(self, audio_data: np.ndarray) -> Optional[np.ndarray]:
        """Extract speaker embedding from audio for diarization"""
        if not self.speaker_diarization_available:
            return None
        
        try:
            import librosa
            
            # Extract MFCC features as a simple speaker embedding
            mfccs = librosa.feature.mfcc(y=audio_data, sr=self.sample_rate, n_mfcc=13)
            
            # Calculate statistics over time to create speaker embedding
            embedding = np.concatenate([
                np.mean(mfccs, axis=1),
                np.std(mfccs, axis=1),
                np.max(mfccs, axis=1),
                np.min(mfccs, axis=1)
            ])
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error extracting speaker embedding: {e}")
            return None
    
    def identify_speaker(self, embedding: np.ndarray) -> str:
        """Identify speaker based on voice embedding"""
        if embedding is None or len(self.speaker_embeddings) == 0:
            # First speaker or no embedding
            speaker_id = f"Speaker_{len(self.speaker_embeddings) + 1}"
            self.speaker_embeddings[speaker_id] = embedding
            return speaker_id
        
        try:
            from sklearn.metrics.pairwise import cosine_similarity
            
            # Compare with existing speakers
            best_match = None
            best_similarity = 0.0
            similarity_threshold = 0.85  # Threshold for speaker identification
            
            for speaker_id, stored_embedding in self.speaker_embeddings.items():
                similarity = cosine_similarity([embedding], [stored_embedding])[0][0]
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = speaker_id
            
            if best_similarity > similarity_threshold:
                # Update the embedding with running average
                alpha = 0.1  # Learning rate
                self.speaker_embeddings[best_match] = (
                    (1 - alpha) * self.speaker_embeddings[best_match] + 
                    alpha * embedding
                )
                return best_match
            else:
                # New speaker
                speaker_id = f"Speaker_{len(self.speaker_embeddings) + 1}"
                self.speaker_embeddings[speaker_id] = embedding
                return speaker_id
                
        except Exception as e:
            logger.error(f"Error identifying speaker: {e}")
            return "Unknown_Speaker"
    
    def start_enhanced_continuous_capture(self, callback: Callable[[Dict[str, Any]], None], 
                                        chunk_duration: int = 5) -> Dict[str, Any]:
        """Start enhanced continuous audio capture with speaker diarization"""
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
            
            # Initialize latest transcription storage
            self.latest_transcription = None
            
            # Set up enhanced callback that also stores transcription
            def enhanced_callback(data):
                try:
                    # Transcribe the audio with speaker info
                    transcription_result = self.transcribe_with_speaker_info(data)
                    
                    if transcription_result.get('success') and transcription_result.get('text'):
                        # Store the latest transcription
                        self.latest_transcription = {
                            'text': transcription_result['text'],
                            'speaker_info': {
                                'speaker_id': data.get('speaker_id', 'Unknown_Speaker'),
                                'confidence': transcription_result.get('confidence', 0)
                            },
                            'confidence': transcription_result.get('confidence', 0),
                            'timestamp': time.time()
                        }
                        
                        logger.debug(f"Stored latest transcription: {self.latest_transcription['text'][:50]}...")
                    
                    # Call the original callback
                    if callback:
                        callback(data)
                        
                except Exception as e:
                    logger.error(f"Error in enhanced callback: {str(e)}")
            
            self.capture_callback = enhanced_callback
            self.is_continuous_capture_active = True
            
            # Start the enhanced capture thread
            self.continuous_capture_thread = threading.Thread(
                target=self._enhanced_capture_worker,
                args=(chunk_duration,),
                daemon=True
            )
            self.continuous_capture_thread.start()
            
            logger.info(f"Started enhanced continuous audio capture with {chunk_duration}s chunks")
            return {
                "success": True,
                "message": "Enhanced continuous capture started",
                "features": ["speaker_diarization", "voice_activity_detection", "audio_enhancement"]
            }
            
        except Exception as e:
            logger.error(f"Error starting enhanced continuous capture: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _enhanced_capture_worker(self, chunk_duration: int):
        """Enhanced worker thread for continuous audio capture with speaker diarization"""
        try:
            import pyaudio
            
            # Initialize PyAudio
            p = self.pyaudio.PyAudio()
            
            # Find the best input device (prefer virtual audio devices)
            virtual_devices = self._detect_virtual_audio_devices()
            input_device_index = virtual_devices[0]['index'] if virtual_devices else None
            
            if input_device_index is None:
                logger.info("Using default input device (microphone only)")
            else:
                logger.info(f"Using virtual audio device for system audio capture")
            
            # Open stream for recording
            stream = p.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=input_device_index,
                frames_per_buffer=self.chunk_size
            )
            
            logger.info("Enhanced continuous audio capture started")

            # Manage chunking with small overlap to avoid word cuts
            overlap_sec = 0.2
            overlap_samples = int(overlap_sec * self.sample_rate)
            tail_buffer = np.array([], dtype=np.float32)
            current_chunk_duration = chunk_duration
            
            while self.is_continuous_capture_active:
                try:
                    # Record audio chunk
                    frames = []
                    iterations = int(self.sample_rate / self.chunk_size * current_chunk_duration)
                    for i in range(0, iterations):
                        if not self.is_continuous_capture_active:
                            break
                        data = stream.read(self.chunk_size, exception_on_overflow=False)
                        frames.append(data)
                    
                    if not self.is_continuous_capture_active:
                        break
                    
                    # Convert to numpy array for processing
                    audio_bytes = b''.join(frames)
                    audio_array = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0

                    # Prepend overlap tail
                    if tail_buffer.size > 0:
                        audio_array = np.concatenate([tail_buffer, audio_array])
                    
                    # Apply Voice Activity Detection
                    has_voice = self.apply_voice_activity_detection(audio_array)
                    
                    if not has_voice:
                        logger.debug("No voice activity detected, skipping chunk")
                        # Increase chunk duration slightly on silence to reduce churn
                        current_chunk_duration = min(chunk_duration + 2, 8)
                        # Update tail buffer for next overlap
                        tail_buffer = audio_array[-overlap_samples:] if audio_array.size > overlap_samples else audio_array
                        continue
                    
                    # Reduce chunk duration on speech for snappier updates
                    current_chunk_duration = max(3, chunk_duration - 2)

                    # Enhance audio quality
                    enhanced_audio = self.enhance_audio_quality(audio_array)
                    
                    # Extract speaker embedding
                    speaker_embedding = self.extract_speaker_embedding(enhanced_audio)
                    speaker_id = self.identify_speaker(speaker_embedding) if speaker_embedding is not None else "Unknown_Speaker"
                    
                    # Convert back to WAV format
                    enhanced_audio_int16 = (enhanced_audio * 32767).astype(np.int16)
                    
                    buffer = io.BytesIO()
                    wf = wave.open(buffer, 'wb')
                    wf.setnchannels(self.channels)
                    wf.setsampwidth(2)  # 16-bit
                    wf.setframerate(self.sample_rate)
                    wf.writeframes(enhanced_audio_int16.tobytes())
                    wf.close()
                    
                    # Convert to base64
                    buffer.seek(0)
                    audio_data = base64.b64encode(buffer.read()).decode('utf-8')
                    
                    # Prepare enhanced callback data
                    enhanced_data = {
                        "audio_data": audio_data,
                        "speaker_id": speaker_id,
                        "timestamp": datetime.now().isoformat(),
                        "duration": current_chunk_duration,
                        "has_voice_activity": has_voice,
                        "audio_quality": "enhanced"
                    }

                    # Update overlap tail buffer
                    tail_buffer = audio_array[-overlap_samples:] if audio_array.size > overlap_samples else audio_array
                    
                    # Call the callback with enhanced data
                    if self.capture_callback and audio_data:
                        self.capture_callback(enhanced_data)
                    
                except Exception as chunk_error:
                    logger.error(f"Error in enhanced capture chunk: {str(chunk_error)}")
                    time.sleep(0.1)  # Brief pause before retrying
            
            # Clean up
            stream.stop_stream()
            stream.close()
            p.terminate()
            
        except Exception as e:
            logger.error(f"Error in enhanced capture worker: {str(e)}")
            self.is_continuous_capture_active = False
    
    def stop_continuous_capture(self) -> Dict[str, Any]:
        """Stop continuous audio capture"""
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
                self.continuous_capture_thread.join(timeout=3.0)
            
            logger.info("Stopped enhanced continuous audio capture")
            return {
                "success": True,
                "message": "Enhanced continuous capture stopped"
            }
            
        except Exception as e:
            logger.error(f"Error stopping enhanced continuous capture: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_latest_transcription_with_speaker(self) -> Optional[Dict[str, Any]]:
        """Get the latest transcription with speaker information"""
        try:
            if not hasattr(self, 'latest_transcription') or not self.latest_transcription:
                return None
                
            return {
                'text': self.latest_transcription.get('text', ''),
                'speaker_info': self.latest_transcription.get('speaker_info', {}),
                'confidence': self.latest_transcription.get('confidence', 0),
                'timestamp': self.latest_transcription.get('timestamp', time.time())
            }
            
        except Exception as e:
            logger.error(f"Error getting latest transcription: {str(e)}")
            return None
    
    def get_speaker_summary(self) -> Dict[str, Any]:
        """Get summary of identified speakers in current session"""
        return {
            "total_speakers": len(self.speaker_embeddings),
            "speakers": list(self.speaker_embeddings.keys()),
            "session_start": datetime.now().isoformat()
        }
    
    def transcribe_with_speaker_info(self, enhanced_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transcribe audio with speaker information"""
        try:
            if not self.gemini_ai:
                return {
                    "success": False,
                    "error": "Gemini AI not available"
                }
            
            # Use the existing transcription method but add speaker info
            audio_data = enhanced_data.get("audio_data", "")
            speaker_id = enhanced_data.get("speaker_id", "Unknown")
            
            # Transcribe using Gemini
            transcription_result = self.analyze_audio_from_base64(audio_data, "audio/wav")
            
            if transcription_result.get("success"):
                # Add speaker information to the result
                transcription_result["speaker_id"] = speaker_id
                transcription_result["timestamp"] = enhanced_data.get("timestamp")
                transcription_result["enhanced"] = True
                
                # Format the text with speaker identification
                original_text = transcription_result.get("text", "")
                if original_text:
                    transcription_result["text_with_speaker"] = f"[{speaker_id}]: {original_text}"
            
            return transcription_result
            
        except Exception as e:
            logger.error(f"Error in enhanced transcription: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def analyze_audio_from_base64(self, data: str, mime_type: str = "audio/wav") -> Dict[str, Any]:
        """Analyze audio using Gemini AI (enhanced version)"""
        try:
            if not self.gemini_ai:
                return {
                    "success": False,
                    "error": "Gemini AI not initialized"
                }
            
            # Prepare the audio data for Gemini
            audio_part = {
                "inline_data": {
                    "mime_type": mime_type,
                    "data": data
                }
            }
            
            # Enhanced prompt for better transcription
            prompt = """
            Please transcribe this audio accurately. Focus on:
            1. Clear, accurate transcription of all speech
            2. Proper punctuation and capitalization
            3. Note any background sounds or audio quality issues
            4. If multiple voices are present, try to distinguish them
            
            Provide only the transcribed text without additional commentary.
            """
            
            # Call Gemini API
            response = self.gemini_ai.generate_content([prompt, audio_part])
            
            if response and hasattr(response, 'text') and response.text:
                return {
                    "success": True,
                    "text": response.text.strip(),
                    "method": "gemini_enhanced"
                }
            else:
                return {
                    "success": False,
                    "error": "No transcription generated"
                }
                
        except Exception as e:
            logger.error(f"Error in enhanced Gemini audio analysis: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }