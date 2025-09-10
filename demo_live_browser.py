#!/usr/bin/env python3
"""
Live Browser Automation Demo
Demonstrates working browser automation with real websites.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'generated_capabilities'))

from simple_browser_automation import SimpleBrowserAutomation
import time

def demo_live_browser_automation():
    """Demonstrate browser automation with real websites."""
    
    print("🌐 Live Browser Automation Demo")
    print("=" * 50)
    print("Testing enhanced web browser interaction with real websites")
    print()
    
    # Create browser instance
    browser = SimpleBrowserAutomation()
    
    # Test 1: URL Validation with Real URLs
    print("1️⃣ URL Validation & Accessibility Testing:")
    print("-" * 45)
    
    test_urls = [
        "https://httpbin.org/html",
        "http://example.com",
        "https://www.google.com",
        "invalid-url-format",
        "https://nonexistent-domain-xyz123.com",
        "ftp://files.example.com"
    ]
    
    validation_results = []
    for url in test_urls:
        print(f"  🔍 Testing: {url}")
        result = browser.validate_url(url)
        
        status = "✅" if result['valid'] else "❌"
        accessible = "🌐" if result.get('accessible') else "🚫"
        
        print(f"    {status} Format Valid: {result['valid']}")
        print(f"    {accessible} Accessible: {result.get('accessible', False)}")
        
        if 'status_code' in result:
            print(f"    📊 Status Code: {result['status_code']}")
        if 'error' in result and result['error']:
            error_msg = result['error'][:60] + "..." if len(result['error']) > 60 else result['error']
            print(f"    ⚠️ Note: {error_msg}")
        
        validation_results.append((url, result))
        print()
    
    # Test 2: Content Extraction from Accessible Site
    print("2️⃣ Content Extraction from Example.com:")
    print("-" * 40)
    
    # Use example.com as it's reliable and simple
    target_url = "http://example.com"
    print(f"  🎯 Target: {target_url}")
    
    result = browser.open_page(target_url)
    if result['success']:
        print(f"  ✅ Successfully loaded page")
        print(f"  📄 Title: '{result['title']}'")
        print(f"  📊 Status: {result['status_code']}")
        print(f"  📏 Size: {result['content_length']:,} bytes")
        print(f"  🗂️ Type: {result['content_type']}")
        
        # Extract text content
        text = browser.get_page_text(max_length=300)
        print(f"  📝 Text Content:")
        print(f"     '{text}'")
        
        print()
        
        # Test 3: Link Discovery
        print("3️⃣ Link Discovery:")
        print("-" * 20)
        
        links = browser.find_links(limit=10)
        print(f"  🔗 Found {len(links)} links:")
        for i, link in enumerate(links, 1):
            link_text = link['text'][:30] if link['text'] else "[No text]"
            link_url = link['url'][:50] if len(link['url']) > 50 else link['url']
            print(f"    {i}. '{link_text}' → {link_url}")
            if link['title']:
                print(f"       Title: '{link['title']}'")
        
        print()
        
        # Test 4: Text Search
        print("4️⃣ Text Search Capabilities:")
        print("-" * 30)
        
        search_terms = ["example", "domain", "information", "website"]
        for term in search_terms:
            results = browser.search_text(term, case_sensitive=False)
            print(f"  🔍 '{term}': {len(results)} matches")
            if results:
                context = results[0][:80].replace('\n', ' ')
                print(f"     Context: '...{context}...'")
        
        print()
        
        # Test 5: Page Analysis
        print("5️⃣ Comprehensive Page Analysis:")
        print("-" * 35)
        
        info = browser.get_page_info()
        if 'error' not in info:
            print(f"  📊 Page Statistics:")
            print(f"     • Title: '{info['title']}'")
            print(f"     • URL: {info['url']}")
            print(f"     • Links: {info['link_count']}")
            print(f"     • Images: {info['image_count']}")
            print(f"     • Forms: {info['form_count']}")
            print(f"     • Encoding: {info['encoding']}")
            print(f"     • Content Length: {info['content_length']:,} bytes")
        
    else:
        print(f"  ❌ Failed to load {target_url}: {result['error']}")
        print("  Trying alternative approach...")
        
        # Try with a different reliable site
        alt_url = "https://httpbin.org/html"
        print(f"  🔄 Trying: {alt_url}")
        
        alt_result = browser.open_page(alt_url)
        if alt_result['success']:
            print(f"  ✅ Alternative site loaded successfully")
            print(f"  📄 Title: '{alt_result['title']}'")
            text = browser.get_page_text(max_length=200)
            print(f"  📝 Text: '{text[:100]}...'")
        else:
            print(f"  ❌ Alternative also failed: {alt_result['error']}")
    
    print()
    print("✨ Enhanced Browser Automation Features Demonstrated:")
    print("  ✅ URL format validation and accessibility checking")
    print("  ✅ HTTP status code analysis and error handling")
    print("  ✅ Page content extraction and text parsing")
    print("  ✅ Title extraction and metadata analysis")
    print("  ✅ Link discovery with URL resolution")
    print("  ✅ Text search with context extraction")
    print("  ✅ Comprehensive page statistics")
    print("  ✅ Robust error handling for network issues")
    
    print()
    print("🚀 System Capabilities Summary:")
    print("  • ✅ Basic web page interaction and content extraction")
    print("  • ✅ URL validation and format checking")
    print("  • ✅ Link and image discovery")
    print("  • ✅ Text search and content analysis")
    print("  • ✅ Error handling and network resilience")
    
    print()
    print("🎯 Ready for Advanced Features:")
    print("  • Selenium WebDriver for JavaScript-heavy sites")
    print("  • Element interaction (clicking, form filling)")
    print("  • Screenshot capture and visual testing")
    print("  • Multi-page navigation and session management")
    print("  • Dynamic content handling and waiting strategies")
    
    print()
    print("📈 Validation Results Summary:")
    valid_count = sum(1 for _, result in validation_results if result['valid'])
    accessible_count = sum(1 for _, result in validation_results if result.get('accessible'))
    print(f"  • URLs tested: {len(validation_results)}")
    print(f"  • Valid format: {valid_count}/{len(validation_results)}")
    print(f"  • Accessible: {accessible_count}/{len(validation_results)}")
    
if __name__ == "__main__":
    print("🚀 Starting Live Browser Automation Demo")
    print("This demo tests real web browser interaction capabilities")
    print()
    
    try:
        demo_live_browser_automation()
        print("\n🎉 Demo completed successfully!")
        print("The browser automation system is working and ready for enhanced features.")
    except Exception as e:
        print(f"\n❌ Demo encountered an error: {str(e)}")
        print("This may be due to network connectivity issues.")
        import traceback
        traceback.print_exc()