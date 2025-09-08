#!/usr/bin/env python3

import requests
import json
import sys

def test_backend_classification():
    """Test the backend classification with various inputs"""
    backend_url = "http://localhost:8888"
    
    test_cases = [
        {
            "input": "what is the largest rock",
            "expected_type": "chat",
            "description": "General knowledge question"
        },
        {
            "input": "how are you",
            "expected_type": "chat", 
            "description": "Conversational greeting"
        },
        {
            "input": "what is python",
            "expected_type": "chat",
            "description": "Informational question"
        },
        {
            "input": "find largest file",
            "expected_type": "action",
            "description": "File system command"
        },
        {
            "input": "open chrome",
            "expected_type": "action",
            "description": "Application launch command"
        },
        {
            "input": "create file notes.txt",
            "expected_type": "action",
            "description": "File creation command"
        }
    ]
    
    print("Testing Backend Classification...\n")
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['description']}")
        print(f"Input: '{test_case['input']}'")
        
        try:
            response = requests.post(
                f"{backend_url}/command",
                json={"command": test_case['input']},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                response_type = data.get('response_type', 'unknown')
                result = data.get('result', '')
                
                print(f"Response Type: {response_type}")
                print(f"Expected: {test_case['expected_type']}")
                
                if response_type == test_case['expected_type']:
                    print("✅ PASS")
                else:
                    print("❌ FAIL")
                    all_passed = False
                    
                print(f"Result Preview: {result[:100]}..." if len(result) > 100 else f"Result: {result}")
                
                # Check for JSON in response (which indicates wrong classification)
                if test_case['expected_type'] == 'chat' and ('{' in result and 'actions' in result):
                    print("❌ CRITICAL: Chat response contains JSON actions!")
                    all_passed = False
                    
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                all_passed = False
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
            all_passed = False
            
        print("-" * 50)
    
    if all_passed:
        print("\n🎉 All tests PASSED!")
        return True
    else:
        print("\n💥 Some tests FAILED!")
        return False

if __name__ == "__main__":
    success = test_backend_classification()
    sys.exit(0 if success else 1)
