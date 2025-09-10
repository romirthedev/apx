#!/usr/bin/env python3
"""
Working Browser Automation Demo
Demonstrates enhanced web browser interaction capabilities with a local server.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'generated_capabilities'))

from simple_browser_automation import SimpleBrowserAutomation
import http.server
import socketserver
import threading
import time
import tempfile

def create_demo_html():
    """Create a comprehensive demo HTML file."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enhanced Browser Automation Demo</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .feature { background: #f0f0f0; padding: 10px; margin: 10px 0; }
        .highlight { background: yellow; }
    </style>
</head>
<body>
    <h1>🌐 Enhanced Browser Automation Demo</h1>
    
    <div class="feature">
        <h2>✨ Key Features Demonstrated:</h2>
        <ul>
            <li><strong>URL Validation</strong> - Check if URLs are properly formatted</li>
            <li><strong>Page Content Extraction</strong> - Get title, text, and metadata</li>
            <li><strong>Link Discovery</strong> - Find and analyze all links on the page</li>
            <li><strong>Image Detection</strong> - Locate images with metadata</li>
            <li><strong>Text Search</strong> - Search for specific content with context</li>
            <li><strong>Form Analysis</strong> - Identify forms and input elements</li>
        </ul>
    </div>
    
    <div class="feature">
        <h2>🔗 Sample Navigation Links:</h2>
        <p>These links demonstrate link discovery capabilities:</p>
        <a href="https://www.google.com" title="Google Search Engine">Google</a> |
        <a href="https://github.com" title="GitHub Code Repository">GitHub</a> |
        <a href="/about" title="About This Demo">About Page</a> |
        <a href="mailto:demo@example.com" title="Contact Email">Contact Us</a>
    </div>
    
    <div class="feature">
        <h2>🖼️ Sample Images:</h2>
        <p>These images test image detection features:</p>
        <img src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgZmlsbD0iIzAwN2NiYSIvPjx0ZXh0IHg9IjUwIiB5PSI1NSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjE0IiBmaWxsPSJ3aGl0ZSIgdGV4dC1hbmNob3I9Im1pZGRsZSI+TG9nbzwvdGV4dD48L3N2Zz4=" 
             alt="Demo Logo" title="Company Logo" width="100" height="100">
        <img src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTUwIiBoZWlnaHQ9IjEwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTUwIiBoZWlnaHQ9IjEwMCIgZmlsbD0iIzI4YTc0NSIvPjx0ZXh0IHg9Ijc1IiB5PSI1NSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjEyIiBmaWxsPSJ3aGl0ZSIgdGV4dC1hbmNob3I9Im1pZGRsZSI+UGxhY2Vob2xkZXI8L3RleHQ+PC9zdmc+" 
             alt="Placeholder Image" title="Sample Placeholder">
    </div>
    
    <div class="feature">
        <h2>📝 Interactive Form:</h2>
        <p>This form demonstrates form detection capabilities:</p>
        <form action="/submit" method="post">
            <label for="name">Name:</label>
            <input type="text" id="name" name="name" placeholder="Enter your name" required><br><br>
            
            <label for="email">Email:</label>
            <input type="email" id="email" name="email" placeholder="your@email.com" required><br><br>
            
            <label for="message">Message:</label><br>
            <textarea id="message" name="message" rows="4" cols="50" placeholder="Your message here..."></textarea><br><br>
            
            <label for="category">Category:</label>
            <select id="category" name="category">
                <option value="general">General Inquiry</option>
                <option value="support">Technical Support</option>
                <option value="feedback">Feedback</option>
            </select><br><br>
            
            <input type="checkbox" id="newsletter" name="newsletter" value="yes">
            <label for="newsletter">Subscribe to newsletter</label><br><br>
            
            <button type="submit">Submit Form</button>
            <button type="reset">Reset</button>
        </form>
    </div>
    
    <div class="feature">
        <h2>🔍 Search Test Content:</h2>
        <p>This content is designed for <span class="highlight">text search testing</span>.</p>
        <p>The browser automation system can search for specific terms like:</p>
        <ul>
            <li><strong>automation</strong> - appears multiple times</li>
            <li><strong>browser</strong> - web browser interaction</li>
            <li><strong>features</strong> - enhanced capabilities</li>
            <li><strong>demo</strong> - demonstration content</li>
        </ul>
        <p>Advanced search capabilities include case-insensitive matching and context extraction.</p>
    </div>
    
    <div class="feature">
        <h2>📊 Page Statistics:</h2>
        <p>This page contains various HTML elements for comprehensive testing:</p>
        <ul>
            <li>Multiple headings (H1, H2)</li>
            <li>Paragraphs with rich text content</li>
            <li>External and internal links</li>
            <li>Images with alt text and titles</li>
            <li>Interactive form elements</li>
            <li>Lists and structured content</li>
            <li>CSS styling and classes</li>
        </ul>
    </div>
    
    <footer>
        <hr>
        <p><em>Enhanced Browser Automation Demo - Showcasing advanced web interaction capabilities</em></p>
        <p>Generated for testing browser automation features including content extraction, link discovery, and form analysis.</p>
    </footer>
    
    <script>
        console.log("Enhanced browser automation demo page loaded successfully!");
        console.log("Features: URL validation, content extraction, link discovery, image detection, text search");
    </script>
