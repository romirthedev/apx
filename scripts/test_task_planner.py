import requests
import json
import sys

def test_task_planner():
    """Test the Cluely task planner functionality directly."""
    url = "http://localhost:8888/command"
    
    # Use a command that should trigger the task planner
    command = "create a text file on my Desktop called test_task_planner.txt with content 'This is a test of the task planner system'"
    
    print(f"Sending command: {command}")
    
    # Make the request
    response = requests.post(
        url,
        json={
            "command": command,
            "context": []
        }
    )
    
    # Parse response
    data = response.json()
    print("\nResponse:")
    print(json.dumps(data, indent=2))
    
    # Check if task planner was used
    method = data.get("metadata", {}).get("method", "unknown")
    print(f"\nMethod used: {method}")
    print(f"Is AI Response: {data.get('is_ai_response', False)}")
    
    # Check if actions were performed
    actions = data.get("metadata", {}).get("actions_performed", [])
    if actions:
        print("\nActions performed:")
        for i, action in enumerate(actions):
            print(f"{i+1}. Type: {action.get('action_type', 'unknown')}")
            if action.get("output"):
                print(f"   Output: {action.get('output')}")
            if action.get("error"):
                print(f"   Error: {action.get('error')}")

if __name__ == "__main__":
    test_task_planner()
