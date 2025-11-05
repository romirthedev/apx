"""
Voice Synthesis module for text-to-speech conversion.

Converts AI responses to natural-sounding speech using system TTS or external services.
"""

import asyncio
import logging
import subprocess
import threading
import queue
from typing import Optional, List
import os
import tempfile

logger = logging.getLogger(__name__)

class VoiceSynthesizer:
    """Handles text-to-speech conversion with natural voice output."""
    
    def __init__(self):
        self.is_ready = False
        self.is_speaking = False
        self.speech_queue = queue.Queue()
        self.speech_thread = None
        self.current_process = None
        self.safe_mode = True  # Use minimal, reliable TTS by default
        
        # Enhanced voice settings for more human-like speech
        self.voice_name = "Samantha"  # Default to a more natural voice
        self.speech_rate = 175  # Optimal rate for natural conversation
        self.volume = 0.85  # Balanced volume for clarity
        self.pitch = 52  # Slightly higher pitch for warmth
        self.intonation = 55  # Enhanced intonation for expressiveness
        
        # Advanced speech parameters for human-like qualities
        self.use_natural_pauses = True
        self.add_emphasis = True
        self.vary_speech_rate = True
        self.emotional_context = True
        
        # Voice quality presets with human-like characteristics
        self.voice_presets = {
            'natural': {
                'voice': 'Samantha',
                'rate': 175,
                'volume': 0.85,
                'pitch': 52,
                'intonation': 55,
                'natural_pauses': True,
                'emphasis': True
            },
            'professional': {
                'voice': 'Victoria',
                'rate': 165,
                'volume': 0.8,
                'pitch': 48,
                'intonation': 45,
                'natural_pauses': True,
                'emphasis': False
            },
            'friendly': {
                'voice': 'Samantha',
                'rate': 185,
                'volume': 0.9,
                'pitch': 55,
                'intonation': 60,
                'natural_pauses': True,
                'emphasis': True
            },
            'friendly': {
                'voice': 'Allison',
                'rate': 190,
                'volume': 0.9,
                'pitch': 55,
                'intonation': 60
            },
            'clear': {
                'voice': 'Alex',
                'rate': 160,
                'volume': 1.0,
                'pitch': 50,
                'intonation': 45
            }
        }
        
        logger.info("VoiceSynthesizer initialized with enhanced voice quality settings")
    
    async def initialize(self) -> bool:
        """Initialize the voice synthesizer."""
        try:
            # Check if system TTS is available (macOS 'say' command)
            result = subprocess.run(['which', 'say'], capture_output=True, text=True)
            
            if result.returncode == 0:
                # Test the voice
                test_result = subprocess.run(
                    ['say', '-v', self.voice_name, '-r', str(self.speech_rate), 'Voice system ready'],
                    capture_output=True,
                    timeout=5
                )
                
                if test_result.returncode == 0:
                    self.is_ready = True
                    logger.info("Voice synthesizer initialized with system TTS")
                    return True
                else:
                    logger.warning("System TTS test failed, trying default voice")
                    # Try with default voice
                    test_result = subprocess.run(['say', 'Voice system ready'], capture_output=True, timeout=5)
                    if test_result.returncode == 0:
                        self.voice_name = None  # Use default
                        self.is_ready = True
                        logger.info("Voice synthesizer initialized with default system voice")
                        return True
            
            logger.error("System TTS not available")
            return False
            
        except subprocess.TimeoutExpired:
            logger.error("TTS initialization timed out")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize voice synthesizer: {e}")
            return False
    
    async def speak(self, text: str, priority: bool = False) -> bool:
        """
        Convert text to speech and play it.
        
        Args:
            text: Text to speak
            priority: If True, interrupt current speech
            
        Returns:
            True if speech was queued/started successfully
        """
        if not self.is_ready:
            logger.warning("Voice synthesizer not ready")
            return False
        
        if not text or not text.strip():
            return False
        
        text = text.strip()
        logger.info(f"Speaking: {text[:50]}{'...' if len(text) > 50 else ''}")
        
        try:
            if priority and self.is_speaking:
                await self.stop_current_speech()
            
            # Add to speech queue
            self.speech_queue.put(text)
            
            # Start speech processing if not already running
            if not self.is_speaking:
                await self._start_speech_processing()
            
            return True
            
        except Exception as e:
            logger.error(f"Error in speak method: {e}")
            return False
    
    async def _start_speech_processing(self):
        """Start processing the speech queue."""
        if self.is_speaking:
            return
        
        self.is_speaking = True
        
        def process_speech_queue():
            """Process speech queue in background thread."""
            while self.is_speaking:
                try:
                    # Get next text to speak (with timeout)
                    text = self.speech_queue.get(timeout=1)
                    
                    if text:
                        self._synthesize_and_play(text)
                    
                    self.speech_queue.task_done()
                    
                except queue.Empty:
                    # No more items in queue
                    break
                except Exception as e:
                    logger.error(f"Error processing speech queue: {e}")
            
            self.is_speaking = False
        
        # Start speech processing thread
        self.speech_thread = threading.Thread(target=process_speech_queue, daemon=True)
        self.speech_thread.start()
    
    def _synthesize_and_play(self, text: str):
        """Synthesize and play speech using system TTS.
        In safe_mode, use a plain command without amplitude or SSML-like tags for reliability.
        """
        try:
            if self.safe_mode:
                # Plain, reliable TTS path (no amplitude or tags)
                fallback_cmd = ['say']
                if self.voice_name:
                    fallback_cmd.extend(['-v', self.voice_name])
                fallback_cmd.extend(['-r', str(self.speech_rate)])
                fallback_cmd.append(text)
                logger.debug(f"Safe TTS command: {' '.join(fallback_cmd[:4])}... [text length: {len(text)}]")
                result = subprocess.run(fallback_cmd, capture_output=True)
                if result.returncode != 0:
                    fb_err = (result.stderr.decode() or '').strip()
                    logger.error(f"Safe TTS error: {fb_err}")
                else:
                    logger.debug("Safe TTS synthesis completed successfully")
            else:
                # Prepare the enhanced command with quality settings
                cmd = ['say']
                # Voice selection
                if self.voice_name:
                    cmd.extend(['-v', self.voice_name])
                # Dynamic speech rate variation for more natural flow
                current_rate = self.speech_rate
                if self.vary_speech_rate and len(text) > 50:
                    if '?' in text:
                        current_rate = int(self.speech_rate * 0.95)
                    elif '!' in text:
                        current_rate = int(self.speech_rate * 1.05)
                    elif text.count('.') > 2:
                        current_rate = int(self.speech_rate * 0.98)
                cmd.extend(['-r', str(current_rate)])
                # Add volume control (macOS say command uses -a for amplitude)
                volume_percent = int(self.volume * 100)
                cmd.extend(['-a', str(volume_percent)])
                # Preprocess text for better speech quality with human-like enhancements
                enhanced_text = self._enhance_text_for_speech(text)
                if self.emotional_context:
                    enhanced_text = self._add_emotional_context(enhanced_text)
                cmd.append(enhanced_text)
                logger.debug(f"Enhanced TTS command: {' '.join(cmd[:4])}... [text length: {len(enhanced_text)}]")
                # Execute TTS with enhanced settings (stoppable)
                self.current_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                stdout, stderr = self.current_process.communicate()
                if self.current_process.returncode != 0:
                    try:
                        err_msg = (stderr.decode() or '').strip()
                    except Exception:
                        err_msg = ''
                    logger.error(f"TTS error (enhanced): {err_msg}")
                    # Fallback to safe path
                    try:
                        fb_cmd = ['say']
                        if self.voice_name:
                            fb_cmd.extend(['-v', self.voice_name])
                        fb_cmd.extend(['-r', str(self.speech_rate)])
                        fb_cmd.append(text)
                        logger.debug(f"Fallback TTS command: {' '.join(fb_cmd[:4])}... [text length: {len(text)}]")
                        result = subprocess.run(fb_cmd, capture_output=True)
                        if result.returncode != 0:
                            fb_err = (result.stderr.decode() or '').strip()
                            logger.error(f"Fallback TTS error: {fb_err}")
                        else:
                            logger.info("Fallback TTS synthesis succeeded")
                    except Exception as fe:
                        logger.error(f"Fallback TTS exception: {fe}")
                else:
                    logger.debug("Enhanced TTS synthesis completed successfully")
                self.current_process = None
            
        except Exception as e:
            logger.error(f"Error in enhanced TTS synthesis: {e}")
            self.current_process = None
    
    def _add_emotional_context(self, text: str) -> str:
        """Add subtle emotional context to speech for more human-like delivery."""
        # Detect emotional cues and adjust accordingly
        if any(word in text.lower() for word in ['sorry', 'apologize', 'unfortunately']):
            # Add slight pause before apologies for sincerity
            text = text.replace('sorry', '[[slnc 200]] sorry')
            text = text.replace('apologize', '[[slnc 200]] apologize')
        
        if any(word in text.lower() for word in ['great', 'excellent', 'wonderful', 'amazing']):
            # Add slight emphasis to positive words
            text = text.replace('great', '[[emph +]] great [[emph -]]')
            text = text.replace('excellent', '[[emph +]] excellent [[emph -]]')
            text = text.replace('wonderful', '[[emph +]] wonderful [[emph -]]')
        
        if any(word in text.lower() for word in ['help', 'assist', 'support']):
            # Add warmth to helpful responses
            text = text.replace('help', '[[emph +]] help [[emph -]]')
            text = text.replace('assist', '[[emph +]] assist [[emph -]]')
        
        return text
    
    def _enhance_text_for_speech(self, text: str) -> str:
        """Enhance text for more natural, human-like speech synthesis."""
        enhanced = text
        
        if self.use_natural_pauses:
            # Add natural pauses with varied lengths for better flow
            enhanced = enhanced.replace('. ', '. [[slnc 400]] ')  # Sentence pause
            enhanced = enhanced.replace('! ', '! [[slnc 450]] ')  # Exclamation pause
            enhanced = enhanced.replace('? ', '? [[slnc 500]] ')  # Question pause (longer for reflection)
            enhanced = enhanced.replace(', ', ', [[slnc 200]] ')  # Comma pause
            enhanced = enhanced.replace('; ', '; [[slnc 300]] ')  # Semicolon pause
            enhanced = enhanced.replace(': ', ': [[slnc 250]] ')  # Colon pause
            enhanced = enhanced.replace(' - ', ' [[slnc 200]] - [[slnc 200]] ')  # Dash pauses
            
            # Add breathing pauses for longer sentences
            if len(enhanced) > 100:
                # Insert natural breathing pauses every ~80-120 characters
                words = enhanced.split()
                result = []
                char_count = 0
                for word in words:
                    result.append(word)
                    char_count += len(word) + 1
                    if char_count > 100 and word.endswith((',', ';')):
                        result.append('[[slnc 300]]')
                        char_count = 0
                enhanced = ' '.join(result)
        
        if self.add_emphasis:
            # Add emphasis to important words and phrases
            enhanced = enhanced.replace('very ', '[[emph +]] very [[emph -]] ')
            enhanced = enhanced.replace('really ', '[[emph +]] really [[emph -]] ')
            enhanced = enhanced.replace('absolutely ', '[[emph +]] absolutely [[emph -]] ')
            enhanced = enhanced.replace('definitely ', '[[emph +]] definitely [[emph -]] ')
            enhanced = enhanced.replace('important', '[[emph +]] important [[emph -]]')
            enhanced = enhanced.replace('amazing', '[[emph +]] amazing [[emph -]]')
            enhanced = enhanced.replace('excellent', '[[emph +]] excellent [[emph -]]')
            enhanced = enhanced.replace('perfect', '[[emph +]] perfect [[emph -]]')
            
            # Emphasize questions and exclamations
            enhanced = enhanced.replace('What ', '[[emph +]] What [[emph -]] ')
            enhanced = enhanced.replace('How ', '[[emph +]] How [[emph -]] ')
            enhanced = enhanced.replace('Why ', '[[emph +]] Why [[emph -]] ')
            enhanced = enhanced.replace('Wow', '[[emph +]] Wow [[emph -]]')
            enhanced = enhanced.replace('Great', '[[emph +]] Great [[emph -]]')
        
        # Handle technical terms and abbreviations for better pronunciation
        tech_replacements = {
            'AI': 'A I',
            'API': 'A P I',
            'URL': 'U R L',
            'HTTP': 'H T T P',
            'HTTPS': 'H T T P S',
            'JSON': 'J S O N',
            'XML': 'X M L',
            'HTML': 'H T M L',
            'CSS': 'C S S',
            'SQL': 'S Q L',
            'PDF': 'P D F',
            'UI': 'U I',
            'UX': 'U X',
            'iOS': 'i O S',
            'macOS': 'mac O S',
            'WiFi': 'Wi Fi',
            'USB': 'U S B',
            'GPS': 'G P S',
            'FAQ': 'F A Q',
            'CEO': 'C E O',
            'CTO': 'C T O'
        }
        
        for abbrev, pronunciation in tech_replacements.items():
            enhanced = enhanced.replace(abbrev, pronunciation)
        
        # Handle numbers for more natural pronunciation
        enhanced = enhanced.replace('1st', 'first')
        enhanced = enhanced.replace('2nd', 'second')
        enhanced = enhanced.replace('3rd', 'third')
        enhanced = enhanced.replace('4th', 'fourth')
        enhanced = enhanced.replace('5th', 'fifth')
        
        # Add natural conversational fillers occasionally for very long responses
        if len(enhanced) > 200 and self.emotional_context:
            # Insert occasional natural conversational elements
            if 'let me' in enhanced.lower():
                enhanced = enhanced.replace('let me', 'let me [[slnc 150]]')
            if 'so,' in enhanced.lower():
                enhanced = enhanced.replace('so,', 'so, [[slnc 200]]')
            if 'well,' in enhanced.lower():
                enhanced = enhanced.replace('well,', 'well, [[slnc 200]]')
        
        return enhanced
    
    async def stop_current_speech(self):
        """Stop current speech output."""
        try:
            if self.current_process:
                self.current_process.terminate()
                self.current_process.wait(timeout=2)
                self.current_process = None
            
            # Clear the queue
            while not self.speech_queue.empty():
                try:
                    self.speech_queue.get_nowait()
                    self.speech_queue.task_done()
                except queue.Empty:
                    break
            
            logger.info("Speech stopped")
            
        except Exception as e:
            logger.error(f"Error stopping speech: {e}")
    
    async def stop(self):
        """Stop the voice synthesizer."""
        self.is_speaking = False
        await self.stop_current_speech()
        
        if self.speech_thread and self.speech_thread.is_alive():
            self.speech_thread.join(timeout=2)
        
        logger.info("Voice synthesizer stopped")

    def set_safe_mode(self, enabled: bool):
        """Enable or disable safe TTS mode."""
        self.safe_mode = bool(enabled)
        logger.info(f"Safe TTS mode set to: {self.safe_mode}")
    
    def set_voice(self, voice_name: str):
        """Set the voice to use for TTS."""
        self.voice_name = voice_name
        logger.info(f"Voice set to: {voice_name}")
    
    def set_speech_rate(self, rate: int):
        """Set speech rate in words per minute."""
        self.speech_rate = max(50, min(500, rate))  # Clamp between 50-500 WPM
        logger.info(f"Speech rate set to: {self.speech_rate} WPM")
    
    def set_volume(self, volume: float):
        """Set volume level (0.0 to 1.0)."""
        self.volume = max(0.0, min(1.0, volume))
        logger.info(f"Volume set to: {self.volume}")
    
    def apply_voice_preset(self, preset_name: str) -> bool:
        """Apply a voice quality preset with human-like characteristics."""
        if preset_name not in self.voice_presets:
            logger.error(f"Unknown voice preset: {preset_name}")
            return False
        
        preset = self.voice_presets[preset_name]
        self.voice_name = preset['voice']
        self.speech_rate = preset['rate']
        self.volume = preset['volume']
        self.pitch = preset['pitch']
        self.intonation = preset['intonation']
        
        # Apply human-like characteristics if present in preset
        if 'natural_pauses' in preset:
            self.use_natural_pauses = preset['natural_pauses']
        if 'emphasis' in preset:
            self.add_emphasis = preset['emphasis']
        
        logger.info(f"Applied enhanced voice preset: {preset_name}")
        return True
    
    def get_voice_presets(self) -> dict:
        """Get available voice presets."""
        return self.voice_presets.copy()
    
    def get_available_voices(self) -> List[str]:
        """Get list of available system voices."""
        try:
            result = subprocess.run(['say', '-v', '?'], capture_output=True, text=True)
            
            if result.returncode == 0:
                voices = []
                for line in result.stdout.split('\n'):
                    if line.strip():
                        # Extract voice name (first word before the space)
                        voice_name = line.split()[0]
                        if voice_name:
                            voices.append(voice_name)
                return voices
            
        except Exception as e:
            logger.error(f"Error getting available voices: {e}")
        
        return ['Alex', 'Samantha', 'Victoria']  # Default fallback voices
    
    async def test_voice(self, voice_name: str = None) -> bool:
        """Test a specific voice."""
        test_voice = voice_name or self.voice_name
        
        try:
            cmd = ['say', '-v', test_voice, 'This is a voice test']
            result = subprocess.run(cmd, capture_output=True, timeout=5)
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Error testing voice {test_voice}: {e}")
            return False
    
    @property
    def status(self) -> dict:
        """Get current status of the voice synthesizer."""
        return {
            'ready': self.is_ready,
            'speaking': self.is_speaking,
            'voice': self.voice_name,
            'speech_rate': self.speech_rate,
            'volume': self.volume,
            'pitch': self.pitch,
            'intonation': self.intonation,
            'queue_size': self.speech_queue.qsize(),
            'available_presets': list(self.voice_presets.keys())
        }