</body>
</html>
"""

def start_demo_server(html_content, port=8000):
    """Start a simple HTTP server with the demo content."""
    
    class DemoHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/' or self.path == '/index.html':
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(html_content.encode('utf-8'))
            else:
                self.send_response(404)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'<h1>404 - Page Not Found</h1>')
    
    # Find available port
    for test_port in range(port, port + 10):
        try:
            with socketserver.TCPServer(("", test_port), DemoHandler) as httpd:
                print(f"🌐 Starting demo server on http://localhost:{test_port}")
                
                # Start server in background thread
                server_thread = threading.Thread(target=httpd.serve_forever)
                server_thread.daemon = True
                server_thread.start()
                
                return httpd, test_port
        except OSError:
            continue
    
    raise Exception("Could not find available port")

def demo_enhanced_browser_automation():
    """Demonstrate enhanced browser automation capabilities."""
    
    print("🚀 Enhanced Browser Automation Demo")
    print("=" * 60)
    print("Showcasing advanced web browser interaction capabilities")
    print()
    
    # Create demo HTML content
    html_content = create_demo_html()
    
    # Start demo server
    try:
        httpd, port = start_demo_server(html_content)
        demo_url = f"http://localhost:{port}"
        
        print(f"✅ Demo server started successfully")
        print(f"🔗 Demo URL: {demo_url}")
        print()
        
        # Give server time to start
        time.sleep(1)
        
        # Create browser instance
        browser = SimpleBrowserAutomation()
        
        # Test 1: URL Validation
        print("1️⃣ Enhanced URL Validation:")
        print("-" * 35)
        
        test_urls = [
            demo_url,
            "https://www.google.com",
            "invalid-url-format",
            "http://nonexistent-domain-12345.com",
            "ftp://files.example.com"
        ]
        
        for url in test_urls:
            result = browser.validate_url(url)
            status = "✅" if result['valid'] else "❌"
            accessible = "🌐" if result.get('accessible') else "🚫"
            print(f"  {status} {accessible} {url[:50]}")
            if result['valid']:
                print(f"     Format: Valid, Accessible: {result.get('accessible', 'Unknown')}")
            else:
                print(f"     Error: {result.get('error', 'Unknown error')[:50]}")
        
        print()
        
        # Test 2: Page Content Extraction
        print("2️⃣ Advanced Content Extraction:")
        print("-" * 35)
        
        result = browser.open_page(demo_url)
        if result['success']:
            print(f"  ✅ Successfully loaded demo page")
            print(f"  📄 Title: '{result['title']}'")
            print(f"  📊 Status Code: {result['status_code']}")
            print(f"  📏 Content Size: {result['content_length']:,} bytes")
            print(f"  🗂️ Content Type: {result['content_type']}")
            
            # Extract and display text preview
            text = browser.get_page_text(max_length=200)
            print(f"  📝 Text Preview: '{text[:100]}...'")
            
        else:
            print(f"  ❌ Failed to load page: {result['error']}")
            return
        
        print()
        
        # Test 3: Link Discovery and Analysis
        print("3️⃣ Intelligent Link Discovery:")
        print("-" * 35)
        
        links = browser.find_links(limit=8)
        print(f"  🔗 Discovered {len(links)} links:")
        for i, link in enumerate(links, 1):
            link_text = link['text'][:25] if link['text'] else "[No text]"
            link_url = link['url'][:40] if len(link['url']) > 40 else link['url']
            print(f"    {i}. '{link_text}' → {link_url}")
            if link['title']:
                print(f"       Title: '{link['title'][:30]}'")
        
        print()
        
        # Test 4: Image Detection and Metadata
        print("4️⃣ Smart Image Detection:")
        print("-" * 30)
        
        images = browser.find_images(limit=5)
        print(f"  🖼️ Found {len(images)} images:")
        for i, img in enumerate(images, 1):
            alt_text = img['alt'][:25] if img['alt'] else "[No alt text]"
            src_preview = img['src'][:40] if len(img['src']) > 40 else img['src']
            print(f"    {i}. Alt: '{alt_text}'")
            print(f"       Src: {src_preview}")
            if img['title']:
                print(f"       Title: '{img['title'][:30]}'")
        
        print()
        
        # Test 5: Advanced Text Search
        print("5️⃣ Contextual Text Search:")
        print("-" * 30)
        
        search_terms = ["automation", "browser", "features", "demo", "enhanced"]
        for term in search_terms:
            results = browser.search_text(term, case_sensitive=False)
            print(f"  🔍 '{term}': {len(results)} matches found")
            if results:
                context = results[0][:60].replace('\n', ' ')
                print(f"     Context: '...{context}...'")
        
        print()
        
        # Test 6: Comprehensive Page Analysis
        print("6️⃣ Complete Page Analysis:")
        print("-" * 30)
        
        info = browser.get_page_info()
        if 'error' not in info:
            print(f"  📊 Comprehensive Statistics:")
            print(f"     • Page Title: '{info['title']}'")
            print(f"     • Total Links: {info['link_count']}")
            print(f"     • Total Images: {info['image_count']}")
            print(f"     • Interactive Forms: {info['form_count']}")
            print(f"     • Content Encoding: {info['encoding']}")
            print(f"     • Response Size: {info['content_length']:,} bytes")
        
        print()
        print("✨ Enhanced Browser Interaction Capabilities:")
        print("  ✅ Advanced URL validation with accessibility checking")
        print("  ✅ Intelligent content extraction and parsing")
        print("  ✅ Smart link discovery with metadata analysis")
        print("  ✅ Image detection with alt text and title extraction")
        print("  ✅ Contextual text search with surrounding content")
        print("  ✅ Comprehensive page statistics and analysis")
        print("  ✅ Robust error handling and validation")
        print("  ✅ Support for various content types and encodings")
        
        print()
        print("🚀 Ready for Advanced Features:")
        print("  • Selenium WebDriver for JavaScript execution")
        print("  • Element interaction (clicking, typing, scrolling)")
        print("  • Form automation and submission")
        print("  • Screenshot capture and visual testing")
        print("  • Cookie and session management")
        print("  • Multi-page navigation and crawling")
        print("  • Dynamic content handling and waiting")
        
    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up server
        try:
            httpd.shutdown()
            print(f"\n🧹 Demo server stopped")
        except:
            pass

if __name__ == "__main__":
    demo_enhanced_browser_automation()