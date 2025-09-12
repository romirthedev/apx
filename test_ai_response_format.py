#!/usr/bin/env python3
"""
AI Response Format Testing Script
Tests the AI's ability to generate proper JSON responses with actions.
"""

import requests
import json
import time
from typing import Dict, Any, List

# Backend configuration
BACKEND_URL = "http://localhost:8888"
HEALTH_ENDPOINT = f"{BACKEND_URL}/health"
COMMAND_ENDPOINT = f"{BACKEND_URL}/command"

def check_backend_health() -> bool:
    """Check if backend is running and healthy."""
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=5)
        return response.status_code == 200
    except:
        return False

def send_command(command: str) -> Dict[str, Any]:
    """Send command to backend and return full response."""
    try:
        response = requests.post(
            COMMAND_ENDPOINT,
            json={"command": command},
            timeout=30
        )
        return {
            "status_code": response.status_code,
            "response": response.json() if response.status_code == 200 else response.text,
            "success": response.status_code == 200
        }
    except Exception as e:
        return {
            "status_code": 0,
            "response": str(e),
            "success": False
        }

def analyze_ai_response(command: str, response_data: Dict) -> Dict[str, Any]:
    """Analyze the AI response format and action generation."""
    analysis = {
        "command": command,
        "status_code": response_data.get("status_code", 0),
        "success": response_data.get("success", False),
        "has_actions": False,
        "action_count": 0,
        "response_format": "unknown",
        "raw_response": "",
        "method": "unknown",
        "issues": []
    }
    
    if not response_data.get("success"):
        analysis["issues"].append("Request failed")
        return analysis
    
    response_body = response_data.get("response", {})
    
    # Extract method from metadata
    if isinstance(response_body, dict):
        metadata = response_body.get("metadata", {})
        analysis["method"] = metadata.get("method", "unknown")
        
        # Get the actual result text
        result_text = response_body.get("result", "")
        analysis["raw_response"] = result_text
        
        # Check if actions were performed
        if "Actions performed:" in result_text:
            analysis["has_actions"] = True
            # Count action lines
            action_lines = [line for line in result_text.split("\n") if line.strip().startswith(("✅", "❌"))]
            analysis["action_count"] = len(action_lines)
        
        # Analyze response format
        if analysis["method"] == "ai_with_actions":
            analysis["response_format"] = "ai_with_actions"
        elif analysis["method"] == "ai_response":
            analysis["response_format"] = "ai_response_only"
        elif analysis["method"] == "direct_response":
            analysis["response_format"] = "direct_response"
            analysis["issues"].append("Command fell back to direct response")
        
        # Check for JSON structure in the raw response
        if "{" in result_text and "}" in result_text:
            analysis["contains_json"] = True
            # Try to extract JSON
            try:
                import re
                json_match = re.search(r'\{.*?\}', result_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    parsed = json.loads(json_str)
                    if "actions" in parsed:
                        analysis["json_has_actions"] = True
                        analysis["json_action_count"] = len(parsed["actions"])
            except:
                analysis["json_parse_error"] = True
        else:
            analysis["contains_json"] = False
    
    return analysis

def run_ai_format_tests():
    """Run comprehensive tests of AI response formats."""
    print("🧪 AI Response Format Testing")
    print("=" * 50)
    
    # Check backend health
    if not check_backend_health():
        print("❌ Backend is not running or unhealthy")
        return
    
    print("✅ Backend is healthy")
    print()
    
    # Test commands that should generate actions
    test_commands = [
        # Simple app commands
        "open calculator",
        "launch safari",
        "open finder",
        
        # File operations
        "create a file called test.txt",
        "find the largest file in downloads",
        "search for python files",
        
        # System commands
        "show system information",
        "list files in current directory",
        "get current date and time",
        
        # Shell commands
        "run ls -la",
        "execute head -n 5 /etc/hosts",
        "run find . -name '*.py'",
        
        # Multi-step commands
        "open calculator and notes",
        "create a file and then open it",
        "search for files and show the results",
        
        # Conversational commands that might not need actions
        "what can you do?",
        "hello how are you?",
        "explain quantum physics"
    ]
    
    results = []
    
    for i, command in enumerate(test_commands, 1):
        print(f"Test {i}/{len(test_commands)}: {command}")
        
        # Send command
        response = send_command(command)
        
        # Analyze response
        analysis = analyze_ai_response(command, response)
        results.append(analysis)
        
        # Print summary
        status = "✅" if analysis["has_actions"] else "❌" if analysis["method"] == "direct_response" else "⚠️"
        print(f"  {status} Method: {analysis['method']}, Actions: {analysis['action_count']}, Format: {analysis['response_format']}")
        
        if analysis["issues"]:
            for issue in analysis["issues"]:
                print(f"    ⚠️ {issue}")
        
        print()
        time.sleep(0.5)  # Rate limiting
    
    # Generate summary
    print("📊 SUMMARY")
    print("=" * 50)
    
    total_tests = len(results)
    ai_with_actions = len([r for r in results if r["method"] == "ai_with_actions"])
    ai_response_only = len([r for r in results if r["method"] == "ai_response"])
    direct_response = len([r for r in results if r["method"] == "direct_response"])
    
    print(f"Total tests: {total_tests}")
    print(f"AI with actions: {ai_with_actions} ({ai_with_actions/total_tests*100:.1f}%)")
    print(f"AI response only: {ai_response_only} ({ai_response_only/total_tests*100:.1f}%)")
    print(f"Direct response: {direct_response} ({direct_response/total_tests*100:.1f}%)")
    print()
    
    # Show problematic commands
    problematic = [r for r in results if r["method"] == "direct_response" and "what can you do" not in r["command"].lower() and "hello" not in r["command"].lower() and "explain" not in r["command"].lower()]
    
    if problematic:
        print("🚨 Commands that fell back to direct response:")
        for result in problematic:
            print(f"  - {result['command']}")
        print()
    
    # Show AI responses without actions
    no_actions = [r for r in results if r["method"] == "ai_response" and not r["has_actions"]]
    
    if no_actions:
        print("⚠️ AI responses without actions:")
        for result in no_actions:
            print(f"  - {result['command']}")
            print(f"    Response: {result['raw_response'][:100]}...")
        print()
    
    # Save detailed results
    with open("ai_format_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"📁 Detailed results saved to ai_format_test_results.json")

if __name__ == "__main__":
    run_ai_format_tests()