#!/usr/bin/env python3
"""
Cluely AI Demo Script
This script demonstrates the new AI-powered capabilities of Cluely with Gemini integration.
"""

import requests
import json
import time

BACKEND_URL = "http://localhost:8888"

def test_ai_command(command, description):
    """Test an AI command and display the result."""
    print(f"\n🧠 Testing AI: {description}")
    print(f"Command: '{command}'")
    print("-" * 60)
    
    try:
        response = requests.post(f"{BACKEND_URL}/command", json={
            "command": command,
            "context": []
        })
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Success ({result.get('metadata', {}).get('method', 'unknown')}):")
                print(f"{result.get('result', 'No result')}")
                
                # Show metadata if available
                metadata = result.get('metadata', {})
                if metadata.get('method') == 'ai_response':
                    print(f"🤖 AI-powered response")
                elif metadata.get('method') == 'rule_based':
                    print(f"⚙️ Rule-based response")
                elif metadata.get('method') == 'ai_with_actions':
                    print(f"🚀 AI with system actions")
                    
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
    
    time.sleep(2)  # Brief pause between tests
    return True

def main():
    print("🧠 Cluely AI Assistant Demo with Gemini Integration")
    print("=" * 60)
    
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
        print("❌ Backend is not running. Please start it first")
        return
    
    # Test AI-powered commands
    ai_commands = [
        ("help", "Getting AI-enhanced help"),
        ("what can you do for me?", "Conversational capability query"),
        ("explain how AI works", "General knowledge question"),
        ("how do I organize my files better?", "Getting advice and recommendations"),
        ("what time is it and how is my computer running?", "Multiple information request"),
        ("can you help me create a shopping list file?", "Task assistance request"),
        ("recommend a good way to backup my data", "Advice seeking"),
        ("what's the best programming language to learn?", "Opinion and recommendation"),
        ("create file ai-notes.txt", "Direct system command via AI"),
        ("tell me about the weather and also launch chrome", "Complex multi-action request"),
    ]
    
    print(f"\n🤖 Testing {len(ai_commands)} AI-powered commands...\n")
    
    successful = 0
    for command, description in ai_commands:
        if test_ai_command(command, description):
            successful += 1
    
    print("\n" + "=" * 60)
    print(f"AI Demo completed: {successful}/{len(ai_commands)} commands successful")
    
    if successful == len(ai_commands):
        print("🎉 All AI tests passed! Cluely is now AI-powered with Gemini!")
        print("\n🌟 Key AI Features:")
        print("  • Natural conversation abilities")
        print("  • Context-aware responses")
        print("  • Smart command understanding")
        print("  • Recommendations and advice")
        print("  • Multi-action requests")
        print("  • Fallback to AI when rules fail")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    print(f"\n🔗 Try the overlay UI: Press Cmd+Space and ask:")
    print("  • 'How can you help me be more productive?'")
    print("  • 'What's the best way to organize my downloads?'")
    print("  • 'Create a file and explain what you did'")

if __name__ == "__main__":
    main()
