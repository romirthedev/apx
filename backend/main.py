import asyncio
import json
import logging
import os
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
from utils.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cluely.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

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
        
        @self.app.route('/command', methods=['POST'])
        def process_command():
            try:
                data = request.get_json()
                command = data.get('command', '').strip()
                context = data.get('context', [])
                
                if not command:
                    return jsonify({
                        'success': False,
                        'error': 'No command provided'
                    })
                
                # Log the incoming command
                logger.info(f"Processing command: {command}")
                
                # All commands go through CommandProcessor (Task Planner bypassed)
                logger.info("Task Planner disabled: routing directly to CommandProcessor")
                result = self.command_processor.process(command, context)
                
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
                is_ai_response = method in ['ai_response', 'ai_with_actions', 'ai_help', 'ai_understanding', 'gemini_ai', 'task_planner']
                
                response_data = {
                    'success': result.get('success', False),
                    'result': result.get('result', ''),
                    'context': context,
                    'metadata': metadata,
                    'is_ai_response': is_ai_response
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
                data = request.get_json()
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
                session_id = request.get_json().get('session_id', 'default')
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
    
    def run(self, host='localhost', port=8888, debug=False):
        logger.info(f"Starting Cluely backend on {host}:{port}")
        
        # Check for required permissions
        if not self.security_manager.check_permissions():
            logger.warning("Some required permissions are missing. App functionality may be limited.")
        
        self.app.run(host=host, port=port, debug=debug, threaded=True)

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
                    backend.run(host=args.host, port=args.port, debug=args.debug)
            except ImportError:
                logger.warning("python-daemon not available. Running in background mode without full daemonization.")
                # Run in background without full daemonization
                backend.run(host=args.host, port=args.port, debug=args.debug)
        else:
            logger.info("Starting Cluely backend in foreground mode...")
            backend.run(host=args.host, port=args.port, debug=args.debug)
            
    except KeyboardInterrupt:
        logger.info("Backend shutting down...")
    except Exception as e:
        logger.error(f"Failed to start backend: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    main()
