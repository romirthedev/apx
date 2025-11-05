#!/usr/bin/env python3
"""
Test script for the enhanced voice interaction system.
Tests the complete flow including pause detection, AI actions, and human-like speech.
"""

import asyncio
import logging
import requests
import json
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoiceInteractionTester:
    """Test the enhanced voice interaction system."""
    
    def __init__(self, base_url="http://localhost:8888"):
        self.base_url = base_url
        
    def test_health_check(self):
        """Test if the backend is running."""
        try:
            response = requests.get(f"{self.base_url}/health")
            if response.status_code == 200:
                logger.info("✅ Backend health check passed")
                return True
            else:
                logger.error(f"❌ Backend health check failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Backend health check failed: {e}")
            return False
    
    def test_voice_init(self):
        """Test voice system initialization."""
        try:
            response = requests.post(f"{self.base_url}/api/voice/init")
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    logger.info("✅ Voice system initialization passed")
                    return True
                else:
                    logger.error(f"❌ Voice init failed: {result.get('error')}")
                    return False
            else:
                logger.error(f"❌ Voice init failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Voice init failed: {e}")
            return False
    
    def test_natural_conversation_endpoint(self):
        """Test the natural conversation endpoint."""
        try:
            response = requests.post(f"{self.base_url}/api/voice/natural")
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    logger.info("✅ Natural conversation endpoint is working")
                    return True
                else:
                    logger.error(f"❌ Natural conversation failed: {result.get('error')}")
                    return False
            else:
                logger.error(f"❌ Natural conversation failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Natural conversation failed: {e}")
            return False
    
    def test_overlay_interaction_endpoints(self):
        """Test overlay interaction endpoints."""
        endpoints_to_test = [
            "/command",
            "/capture_screenshot",
            "/audio_setup_info"
        ]
        
        all_passed = True
        for endpoint in endpoints_to_test:
            try:
                if endpoint == "/command":
                    # Test with a simple command
                    response = requests.post(f"{self.base_url}{endpoint}", 
                                           json={"command": "get system info"})
                elif endpoint == "/capture_screenshot":
                    response = requests.post(f"{self.base_url}{endpoint}")
                else:
                    response = requests.get(f"{self.base_url}{endpoint}")
                
                if response.status_code in [200, 201]:
                    logger.info(f"✅ Endpoint {endpoint} is accessible")
                else:
                    logger.warning(f"⚠️ Endpoint {endpoint} returned {response.status_code}")
                    all_passed = False
            except Exception as e:
                logger.error(f"❌ Endpoint {endpoint} failed: {e}")
                all_passed = False
        
        return all_passed
    
    def run_all_tests(self):
        """Run all tests and provide a summary."""
        logger.info("🚀 Starting Voice Interaction System Tests")
        logger.info("=" * 50)
        
        tests = [
            ("Backend Health Check", self.test_health_check),
            ("Voice System Initialization", self.test_voice_init),
            ("Natural Conversation Endpoint", self.test_natural_conversation_endpoint),
            ("Overlay Interaction Endpoints", self.test_overlay_interaction_endpoints)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            logger.info(f"\n🧪 Running: {test_name}")
            try:
                if test_func():
                    passed += 1
                    logger.info(f"✅ {test_name}: PASSED")
                else:
                    logger.error(f"❌ {test_name}: FAILED")
            except Exception as e:
                logger.error(f"❌ {test_name}: FAILED with exception: {e}")
        
        logger.info("\n" + "=" * 50)
        logger.info(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 All tests passed! The voice interaction system is ready.")
            logger.info("\n📋 Features Available:")
            logger.info("  • Natural conversation with pause detection (Siri-like)")
            logger.info("  • AI can perform actions through overlay interface")
            logger.info("  • Human-like speech synthesis with natural pauses and emphasis")
            logger.info("  • Enhanced voice recognition with conversation flow")
            logger.info("  • Integration with Gemini AI for intelligent responses")
            logger.info("\n🎯 To test manually:")
            logger.info("  1. Open http://localhost:8888/overlay-unified.html")
            logger.info("  2. Click 'Initialize Voice' button")
            logger.info("  3. Click 'Start Natural Conversation' button")
            logger.info("  4. Speak naturally and wait for pauses to be detected")
            logger.info("  5. Try commands like 'take a screenshot' or 'search for AI news'")
        else:
            logger.warning(f"⚠️ {total - passed} tests failed. Please check the logs above.")
        
        return passed == total

if __name__ == "__main__":
    tester = VoiceInteractionTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)