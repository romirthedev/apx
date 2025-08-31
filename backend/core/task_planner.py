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
            # Step 1: Break down the request into subtasks
            subtasks = self._break_down_request(user_input)
            
            # Step 2: Process each subtask
            results = []
            overall_success = True
            final_response = ""
            
            for subtask in subtasks:
                # Check if this is a web navigation request that needs special handling
                if self._is_web_navigation_request(subtask):
                    result = self._handle_web_navigation_request(subtask, context)
                    result['is_ai_response'] = True
                    result['metadata'] = result.get('metadata', {})
                    result['metadata']['method'] = 'task_planner'
                    results.append(result)
                    continue
                
                # Generate structured tasks from subtask
                ai_response = self.gemini_ai.generate_response(subtask, context)
                
                if not ai_response.get('success', False):
                    results.append({
                        'success': False,
                        'response': f"Failed to process subtask: {subtask}",
                        'error': ai_response.get('error', '')
                    })
                    overall_success = False
                    continue
                
                # Extract structured actions
                actions = ai_response.get('suggested_actions', [])
                response_text = ai_response.get('response', '')
                requires_action = ai_response.get('requires_action', False)
                
                if not requires_action or not actions:
                    results.append({
                        'success': True,
                        'response': response_text,
                        'requires_action': False,
                        'actions_performed': []
                    })
                    continue
            
                # Execute the actions for this subtask
                execution_result = self.command_executor.execute_plan(actions)
                
                # Generate response for this subtask
                subtask_response = self._generate_final_response(response_text, execution_result)
                final_response += subtask_response + "\n"
                
                # Record in task history
                self.task_history.append({
                    'subtask': subtask,
                    'actions': actions,
                    'execution_result': execution_result,
                    'response': subtask_response
                })
                
                # Add execution results to overall results
                results.append({
                    'success': execution_result.get('success', False),
                    'response': subtask_response,
                    'requires_action': True,
                    'actions_performed': execution_result.get('results', []),
                    'execution_time': execution_result.get('total_execution_time', 0)
                })
                
                if not execution_result.get('success', False):
                    overall_success = False
            
            # Return combined results
            return {
                'success': overall_success,
                'response': final_response.strip(),
                'requires_action': True,
                'subtask_results': results,
                'execution_time': sum(r.get('execution_time', 0) for r in results)
            }
            
        except Exception as e:
            logger.error(f"Error processing user request: {str(e)}")
            return {
                'success': False,
                'response': f"I encountered an error while processing your request: {str(e)}",
                'requires_action': False,
                'actions_performed': []
            }
    
    def _is_web_navigation_request(self, user_input: str) -> bool:
        """Check if the user input is a web navigation or web summary request."""
        # Expanded web keywords for robust detection
        web_keywords = [
            'go to', 'visit', 'browse', 'open', 'navigate to', 'check out', 'website', 'site', 'page', 'url', 'link',
            'show', 'list', 'what are', 'trending', 'top', 'latest', 'posts', 'repos', 'summarize', 'summary', 'readme', 'explore', 'search', 'fetch', 'scrape', 'analyze', 'details', 'information', 'overview', 'describe', 'content', 'web', 'internet', 'online', 'data'
        ]
        input_lower = user_input.lower()
        detected = any(keyword in input_lower for keyword in web_keywords)
        if detected:
            logger.info(f"[DEBUG] Detected web/navigation/summary keyword in user input: {user_input}")
        return detected
    
    def _handle_web_navigation_request(self, user_input: str, context: List[Dict] = None) -> Dict[str, Any]:
        """Handle web navigation requests with multi-step AI workflow."""
        try:
            from plugins.web_controller import WebController
            web_controller = WebController()
            user_input_lower = user_input.lower()
            # DEBUG: Log entry and input
            logger.info(f"[DEBUG] Entered _handle_web_navigation_request with input: {user_input_lower}")
            if any(kw in user_input_lower for kw in ['show', 'list', 'what are', 'trending', 'top', 'latest', 'posts', 'repos']):
                # Summary intent
                logger.info(f"[DEBUG] Detected summary intent for: {user_input_lower}")
                if 'github' in user_input_lower:
                    result = web_controller.navigate_within_website('github', 'trending', summary_only=True)
                    logger.info(f"[DEBUG] GitHub summary result: {result}")
                    return {
                        'success': True,
                        'response': result,
                        'requires_action': False,
                        'actions_performed': [{'type': 'web_summary', 'site': 'github', 'section': 'trending'}],
                    }
                elif 'reddit' in user_input_lower:
                    result = web_controller.navigate_within_website('reddit', 'trending', summary_only=True)
                    logger.info(f"[DEBUG] Reddit summary result: {result}")
                    return {
                        'success': True,
                        'response': result,
                        'requires_action': False,
                        'actions_performed': [{'type': 'web_summary', 'site': 'reddit', 'section': 'trending'}],
                    }
                logger.info(f"[DEBUG] No summary fetch implemented for: {user_input_lower}")
            # Otherwise, treat as browse intent
            logger.info(f"[DEBUG] Treating as browse intent for: {user_input_lower}")
            interpretation_prompt = f"""
            The user wants to navigate to: "{user_input}"
            Analyze this request and determine:
            1. What type of website they want to visit
            2. The most appropriate search query to find it
            3. Whether this is a specific site or a general category
            4. What actions need to be performed AFTER opening the website
            Return ONLY the search query, nothing else.
            """
            ai_response = self.gemini_ai.generate_response(
                interpretation_prompt,
                context,
                []
            )
            logger.info(f"[DEBUG] Gemini AI response: {ai_response}")
            if not ai_response.get('success'):
                return {
                    'success': False,
                    'response': f"Failed to interpret web navigation request: {user_input}",
                    'requires_action': False,
                    'actions_performed': []
                }
            search_query = ai_response.get('response', '').strip()
            import re
            site_map = {
                'github': 'https://github.com',
                'python docs': 'https://docs.python.org',
                'python': 'https://python.org',
                'linux': 'https://linux.org',
                'stack overflow': 'https://stackoverflow.com',
                'apple': 'https://apple.com',
                'microsoft': 'https://microsoft.com',
                'google': 'https://google.com',
                'techcrunch': 'https://techcrunch.com',
                'yelp': 'https://yelp.com'
            }
            site_key = search_query.lower().replace(' official website', '').strip()
            url_pattern = r"^(https?://)?([\w.-]+)\.[a-z]{2,}"
            if site_key in site_map:
                url = site_map[site_key]
                result = web_controller.browse_url(url)
                final_response = f"Opened site: {url} based on your request: '{user_input}'\n{result}"
                logger.info(f"[DEBUG] Browse result: {final_response}")
                self.task_history.append({
                    'user_input': user_input,
                    'actions': [{'type': 'web_browse', 'url': url}],
                    'execution_result': result,
                    'final_response': final_response
                })
                return {
                    'success': True,
                    'response': final_response,
                    'requires_action': True,
                    'actions_performed': [{'type': 'web_browse', 'url': url}],
                }
            if re.match(url_pattern, search_query):
                if not search_query.startswith(('http://', 'https://')):
                    search_query = 'https://' + search_query
                result = web_controller.browse_url(search_query)
                final_response = f"Opened site: {search_query} based on your request: '{user_input}'\n{result}"
                logger.info(f"[DEBUG] Browse result: {final_response}")
                self.task_history.append({
                    'user_input': user_input,
                    'actions': [{'type': 'web_browse', 'url': search_query}],
                    'execution_result': result,
                    'final_response': final_response
                })
                return {
                    'success': True,
                    'response': final_response,
                    'requires_action': True,
                    'actions_performed': [{'type': 'web_browse', 'url': search_query}],
                }
            if site_key not in site_map and not re.match(url_pattern, search_query):
                # Use the new AI-powered URL resolution method
                result = web_controller.resolve_and_open_url(user_input, self.gemini_ai)
                final_response = f"Resolved and opened site for '{user_input}' based on your request: '{user_input}'\n{result}"
                logger.info(f"[DEBUG] AI URL resolution result: {final_response}")
                self.task_history.append({
                    'user_input': user_input,
                    'actions': [{'type': 'web_browse', 'url': user_input}],
                    'execution_result': result,
                    'final_response': final_response
                })
                return {
                    'success': True,
                    'response': final_response,
                    'requires_action': True,
                    'actions_performed': [{'type': 'web_browse', 'url': user_input}],
                }
            # Fallback: perform a web search
            actions = [
                {
                    'type': 'web_search',
                    'description': f"Search for {search_query}",
                    'parameters': {
                        'query': search_query,
                        'engine': 'google'
                    }
                }
            ]
            execution_result = self.command_executor.execute_plan(actions)
            logger.info(f"[DEBUG] Fallback web search result: {execution_result}")
            if execution_result.get('success'):
                return {
                    'success': True,
                    'response': execution_result.get('response', ''),
                    'requires_action': True,
                    'actions_performed': actions
                }
            return {
                'success': False,
                'response': f"Could not process web navigation request: {user_input}",
                'requires_action': False,
                'actions_performed': []
            }
        except Exception as e:
            logger.error(f"Error handling web navigation request: {str(e)}")
            return {
                'success': False,
                'response': f"Error processing web navigation request: {str(e)}",
                'requires_action': False,
                'actions_performed': []
            }
    
    def _handle_multi_step_web_request(self, user_input: str, context: List[Dict] = None) -> Dict[str, Any]:
        """Handle complex multi-step web navigation requests."""
        try:
            # Step 1: AI analysis to break down the multi-step task
            analysis_prompt = f"""
            The user wants to: "{user_input}"
            
            This is a complex web navigation task that requires multiple steps. Break it down:
            
            1. What website needs to be opened first?
            2. What specific section or page needs to be navigated to?
            3. What actions need to be performed on that page?
            4. What is the final goal?
            
            Examples:
            - "open the most popular repository on github" →
              Step 1: Open github.com
              Step 2: Navigate to trending repositories section
              Step 3: Find the repository with highest stars/activity
              Step 4: Open that specific repository
            
            - "show me the trending repositories on github" →
              Step 1: Open github.com
              Step 2: Navigate to trending repositories section
              Step 3: Display the trending repositories list
            
            - "find the best restaurants on yelp" →
              Step 1: Open yelp.com
              Step 2: Navigate to restaurant search
              Step 3: Apply best rating filter
            
            IMPORTANT: You MUST respond with ONLY valid JSON in this exact format:
            {{
                "website": "main website to open",
                "steps": [
                    {{"action": "open_site", "description": "Open the main website"}},
                    {{"action": "navigate_section", "description": "Navigate to specific section"}},
                    {{"action": "perform_action", "description": "Perform specific action"}}
                ],
                "final_goal": "what the user will see/achieve"
            }}
            
            Do not include any other text, only the JSON.
            """
            
            ai_response = self.gemini_ai.generate_response(
                analysis_prompt,
                context,
                []
            )
            
            if not ai_response.get('success'):
                return {
                    'success': False,
                    'response': f"Failed to analyze multi-step request: {user_input}",
                    'requires_action': False,
                    'actions_performed': []
                }
            
            # Try to extract the JSON plan
            response_text = ai_response.get('response', '')
            import re
            import json
            
            # Look for JSON in the response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    plan = json.loads(json_match.group(0))
                    
                    # Step 2: Execute the multi-step plan using enhanced web controller
                    try:
                        # Import web controller to use enhanced navigation
                        from plugins.web_controller import WebController
                        web_controller = WebController()
                        
                        # Execute the multi-step navigation plan
                        result = web_controller.execute_multi_step_navigation(plan)
                        
                        final_response = f"""🚀 **Multi-Step Task Completed!**

**Request:** {user_input}

**What I did:**
{result}

**Final Goal:** {plan.get('final_goal', 'Task completed successfully')}

**Note:** I've opened the main website and navigated to the appropriate sections. The system is now ready for you to complete any remaining manual steps."""
                        
                        # Record in task history
                        self.task_history.append({
                            'user_input': user_input,
                            'actions': [{'type': 'multi_step_navigation', 'plan': plan}],
                            'execution_result': {'success': True, 'result': result},
                            'final_response': final_response
                        })
                        
                        return {
                            'success': True,
                            'response': final_response,
                            'requires_action': True,
                            'actions_performed': [{'type': 'multi_step_navigation', 'result': result}],
                            'execution_time': 0
                        }
                        
                    except Exception as e:
                        logger.error(f"Failed to execute multi-step navigation: {str(e)}")
                        # Fall back to web search approach
                        actions = [
                            {
                                'type': 'web_search',
                                'description': f"Open {plan.get('website', 'the requested website')}",
                                'parameters': {
                                    'query': f"{plan.get('website', '')} official website",
                                    'engine': 'google'
                                }
                            }
                        ]
                        
                        execution_result = self.command_executor.execute_plan(actions)
                        
                        final_response = f"""🚀 **Multi-Step Task Started!**

**Request:** {user_input}

**What I did:**
1. ✅ Opened {plan.get('website', 'the requested website')}

**Next Steps:** {plan.get('final_goal', 'Navigate to the appropriate sections manually')}

**Note:** I've opened the main website. You can now navigate to the specific sections you need."""
                        
                        return {
                            'success': execution_result.get('success', False),
                            'response': final_response,
                            'requires_action': True,
                            'actions_performed': execution_result.get('results', []),
                            'execution_time': execution_result.get('total_execution_time', 0)
                        }
                    
                except json.JSONDecodeError:
                    logger.warning("Failed to parse JSON plan from AI response")
            
            # Fallback: Generate a manual plan based on common patterns
            logger.info("AI didn't generate proper JSON, creating manual plan")
            manual_plan = self._create_manual_plan(user_input)
            
            if manual_plan:
                try:
                    # Import web controller to use enhanced navigation
                    from plugins.web_controller import WebController
                    web_controller = WebController()
                    
                    # Execute the manual plan
                    result = web_controller.execute_multi_step_navigation(manual_plan)
                    
                    final_response = f"""🚀 **Multi-Step Task Completed!**

**Request:** {user_input}

**What I did:**
{result}

**Final Goal:** {manual_plan.get('final_goal', 'Task completed successfully')}

**Note:** I've opened the main website and navigated to the appropriate sections. The system is now ready for you to complete any remaining manual steps."""
                    
                    return {
                        'success': True,
                        'response': final_response,
                        'requires_action': True,
                        'actions_performed': [{'type': 'manual_navigation', 'result': result}],
                        'execution_time': 0
                    }
                    
                except Exception as e:
                    logger.error(f"Failed to execute manual plan: {str(e)}")
            
            # Final fallback: execute as simple web search
            actions = [
                {
                    'type': 'web_search',
                    'description': f"Search for {user_input}",
                    'parameters': {
                        'query': user_input,
                        'engine': 'google'
                    }
                }
            ]
            
            execution_result = self.command_executor.execute_plan(actions)
            
            final_response = f"Navigated to web search for '{user_input}' (fallback mode)"
            
            return {
                'success': execution_result.get('success', False),
                'response': final_response,
                'requires_action': True,
                'actions_performed': execution_result.get('results', []),
                'execution_time': execution_result.get('total_execution_time', 0)
            }
            
        except Exception as e:
            logger.error(f"Error handling multi-step web request: {str(e)}")
            return {
                'success': False,
                'response': f"Error processing multi-step request: {str(e)}",
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

    def _create_manual_plan(self, user_input: str) -> dict:
        """Create a manual plan based on common patterns when AI fails."""
        input_lower = user_input.lower()
        
        # GitHub patterns
        if 'github' in input_lower:
            if any(keyword in input_lower for keyword in ['trending', 'most popular', 'top repositories']):
                return {
                    'website': 'github',
                    'steps': [
                        {'action': 'open_site', 'description': 'Open GitHub.com'},
                        {'action': 'navigate_section', 'description': 'Navigate to trending repositories'},
                        {'action': 'perform_action', 'description': 'Display trending repositories list'}
                    ],
                    'final_goal': 'Show trending repositories on GitHub'
                }
            elif 'repository' in input_lower:
                return {
                    'website': 'github',
                    'steps': [
                        {'action': 'open_site', 'description': 'Open GitHub.com'},
                        {'action': 'navigate_section', 'description': 'Navigate to explore section'},
                        {'action': 'perform_action', 'description': 'Find and display repositories'}
                    ],
                    'final_goal': 'Show repositories on GitHub'
                }
        
        # YouTube patterns
        elif 'youtube' in input_lower:
            if any(keyword in input_lower for keyword in ['trending', 'most popular', 'latest']):
                return {
                    'website': 'youtube',
                    'steps': [
                        {'action': 'open_site', 'description': 'Open YouTube.com'},
                        {'action': 'navigate_section', 'description': 'Navigate to trending section'},
                        {'action': 'perform_action', 'description': 'Display trending videos'}
                    ],
                    'final_goal': 'Show trending videos on YouTube'
                }
        
        # Reddit patterns
        elif 'reddit' in input_lower:
            if any(keyword in input_lower for keyword in ['trending', 'most popular', 'top posts']):
                return {
                    'website': 'reddit',
                    'steps': [
                        {'action': 'open_site', 'description': 'Open Reddit.com'},
                        {'action': 'navigate_section', 'description': 'Navigate to popular section'},
                        {'action': 'perform_action', 'description': 'Display popular posts'}
                    ],
                    'final_goal': 'Show popular posts on Reddit'
                }
        
        # TechCrunch patterns
        elif 'techcrunch' in input_lower:
            if any(keyword in input_lower for keyword in ['latest', 'breaking', 'top stories']):
                return {
                    'website': 'techcrunch',
                    'steps': [
                        {'action': 'open_site', 'description': 'Open TechCrunch.com'},
                        {'action': 'navigate_section', 'description': 'Navigate to latest news'},
                        {'action': 'perform_action', 'description': 'Display latest articles'}
                    ],
                    'final_goal': 'Show latest news on TechCrunch'
                }
        
        return None
