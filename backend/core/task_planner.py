import logging
from typing import Dict, Any, List
from .command_executor import CommandExecutor
from .gemini_ai import GeminiAI

logger = logging.getLogger(__name__)

class TaskPlannerManager:
    """
    Manages the three-layer architecture for AI-powered system automation:
    1. AI Planner (User Input → Structured Tasks)
    2. Local Agent (JSON Instructions → Executable Commands)
    3. OS Execution (Execute Commands → Collect Feedback)
    """
    
    def __init__(self, gemini_ai: GeminiAI, sandbox_mode: bool = True):
        """Initialize the TaskPlannerManager.
        
        Args:
            gemini_ai: Instance of GeminiAI for planning
            sandbox_mode: Whether to run in sandbox mode for safety
        """
        self.gemini_ai = gemini_ai
        self.command_executor = CommandExecutor(sandbox_mode=sandbox_mode)
        self.task_history = []
        self.last_plan = None
        self.last_result = None
    
    def process_user_request(self, user_input: str, context: List[Dict] = None) -> Dict[str, Any]:
        """Process a user's natural language request through the three-layer architecture.
        
        Args:
            user_input: The natural language request from the user
            context: Optional conversation context
            
        Returns:
            Dictionary with response and execution results
        """
        try:
            # Step 1: AI Planner - Generate structured tasks from user input
            ai_response = self.gemini_ai.generate_response(user_input, context)
            
            # Check if the response was successful and requires action
            if not ai_response.get('success', False):
                return {
                    'success': False,
                    'response': "Failed to generate a response to your request",
                    'error': ai_response.get('error', '')
                }
            
            # Extract structured actions
            actions = ai_response.get('suggested_actions', [])
            response_text = ai_response.get('response', '')
            requires_action = ai_response.get('requires_action', False)
            
            if not requires_action or not actions:
                # No actions needed, just return the conversational response
                return {
                    'success': True,
                    'response': response_text,
                    'requires_action': False,
                    'actions_performed': []
                }
            
            # Step 2: Local Agent → OS - Execute the actions
            execution_result = self.command_executor.execute_plan(actions)
            self.last_plan = actions
            self.last_result = execution_result
            
            # Step 3: Generate the final response combining AI response and execution results
            final_response = self._generate_final_response(response_text, execution_result)
            
            # Record in task history
            self.task_history.append({
                'user_input': user_input,
                'actions': actions,
                'execution_result': execution_result,
                'final_response': final_response
            })
            
            # Enhance results with action type information
            results = execution_result.get('results', [])
            for i, result in enumerate(results):
                # If action_type is not set in the result, get it from the original actions
                if not result.get('action_type') and i < len(actions):
                    result['action_type'] = actions[i].get('type', 'unknown')
            
            return {
                'success': execution_result.get('success', False),
                'response': final_response,
                'requires_action': True,
                'actions_performed': results,
                'execution_time': execution_result.get('total_execution_time', 0)
            }
            
        except Exception as e:
            logger.error(f"Error processing user request: {str(e)}")
            return {
                'success': False,
                'response': f"I encountered an error while processing your request: {str(e)}",
                'requires_action': False,
                'actions_performed': []
            }
    
    def _generate_final_response(self, ai_response: str, execution_result: Dict[str, Any]) -> str:
        """Generate a final response combining AI planning and execution results.
        
        Args:
            ai_response: Original AI response text
            execution_result: Results from command execution
            
        Returns:
            Formatted final response
        """
        # If execution failed, include error information
        if not execution_result.get('success', False):
            failed_actions = [r for r in execution_result.get('results', []) if not r.get('success', False)]
            if failed_actions:
                error_messages = [f"{r.get('action_type', 'Action')}: {r.get('error', 'Unknown error')}" 
                                 for r in failed_actions]
                error_summary = "\n".join(error_messages)
                return f"Task failed: {error_summary}"
        
        # For successful execution, return original stripped AI response or execution output
        successful_results = [r['output'] for r in execution_result.get('results', []) 
                             if r.get('success', True) and r.get('output')]
        
        if successful_results:
            return "\n".join(successful_results)
        
        # Fall back to the original AI response if no better output is available
        return ai_response
    
    def execute_custom_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single custom action directly.
        
        Args:
            action: Dictionary with action details
            
        Returns:
            Dictionary with execution results
        """
        return self.command_executor.execute_action(action)
