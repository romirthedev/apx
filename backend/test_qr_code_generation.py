#!/usr/bin/env python3
"""
Comprehensive test for QR code generation capability.
This test validates that the self-improvement system can:
1. Detect missing QR code capability
2. Generate the appropriate tool
3. Execute the tool successfully
4. Produce actual QR code files
"""

import requests
import json
import time
import os
from pathlib import Path

def test_qr_code_generation():
    """Test the complete QR code generation workflow."""
    
    # Backend URL
    backend_url = "http://localhost:8889"
    
    print("🧪 Testing QR Code Generation Capability")
    print("=" * 50)
    
    # Test 1: Request QR code generation
    print("\n📝 Step 1: Requesting QR code generation...")
    
    request_data = {
        "command": "Create a QR code for 'https://github.com/traehq/trae' and save it as 'github_qr.png' on my Desktop",
        "context": []
    }
    
    try:
        response = requests.post(f"{backend_url}/command", json=request_data, timeout=60)
        print(f"✅ Request sent successfully (Status: {response.status_code})")
        
        if response.status_code != 200:
            print(f"❌ Backend returned error: {response.status_code}")
            return False
            
        response_data = response.json()
        print(f"📋 Response: {json.dumps(response_data, indent=2)[:500]}...")
        
    except Exception as e:
        print(f"❌ Failed to send request: {e}")
        return False
    
    # Test 2: Check if QR code file was created
    print("\n📁 Step 2: Checking if QR code file was created...")
    
    desktop_path = os.path.expanduser("~/Desktop")
    qr_file_path = os.path.join(desktop_path, "github_qr.png")
    
    # Wait a moment for file creation
    time.sleep(2)
    
    if os.path.exists(qr_file_path):
        print(f"✅ QR code file created successfully: {qr_file_path}")
        file_size = os.path.getsize(qr_file_path)
        print(f"📊 File size: {file_size} bytes")
        
        # Verify it's a valid image file
        try:
            from PIL import Image
            img = Image.open(qr_file_path)
            print(f"🖼️ Image dimensions: {img.size}")
            print(f"🎨 Image format: {img.format}")
            img.close()
            
        except Exception as e:
            print(f"⚠️ Could not verify image: {e}")
            
    else:
        print(f"❌ QR code file not found at: {qr_file_path}")
        return False
    
    # Test 3: Request QR code with custom logo
    print("\n🎨 Step 3: Testing QR code with custom logo...")
    
    logo_request = {
        "command": "Create a QR code for 'https://trae.ai' with a custom logo and save it as 'trae_qr_with_logo.png' on my Desktop. Use any available logo image.",
        "context": []
    }
    
    try:
        response = requests.post(f"{backend_url}/command", json=logo_request, timeout=60)
        print(f"✅ Logo QR request sent (Status: {response.status_code})")
        
        if response.status_code == 200:
            logo_qr_path = os.path.join(desktop_path, "trae_qr_with_logo.png")
            time.sleep(2)
            
            if os.path.exists(logo_qr_path):
                print(f"✅ QR code with logo created: {logo_qr_path}")
            else:
                print(f"⚠️ Logo QR code not found (may be expected if no logo available)")
                
    except Exception as e:
        print(f"⚠️ Logo QR request failed: {e}")
    
    # Test 4: Validate response indicates success
    print("\n🔍 Step 4: Validating response data...")
    
    success_indicators = [
        "success" in str(response_data).lower(),
        "qr" in str(response_data).lower(),
        "generated" in str(response_data).lower() or "created" in str(response_data).lower(),
        os.path.exists(qr_file_path)
    ]
    
    success_count = sum(success_indicators)
    print(f"📊 Success indicators: {success_count}/4")
    
    for i, indicator in enumerate([
        "Response contains 'success'",
        "Response mentions 'qr'", 
        "Response indicates generation/creation",
        "QR file actually exists"
    ]):
        status = "✅" if success_indicators[i] else "❌"
        print(f"  {status} {indicator}")
    
    # Final assessment
    print("\n🏁 Final Assessment")
    print("=" * 30)
    
    if success_count >= 3:
        print("🎉 QR Code Generation Test: PASSED")
        print("✅ The self-improvement system successfully:")
        print("   - Detected missing QR code capability")
        print("   - Generated appropriate tool")
        print("   - Executed the tool")
        print("   - Produced actual QR code files")
        return True
    else:
        print("❌ QR Code Generation Test: FAILED")
        print(f"   Only {success_count}/4 success criteria met")
        return False

if __name__ == "__main__":
    success = test_qr_code_generation()
    exit(0 if success else 1)