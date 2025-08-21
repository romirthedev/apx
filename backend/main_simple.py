import asyncio
import logging
from quart import Quart, request, jsonify
from quart_cors import cors
from pathlib import Path
import sys

# Add the backend directory to the Python path
sys.path.append(str(Path(__file__).parent.absolute()))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleBackend:
    def __init__(self):
        self.app = Quart(__name__)
        self.app = cors(self.app, allow_origin=["*"])
        self.command_processor = None
        self.setup_routes()
        
    def setup_routes(self):
        @self.app.route('/api/command', methods=['POST'])
        async def handle_command():
            try:
                data = await request.get_json()
                user_input = data.get('command', '').strip()
                
                if not user_input:
                    return jsonify({
                        'success': False,
                        'error': 'No input provided'
                    }), 400
                
                # Initialize command processor if not already done
                if not self.command_processor:
                    from core.command_processor_simple import CommandProcessor
                    self.command_processor = CommandProcessor()
                
                # First, ask the AI if this is a command or just chat
                intent = await self.command_processor.determine_intent(user_input)
                
                if intent['is_command']:
                    # Process as a command
                    result = await self.command_processor.process_command(user_input)
                    return jsonify({
                        'success': True,
                        'is_command': True,
                        'result': result
                    })
                else:
                    # Handle as a chat message
                    response = await self.command_processor.generate_chat_response(user_input)
                    return jsonify({
                        'success': True,
                        'is_command': False,
                        'response': response
                    })
                    
                    class DummySecurityManager:
                        def check_permission(self, permission):
                            return True
                            
                    class DummyActionLogger:
                        def log_action(self, action_type, details):
                            logger.info(f"Action: {action_type} - {details}")
                    
                    self.command_processor = CommandProcessor(
                        DummySecurityManager(), 
                        DummyActionLogger()
                    )
                
                # Process the command
                result = await self.command_processor.process_command(command)
                
                return jsonify({
                    'success': True,
                    'response': result
                })
                
            except Exception as e:
                logger.error(f"Error handling command: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/health', methods=['GET'])
        async def health_check():
            return jsonify({
                'status': 'ok',
                'service': 'cluely-backend',
                'version': '1.0.0-simple'
            })
    
    async def run(self, host='0.0.0.0', port=5001):
        """Run the backend server."""
        logger.info(f"Starting Cluely backend on {host}:{port}")
        await self.app.run_task(host=host, port=port)

if __name__ == "__main__":
    backend = SimpleBackend()
    asyncio.run(backend.run())
