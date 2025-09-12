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
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')
        
        # System prompt to make Gemini understand it's controlling a computer
        self.system_prompt = """You are Cluely, an AI assistant with FULL COMPUTER CONTROL. You have complete access to execute any command on this Mac system.

🚨 EXECUTE ONLY - ZERO EXPLANATIONS - RESULTS ONLY
When users request actions, you MUST:
1. Execute the action SILENTLY with ABSOLUTELY NO explanation of what you're doing
2. Report ONLY the final results, never how you got them
3. NEVER ask permission or explain what you will do
4. If a command fails, try a simpler approach immediately without explaining the change
5. Always provide concrete results with no commentary or conversational language

AVAILABLE ACTIONS (execute these directly):
• SHELL COMMANDS: find, ls, grep, curl, python, npm, git - ANY terminal command
• FILE OPERATIONS: create, edit, delete, move, copy, search files and folders  
• APP CONTROL: launch/close applications, switch windows
• WEB AUTOMATION: browse websites, download files, search online
• SYSTEM INFO: check processes, disk usage, system status, time, weather

CRITICAL BEHAVIOR:
- User says "find smallest file" → EXECUTE search → Report: "Smallest files: file1.txt (0 bytes), file2.txt (12 bytes)..."
- User says "create file notes.txt" → CREATE file → Report: "Created notes.txt"
- User says "launch Chrome" → OPEN Chrome → Report: "Chrome launched"
- User says "what files are in downloads" → LIST files → Report: "Downloads contains: [file list]"
- User says "go to the linux website" or "open the python docs" → DO NOT just prepend https:// and open. INSTEAD: SEARCH online for the correct site, extract the best URL, then open it in the browser. Always reason in steps for ambiguous web requests.

❌ FORBIDDEN RESPONSES:
- "I understand you want me to find..."
- "I'll proceed with the search..."  
- "Do you want me to..."
- "This command will..."
- "Let me search for..."

✅ REQUIRED RESPONSES:
- Execute → Report results only
- "Found 3 files: example.txt (0 bytes)..."
- "Created file successfully"
- "Application launched"
- "Searched online for 'linux website', found: https://linux.org, opened in browser."

ERROR HANDLING:
- If search takes too long → Use faster limited search and report what you found
- If file not found → Create it or suggest alternative
- If app won't launch → Report error and suggest fix
- Always take action, never just explain what you "could" do

SYSTEM ACCESS:
- You have the ability to execute file searches, create/edit files, launch apps
- Commands are safe and run with appropriate permissions
- Execute first, report results after - users expect immediate action

Be direct, immediate, and action-oriented. Users expect you to DO things, not discuss them. For ambiguous web requests, always search online for the correct site before navigating. Reason in steps and execute each step directly."""

    def generate_response(self, user_input: str, context: List[Dict] = None, available_actions: List[str] = None, is_chat: bool = False) -> Dict[str, Any]:
        """Generate an AI response using Gemini with fallback to simple responses."""
        logger.debug(f"GeminiAI.generate_response received - user_input: {user_input}, is_chat: {is_chat}")
        # Handle common queries without API call first
        lower_input = user_input.lower()
        
        # Common queries with direct responses
        if any(phrase in lower_input for phrase in ['what apps', 'which apps', 'connect with']):
            return {
                'response': "I can work with various applications including browsers, messaging apps, productivity tools, and more. Here are some examples:\n\n"
                          "• Browsers: Chrome, Safari, Firefox\n"
                          "• Messaging: iMessage, Slack, Discord\n"
                          "• Productivity: Calendar, Notes, Reminders\n"
                          "• Media: Music, Photos, Videos\n\n"
                          "What would you like me to help you with?"
            }
        if any(phrase in lower_input for phrase in ['what can you do', 'help']):
            return {
                'response': "I can help you with various tasks including:\n\n"
                          "• Open applications and websites\n"
                          "• Search the web\n"
                          "• Answer questions\n"
                          "• Set reminders and timers\n"
                          "• Control media playback\n\n"
                          "Just let me know what you'd like to do!"
            }
        
        try:
            # Use different prompts for chat vs command responses
            if is_chat:
                # Chat-focused prompt for conversational responses
                chat_prompt = (
                    "Always format responses in Markdown. Use fenced code blocks ( lang … ), headings (# …), and standard LaTeX delimiters : $ for inline math (e.g., $f(x) = x^2$ ), and $$ or \[ \] for block math (e.g., $$ \int x^2 dx $$ or \[ \int x^2 dx \] )."
                    "You are Apx, a helpful AI assistant. Provide the direct answer to the user's question. If it seems like a friendly chat, be friendly, but if it is serious or direct, don't add fluff."
                    "Do NOT provide JSON responses or action commands. Just answer naturally and helpfully.\n\n"
                    f"User question: {user_input}\n\n"
                    "Provide a helpful, conversational response:"
                )
                
                response = self.model.generate_content(chat_prompt)
                return {
                    'success': True,
                    'response': response.text.strip()
                }
            
            # Original command-focused logic for actions
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
            prompt_parts.append("""
CRITICAL: For system commands, you MUST create structured action plans.

FORMAT FOR SYSTEM ACTIONS:
```json
{
  "response": "I'll help you with that. Let me break this down into steps...",
  "actions": [
    {"action": "open_app", "app": "Safari", "parameters": {}},
    {"action": "navigate_url", "url": "https://openai.com", "parameters": {}},
    {"action": "get_date", "parameters": {"format": "%B %d, %Y"}},
    {"action": "open_app", "app": "Notes", "parameters": {}},
    {"action": "type_text", "text": "August 15, 2025", "parameters": {}}
  ]
}
```

AVAILABLE ACTIONS:
- open_app: Launch applications
- close_app: Close applications  
- navigate_url: Open URLs in browsers
- click_coordinates: Click at x,y position
- type_text: Type text using keyboard
- press_keys: Press key combinations
- get_date: Get current date/time
- take_screenshot: Capture screen
- find_file: Search for files
- create_file: Create new files
- run_command: Execute shell commands
- get_system_info: Get system status

For conversational queries, respond normally without the JSON structure.""")
            
            full_prompt = "\n".join(prompt_parts)
            
            # Generate response
            response = self.model.generate_content(full_prompt)
            
            # Parse the response to determine if it requires system actions
            ai_response = response.text
            
            # Try to extract structured JSON actions first
            structured_actions = self._extract_json_actions(ai_response)
            
            # Fallback to pattern-based extraction if no JSON found
            if not structured_actions:
                structured_actions = self._extract_actions(ai_response, user_input)
            
            # If structured actions are found, return the raw AI response as the 'response' field
            if structured_actions:
                return {
                    'success': True,
                    'response': ai_response, # Return the full AI response, which should contain the JSON
                    'suggested_actions': structured_actions,
                    'requires_action': True
                }

            else:
                # If no structured actions, return the AI response as is
                return {
                    'success': True,
                    'response': ai_response,
                    'suggested_actions': [],
                    'requires_action': False
                }
            
        except Exception as e:
            logger.error(f"Gemini AI error: {str(e)}")
            error_message = str(e)
            
            # Check for specific error types and provide more helpful messages
            if "429" in error_message and "quota" in error_message.lower():
                friendly_message = "Sorry, the quota error has been hit :("
                # For quota errors, try to provide a simpler version of the task planner functionality
                if "find" in user_input.lower() and "file" in user_input.lower():
                    return {
                        'success': True,
                        'response': "I'll search for those files for you.",
                        'suggested_actions': [{
                            'type': 'run_command',
                            'description': "Execute file search",
                            'parameters': {
                                'command': f"find ~/Desktop -name '*.txt' -type f -exec ls -la {{}} \\;"
                            },
                            'confidence': 0.9,
                            'source': 'fallback_pattern'
                        }],
                        'requires_action': True
                    }
                # Handle app launch requests
                elif any(word in user_input.lower() for word in ['open', 'launch', 'start']) and any(word in user_input.lower() for word in ['app', 'application', 'calculator', 'safari', 'chrome', 'finder']):
                    # Extract app name from user input
                    app_name = "Calculator"  # Default
                    if "calculator" in user_input.lower():
                        app_name = "Calculator"
                    elif "safari" in user_input.lower():
                        app_name = "Safari"
                    elif "chrome" in user_input.lower():
                        app_name = "Google Chrome"
                    elif "finder" in user_input.lower():
                        app_name = "Finder"
                    
                    return {
                        'success': True,
                        'response': f"I'll open {app_name} for you.",
                        'suggested_actions': [{
                            'type': 'open_app',
                            'description': f"Open {app_name} application",
                            'parameters': {
                                'app': app_name
                            },
                            'confidence': 0.9,
                            'source': 'fallback_pattern'
                        }],
                        'requires_action': True
                    }
                # Handle joke requests specifically
                elif "joke" in user_input.lower() or "tell me a joke" in user_input.lower():
                    jokes = [
                        "Why don't scientists trust atoms? Because they make up everything!",
                        "Why did the scarecrow win an award? Because he was outstanding in his field!",
                        "What do you call a fake noodle? An impasta!",
                        "How does a computer get drunk? It takes screenshots!",
                        "Why did the programmer quit his job? Because he didn't get arrays!",
                        "What's a computer's favorite snack? Microchips!",
                        "Why don't programmers like nature? It has too many bugs!"
                    ]
                    import random
                    return {
                        'success': True,
                        'response': random.choice(jokes),
                        'suggested_actions': [],
                        'requires_action': False
                    }
            elif "403" in error_message or "401" in error_message:
                friendly_message = "Authentication error with the Gemini API. Please check your API key configuration."
            else:
                friendly_message = f"I encountered an error while processing your request: {error_message}"
                
            logger.error(f"Gemini AI error details: {error_message}")
            
            return {
                'success': False,
                'response': friendly_message,
                'suggested_actions': [],
                'requires_action': False
            }
    
    def _extract_actions(self, ai_response: str, user_input: str) -> List[Dict[str, str]]:
        """Extract actionable commands from AI response."""
        actions = []
        
        # Enhanced action patterns that Gemini might suggest
        action_patterns = {
            'file_create': ['create file', 'make file', 'new file', 'generate file', 'build file', 'i\'ve created', 'creating', 'i will create'],
            'file_open': ['open file', 'show file', 'display file', 'view file', 'read file'],
            'file_edit': ['edit file', 'modify file', 'update file', 'change file', 'write to file'],
            'file_delete': ['delete file', 'remove file', 'erase file'],
            'file_search': ['find file', 'search file', 'locate file', 'find smallest', 'find largest', 'search for file', 'smallest file', 'largest file'],
            'system_search': ['find smallest file', 'find largest file', 'search system', 'scan for files', 'finding the smallest', 'searching for smallest', 'looking for smallest'],
            'app_launch': ['launch app', 'open app', 'start app', 'run app', 'i\'ll launch', 'launching', 'i will open'],
            'app_close': ['close app', 'quit app', 'exit app', 'stop app', 'kill app'],
            'web_search': ['search web', 'google search', 'search for', 'look up', 'find online', 'web search'],
            'web_browse': ['browse', 'visit', 'go to', 'navigate to', 'open url'],
            'system_info': ['system info', 'system status', 'check system', 'system details'],
            'script_run': ['run script', 'execute script', 'python script', 'bash command', 'run command', 'execute command', 'terminal command'],
            'organize': ['organize', 'sort', 'arrange', 'clean up', 'tidy up', 'structure'],
            'backup': ['backup', 'back up', 'save copy', 'create backup', 'archive'],
            'screenshot': ['screenshot', 'screen capture', 'take screenshot', 'capture screen'],
            'terminal_command': ['find /', 'ls -la', 'grep', 'cat', 'head', 'tail', 'sort', 'awk', 'sed', 'i\'m finding', 'i\'m searching', 'i\'m looking']
        }
        
        response_lower = ai_response.lower()
        user_input_lower = user_input.lower()
        
        # Check both the AI response and original user input for action indicators
        combined_text = response_lower + " " + user_input_lower
        
        for action_type, keywords in action_patterns.items():
            for keyword in keywords:
                if keyword in combined_text:
                    actions.append({
                        'type': action_type,
                        'description': f"Execute {action_type.replace('_', ' ')}",
                        'confidence': 0.8,
                        'source': 'ai_response' if keyword in response_lower else 'user_input'
                    })
                    break  # Only add each action type once
        
        # Check for specific file names in create commands
        if 'file_create' in [a['type'] for a in actions]:
            import re
            # Look for filename patterns in user input
            filename_patterns = [
                r'create (?:file |)([^\s]+\.[\w]+)',  # "create file name.ext"
                r'make (?:file |)([^\s]+\.[\w]+)',    # "make file name.ext"  
                r'new (?:file |)([^\s]+\.[\w]+)',     # "new file name.ext"
                r'file (?:called |named |)([^\s]+\.[\w]+)'  # "file called name.ext"
            ]
            
            for pattern in filename_patterns:
                match = re.search(pattern, user_input_lower)
                if match:
                    # Update the file_create action with specific filename
                    for action in actions:
                        if action['type'] == 'file_create':
                            action['filename'] = match.group(1)
                            action['confidence'] = 0.9
                            break
                    break
        
        return actions
    
    def _extract_json_actions(self, ai_response: str) -> List[Dict[str, Any]]:
        """Extract JSON-formatted action plans from AI response."""
        actions = []
        
        try:
            import re
            import json
            
            # Look for JSON inside code blocks with improved pattern matching
            json_patterns = [
                r'```json\s*(.*?)\s*```',  # Standard markdown JSON block
                r'```\s*(\{.*?\})\s*```',   # Generic code block with JSON object
                r'\{[\s\n]*"response"[\s\n]*:.*?"actions"[\s\n]*:[\s\n]*\[.*?\][\s\n]*\}', # Raw JSON with actions array
                r'\{[\s\n]*"actions"[\s\n]*:[\s\n]*\[.*?\][\s\n]*\}' # Raw JSON with only actions array
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, ai_response, re.DOTALL)
                
                for match in matches:
                    try:
                        # Clean up the match to handle potential formatting issues
                        cleaned_match = match.strip()
                        # Remove any trailing commas that might cause parsing errors
                        cleaned_match = re.sub(r',\s*}', '}', cleaned_match)
                        cleaned_match = re.sub(r',\s*]', ']', cleaned_match)
                        
                        parsed_json = json.loads(cleaned_match)
                        
                        # Check if the parsed JSON has an "actions" array
                        if isinstance(parsed_json, dict) and 'actions' in parsed_json:
                            action_list = parsed_json['actions']
                            
                            # Process each action in the list
                            for action in action_list:
                                if isinstance(action, dict) and 'action' in action:
                                    # Convert action to standard format
                                    actions.append({
                                        'type': action['action'],
                                        'description': f"Execute {action['action']}",
                                        'parameters': {k: v for k, v in action.items() if k != 'action'},
                                        'confidence': 0.95,
                                        'source': 'json_structure'
                                    })
                            
                            # If we found valid actions, no need to check other patterns
                            if actions:
                                break
                                
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse JSON from match: {match[:100]}...")
                
                # If we found valid actions, no need to check other patterns
                if actions:
                    break
            
        except Exception as e:
            logger.error(f"Error extracting JSON actions: {str(e)}")
        
        return actions

    def _extract_structured_actions(self, ai_response: str) -> List[Dict[str, str]]:
        """Extract structured action plans from AI response."""
        actions = []
        
        try:
            import re
            import json
            
            # Look for PLANNED_ACTIONS in the response
            pattern = r'PLANNED_ACTIONS:\s*\[(.*?)\]'
            match = re.search(pattern, ai_response, re.DOTALL)
            
            if match:
                actions_text = '[' + match.group(1) + ']'
                try:
                    parsed_actions = json.loads(actions_text)
                    
                    for action in parsed_actions:
                        if isinstance(action, dict) and 'action' in action:
                            actions.append({
                                'type': action['action'],
                                'target': action.get('target', ''),
                                'parameters': action.get('parameters', {}),
                                'description': f"Execute {action['action']} on {action.get('target', 'system')}",
                                'confidence': 0.95,
                                'source': 'structured_plan'
                            })
                except json.JSONDecodeError:
                    logger.warning("Failed to parse structured actions JSON")
            
        except Exception as e:
            logger.error(f"Error extracting structured actions: {str(e)}")
        
        return actions

    def should_use_ai(self, command: str) -> bool:
        """Determine if a command should be processed by AI instead of rule-based system."""
        # Use AI for conversational queries, complex requests, or natural language action requests
        ai_indicators = [
            # Conversational patterns
            'how', 'why', 'what', 'when', 'where', 'who',
            'explain', 'tell me', 'describe', 'help me understand',
            'i need', 'can you', 'please', 'would you',
            'recommend', 'suggest', 'advice', 'think',
            'best way', 'how to', 'tutorial', 'guide',
            # Natural language action requests
            'help me', 'i want to', 'i need to', 'could you',
            'would you mind', 'can you help me', 'please help',
            # Complex or multi-part requests
            'and also', 'then', 'after that', 'both', 'multiple'
        ]
        
        command_lower = command.lower()
        
        # Use AI if command contains conversational indicators
        if any(indicator in command_lower for indicator in ai_indicators):
            return True
            
        # Use AI for longer, more natural language requests (likely more complex)
        if len(command.split()) > 6:  # Commands with more than 6 words are likely conversational
            return True
            
        # Use AI for questions (end with ?)
        if command.strip().endswith('?'):
            return True
            
        return False
    
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
            text = response.text.strip()
            try:
                data = json.loads(text)
            except Exception:
                import re
                m = re.search(r"\{[\s\S]*\}", text)
                if not m:
                    raise ValueError("No JSON found in understanding response")
                data = json.loads(m.group(0))
            return {
                'success': True,
                'understanding': data
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

    def classify_intent(self, user_input: str) -> Dict[str, Any]:
        """Classify raw user input as 'command' (requires action) or 'chat' (no action).

        Returns a dict:
            {
              'success': bool,
              'type': 'command'|'chat',
              'requires_action': bool,
              'confidence': float,
              'reason': str
            }
        """
        logger.debug(f"GeminiAI.classify_intent received - user_input: {user_input}")
        try:
            prompt = (
                "You are an intent classifier. Decide if the user's message is a COMMAND that requires taking an action on the computer, "
                "or a CHAT message that is just a question or conversation.\n\n"
                "COMMANDS (require computer actions):\n"
                "- 'open chrome' - launches an application\n"
                "- 'create file notes.txt' - creates a file\n"
                "- 'find largest file' - searches filesystem\n"
                "- 'launch calculator' - opens an app\n"
                "- 'delete temp files' - removes files\n"
                "- 'take screenshot' - captures screen\n"
                "- 'read screen text' - performs OCR on screen\n\n"
                "CHAT (just questions/conversation):\n"
                "- 'what is the largest rock' - general knowledge question\n"
                "- 'how are you' - conversational\n"
                "- 'what is python' - informational question\n"
                "- 'tell me about AI' - general inquiry\n"
                "- 'what's the weather like' - information request\n"
                "- 'explain quantum physics' - educational question\n"
                "- 'analyze this captured content' - analyzing already captured content\n"
                "- 'what does this screen show' - discussing captured content\n"
                "- 'explain what's on my screen' - analyzing captured content\n\n"
                "User message: " + json.dumps(user_input) + "\n\n"
                "Required JSON schema:\n"
                "{\n"
                "  \"type\": \"command\" | \"chat\",\n"
                "  \"requires_action\": boolean,\n"
                "  \"confidence\": number (0.0-1.0),\n"
                "  \"reason\": string\n"
                "}"
            )
            response = self.model.generate_content(prompt)
            text = response.text.strip()

            # Try direct JSON parse
            try:
                data = json.loads(text)
            except Exception:
                # Try to extract JSON block
                import re
                m = re.search(r"\{[\s\S]*\}", text)
                if not m:
                    raise ValueError("No JSON found in classifier response")
                data = json.loads(m.group(0))

            ctype = str(data.get('type', 'chat')).lower()
            requires = bool(data.get('requires_action', ctype == 'command'))
            conf = float(data.get('confidence', 0.5))
            reason = str(data.get('reason', ''))

            return {
                'success': True,
                'type': 'command' if ctype == 'command' else 'chat',
                'requires_action': requires,
                'confidence': max(0.0, min(1.0, conf)),
                'reason': reason
            }
        except Exception as e:
            logger.error(f"Intent classification error: {e}")
            return {
                'success': False,
                'type': 'chat',
                'requires_action': False,
                'confidence': 0.0,
                'reason': str(e)
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
