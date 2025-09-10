#!/usr/bin/env python3
"""
Demo of Browser Automation Features
Shows working web browser interaction capabilities without network dependencies.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'generated_capabilities'))

from simple_browser_automation import SimpleBrowserAutomation
import tempfile

def create_demo_html():
    """Create a demo HTML file for testing."""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Demo Web Page for Browser Automation</title>
</head>
<body>
    <h1>Welcome to Browser Automation Demo</h1>
    
    <p>This is a demo page to test browser automation capabilities.</p>
    
    <h2>Features Demonstrated:</h2>
    <ul>
        <li>Page title extraction</li>
        <li>Text content extraction</li>
        <li>Link discovery</li>
        <li>Image detection</li>
        <li>Form identification</li>
    </ul>
    
    <h2>Sample Links:</h2>
    <a href="https://example.com" title="Example Website">Example.com</a><br>
    <a href="/about" title="About Page">About Us</a><br>
    <a href="mailto:test@example.com" title="Contact Email">Contact</a>
    
    <h2>Sample Images:</h2>
    <img src="/images/logo.png" alt="Company Logo" title="Our Logo">
    <img src="https://via.placeholder.com/150" alt="Placeholder Image">
    
    <h2>Sample Form:</h2>
    <form action="/submit" method="post">
        <input type="text" name="username" placeholder="Username">
        <input type="email" name="email" placeholder="Email">
        <button type="submit">Submit</button>
    </form>
    
    <p>This page contains various HTML elements to test browser automation features.</p>
    
    <div id="hidden-content" style="display: none;">Hidden content for testing</div>
    
    <script>
        console.log("Demo page loaded successfully!");
    </script>
</body>
</html>
"""
    
    # Create temporary HTML file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        f.write(html_content)
        return f.name

def demo_browser_automation():
    """Demonstrate browser automation capabilities."""
    
    print("🌐 Browser Automation Features Demo")
    print("=" * 50)
    print("Demonstrating enhanced web browser interaction capabilities")
    print()
    
    # Create browser instance
    browser = SimpleBrowserAutomation()
    
    # Create demo HTML file
    html_file = create_demo_html()
    file_url = f"file://{html_file}"
    
    print(f"📄 Created demo HTML file: {html_file}")
    print(f"🔗 File URL: {file_url}")
    print()
    
    try:
        # Test 1: URL Validation
        print("1️⃣ URL Validation Features:")
        print("-" * 30)
        
        test_urls = [
            "https://www.google.com",
            "http://example.com", 
            "invalid-url",
            "ftp://files.example.com",
            file_url
        ]
        
        for url in test_urls:
            result = browser.validate_url(url)
            status = "✅" if result['valid'] else "❌"
            print(f"  {status} {url}")
            print(f"     Valid: {result['valid']}, Format OK: {not result.get('error', '').startswith('Missing')}")
            if 'error' in result and result['error']:
                print(f"     Note: {result['error'][:60]}...")
        
        print()
        
        # Test 2: Page Opening and Content Extraction
        print("2️⃣ Page Content Extraction:")
        print("-" * 30)
        
        result = browser.open_page(file_url)
        if result['success']:
            print(f"  ✅ Successfully opened page")
            print(f"  📄 Title: {result['title']}")
            print(f"  📊 Status: {result['status_code']}")
            print(f"  📏 Content Length: {result['content_length']} bytes")
            
            # Extract text content
            text = browser.get_page_text(max_length=300)
            print(f"  📝 Text Preview: {text[:150]}...")
            
        else:
            print(f"  ❌ Failed to open page: {result['error']}")
        
        print()
        
        # Test 3: Link Discovery
        print("3️⃣ Link Discovery:")
        print("-" * 20)
        
        links = browser.find_links(limit=5)
        print(f"  🔗 Found {len(links)} links:")
        for i, link in enumerate(links, 1):
            print(f"    {i}. {link['text'][:30]} -> {link['url'][:50]}")
            if link['title']:
                print(f"       Title: {link['title']}")
        
        print()
        
        # Test 4: Image Detection
        print("4️⃣ Image Detection:")
        print("-" * 20)
        
        images = browser.find_images(limit=5)
        print(f"  🖼️ Found {len(images)} images:")
        for i, img in enumerate(images, 1):
            print(f"    {i}. {img['alt'][:30]} -> {img['src'][:50]}")
            if img['title']:
                print(f"       Title: {img['title']}")
        
        print()
        
        # Test 5: Text Search
        print("5️⃣ Text Search:")
        print("-" * 15)
        
        search_terms = ["automation", "demo", "features"]
        for term in search_terms:
            results = browser.search_text(term, case_sensitive=False)
            print(f"  🔍 '{term}': {len(results)} matches")
            if results:
                print(f"     Context: {results[0][:80]}...")
        
        print()
        
        # Test 6: Page Information Summary
        print("6️⃣ Page Information Summary:")
        print("-" * 30)
        
        info = browser.get_page_info()
        if 'error' not in info:
            print(f"  📊 Page Statistics:")
            print(f"     • Title: {info['title']}")
            print(f"     • Links: {info['link_count']}")
            print(f"     • Images: {info['image_count']}")
            print(f"     • Forms: {info['form_count']}")
            print(f"     • Content Type: {info['content_type']}")
            print(f"     • Encoding: {info['encoding']}")
        
        print()
        print("✨ Enhanced Browser Interaction Features:")
        print("  ✅ URL validation and format checking")
        print("  ✅ Page content extraction and parsing")
        print("  ✅ Title and text extraction")
        print("  ✅ Link discovery and analysis")
        print("  ✅ Image detection and metadata")
        print("  ✅ Text search with context")
        print("  ✅ Comprehensive page analysis")
        print("  ✅ Error handling and validation")
        
        print()
        print("🚀 Ready for Enhanced Features:")
        print("  • Selenium WebDriver integration")
        print("  • JavaScript execution")
        print("  • Element clicking and interaction")
        print("  • Form filling and submission")
        print("  • Screenshot capture")
        print("  • Cookie and session management")
        
    finally:
        # Clean up temporary file
        try:
            os.unlink(html_file)
            print(f"\n🧹 Cleaned up demo file: {html_file}")
        except:
            pass

if __name__ == "__main__":
    demo_browser_automation()