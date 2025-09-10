#!/usr/bin/env python3
"""
Test script to verify the Web Search integration works correctly
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.generated_capabilities.enhanced_web_search_automation import EnhancedWebSearchAutomation

def test_web_search_integration():
    """Test the web search integration that will be called from the overlay"""
    print("🔍 Testing Web Search Integration")
    print("=" * 50)
    
    # Initialize the search automation
    search = EnhancedWebSearchAutomation()
    
    # Test queries that should work well
    test_queries = [
        "best iphone 13 case",
        "github repo for react",
        "npm package for express",
        "python requests documentation"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Testing: {query}")
        print("-" * 30)
        
        try:
            result = search.search_and_open(query)
            
            if result['success']:
                print(f"✅ SUCCESS")
                print(f"📄 Title: {result.get('title', 'N/A')}")
                print(f"🔗 URL: {result.get('opened_url', 'N/A')}")
                print(f"🎯 Type: {result.get('query_type', 'N/A')}")
                
                # Format the output as expected by the IPC handler
                output_line = f"SUCCESS:{result['success']}:{result.get('title', '')}:{result.get('opened_url', '')}:{result.get('query_type', '')}"
                print(f"📤 IPC Output: {output_line}")
            else:
                print(f"❌ FAILED: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"💥 ERROR: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎯 Web Search Integration Test Complete")

if __name__ == "__main__":
    test_web_search_integration()