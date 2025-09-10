#!/usr/bin/env python3
"""
Debug script to test the enhanced web search functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'generated_capabilities'))

from enhanced_web_search_automation import EnhancedWebSearchAutomation
import requests
from bs4 import BeautifulSoup
import urllib.parse

def test_duckduckgo_search():
    """Test DuckDuckGo search directly"""
    query = "best iphone 13 case"
    
    print(f"Testing DuckDuckGo search for: {query}")
    print("=" * 50)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    
    try:
        # Test HTML search
        search_url = f"https://duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        print(f"URL: {search_url}")
        
        response = session.get(search_url, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Content Length: {len(response.content)}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Check what we actually get
            print("\nLooking for result divs...")
            results = soup.find_all('div', class_='result')
            print(f"Found {len(results)} result divs")
            
            if not results:
                # Try different selectors
                print("\nTrying alternative selectors...")
                
                # Look for any divs with 'result' in class name
                alt_results = soup.find_all('div', class_=lambda x: x and 'result' in x)
                print(f"Found {len(alt_results)} divs with 'result' in class")
                
                # Look for links
                links = soup.find_all('a', href=True)
                print(f"Found {len(links)} total links")
                
                # Show first few links
                for i, link in enumerate(links[:5]):
                    href = link.get('href')
                    text = link.get_text().strip()[:50]
                    print(f"  {i+1}. {href} - {text}")
            
            else:
                print("\nProcessing results...")
                for i, result in enumerate(results[:3]):
                    print(f"\nResult {i+1}:")
                    
                    link_elem = result.find('a', class_='result__a')
                    title_elem = result.find('h2', class_='result__title')
                    snippet_elem = result.find('a', class_='result__snippet')
                    
                    print(f"  Link elem: {link_elem is not None}")
                    print(f"  Title elem: {title_elem is not None}")
                    print(f"  Snippet elem: {snippet_elem is not None}")
                    
                    if link_elem:
                        url = link_elem.get('href')
                        print(f"  URL: {url}")
                    
                    if title_elem:
                        title = title_elem.get_text().strip()
                        print(f"  Title: {title}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

def test_enhanced_search():
    """Test the enhanced search automation"""
    print("\n" + "=" * 50)
    print("Testing Enhanced Search Automation")
    print("=" * 50)
    
    search_automation = EnhancedWebSearchAutomation()
    
    test_queries = [
        "best iphone 13 case",
        "github repo for react",
        "npm package for express"
    ]
    
    for query in test_queries:
        print(f"\nTesting: {query}")
        print("-" * 30)
        
        result = search_automation.search_and_open(query)
        
        print(f"Success: {result['success']}")
        if result['success']:
            print(f"URL: {result['opened_url']}")
            print(f"Title: {result['title']}")
            print(f"Type: {result['query_type']}")
        else:
            print(f"Error: {result['error']}")

if __name__ == "__main__":
    test_duckduckgo_search()
    test_enhanced_search()