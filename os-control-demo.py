#!/usr/bin/env python3
"""
Cluely OS-Level Control Demo
Demonstrates local execution with full system privileges
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
    if len(result) > 300:
        print(f"{result[:300]}...")
    else:
        print(result)
    
    print("-" * 60)

def main():
    print("🚀 Cluely OS-Level Control Demo")
    print("=" * 60)
    print("Testing local execution with full system privileges")
    print("=" * 60)
    
    # Test system analysis
    print("\n📊 SYSTEM ANALYSIS TESTS")
    commands = [
        "what app takes the most space on my computer",
        "show disk usage",
        "check system permissions"
    ]
    
    for cmd in commands:
        response = send_command(cmd)
        print_response(cmd, response)
        time.sleep(1)
    
    # Test OS-level control (requires permissions)
    print("\n🖥️ OS-LEVEL CONTROL TESTS")
    print("Note: These require macOS permissions to work properly")
    commands = [
        "take a screenshot",
        "check system permissions",
        "request permissions"
    ]
    
    for cmd in commands:
        response = send_command(cmd)
        print_response(cmd, response)
        time.sleep(1)
    
    # Test enhanced automation
    print("\n🤖 ENHANCED AUTOMATION TESTS")
    commands = [
        "organize downloads",
        "create daily report",
        "help"
    ]
    
    for cmd in commands:
        response = send_command(cmd)
        print_response(cmd, response)
        time.sleep(1)
    
    # Test AI conversation about system control
    print("\n🧠 AI SYSTEM CONTROL CONVERSATION")
    commands = [
        "How can I give you full control of my Mac?",
        "What permissions do you need to automate tasks?",
        "How can I make you run automatically on startup?"
    ]
    
    for cmd in commands:
        response = send_command(cmd)
        print_response(cmd, response)
        time.sleep(2)
    
    print(f"\n{'='*60}")
    print("🎉 Demo completed!")
    print("📝 Summary of Cluely's Local Execution Capabilities:")
    print("   • Full disk access and app size analysis")
    print("   • System permission checking and management")
    print("   • OS-level automation (click, type, screenshot)")
    print("   • Always-on background operation")
    print("   • AI-powered natural language control")
    print("   • Comprehensive security and logging")
    print(f"{'='*60}")
    print("\n🔐 To enable full functionality:")
    print("1. Run 'check system permissions' to see what's needed")
    print("2. Run 'request permissions' for detailed setup instructions")
    print("3. Grant permissions in System Settings → Privacy & Security")
    print("4. Restart Cluely for changes to take effect")
    print("\n✨ Once set up, Cluely can control your Mac like a human!")

if __name__ == "__main__":
    main()
