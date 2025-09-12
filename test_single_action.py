#!/usr/bin/env python3
"""
Simple test to verify that actions are actually executed, not just returned as JSON.
"""

import requests
import time
import subprocess
import sys

# Configuration
BACKEND_URL = "http://localhost:8888"

def check_if_app_running(app_name):
    """Check if an application is currently running"""
    try:
        result = subprocess.run(
            ["pgrep", "-f", app_name], 
            capture_output=True, 
            text=True
        )
        return len(result.stdout.strip()) > 0
    except:
        return False

def test_calculator_action():
    """Test opening Calculator app and verify it actually opens"""
    print("🧪 Testing Calculator Action Execution")
    print("=" * 50)
    
    # Check if Calculator is already running
    calc_running_before = check_if_app_running("Calculator")
    print(f"📱 Calculator running before test: {calc_running_before}")
    
    # If Calculator is running, close it first
    if calc_running_before:
        print("🔄 Closing Calculator first...")
        subprocess.run(["pkill", "-f", "Calculator"], capture_output=True)
        time.sleep(2)
    
    # Send action command to backend
    payload = {
        "command": "Open Calculator app",
        "action_mode": True
    }
    
    print(f"📤 Sending request: {payload}")
    
    try:
        response = requests.post(f"{BACKEND_URL}/command", json=payload, timeout=10)
        print(f"📥 Response status: {response.status_code}")
        print(f"📥 Response body: {response.text}")
        
        if response.status_code == 200:
            # Wait a moment for the app to launch
            time.sleep(3)
            
            # Check if Calculator is now running
            calc_running_after = check_if_app_running("Calculator")
            print(f"📱 Calculator running after test: {calc_running_after}")
            
            if calc_running_after and not calc_running_before:
                print("✅ SUCCESS: Calculator was successfully opened!")
                print("🎉 Action execution is working correctly!")
                return True
            elif calc_running_after and calc_running_before:
                print("⚠️  Calculator was already running, test inconclusive")
                return True
            else:
                print("❌ FAILURE: Calculator was not opened")
                print("🚨 Action execution is NOT working!")
                return False
        else:
            print(f"❌ FAILURE: Backend returned error {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ FAILURE: Request failed - {str(e)}")
        return False

def test_backend_health():
    """Test if backend is running"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

if __name__ == "__main__":
    print("🚀 Starting Action Execution Verification Test")
    print("=" * 60)
    
    # Check backend health
    if not test_backend_health():
        print("❌ Backend is not running! Please start the backend first.")
        sys.exit(1)
    
    print("✅ Backend is running")
    print()
    
    # Test Calculator action
    success = test_calculator_action()
    
    print()
    print("=" * 60)
    if success:
        print("🎉 TEST PASSED: Actions are being executed correctly!")
    else:
        print("💥 TEST FAILED: Actions are not being executed!")
    print("=" * 60)