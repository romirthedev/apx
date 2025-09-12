import asyncio
import json
import logging
import os
import re
import sys
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional

from flask import Flask, request, jsonify
from flask_cors import CORS
import threading

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
        
        self._setup_routes()
        
    def _setup_routes(self):
        @self.app.route('/health', methods=['GET'])
        def health_check():
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0'
            })
        
        @self.app.route('/transcribe_audio', methods=['POST'])
        def transcribe_audio():
            try:
                data = request.get_json() or {}
                audio_data = data.get('audio_data', '')
                use_gemini = data.get('use_gemini', False)
                capture_system_audio = data.get('capture_system_audio', False)
                
                # Import audio manager
                from plugins.audio_manager import AudioManager
                audio_manager = AudioManager()
                
                # If requested to capture system audio (for Zoom/Meet calls)
                if capture_system_audio and not audio_data:
                    logger.info("Attempting to capture system audio...")
                    capture_result = audio_manager.capture_system_audio(duration_seconds=5)
                    
                    if capture_result.get('success', False):
                        audio_data = capture_result.get('audio_data', '')
                        logger.info("Successfully captured system audio")
                    else:
                        logger.warning(f"System audio capture failed: {capture_result.get('error')}")
                
                if not audio_data:
                    return jsonify({
                        'success': False,
                        'error': 'No audio data provided or system audio capture failed'
                    })
                
                # Transcribe audio with specified model
                logger.info(f"Transcribing audio with {'Gemini' if use_gemini else 'standard'} model")
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
        
        @self.app.route('/command', methods=['POST'])
        def process_command():
            try:
                data = request.get_json() or {}
                command = data.get('command', '').strip()
                context = data.get('context', [])
                action_mode = data.get('action_mode', False)
                
                # Ensure context is always a list
                if not isinstance(context, list):
                    context = []
                
                if not command:
                    return jsonify({
                        'success': False,
                        'error': 'No command provided'
                    })
                
                # Log the incoming command
                logger.info(f"Processing command: {command}" + (" [ACTION MODE]" if action_mode else ""))
                
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
                
                # If we didn't already answer via AI chat, route to CommandProcessor
                if not used_ai_chat:
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
                
                # Log the result for debugging
                logger.info(f"Command result: success={result.get('success')}, method={result.get('metadata', {}).get('method')}")
                
                # Update context
                new_context_item = {
                    'timestamp': datetime.now().isoformat(),
                    'command': command,
                    'result': result.get('result', ''),
                    'success': result.get('success', False)
                }
                
                # Keep only last 10 context items
                context.append(new_context_item)
                if len(context) > 10:
                    context = context[-10:]
                
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
                context = data.get('context', [])
                
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
                
                # Update context if command was executed
                if confirmed and result.get('success'):
                    new_context_item = {
                        'timestamp': datetime.now().isoformat(),
                        'command': original_command,
                        'result': result.get('result', ''),
                        'success': result.get('success', False)
                    }
                    
                    context.append(new_context_item)
                    if len(context) > 10:
                        context = context[-10:]
                    
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
