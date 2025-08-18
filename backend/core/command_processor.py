import re
import json
import logging
import urllib.parse
from typing import Dict, List, Any, Optional
from datetime import datetime

from plugins.file_manager import FileManager
from plugins.app_controller import AppController
from plugins.web_controller import WebController
from plugins.script_runner import ScriptRunner
from plugins.system_info import SystemInfo
from plugins.document_manager import DocumentManager
from plugins.email_manager import EmailManager
from plugins.automation_manager import AutomationManager
from core.nlp_processor import NLPProcessor
from core.gemini_ai import GeminiAI
from core.macos_permissions import MacOSPermissionsManager
from core.macos_controller import MacOSSystemController

logger = logging.getLogger(__name__)

class CommandProcessor:
    def __init__(self, security_manager, action_logger):
        self.security_manager = security_manager
        self.action_logger = action_logger
        self.nlp_processor = NLPProcessor()
        
        # Initialize Gemini AI
        from utils.config import Config
        config = Config()
        gemini_api_key = config.get('apis.gemini.api_key')
        gemini_enabled = config.get('apis.gemini.enabled', True)
        
        self.gemini_ai = None
        if gemini_api_key and gemini_enabled:
            try:
                self.gemini_ai = GeminiAI(gemini_api_key)
                logger.info("Gemini AI initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini AI: {str(e)}")
                self.gemini_ai = None
        
        # Initialize plugins
        self.plugins = {
            'file_manager': FileManager(),
            'app_controller': AppController(),
            'web_controller': WebController(),
            'script_runner': ScriptRunner(),
            'system_info': SystemInfo(),
            'document_manager': DocumentManager(),
            'email_manager': EmailManager(),
            'automation_manager': AutomationManager()
        }
        
        # Initialize macOS-specific components
        import platform
        if platform.system().lower() == "darwin":
            self.permissions_manager = MacOSPermissionsManager()
            self.system_controller = MacOSSystemController()
        else:
            self.permissions_manager = None
            self.system_controller = None
        
        # Command patterns and their handlers
        self.command_patterns = [
            # System info (check these first)
            (r'(?:what|which)\s+(?:is\s+)?(?:my\s+)?(?:operating\s+)?(?:system|os)(?:\s+am\s+i\s+(?:running|using))?', self._handle_operating_system),
            (r'(?:show|get|display)\s+(?:system\s+)?(?:info|information|status)', self._handle_system_info),
            (r'(?:what\s+time|time|clock)', self._handle_time),
            (r'(?:weather|temperature)', self._handle_weather),
            (r'(?:show|list)\s+(?:running\s+)?processes', self._handle_running_processes),
            (r'(?:what|which)\s+(?:app|application|program)s?\s+(?:take|use|consume)s?\s+(?:the\s+)?most\s+(?:space|disk|storage)', self._handle_largest_apps),
            (r'(?:find|show|get)\s+(?:the\s+)?largest\s+file(?:s?)\s*(?:on\s+(?:my\s+)?computer|in\s+system)?', self._handle_find_largest_file),
            (r'(?:find|show|get)\s+(?:the\s+)?smallest\s+file(?:s?)\s*(?:on\s+(?:my\s+)?computer|in\s+system)?', self._handle_find_smallest_file),
            (r'(?:show|analyze|check)\s+(?:disk\s+)?(?:usage|space)', self._handle_disk_usage),
            
            # macOS System Control
            (r'(?:check|show)\s+(?:system\s+)?permissions', self._handle_check_permissions),
            (r'(?:request|grant|setup)\s+permissions', self._handle_request_permissions),
            (r'(?:open|show)\s+(?:system\s+)?(?:settings|preferences)', self._handle_open_system_settings),
            (r'(?:click|tap)\s+(?:at\s+)?(?:coordinates\s+)?(\d+)\s*,?\s*(\d+)', self._handle_click_coordinates),
            (r'(?:type|enter)\s+(?:text\s+)?["\'](.+)["\']', self._handle_type_text),
            (r'(?:press|hit)\s+(?:key\s+)?(.+)', self._handle_press_keys),
            (r'(?:take|capture)\s+(?:a\s+)?screenshot', self._handle_screenshot),
            (r'(?:control|manage)\s+window\s+(.+)', self._handle_window_control),
            
            # Document creation
            (r'(?:create|make|new)\s+(?:word\s+)?(?:document|doc)\s+(.+)', self._handle_create_word_doc),
            (r'(?:create|make|new)\s+(?:excel\s+)?(?:spreadsheet|sheet)\s+(.+)', self._handle_create_excel),
            (r'(?:create|make|new)\s+(?:powerpoint\s+)?(?:presentation|ppt)\s+(.+)', self._handle_create_presentation),
            (r'(?:create|make|new)\s+pdf\s+(.+)', self._handle_create_pdf),
            
            # Email operations
            (r'(?:compose|write|send)\s+(?:email|mail)\s+(?:to\s+)?(.+)', self._handle_compose_email),
            (r'(?:create|send)\s+(?:meeting\s+)?(?:invite|invitation)\s+(.+)', self._handle_create_meeting),
            (r'(?:check|show)\s+(?:calendar|schedule)\s*(?:for\s+)?(.+)?', self._handle_check_calendar),
            (r'(?:switch|change)\s+google\s+account\s*(?:to\s+)?(.+)?', self._handle_switch_google_account),
            (r'(?:open|show)\s+gmail\s*(?:for\s+)?(.+)?', self._handle_open_gmail),
            
            # Automation
            (r'(?:organize|clean\s+up)\s+downloads', self._handle_organize_downloads),
            (r'(?:create|run)\s+(?:daily\s+)?report', self._handle_create_daily_report),
            (r'(?:backup|save)\s+(?:important\s+)?(?:files|folders)', self._handle_backup_files),
            (r'(?:clean|clear)\s+(?:temp|temporary)\s+files', self._handle_clean_temp),
            (r'(?:list|show)\s+workflows', self._handle_list_workflows),
            (r'(?:run|execute)\s+workflow\s+(.+)', self._handle_run_workflow),
            
            # General queries
            (r'(?:help|what\s+can\s+you\s+do)', self._handle_help),

            # Web operations (placed BEFORE generic file/app open handlers)
            # Open explicit URLs like "open https://..." or "open www.example.com"
            (r'(?:open)\s+((?:https?://|www\.)[^\s]+)', self._handle_browse_url),
            # Common site intents like "open reddit ..." get routed to web browse
            # Capture the full target phrase (site plus any trailing query)
            (r'(?:open)\s+((?:reddit|hacker\s*news|hn|youtube|twitter|x|github|stackoverflow|stack\s*overflow|gmail|google|bing|amazon|linkedin)(?:\s+.+)?)', self._handle_web_browse),
            (r'(?:search\s+(?:web|google|internet)\s+(?:for\s+)?|google\s+)(.+)', self._handle_web_search),
            (r'(?:browse|visit|go\s+to)\s+(.+)', self._handle_browse_url),
            (r'(?:download|get)\s+(.+)', self._handle_download),

            # File operations
            (r'(?:open|show|display)\s+(.+)', self._handle_open_file),
            (r'(?:create|make|new)\s+(?:file|folder|directory)\s+(.+)', self._handle_create),
            (r'(?:delete|remove|rm)\s+(.+)', self._handle_delete),
            (r'(?:find|search)\s+(?:for\s+)?(.+)', self._handle_search),
            (r'(?:copy|cp)\s+(.+)\s+(?:to\s+)?(.+)', self._handle_copy),
            (r'(?:move|mv)\s+(.+)\s+(?:to\s+)?(.+)', self._handle_move),
            (r'(?:edit|modify)\s+(.+)', self._handle_edit_file),
            
            # App control
            (r'(?:launch|start|open|run)\s+(.+)', self._handle_launch_app),
            (r'(?:close|quit|exit)\s+(.+)', self._handle_close_app),
            (r'(?:switch\s+to|focus\s+on)\s+(.+)', self._handle_switch_app),
            
            # Script execution
            (r'(?:run|execute)\s+(?:script\s+)?(.+)', self._handle_run_script),
            (r'(?:python|py)\s+(.+)', self._handle_run_python),
            (r'(?:bash|sh)\s+(.+)', self._handle_run_bash),
        ]
    
    def process(self, command: str, context: List[Dict] = None) -> Dict[str, Any]:
        """Process a natural language command and return the result."""
        try:
            original_command = command
            command = command.strip().lower()
            context = context or []
            
            logger.info(f"Processing command: {command}")
            
            # Security validation
            security_result = self.security_manager.validate_command_execution(original_command)
            
            if not security_result.get('allowed', False):
                return {
                    'success': False,
                    'result': f"Command blocked: {security_result.get('reason', 'Security validation failed')}",
                    'metadata': {'security_blocked': True}
                }
            
            # Check if command needs user confirmation (only for extremely dangerous commands)
            if security_result.get('needs_confirmation', False) and not security_result.get('auto_execute', True):
                return {
                    'success': True,
                    'needs_confirmation': True,
                    'confirmation_message': f"⚠️ DANGER: Execute extremely dangerous command?",
                    'confirmation_reason': security_result.get('confirmation_reason', ''),
                    'warnings': security_result.get('warnings', []),
                    'cache_key': security_result.get('cache_key', ''),
                    'original_command': original_command,
                    'metadata': {
                        'risk_level': security_result['risk_level'],
                        'pending_execution': True
                    }
                }
            
            # Proceed with execution (either auto-execute or already confirmed)
            return self._execute_command(original_command, context, security_result)
            
        except Exception as e:
            logger.error(f"Error processing command: {str(e)}")
            return {
                'success': False,
                'result': f'An error occurred while processing the command: {str(e)}',
                'metadata': {'error': True}
            }
    
    def confirm_and_execute(self, cache_key: str, confirmed: bool, original_command: str, context: List[Dict] = None) -> Dict[str, Any]:
        """Execute a command after user confirmation."""
        try:
            # Store confirmation in security manager
            self.security_manager.confirm_action(cache_key, confirmed)
            
            if not confirmed:
                return {
                    'success': False,
                    'result': 'Command execution cancelled by user.',
                    'metadata': {'user_cancelled': True}
                }
            
            # Re-validate and execute
            security_result = self.security_manager.validate_command_execution(original_command)
            return self._execute_command(original_command, context or [], security_result)
            
        except Exception as e:
            logger.error(f"Error in confirm_and_execute: {str(e)}")
            return {
                'success': False,
                'result': f'An error occurred during execution: {str(e)}',
                'metadata': {'error': True}
            }
    
    def _execute_command(self, command: str, context: List[Dict], security_result: Dict) -> Dict[str, Any]:
        """Execute the validated command with fallback to simple responses when AI is unavailable."""
        try:
            command_lower = command.strip().lower()
            
            # Handle common queries directly without AI
            if any(phrase in command_lower for phrase in ['what apps', 'which apps', 'connect with']):
                return {
                    'success': True,
                    'result': "I can work with various applications including:\n\n"
                              "• Browsers: Chrome, Safari, Firefox\n"
                              "• Messaging: iMessage, Slack, Discord\n"
                              "• Productivity: Calendar, Notes, Reminders\n"
                              "• Media: Music, Photos, Videos\n\n"
                              "What would you like me to help you with?",
                    'metadata': {'method': 'direct_response'}
                }
                
            if any(phrase in command_lower for phrase in ['what can you do', 'help']):
                return {
                    'success': True,
                    'result': "I can help you with various tasks including:\n\n"
                              "• Open applications and websites\n"
                              "• Search the web\n"
                              "• Answer questions\n"
                              "• Set reminders and timers\n"
                              "• Control media playback\n\n"
                              "Just let me know what you'd like to do!",
                    'metadata': {'method': 'direct_response'}
                }
            
            # Try using Gemini AI if available
            if self.gemini_ai:
                try:
                    ai_response = self.gemini_ai.generate_response(
                        command, 
                        context, 
                        self.get_available_actions()
                    )
                    
                    if ai_response.get('success'):
                        # If AI suggests specific actions, try to execute them
                        if ai_response.get('requires_action') and ai_response.get('suggested_actions'):
                            action_results = []
                            for action in ai_response['suggested_actions']:
                                action_result = self._execute_ai_suggested_action(action, command)
                                if action_result:
                                    action_results.append(action_result)
                            
                            if action_results:
                                combined_result = ai_response['response'] + "\n\nActions performed:\n" + "\n".join(action_results)
                                return {
                                    'success': True,
                                    'result': combined_result,
                                    'metadata': {'method': 'ai_with_actions', 'actions': action_results}
                                }
                        
                        # Return AI response
                        return {
                            'success': True,
                            'result': ai_response['response'],
                            'metadata': {'method': 'ai_response'}
                        }
                except Exception as e:
                    logger.error(f"AI processing failed: {str(e)}")
                    # Fall through to direct response
            
            # For other commands, provide a helpful response
            return {
                'success': True,
                'result': "I can help you with various tasks. Try asking me to open an app, search the web, or ask what I can do.",
                'metadata': {'method': 'direct_response'}
            }
        
        except Exception as e:
            logger.error(f"Command processing failed: {str(e)}")
            return {
                'success': False,
                'result': f"An error occurred: {str(e)}",
                'metadata': {'error': str(e)}
            }
    
    def _check_command_security(self, command: str) -> bool:
        """Check if command is allowed by security policy."""
        # For now, allow most commands but block potentially dangerous ones
        dangerous_patterns = [
            r'(?:sudo|su)\s+',
            r'rm\s+-rf\s+/',
            r'format\s+',
            r'delete\s+system',
            r'chmod\s+777',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, command):
                return False
        
        return True
    
    def _handle_open_file(self, file_path: str, context: List[Dict] = None) -> str:
        """Handle file opening commands."""
        return self.plugins['file_manager'].open_file(file_path)
    
    def _handle_create(self, path: str, context: List[Dict] = None) -> str:
        """Handle file/folder creation commands."""
        if 'folder' in path or 'directory' in path:
            return self.plugins['file_manager'].create_folder(path)
        else:
            return self.plugins['file_manager'].create_file(path)
    
    def _handle_delete(self, path: str, context: List[Dict] = None) -> str:
        """Handle deletion commands."""
        return self.plugins['file_manager'].delete(path)
    
    def _handle_search(self, query: str, context: List[Dict] = None) -> str:
        """Handle search commands."""
        return self.plugins['file_manager'].search_files(query)
    
    def _handle_copy(self, source: str, destination: str, context: List[Dict] = None) -> str:
        """Handle copy commands."""
        return self.plugins['file_manager'].copy(source, destination)
    
    def _handle_move(self, source: str, destination: str, context: List[Dict] = None) -> str:
        """Handle move commands."""
        return self.plugins['file_manager'].move(source, destination)
    
    def _handle_edit_file(self, file_path: str, context: List[Dict] = None) -> str:
        """Handle file editing commands."""
        return self.plugins['file_manager'].edit_file(file_path)
    
    def _handle_launch_app(self, app_name: str, context: List[Dict] = None) -> str:
        """Handle app launching commands."""
        return self.plugins['app_controller'].launch_app(app_name)
    
    def _handle_close_app(self, app_name: str, context: List[Dict] = None) -> str:
        """Handle app closing commands."""
        return self.plugins['app_controller'].close_app(app_name)
    
    def _handle_switch_app(self, app_name: str, context: List[Dict] = None) -> str:
        """Handle app switching commands."""
        return self.plugins['app_controller'].switch_to_app(app_name)
    
    def _handle_web_search(self, query: str, context: List[Dict] = None) -> str:
        """Handle web search commands."""
        return self.plugins['web_controller'].search_web(query)
    
    def _handle_web_browse(self, target: str, context: List[Dict] = None) -> str:
        """Handle site-intent browse commands like 'open twitter AI agents'.
        Cleans the phrase and routes to the enhanced URL resolver.
        """
        try:
            text = (target or '').strip()
            # Remove trailing politeness
            text = re.sub(r"\s+(?:please|thanks|thank you)\.?$", '', text, flags=re.IGNORECASE).strip()
            return self._handle_browse_url(text, context=context)
        except Exception as e:
            logger.error(f"_handle_web_browse failed: {e}")
            return self.plugins['web_controller'].search_web(target or '')

    def _handle_browse_url(self, url_or_query: str, context: List[Dict] = None) -> str:
        """Handle URL browsing commands.
        Accepts full URLs, bare domains, or natural language like 'open reddit about colored tshirts'.
        """
        # Normalize
        text = (url_or_query or '').strip().strip(" \"'.,!")

        # If looks like a full URL or bare domain, normalize and open
        url_pattern = r"^(?:https?://)?[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&'\(\)\*\+,;=.]*$"
        if re.match(url_pattern, text):
            url = text if text.startswith(('http://', 'https://')) else f"https://{text}"
            logger.info(f"[BROWSE] Direct URL detected -> {url}")
            return self.plugins['web_controller'].browse_url(url)

        # Prefer site-native search when an explicit site is mentioned
        lower = text.lower()
        site_aliases = {
            'twitter': ['twitter', 'x.com', 'x ' , ' on x', ' on twitter'],
            'linkedin': ['linkedin', 'linked in'],
            'reddit': ['reddit'],
            'youtube': ['youtube', 'yt'],
            'github': ['github'],
            'stackoverflow': ['stackoverflow', 'stack overflow', 'stack-overflow'],
            'hackernews': ['hacker news', 'hn', 'news.ycombinator.com'],
            'medium': ['medium'],
            'producthunt': ['product hunt', 'producthunt']
        }

        def detect_site(s: str) -> Optional[str]:
            for key, aliases in site_aliases.items():
                for a in aliases:
                    if a in s:
                        return key
            # Also catch patterns like "on twitter" or "in linkedin"
            m = re.search(r"(?:on|in|at)\s+([a-z\.-]+)", s)
            if m:
                token = m.group(1)
                for key, aliases in site_aliases.items():
                    if token in aliases or token == key:
                        return key
            return None

        def strip_site_and_fillers(s: str, site_key: str) -> str:
            # Remove leading verbs
            s = re.sub(r"^(?:open|browse|visit|go to|search)\s+", '', s).strip()
            # Remove site mention phrases like "on twitter", "in linkedin"
            site_patterns = ['on', 'in', 'at', 'from', 'for']
            for sp in site_patterns:
                s = re.sub(rf"\b{sp}\s+{site_key}\b", '', s)
            # Also remove all aliases tokens
            for alias in site_aliases.get(site_key, []):
                s = s.replace(alias, '')
            # Remove common filler phrases
            s = re.sub(r"\b(posts|post|articles|article)\b", '', s)
            s = re.sub(r"\babout\b", '', s)
            # Clean extra spaces
            s = re.sub(r"\s+", ' ', s).strip()
            return s

        site_key = detect_site(lower)

        def build_site_url(site: str, query: str) -> Optional[str]:
            q = urllib.parse.quote_plus(query) if query else ''
            if site == 'twitter':
                return f"https://twitter.com/search?q={q}&src=typed_query"
            if site == 'linkedin':
                return f"https://www.linkedin.com/search/results/content/?keywords={q}"
            if site == 'reddit':
                return f"https://www.reddit.com/search/?q={q}"
            if site == 'youtube':
                return f"https://www.youtube.com/results?search_query={q}"
            if site == 'github':
                return f"https://github.com/search?q={q}"
            if site == 'stackoverflow':
                return f"https://stackoverflow.com/search?q={q}"
            if site == 'hackernews':
                return f"https://hn.algolia.com/?q={q}"
            if site == 'medium':
                return f"https://medium.com/search?q={q}"
            if site == 'producthunt':
                return f"https://www.producthunt.com/search?q={q}"
            return None

        if site_key:
            topic = strip_site_and_fillers(lower, site_key)
            # Build site-native search even if topic is empty to avoid opening the bare homepage
            built = build_site_url(site_key, topic)
            if built:
                logger.info(f"[BROWSE] Site-native search for '{site_key}' with topic '{topic}' -> {built}")
                return self.plugins['web_controller'].browse_url(built)

        # 1) Ask Gemini to produce the exact URL to open for this phrase (no explicit site or builder failed)
        if self.gemini_ai:
            try:
                prompt = (
                    "You are a URL resolver. Given a user request, output ONE final URL to open in a web browser "
                    "that best achieves the request. If a site requires a search URL, return the correct search URL "
                    "for that site. Output ONLY the URL, no extra text.\n\n"
                    f"User request: {text}"
                )
                ai_response = self.gemini_ai.generate_response(prompt, context or [], self.get_available_actions())

                # Accept either 'result' or 'response' then extract a URL
                possible = ai_response.get('result') or ai_response.get('response') or ''
                if isinstance(possible, dict):
                    possible = json.dumps(possible)

                # Extract first URL-looking token
                url_match = re.search(r"(https?://[^\s]+)", possible)
                candidate = url_match.group(1) if url_match else possible.strip()

                if candidate:
                    # Remove any surrounding punctuation
                    candidate = candidate.strip(" \"'.,!()[]{}")
                    if re.match(r"^https?://[\w.-]+(?:\.[\w\.-]+)+", candidate):
                        # If we detected a site intent earlier, ensure candidate domain matches
                        if site_key:
                            from urllib.parse import urlparse
                            cand_host = urlparse(candidate).netloc.lower()
                            site_host_map = {
                                'twitter': 'twitter.com',
                                'linkedin': 'www.linkedin.com',
                                'reddit': 'www.reddit.com',
                                'youtube': 'www.youtube.com',
                                'github': 'github.com',
                                'stackoverflow': 'stackoverflow.com',
                                'hackernews': 'news.ycombinator.com',
                                'medium': 'medium.com',
                                'producthunt': 'www.producthunt.com'
                            }
                            expected = site_host_map.get(site_key)
                            if expected and expected not in cand_host:
                                logger.warning(f"[BROWSE] Gemini candidate domain mismatch. expected~{expected} got {cand_host}. Falling back to site-native builder.")
                                # Mismatch: prefer site-native builder instead of wrong domain like ai.com or posts.com
                                built = build_site_url(site_key, strip_site_and_fillers(lower, site_key))
                                if built:
                                    logger.info(f"[BROWSE] Fallback site-native URL -> {built}")
                                    return self.plugins['web_controller'].browse_url(built)
                            logger.info(f"[BROWSE] Gemini candidate accepted -> {candidate}")
                        return self.plugins['web_controller'].browse_url(candidate)
                    # If it looks like a domain without scheme
                    if re.match(r"^[\w.-]+\.[a-zA-Z]{2,}(/.*)?$", candidate):
                        fixed = f"https://{candidate}"
                        logger.info(f"[BROWSE] Gemini candidate looked like bare domain, adding scheme -> {fixed}")
                        return self.plugins['web_controller'].browse_url(fixed)
            except Exception as e:
                logger.warning(f"[BROWSE] Gemini URL resolution failed: {e}")

        # 2) Fallback: detect a domain and create a site: search query
        domain_match = re.search(r"(?:on|in|at|from|for)\s+([a-z0-9.-]+\.[a-z]{2,})(?:\b|/)", lower)
        domain = domain_match.group(1) if domain_match else None
        if not domain:
            # Try to find any domain-like token anywhere
            any_domain = re.search(r"([a-z0-9.-]+\.[a-z]{2,})(?:\b|/)", lower)
            domain = any_domain.group(1) if any_domain else None

        if domain:
            # Remove domain reference words to form the topic
            topic = re.sub(rf"\b(?:on|in|at|from|for)\s+{re.escape(domain)}\b", "", lower).strip()
            if not topic:
                topic = lower
            q = urllib.parse.quote_plus(f"site:{domain} {topic}")
            google_url = f"https://www.google.com/search?q={q}"
            logger.info(f"[BROWSE] Fallback site: search -> {google_url}")
            return self.plugins['web_controller'].browse_url(google_url)

        # Fallback: perform a web search with the phrase
        logger.info(f"[BROWSE] Fallback generic web search for '{text}'")
        return self.plugins['web_controller'].search_web(text)

    def _open_url_in_browser(self, url: str) -> str:
        """Open the URL in the browser using browser_action tool."""
        try:
            self.plugins['web_controller'].browse_url(url)
            return f"Opened URL: {url}"
        except Exception as e:
            return f"Failed to open URL in browser: {str(e)}"
    
    def _handle_download(self, url: str, context: List[Dict] = None) -> str:
        """Handle download commands."""
        return self.plugins['web_controller'].download_file(url)
    
    def _handle_run_script(self, script_path: str, context: List[Dict] = None) -> str:
        """Handle script execution commands."""
        return self.plugins['script_runner'].run_script(script_path)
    
    def _handle_run_python(self, code_or_file: str, context: List[Dict] = None) -> str:
        """Handle Python execution commands."""
        return self.plugins['script_runner'].run_python(code_or_file)
    
    def _handle_run_bash(self, command: str, context: List[Dict] = None) -> str:
        """Handle bash command execution."""
        return self.plugins['script_runner'].run_bash(command)
    
    def _handle_system_info(self, context: List[Dict] = None) -> str:
        """Handle system information requests."""
        return self.plugins['system_info'].get_system_info()
    
    def _handle_time(self, context: List[Dict] = None) -> str:
        """Handle time requests."""
        return self.plugins['system_info'].get_current_time()
    
    def _handle_weather(self, context: List[Dict] = None) -> str:
        """Handle weather requests."""
        return self.plugins['system_info'].get_weather()
    
    def _handle_running_processes(self, context: List[Dict] = None) -> str:
        """Handle running processes requests."""
        return self.plugins['system_info'].get_running_processes()
    
    def _handle_largest_apps(self, context: List[Dict] = None) -> str:
        """Handle largest applications requests."""
        return self.plugins['system_info'].get_largest_apps()
    
    def _handle_find_largest_file(self, context: List[Dict] = None) -> str:
        """Handle finding the largest file on the system."""
        try:
            import subprocess
            import os
            
            # Start with more targeted search to avoid timeouts
            # First try user directories which are more likely to have large files
            user_home = os.path.expanduser("~")
            
            # Search priority areas first
            search_areas = [
                f"{user_home}/Downloads",
                f"{user_home}/Desktop", 
                f"{user_home}/Documents",
                f"{user_home}/Movies",
                f"{user_home}/Pictures",
                f"{user_home}",  # Entire home directory
                "/Applications",  # macOS Applications
                "/"  # Full system (last resort)
            ]
            
            largest_file = None
            largest_size = 0
            
            for search_path in search_areas:
                if not os.path.exists(search_path):
                    continue
                    
                try:
                    # Use a shorter timeout for each area
                    cmd = f"find '{search_path}' -type f -exec ls -la {{}} + 2>/dev/null | awk '{{if($5 > max) {{max=$5; file=$9}} }} END {{print max, file}}'"
                    
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                    
                    if result.returncode == 0 and result.stdout.strip():
                        output = result.stdout.strip()
                        if output and output != " ":
                            parts = output.split(' ', 1)
                            if len(parts) == 2 and parts[0].isdigit():
                                size_bytes = int(parts[0])
                                file_path = parts[1]
                                
                                if size_bytes > largest_size:
                                    largest_size = size_bytes
                                    largest_file = file_path
                
                except (subprocess.TimeoutExpired, Exception) as e:
                    # Continue to next search area if this one fails
                    continue
            
            if largest_file and largest_size > 0:
                # Convert bytes to human readable format
                def format_size(bytes):
                    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                        if bytes < 1024.0:
                            return f"{bytes:.1f} {unit}"
                        bytes /= 1024.0
                    return f"{bytes:.1f} PB"
                
                formatted_size = format_size(largest_size)
                
                return f"""🔍 **Largest File Found**

**File:** {largest_file}
**Size:** {formatted_size} ({largest_size:,} bytes)

This is the largest file found during the search of your accessible directories."""
            
            # If no file found, try a quick alternative approach
            try:
                # Use du command for a faster approach
                cmd = f"du -a '{user_home}' 2>/dev/null | sort -rn | head -1"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
                
                if result.returncode == 0 and result.stdout.strip():
                    output = result.stdout.strip()
                    parts = output.split('\t', 1) if '\t' in output else output.split(' ', 1)
                    if len(parts) == 2:
                        size_kb = int(parts[0])
                        file_path = parts[1]
                        size_bytes = size_kb * 1024
                        
                        def format_size(bytes):
                            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                                if bytes < 1024.0:
                                    return f"{bytes:.1f} {unit}"
                                bytes /= 1024.0
                            return f"{bytes:.1f} PB"
                        
                        formatted_size = format_size(size_bytes)
                        
                        return f"""🔍 **Largest File Found**

**File:** {file_path}
**Size:** {formatted_size} ({size_bytes:,} bytes)

This is the largest file found in your home directory."""
            except Exception:
                pass
            
            return "❌ Could not find large files. The search may have been restricted by system permissions or no accessible large files were found."
                
        except Exception as e:
            return f"❌ Failed to search for largest file: {str(e)}"
    
    def _handle_find_smallest_file(self, context: List[Dict] = None) -> str:
        """Handle finding the smallest file on the system."""
        try:
            import subprocess
            import os
            
            # Start with more targeted search to avoid timeouts
            user_home = os.path.expanduser("~")
            
            # Search priority areas first
            search_areas = [
                f"{user_home}/Downloads",
                f"{user_home}/Desktop", 
                f"{user_home}/Documents",
                f"{user_home}/.config",
                f"{user_home}",  # Entire home directory
                "/Applications",  # macOS Applications
                "/"  # Full system (last resort)
            ]
            
            smallest_file = None
            smallest_size = float('inf')  # Start with infinity to find the smallest
            
            for search_path in search_areas:
                if not os.path.exists(search_path):
                    continue
                    
                try:
                    # Use find to locate non-empty files (size > 0) and get the smallest
                    cmd = f"find '{search_path}' -type f -size +0c -exec ls -la {{}} + 2>/dev/null | awk '{{if($5 < min || min==0) {{min=$5; file=$9}} }} END {{print min, file}}'"
                    
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                    
                    if result.returncode == 0 and result.stdout.strip():
                        output = result.stdout.strip()
                        if output and output != " ":
                            parts = output.split(' ', 1)
                            if len(parts) == 2 and parts[0].isdigit():
                                size_bytes = int(parts[0])
                                file_path = parts[1]
                                
                                if size_bytes < smallest_size:
                                    smallest_size = size_bytes
                                    smallest_file = file_path
                
                except (subprocess.TimeoutExpired, Exception) as e:
                    # Continue to next search area if this one fails
                    continue
            
            if smallest_file and smallest_size < float('inf'):
                # Convert bytes to human readable format
                def format_size(bytes):
                    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                        if bytes < 1024.0:
                            return f"{bytes:.1f} {unit}"
                        bytes /= 1024.0
                    return f"{bytes:.1f} PB"
                
                formatted_size = format_size(smallest_size)
                
                return f"""🔍 **Smallest File Found**

**File:** {smallest_file}
**Size:** {formatted_size} ({smallest_size:,} bytes)

This is the smallest file found during the search of your accessible directories."""
            
            # If no file found, try a quick alternative approach
            try:
                # Use find with a more focused approach
                cmd = f"find '{user_home}' -type f -size +0c -size -1024c 2>/dev/null | xargs ls -la 2>/dev/null | sort -n -k 5 | head -1"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
                
                if result.returncode == 0 and result.stdout.strip():
                    output = result.stdout.strip()
                    parts = output.split()
                    if len(parts) >= 5:
                        size_bytes = int(parts[4])
                        file_path = ' '.join(parts[8:]) if len(parts) > 8 else parts[8]
                        
                        def format_size(bytes):
                            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                                if bytes < 1024.0:
                                    return f"{bytes:.1f} {unit}"
                                bytes /= 1024.0
                            return f"{bytes:.1f} PB"
                        
                        formatted_size = format_size(size_bytes)
                        
                        return f"""🔍 **Smallest File Found**

**File:** {file_path}
**Size:** {formatted_size} ({size_bytes:,} bytes)

This is the smallest file found in your home directory."""
            except Exception:
                pass
            
            return "❌ Could not find small files. The search may have been restricted by system permissions or no accessible small files were found."
                
        except Exception as e:
            return f"❌ Failed to search for smallest file: {str(e)}"
    
    def _handle_disk_usage(self, context: List[Dict] = None) -> str:
        """Handle disk usage analysis requests."""
        return self.plugins['system_info'].get_disk_usage_analysis()
    
    def _handle_help(self, context: List[Dict] = None) -> str:
        """Handle help requests."""
        ai_status = "🤖 AI-Powered" if self.gemini_ai else "🔧 Rule-Based"
        
        return f"""I'm Cluely, your {ai_status} desktop assistant! I can help you with:
        
📁 File Operations:
  - Open, create, delete, copy, move files and folders
  - Search for files by name or content
  - Edit text files
  
🚀 App Control:
  - Launch, close, and switch between applications
  - Control app windows and menus
  
🌐 Web Operations:
  - Search the web, browse websites
  - Download files from URLs
  - Interact with web APIs
  
⚙️ Script Execution:
  - Run Python scripts and code
  - Execute bash/shell commands
  - Automate multi-step tasks
  
📊 System Information:
  - Get system status and information
  - Check time, weather, and more
  - Analyze disk usage and app sizes

🧠 AI Assistance:
  - Ask questions in natural language
  - Get explanations and recommendations
  - Context-aware responses

📝 Document Creation:
  - Create Word documents, Excel spreadsheets
  - Make PowerPoint presentations, PDFs
  - Use templates for common document types

📧 Email & Calendar:
  - Compose and send emails
  - Create meeting invites and calendar events
  - Check your schedule
  - Switch between Google accounts

🤖 Automation:
  - Organize your Downloads folder
  - Create daily productivity reports
  - Backup important files
  - Clean temporary files
  - Run custom workflows

🖥️ OS-Level Control (macOS):
  - Check and request system permissions
  - Click at specific coordinates
  - Type text and press key combinations
  - Take screenshots
  - Control windows (minimize, maximize, close)
  - Full accessibility and automation

🔐 Security Features:
  - Permission management and checking
  - Action logging for safety
  - Safe command execution with confirmations

Examples:
  • "What app takes the most space on my computer?"
  • "Check system permissions"
  • "Take a screenshot"
  • "Click at coordinates 100, 200"
  • "Type text 'Hello World'"
  • "Press command+c"
  • "Control window minimize Safari"
  • "Create a Word document called meeting-notes"
  • "Organize my downloads folder"
  • "Create a daily report"

Just tell me what you want to do in natural language!"""
    
    def _handle_intent(self, intent: Dict[str, Any], context: List[Dict] = None) -> str:
        """Handle intents extracted by NLP processor."""
        action = intent.get('action', '')
        target = intent.get('target', '')
        
        if action == 'open' and target:
            return self._handle_open_file(target, context)
        elif action == 'search' and target:
            return self._handle_search(target, context)
        elif action == 'help':
            return self._handle_help(context)
        else:
            return "I couldn't understand that request. Could you rephrase it?"
    
    def get_capabilities(self) -> List[str]:
        """Return list of available capabilities."""
        return [
            "File and folder management",
            "Application control",
            "Web browsing and searching",
            "Script execution",
            "System information",
            "Natural language processing"
        ]
    
    def get_available_actions(self) -> List[str]:
        """Get list of available system actions for AI context."""
        return [
            "create/edit/delete files", "search files", "copy/move files",
            "launch/close applications", "switch between apps",
            "web search", "browse URLs", "download files",
            "run Python code", "execute bash commands", "run scripts",
            "get system info", "check time", "list processes",
            "get weather", "help and assistance",
            "create Word documents", "create Excel spreadsheets", 
            "create PowerPoint presentations", "create PDF documents",
            "compose emails", "send emails", "create meeting invites",
            "check calendar", "switch Google accounts", "open Gmail",
            "organize downloads", "backup files", "clean temp files",
            "create daily reports", "run automation workflows"
        ]
    
    def _execute_ai_suggested_action(self, action: Dict[str, str], original_command: str) -> Optional[str]:
        """Execute an action suggested by AI."""
        try:
            action_type = action.get('type', '')
            logger.info(f"Executing AI suggested action: {action_type}")
            
            if action_type == 'file_create':
                # Check if we have a specific filename from action extraction
                if 'filename' in action:
                    filename = action['filename']
                else:
                    # Extract filename from original command
                    filename_patterns = [
                        r'create (?:file |)([^\s]+\.[\w]+)',
                        r'make (?:file |)([^\s]+\.[\w]+)', 
                        r'new (?:file |)([^\s]+\.[\w]+)',
                        r'file (?:called |named |)([^\s]+\.[\w]+)'
                    ]
                    
                    filename = None
                    for pattern in filename_patterns:
                        match = re.search(pattern, original_command.lower())
                        if match:
                            filename = match.group(1)
                            break
                    
                    if not filename:
                        # Default filename if none specified
                        filename = f"new_file_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                
                return self.plugins['file_manager'].create_file(filename)
            
            elif action_type == 'file_open':
                # Extract filename from command
                filename_match = re.search(r'(?:open|show|display)\s+(?:file\s+)?(\S+)', original_command.lower())
                if filename_match:
                    filename = filename_match.group(1)
                    return self.plugins['file_manager'].open_file(filename)
                return "Please specify which file to open."
            
            elif action_type == 'file_edit':
                # Extract filename from command
                filename_match = re.search(r'(?:edit|modify|update)\s+(?:file\s+)?(\S+)', original_command.lower())
                if filename_match:
                    filename = filename_match.group(1)
                    return self.plugins['file_manager'].edit_file(filename)
                return "Please specify which file to edit."
            
            elif action_type == 'file_delete':
                # Extract filename from command
                filename_match = re.search(r'(?:delete|remove)\s+(?:file\s+)?(\S+)', original_command.lower())
                if filename_match:
                    filename = filename_match.group(1)
                    return self.plugins['file_manager'].delete(filename)
                return "Please specify which file to delete."
            
            elif action_type == 'app_launch':
                app_patterns = [
                    r'(?:launch|open|start)\s+(\w+)',
                    r'open\s+(\w+)\s+app',
                    r'start\s+(\w+)\s+application'
                ]
                
                for pattern in app_patterns:
                    app_match = re.search(pattern, original_command.lower())
                    if app_match:
                        app_name = app_match.group(1)
                        return self.plugins['app_controller'].launch_app(app_name)
                return "Please specify which application to launch."
            
            elif action_type == 'app_close':
                app_patterns = [
                    r'(?:close|quit|exit)\s+(\w+)',
                    r'close\s+(\w+)\s+app'
                ]
                
                for pattern in app_patterns:
                    app_match = re.search(pattern, original_command.lower())
                    if app_match:
                        app_name = app_match.group(1)
                        return self.plugins['app_controller'].close_app(app_name)
                return "Please specify which application to close."
            
            elif action_type == 'web_search':
                search_patterns = [
                    r'(?:search|google)\s+(?:for\s+)?(.+)',
                    r'look\s+up\s+(.+)',
                    r'find\s+(?:online\s+)?(.+)'
                ]
                
                for pattern in search_patterns:
                    search_match = re.search(pattern, original_command.lower())
                    if search_match:
                        query = search_match.group(1).strip()
                        # Remove common stop words from end of query
                        query = re.sub(r'\s+(?:please|for me|online)$', '', query)
                        return self.plugins['web_controller'].search_web(query)
                return "Please specify what to search for."
            
            elif action_type == 'web_browse':
                # Capture the full target phrase after the browsing verb and route through _handle_browse_url
                target_match = re.search(r'(?:browse|visit|go to|open)\s+(.+)$', original_command.strip(), flags=re.IGNORECASE)
                if target_match:
                    target = target_match.group(1).strip()
                    # Remove trailing politeness or filler
                    target = re.sub(r'\s+(please|thanks|thank you)\.?$', '', target, flags=re.IGNORECASE).strip()
                    return self._handle_browse_url(target)
                return "Please specify which URL to browse."
            
            elif action_type == 'system_info':
                return self.plugins['system_info'].get_system_info()
            
            elif action_type == 'script_run':
                # Extract script content or filename
                script_match = re.search(r'(?:python|run)\s+(.+)', original_command)
                if script_match:
                    script_content = script_match.group(1)
                    return self.plugins['script_runner'].run_python(script_content)
                return "Please specify what script to run."
            
            elif action_type == 'organize':
                # Check for organize downloads specifically
                if 'download' in original_command.lower():
                    return self.plugins['automation_manager'].organize_downloads()
                return "Please specify what to organize."
            
            elif action_type == 'screenshot':
                if self.system_controller:
                    return self.system_controller.take_screenshot()
                return "Screenshot functionality requires system permissions."
            
            elif action_type == 'file_search':
                # Handle file search commands like "find smallest file"
                import subprocess
                import os
                
                if 'smallest' in original_command.lower():
                    try:
                        # Find smallest files - use more efficient approach with common directories
                        search_dirs = [
                            os.path.expanduser('~/Desktop'),
                            os.path.expanduser('~/Documents'), 
                            os.path.expanduser('~/Downloads'),
                            '/tmp',
                            '/var/tmp'
                        ]
                        
                        all_files = []
                        for search_dir in search_dirs:
                            if os.path.exists(search_dir):
                                try:
                                    # Find files in this directory only (not recursive for speed)
                                    cmd = f"find '{search_dir}' -maxdepth 2 -type f -exec ls -la {{}} + 2>/dev/null | sort -k5 -n | head -5"
                                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                                    if result.returncode == 0 and result.stdout:
                                        all_files.extend(result.stdout.strip().split('\n'))
                                except subprocess.TimeoutExpired:
                                    continue
                        
                        if all_files:
                            # Sort all results by size
                            valid_files = []
                            for line in all_files:
                                if line.strip():
                                    parts = line.split()
                                    if len(parts) >= 9 and parts[4].isdigit():
                                        size = int(parts[4])
                                        filename = ' '.join(parts[8:])
                                        valid_files.append((size, filename))
                            
                            # Sort by size and format result
                            valid_files.sort(key=lambda x: x[0])
                            formatted_result = "Smallest files found:\n"
                            for i, (size, filename) in enumerate(valid_files[:10]):
                                formatted_result += f"{i+1}. {filename} ({size} bytes)\n"
                            return formatted_result
                        else:
                            return "No files found in common directories."
                    except Exception as e:
                        return f"Search failed: {str(e)}"
                
                elif 'largest' in original_command.lower():
                    try:
                        # Find largest files - use more efficient approach with common directories
                        search_dirs = [
                            os.path.expanduser('~/Desktop'),
                            os.path.expanduser('~/Documents'), 
                            os.path.expanduser('~/Downloads'),
                            os.path.expanduser('~/Pictures'),
                            os.path.expanduser('~/Movies')
                        ]
                        
                        all_files = []
                        for search_dir in search_dirs:
                            if os.path.exists(search_dir):
                                try:
                                    # Find files in this directory (maxdepth 3 for more coverage of large files)
                                    cmd = f"find '{search_dir}' -maxdepth 3 -type f -exec ls -la {{}} + 2>/dev/null | sort -k5 -nr | head -5"
                                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                                    if result.returncode == 0 and result.stdout:
                                        all_files.extend(result.stdout.strip().split('\n'))
                                except subprocess.TimeoutExpired:
                                    continue
                        
                        if all_files:
                            # Sort all results by size (largest first)
                            valid_files = []
                            for line in all_files:
                                if line.strip():
                                    parts = line.split()
                                    if len(parts) >= 9 and parts[4].isdigit():
                                        size = int(parts[4])
                                        filename = ' '.join(parts[8:])
                                        valid_files.append((size, filename))
                            
                            # Sort by size (descending)
                            valid_files.sort(key=lambda x: x[0], reverse=True)
                            formatted_result = "Largest files found:\n"
                            for i, (size, filename) in enumerate(valid_files[:10]):
                                size_mb = size / (1024 * 1024)
                                formatted_result += f"{i+1}. {filename} ({size_mb:.2f} MB)\n"
                            return formatted_result
                        else:
                            return "No files found in common directories."
                    except Exception as e:
                        return f"Search failed: {str(e)}"
                
                else:
                    # General file search
                    search_match = re.search(r'(?:find|search|locate)\s+(?:file\s+)?(.+)', original_command.lower())
                    if search_match:
                        query = search_match.group(1).strip()
                        return self.plugins['file_manager'].search_files(query)
                    return "Please specify what to search for."
            
            elif action_type == 'system_search':
                # Handle system-wide searches
                import subprocess
                import os
                
                if 'smallest file' in original_command.lower():
                    try:
                        # Find smallest files system-wide (efficient approach)
                        safe_dirs = [
                            os.path.expanduser('~/Desktop'),
                            os.path.expanduser('~/Documents'), 
                            os.path.expanduser('~/Downloads'),
                            '/tmp',
                            '/var/tmp',
                            '/System/Library/CoreServices'
                        ]
                        results = []
                        
                        for directory in safe_dirs:
                            if os.path.exists(directory):
                                try:
                                    cmd = f"find '{directory}' -maxdepth 2 -type f -exec ls -la {{}} + 2>/dev/null | sort -k5 -n | head -3"
                                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=8)
                                    if result.returncode == 0 and result.stdout:
                                        results.extend(result.stdout.strip().split('\n'))
                                except subprocess.TimeoutExpired:
                                    continue
                        
                        if results:
                            # Parse and sort all results
                            valid_files = []
                            for line in results:
                                if line.strip():
                                    parts = line.split()
                                    if len(parts) >= 9 and parts[4].isdigit():
                                        size = int(parts[4])
                                        filename = ' '.join(parts[8:])
                                        valid_files.append((size, filename))
                            
                            # Sort by size and take smallest
                            valid_files.sort(key=lambda x: x[0])
                            formatted_result = "Smallest files found on system:\n"
                            for i, (size, filename) in enumerate(valid_files[:10]):
                                formatted_result += f"{i+1}. {filename} ({size} bytes)\n"
                            return formatted_result
                        else:
                            return "No files found or access denied."
                    except Exception as e:
                        return f"System search failed: {str(e)}"
                
                elif 'largest file' in original_command.lower():
                    try:
                        # Find largest files system-wide (efficient approach)
                        safe_dirs = [
                            os.path.expanduser('~/Desktop'),
                            os.path.expanduser('~/Documents'), 
                            os.path.expanduser('~/Downloads'),
                            os.path.expanduser('~/Pictures'),
                            os.path.expanduser('~/Movies'),
                            '/Applications'
                        ]
                        results = []
                        
                        for directory in safe_dirs:
                            if os.path.exists(directory):
                                try:
                                    cmd = f"find '{directory}' -maxdepth 3 -type f -exec ls -la {{}} + 2>/dev/null | sort -k5 -nr | head -3"
                                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=8)
                                    if result.returncode == 0 and result.stdout:
                                        results.extend(result.stdout.strip().split('\n'))
                                except subprocess.TimeoutExpired:
                                    continue
                        
                        if results:
                            # Parse and sort all results
                            valid_files = []
                            for line in results:
                                if line.strip():
                                    parts = line.split()
                                    if len(parts) >= 9 and parts[4].isdigit():
                                        size = int(parts[4])
                                        filename = ' '.join(parts[8:])
                                        valid_files.append((size, filename))
                            
                            # Sort by size (largest first)
                            valid_files.sort(key=lambda x: x[0], reverse=True)
                            formatted_result = "Largest files found on system:\n"
                            for i, (size, filename) in enumerate(valid_files[:10]):
                                size_mb = size / (1024 * 1024)
                                formatted_result += f"{i+1}. {filename} ({size_mb:.2f} MB)\n"
                            return formatted_result
                        else:
                            return "No files found or access denied."
                    except Exception as e:
                        return f"System search failed: {str(e)}"
                        
                return "System search completed."
            
            elif action_type == 'terminal_command':
                # Handle direct terminal commands
                import subprocess
                
                # Extract the actual command to run
                
                # Common patterns for terminal commands
                terminal_patterns = [
                    r'run command (.+)',
                    r'execute (.+)', 
                    r'terminal (.+)',
                    original_command.lower()  # Use full command as fallback
                ]
                
                command_to_run = None
                for pattern in terminal_patterns:
                    if pattern == original_command.lower():
                        command_to_run = original_command.lower()
                        break
                    else:
                        match = re.search(pattern, original_command.lower())
                        if match:
                            command_to_run = match.group(1)
                            break
                
                if command_to_run:
                    try:
                        # Security check: only allow safe commands
                        safe_commands = ['ls', 'find', 'grep', 'cat', 'head', 'tail', 'sort', 'awk', 'sed', 'wc', 'du', 'df']
                        cmd_parts = command_to_run.split()
                        if cmd_parts and cmd_parts[0] in safe_commands:
                            result = subprocess.run(command_to_run, shell=True, capture_output=True, text=True, timeout=30)
                            if result.returncode == 0:
                                return f"Command output:\n{result.stdout}" if result.stdout else "Command completed successfully (no output)."
                            else:
                                return f"Command failed with error:\n{result.stderr}" if result.stderr else "Command failed."
                        else:
                            return f"Command '{cmd_parts[0] if cmd_parts else command_to_run}' is not allowed for security reasons."
                    except Exception as e:
                        return f"Failed to execute command: {str(e)}"
                
                return "Please specify a valid terminal command."
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to execute AI suggested action: {str(e)}")
            return f"Action failed: {str(e)}"
    
    def _execute_intent(self, intent_data: Dict[str, Any], context: List[Dict]) -> Optional[str]:
        """Execute an intent understood by AI."""
        try:
            intent = intent_data.get('intent', '')
            action = intent_data.get('action', '')
            target = intent_data.get('target', '')
            
            if intent == 'file_operation':
                if action == 'create':
                    return self.plugins['file_manager'].create_file(target)
                elif action == 'open':
                    return self.plugins['file_manager'].open_file(target)
                elif action == 'delete':
                    return self.plugins['file_manager'].delete(target)
                elif action == 'search':
                    return self.plugins['file_manager'].search_files(target)
            
            elif intent == 'app_control':
                if action == 'launch':
                    return self.plugins['app_controller'].launch_app(target)
                elif action == 'close':
                    return self.plugins['app_controller'].close_app(target)
                elif action == 'switch':
                    return self.plugins['app_controller'].switch_to_app(target)
            
            elif intent == 'web_operation':
                if action == 'search':
                    return self.plugins['web_controller'].search_web(target)
                elif action == 'browse':
                    return self.plugins['web_controller'].browse_url(target)
                elif action == 'download':
                    return self.plugins['web_controller'].download_file(target)
            
            elif intent == 'script_execution':
                if action == 'python':
                    return self.plugins['script_runner'].run_python(target)
                elif action == 'bash':
                    return self.plugins['script_runner'].run_bash(target)
            
            elif intent == 'system_info':
                if action == 'status':
                    return self.plugins['system_info'].get_system_info()
                elif action == 'time':
                    return self.plugins['system_info'].get_current_time()
                elif action == 'processes':
                    return self.plugins['system_info'].get_running_processes()
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to execute intent: {str(e)}")
            return None
    
    # Document creation handlers
    def _handle_create_word_doc(self, filename: str, context: List[Dict] = None) -> str:
        """Handle Word document creation."""
        return self.plugins['document_manager'].create_word_document(filename)
    
    def _handle_create_excel(self, filename: str, context: List[Dict] = None) -> str:
        """Handle Excel spreadsheet creation."""
        return self.plugins['document_manager'].create_excel_spreadsheet(filename)
    
    def _handle_create_presentation(self, filename: str, context: List[Dict] = None) -> str:
        """Handle PowerPoint presentation creation."""
        return self.plugins['document_manager'].create_presentation(filename)
    
    def _handle_create_pdf(self, filename: str, context: List[Dict] = None) -> str:
        """Handle PDF document creation."""
        return self.plugins['document_manager'].create_pdf_document(filename)
    
    # Email and calendar handlers
    def _handle_compose_email(self, recipient_info: str, context: List[Dict] = None) -> str:
        """Handle email composition."""
        # Parse recipient info - could be "john@example.com" or "john@example.com about meeting"
        parts = recipient_info.split(' about ', 1)
        to_email = parts[0].strip()
        subject = parts[1] if len(parts) > 1 else ""
        
        return self.plugins['email_manager'].compose_email(to=to_email, subject=subject)
    
    def _handle_create_meeting(self, meeting_info: str, context: List[Dict] = None) -> str:
        """Handle meeting invite creation."""
        # Simple parsing - could be enhanced with NLP
        # Format: "Team standup tomorrow at 2pm with john@example.com, jane@example.com"
        parts = meeting_info.split(' with ', 1)
        title_and_time = parts[0].strip()
        
        # Extract attendees if provided
        attendees = []
        if len(parts) > 1:
            attendee_str = parts[1]
            attendees = [email.strip() for email in attendee_str.split(',')]
        
        # Extract time - simple parsing
        if ' at ' in title_and_time:
            title, time_str = title_and_time.rsplit(' at ', 1)
        else:
            title = title_and_time
            time_str = "tomorrow 2pm"  # default
        
        return self.plugins['email_manager'].create_meeting_invite(
            title=title, 
            attendees=attendees, 
            start_time=time_str
        )
    
    def _handle_check_calendar(self, date_info: str = "", context: List[Dict] = None) -> str:
        """Handle calendar checking."""
        date = date_info.strip() if date_info else "today"
        return self.plugins['email_manager'].check_calendar(date)
    
    def _handle_switch_google_account(self, account_email: str = "", context: List[Dict] = None) -> str:
        """Handle Google account switching."""
        return self.plugins['email_manager'].switch_google_account(account_email)
    
    def _handle_open_gmail(self, account: str = "", context: List[Dict] = None) -> str:
        """Handle Gmail opening."""
        return self.plugins['email_manager'].open_gmail(account)
    
    # Automation handlers
    def _handle_organize_downloads(self, context: List[Dict] = None) -> str:
        """Handle downloads organization."""
        return self.plugins['automation_manager'].organize_downloads()
    
    def _handle_create_daily_report(self, context: List[Dict] = None) -> str:
        """Handle daily report creation."""
        return self.plugins['automation_manager'].create_daily_report()
    
    def _handle_backup_files(self, context: List[Dict] = None) -> str:
        """Handle file backup."""
        return self.plugins['automation_manager'].backup_important_folders()
    
    def _handle_clean_temp(self, context: List[Dict] = None) -> str:
        """Handle temporary file cleaning."""
        return self.plugins['automation_manager'].clean_temp_files()
    
    def _handle_list_workflows(self, context: List[Dict] = None) -> str:
        """Handle workflow listing."""
        return self.plugins['automation_manager'].list_workflows()
    
    def _handle_run_workflow(self, workflow_name: str, context: List[Dict] = None) -> str:
        """Handle workflow execution."""
        return self.plugins['automation_manager'].run_workflow(workflow_name)
    
    # macOS System Control handlers
    def _handle_check_permissions(self, context: List[Dict] = None) -> str:
        """Handle checking system permissions."""
        if not self.permissions_manager:
            return "❌ Permission checking only available on macOS"
        
        try:
            check_result = self.permissions_manager.check_all_permissions()
            
            if check_result['all_granted']:
                return "✅ All required system permissions are granted!"
            else:
                missing = ", ".join(check_result['missing'])
                return f"⚠️  Missing permissions: {missing}\\nUse 'request permissions' for setup instructions."
                
        except Exception as e:
            return f"❌ Permission check failed: {str(e)}"
    
    def _handle_request_permissions(self, context: List[Dict] = None) -> str:
        """Handle requesting system permissions."""
        if not self.permissions_manager:
            return "❌ Permission management only available on macOS"
        
        return self.permissions_manager.request_permissions()
    
    def _handle_open_system_settings(self, context: List[Dict] = None) -> str:
        """Handle opening system settings."""
        if not self.permissions_manager:
            return "❌ System settings access only available on macOS"
        
        return self.permissions_manager.open_system_preferences("privacy")
    
    def _handle_click_coordinates(self, x: str, y: str, context: List[Dict] = None) -> str:
        """Handle clicking at specific coordinates."""
        if not self.system_controller:
            return "❌ System control only available on macOS"
        
        try:
            x_coord = int(x)
            y_coord = int(y)
            return self.system_controller.click_at_coordinates(x_coord, y_coord)
        except ValueError:
            return "❌ Invalid coordinates. Use format: click at 100, 200"
    
    def _handle_type_text(self, text: str, context: List[Dict] = None) -> str:
        """Handle typing text."""
        if not self.system_controller:
            return "❌ System control only available on macOS"
        
        return self.system_controller.type_text(text)
    
    def _handle_press_keys(self, keys: str, context: List[Dict] = None) -> str:
        """Handle pressing key combinations."""
        if not self.system_controller:
            return "❌ System control only available on macOS"
        
        # Parse key combination
        key_list = [k.strip() for k in keys.replace('+', ',').split(',')]
        return self.system_controller.press_key_combination(key_list)
    
    def _handle_screenshot(self, context: List[Dict] = None) -> str:
        """Handle taking screenshots."""
        if not self.system_controller:
            return "❌ System control only available on macOS"
        
        return self.system_controller.take_screenshot()
    
    def _handle_window_control(self, command: str, context: List[Dict] = None) -> str:
        """Handle window control commands."""
        if not self.system_controller:
            return "❌ System control only available on macOS"
        
        # Parse command like "minimize Safari" or "close Chrome window"
        parts = command.lower().split()
        if len(parts) >= 2:
            action = parts[0]
            app_name = " ".join(parts[1:]).replace(" window", "")
            return self.system_controller.control_window(app_name, action)
        else:
            return "❌ Invalid window control command. Use format: 'control window minimize Safari'"
    
    def _handle_operating_system(self, context: List[Dict] = None) -> str:
        """Handle operating system information requests."""
        try:
            import subprocess
            import platform
            
            # Get detailed system information
            system_name = platform.system()
            system_release = platform.release()
            system_version = platform.version()
            machine = platform.machine()
            processor = platform.processor()
            
            # Get more detailed info using system commands
            if system_name == "Darwin":  # macOS
                try:
                    # Get macOS version info
                    result = subprocess.run(['sw_vers'], capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        sw_vers_output = result.stdout.strip()
                        
                        # Extract version info
                        lines = sw_vers_output.split('\n')
                        product_name = ""
                        product_version = ""
                        build_version = ""
                        
                        for line in lines:
                            if line.startswith('ProductName:'):
                                product_name = line.split(':', 1)[1].strip()
                            elif line.startswith('ProductVersion:'):
                                product_version = line.split(':', 1)[1].strip()
                            elif line.startswith('BuildVersion:'):
                                build_version = line.split(':', 1)[1].strip()
                        
                        return f"🖥️ **Operating System Information**\n\n**System:** {product_name} {product_version}\n**Build:** {build_version}\n**Architecture:** {machine}\n**Processor:** {processor}"
                    
                except subprocess.TimeoutExpired:
                    pass
                except Exception as e:
                    logger.warning(f"Could not get detailed macOS info: {e}")
                
                return f"🖥️ **Operating System Information**\n\n**System:** {system_name} {system_release}\n**Version:** {system_version}\n**Architecture:** {machine}"
                
            elif system_name == "Linux":
                try:
                    # Try to get distribution info
                    result = subprocess.run(['lsb_release', '-d'], capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        distro_info = result.stdout.strip().split('\t')[1]
                        return f"🖥️ **Operating System Information**\n\n**Distribution:** {distro_info}\n**Kernel:** {system_name} {system_release}\n**Architecture:** {machine}"
                except:
                    pass
                
                return f"🖥️ **Operating System Information**\n\n**System:** {system_name} {system_release}\n**Version:** {system_version}\n**Architecture:** {machine}"
                
            elif system_name == "Windows":
                return f"🖥️ **Operating System Information**\n\n**System:** {system_name} {system_release}\n**Version:** {system_version}\n**Architecture:** {machine}"
            
            else:
                return f"🖥️ **Operating System Information**\n\n**System:** {system_name} {system_release}\n**Version:** {system_version}\n**Architecture:** {machine}"
                
        except Exception as e:
            logger.error(f"Error getting operating system info: {e}")
            return f"❌ Error getting operating system information: {str(e)}"
    
    
