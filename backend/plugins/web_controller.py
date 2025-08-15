import requests
import webbrowser
import logging
import os
import time
import urllib.parse
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class WebController:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.download_dir = Path.home() / 'Downloads'
    
    def search_web(self, query: str) -> str:
        """Perform a web search and return results."""
        try:
            # Open search in default browser
            search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
            webbrowser.open(search_url)
            
            # Also try to get some quick results
            try:
                # Use DuckDuckGo Instant Answer API for quick results
                api_url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1&skip_disambig=1"
                
                response = self.session.get(api_url, timeout=5)
                data = response.json()
                
                result = f"Opened web search for '{query}'\n\n"
                
                # Extract useful information
                if data.get('Abstract'):
                    result += f"Quick Answer: {data['Abstract']}\n"
                
                if data.get('Definition'):
                    result += f"Definition: {data['Definition']}\n"
                
                if data.get('RelatedTopics'):
                    result += f"\nRelated Topics:\n"
                    for topic in data['RelatedTopics'][:3]:
                        if isinstance(topic, dict) and topic.get('Text'):
                            result += f"• {topic['Text']}\n"
                
                return result
                
            except Exception as e:
                logger.warning(f"Failed to get quick results: {str(e)}")
                return f"Opened web search for '{query}'"
            
        except Exception as e:
            logger.error(f"Error performing web search: {str(e)}")
            return f"Failed to search web: {str(e)}"
    
    def browse_url(self, url: str) -> str:
        """Open a URL in the default browser."""
        try:
            # Add protocol if missing
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Open URL in browser
            webbrowser.open(url)
            
            # Try to get page title
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    # Simple title extraction
                    content = response.text
                    if '<title>' in content:
                        title_start = content.find('<title>') + 7
                        title_end = content.find('</title>', title_start)
                        if title_end > title_start:
                            title = content[title_start:title_end].strip()
                            return f"Opened: {title}\nURL: {url}"
                
                return f"Opened URL: {url}"
                
            except Exception as e:
                logger.warning(f"Failed to get page info: {str(e)}")
                return f"Opened URL: {url}"
            
        except Exception as e:
            logger.error(f"Error browsing URL: {str(e)}")
            return f"Failed to open URL: {str(e)}"
    
    def download_file(self, url: str, filename: Optional[str] = None) -> str:
        """Download a file from URL."""
        try:
            # Add protocol if missing
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Get filename from URL if not provided
            if not filename:
                parsed_url = urllib.parse.urlparse(url)
                filename = os.path.basename(parsed_url.path)
                if not filename or '.' not in filename:
                    filename = 'downloaded_file'
            
            # Ensure download directory exists
            self.download_dir.mkdir(exist_ok=True)
            
            file_path = self.download_dir / filename
            
            # Download the file
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(file_path, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
            
            size_mb = file_path.stat().st_size / (1024 * 1024)
            
            return f"Downloaded: {filename}\nSize: {size_mb:.2f} MB\nLocation: {file_path}"
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Download failed: {str(e)}")
            return f"Failed to download from {url}: {str(e)}"
        except Exception as e:
            logger.error(f"Error downloading file: {str(e)}")
            return f"Error downloading file: {str(e)}"
    
    def get_page_content(self, url: str) -> str:
        """Get the text content of a web page."""
        try:
            # Add protocol if missing
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            # Try to extract readable content
            content = response.text
            
            # Simple content extraction (in a real app, you'd use BeautifulSoup)
            # Remove scripts and styles
            import re
            content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
            content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
            
            # Remove HTML tags
            content = re.sub(r'<[^>]+>', '', content)
            
            # Clean up whitespace
            content = re.sub(r'\s+', ' ', content).strip()
            
            # Limit content length
            if len(content) > 2000:
                content = content[:2000] + "..."
            
            return f"Content from {url}:\n\n{content}"
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get page content: {str(e)}")
            return f"Failed to get content from {url}: {str(e)}"
        except Exception as e:
            logger.error(f"Error getting page content: {str(e)}")
            return f"Error getting page content: {str(e)}"
    
    def check_website_status(self, url: str) -> str:
        """Check if a website is accessible."""
        try:
            # Add protocol if missing
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            start_time = time.time()
            response = self.session.head(url, timeout=10, allow_redirects=True)
            response_time = (time.time() - start_time) * 1000
            
            status_info = []
            status_info.append(f"URL: {url}")
            status_info.append(f"Status: {response.status_code} {response.reason}")
            status_info.append(f"Response Time: {response_time:.2f}ms")
            
            if response.headers.get('content-type'):
                status_info.append(f"Content Type: {response.headers['content-type']}")
            
            if response.headers.get('server'):
                status_info.append(f"Server: {response.headers['server']}")
            
            return "\n".join(status_info)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Website check failed: {str(e)}")
            return f"Website {url} is not accessible: {str(e)}"
        except Exception as e:
            logger.error(f"Error checking website: {str(e)}")
            return f"Error checking website: {str(e)}"
    
    def api_request(self, url: str, method: str = 'GET', headers: Optional[Dict] = None, data: Optional[Dict] = None) -> str:
        """Make an API request."""
        try:
            method = method.upper()
            headers = headers or {}
            
            # Merge with session headers
            request_headers = {**self.session.headers, **headers}
            
            if method == 'GET':
                response = self.session.get(url, headers=request_headers, params=data, timeout=15)
            elif method == 'POST':
                response = self.session.post(url, headers=request_headers, json=data, timeout=15)
            elif method == 'PUT':
                response = self.session.put(url, headers=request_headers, json=data, timeout=15)
            elif method == 'DELETE':
                response = self.session.delete(url, headers=request_headers, timeout=15)
            else:
                return f"Unsupported HTTP method: {method}"
            
            result = []
            result.append(f"API Request: {method} {url}")
            result.append(f"Status: {response.status_code} {response.reason}")
            
            # Try to format response as JSON
            try:
                json_data = response.json()
                import json
                formatted_json = json.dumps(json_data, indent=2)
                if len(formatted_json) > 1000:
                    formatted_json = formatted_json[:1000] + "\n... (truncated)"
                result.append(f"Response:\n{formatted_json}")
            except:
                # If not JSON, show text response
                text_response = response.text
                if len(text_response) > 500:
                    text_response = text_response[:500] + "... (truncated)"
                result.append(f"Response:\n{text_response}")
            
            return "\n\n".join(result)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            return f"API request failed: {str(e)}"
        except Exception as e:
            logger.error(f"Error making API request: {str(e)}")
            return f"Error making API request: {str(e)}"
