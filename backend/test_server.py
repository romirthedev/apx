from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import sys
from pathlib import Path

# Add the backend directory to the Python path
sys.path.append(str(Path(__file__).parent.absolute()))

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Configure CORS to allow all origins and methods for testing
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Mock command processor for testing
class MockCommandProcessor:
    async def determine_intent(self, user_input):
        # Simple keyword-based intent detection for testing
        command_keywords = ['open', 'search', 'start', 'find']
        is_command = any(word in user_input.lower().split() for word in command_keywords)
        
        return {
            'is_command': is_command,
            'confidence': 0.9 if is_command else 0.1,
            'reason': 'Test response'
        }
    
    async def process_command(self, command):
        return f"Processed command: {command}"
    
    async def generate_chat_response(self, message):
        return f"Chat response to: {message}"

# Initialize command processor
command_processor = MockCommandProcessor()

@app.route('/api/command', methods=['POST'])
async def handle_command():
    try:
        data = request.get_json()
        user_input = data.get('command', '').strip()
        
        if not user_input:
            return jsonify({
                'success': False,
                'error': 'No input provided'
            }), 400
        
        # First, ask the AI if this is a command or just chat
        intent = await command_processor.determine_intent(user_input)
        
        if intent['is_command']:
            # Process as a command
            result = await command_processor.process_command(user_input)
            return jsonify({
                'success': True,
                'is_command': True,
                'result': result
            })
        else:
            # Handle as a chat message
            response = await command_processor.generate_chat_response(user_input)
            return jsonify({
                'success': True,
                'is_command': False,
                'response': response
            })
    
    except Exception as e:
        logger.error(f"Error handling command: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    print("Starting test server on http://localhost:5001")
    app.run(debug=True, port=5001, use_reloader=False)
