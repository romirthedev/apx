"""
Voice Command Processor for Apex AI Assistant.

Processes classified voice commands and generates appropriate responses
by integrating with existing backend systems.
"""

import logging
import asyncio
from typing import Dict, Any, Optional
import sys
import os

# Add the backend directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

class VoiceProcessor:
    """Processes classified voice commands and generates responses."""
    
    def __init__(self):
        self.command_executor = None
        self.gemini_ai = None
        self._initialize_components()
        logger.info("VoiceProcessor initialized")
    
    def _initialize_components(self):
        """Initialize backend components for processing."""
        try:
            # Import existing backend components
            from core.command_executor import CommandExecutor
            from core.gemini_ai import GeminiAI
            from utils.config import Config
            
            self.command_executor = CommandExecutor()
            
            # Initialize GeminiAI with proper API key
            config = Config()
            gemini_api_key = config.get('apis.gemini.api_key')
            gemini_enabled = config.get('apis.gemini.enabled', True)
            
            if gemini_api_key and gemini_enabled:
                self.gemini_ai = GeminiAI(gemini_api_key)
                logger.info("GeminiAI initialized successfully for voice processing")
            else:
                logger.warning("GeminiAI disabled or missing API key for voice processing")
                self.gemini_ai = None
            
            logger.info("Backend components initialized successfully")
        except ImportError as e:
            logger.warning(f"Could not import backend components: {e}")
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
    
    async def process(self, text: str, classification: Dict[str, Any]) -> Optional[str]:
        """
        Process a classified voice command and return a response.
        
        Args:
            text: The original voice input text
            classification: Classification result from VoiceClassifier
            
        Returns:
            Response text to be spoken back to the user
        """
        command_type = classification['type']
        confidence = classification['confidence']
        
        logger.info(f"Processing {command_type} command: '{text}' (confidence: {confidence:.2f})")
        
        try:
            if command_type == 'action':
                return await self._process_action_command(text, classification)
            elif command_type == 'web_search':
                return await self._process_search_command(text, classification)
            elif command_type == 'chat':
                return await self._process_chat_command(text, classification)
            else:
                return "I'm not sure how to handle that request."
                
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            return "I encountered an error while processing your request. Please try again."
    
    async def _process_action_command(self, text: str, classification: Dict[str, Any]) -> str:
        """Process action commands (file operations, app control, etc.)."""
        category = classification.get('category', 'general')
        
        logger.info(f"Processing action command in category: {category}")
        
        # Use existing command executor if available
        if self.command_executor:
            try:
                # Convert voice command to action format
                action_data = self._convert_to_action_format(text, category)
                
                # Execute the action
                result = await self._execute_action(action_data)
                
                if result and result.get('success'):
                    return self._format_action_response(result, text)
                else:
                    error_msg = result.get('error', 'Unknown error') if result else 'No result'
                    return f"I couldn't complete that action. {error_msg}"
                    
            except Exception as e:
                logger.error(f"Error executing action: {e}")
                return "I encountered an error while trying to perform that action."
        
        # Fallback responses based on category
        return self._get_fallback_action_response(category, text)
    
    async def _process_search_command(self, text: str, classification: Dict[str, Any]) -> str:
        """Process web search commands."""
        logger.info("Processing web search command")
        
        # Extract search query from the text
        search_query = self._extract_search_query(text)
        
        if self.command_executor:
            try:
                # Use existing web search functionality
                search_data = {
                    'action_type': 'web_search',
                    'query': search_query,
                    'max_results': 3
                }
                
                result = await self._execute_action(search_data)
                
                if result and result.get('success'):
                    return self._format_search_response(result, search_query)
                else:
                    return f"I couldn't find information about {search_query}. Please try rephrasing your question."
                    
            except Exception as e:
                logger.error(f"Error executing search: {e}")
                return "I encountered an error while searching. Please try again."
        
        return f"I would search for '{search_query}' but the search functionality is not available right now."
    
    async def _process_chat_command(self, text: str, classification: Dict[str, Any]) -> str:
        """Process general chat/conversation commands."""
        logger.info("Processing chat command")
        
        # Use Gemini AI for general conversation if available
        if self.gemini_ai:
            try:
                # Create a conversational prompt
                prompt = f"Respond conversationally to this user message: {text}"
                
                response = await self._get_ai_response(prompt)
                
                if response:
                    return response
                    
            except Exception as e:
                logger.error(f"Error getting AI response: {e}")
        
        # Fallback conversational responses
        return self._get_fallback_chat_response(text)
    
    def _convert_to_action_format(self, text: str, category: str) -> Dict[str, Any]:
        """Convert voice command to action format for the command executor."""
        # This is a simplified conversion - could be enhanced with more sophisticated parsing
        
        if category == 'file_operations':
            if 'screenshot' in text.lower():
                return {'action_type': 'screenshot'}
            elif 'open' in text.lower():
                # Try to extract filename/app name
                words = text.lower().split()
                if 'open' in words:
                    idx = words.index('open')
                    if idx + 1 < len(words):
                        target = words[idx + 1]
                        return {'action_type': 'open_file', 'target': target}
        
        elif category == 'app_control':
            if any(word in text.lower() for word in ['launch', 'start', 'open']):
                # Extract app name
                words = text.lower().split()
                for trigger in ['launch', 'start', 'open']:
                    if trigger in words:
                        idx = words.index(trigger)
                        if idx + 1 < len(words):
                            app_name = words[idx + 1]
                            return {'action_type': 'launch_app', 'app_name': app_name}
        
        # Default action format
        return {
            'action_type': 'general_action',
            'command': text,
            'category': category
        }
    
    async def _execute_action(self, action_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Execute an action using the command executor."""
        if not self.command_executor:
            return None
        
        try:
            # This would integrate with the existing command executor
            # For now, we'll simulate the execution
            action_type = action_data.get('action_type')
            
            if action_type == 'screenshot':
                return {'success': True, 'message': 'Screenshot taken successfully'}
            elif action_type == 'web_search':
                # Simulate web search
                query = action_data.get('query', '')
                return {
                    'success': True,
                    'results': [
                        {'title': f'Search result for {query}', 'snippet': f'Information about {query}'}
                    ]
                }
            else:
                return {'success': False, 'error': 'Action type not supported yet'}
                
        except Exception as e:
            logger.error(f"Error executing action: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _get_ai_response(self, prompt: str) -> Optional[str]:
        """Get AI response for chat commands."""
        if not self.gemini_ai:
            return None
        
        try:
            # This would integrate with the existing Gemini AI
            # For now, we'll provide a simple response
            return "I'm here to help! What would you like to know or do?"
        except Exception as e:
            logger.error(f"Error getting AI response: {e}")
            return None
    
    def _extract_search_query(self, text: str) -> str:
        """Extract the actual search query from voice input."""
        # Remove common search prefixes
        prefixes = [
            'search for', 'look up', 'find', 'google', 'what is', 'who is',
            'tell me about', 'information about', 'how to', 'when did', 'where is'
        ]
        
        text_lower = text.lower()
        for prefix in prefixes:
            if text_lower.startswith(prefix):
                return text[len(prefix):].strip()
        
        # If no prefix found, return the whole text
        return text.strip()
    
    def _format_action_response(self, result: Dict[str, Any], original_text: str) -> str:
        """Format the response for action commands."""
        if result.get('success'):
            message = result.get('message', 'Action completed successfully')
            return f"Done! {message}"
        else:
            error = result.get('error', 'Unknown error')
            return f"I couldn't complete that action. {error}"
    
    def _format_search_response(self, result: Dict[str, Any], query: str) -> str:
        """Format the response for search commands."""
        if result.get('success') and result.get('results'):
            results = result['results']
            if results:
                first_result = results[0]
                title = first_result.get('title', '')
                snippet = first_result.get('snippet', '')
                return f"I found information about {query}. {snippet}"
        
        return f"I couldn't find specific information about {query}."
    
    def _get_fallback_action_response(self, category: str, text: str) -> str:
        """Get fallback response for action commands when executor is not available."""
        responses = {
            'file_operations': "I would help you with that file operation, but I need additional permissions.",
            'app_control': "I would launch that application for you, but the app control system is not available.",
            'system_control': "I would adjust that system setting, but I need system access.",
            'automation': "I would run that automation for you, but the automation system is not ready."
        }
        
        return responses.get(category, "I understand you want me to perform an action, but I'm not able to do that right now.")
    
    def _get_fallback_chat_response(self, text: str) -> str:
        """Get fallback response for chat commands when AI is not available."""
        text_lower = text.lower()
        
        if any(greeting in text_lower for greeting in ['hello', 'hi', 'hey']):
            return "Hello! I'm your voice assistant. How can I help you today?"
        elif any(thanks in text_lower for thanks in ['thank', 'thanks']):
            return "You're welcome! Is there anything else I can help you with?"
        elif 'how are you' in text_lower:
            return "I'm doing well and ready to help! What can I do for you?"
        else:
            return "I'm here to help! You can ask me to search for information, perform actions, or just chat."