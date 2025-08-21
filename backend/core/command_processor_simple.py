import logging
from typing import Dict, Any
import asyncio

logger = logging.getLogger(__name__)

class CommandProcessor:
    def __init__(self):
        self.gemini_ai = None
        self.security_manager = None
        self.action_logger = None
        self._initialize_components()
    
    def _initialize_components(self):
        # Initialize Gemini AI if available
        try:
            from core.gemini_ai import GeminiAI
            from utils.config import Config
            api_key = Config().get_gemini_api_key()
            if api_key:
                self.gemini_ai = GeminiAI(api_key=api_key)
        except ImportError as e:
            logger.warning(f"Could not initialize Gemini AI: {e}")
        
        # Initialize security manager and action logger
        try:
            from core.security_manager import SecurityManager
            from core.action_logger import ActionLogger
            self.security_manager = SecurityManager()
            self.action_logger = ActionLogger()
        except ImportError as e:
            logger.warning(f"Could not initialize security components: {e}")
    
    async def determine_intent(self, user_input: str) -> Dict[str, Any]:
        """
        Determine if the user input is a command or just a chat message.
        Returns a dict with 'is_command' boolean and 'confidence' float.
        """
        if not user_input:
            return {'is_command': False, 'confidence': 0.0}
        
        # Simple keyword-based intent detection (can be enhanced with ML later)
        command_keywords = [
            'open', 'close', 'start', 'stop', 'search', 'find',
            'send', 'create', 'delete', 'update', 'show', 'list',
            'enable', 'disable', 'set', 'get', 'run', 'execute',
            'browse', 'navigate', 'go to', 'play', 'pause', 'next'
        ]
        
        # Check for command-like patterns
        lower_input = user_input.lower()
        is_likely_command = any(
            keyword in lower_input.split()[:3]  # Only check first few words
            for keyword in command_keywords
        )
        
        # If using Gemini AI, get a more sophisticated classification
        if self.gemini_ai:
            try:
                prompt = f"""
                Analyze if the following user input is a command to perform an action 
                or just a general question/chat message. 
                
                Input: "{user_input}"
                
                Respond with JSON only: {{"is_command": boolean, "confidence": float, "reason": str}}
                """
                
                response = await self.gemini_ai.generate_text(prompt)
                try:
                    import json
                    ai_judgment = json.loads(response)
                    return {
                        'is_command': ai_judgment.get('is_command', is_likely_command),
                        'confidence': ai_judgment.get('confidence', 0.5),
                        'reason': ai_judgment.get('reason', 'Keyword match' if is_likely_command else 'No command detected')
                    }
                except (json.JSONDecodeError, AttributeError):
                    logger.warning("Failed to parse AI response for intent detection")
            except Exception as e:
                logger.error(f"Error in AI intent detection: {e}")
        
        # Fallback to keyword-based detection
        return {
            'is_command': is_likely_command,
            'confidence': 0.7 if is_likely_command else 0.3,
            'reason': 'Keyword match' if is_likely_command else 'No command detected'
        }
    
    async def process_command(self, command: str) -> str:
        """Process a command that was identified as an action."""
        # Log the command
        if self.action_logger:
            self.action_logger.log_action('command_received', f'Processing command: {command}')
        
        # Simple command processing (can be enhanced)
        if 'what can you do' in command.lower() or 'help' in command.lower():
            return self._get_capabilities()
            
        # Handle app-related queries
        if any(phrase in command.lower() for phrase in ['what apps', 'which apps', 'connect with']):
            return self._get_connected_apps()
        
        # Add more command handlers here
        
        return f"I'm not sure how to process the command: {command}"
    
    async def generate_chat_response(self, message: str) -> str:
        """Generate a conversational response to a chat message."""
        if self.gemini_ai:
            try:
                response = await self.gemini_ai.generate_text(message)
                return response.strip()
            except Exception as e:
                logger.error(f"Error generating AI response: {e}")
        
        # Fallback responses if AI is not available
        fallback_responses = [
            "I'm here to help! How can I assist you today?",
            "I'm still learning. Could you rephrase that?",
            "I'm not sure I understand. Could you provide more details?",
            "Thanks for reaching out! How can I help you?"
        ]
        import random
        return random.choice(fallback_responses)
    
    def _get_capabilities(self) -> str:
        """Return a description of what commands are available."""
        return """Here are some things I can help you with:
        
        - Open applications and websites
        - Search the web
        - Answer questions
        - Set reminders and timers
        - Control media playback
        - And much more!
        
        Just tell me what you'd like to do in natural language."""
    
    def get_available_commands(self) -> list:
        """Return a list of available commands."""
        return [
            "open [app/website]",
            "search [query]",
            "what can you do?",
            "what apps do you work with?",
            "help"
        ]
        
    def _get_connected_apps(self) -> str:
        """Return information about connected apps and capabilities."""
        return """I can work with various applications and services including:

📱 Native Apps:
- Browsers (Safari, Chrome, Firefox)
- Messaging (iMessage, Slack, Discord)
- Productivity (Calendar, Notes, Reminders)
- Media (Music, Videos, Photos)

🌐 Web Services:
- Google Workspace (Gmail, Docs, Sheets)
- Microsoft 365 (Outlook, Word, Excel)
- Project Management (Asana, Trello, Jira)
- Communication (Zoom, Teams, Google Meet)

💻 System:
- File management
- Window control
- System settings
- Automation workflows

You can ask me to open these apps, perform actions, or help you work with them more efficiently!"""
