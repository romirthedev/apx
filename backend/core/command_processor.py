import re
import json
import logging
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
            (r'(?:show|get|display)\s+(?:system\s+)?(?:info|information|status)', self._handle_system_info),
            (r'(?:what\s+time|time|clock)', self._handle_time),
            (r'(?:weather|temperature)', self._handle_weather),
            (r'(?:show|list)\s+(?:running\s+)?processes', self._handle_running_processes),
            (r'(?:what|which)\s+(?:app|application|program)s?\s+(?:take|use|consume)s?\s+(?:the\s+)?most\s+(?:space|disk|storage)', self._handle_largest_apps),
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
            
            # Web operations
            (r'(?:search\s+(?:web|google|internet)\s+(?:for\s+)?|google\s+)(.+)', self._handle_web_search),
            (r'(?:browse|visit|go\s+to)\s+(.+)', self._handle_browse_url),
            (r'(?:download|get)\s+(.+)', self._handle_download),
            
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
            
            # Check security permissions
            if not self._check_command_security(command):
                return {
                    'success': False,
                    'result': 'Permission denied. This command requires elevated privileges.',
                    'metadata': {'security_blocked': True}
                }
            
            # First try rule-based pattern matching for direct system commands
            for pattern, handler in self.command_patterns:
                match = re.search(pattern, command)
                if match:
                    try:
                        result = handler(*match.groups(), context=context)
                        return {
                            'success': True,
                            'result': result,
                            'metadata': {'handler': handler.__name__, 'pattern': pattern, 'method': 'rule_based'}
                        }
                    except Exception as e:
                        logger.error(f"Handler {handler.__name__} failed: {str(e)}")
                        # Continue to AI processing if rule-based fails
                        break
            
            # If no pattern matched or rule-based failed, try AI processing
            if self.gemini_ai:
                try:
                    # Check if this command should use AI
                    if self.gemini_ai.should_use_ai(original_command):
                        ai_response = self.gemini_ai.generate_response(
                            original_command, 
                            context, 
                            self.get_available_actions()
                        )
                        
                        if ai_response.get('success'):
                            # If AI suggests specific actions, try to execute them
                            if ai_response.get('requires_action') and ai_response.get('suggested_actions'):
                                action_results = []
                                for action in ai_response['suggested_actions']:
                                    action_result = self._execute_ai_suggested_action(action, original_command)
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
                    
                    # Try AI-enhanced command understanding for ambiguous commands
                    understanding = self.gemini_ai.enhance_command_understanding(original_command)
                    if understanding.get('success') and understanding['understanding']['confidence'] > 0.7:
                        intent_data = understanding['understanding']
                        result = self._execute_intent(intent_data, context)
                        if result:
                            return {
                                'success': True,
                                'result': result,
                                'metadata': {'method': 'ai_understanding', 'intent': intent_data}
                            }
                    
                except Exception as e:
                    logger.error(f"AI processing failed: {str(e)}")
                    # Fall back to NLP processing
            
            # Fall back to original NLP processing
            try:
                intent = self.nlp_processor.extract_intent(command, context)
                result = self._handle_intent(intent, context)
                return {
                    'success': True,
                    'result': result,
                    'metadata': {'nlp_intent': intent, 'method': 'nlp_fallback'}
                }
            except Exception as e:
                logger.error(f"NLP processing failed: {str(e)}")
                
                # Final fallback: AI help if available
                if self.gemini_ai:
                    help_response = self.gemini_ai.get_contextual_help(original_command, self.get_available_actions())
                    return {
                        'success': True,
                        'result': help_response,
                        'metadata': {'method': 'ai_help'}
                    }
                
                return {
                    'success': False,
                    'result': "I couldn't understand that command. Try being more specific or use 'help' to see what I can do.",
                    'metadata': {'nlp_error': str(e), 'method': 'fallback'}
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
    
    def _handle_browse_url(self, url: str, context: List[Dict] = None) -> str:
        """Handle URL browsing commands."""
        return self.plugins['web_controller'].browse_url(url)
    
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
            
            if action_type == 'file_create':
                # Extract filename from original command
                import re
                filename_match = re.search(r'(?:create|make|new)\s+(?:file\s+)?(\S+)', original_command)
                if filename_match:
                    filename = filename_match.group(1)
                    return self.plugins['file_manager'].create_file(filename)
            
            elif action_type == 'app_launch':
                app_match = re.search(r'(?:launch|open|start)\s+(\w+)', original_command)
                if app_match:
                    app_name = app_match.group(1)
                    return self.plugins['app_controller'].launch_app(app_name)
            
            elif action_type == 'web_search':
                search_match = re.search(r'(?:search|google)\s+(?:for\s+)?(.+)', original_command)
                if search_match:
                    query = search_match.group(1)
                    return self.plugins['web_controller'].search_web(query)
            
            elif action_type == 'system_info':
                return self.plugins['system_info'].get_system_info()
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to execute AI suggested action: {str(e)}")
            return None
    
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
