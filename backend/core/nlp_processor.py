import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class NLPProcessor:
    def __init__(self):
        # Enhanced intent patterns with more variations and context awareness
        self.intent_patterns = {
            'open': [
                r'(?:open|show|display|view|access|get)\s+(.+)',
                r'(?:can\s+you\s+)?(?:open|show|pull\s+up)\s+(.+)',
                r'i\s+(?:want\s+to\s+|need\s+to\s+|would\s+like\s+to\s+)?(?:open|see|access)\s+(.+)',
                r'bring\s+up\s+(.+)',
                r'load\s+(.+)'
            ],
            'create': [
                r'(?:create|make|new|generate|setup|initialize)\s+(?:a\s+|an\s+)?(.+)',
                r'(?:can\s+you\s+)?(?:create|make|set\s+up)\s+(?:a\s+|an\s+)?(.+)',
                r'i\s+(?:want\s+to\s+|need\s+to\s+|would\s+like\s+to\s+)?(?:create|make|start)\s+(?:a\s+|an\s+)?(.+)',
                r'start\s+(?:a\s+new\s+)?(.+)',
                r'begin\s+(?:a\s+new\s+)?(.+)'
            ],
            'delete': [
                r'(?:delete|remove|rm|trash|eliminate)\s+(.+)',
                r'(?:can\s+you\s+)?(?:delete|remove|get\s+rid\s+of)\s+(.+)',
                r'i\s+(?:want\s+to\s+|need\s+to\s+|would\s+like\s+to\s+)?(?:delete|remove)\s+(.+)',
                r'clean\s+up\s+(.+)',
                r'purge\s+(.+)'
            ],
            'search': [
                r'(?:find|search|locate|look\s+for)\s+(.+)',
                r'(?:can\s+you\s+)?(?:find|search\s+for|help\s+me\s+find)\s+(.+)',
                r'(?:where\s+is|look\s+for|hunt\s+for)\s+(.+)',
                r'i\s+(?:need\s+to\s+|want\s+to\s+|would\s+like\s+to\s+)?(?:find|search\s+for)\s+(.+)',
                r'locate\s+(?:all\s+)?(.+)',
                r'show\s+me\s+(?:all\s+)?(.+)'
            ],
            'launch': [
                r'(?:launch|start|open|run|execute|boot)\s+(.+)',
                r'(?:can\s+you\s+)?(?:launch|start|fire\s+up)\s+(.+)',
                r'i\s+(?:want\s+to\s+|need\s+to\s+|would\s+like\s+to\s+)?(?:launch|start|run)\s+(.+)',
                r'get\s+(.+)\s+running',
                r'initiate\s+(.+)'
            ],
            'web_search': [
                r'(?:google|search\s+(?:web|internet|google|online))\s+(?:for\s+)?(.+)',
                r'(?:can\s+you\s+)?(?:google|search\s+(?:for|the\s+web\s+for|online\s+for))\s+(.+)',
                r'i\s+(?:want\s+to\s+|need\s+to\s+|would\s+like\s+to\s+)?(?:google|search\s+for|look\s+up)\s+(.+)',
                r'find\s+information\s+about\s+(.+)',
                r'research\s+(.+)'
            ],
            'help': [
                r'(?:help|what\s+can\s+you\s+do|capabilities|features)',
                r'(?:can\s+you\s+)?(?:help|assist|guide)\s+me',
                r'i\s+(?:need|want|would\s+like)\s+(?:help|assistance|guidance)',
                r'show\s+me\s+what\s+you\s+can\s+do',
                r'list\s+(?:your\s+)?(?:commands|abilities)'
            ],
            'time': [
                r'(?:what\s+time|time|clock|current\s+time)',
                r'(?:can\s+you\s+)?(?:tell\s+me\s+the\s+)?(?:time|current\s+time)',
                r'what\s+time\s+is\s+it',
                r'check\s+(?:the\s+)?time',
                r'display\s+(?:the\s+)?time'
            ],
            'weather': [
                r'(?:weather|temperature|forecast|conditions)',
                r'(?:what\'s\s+the\s+|how\'s\s+the\s+)?(?:weather|temperature)',
                r'(?:can\s+you\s+)?(?:check\s+the\s+)?(?:weather|forecast)',
                r'is\s+it\s+(?:hot|cold|warm|raining|sunny)',
                r'what\'s\s+it\s+like\s+outside'
            ],
            'automation': [
                r'(?:automate|schedule|repeat|run\s+periodically)\s+(.+)',
                r'(?:can\s+you\s+)?(?:automate|schedule)\s+(.+)',
                r'i\s+(?:want\s+to\s+|need\s+to\s+)?(?:automate|schedule)\s+(.+)',
                r'set\s+up\s+(?:automation|scheduled\s+task)\s+for\s+(.+)',
                r'create\s+(?:a\s+)?workflow\s+for\s+(.+)'
            ],
            'system': [
                r'(?:system|os|computer)\s+(?:status|health|info|information)',
                r'(?:check|monitor|show)\s+(?:system|computer)\s+(?:status|health)',
                r'how\s+is\s+(?:my\s+)?(?:system|computer)\s+(?:doing|performing)',
                r'show\s+(?:system|computer)\s+metrics',
                r'display\s+resource\s+usage'
            ]
        }
        
        # Enhanced entity extraction patterns
        self.entity_patterns = {
            'file_path': {
                'patterns': [
                    r'(?:\/[^\s]+|[A-Za-z]:\\[^\s]+|~\/[^\s]+)',
                    r'(?:in|at|from|to)\s+([\w\-\.]+(?:\/[\w\-\.]+)*)',
                    r'([\w\-\.]+\.[a-zA-Z0-9]+)'
                ],
                'context_hints': ['file', 'folder', 'directory', 'path', 'location']
            },
            'url': {
                'patterns': [
                    r'https?:\/\/[^\s]+',
                    r'www\.[^\s]+\.[a-z]{2,}',
                    r'(?:visit|browse|go\s+to)\s+([^\s]+\.[a-z]{2,})'
                ],
                'context_hints': ['website', 'link', 'page', 'site']
            },
            'app_name': {
                'patterns': [
                    r'(?:chrome|firefox|safari|vscode|code|terminal|finder|calculator|notes)',
                    r'(?:microsoft|google|apple)\s+([\w\-]+)',
                    r'([\w\-]+)\s+(?:app|application|program)'
                ],
                'context_hints': ['application', 'program', 'software', 'tool']
            },
            'file_extension': {
                'patterns': [
                    r'\.[a-zA-Z0-9]+$',
                    r'(?:a|an)\s+([a-z0-9]+)\s+file'
                ],
                'context_hints': ['type', 'format', 'extension']
            },
            'datetime': {
                'patterns': [
                    r'(?:today|tomorrow|yesterday)',
                    r'(?:next|last)\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
                    r'(?:in|after|before)\s+(\d+)\s+(?:minute|hour|day|week|month|year)s?',
                    r'(?:at|on)\s+(\d{1,2}(?::\d{2})?(?:\s*[ap]m)?)',
                    r'(\d{4}-\d{2}-\d{2})',
                    r'(\d{1,2}/\d{1,2}(?:/\d{2,4})?)'
                ],
                'context_hints': ['time', 'date', 'when', 'schedule']
            },
            'email': {
                'patterns': [
                    r'[\w\.-]+@[\w\.-]+\.[a-z]{2,}',
                    r'(?:send|email|mail|message)\s+to\s+([\w\.-]+@[\w\.-]+\.[a-z]{2,})'
                ],
                'context_hints': ['email', 'mail', 'address', 'contact']
            }
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
    
    def _extract_entities(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """Extract entities from text using enhanced pattern matching and context analysis.
        
        Args:
            text: The text to extract entities from
            
        Returns:
            Dictionary mapping entity types to lists of extracted entities with metadata
        """
        entities = {}
        text_lower = text.lower()
        
        for entity_type, config in self.entity_patterns.items():
            entities[entity_type] = []
            
            # Check for context hints first
            context_score = 0
            for hint in config['context_hints']:
                if hint in text_lower:
                    context_score += 0.2  # Increase confidence for each context hint
            
            # Try each pattern
            for pattern in config['patterns']:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    # Get the actual matched text
                    matched_text = match.group(1) if match.groups() else match.group(0)
                    
                    # Calculate match quality
                    match_start = match.start()
                    match_end = match.end()
                    surrounding_text = text[max(0, match_start-20):min(len(text), match_end+20)]
                    
                    # Analyze surrounding context
                    context_relevance = self._analyze_surrounding_context(
                        surrounding_text,
                        config['context_hints']
                    )
                    
                    # Calculate confidence score
                    confidence = 0.6 + context_score + context_relevance
                    if any(hint in surrounding_text.lower() for hint in config['context_hints']):
                        confidence += 0.2
                    
                    # Add metadata about the match
                    entity_info = {
                        'value': matched_text,
                        'confidence': min(1.0, confidence),
                        'start': match_start,
                        'end': match_end,
                        'surrounding_context': surrounding_text
                    }
                    
                    entities[entity_type].append(entity_info)
            
            # Sort entities by confidence
            entities[entity_type].sort(key=lambda x: x['confidence'], reverse=True)
        
        return entities
    
    def _analyze_surrounding_context(self, text: str, context_hints: List[str]) -> float:
        """Analyze text surrounding an entity match for relevance.
        
        Args:
            text: The surrounding text to analyze
            context_hints: List of context hint words
            
        Returns:
            Float score indicating context relevance (0.0 to 0.4)
        """
        text_lower = text.lower()
        score = 0.0
        
        # Check for context hints
        hint_matches = sum(1 for hint in context_hints if hint in text_lower)
        score += min(0.2, hint_matches * 0.1)
        
        # Check for prepositions that often indicate entity references
        prepositions = ['in', 'at', 'on', 'to', 'from', 'with', 'by']
        prep_matches = sum(1 for prep in prepositions if f" {prep} " in text_lower)
        score += min(0.1, prep_matches * 0.05)
        
        # Check for determiners that often precede entities
        determiners = ['the', 'this', 'that', 'these', 'those', 'my', 'your']
        det_matches = sum(1 for det in determiners if f" {det} " in text_lower)
        score += min(0.1, det_matches * 0.05)
        
        return score
    
    def _calculate_confidence(self, command: str, pattern: str) -> float:
        """Calculate confidence score for pattern match using enhanced heuristics.
        
        Args:
            command: The user's command
            pattern: The regex pattern that matched
            
        Returns:
            Float confidence score between 0.0 and 1.0
        """
        # Base confidence from pattern complexity
        pattern_complexity = len(pattern.split('|'))
        command_words = len(command.split())
        
        base_confidence = 0.7
        
        # Bonus for pattern complexity (more complex patterns are more specific)
        complexity_bonus = min(pattern_complexity * 0.05, 0.2)
        
        # Penalty for very short or very long commands
        length_penalty = 0.0
        if command_words < 2:
            length_penalty = 0.1
        elif command_words > 10:
            length_penalty = min((command_words - 10) * 0.02, 0.2)
        
        # Bonus for commands that use common action verbs
        common_verbs = ['open', 'create', 'delete', 'search', 'find', 'launch', 'run']
        verb_bonus = 0.1 if any(verb in command.lower().split() for verb in common_verbs) else 0.0
        
        # Combine scores
        confidence = base_confidence + complexity_bonus - length_penalty + verb_bonus
        
        return max(0.1, min(1.0, confidence))
    
    def _infer_intent_from_context(self, command: str, entities: Dict, context: List[Dict]) -> Dict[str, Any]:
        """Infer intent from context using enhanced analysis.
        
        Args:
            command: The user's command
            entities: Extracted entities from the command
            context: List of previous commands and their results
            
        Returns:
            Dictionary containing inferred intent information
        """
        command_lower = command.lower()
        words = command_lower.split()
        
        # Enhanced action word mapping with weights
        action_words = {
            'open': {
                'keywords': ['open', 'show', 'display', 'view', 'launch', 'access'],
                'weight': 1.0,
                'requires_target': True
            },
            'create': {
                'keywords': ['create', 'make', 'new', 'build', 'generate', 'setup'],
                'weight': 1.0,
                'requires_target': True
            },
            'delete': {
                'keywords': ['delete', 'remove', 'kill', 'close', 'trash', 'purge'],
                'weight': 1.2,  # Higher weight due to destructive nature
                'requires_target': True
            },
            'search': {
                'keywords': ['find', 'search', 'locate', 'look', 'where'],
                'weight': 0.8,
                'requires_target': True
            },
            'help': {
                'keywords': ['help', 'assist', 'support', 'guide', 'how'],
                'weight': 0.6,
                'requires_target': False
            }
        }
        
        # Score each possible intent
        intent_scores = {}
        for intent, config in action_words.items():
            score = 0.0
            
            # Check for keywords
            for keyword in config['keywords']:
                if keyword in words:
                    score += config['weight']
                    # Bonus for keyword position
                    if words.index(keyword) == 0:
                        score += 0.2
            
            # Check if required target is present
            if config['requires_target']:
                if len(words) > 1:
                    score += 0.2
                else:
                    score -= 0.5
            
            # Consider entity matches
            if entities:
                for entity_list in entities.values():
                    for entity in entity_list:
                        if entity['confidence'] > 0.7:
                            score += 0.2
            
            if score > 0:
                intent_scores[intent] = score
        
        # Check context for similar commands
        if context:
            recent_commands = [item.get('command', '') for item in context[-3:]]
            for recent in recent_commands:
                if recent and len(set(words) & set(recent.lower().split())) >= 2:
                    recent_intent = self.extract_intent(recent)
                    if recent_intent.get('action') != 'unknown':
                        intent_scores[recent_intent['action']] = intent_scores.get(
                            recent_intent['action'], 0) + 0.3
        
        # Select best intent
        if intent_scores:
            best_intent = max(intent_scores.items(), key=lambda x: x[1])
            if best_intent[1] >= 0.8:  # Confidence threshold
                # Extract target (everything after the action word)
                for keyword in action_words[best_intent[0]]['keywords']:
                    if keyword in words:
                        target_start = words.index(keyword) + 1
                        target = ' '.join(command.split()[target_start:])
                        return {
                            'action': best_intent[0],
                            'target': target,
                            'confidence': best_intent[1]
                        }
        
        return {
            'action': 'unknown',
            'target': command,
            'confidence': 0.0
        }
    
    def preprocess_command(self, command: str) -> str:
        """Preprocess command for better matching and understanding.
        
        Args:
            command: Raw command string from user
            
        Returns:
            Preprocessed command string
        """
        # Remove extra whitespace and normalize spaces
        command = ' '.join(command.split())
        
        # Convert to lowercase for consistent matching
        command = command.lower()
        
        # Remove punctuation at the end of sentences
        command = command.rstrip('.!?')
        
        # Normalize common contractions
        contractions = {
            "won't": "will not",
            "can't": "cannot",
            "don't": "do not",
            "i'm": "i am",
            "i'll": "i will",
            "i've": "i have",
            "let's": "let us",
            "that's": "that is",
            "what's": "what is",
            "where's": "where is",
            "it's": "it is",
            "isn't": "is not",
            "aren't": "are not",
            "wasn't": "was not",
            "weren't": "were not",
            "haven't": "have not",
            "hasn't": "has not",
            "hadn't": "had not",
            "doesn't": "does not",
            "didn't": "did not",
            "shouldn't": "should not",
            "wouldn't": "would not",
            "couldn't": "could not",
            "mustn't": "must not",
            "might've": "might have",
            "must've": "must have",
            "should've": "should have",
            "could've": "could have",
            "would've": "would have"
        }
        
        for contraction, expansion in contractions.items():
            command = command.replace(contraction, expansion)
        
        # Normalize common synonyms and variations
        synonyms = {
            r'\bdel\b': 'delete',
            r'\brm\b': 'delete',
            r'\bremove\b': 'delete',
            r'\btrash\b': 'delete',
            r'\bfind\b': 'search',
            r'\blocate\b': 'search',
            r'\blook\s+for\b': 'search',
            r'\bshow\b': 'display',
            r'\bview\b': 'display',
            r'\brun\b': 'execute',
            r'\bstart\b': 'execute',
            r'\bbegin\b': 'execute',
            r'\blaunch\b': 'execute',
            r'\bmail\b': 'email',
            r'\bmessage\b': 'email',
            r'\bapp\b': 'application',
            r'\bdir\b': 'directory',
            r'\bfolder\b': 'directory'
        }
        
        for pattern, replacement in synonyms.items():
            command = re.sub(pattern, replacement, command)
        
        # Normalize file paths
        command = re.sub(r'\\+', '/', command)  # Convert backslashes to forward slashes
        command = re.sub(r'/+', '/', command)    # Normalize multiple slashes
        
        return command
    
    def get_suggestions(self, partial_command: str, context: List[Dict] = None) -> List[Dict[str, Any]]:
        """Get intelligent command suggestions based on partial input and context.
        
        Args:
            partial_command: Partial command from user
            context: Optional list of recent commands and their results
            
        Returns:
            List of suggestion dictionaries with template and description
        """
        suggestions = []
        partial_command = partial_command.lower()
        context = context or []
        
        # Command templates with descriptions and examples
        templates = [
            {
                'template': 'open {app}',
                'description': 'Open an application',
                'examples': ['open chrome', 'open terminal', 'open vscode'],
                'category': 'application'
            },
            {
                'template': 'create {file_type} {name}',
                'description': 'Create a new file or directory',
                'examples': ['create file report.txt', 'create directory projects', 'create python script'],
                'category': 'file'
            },
            {
                'template': 'search for {query}',
                'description': 'Search files or content',
                'examples': ['search for todo.txt', 'search for python files', 'search for "error log"'],
                'category': 'search'
            },
            {
                'template': 'delete {file}',
                'description': 'Delete a file or directory',
                'examples': ['delete temp.txt', 'delete old_folder', 'delete *.log'],
                'category': 'file'
            },
            {
                'template': 'web search {query}',
                'description': 'Search the web',
                'examples': ['web search python tutorials', 'web search current weather', 'web search news'],
                'category': 'web'
            },
            {
                'template': 'email to {recipient} about {subject}',
                'description': 'Compose an email',
                'examples': ['email to john@example.com about meeting', 'email to team about update'],
                'category': 'communication'
            },
            {
                'template': 'automate {task} every {interval}',
                'description': 'Create automated task',
                'examples': ['automate backup every day', 'automate report every monday'],
                'category': 'automation'
            },
            {
                'template': 'system {action}',
                'description': 'Perform system operations',
                'examples': ['system status', 'system cleanup', 'system update'],
                'category': 'system'
            }
        ]
        
        # Add context-aware suggestions
        if context:
            recent_categories = []
            for cmd in context[-3:]:
                intent = self.extract_intent(cmd.get('command', ''), [])
                if intent['action'] != 'unknown':
                    recent_categories.append(intent['action'])
            
            # Prioritize templates from recently used categories
            templates.sort(key=lambda x: x['category'] in recent_categories, reverse=True)
        
        # Filter and score suggestions
        for template in templates:
            score = 0
            
            # Check if partial command matches template or examples
            if partial_command in template['template'].lower():
                score += 0.5
            
            for example in template['examples']:
                if partial_command in example.lower():
                    score += 0.3
                    break
            
            if partial_command in template['description'].lower():
                score += 0.2
            
            if score > 0:
                suggestion = template.copy()
                suggestion['score'] = score
                suggestions.append(suggestion)
        
        # Sort by score and limit results
        suggestions.sort(key=lambda x: x['score'], reverse=True)
        return suggestions[:5]
