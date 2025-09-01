import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class NLPProcessor:
    def __init__(self):
        # Intent patterns for natural language understanding
        self.intent_patterns = {
            'open': [
                r'(?:open|show|display|view)\s+(.+)',
                r'(?:can\s+you\s+)?(?:open|show)\s+(.+)',
                r'i\s+(?:want\s+to\s+|need\s+to\s+)?(?:open|see)\s+(.+)'
            ],
            'create': [
                r'(?:create|make|new)\s+(.+)',
                r'(?:can\s+you\s+)?(?:create|make)\s+(.+)',
                r'i\s+(?:want\s+to\s+|need\s+to\s+)?(?:create|make)\s+(.+)'
            ],
            'delete': [
                r'(?:delete|remove|rm)\s+(.+)',
                r'(?:can\s+you\s+)?(?:delete|remove)\s+(.+)',
                r'i\s+(?:want\s+to\s+|need\s+to\s+)?(?:delete|remove)\s+(.+)'
            ],
            'search': [
                r'(?:find|search|locate)\s+(.+)',
                r'(?:can\s+you\s+)?(?:find|search\s+for)\s+(.+)',
                r'(?:where\s+is|look\s+for)\s+(.+)',
                r'i\s+(?:need\s+to\s+|want\s+to\s+)?(?:find|search\s+for)\s+(.+)'
            ],
            'launch': [
                r'(?:launch|start|open|run)\s+(.+)',
                r'(?:can\s+you\s+)?(?:launch|start|open)\s+(.+)',
                r'i\s+(?:want\s+to\s+|need\s+to\s+)?(?:launch|start|open)\s+(.+)'
            ],
            'web_search': [
                r'(?:google|search\s+(?:web|internet|google))\s+(.+)',
                r'(?:can\s+you\s+)?(?:google|search\s+(?:for|the\s+web\s+for))\s+(.+)',
                r'i\s+(?:want\s+to\s+|need\s+to\s+)?(?:google|search\s+for)\s+(.+)'
            ],
            'help': [
                r'(?:help|what\s+can\s+you\s+do|capabilities)',
                r'(?:can\s+you\s+)?help\s+me',
                r'i\s+need\s+help'
            ],
            'time': [
                r'(?:what\s+time|time|clock|current\s+time)',
                r'(?:can\s+you\s+)?(?:tell\s+me\s+the\s+)?time',
                r'what\s+time\s+is\s+it'
            ],
            'weather': [
                r'(?:weather|temperature|forecast)',
                r'(?:what\'s\s+the\s+|how\'s\s+the\s+)?weather',
                r'(?:can\s+you\s+)?(?:check\s+the\s+)?weather'
            ]
        }
        
        # Entity extraction patterns
        self.entity_patterns = {
            'file_path': r'(?:\/[^\s]+|[A-Za-z]:\\[^\s]+|~\/[^\s]+)',
            'url': r'https?:\/\/[^\s]+',
            'app_name': r'(?:chrome|firefox|safari|vscode|code|terminal|finder|calculator|notes)',
            'file_extension': r'\.[a-zA-Z0-9]+$'
        }
    
    def extract_intent(self, command: str, context: List[Dict] = None) -> Dict[str, Any]:
        """Extract intent and entities from natural language command."""
        command = command.strip().lower()
        context = context or []
        
        # Try to match intent patterns
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, command)
                if match:
                    target = match.group(1).strip() if match.groups() else ""
                    
                    # Extract entities from the target
                    entities = self._extract_entities(target)
                    
                    return {
                        'action': intent,
                        'target': target,
                        'entities': entities,
                        'confidence': self._calculate_confidence(command, pattern),
                        'original_command': command
                    }
        
        # If no intent matched, try to extract key information
        entities = self._extract_entities(command)
        
        # Try to infer intent from entities and context
        inferred_intent = self._infer_intent_from_context(command, entities, context)
        
        return {
            'action': inferred_intent.get('action', 'unknown'),
            'target': inferred_intent.get('target', ''),
            'entities': entities,
            'confidence': 0.5,
            'original_command': command
        }
    
    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract entities from text using regex patterns."""
        entities = {}
        
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                entities[entity_type] = matches
        
        return entities
    
    def _calculate_confidence(self, command: str, pattern: str) -> float:
        """Calculate confidence score for pattern match."""
        # Simple confidence calculation based on pattern complexity
        # and command length
        pattern_complexity = len(pattern.split('|'))
        command_words = len(command.split())
        
        base_confidence = 0.8
        complexity_bonus = min(pattern_complexity * 0.05, 0.15)
        length_penalty = max(0, (command_words - 5) * 0.02)
        
        confidence = base_confidence + complexity_bonus - length_penalty
        return max(0.1, min(1.0, confidence))
    
    def _infer_intent_from_context(self, command: str, entities: Dict, context: List[Dict]) -> Dict[str, Any]:
        """Infer intent from context when no pattern matches."""
        # Look for action words in the command
        action_words = {
            'open': ['open', 'show', 'display', 'view', 'launch'],
            'create': ['create', 'make', 'new', 'build'],
            'delete': ['delete', 'remove', 'kill', 'close'],
            'search': ['find', 'search', 'locate', 'look'],
            'help': ['help', 'assist', 'support']
        }
        
        words = command.split()
        
        for intent, keywords in action_words.items():
            for keyword in keywords:
                if keyword in words:
                    # Find the target (usually the words after the action)
                    try:
                        keyword_index = words.index(keyword)
                        target_words = words[keyword_index + 1:]
                        target = ' '.join(target_words)
                        
                        return {
                            'action': intent,
                            'target': target
                        }
                    except (ValueError, IndexError):
                        pass
        
        # Check recent context for similar commands
        if context:
            recent_commands = [item.get('command', '') for item in context[-3:]]
            for recent in recent_commands:
                if len(set(command.split()) & set(recent.split())) >= 2:
                    # Similar command found in context
                    recent_intent = self.extract_intent(recent)
                    if recent_intent.get('action') != 'unknown':
                        return {
                            'action': recent_intent.get('action'),
                            'target': command  # Use current command as target
                        }
        
        return {
            'action': 'unknown',
            'target': command
        }
    
    def preprocess_command(self, command: str) -> str:
        """Preprocess command text for better understanding."""
        # Convert to lowercase
        command = command.lower().strip()
        
        # Remove common filler words
        filler_words = ['please', 'can you', 'could you', 'would you', 'i want to', 'i need to']
        for filler in filler_words:
            command = re.sub(r'\b' + re.escape(filler) + r'\b', '', command)
        
        # Clean up extra spaces
        command = re.sub(r'\s+', ' ', command).strip()
        
        return command
    
    def get_suggestions(self, partial_command: str) -> List[str]:
        """Get command suggestions based on partial input."""
        suggestions = []
        
        # Common command templates
        templates = [
            "open {file_or_app}",
            "create file {filename}",
            "search for {query}",
            "delete {file_or_folder}",
            "launch {app_name}",
            "google {search_query}",
            "what time is it",
            "show weather",
            "help"
        ]
        
        partial_lower = partial_command.lower()
        
        for template in templates:
            if any(word in template for word in partial_lower.split()):
                suggestions.append(template)
        
        return suggestions[:5]  # Return top 5 suggestions
