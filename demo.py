#!/usr/bin/env python3
"""
Cluely Demo Script
This script demonstrates some of the capabilities of the Cluely AI assistant.
Run this to test various features of the backend.
"""

import requests
import json
import time

BACKEND_URL = "http://localhost:8888"

def test_command(command, description):
    """Test a command and display the result."""
    print(f"\n🧠 Testing: {description}")
    print(f"Command: '{command}'")
    print("-" * 50)
    
    try:
        response = requests.post(f"{BACKEND_URL}/command", json={
            "command": command,
            "context": []
        })
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Success: {result.get('result', 'No result')}")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Make sure it's running on localhost:8888")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False
    
    time.sleep(1)  # Brief pause between tests
    return True

def main():
    print("🧠 Cluely AI Assistant Demo")
    print("=" * 40)
    
    # Check if backend is running
    try:
        response = requests.get(f"{BACKEND_URL}/health")
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Backend is healthy - Version {health.get('version', 'unknown')}")
        else:
            print("❌ Backend health check failed")
            return
    except:
        print("❌ Backend is not running. Please start it first with:")
        print("   cd backend && python main.py")
        return
    
    # Demo commands
    commands = [
        ("help", "Getting help and available commands"),
        ("what time is it", "Getting current time"),
        ("show system information", "Getting system information"),
        ("python print('Hello from Cluely!')", "Running Python code"),
        ("create file demo.txt", "Creating a new file"),
        ("search for *.py", "Searching for Python files"),
        ("google latest AI news", "Performing web search"),
        ("show running processes", "Listing running processes"),
    ]
    
    print(f"\nRunning {len(commands)} demo commands...\n")
    
    successful = 0
    for command, description in commands:
        if test_command(command, description):
            successful += 1
    
    print("\n" + "=" * 50)
    print(f"Demo completed: {successful}/{len(commands)} commands successful")
    
    if successful == len(commands):
        print("🎉 All tests passed! Cluely is working perfectly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()
