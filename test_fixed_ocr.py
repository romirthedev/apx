#!/usr/bin/env python3
"""
Test script to verify the fixed OCR implementation works correctly.
"""

import requests
import json
import time

def test_ocr_api():
    """Test the OCR functionality through the backend API."""
    print("🧪 Testing Fixed OCR Implementation")
    print("=" * 50)
    
    # Backend URL
    url = "http://localhost:8888/command"
    
    # Test command
    command = "read screen text"
    
    print(f"📡 Sending request to: {url}")
    print(f"📝 Command: {command}")
    print("⏳ Processing...")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            url,
            json={"command": command},
            headers={"Content-Type": "application/json"},
            timeout=60  # 60 second timeout
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️  Response time: {duration:.2f} seconds")
        print(f"📊 Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Request successful!")
            print(f"📄 Response: {json.dumps(result, indent=2)}")
            
            # Check if OCR worked
            if 'result' in result and 'Extracted text' in str(result['result']):
                print("🎉 OCR functionality is working correctly!")
            elif 'timeout' in str(result).lower():
                print("⚠️  OCR timed out - this was the original issue")
            else:
                print("ℹ️  OCR completed but may not have found text")
                
        else:
            print(f"❌ Request failed with status: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out after 60 seconds")
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend. Is it running on localhost:8888?")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🏁 Test completed")

if __name__ == "__main__":
    test_ocr_api()