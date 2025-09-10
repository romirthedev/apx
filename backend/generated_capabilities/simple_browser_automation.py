#!/usr/bin/env python3
"""
Simple Browser Automation Capability
Generated to demonstrate basic web browser interaction features.
"""

import requests
from bs4 import BeautifulSoup
import urllib.parse
import time
import json
from typing import Dict, List, Optional, Any

class SimpleBrowserAutomation:
    """A simple browser automation tool with basic web interaction capabilities."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.last_response = None
        self.last_soup = None
    
    def open_page(self, url: str, timeout: int = 10) -> Dict[str, Any]:
        """Open a webpage and return basic information about it."""
        try:
            # Validate URL format
            parsed = urllib.parse.urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return {
                    'success': False,
                    'error': 'Invalid URL format',
                    'url': url
                }
            
            # Make request
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            
            self.last_response = response
            self.last_soup = BeautifulSoup(response.content, 'html.parser')
            
            return {
                'success': True,
                'url': url,
                'status_code': response.status_code,
                'title': self.get_page_title(),
                'content_length': len(response.content),
                'content_type': response.headers.get('content-type', 'unknown')
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Request failed: {str(e)}',
                'url': url
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'url': url
            }
    
    def get_page_title(self) -> str:
        """Get the title of the currently loaded page."""
        if not self.last_soup:
            return "No page loaded"
        
        title_tag = self.last_soup.find('title')
        return title_tag.get_text().strip() if title_tag else "No title found"
    
    def get_page_text(self, max_length: int = 1000) -> str:
        """Extract visible text from the currently loaded page."""
        if not self.last_soup:
            return "No page loaded"
        
        # Remove script and style elements
        for script in self.last_soup(["script", "style"]):
            script.decompose()
        
        # Get text
        text = self.last_soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length] + "..."
        
        return text
    
    def find_links(self, limit: int = 10) -> List[Dict[str, str]]:
        """Find all links on the currently loaded page."""
        if not self.last_soup:
            return []
        
        links = []
        for link in self.last_soup.find_all('a', href=True)[:limit]:
            href = link['href']
            text = link.get_text().strip()
            
            # Convert relative URLs to absolute
            if self.last_response:
                href = urllib.parse.urljoin(self.last_response.url, href)
            
            links.append({
                'url': href,
                'text': text,
                'title': link.get('title', '')
            })
        
        return links
    
    def find_images(self, limit: int = 5) -> List[Dict[str, str]]:
        """Find all images on the currently loaded page."""
        if not self.last_soup:
            return []
        
        images = []
        for img in self.last_soup.find_all('img', src=True)[:limit]:
            src = img['src']
            
            # Convert relative URLs to absolute
            if self.last_response:
                src = urllib.parse.urljoin(self.last_response.url, src)
            
            images.append({
                'src': src,
                'alt': img.get('alt', ''),
                'title': img.get('title', '')
            })
        
        return images
    
    def validate_url(self, url: str) -> Dict[str, Any]:
        """Validate if a URL is properly formatted and accessible."""
        try:
            # Parse URL
            parsed = urllib.parse.urlparse(url)
            
            # Check basic format
            if not parsed.scheme:
                return {
                    'valid': False,
                    'accessible': False,
                    'error': 'Missing URL scheme (http/https)'
                }
            
            if not parsed.netloc:
                return {
                    'valid': False,
                    'accessible': False,
                    'error': 'Missing domain name'
                }
            
            # Check if accessible
            try:
                response = requests.head(url, timeout=5, allow_redirects=True)
                accessible = response.status_code < 400
                
                return {
                    'valid': True,
                    'accessible': accessible,
                    'status_code': response.status_code,
                    'final_url': response.url,
                    'content_type': response.headers.get('content-type', 'unknown')
                }
                
            except requests.exceptions.RequestException as e:
                return {
                    'valid': True,
                    'accessible': False,
                    'error': f'Not accessible: {str(e)}'
                }
                
        except Exception as e:
            return {
                'valid': False,
                'accessible': False,
                'error': f'Invalid URL: {str(e)}'
            }
    
    def search_text(self, search_term: str, case_sensitive: bool = False) -> List[str]:
        """Search for text on the currently loaded page."""
        if not self.last_soup:
            return []
        
        text = self.get_page_text(max_length=10000)
        
        if not case_sensitive:
            text = text.lower()
            search_term = search_term.lower()
        
        # Find all occurrences
        results = []
        start = 0
        while True:
            pos = text.find(search_term, start)
            if pos == -1:
                break
            
            # Get context around the match
            context_start = max(0, pos - 50)
            context_end = min(len(text), pos + len(search_term) + 50)
            context = text[context_start:context_end].strip()
            
            results.append(context)
            start = pos + 1
        
        return results[:10]  # Limit to 10 results
    
    def get_page_info(self) -> Dict[str, Any]:
        """Get comprehensive information about the currently loaded page."""
        if not self.last_response or not self.last_soup:
            return {'error': 'No page loaded'}
        
        return {
            'url': self.last_response.url,
            'title': self.get_page_title(),
            'status_code': self.last_response.status_code,
            'content_type': self.last_response.headers.get('content-type', 'unknown'),
            'content_length': len(self.last_response.content),
            'text_preview': self.get_page_text(max_length=200),
            'link_count': len(self.last_soup.find_all('a', href=True)),
            'image_count': len(self.last_soup.find_all('img', src=True)),
            'form_count': len(self.last_soup.find_all('form')),
            'encoding': self.last_response.encoding
        }

# Example usage and testing
if __name__ == "__main__":
    browser = SimpleBrowserAutomation()
    
    print("🌐 Testing Simple Browser Automation")
    print("=" * 40)
    
    # Test URL validation
    print("\n1. Testing URL validation:")
    test_urls = [
        "https://httpbin.org/html",
        "http://example.com",
        "invalid-url",
        "https://nonexistent-domain-12345.com"
    ]
    
    for url in test_urls:
        result = browser.validate_url(url)
        print(f"  {url}: Valid={result['valid']}, Accessible={result['accessible']}")
        if 'error' in result:
            print(f"    Error: {result['error']}")
    
    # Test opening a page
    print("\n2. Testing page opening:")
    result = browser.open_page("https://httpbin.org/html")
    if result['success']:
        print(f"  ✅ Opened: {result['title']}")
        print(f"  Status: {result['status_code']}")
        
        # Test text extraction
        print("\n3. Testing text extraction:")
        text = browser.get_page_text(max_length=200)
        print(f"  Text preview: {text}")
        
        # Test link finding
        print("\n4. Testing link finding:")
        links = browser.find_links(limit=3)
        for link in links:
            print(f"  Link: {link['text']} -> {link['url']}")
        
        # Test page info
        print("\n5. Testing page info:")
        info = browser.get_page_info()
        print(f"  Links: {info['link_count']}, Images: {info['image_count']}")
        
    else:
        print(f"  ❌ Failed: {result['error']}")
    
    print("\n✅ Browser automation testing completed!")