"""
Voice Command Classifier for Apex AI Assistant.

Uses AI to classify voice input into different command types:
- chat: General conversation
- action: System actions (file operations, app control, etc.)
- web_search: Web search requests
"""

import logging
import re
from typing import Dict, Any, List
import asyncio

logger = logging.getLogger(__name__)

class VoiceClassifier:
    """AI-powered classifier for voice commands."""
    
    def __init__(self):
        self.action_keywords = {
            'file_operations': [
                'open', 'create', 'delete', 'move', 'copy', 'rename', 'save',
                'file', 'folder', 'directory', 'document'
            ],
            'app_control': [
                'launch', 'start', 'quit', 'close', 'switch to', 'open app',
                'application', 'program', 'software'
            ],
            'system_control': [
                'screenshot', 'volume', 'brightness', 'wifi', 'bluetooth',
                'settings', 'preferences', 'system'
            ],
            'automation': [
                'automate', 'script', 'run', 'execute', 'perform', 'do'
            ]
        }
        
        self.search_keywords = [
            'search', 'find', 'look up', 'google', 'what is', 'who is',
            'how to', 'when did', 'where is', 'why', 'tell me about',
            'information about', 'learn about'
        ]
        
        self.chat_indicators = [
            'hello', 'hi', 'hey', 'thanks', 'thank you', 'please',
            'can you', 'would you', 'could you', 'i need', 'help me'
        ]
        
        logger.info("VoiceClassifier initialized")
    
    async def classify(self, text: str) -> Dict[str, Any]:
        """
        Classify voice input into command type.
        
        Returns:
            Dict with 'type', 'confidence', 'category', and 'keywords'
        """
        text_lower = text.lower().strip()
        
        # Calculate scores for each type
        action_score = self._calculate_action_score(text_lower)
        search_score = self._calculate_search_score(text_lower)
        chat_score = self._calculate_chat_score(text_lower)
        
        # Determine the classification
        scores = {
            'action': action_score,
            'web_search': search_score,
            'chat': chat_score
        }
        
        # Get the highest scoring type
        classified_type = max(scores, key=scores.get)
        confidence = scores[classified_type]
        
        # If confidence is too low, default to chat
        if confidence < 0.3:
            classified_type = 'chat'
            confidence = 0.5
        
        # Get additional details
        category = self._get_action_category(text_lower) if classified_type == 'action' else None
        keywords = self._extract_keywords(text_lower, classified_type)
        
        result = {
            'type': classified_type,
            'confidence': confidence,
            'category': category,
            'keywords': keywords,
            'original_text': text,
            'scores': scores
        }
        
        logger.debug(f"Classification result: {result}")
        return result
    
    def _calculate_action_score(self, text: str) -> float:
        """Calculate score for action classification."""
        score = 0.0
        total_keywords = 0
        
        for category, keywords in self.action_keywords.items():
            for keyword in keywords:
                total_keywords += 1
                if keyword in text:
                    # Give higher weight to exact matches
                    if f" {keyword} " in f" {text} ":
                        score += 1.0
                    else:
                        score += 0.5
        
        # Action patterns
        action_patterns = [
            r'\b(open|launch|start|run)\s+\w+',
            r'\b(create|make|new)\s+\w+',
            r'\b(delete|remove)\s+\w+',
            r'\b(take|capture)\s+(screenshot|photo)',
            r'\b(set|change|adjust)\s+\w+',
        ]
        
        for pattern in action_patterns:
            if re.search(pattern, text):
                score += 2.0
        
        # Normalize score
        max_possible = len(self.action_keywords) * 2 + len(action_patterns) * 2
        return min(score / max_possible, 1.0) if max_possible > 0 else 0.0
    
    def _calculate_search_score(self, text: str) -> float:
        """Calculate score for web search classification."""
        score = 0.0
        
        # Direct search keywords
        for keyword in self.search_keywords:
            if keyword in text:
                if f" {keyword} " in f" {text} ":
                    score += 1.0
                else:
                    score += 0.5
        
        # Question patterns
        question_patterns = [
            r'^\s*(what|who|when|where|why|how)\s+',
            r'\?\s*$',
            r'\b(tell me|show me|find)\s+',
            r'\b(information|details|facts)\s+about\b',
        ]
        
        for pattern in question_patterns:
            if re.search(pattern, text):
                score += 1.5
        
        # Normalize score
        max_possible = len(self.search_keywords) + len(question_patterns) * 1.5
        return min(score / max_possible, 1.0) if max_possible > 0 else 0.0
    
    def _calculate_chat_score(self, text: str) -> float:
        """Calculate score for chat classification."""
        score = 0.0
        
        # Chat indicators
        for indicator in self.chat_indicators:
            if indicator in text:
                score += 1.0
        
        # Conversational patterns
        chat_patterns = [
            r'^\s*(hello|hi|hey|good\s+(morning|afternoon|evening))',
            r'\b(please|thank you|thanks)\b',
            r'\b(i\s+(think|feel|believe|want|need))\b',
            r'\b(can you|could you|would you)\b',
        ]
        
        for pattern in chat_patterns:
            if re.search(pattern, text):
                score += 1.0
        
        # Length factor (longer texts are more likely to be chat)
        word_count = len(text.split())
        if word_count > 10:
            score += 0.5
        
        # Normalize score
        max_possible = len(self.chat_indicators) + len(chat_patterns) + 0.5
        return min(score / max_possible, 1.0) if max_possible > 0 else 0.0
    
    def _get_action_category(self, text: str) -> str:
        """Get the specific action category."""
        category_scores = {}
        
        for category, keywords in self.action_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                category_scores[category] = score
        
        if category_scores:
            return max(category_scores, key=category_scores.get)
        return 'general'
    
    def _extract_keywords(self, text: str, command_type: str) -> List[str]:
        """Extract relevant keywords based on command type."""
        keywords = []
        
        if command_type == 'action':
            for category, kw_list in self.action_keywords.items():
                keywords.extend([kw for kw in kw_list if kw in text])
        elif command_type == 'web_search':
            keywords.extend([kw for kw in self.search_keywords if kw in text])
        elif command_type == 'chat':
            keywords.extend([kw for kw in self.chat_indicators if kw in text])
        
        return list(set(keywords))  # Remove duplicates
    
    def add_custom_keywords(self, command_type: str, keywords: List[str]):
        """Add custom keywords for better classification."""
        if command_type == 'action':
            if 'custom' not in self.action_keywords:
                self.action_keywords['custom'] = []
            self.action_keywords['custom'].extend(keywords)
        elif command_type == 'search':
            self.search_keywords.extend(keywords)
        elif command_type == 'chat':
            self.chat_indicators.extend(keywords)
        
        logger.info(f"Added custom keywords for {command_type}: {keywords}")
    
    async def learn_from_feedback(self, text: str, correct_type: str):
        """Learn from user feedback to improve classification."""
        # This could be enhanced with machine learning in the future
        logger.info(f"Learning feedback: '{text}' should be classified as '{correct_type}'")
        # For now, we could store this for future training