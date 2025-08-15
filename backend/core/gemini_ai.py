import os
import logging
import json
from typing import Dict, Any, List, Optional
import google.generativeai as genai

logger = logging.getLogger(__name__)

class GeminiAI:
    def __init__(self, api_key: str):
        """Initialize Gemini AI with API key."""
        self.api_key = api_key
        genai.configure(api_key=api_key)
        
        # Initialize the model
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # System prompt to make Gemini understand it's controlling a computer
        self.system_prompt = """You are Cluely, an AI assistant with direct computer control capabilities. You can:

1. EXECUTE SYSTEM COMMANDS: Run shell commands, scripts, and programs
2. FILE OPERATIONS: Create, read, edit, delete, copy, move files and folders
3. APP CONTROL: Launch, close, and switch between applications
4. WEB AUTOMATION: Browse websites, search the web, download files
5. SYSTEM MONITORING: Check system status, processes, time, weather

When users ask you to do something with their computer, you should:
- Be helpful and execute the requested actions
- Explain what you're doing
- Ask for confirmation for potentially destructive operations
- Provide clear feedback on results

You have access to these computer control functions through the Cluely backend system. Always be precise and helpful in your responses.

Current capabilities:
- File management (create, edit, delete, search files)
- Application control (launch apps, close windows)
- Web operations (search, browse, download)
- Script execution (Python, Bash, etc.)
- System information and monitoring

Respond naturally and helpfully to user requests."""

    def generate_response(self, user_input: str, context: List[Dict] = None, available_actions: List[str] = None) -> Dict[str, Any]:
        """Generate an AI response using Gemini."""
        try:
            # Build the conversation context
            conversation_history = []
            
            if context:
                for item in context[-5:]:  # Last 5 interactions
                    conversation_history.append(f"User: {item.get('command', '')}")
                    conversation_history.append(f"Assistant: {item.get('result', '')}")
            
            # Build the prompt
            prompt_parts = [self.system_prompt]
            
            if available_actions:
                prompt_parts.append(f"\nAvailable system actions: {', '.join(available_actions)}")
            
            if conversation_history:
                prompt_parts.append(f"\nRecent conversation:\n" + "\n".join(conversation_history))
            
            prompt_parts.append(f"\nUser request: {user_input}")
            prompt_parts.append("\nProvide a helpful response. If this requires a system action, suggest the specific command or explain how you would accomplish it.")
            
            full_prompt = "\n".join(prompt_parts)
            
            # Generate response
            response = self.model.generate_content(full_prompt)
            
            # Parse the response to determine if it requires system actions
            ai_response = response.text
            
            # Try to extract actionable commands from the response
            suggested_actions = self._extract_actions(ai_response, user_input)
            
            return {
                'success': True,
                'response': ai_response,
                'suggested_actions': suggested_actions,
                'requires_action': len(suggested_actions) > 0
            }
            
        except Exception as e:
            logger.error(f"Gemini AI error: {str(e)}")
            return {
                'success': False,
                'response': f"I apologize, but I encountered an error while processing your request: {str(e)}",
                'suggested_actions': [],
                'requires_action': False
            }
    
    def _extract_actions(self, ai_response: str, user_input: str) -> List[Dict[str, str]]:
        """Extract actionable commands from AI response."""
        actions = []
        
        # Common action patterns that Gemini might suggest
        action_patterns = {
            'file_create': ['create file', 'make file', 'new file'],
            'file_open': ['open file', 'show file', 'display file'],
            'app_launch': ['launch app', 'open app', 'start app', 'run app'],
            'web_search': ['search web', 'google search', 'search for'],
            'system_info': ['system info', 'system status', 'check system'],
            'script_run': ['run script', 'execute script', 'python script']
        }
        
        response_lower = ai_response.lower()
        
        for action_type, keywords in action_patterns.items():
            for keyword in keywords:
                if keyword in response_lower:
                    actions.append({
                        'type': action_type,
                        'description': f"Execute {action_type.replace('_', ' ')}",
                        'confidence': 0.8
                    })
                    break
        
        return actions
    
    def should_use_ai(self, command: str) -> bool:
        """Determine if a command should be processed by AI instead of rule-based system."""
        # Use AI for conversational queries, complex requests, or when rule-based system fails
        ai_indicators = [
            'how', 'why', 'what', 'when', 'where', 'who',
            'explain', 'tell me', 'describe', 'help me understand',
            'i need', 'can you', 'please', 'would you',
            'recommend', 'suggest', 'advice', 'think',
            'best way', 'how to', 'tutorial', 'guide'
        ]
        
        command_lower = command.lower()
        return any(indicator in command_lower for indicator in ai_indicators)
    
    def enhance_command_understanding(self, command: str) -> Dict[str, Any]:
        """Use AI to better understand ambiguous commands."""
        try:
            prompt = f"""
            Analyze this user command and determine what system action they want to perform:
            
            Command: "{command}"
            
            Respond with JSON in this format:
            {{
                "intent": "file_operation|app_control|web_operation|system_info|script_execution|general_query",
                "action": "specific_action_name",
                "target": "what_to_act_on",
                "parameters": {{"key": "value"}},
                "confidence": 0.0-1.0
            }}
            
            Only respond with valid JSON, no other text.
            """
            
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)
            
            return {
                'success': True,
                'understanding': result
            }
            
        except Exception as e:
            logger.error(f"Command understanding error: {str(e)}")
            return {
                'success': False,
                'understanding': {
                    'intent': 'general_query',
                    'action': 'unknown',
                    'target': command,
                    'confidence': 0.1
                }
            }
    
    def get_contextual_help(self, user_query: str, available_commands: List[str]) -> str:
        """Get AI-powered contextual help."""
        try:
            prompt = f"""
            A user is asking for help with: "{user_query}"
            
            Available system commands include: {', '.join(available_commands)}
            
            Provide a helpful response that:
            1. Addresses their specific question
            2. Suggests relevant commands they can use
            3. Gives examples of how to phrase requests
            4. Is concise but informative
            
            Be friendly and helpful.
            """
            
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Contextual help error: {str(e)}")
            return "I'm here to help! You can ask me to manage files, control apps, search the web, run scripts, or get system information. Try commands like 'create file notes.txt' or 'launch chrome'."
