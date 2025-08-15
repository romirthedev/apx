#!/usr/bin/env python3
"""
Cluely Enhanced Features Demo
Demonstrates all the new AI and automation capabilities
"""

import requests
import json
import time

BACKEND_URL = "http://localhost:8888"

def send_command(command):
    """Send a command to Cluely backend and return response."""
    try:
        response = requests.post(f"{BACKEND_URL}/command", 
                               json={"command": command, "context": []})
        return response.json()
    except Exception as e:
        return {"error": str(e), "success": False}

def print_response(command, response):
    """Print formatted response."""
    print(f"\n🎯 Command: {command}")
    print(f"✅ Success: {response.get('success', False)}")
    
    if response.get('is_ai_response'):
        print("🤖 AI Response:")
    else:
        print("⚡ System Response:")
    
    result = response.get('result', 'No result')
    # Truncate long responses for demo
    if len(result) > 200:
        print(f"{result[:200]}...")
    else:
        print(result)
    
    print("-" * 50)

def main():
    print("🚀 Cluely Enhanced Features Demo")
    print("=" * 50)
    
    # Test document creation
    print("\n📝 DOCUMENT CREATION TESTS")
    commands = [
        "make a new excel spreadsheet called demo-budget",
        "create a word document called meeting-notes",
        "make a powerpoint presentation called quarterly-review"
    ]
    
    for cmd in commands:
        response = send_command(cmd)
        print_response(cmd, response)
        time.sleep(1)
    
    # Test automation features
    print("\n🤖 AUTOMATION TESTS")
    commands = [
        "list workflows",
        "create daily report"
    ]
    
    for cmd in commands:
        response = send_command(cmd)
        print_response(cmd, response)
        time.sleep(1)
    
    # Test AI conversation
    print("\n🧠 AI CONVERSATION TESTS")
    commands = [
        "What's the best way to organize my files?",
        "How do I create a productive morning routine?",
        "Can you explain the benefits of automation?"
    ]
    
    for cmd in commands:
        response = send_command(cmd)
        print_response(cmd, response)
        time.sleep(2)  # Give AI time to respond
    
    # Test system capabilities
    print("\n⚙️ SYSTEM CAPABILITY TESTS")
    commands = [
        "help",
        "show system info",
        "what time is it"
    ]
    
    for cmd in commands:
        response = send_command(cmd)
        print_response(cmd, response)
        time.sleep(1)
    
    print("\n🎉 Demo completed! Cluely is ready to be your AI assistant.")
    print("Try pressing Cmd+Space (or Ctrl+Space) to open the overlay interface!")

if __name__ == "__main__":
    main()
