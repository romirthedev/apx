"""
Main Voice Manager for Apex AI Assistant.

This module orchestrates all voice functionality including recognition,
classification, processing, and synthesis for a seamless voice interaction experience.
"""

import asyncio
import logging
from typing import Optional, Callable, Dict, Any
from .voice_recognizer import VoiceRecognizer
from .voice_classifier import VoiceClassifier
from .voice_synthesizer import VoiceSynthesizer
from .voice_processor import VoiceProcessor
from core.overlay_interaction import OverlayInteractionManager

logger = logging.getLogger(__name__)

class VoiceManager:
    """Main manager for voice functionality - the Jarvis-like interface."""
    
    def __init__(self):
        self.is_active = False
        self.is_listening = False
        
        # Initialize components
        self.recognizer = VoiceRecognizer()
        self.classifier = VoiceClassifier()
        self.synthesizer = VoiceSynthesizer()
        self.processor = VoiceProcessor()
        self.overlay_interaction = OverlayInteractionManager()
        
        # Callbacks
        self.on_activation_change: Optional[Callable[[bool], None]] = None
        self.on_voice_input: Optional[Callable[[str], None]] = None
        self.on_response: Optional[Callable[[str], None]] = None
        
        logger.info("VoiceManager initialized with overlay interaction capabilities")
    
    async def activate(self) -> bool:
        """Activate voice mode - start listening and processing."""
        try:
            if self.is_active:
                logger.warning("Voice mode already active")
                return True
            
            # Initialize all components
            await self.recognizer.initialize()
            await self.synthesizer.initialize()
            
            self.is_active = True
            self.is_listening = True
            
            # Start continuous listening
            asyncio.create_task(self._continuous_listening())
            
            # Notify activation
            if self.on_activation_change:
                self.on_activation_change(True)
            
            # Welcome message
            await self.synthesizer.speak("Voice mode activated. I'm listening and ready to help.")
            
            logger.info("Voice mode activated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to activate voice mode: {e}")
            self.is_active = False
            return False
    
    async def deactivate(self):
        """Deactivate voice mode - stop listening and processing."""
        try:
            if not self.is_active:
                return
            
            self.is_listening = False
            self.is_active = False
            
            # Stop components
            await self.recognizer.stop()
            await self.synthesizer.stop()
            
            # Notify deactivation
            if self.on_activation_change:
                self.on_activation_change(False)
            
            logger.info("Voice mode deactivated")
            
        except Exception as e:
            logger.error(f"Error deactivating voice mode: {e}")
    
    async def _continuous_listening(self):
        """Main listening loop - the heart of the voice interaction."""
        logger.info("Starting continuous listening loop")
        
        while self.is_listening and self.is_active:
            try:
                # Listen for voice input
                voice_text = await self.recognizer.listen()
                
                if voice_text and voice_text.strip():
                    logger.info(f"Voice input received: {voice_text}")
                    
                    # Notify about voice input
                    if self.on_voice_input:
                        self.on_voice_input(voice_text)
                    
                    # Process the voice command
                    await self._process_voice_command(voice_text)
                
                # Small delay to prevent overwhelming the system
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in continuous listening: {e}")
                await asyncio.sleep(1)  # Wait before retrying
    
    async def _process_voice_command(self, voice_text: str):
        """Process a voice command through classification and execution."""
        try:
            # If we have a voice command callback (from start_listening), use it
            if hasattr(self, 'voice_command_callback') and self.voice_command_callback:
                # Classify the command first
                classification = await self.classifier.classify(voice_text)
                command_type = classification['type']
                
                logger.info(f"Command classified as: {command_type} (confidence: {classification['confidence']})")
                
                # Call the callback with the voice text and command type (await it since it's async)
                await self.voice_command_callback(voice_text, command_type)
                return
            
            # Default processing (when no callback is set)
            # Classify the command
            classification = await self.classifier.classify(voice_text)
            
            logger.info(f"Command classified as: {classification['type']} (confidence: {classification['confidence']})")
            
            # Process based on classification
            response = await self.processor.process(voice_text, classification)
            
            if response:
                # Notify about response
                if self.on_response:
                    self.on_response(response)
                
                # Speak the response
                await self.synthesizer.speak(response)
            
        except Exception as e:
            logger.error(f"Error processing voice command: {e}")
            await self.synthesizer.speak("I'm sorry, I encountered an error processing your request.")
    
    async def manual_input(self, text: str) -> str:
        """Process manual text input (for testing or fallback)."""
        try:
            classification = await self.classifier.classify(text)
            response = await self.processor.process(text, classification)
            return response or "I couldn't process that request."
        except Exception as e:
            logger.error(f"Error in manual input processing: {e}")
            return "Sorry, I encountered an error."
    
    def set_callbacks(self, 
                     on_activation_change: Optional[Callable[[bool], None]] = None,
                     on_voice_input: Optional[Callable[[str], None]] = None,
                     on_response: Optional[Callable[[str], None]] = None):
        """Set callback functions for various events."""
        if on_activation_change:
            self.on_activation_change = on_activation_change
        if on_voice_input:
            self.on_voice_input = on_voice_input
        if on_response:
            self.on_response = on_response
    
    @property
    def status(self) -> Dict[str, Any]:
        """Get current status of the voice manager."""
        return {
            'is_active': self.is_active,
            'is_listening': self.is_listening,
            'recognizer_ready': self.recognizer.is_ready if hasattr(self.recognizer, 'is_ready') else False,
            'synthesizer_ready': self.synthesizer.is_ready if hasattr(self.synthesizer, 'is_ready') else False
        }
    
    async def start_natural_conversation(self, callback: Callable[[str, str], None]):
        """Start natural conversation mode with pause detection (like Siri)."""
        try:
            # Set the callback for voice commands
            self.voice_command_callback = callback
            
            # Store the current event loop for thread-safe async operations
            self.main_loop = asyncio.get_running_loop()
            
            # Initialize recognizer if not already done
            if not self.recognizer.is_ready:
                await self.recognizer.initialize()
            
            # Initialize synthesizer if not already done
            if not self.synthesizer.is_ready:
                await self.synthesizer.initialize()
            
            # Set up recognition callback for natural conversation
            def on_natural_speech_recognized(text):
                if text and text.strip():
                    try:
                        # Check if the event loop is still running
                        if self.main_loop.is_closed():
                            logger.warning("Event loop is closed, cannot process voice command")
                            return
                        
                        # Schedule the async task on the main event loop from the background thread
                        future = asyncio.run_coroutine_threadsafe(
                            self._handle_natural_speech(text), 
                            self.main_loop
                        )
                        # Don't wait for the result to avoid blocking
                        
                    except Exception as e:
                        logger.error(f"Error scheduling natural voice command processing: {e}")
            
            # Start natural listening with pause detection
            self.recognizer.start_natural_listening(on_natural_speech_recognized)
            self.is_listening = True
            self.is_active = True
            
            logger.info("Natural conversation mode started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start natural conversation mode: {str(e)}")
            return False
    
    async def _handle_natural_speech(self, text: str):
        """Handle speech recognized in natural conversation mode."""
        try:
            logger.info(f"Natural speech recognized: {text}")
            
            # Notify about voice input
            if self.on_voice_input:
                self.on_voice_input(text)
            
            # Process the voice command with natural conversation handling
            await self._process_voice_command(text)
            
        except Exception as e:
            logger.error(f"Error handling natural speech: {e}")
    
    async def start_listening(self, callback: Callable[[str, str], None]):
        """Start listening with a callback for voice commands."""
        try:
            # Set the callback for voice commands
            self.voice_command_callback = callback
            
            # Store the current event loop for thread-safe async operations
            self.main_loop = asyncio.get_running_loop()
            
            # If voice system is already active (from activate), just update the callback
            if self.is_listening and self.is_active:
                logger.info("Voice listening already active, callback updated")
                return True
            
            # If not active, we need to start the voice system
            # Initialize recognizer if not already done
            if not self.recognizer.is_ready:
                await self.recognizer.initialize()
            
            # Start the listening state
            self.is_listening = True
            self.is_active = True
            
            # Start the continuous listening loop if not already running
            asyncio.create_task(self._continuous_listening())
            
            logger.info("Voice listening started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start voice listening: {str(e)}")
            return False
    
    async def _handle_speech_recognition(self, text: str):
        """Handle speech recognition with proper async/await."""
        try:
            # Classify the command
            command_type = await self.classifier.classify(text)
            logger.info(f"Voice command recognized: '{text}' -> {command_type}")
            
            # Call the provided callback
            if self.voice_command_callback:
                await self.voice_command_callback(text, command_type)
        except Exception as e:
            logger.error(f"Error handling speech recognition: {e}")
    
    def stop_listening(self):
        """Stop voice listening."""
        try:
            if hasattr(self, 'recognizer') and self.recognizer:
                self.recognizer.stop_listening()
            
            self.is_listening = False
            self.is_active = False
            self.voice_command_callback = None
            
            logger.info("Voice listening stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop voice listening: {str(e)}")
            return False
    
    async def speak_response(self, text: str):
        """Speak a response using text-to-speech."""
        try:
            logger.info(f"speak_response called with text: {text[:50]}...")
            if hasattr(self, 'synthesizer') and self.synthesizer:
                logger.info("Synthesizer available, calling speak method")
                result = await self.synthesizer.speak(text)
                logger.info(f"Synthesizer speak result: {result}")
            else:
                logger.warning("Synthesizer not available for speech output")
                
        except Exception as e:
            logger.error(f"Failed to speak response: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    async def perform_ai_action(self, action_type: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Perform an AI action through the overlay interface."""
        try:
            if parameters is None:
                parameters = {}
            
            logger.info(f"Performing AI action: {action_type} with parameters: {parameters}")
            
            # Map action types to overlay interaction methods
            if action_type == "execute_command":
                command = parameters.get("command", "")
                context = parameters.get("context", [])
                return await self.overlay_interaction.execute_command(command, context)
            
            elif action_type == "take_screenshot":
                return await self.overlay_interaction.take_screenshot()
            
            elif action_type == "web_search":
                query = parameters.get("query", "")
                return await self.overlay_interaction.perform_web_search(query)
            
            elif action_type == "create_file":
                filename = parameters.get("filename", "")
                content = parameters.get("content", "")
                return await self.overlay_interaction.create_file(filename, content)
            
            elif action_type == "read_file":
                filename = parameters.get("filename", "")
                return await self.overlay_interaction.read_file(filename)
            
            elif action_type == "list_files":
                directory = parameters.get("directory", ".")
                return await self.overlay_interaction.list_files(directory)
            
            elif action_type == "open_application":
                app_name = parameters.get("app_name", "")
                return await self.overlay_interaction.open_application(app_name)
            
            elif action_type == "get_system_info":
                return await self.overlay_interaction.get_system_info()
            
            elif action_type == "start_audio_capture":
                return await self.overlay_interaction.start_audio_capture()
            
            elif action_type == "stop_audio_capture":
                return await self.overlay_interaction.stop_audio_capture()
            
            elif action_type == "clear_context":
                return await self.overlay_interaction.clear_context()
            
            elif action_type == "refresh_context":
                return await self.overlay_interaction.refresh_context()
            
            elif action_type == "get_capabilities":
                return await self.overlay_interaction.get_system_capabilities()
            
            else:
                return {
                    'success': False,
                    'error': f"Unknown action type: {action_type}"
                }
                
        except Exception as e:
            logger.error(f"Error performing AI action '{action_type}': {str(e)}")
            return {
                'success': False,
                'error': f"Action failed: {str(e)}"
            }