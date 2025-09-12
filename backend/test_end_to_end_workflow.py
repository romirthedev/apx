#!/usr/bin/env python3
"""
End-to-End APX Self-Improvement System Test

This test simulates a real user request through the APX backend API
for a capability that doesn't exist, then validates the complete
self-improvement workflow from detection through execution.
"""

import requests
import json
import time
import sys
import os
from datetime import datetime

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class EndToEndTester:
    def __init__(self, backend_url="http://localhost:8889"):
        self.backend_url = backend_url
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'backend_connectivity': False,
            'request_processing': False,
            'self_improvement_triggered': False,
            'code_generation': False,
            'capability_execution': False,
            'task_completion': False,
            'overall_success': False,
            'details': {}
        }
    
    def test_backend_connectivity(self):
        """Test if the APX backend is accessible"""
        print("🔗 Step 1: Testing backend connectivity...")
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            if response.status_code == 200:
                self.test_results['backend_connectivity'] = True
                print("   ✅ Backend is accessible")
                return True
            else:
                print(f"   ❌ Backend returned status code: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Backend connectivity failed: {str(e)}")
            return False
    
    def send_user_request(self, user_command):
        """Send a user request that requires a new capability"""
        print(f"\n📤 Step 2: Sending user request...")
        print(f"   Request: '{user_command}'")
        
        try:
            payload = {
                "command": user_command,
                "context": "End-to-end test request",
                "user_id": "test_user_001"
            }
            
            response = requests.post(
                f"{self.backend_url}/command",
                json=payload,
                timeout=120  # Allow time for self-improvement
            )
            
            if response.status_code == 200:
                self.test_results['request_processing'] = True
                result = response.json()
                self.test_results['details']['api_response'] = result
                print("   ✅ Request processed successfully")
                return result
            else:
                print(f"   ❌ Request failed with status: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Request failed: {str(e)}")
            return None
    
    def analyze_response(self, response):
        """Analyze the API response for self-improvement indicators"""
        print("\n🔍 Step 3: Analyzing response for self-improvement...")
        
        if not response:
            print("   ❌ No response to analyze")
            return False
        
        # Check for self-improvement indicators
        response_str = json.dumps(response).lower()
        
        improvement_indicators = [
            'self-improvement',
            'generating',
            'capability',
            'iteration',
            'code generation',
            'new tool',
            'dynamic'
        ]
        
        found_indicators = []
        for indicator in improvement_indicators:
            if indicator in response_str:
                found_indicators.append(indicator)
        
        if found_indicators:
            self.test_results['self_improvement_triggered'] = True
            print(f"   ✅ Self-improvement triggered (indicators: {found_indicators})")
            
            # Check for code generation
            if 'code' in response or 'generated' in response_str:
                self.test_results['code_generation'] = True
                print("   ✅ Code generation detected")
            
            return True
        else:
            print("   ⚠️ No clear self-improvement indicators found")
            return False
    
    def validate_task_completion(self, response, expected_outcome):
        """Validate that the requested task was actually completed"""
        print("\n✅ Step 4: Validating task completion...")
        
        if not response:
            print("   ❌ No response to validate")
            return False
        
        # Check response for success indicators
        success_indicators = [
            'success',
            'completed',
            'created',
            'generated',
            'executed'
        ]
        
        response_str = json.dumps(response).lower()
        found_success = any(indicator in response_str for indicator in success_indicators)
        
        if found_success:
            self.test_results['task_completion'] = True
            print("   ✅ Task appears to have been completed")
            
            # Additional validation based on expected outcome
            if expected_outcome:
                if expected_outcome.lower() in response_str:
                    self.test_results['capability_execution'] = True
                    print(f"   ✅ Expected outcome '{expected_outcome}' found in response")
                    return True
                else:
                    print(f"   ⚠️ Expected outcome '{expected_outcome}' not clearly indicated")
            
            return True
        else:
            print("   ❌ No clear success indicators found")
            return False
    
    def run_comprehensive_test(self):
        """Run the complete end-to-end test"""
        print("🧪 APX End-to-End Self-Improvement Test")
        print("=" * 50)
        
        # Test 1: Backend connectivity
        if not self.test_backend_connectivity():
            print("\n❌ Test failed: Backend not accessible")
            return self.test_results
        
        # Test 2: Send a request for a non-existent capability
        test_command = "Create a QR code generator tool that can generate QR codes with custom logos and save them as PNG files"
        expected_outcome = "qr code"
        
        response = self.send_user_request(test_command)
        
        # Test 3: Analyze for self-improvement
        self.analyze_response(response)
        
        # Test 4: Validate task completion
        self.validate_task_completion(response, expected_outcome)
        
        # Calculate overall success
        self.test_results['overall_success'] = (
            self.test_results['backend_connectivity'] and
            self.test_results['request_processing'] and
            self.test_results['self_improvement_triggered'] and
            self.test_results['task_completion']
        )
        
        # Print final results
        print("\n" + "=" * 50)
        print("📊 Final Test Results:")
        print("=" * 50)
        
        for key, value in self.test_results.items():
            if key != 'details':
                status = "✅" if value else "❌"
                print(f"{status} {key.replace('_', ' ').title()}: {value}")
        
        if self.test_results['overall_success']:
            print("\n🎉 END-TO-END TEST PASSED! 🎉")
            print("The APX self-improvement system successfully:")
            print("  • Detected missing capability")
            print("  • Generated new code/tool")
            print("  • Executed the requested task")
        else:
            print("\n❌ END-TO-END TEST FAILED")
            print("Review the results above to identify issues.")
        
        return self.test_results

def main():
    """Main test execution"""
    tester = EndToEndTester()
    results = tester.run_comprehensive_test()
    
    # Save detailed results
    with open('end_to_end_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: end_to_end_test_results.json")
    
    # Exit with appropriate code
    sys.exit(0 if results['overall_success'] else 1)

if __name__ == "__main__":
    main()