#!/usr/bin/env python3

import sys
import os
sys.path.append('/Users/romirpatel/apx/backend')

from core.tool_testing_framework import ToolTestingFramework
from core.security_manager import SecurityManager
import importlib.util

def test_qr_tool():
    print("🔍 Testing QR Code Tool with Adaptive Framework")
    print("=" * 50)
    
    # Initialize testing framework
    security_manager = SecurityManager()
    testing_framework = ToolTestingFramework(security_manager)
    
    # Load the QR code tool
    tool_path = '/Users/romirpatel/apx/backend/generated_capabilities/custom_tool_20250910_201404.py'
    
    spec = importlib.util.spec_from_file_location("custom_tool_20250910_201404", tool_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # Get the class
    tool_class = getattr(module, 'QRCodeGenerator')
    tool_instance = tool_class()
    
    print(f"✅ Tool loaded: {tool_class.__name__}")
    print(f"📋 Available methods: {[method for method in dir(tool_instance) if not method.startswith('_')]}")
    
    # Create test suite
    user_request = "Create a QR code for https://github.com/traehq/trae and save it as github_final_test.png on my Desktop"
    test_suite = testing_framework.create_test_suite('custom', user_request)
    
    print(f"\n🧪 Created test suite with {len(test_suite)} tests:")
    for i, test in enumerate(test_suite):
        print(f"  {i+1}. {test['name']}: {test['description']}")
    
    # Run tests
    print("\n🚀 Running tests...")
    results = testing_framework.run_test_suite(tool_instance, test_suite, "custom_tool_20250910_201404")
    
    print(f"\n📊 Test Results:")
    print(f"  Total tests: {results['total_tests']}")
    print(f"  Passed: {results['passed']}")
    print(f"  Failed: {results['failed']}")
    print(f"  Success rate: {results['success_rate']:.2%}")
    print(f"  Overall success: {results['overall_success']}")
    
    print("\n📝 Detailed results:")
    for result in results['test_results']:
        status = "✅ PASS" if result['passed'] else "❌ FAIL"
        print(f"  {status} {result['name']}: {result['description']}")
        if result['output']:
            print(f"    Output: {result['output']}")
        if result['error']:
            print(f"    Error: {result['error']}")
    
    return results['overall_success']

if __name__ == '__main__':
    success = test_qr_tool()
    print(f"\n🏁 Final result: {'SUCCESS' if success else 'FAILURE'}")
    sys.exit(0 if success else 1)