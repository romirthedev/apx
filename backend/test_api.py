import aiohttp
import asyncio
import json
import time
from typing import Dict, Any, Optional

async def make_request(session: aiohttp.ClientSession, url: str, method: str = 'GET', 
                      data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Helper function to make HTTP requests."""
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    try:
        if method.upper() == 'GET':
            async with session.get(url, headers=headers) as response:
                return {
                    'status': response.status,
                    'headers': dict(response.headers),
                    'body': await response.text()
                }
        else:
            async with session.post(url, headers=headers, json=data) as response:
                return {
                    'status': response.status,
                    'headers': dict(response.headers),
                    'body': await response.text()
                }
    except Exception as e:
        return {
            'error': str(e),
            'status': 0
        }

async def test_api():
    base_url = "http://localhost:5050"  # Using port 5050 for our Quart server
    
    async with aiohttp.ClientSession() as session:
        # Test health check
        print("\n" + "="*50)
        print("Testing health check...")
        health_response = await make_request(session, f"{base_url}/health")
        print(f"Status: {health_response.get('status')}")
        print(f"Response: {health_response.get('body')}")
        
        test_cases = [
            "what can you do?",
            "open browser",
            "hello, how are you?",
            "search for python tutorials",
            "what time is it?"
        ]
        
        for test_input in test_cases:
            print("\n" + "="*50)
            print(f"Testing input: {test_input}")
            print("="*50)
            
            # Add a small delay between requests
            await asyncio.sleep(0.5)
            
            # Make the request
            response = await make_request(
                session, 
                f"{base_url}/api/command",
                method='POST',
                data={"command": test_input}
            )
            
            print(f"Status Code: {response.get('status')}")
            print("Headers:", json.dumps(response.get('headers', {}), indent=2))
            
            try:
                json_body = json.loads(response.get('body', '{}'))
                print("Response Body:")
                print(json.dumps(json_body, indent=2))
            except json.JSONDecodeError:
                print(f"Non-JSON Response: {response.get('body')}")
            except Exception as e:
                print(f"Error parsing response: {e}")

if __name__ == '__main__':
    print("Starting API tests...")
    asyncio.run(test_api())
