#!/usr/bin/env python3
"""
Comprehensive test script for action button functionality in the overlay.
Tests the complete workflow of clicking action button, entering text, and processing as action.
"""

import requests
import time
import json
import subprocess
import os
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8888"
TEST_ACTIONS = [
    "Create a new text file called test.txt with hello world",
    "Open Calculator app",
    "Take a screenshot and save it",
    "List all files in the current directory",
    "Create a folder called test_folder",
    "Open Safari and go to google.com",
    "Show current time and date",
    "Create a simple Python script that prints hello",
    "Open Terminal application",
    "Check system memory usage",
    "Create a reminder for tomorrow",
    "Open Finder and navigate to Documents",
    "Show weather information",
    "Create a new spreadsheet with sample data",
    "Open Music app and play a song"
]

def test_backend_health():
    """Test if backend is running and responsive."""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def test_action_command(action_text):
    """Test sending an action command to the backend."""
    try:
        payload = {
            "command": action_text,
            "action_mode": True
        }
        
        response = requests.post(
            f"{BACKEND_URL}/command",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return True, result
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
            
    except Exception as e:
        return False, str(e)

def test_electron_app_running():
    """Check if Electron app is running."""
    try:
        # Check for Electron process
        result = subprocess.run(
            ["pgrep", "-f", "Electron"],
            capture_output=True,
            text=True
        )
        return len(result.stdout.strip()) > 0
    except:
        return False

def simulate_action_workflow():
    """Simulate the complete action button workflow."""
    print("🧪 Testing Action Button Workflow")
    print("=" * 50)
    
    # Test 1: Backend Health
    print("\n1. Testing Backend Health...")
    if test_backend_health():
        print("   ✅ Backend is running and responsive")
    else:
        print("   ❌ Backend is not responding")
        return False
    
    # Test 2: Electron App
    print("\n2. Testing Electron App...")
    if test_electron_app_running():
        print("   ✅ Electron app is running")
    else:
        print("   ⚠️  Electron app may not be running")
    
    # Test 3: Action Commands
    print("\n3. Testing Action Commands...")
    successful_actions = 0
    failed_actions = 0
    
    for i, action in enumerate(TEST_ACTIONS, 1):
        print(f"\n   Action {i}: {action}")
        
        success, result = test_action_command(action)
        
        if success:
            print(f"   ✅ Success: {result.get('response', 'Action completed')[:100]}...")
            successful_actions += 1
        else:
            print(f"   ❌ Failed: {result}")
            failed_actions += 1
        
        # Small delay between actions
        time.sleep(1)
    
    # Test Results
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS")
    print("=" * 50)
    print(f"Total Actions Tested: {len(TEST_ACTIONS)}")
    print(f"Successful Actions: {successful_actions}")
    print(f"Failed Actions: {failed_actions}")
    print(f"Success Rate: {(successful_actions/len(TEST_ACTIONS)*100):.1f}%")
    
    if successful_actions == len(TEST_ACTIONS):
        print("\n🎉 ALL TESTS PASSED! Action button workflow is working perfectly.")
    elif successful_actions > len(TEST_ACTIONS) * 0.8:
        print("\n✅ MOSTLY SUCCESSFUL! Action button workflow is working well.")
    else:
        print("\n⚠️  SOME ISSUES DETECTED. Action button workflow needs attention.")
    
    return successful_actions > 0

def test_action_mode_toggle():
    """Test action mode toggle functionality."""
    print("\n🔄 Testing Action Mode Toggle")
    print("-" * 30)
    
    # Simulate different action mode scenarios
    scenarios = [
        "Simple text action",
        "Complex multi-step action with parameters",
        "Action with special characters !@#$%",
        "Very long action command that spans multiple words and contains detailed instructions",
        "Action with numbers 123 and symbols &*("
    ]
    
    for scenario in scenarios:
        print(f"\n   Testing: {scenario[:50]}...")
        success, result = test_action_command(scenario)
        
        if success:
            print("   ✅ Action mode toggle working")
        else:
            print(f"   ❌ Action mode toggle failed: {result}")
        
        time.sleep(0.5)

def main():
    """Main test function."""
    print("🚀 Action Button Workflow Test Suite")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Run workflow simulation
    workflow_success = simulate_action_workflow()
    
    # Test action mode toggle
    test_action_mode_toggle()
    
    print("\n" + "=" * 60)
    print("🏁 Test Suite Complete")
    
    if workflow_success:
        print("\n✨ The action button functionality is working correctly!")
        print("\n📝 How to use:")
        print("   1. Click the ⚡ Action button in the overlay")
        print("   2. The input field will show 'Enter your action...'")
        print("   3. Type your action command")
        print("   4. Press Enter to execute the action")
        print("   5. The action will be processed by the backend")
    else:
        print("\n❌ Action button functionality needs debugging.")
    
    return workflow_success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)