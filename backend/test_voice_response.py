#!/usr/bin/env python3
"""
Test script to debug voice response issues.
Tests the voice synthesizer and response flow directly.
"""

import asyncio
import logging
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from voice.voice_synthesizer import VoiceSynthesizer
from voice.voice_manager import VoiceManager
from voice.voice_processor import VoiceProcessor
from voice.voice_classifier import VoiceClassifier

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_voice_synthesizer():
    """Test the voice synthesizer directly."""
    print("🎤 Testing Voice Synthesizer...")
    
    synthesizer = VoiceSynthesizer()
    
    # Initialize
    success = await synthesizer.initialize()
    print(f"✅ Synthesizer initialized: {success}")
    
    if success:
        # Test speaking
        print("🔊 Testing speech output...")
        await synthesizer.speak("Hello! This is a test of the voice synthesizer. Can you hear me?")
        
        # Wait for speech to complete
        await asyncio.sleep(3)
        
        print(f"📊 Synthesizer status: {synthesizer.status}")
    
    await synthesizer.stop()
    return success

async def test_voice_processor():
    """Test the voice processor for chat responses."""
    print("\n🧠 Testing Voice Processor...")
    
    processor = VoiceProcessor()
    await processor.initialize()
    
    # Test chat classification
    classification = {
        'type': 'chat',
        'confidence': 0.5,
        'category': None,
        'keywords': ['hello'],
        'original_text': 'hello how are you doing today'
    }
    
    response = await processor.process('hello how are you doing today', classification)
    print(f"💬 Generated response: {response}")
    
    return response is not None

async def test_full_voice_flow():
    """Test the complete voice flow."""
    print("\n🔄 Testing Full Voice Flow...")
    
    # Initialize components
    synthesizer = VoiceSynthesizer()
    classifier = VoiceClassifier()
    processor = VoiceProcessor()
    
    await synthesizer.initialize()
    await processor.initialize()
    
    # Test the flow
    text = "hello how are you doing today"
    
    # 1. Classify
    classification = await classifier.classify(text)
    print(f"🏷️  Classification: {classification}")
    
    # 2. Process
    response = await processor.process(text, classification)
    print(f"💭 Response: {response}")
    
    # 3. Speak
    if response:
        print("🔊 Speaking response...")
        await synthesizer.speak(response)
        await asyncio.sleep(4)  # Wait for speech
    
    await synthesizer.stop()
    return response is not None

async def test_voice_manager():
    """Test the voice manager's speak_response method."""
    print("\n🎯 Testing Voice Manager...")
    
    manager = VoiceManager()
    success = await manager.activate()
    print(f"✅ Voice manager activated: {success}")
    
    if success:
        print("🔊 Testing speak_response...")
        await manager.speak_response("Hello! This is a test of the voice manager's speak response method.")
        await asyncio.sleep(4)  # Wait for speech
    
    await manager.deactivate()
    return success

async def main():
    """Run all voice tests."""
    print("🚀 Starting Voice Response Debug Tests\n")
    
    results = {}
    
    try:
        # Test 1: Voice Synthesizer
        results['synthesizer'] = await test_voice_synthesizer()
        
        # Test 2: Voice Processor
        results['processor'] = await test_voice_processor()
        
        # Test 3: Full Voice Flow
        results['full_flow'] = await test_full_voice_flow()
        
        # Test 4: Voice Manager
        results['voice_manager'] = await test_voice_manager()
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    # Summary
    print("\n📊 Test Results Summary:")
    print("=" * 40)
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:15} : {status}")
    
    all_passed = all(results.values())
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if not all_passed:
        print("\n🔍 Debugging Tips:")
        if not results.get('synthesizer'):
            print("- Voice synthesizer failed - check macOS TTS permissions")
        if not results.get('processor'):
            print("- Voice processor failed - check AI response generation")
        if not results.get('voice_manager'):
            print("- Voice manager failed - check component initialization")

if __name__ == "__main__":
    asyncio.run(main())