#!/usr/bin/env python3
"""
Comprehensive Action Execution Testing Script
Tests various aspects of the AI action execution system
"""

import requests
import time
import json
import subprocess
import os
from typing import Dict, Any, List

# Configuration
BACKEND_URL = "http://localhost:8888"
TEST_RESULTS = []

def check_backend_health() -> bool:
    """Check if backend is running"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def is_app_running(app_name: str) -> bool:
    """Check if an application is currently running"""
    try:
        result = subprocess.run(
            ["pgrep", "-f", app_name], 
            capture_output=True, 
            text=True
        )
        return result.returncode == 0
    except:
        return False

def send_command(command: str, action_mode: bool = True) -> Dict[str, Any]:
    """Send command to backend and return response"""
    try:
        payload = {
            "command": command,
            "action_mode": action_mode
        }
        response = requests.post(
            f"{BACKEND_URL}/command",
            json=payload,
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

def run_test(test_name: str, command: str, expected_actions: List[str] = None, 
             check_app: str = None, should_succeed: bool = True) -> Dict[str, Any]:
    """Run a single test case"""
    print(f"\n🧪 Testing: {test_name}")
    print(f"📤 Command: {command}")
    
    # Record initial state
    initial_app_state = is_app_running(check_app) if check_app else None
    
    # Send command
    result = send_command(command)
    
    # Wait a moment for actions to complete
    time.sleep(2)
    
    # Check final state
    final_app_state = is_app_running(check_app) if check_app else None
    
    # Analyze results
    test_result = {
        "test_name": test_name,
        "command": command,
        "status_code": result["status_code"],
        "success": result["success"],
        "response": result["response"],
        "initial_app_state": initial_app_state,
        "final_app_state": final_app_state,
        "app_state_changed": initial_app_state != final_app_state if check_app else None,
        "expected_success": should_succeed
    }
    
    # Extract actions from response
    actions_performed = []
    if result["success"] and isinstance(result["response"], dict):
        response_text = result["response"].get("result", "")
        if "Actions performed:" in response_text:
            actions_section = response_text.split("Actions performed:")[1]
            for line in actions_section.split("\n"):
                line = line.strip()
                if line.startswith("✅") or line.startswith("❌"):
                    actions_performed.append(line)
    
    test_result["actions_performed"] = actions_performed
    
    # Determine if test passed
    if should_succeed:
        test_passed = result["success"] and len(actions_performed) > 0
        if check_app:
            test_passed = test_passed and (final_app_state or initial_app_state)
    else:
        test_passed = not result["success"] or any("❌" in action for action in actions_performed)
    
    test_result["test_passed"] = test_passed
    
    # Print results
    status = "✅ PASS" if test_passed else "❌ FAIL"
    print(f"📥 Status: {result['status_code']}")
    print(f"🎯 Result: {status}")
    if actions_performed:
        print("🔧 Actions:")
        for action in actions_performed:
            print(f"   {action}")
    if check_app:
        print(f"📱 App {check_app}: {initial_app_state} → {final_app_state}")
    
    TEST_RESULTS.append(test_result)
    return test_result

def print_summary():
    """Print comprehensive test summary"""
    print("\n" + "="*80)
    print("📊 COMPREHENSIVE TEST SUMMARY")
    print("="*80)
    
    total_tests = len(TEST_RESULTS)
    passed_tests = sum(1 for test in TEST_RESULTS if test["test_passed"])
    failed_tests = total_tests - passed_tests
    
    print(f"\n📈 Overall Results:")
    print(f"   Total Tests: {total_tests}")
    print(f"   Passed: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
    print(f"   Failed: {failed_tests} ({failed_tests/total_tests*100:.1f}%)")
    
    # Categorize by action type
    action_types = {}
    for test in TEST_RESULTS:
        for action in test["actions_performed"]:
            if "Execute" in action:
                action_type = action.split("Execute ")[1].split(":")[0]
                if action_type not in action_types:
                    action_types[action_type] = {"total": 0, "success": 0, "failed": 0}
                action_types[action_type]["total"] += 1
                if "✅" in action:
                    action_types[action_type]["success"] += 1
                else:
                    action_types[action_type]["failed"] += 1
    
    print(f"\n🔧 Action Type Analysis:")
    for action_type, stats in action_types.items():
        success_rate = stats["success"] / stats["total"] * 100 if stats["total"] > 0 else 0
        print(f"   {action_type}: {stats['success']}/{stats['total']} ({success_rate:.1f}% success)")
    
    # Failed tests details
    if failed_tests > 0:
        print(f"\n❌ Failed Tests Details:")
        for test in TEST_RESULTS:
            if not test["test_passed"]:
                print(f"   • {test['test_name']}")
                print(f"     Command: {test['command']}")
                print(f"     Status: {test['status_code']}")
                if test["actions_performed"]:
                    print(f"     Actions: {len(test['actions_performed'])} performed")
                    for action in test["actions_performed"]:
                        if "❌" in action:
                            print(f"       {action}")
                else:
                    print(f"     Actions: None performed")
                print()
    
    # Save detailed results
    with open("/Users/romirpatel/apx/comprehensive_test_results.json", "w") as f:
        json.dump(TEST_RESULTS, f, indent=2)
    print(f"\n💾 Detailed results saved to: comprehensive_test_results.json")

def main():
    print("🚀 Starting Comprehensive Action Execution Testing")
    print("="*80)
    
    # Check backend
    if not check_backend_health():
        print("❌ Backend is not running! Please start the backend first.")
        return
    
    print("✅ Backend is running\n")
    
    # Test Categories
    
    # 1. Application Control Tests
    print("\n📱 APPLICATION CONTROL TESTS")
    print("-" * 50)
    run_test("Open Calculator", "Open Calculator app", check_app="Calculator")
    run_test("Open TextEdit", "Launch TextEdit application", check_app="TextEdit")
    run_test("Open Finder", "Open Finder window", check_app="Finder")
    run_test("Open Preview", "Start Preview app", check_app="Preview")
    run_test("Open Safari", "Launch Safari browser", check_app="Safari")
    run_test("Open Invalid App", "Open NonExistentApp123", should_succeed=False)
    
    # 2. File Operations Tests
    print("\n📁 FILE OPERATIONS TESTS")
    print("-" * 50)
    run_test("Create Test File", "Create a file called test_file.txt with content 'Hello World'")
    run_test("Find Python Files", "Find all Python files in the current directory")
    run_test("Find Text Files", "Search for all .txt files")
    run_test("Open Test File", "Open the file test_file.txt")
    run_test("Find Non-existent Files", "Find files with extension .nonexistent")
    
    # 3. Shell Command Tests
    print("\n💻 SHELL COMMAND TESTS")
    print("-" * 50)
    run_test("List Directory", "List the contents of the current directory")
    run_test("Show Current Directory", "Show the current working directory")
    run_test("Display Date", "Show the current date and time")
    run_test("Count Files", "Count the number of files in the current directory")
    run_test("Show System Info", "Display system information")
    run_test("Invalid Command", "Run the command 'invalidcommand123'", should_succeed=False)
    run_test("Command with Invalid Options", "Run 'head -z file.txt'", should_succeed=False)
    
    # 4. Complex Multi-Action Tests
    print("\n🔄 MULTI-ACTION TESTS")
    print("-" * 50)
    run_test("Create and Open File", "Create a file called multi_test.txt and then open it")
    run_test("Open Multiple Apps", "Open Calculator and TextEdit applications")
    run_test("File Operations Chain", "Create a file called chain_test.txt, find all txt files, then open the new file")
    run_test("Mixed Operations", "Show current directory, open Calculator, and find Python files")
    
    # 5. Edge Cases and Error Handling
    print("\n⚠️  EDGE CASES AND ERROR HANDLING")
    print("-" * 50)
    run_test("Empty Command", "", should_succeed=False)
    run_test("Very Long Command", "Open " + "Calculator " * 100, check_app="Calculator")
    run_test("Special Characters", "Create a file with name 'test@#$%^&*().txt'")
    run_test("Unicode Command", "Create a file called 'тест.txt' with content 'Hello 世界'")
    run_test("Path Traversal Attempt", "Create a file at ../../../etc/passwd", should_succeed=False)
    
    # 6. Performance and Stress Tests
    print("\n⚡ PERFORMANCE TESTS")
    print("-" * 50)
    run_test("Rapid Commands 1", "List directory")
    time.sleep(0.1)
    run_test("Rapid Commands 2", "Show date")
    time.sleep(0.1)
    run_test("Rapid Commands 3", "Count files")
    
    # 7. Context and State Tests
    print("\n🔄 CONTEXT AND STATE TESTS")
    print("-" * 50)
    run_test("Context Dependent 1", "Create a file called context_test.txt")
    run_test("Context Dependent 2", "Now open that file I just created")
    run_test("State Persistence", "List all the files I've created in this session")
    
    # Print comprehensive summary
    print_summary()

if __name__ == "__main__":
    main()
