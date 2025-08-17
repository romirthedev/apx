"""Task Planner Module - Three-layer architecture for AI-powered system automation."""
import logging
import json
from typing import Dict, List, Any, Optional, Callable
from core.gemini_ai import GeminiAI

logger = logging.getLogger(__name__)

class TaskPlannerManager:
    """Manages the three-layer architecture for AI-powered system automation."""
    
    def __init__(
        self,
        gemini_ai: GeminiAI,
        sandbox_mode: bool = True,
        web_browse_handler: Optional[Callable[[str, List[Dict]], str]] = None,
    ):
        """Initialize the TaskPlannerManager.

        Args:
            gemini_ai: Gemini AI client instance.
            sandbox_mode: If True, restricts side effects (future use).
            web_browse_handler: Optional delegate to handle web navigation requests.
                When provided, ALL web navigation will be routed through this handler
                (e.g., CommandProcessor._handle_browse_url) to ensure consistent,
                validated URL resolution.
        """
        self.gemini_ai = gemini_ai
        self.sandbox_mode = sandbox_mode
        self.task_history = []
        self.web_browse_handler = web_browse_handler
        logger.info("Task Planner Manager initialized successfully")
    
    def _is_web_navigation_request(self, user_input: str) -> bool:
        """Check if the user input is a web navigation request."""
        web_keywords = [
            'go to', 'visit', 'browse', 'open', 'navigate to', 'check out',
            'website', 'site', 'page', 'url', 'link', 'search for', 'look up',
            'reddit', 'youtube', 'github', 'google', 'facebook', 'twitter',
            'amazon', 'wikipedia', 'stack overflow', 'netflix', 'spotify',
            'show me', 'take me to'
        ]
        input_lower = user_input.lower()
        return any(keyword in input_lower for keyword in web_keywords)
    
    def _handle_web_navigation_request(self, user_input: str, context: List[Dict] = None) -> Dict[str, Any]:
        """Handle web navigation requests with AI assistance."""
        try:
            import re
            logger.info(f"[DEBUG] Handling web navigation request: {user_input}")
            
            # Always delegate to the main CommandProcessor's URL handler when available
            # to avoid naive domain guessing like appending ".com" to arbitrary tokens.
            if self.web_browse_handler:
                result_str = self.web_browse_handler(user_input, context or [])
                return {
                    'success': True,
                    'result': result_str,
                    'metadata': {
                        'method': 'command_processor_browse',
                        'actions_performed': [{'type': 'web_browse', 'target': user_input}]
                    }
                }
            
            # Fallback (should not be used if web_browse_handler is provided):
            from plugins.web_controller import WebController
            web_controller = WebController()
            
            # Simple direct URL handling first
            if user_input.startswith(('http://', 'https://')):
                result = web_controller.browse_url(user_input)
                return {
                    'success': True,
                    'result': result,
                    'metadata': {
                        'method': 'direct_url',
                        'actions_performed': [{'type': 'web_browse', 'url': user_input}]
                    }
                }
            
            # For other cases, AVOID naive domain construction like appending ".com".
            # Use a safe generic web search so the user can pick the correct result.
            search_result = web_controller.search_web(user_input)
            return {
                'success': True,
                'result': search_result,
                'metadata': {
                    'method': 'safe_search_fallback',
                    'actions_performed': [{'type': 'web_search', 'query': user_input}]
                }
            }
            
            # If we get here, we couldn't handle the request
            return {
                'success': False,
                'result': "I couldn't understand which website you want to visit. Please try being more specific.",
                'metadata': {'method': 'error'}
            }
            
        except Exception as e:
            logger.error(f"[DEBUG] Error in web navigation handler: {str(e)}")
            return {
                'success': False,
                'result': f"❌ Error processing web navigation request: {str(e)}",
                'metadata': {
                    'method': 'error',
                    'error': str(e)
                }
            }
    
    def process_user_request(self, user_input: str, context: List[Dict] = None) -> Dict[str, Any]:
        """Process a user's natural language request."""
        try:
            # Check if this is a web navigation request
            if self._is_web_navigation_request(user_input):
                return self._handle_web_navigation_request(user_input, context)
                
            # Other request types would be handled here
            
            return {
                'success': False,
                'result': "I'm not sure how to handle that request yet.",
                'metadata': {'method': 'unknown'}
            }
            
        except Exception as e:
            logger.error(f"Error processing user request: {str(e)}")
            return {
                'success': False,
                'result': f"An error occurred: {str(e)}",
                'metadata': {'method': 'error'}
            }
