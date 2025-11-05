"""
Voice functionality module for Apex AI Assistant.

This module provides comprehensive voice interaction capabilities including:
- Voice recognition and continuous listening
- AI-powered command classification
- Text-to-speech response generation
- Integration with existing backend systems
"""

from .voice_manager import VoiceManager
from .voice_recognizer import VoiceRecognizer
from .voice_classifier import VoiceClassifier
from .voice_synthesizer import VoiceSynthesizer

__all__ = ['VoiceManager', 'VoiceRecognizer', 'VoiceClassifier', 'VoiceSynthesizer']