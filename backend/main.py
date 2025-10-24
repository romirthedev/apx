import asyncio
import json
import logging
import os
import re
import sys
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional

from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import threading
import requests
from bs4 import BeautifulSoup
import urllib.parse

# Import core modules
from core.command_processor import CommandProcessor
from core.action_logger import ActionLogger
from core.security_manager import SecurityManager
from core.gemini_ai import GeminiAI
from utils.config import Config


# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cluely.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)
logging.getLogger('core.command_executor').setLevel(logging.DEBUG)
logging.getLogger('plugins.file_manager').setLevel(logging.DEBUG)

class CluelyBackend:
    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app)
        
        # Initialize core components
        self.config = Config()
        self.security_manager = SecurityManager()
        self.action_logger = ActionLogger()
        self.command_processor = CommandProcessor(
            security_manager=self.security_manager,
            action_logger=self.action_logger
        )
        
        # Initialize Gemini AI (for first-pass intent classification and chat responses)
        self.gemini_ai = None
        try:
            gemini_api_key = self.config.get('apis.gemini.api_key')
            gemini_enabled = self.config.get('apis.gemini.enabled', True)
            if gemini_api_key and gemini_enabled:
                self.gemini_ai = GeminiAI(gemini_api_key)
                logger.info("Gemini AI initialized for front-door intent classification")
            else:
                logger.info("Gemini AI disabled or missing API key; skipping AI front-door classification")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini AI: {e}")
            self.gemini_ai = None
        
        # Disable Task Planner entirely (force all commands through CommandProcessor)
        self.task_planner = None
        logger.info("Task Planner disabled at startup: all commands handled by CommandProcessor")
        
        # Context storage for conversation continuity
        self.context_storage: Dict[str, List[Dict]] = {}
        
        # Persistent context that survives mode switches (only cleared on explicit refresh)
        self.persistent_context: List[Dict] = []
        
        # Storage for latest audio chunk and transcription from continuous capture
        self.latest_audio_chunk = None
        self.latest_transcription = None
        self.transcription_lock = threading.Lock()
        
        self._setup_routes()
        
    def _setup_routes(self):
        @self.app.route('/health', methods=['GET'])
        def health_check():
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0'
            })
        
        @self.app.route('/audio-test')
        def audio_test():
            return send_file('../src/audio-test.html')
        
        @self.app.route('/analyze_audio_base64', methods=['POST'])
        def analyze_audio_base64():
            """Analyze audio from base64 data using Gemini AI"""
            try:
                data = request.get_json() or {}
                audio_data = data.get('data', '')
                mime_type = data.get('mimeType', 'audio/webm')
                
                if not audio_data:
                    return jsonify({
                        'success': False,
                        'error': 'No audio data provided'
                    })
                
                # Import audio manager
                from plugins.audio_manager import AudioManager
                audio_manager = AudioManager()
                
                # Analyze audio using Gemini AI
                logger.info(f"Analyzing audio with Gemini AI (mime_type: {mime_type})")
                result = audio_manager.analyze_audio_from_base64(audio_data, mime_type)
                
                return jsonify(result)
                
            except Exception as e:
                logger.error(f"Error analyzing audio from base64: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        @self.app.route('/analyze_audio_file', methods=['POST'])
        def analyze_audio_file():
            """Analyze audio from file path using Gemini AI"""
            try:
                data = request.get_json() or {}
                file_path = data.get('path', '')
                
                if not file_path:
                    return jsonify({
                        'success': False,
                        'error': 'No file path provided'
                    })
                
                # Read audio file and convert to base64
                import os
                if not os.path.exists(file_path):
                    return jsonify({
                        'success': False,
                        'error': f'File not found: {file_path}'
                    })
                
                try:
                    with open(file_path, 'rb') as audio_file:
                        audio_data = base64.b64encode(audio_file.read()).decode('utf-8')
                    
                    # Determine MIME type based on file extension
                    file_ext = os.path.splitext(file_path)[1].lower()
                    mime_type_map = {
                        '.mp3': 'audio/mp3',
                        '.wav': 'audio/wav',
                        '.webm': 'audio/webm',
                        '.m4a': 'audio/mp4',
                        '.ogg': 'audio/ogg'
                    }
                    mime_type = mime_type_map.get(file_ext, 'audio/mp3')
                    
                    # Import audio manager
                    from plugins.audio_manager import AudioManager
                    audio_manager = AudioManager()
                    
                    # Analyze audio using Gemini AI
                    logger.info(f"Analyzing audio file: {file_path} (mime_type: {mime_type})")
                    result = audio_manager.analyze_audio_from_base64(audio_data, mime_type)
                    
                    return jsonify(result)
                    
                except Exception as file_error:
                    logger.error(f"Error reading audio file {file_path}: {str(file_error)}")
                    return jsonify({
                        'success': False,
                        'error': f'Error reading audio file: {str(file_error)}'
                    })
                
            except Exception as e:
                logger.error(f"Error analyzing audio file: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        @self.app.route('/transcribe_audio', methods=['POST'])
        def transcribe_audio():
            """Legacy endpoint for audio transcription - now uses Gemini AI"""
            try:
                data = request.get_json() or {}
                audio_data = data.get('audio_data', '')
                use_gemini = data.get('use_gemini', True)  # Default to True now
                capture_system_audio = data.get('capture_system_audio', False)
                
                # Import audio manager
                from plugins.audio_manager import AudioManager
                audio_manager = AudioManager()
                
                # If requested to capture system audio (for Zoom/Meet calls)
                if capture_system_audio and not audio_data:
                    logger.info("Retrieving latest transcription from continuous capture...")
                    # Return the latest transcription from continuous capture
                    with self.transcription_lock:
                        if self.latest_transcription:
                            transcription = self.latest_transcription.copy()
                            # Clear the transcription so we don't return the same one multiple times
                            self.latest_transcription = None
                            logger.info(f"Returning transcription: {transcription.get('text', '')[:50]}...")
                            return jsonify({
                                'success': transcription.get('success', False),
                                'text': transcription.get('text', ''),
                                'timestamp': transcription.get('timestamp', ''),
                                'error': transcription.get('error', '')
                            })
                        else:
                            logger.debug("No new transcription available")
                            return jsonify({
                                'success': True,
                                'text': '',
                                'message': 'No new transcription available'
                            })
                
                if not audio_data:
                    return jsonify({
                        'success': False,
                        'error': 'No audio data provided or system audio capture failed'
                    })
                
                # Transcribe audio using Gemini AI
                logger.info(f"Transcribing audio with Gemini AI")
                result = audio_manager.transcribe_audio(audio_data, use_gemini=use_gemini)
                
                # If transcription failed, use sample data
                if not result.get('success', False):
                    logger.warning(f"Audio transcription failed: {result.get('error')}. Using sample data.")
                    result = audio_manager.get_sample_transcription()
                
                return jsonify(result)
                
            except Exception as e:
                logger.error(f"Error processing audio transcription: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        @self.app.route('/analyze_meeting', methods=['POST'])
        def analyze_meeting():
            try:
                data = request.get_json() or {}
                recent_transcript = data.get('recent_transcript', '')
                conversation_history = data.get('conversation_history', [])
                conversation_summary = data.get('conversation_summary', '')
                trigger_reason = data.get('trigger_reason', 'unknown')
                timestamp = data.get('timestamp', datetime.now().isoformat())
                
                # Handle speaker change context
                previous_speaker = data.get('previousSpeaker', '')
                new_speaker = data.get('newSpeaker', '')
                speaker_content = data.get('speakerContent', '')
                
                if not recent_transcript and not conversation_history:
                    return jsonify({
                        'success': False,
                        'error': 'No transcript or conversation history provided'
                    })
                
                logger.info(f"Analyzing meeting content (trigger: {trigger_reason})")
                
                # Prepare context for AI analysis
                # Build the conversation summary section separately to avoid f-string backslash issues
                summary_section = ''
                if conversation_summary:
                    summary_section = f'Previous conversation summary:\n{conversation_summary}\n\n'
                
                # Build speaker change context if applicable
                speaker_change_section = ''
                if trigger_reason == 'speaker_change' and previous_speaker and new_speaker:
                    speaker_change_section = f'\nSpeaker Change Context:\n- Previous speaker: {previous_speaker}\n- New speaker: {new_speaker}\n- Previous speaker\'s content: {speaker_content}\n\n'
                
                analysis_prompt = f"""
Provide direct answers only. After your answer, add 2-3 sentences of brief reasoning or helpful context. For mathematical expressions, use proper LaTeX formatting with $ for inline math and $$ for display math (e.g., $x^2$, $$\\frac{{d}}{{dx}}(x^n) = nx^{{n-1}}$$). Use clear formatting with appropriate markdown for structure, but avoid excessive styling.

You are an AI assistant analyzing a live meeting or conversation. Based on the recent transcript, conversation history, and previous conversation summary, provide helpful insights, answers to questions, or relevant information.

Trigger reason: {trigger_reason}
Timestamp: {timestamp}

Recent transcript:
{recent_transcript}

Conversation history (recent):
{json.dumps(conversation_history, indent=2)}

{summary_section}{speaker_change_section}Please provide a concise, helpful response that:
1. Answers any questions detected in the recent transcript
2. Provides relevant context or insights from the full conversation context
3. If this is a speaker change, acknowledge the transition and provide relevant context
4. Suggests next steps if appropriate
5. Keeps the response under 200 words for real-time display

Response:"""
                
                # Use Gemini AI for analysis with persistent context
                if self.gemini_ai:
                    ai_response = self.gemini_ai.generate_response(
                        user_input=analysis_prompt,
                        context=self.persistent_context,  # Use persistent context for cross-mode continuity
                        available_actions=[],
                        is_chat=True
                    )
                    
                    if ai_response.get('success', False):
                        return jsonify({
                            'success': True,
                            'response': ai_response.get('response', ''),
                            'trigger': trigger_reason,
                            'timestamp': timestamp
                        })
                    else:
                        logger.error(f"AI analysis failed: {ai_response.get('error')}")
                        return jsonify({
                            'success': False,
                            'error': 'AI analysis failed'
                        })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'AI analysis not available - Gemini AI not initialized'
                    })
                    
            except Exception as e:
                logger.error(f"Error analyzing meeting: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        @self.app.route('/start_continuous_capture', methods=['POST'])
        def start_continuous_capture():
            try:
                data = request.get_json() or {}
                chunk_duration = data.get('chunk_duration', 3)
                
                # Import audio manager
                from plugins.audio_manager import AudioManager
                audio_manager = AudioManager()
                
                # Define callback function to handle audio chunks
                def audio_chunk_callback(audio_data):
                    # Store the latest audio chunk for transcription requests
                    self.latest_audio_chunk = audio_data
                    logger.debug(f"Received audio chunk of length: {len(audio_data)}")
                    
                    # Automatically transcribe the audio chunk
                    try:
                        transcription_result = audio_manager.transcribe_audio(audio_data, use_gemini=True)
                        if transcription_result.get('success') and transcription_result.get('text'):
                            with self.transcription_lock:
                                self.latest_transcription = {
                                    'text': transcription_result['text'],
                                    'timestamp': datetime.now().isoformat(),
                                    'success': True
                                }
                            logger.info(f"Transcribed: {transcription_result['text'][:50]}...")
                        else:
                            logger.debug("No speech detected in audio chunk")
                    except Exception as transcription_error:
                        logger.error(f"Error transcribing audio chunk: {str(transcription_error)}")
                        with self.transcription_lock:
                            self.latest_transcription = {
                                'text': '',
                                'timestamp': datetime.now().isoformat(),
                                'success': False,
                                'error': str(transcription_error)
                            }
                
                result = audio_manager.start_continuous_capture(
                    callback=audio_chunk_callback,
                    chunk_duration=chunk_duration
                )
                
                return jsonify(result)
                
            except Exception as e:
                logger.error(f"Error starting continuous capture: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        @self.app.route('/stop_continuous_capture', methods=['POST'])
        def stop_continuous_capture():
            try:
                # Import audio manager
                from plugins.audio_manager import AudioManager
                audio_manager = AudioManager()
                
                result = audio_manager.stop_continuous_capture()
                return jsonify(result)
                
            except Exception as e:
                logger.error(f"Error stopping continuous capture: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        @self.app.route('/audio_setup_info', methods=['GET'])
        def get_audio_setup_info():
            try:
                # Import audio manager
                from plugins.audio_manager import AudioManager
                audio_manager = AudioManager()
                
                result = audio_manager.get_system_audio_setup_info()
                return jsonify(result)
                
            except Exception as e:
                logger.error(f"Error getting audio setup info: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        @self.app.route('/capture_screenshot', methods=['POST'])
        def capture_screenshot():
            """Capture a screenshot and analyze it with AI to answer questions on screen"""
            try:
                # Import screenshot manager
                from plugins.screenshot_manager import ScreenshotManager
                screenshot_manager = ScreenshotManager()
                
                # Capture screenshot and analyze with AI
                logger.info("Capturing screenshot and analyzing with AI")
                result = screenshot_manager.capture_screenshot_and_analyze()
                
                return jsonify(result)
                
            except Exception as e:
                logger.error(f"Error capturing screenshot: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        @self.app.route('/command', methods=['POST'])
        def process_command():
            try:
                data = request.get_json() or {}
                command = data.get('command', '').strip()
                incoming_context = data.get('context', [])
                action_mode = data.get('action_mode', False) or data.get('is_action', False)
                
                # Ensure incoming context is always a list
                if not isinstance(incoming_context, list):
                    incoming_context = []
                
                # Use persistent context that survives mode switches
                # Only merge new items from incoming context that aren't already in persistent context
                for item in incoming_context:
                    if item not in self.persistent_context:
                        self.persistent_context.append(item)
                
                # Keep only the last 10 items in persistent context
                if len(self.persistent_context) > 10:
                    self.persistent_context = self.persistent_context[-10:]
                
                # Use persistent context for processing
                context = self.persistent_context.copy()
                
                if not command:
                    return jsonify({
                        'success': False,
                        'error': 'No command provided'
                    })
                
                # Log the incoming command
                logger.info(f"Processing command: {command}" + (" [ACTION MODE]" if action_mode else ""))
                
                # Check for document/spreadsheet creation in action mode FIRST
                if action_mode and self._is_document_creation_request(command):
                    logger.info(f"Document creation request detected in action mode for command: {command}")
                    result = self._handle_document_creation(command)
                    used_ai_chat = False
                    ai_metadata: Dict[str, Any] = {}
                    logger.info(f"Document creation result: {result}")
                else:
                    # Front-door: pass raw input to AI for intent classification
                    ai_first = True and not action_mode  # Skip AI classification if action_mode is true
                    used_ai_chat = False
                    ai_metadata: Dict[str, Any] = {}
                    
                    # Front-door: pass raw input to AI for intent classification
                    # No special handling for GitHub repository searches - let the command processor handle it
                    # If action_mode is true, bypass AI classification and go directly to CommandProcessor
                    
                    if ai_first and self.gemini_ai is not None:
                        try:
                            classify = self.gemini_ai.classify_intent(command)
                            ai_metadata = {
                                'method': 'gemini_ai',
                                'classifier': classify
                            }
                            # Treat as chat if AI says chat and is reasonably confident and no action required
                            if classify.get('success') and classify.get('type') == 'chat' and not classify.get('requires_action', False) and classify.get('confidence', 0.0) >= 0.6:
                                ai_resp = self.gemini_ai.generate_response(
                                    user_input=command,
                                    context=context,
                                    available_actions=self.command_processor.get_capabilities(),
                                    is_chat=True
                                )
                                used_ai_chat = True
                                result = {
                                    'success': ai_resp.get('success', True),
                                    'result': ai_resp.get('response', ''),
                                    'response_type': 'chat',
                                    'metadata': {
                                        'method': 'gemini_ai_chat',
                                        'ai_frontdoor': ai_metadata
                                    }
                                }
                            else:
                                logger.info("Classifier indicates command or low confidence; delegating to CommandProcessor")
                        except Exception as e:
                            logger.warning(f"AI front-door classification failed: {e}")
                
                # If we didn't already answer via AI chat or handle document creation, route to CommandProcessor
                if not used_ai_chat and 'result' not in locals():
                    logger.info("Task Planner disabled: routing directly to CommandProcessor")
                    result = self.command_processor.process(command, context)
                    
                    # Set response_type to action for command responses
                    result['response_type'] = 'action'
                    # Merge AI metadata if present
                    if ai_metadata:
                        meta = result.get('metadata', {})
                        # Only annotate; do not overwrite CommandProcessor method
                        meta.setdefault('ai_frontdoor', ai_metadata)
                        result['metadata'] = meta
                elif 'result' in locals() and not used_ai_chat:
                    # Document creation was handled, set response_type to action
                    result['response_type'] = 'action'
                
                # Log the result for debugging
                logger.info(f"Command result: success={result.get('success')}, method={result.get('metadata', {}).get('method')}")
                
                # Update persistent context
                new_context_item = {
                    'timestamp': datetime.now().isoformat(),
                    'command': command,
                    'result': result.get('result', ''),
                    'success': result.get('success', False)
                }
                
                # Add to persistent context and keep only last 10 items
                self.persistent_context.append(new_context_item)
                if len(self.persistent_context) > 10:
                    self.persistent_context = self.persistent_context[-10:]
                
                # Update local context for response
                context = self.persistent_context.copy()
                
                # Log the action
                self.action_logger.log_action(
                    command=command,
                    result=result.get('result', ''),
                    success=result.get('success', False),
                    metadata=result.get('metadata', {})
                )
                
                # Determine if this was an AI response
                metadata = result.get('metadata', {})
                method = metadata.get('method', 'unknown')
                is_ai_response = method in ['ai_response', 'ai_with_actions', 'ai_help', 'ai_understanding', 'gemini_ai', 'task_planner'] or bool(result.get('metadata', {}).get('ai_frontdoor'))
                
                response_data = {
                    'success': result.get('success', False),
                    'result': result.get('result', ''),
                    'context': context,
                    'metadata': metadata,
                    'is_ai_response': is_ai_response,
                    'response_type': result.get('response_type', 'unknown')
                }
                
                # Add debug info if result is empty
                if not result.get('result'):
                    response_data['debug'] = f"No result from method: {method}"
                    logger.warning(f"Empty result from command: {command}, method: {method}")
                
                return jsonify(response_data)
                
            except Exception as e:
                logger.error(f"Error processing command: {str(e)}")
                logger.error(traceback.format_exc())
                
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'result': 'An error occurred while processing your command.'
                })
        
        @self.app.route('/command/confirm', methods=['POST'])
        def confirm_command():
            try:
                data = request.get_json() or {}
                cache_key = data.get('cache_key', '')
                confirmed = data.get('confirmed', False)
                original_command = data.get('original_command', '')
                incoming_context = data.get('context', [])
                
                # Use persistent context instead of incoming context
                context = self.persistent_context.copy()
                
                if not cache_key or not original_command:
                    return jsonify({
                        'success': False,
                        'error': 'Missing cache_key or original_command'
                    })
                
                # Log the confirmation
                logger.info(f"Command confirmation: {confirmed} for command: {original_command}")
                
                # Process the confirmed command
                result = self.command_processor.confirm_and_execute(
                    cache_key, confirmed, original_command, context
                )
                
                # Log the result
                logger.info(f"Confirmed command result: success={result.get('success')}")
                
                # Update persistent context if command was executed
                if confirmed and result.get('success'):
                    new_context_item = {
                        'timestamp': datetime.now().isoformat(),
                        'command': original_command,
                        'result': result.get('result', ''),
                        'success': result.get('success', False)
                    }
                    
                    # Add to persistent context and keep only last 10 items
                    self.persistent_context.append(new_context_item)
                    if len(self.persistent_context) > 10:
                        self.persistent_context = self.persistent_context[-10:]
                    
                    # Update local context for response
                    context = self.persistent_context.copy()
                    
                    # Log the action
                    self.action_logger.log_action(
                        command=original_command,
                        result=result.get('result', ''),
                        success=result.get('success', False),
                        metadata=result.get('metadata', {})
                    )
                
                # Determine if this was an AI response
                metadata = result.get('metadata', {})
                method = metadata.get('method', 'unknown')
                is_ai_response = method in ['ai_response', 'ai_with_actions', 'ai_help', 'ai_understanding', 'gemini_ai', 'task_planner']
                
                response_data = {
                    'success': result.get('success', False),
                    'result': result.get('result', ''),
                    'context': context,
                    'metadata': metadata,
                    'is_ai_response': is_ai_response
                }
                
                return jsonify(response_data)
                
            except Exception as e:
                logger.error(f"Error confirming command: {str(e)}")
                logger.error(traceback.format_exc())
                
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'result': 'An error occurred while confirming the command.'
                })
        
        @self.app.route('/context/clear', methods=['POST'])
        def clear_context():
            try:
                session_id = (request.get_json() or {}).get('session_id', 'default')
                self.context_storage[session_id] = []
                return jsonify({'success': True})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/refresh_context', methods=['POST'])
        def refresh_context():
            try:
                # Clear the persistent context (only happens on Cmd+R)
                self.persistent_context = []
                # Also clear all session-based context storage
                self.context_storage = {}
                logger.info("Context refreshed via Cmd+R")
                return jsonify({'success': True, 'message': 'Context refreshed successfully'})
            except Exception as e:
                logger.error(f"Error refreshing context: {str(e)}")
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/logs', methods=['GET'])
        def get_logs():
            try:
                limit = request.args.get('limit', 50, type=int)
                logs = self.action_logger.get_recent_logs(limit)
                return jsonify({'success': True, 'logs': logs})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/capabilities', methods=['GET'])
        def get_capabilities():
            return jsonify({
                'success': True,
                'capabilities': self.command_processor.get_capabilities()
            })
        
        # Serve frontend files
        @self.app.route('/')
        def serve_index():
            try:
                # Serve the unified overlay as the main interface
                src_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src')
                return send_file(os.path.join(src_dir, 'overlay-unified.html'))
            except Exception as e:
                logger.error(f"Error serving index: {str(e)}")
                return f"Error loading interface: {str(e)}", 500
        
        @self.app.route('/src/<path:filename>')
        def serve_src_files(filename):
            try:
                src_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src')
                return send_from_directory(src_dir, filename)
            except Exception as e:
                logger.error(f"Error serving file {filename}: {str(e)}")
                return f"File not found: {filename}", 404
    
    def _is_document_creation_request(self, command: str) -> bool:
        """Check if the command is requesting document or spreadsheet creation."""
        command_lower = command.lower()
        document_keywords = [
            'make a spreadsheet', 'create a spreadsheet', 'make spreadsheet',
            'create spreadsheet', 'make a document', 'create a document',
            'make document', 'create document', 'make a text document',
            'create a text document', 'write a document', 'generate a spreadsheet',
            'generate spreadsheet', 'make excel', 'create excel', 'make csv',
            'create csv', 'write an essay', 'write essay', 'csv spreadsheet',
            'financial spreadsheet', 'financial data', 'spreadsheet with',
            'create a csv', 'make a csv', 'generate csv'
        ]
        return any(keyword in command_lower for keyword in document_keywords)
    
    def _handle_document_creation(self, command: str) -> Dict[str, Any]:
        """Handle document/spreadsheet creation requests."""
        try:
            logger.info(f"Processing document creation request: {command}")
            
            # Use Gemini AI to generate document content
            if not self.gemini_ai:
                return {
                    'success': False,
                    'result': 'AI service is not available for document creation.',
                    'metadata': {'error': True}
                }
            
            # Create a web search function for data validation
            def web_search_for_validation(query: str, num: int = 3) -> List[Dict[str, Any]]:
                """Simple web search function that returns search results data."""
                try:
                    import requests
                    from bs4 import BeautifulSoup
                    import urllib.parse
                    
                    # Construct Google search URL
                    search_url = f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}&num={num}"
                    
                    # Headers to mimic a real browser
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    }
                    
                    response = requests.get(search_url, headers=headers, timeout=10)
                    response.raise_for_status()
                    
                    # Parse the HTML
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Find search result containers
                    search_containers = soup.find_all('div', class_='g')
                    
                    results = []
                    for container in search_containers[:num]:
                        try:
                            # Extract title and snippet
                            title_elem = container.find('h3')
                            title = title_elem.get_text() if title_elem else ''
                            
                            # Extract snippet
                            snippet_elem = container.find('span', class_='aCOpRe') or container.find('div', class_='VwiC3b')
                            snippet = snippet_elem.get_text() if snippet_elem else ''
                            
                            if title or snippet:
                                results.append({
                                    'title': title,
                                    'website_content': snippet,
                                    'website_snippets': snippet
                                })
                        except Exception:
                            continue
                    
                    return results
                except Exception as e:
                    logger.error(f"Web search error: {str(e)}")
                    return []
            
            # Generate content using the new method with web search validation
            content_result = self.gemini_ai.generate_document_content(command, web_search_func=web_search_for_validation)
            
            if not content_result.get('success', False):
                return {
                    'success': False,
                    'result': f"Failed to generate document content: {content_result.get('error', 'Unknown error')}",
                    'metadata': {'error': True}
                }
            
            # Extract content and metadata
            content = content_result.get('content', '')
            doc_type = content_result.get('type', 'document')
            title = content_result.get('title', 'Generated Document')
            raw_json_content = content_result.get('raw_json_content')
            
            # Log raw JSON content to terminal for investigation
            if raw_json_content:
                logger.info("=== RAW JSON CONTENT FOR INVESTIGATION ===")
                logger.info(f"Request: {command}")
                logger.info(f"Raw JSON Data:\n{raw_json_content}")
                logger.info("=== END RAW JSON CONTENT ===")
            else:
                logger.warning(f"No raw JSON content available for request: {command}")
            
            # Save the document
            file_result = self._save_document(content, doc_type, title, raw_json_content)
            
            if file_result.get('success', False):
                return {
                    'success': True,
                    'result': f"✅ {doc_type.title()} created successfully!\n\n📁 Saved as: {file_result['filename']}\n\n📝 Content: {file_result['summary']}",
                    'metadata': {
                        'method': 'document_creation',
                        'file_path': file_result['file_path'],
                        'doc_type': doc_type
                    }
                }
            else:
                return {
                    'success': False,
                    'result': f"Failed to save document: {file_result.get('error', 'Unknown error')}",
                    'metadata': {'error': True}
                }
                
        except Exception as e:
            logger.error(f"Error in document creation: {str(e)}")
            return {
                'success': False,
                'result': f'An error occurred while creating the document: {str(e)}',
                'metadata': {'error': True}
            }
    
    def _save_document(self, content: str, doc_type: str, title: str, raw_json_content: Optional[str] = None) -> Dict[str, Any]:
        """Save the generated content to a file."""
        try:
            import os
            from datetime import datetime
            
            # Create documents directory if it doesn't exist
            docs_dir = os.path.expanduser("~/Documents/Cluely_Generated")
            os.makedirs(docs_dir, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')
            
            if doc_type == 'spreadsheet':
                filename = f"{safe_title}_{timestamp}.csv"
                file_path = os.path.join(docs_dir, filename)
                
                # Write CSV content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    if raw_json_content:
                        f.write('\n\n-- RAW JSON RESPONSE FROM GEMINI --\n')
                        f.write(raw_json_content)
                    
            else:  # document/text
                filename = f"{safe_title}_{timestamp}.txt"
                file_path = os.path.join(docs_dir, filename)
                
                # Write text content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            # Generate summary
            lines = content.split('\n')
            summary = f"Contains {len(lines)} lines of content"
            if doc_type == 'spreadsheet':
                summary = f"Contains {len([l for l in lines if l.strip()])} rows of data"
            
            return {
                'success': True,
                'filename': filename,
                'file_path': file_path,
                'summary': summary
            }
            
        except Exception as e:
            logger.error(f"Error saving document: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def run(self, host='0.0.0.0', port=None):
        if port is None:
            port = self.config.get('server.port', 8888)
        logger.info(f"Starting Cluely backend on {host}:{port}")
        
        # Check for required permissions
        if not self.security_manager.check_permissions():
            logger.warning("Some required permissions are missing. App functionality may be limited.")
        
        # Use Flask's built-in server for dev
        self.app.run(host=host, port=port)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Cluely AI Assistant Backend')
    parser.add_argument('--daemon', action='store_true', 
                       help='Run as daemon service')
    parser.add_argument('--host', default='localhost', 
                       help='Host to bind to (default: localhost)')
    parser.add_argument('--port', type=int, default=8888, 
                       help='Port to bind to (default: 8888)')
    parser.add_argument('--debug', action='store_true', 
                       help='Enable debug mode')
    parser.add_argument('--check-permissions', action='store_true',
                       help='Check macOS permissions and exit')
    
    args = parser.parse_args()
    
    # If running permission check, do it and exit
    if args.check_permissions:
        from core.macos_permissions import MacOSPermissionsManager
        perm_manager = MacOSPermissionsManager()
        results = perm_manager.check_all_permissions()
        
        print("=== macOS Permissions Status ===")
        print(f"All permissions granted: {results['all_granted']}")
        print("\nPermission Details:")
        for perm, status in results['permissions'].items():
            status_str = "✅ GRANTED" if status else "❌ DENIED"
            print(f"  {perm}: {status_str}")
        
        if not results['all_granted']:
            print("\nMissing permissions:")
            for missing in results['missing']:
                print(f"  - {missing}")
            print("\nSetup instructions:")
            for instruction in results['instructions']:
                print(f"  {instruction}")
        
        sys.exit(0 if results['all_granted'] else 1)
    
    try:
        backend = CluelyBackend()
        
        if args.daemon:
            logger.info("Starting Cluely backend in daemon mode...")
            # For daemon mode, we might want to detach from terminal
            # and run in background with different logging
            try:
                import daemon
                import daemon.pidfile
                
                daemon_context = daemon.DaemonContext(
                    pidfile=daemon.pidfile.TimeoutPIDLockFile('/tmp/cluely.pid'),
                    working_directory=os.getcwd()
                )
                
                with daemon_context:
                    backend.run(host=args.host, port=args.port)
            except ImportError:
                logger.warning("python-daemon not available. Running in background mode without full daemonization.")
                # Run in background without full daemonization
                backend.run(host=args.host, port=args.port)
        else:
            logger.info("Starting Cluely backend in foreground mode...")
            backend.run(host=args.host, port=args.port)
            
    except KeyboardInterrupt:
        logger.info("Backend shutting down...")
    except Exception as e:
        logger.error(f"Failed to start backend: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    main()
