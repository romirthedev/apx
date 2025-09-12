#!/usr/bin/env python3
"""
Enhanced Web Search and Link Opening Automation

This module provides intelligent web search capabilities that can handle diverse queries
from general product searches to specific repository lookups, automatically finding
and opening the most relevant links.
"""

import requests
import webbrowser
import json
import re
import urllib.parse
import time
from typing import Dict, List, Any, Optional, Tuple
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedWebSearchAutomation:
    """Enhanced web search automation with intelligent link discovery and opening."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # Search engines and APIs
        self.search_engines = {
            'duckduckgo': 'https://api.duckduckgo.com/',
            'google': 'https://www.google.com/search',
            'bing': 'https://www.bing.com/search'
        }
        
        # Specialized search patterns
        self.search_patterns = {
            'github_repo': r'(?:github|gh)\s+(?:repo|repository)\s+(?:for|of|about)?\s*(.+)',
            'npm_package': r'npm\s+(?:package|module)\s+(?:for|of|about)?\s*(.+)',
            'pypi_package': r'(?:pypi|pip)\s+(?:package|module)\s+(?:for|of|about)?\s*(.+)',
            'product_search': r'(?:find|search|best|top|good|buy|purchase|get|need)\s+(.+?)(?:\s+(?:case|cover|accessory|product|item))?$',
            'documentation': r'(?:docs|documentation)\s+(?:for|of|about)?\s*(.+)',
            'tutorial': r'(?:tutorial|guide|how\s+to)\s+(.+)',
            'download': r'download\s+(.+)',
            'latest_model': r'(?:latest|newest|recent)\s+(.+?)\s+(?:model|version|release)'
        }
    
    def search_and_open(self, query: str) -> Dict[str, Any]:
        """Main method to search and open the most specific, best result."""
        try:
            logger.info(f"Processing search query: {query}")
            
            # Analyze query type
            query_type = self._analyze_query_type(query)
            logger.info(f"Detected query type: {query_type}")
            
            # For specific query types, use targeted deep search
            if query_type == 'product_search':
                return self._handle_product_search(query)
            elif query_type in ['tutorial', 'documentation']:
                return self._handle_learning_search(query)
            elif query_type == 'github_repo':
                return self._handle_github_search(query)
            else:
                # For general queries, still use enhanced search
                return self._handle_general_search(query, query_type)
            
        except Exception as e:
            logger.error(f"Error in search_and_open: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _analyze_query_type(self, query: str) -> str:
        """Analyze the query to determine the best search strategy."""
        query_lower = query.lower()
        
        # Check for specific patterns
        for pattern_name, pattern in self.search_patterns.items():
            if re.search(pattern, query_lower):
                return pattern_name
        
        # Default categorization
        if any(word in query_lower for word in ['github', 'repository', 'repo']):
            return 'github_repo'
        elif any(word in query_lower for word in ['npm', 'package', 'module']):
            return 'npm_package'
        elif any(word in query_lower for word in ['pip', 'pypi', 'python']):
            return 'pypi_package'
        elif any(word in query_lower for word in ['best', 'top', 'find', 'good', 'case', 'cover', 'headphones', 'earbuds', 'speaker', 'phone', 'laptop', 'computer', 'tablet', 'watch', 'camera', 'charger', 'cable', 'adapter', 'keyboard', 'mouse', 'monitor', 'tv', 'gaming', 'wireless', 'bluetooth', 'usb', 'hdmi', 'iphone', 'samsung', 'apple', 'google', 'sony', 'lg', 'hp', 'dell', 'buy', 'purchase', 'price', 'chocolate', 'food']):
            return 'product_search'
        elif any(word in query_lower for word in ['docs', 'documentation', 'api']):
            return 'documentation'
        elif any(word in query_lower for word in ['tutorial', 'guide', 'how to', 'learn']):
            return 'tutorial'
        elif any(word in query_lower for word in ['download', 'install']):
            return 'download'
        else:
            return 'general'
    
    def _extract_product_terms_smart(self, query: str) -> str:
        """Universal smart extraction of product terms preserving ALL important descriptors."""
        query_lower = query.lower().strip()
        original_query = query_lower  # Keep original for comparison
        
        # Step 1: Remove only leading action/intent words (be very conservative)
        leading_removal_patterns = [
            r'^(?:find me?\s+)',
            r'^(?:search for\s+)',
            r'^(?:i need\s+)',
            r'^(?:get me\s+)',
            r'^(?:looking for\s+)',
            r'^(?:want to buy\s+)',
            r'^(?:buy me?\s+)',
            r'^(?:purchase\s+)',
            r'^(?:show me\s+)',
            r'^(?:i want\s+)',
            r'^(?:get\s+)',
            r'^(?:need\s+)',
        ]
        
        for pattern in leading_removal_patterns:
            query_lower = re.sub(pattern, '', query_lower, flags=re.IGNORECASE)
        
        # Step 2: Clean up extra spaces
        query_lower = re.sub(r'\s+', ' ', query_lower).strip()
        
        # Step 3: Universal approach - preserve ALL descriptive content
        # Only remove truly generic qualifiers that add no value
        
        # Split into words for analysis
        words = query_lower.split()
        if not words:
            return original_query
        
        # Define words that are purely generic and can be safely removed
        # (Be very conservative - only remove words that truly add no search value)
        purely_generic_words = {
            'some', 'any', 'good', 'nice', 'decent', 'quality', 
            'product', 'item', 'thing', 'stuff', 'one'
        }
        
        # Define words that seem generic but are actually valuable for search
        # (These should NOT be removed as they often indicate quality/type)
        valuable_descriptors = {
            'best', 'top', 'premium', 'luxury', 'professional', 'commercial',
            'heavy', 'light', 'lightweight', 'durable', 'strong', 'soft', 'hard',
            'large', 'small', 'mini', 'compact', 'portable', 'wireless', 'wired',
            'fast', 'quick', 'slow', 'automatic', 'manual', 'digital', 'analog',
            'waterproof', 'water', 'resistant', 'proof', 'safe', 'secure',
            'cheap', 'expensive', 'affordable', 'budget', 'high', 'low',
            'new', 'latest', 'newest', 'modern', 'vintage', 'retro', 'classic',
            'smart', 'intelligent', 'basic', 'advanced', 'pro', 'standard'
        }
        
        # Step 4: Material/brand/specific descriptors (never remove these)
        material_brand_patterns = [
            r'\b(?:carbon|bamboo|wood|wooden|steel|stainless|aluminum|plastic|glass|ceramic|leather|fabric|cotton|silk|wool|metal|titanium|gold|silver|copper|bronze)\b',
            r'\b(?:apple|samsung|google|sony|lg|hp|dell|lenovo|asus|microsoft|adobe|nike|adidas|amazon|walmart|target)\b',
            r'\b(?:iphone|android|windows|mac|ios|linux|xbox|playstation|nintendo)\b',
            r'\b\d+(?:gb|tb|mb|kg|lb|oz|inch|ft|cm|mm|w|watt|amp|volt|hz|ghz|mhz)\b',
            r'\b(?:usb|hdmi|bluetooth|wifi|wireless|wired|magsafe|lightning|type-c|micro)\b'
        ]
        
        contains_specific_descriptors = any(
            re.search(pattern, query_lower, re.IGNORECASE) 
            for pattern in material_brand_patterns
        )
        
        # Step 5: Conservative filtering approach
        filtered_words = []
        for i, word in enumerate(words):
            # Always keep if:
            # - Contains numbers/measurements
            # - Is a valuable descriptor  
            # - Matches material/brand patterns
            # - Is not in the purely generic list
            # - Is the last word (often the product type)
            
            keep_word = (
                re.search(r'\d', word) or  # Contains numbers
                word in valuable_descriptors or
                any(re.search(pattern, word, re.IGNORECASE) for pattern in material_brand_patterns) or
                word not in purely_generic_words or
                i == len(words) - 1  # Last word (product type)
            )
            
            if keep_word:
                filtered_words.append(word)
        
        result = ' '.join(filtered_words) if filtered_words else query_lower
        
        # Step 6: Safety check - if we removed too much, use the original
        # (Preserve at least 60% of meaningful content)
        original_meaningful_words = [w for w in original_query.split() if len(w) > 2]
        result_words = result.split()
        
        if len(result_words) < len(original_meaningful_words) * 0.6:
            logger.info(f"Preserving original query - too much content would be removed")
            result = query_lower  # Use the version with just action words removed
        
        logger.info(f"Query extraction: '{original_query}' -> '{result}'")
        return result
    
    def _get_search_results(self, query: str, query_type: str) -> List[Dict[str, Any]]:
        """Get search results based on query type with robust fallbacks."""
        all_results = []
        
        try:
            # Try specialized searches first
            if query_type == 'github_repo':
                all_results.extend(self._search_github(query))
                # Fallback to general search if no GitHub results
                if not all_results:
                    all_results.extend(self._search_web_general(f"{query} github"))
                    
            elif query_type == 'npm_package':
                all_results.extend(self._search_npm(query))
                # Fallback to general search
                if not all_results:
                    all_results.extend(self._search_web_general(f"{query} npm"))
                    
            elif query_type == 'pypi_package':
                all_results.extend(self._search_pypi(query))
                # Fallback to general search
                if not all_results:
                    all_results.extend(self._search_web_general(f"{query} python package"))
                    
            else:
                # For all other query types, use general web search
                all_results.extend(self._search_web_general(query))
            
            # If we still don't have results, try a broader search
            if not all_results:
                logger.info(f"No results found, trying broader search for: {query}")
                # Try DuckDuckGo directly as last resort
                all_results.extend(self._search_duckduckgo(query))
                
                # If still no results, try simplified query
                if not all_results:
                    simplified_query = self._simplify_query(query)
                    if simplified_query != query:
                        all_results.extend(self._search_duckduckgo(simplified_query))
            
            # Remove duplicates and sort by score
            unique_results = []
            seen_urls = set()
            
            for result in sorted(all_results, key=lambda x: x.get('score', 0), reverse=True):
                if result['url'] not in seen_urls:
                    unique_results.append(result)
                    seen_urls.add(result['url'])
            
            return unique_results[:10]  # Return top 10 results
            
        except Exception as e:
            logger.error(f"Error getting search results: {str(e)}")
            return []
    
    def _handle_product_search(self, query: str) -> Dict[str, Any]:
        """Handle product searches with better term extraction and relevance matching."""
        try:
            # Use smart extraction to preserve important descriptors
            product_terms = self._extract_product_terms_smart(query)
            logger.info(f"Extracted product terms: '{product_terms}' from query: '{query}'")
            
            # First try to find specific highly-rated products with exact terms
            specific_results = self._find_specific_products(product_terms)
            
            if specific_results:
                # Score results based on relevance to original query
                scored_results = self._score_product_relevance(specific_results, product_terms, query)
                
                if scored_results:
                    best_result = scored_results[0]
                    logger.info(f"Opening most relevant product: {best_result['title']}")
                    logger.info(f"Relevance score: {best_result.get('relevance_score', 'N/A')} | Rating: {best_result.get('rating', 'N/A')} | Price: {best_result.get('price', 'N/A')}")
                    
                    try:
                        webbrowser.open(best_result['url'])
                        return {
                            'success': True,
                            'query': query,
                            'query_type': 'product_search',
                            'opened_url': best_result['url'],
                            'title': best_result['title'],
                            'rating': best_result.get('rating', 'N/A'),
                            'price': best_result.get('price', 'N/A'),
                            'relevance_score': best_result.get('relevance_score', 'N/A'),
                            'message': f"Opened relevant product: {best_result['title']}"
                        }
                    except Exception as e:
                        logger.warning(f"Error opening specific product: {e}")
            
            # Fallback to enhanced Amazon search with better query preservation
            amazon_url = f"https://www.amazon.com/s?k={urllib.parse.quote_plus(product_terms)}&s=review-rank&ref=sr_st_review-rank"
            
            # Try to get the first relevant product result from Amazon
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
                }
                
                response = requests.get(amazon_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for product results and check relevance
                    product_containers = soup.find_all('div', {'data-component-type': 's-search-result'})
                    
                    for container in product_containers[:5]:  # Check first 5 results
                        try:
                            # Extract title
                            title_elem = container.find('h2')
                            if title_elem:
                                title_link = title_elem.find('a')
                                if title_link:
                                    title = title_link.get_text(strip=True)
                                    href = title_link.get('href')
                                    
                                    # Check if this product matches our query terms
                                    relevance = self._calculate_text_relevance(title, product_terms)
                                    
                                    if relevance > 0.3:  # Minimum relevance threshold
                                        full_url = f"https://www.amazon.com{href}" if href.startswith('/') else href
                                        webbrowser.open(full_url)
                                        return {
                                            'success': True,
                                            'query': query,
                                            'query_type': 'product_search',
                                            'opened_url': full_url,
                                            'title': title,
                                            'relevance_score': f"{relevance:.2f}",
                                            'message': f"Opened relevant Amazon product: {title}"
                                        }
                        except Exception as e:
                            logger.warning(f"Error parsing Amazon product: {e}")
                            continue
            except Exception as e:
                logger.warning(f"Could not parse Amazon results: {e}")
            
            # Final fallback to Amazon search page with exact terms
            webbrowser.open(amazon_url)
            return {
                'success': True,
                'query': query,
                'query_type': 'product_search',
                'opened_url': amazon_url,
                'title': f"Amazon Search: {product_terms}",
                'message': f"Opened Amazon search for: {product_terms}"
            }
            
        except Exception as e:
            logger.error(f"Error in product search: {e}")
            return {'success': False, 'error': str(e)}
    
    def _score_product_relevance(self, products: List[Dict[str, Any]], product_terms: str, original_query: str) -> List[Dict[str, Any]]:
        """Score products based on relevance to the search terms."""
        scored_products = []
        
        for product in products:
            title = product.get('title', '').lower()
            snippet = product.get('snippet', '').lower()
            
            # Calculate relevance scores
            title_relevance = self._calculate_text_relevance(title, product_terms)
            snippet_relevance = self._calculate_text_relevance(snippet, product_terms)
            
            # Combined relevance score (title weighted more heavily)
            relevance_score = (title_relevance * 0.7) + (snippet_relevance * 0.3)
            
            # Boost score for exact matches of key terms
            key_terms = product_terms.split()
            for term in key_terms:
                if len(term) > 3 and term in title:
                    relevance_score += 0.2
            
            # Only include products with reasonable relevance
            if relevance_score > 0.2:
                product['relevance_score'] = relevance_score
                scored_products.append(product)
        
        # Sort by relevance score (with rating as tiebreaker)
        scored_products.sort(key=lambda x: (
            x['relevance_score'],
            float(x['rating']) if x['rating'] != 'N/A' else 0
        ), reverse=True)
        
        return scored_products
    
    def _calculate_text_relevance(self, text: str, query_terms: str) -> float:
        """Calculate how relevant a text is to the query terms."""
        if not text or not query_terms:
            return 0.0
        
        text_lower = text.lower()
        query_lower = query_terms.lower()
        
        # Exact match gets highest score
        if query_lower in text_lower:
            return 1.0
        
        # Calculate word overlap
        text_words = set(text_lower.split())
        query_words = set(query_lower.split())
        
        # Remove common stop words for better matching
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'for', 'with', 'to', 'of', 'in', 'on', 'at'}
        text_words -= stop_words
        query_words -= stop_words
        
        if not query_words:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = text_words & query_words
        union = text_words | query_words
        
        if not union:
            return 0.0
        
        jaccard_score = len(intersection) / len(union)
        
        # Boost score for longer matching terms
        long_term_bonus = 0
        for term in query_words:
            if len(term) > 4 and term in text_lower:
                long_term_bonus += 0.1
        
        return min(1.0, jaccard_score + long_term_bonus)
    
    def _find_specific_products(self, query: str) -> List[Dict[str, Any]]:
        """Find specific product pages with ratings and prices using direct Amazon scraping."""
        try:
            # Try direct Amazon search first with exact terms
            amazon_products = self._scrape_amazon_products(query)
            if amazon_products:
                return amazon_products
            
            # Fallback to Google search if Amazon scraping fails
            search_query = f'"{query}" site:amazon.com OR site:bestbuy.com OR site:target.com'
            results = self._search_google_scrape(search_query)
            
            specific_products = []
            for result in results[:5]:  # Check top 5 results
                if any(site in result['url'].lower() for site in ['amazon.com', 'bestbuy.com', 'target.com']):
                    # Extract product info if available
                    product_info = {
                        'title': result['title'],
                        'url': result['url'],
                        'snippet': result.get('snippet', ''),
                        'rating': self._extract_rating(result.get('snippet', '')),
                        'price': self._extract_price(result.get('snippet', ''))
                    }
                    specific_products.append(product_info)
            
            return specific_products
            
        except Exception as e:
            logger.error(f"Error finding specific products: {e}")
            return []
    
    def _extract_rating(self, text: str) -> str:
        """Extract rating from text snippet."""
        import re
        # Look for patterns like "4.5 stars", "4.5/5", "4.5 out of 5"
        rating_patterns = [
            r'(\d+\.\d+)\s*(?:stars?|out of 5|/5)',
            r'(\d+\.\d+)\s*★',
            r'★\s*(\d+\.\d+)',
            r'Rating:\s*(\d+\.\d+)'
        ]
        
        for pattern in rating_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return 'N/A'
    
    def _extract_price(self, text: str) -> str:
        """Extract price from text snippet."""
        import re
        # Look for price patterns
        price_patterns = [
            r'\$([\d,]+\.\d{2})',
            r'\$([\d,]+)',
            r'Price:\s*\$([\d,]+(?:\.\d{2})?)',
            r'([\d,]+\.\d{2})\s*USD'
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, text)
            if match:
                return f"${match.group(1)}"
        return 'N/A'
    
    def _scrape_amazon_products(self, query: str) -> List[Dict[str, Any]]:
        """Directly scrape Amazon for specific products with ratings and prices."""
        try:
            import requests
            from bs4 import BeautifulSoup
            import time
            
            # Amazon search URL with rating sort - use exact query
            search_url = f"https://www.amazon.com/s?k={urllib.parse.quote_plus(query)}&s=review-rank&ref=sr_st_review-rank"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            logger.info(f"Scraping Amazon for exact terms: {query}")
            response = requests.get(search_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                products = []
                
                # Find product containers
                product_containers = soup.find_all('div', {'data-component-type': 's-search-result'})
                
                for container in product_containers[:10]:  # Get top 10 products for better relevance checking
                    try:
                         # Extract title - try multiple selectors
                         title = 'Unknown Product'
                         title_selectors = [
                             'h2 a span',
                             'h2 span',
                             '.a-size-base-plus',
                             '.a-size-medium',
                             '.a-size-mini',
                             'h2',
                             '.s-size-mini'
                         ]
                         
                         for selector in title_selectors:
                             title_elem = container.select_one(selector)
                             if title_elem:
                                 title_text = title_elem.get_text(strip=True)
                                 if title_text and len(title_text) > 5:  # Ensure meaningful title
                                     title = title_text
                                     break
                         
                         # Extract URL
                         link_elem = container.find('a', class_='a-link-normal')
                         if link_elem and link_elem.get('href'):
                             product_url = 'https://www.amazon.com' + link_elem['href']
                         else:
                             continue
                         
                         # Extract rating
                         rating_elem = container.find('span', class_='a-icon-alt')
                         rating = 'N/A'
                         if rating_elem:
                             rating_text = rating_elem.get_text(strip=True)
                             rating_match = re.search(r'(\d+\.\d+)', rating_text)
                             if rating_match:
                                 rating = rating_match.group(1)
                         
                         # Extract price
                         price_elem = container.find('span', class_='a-price-whole')
                         if not price_elem:
                             price_elem = container.find('span', class_='a-offscreen')
                         price = 'N/A'
                         if price_elem:
                             price_text = price_elem.get_text(strip=True)
                             price_match = re.search(r'\$?([\d,]+(?:\.\d{2})?)', price_text)
                             if price_match:
                                 price = f"${price_match.group(1)}"
                         
                         products.append({
                             'title': title,
                             'url': product_url,
                             'rating': rating,
                             'price': price,
                             'snippet': f"Rating: {rating}, Price: {price}"
                         })
                        
                    except Exception as e:
                        logger.warning(f"Error parsing product container: {e}")
                        continue
                
                if products:
                    logger.info(f"Found {len(products)} products on Amazon for: {query}")
                    return products
                else:
                    logger.warning("No products found in Amazon search results")
                    
            else:
                logger.warning(f"Amazon request failed with status: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error scraping Amazon products: {e}")
            
        return []
    
    def _handle_learning_search(self, query: str) -> Dict[str, Any]:
        """Handle tutorial and documentation searches with YouTube and official docs targeting."""
        try:
            query_lower = query.lower()
            
            # For tutorials, prioritize YouTube
            if 'tutorial' in query_lower or 'how to' in query_lower or 'guide' in query_lower:
                # Extract the main topic
                topic = query_lower.replace('tutorial', '').replace('how to', '').replace('guide', '').replace('for', '').strip()
                
                # Search YouTube directly
                youtube_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(topic + ' tutorial')}"
                
                try:
                    # Try to get the first video result
                    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
                    response = requests.get(youtube_url, headers=headers, timeout=10)
                    
                    if response.status_code == 200:
                        # Look for video links in the response
                        import re
                        video_pattern = r'"videoId":"([^"]+)"'
                        matches = re.findall(video_pattern, response.text)
                        
                        if matches:
                            first_video_url = f"https://www.youtube.com/watch?v={matches[0]}"
                            webbrowser.open(first_video_url)
                            return {
                                'success': True,
                                'query': query,
                                'query_type': 'tutorial',
                                'opened_url': first_video_url,
                                'title': f"YouTube Tutorial: {topic}",
                                'message': f"Opened specific YouTube tutorial for: {topic}"
                            }
                except Exception as e:
                    logger.warning(f"Could not parse YouTube results: {e}")
                
                # Fallback to YouTube search
                webbrowser.open(youtube_url)
                return {
                    'success': True,
                    'query': query,
                    'query_type': 'tutorial',
                    'opened_url': youtube_url,
                    'title': f"YouTube Search: {topic} tutorial",
                    'message': f"Opened YouTube search for: {topic} tutorial"
                }
            
            # For documentation, try to find official docs
            elif 'docs' in query_lower or 'documentation' in query_lower:
                topic = query_lower.replace('documentation', '').replace('docs', '').replace('for', '').strip()
                
                # Common documentation patterns
                doc_urls = [
                    f"https://{topic}.readthedocs.io",
                    f"https://docs.{topic}.org",
                    f"https://{topic}.org/docs",
                    f"https://developer.{topic}.com"
                ]
                
                # Try each potential documentation URL
                for doc_url in doc_urls:
                    try:
                        response = requests.head(doc_url, timeout=5)
                        if response.status_code == 200:
                            webbrowser.open(doc_url)
                            return {
                                'success': True,
                                'query': query,
                                'query_type': 'documentation',
                                'opened_url': doc_url,
                                'title': f"Official Documentation: {topic}",
                                'message': f"Opened official documentation for: {topic}"
                            }
                    except:
                        continue
                
                # Fallback to Google search for official docs
                google_docs_url = f"https://www.google.com/search?q={urllib.parse.quote_plus(topic + ' official documentation')}"
                webbrowser.open(google_docs_url)
                return {
                    'success': True,
                    'query': query,
                    'query_type': 'documentation',
                    'opened_url': google_docs_url,
                    'title': f"Search: {topic} official documentation",
                    'message': f"Searching for official documentation: {topic}"
                }
            
        except Exception as e:
            logger.error(f"Error in learning search: {e}")
            return {'success': False, 'error': str(e)}
    
    def _handle_github_search(self, query: str) -> Dict[str, Any]:
        """Handle GitHub repository searches with direct repository targeting."""
        try:
            # Extract repository name from query
            match = re.search(self.search_patterns['github_repo'], query.lower())
            if match:
                repo_query = match.group(1).strip()
            else:
                repo_query = query.replace('github', '').replace('repo', '').replace('repository', '').strip()
            
            # Search GitHub API for exact matches first
            api_url = f"https://api.github.com/search/repositories?q={urllib.parse.quote(repo_query)}&sort=stars&order=desc&per_page=1"
            
            try:
                response = self.session.get(api_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('items'):
                        repo = data['items'][0]
                        repo_url = repo.get('html_url')
                        
                        webbrowser.open(repo_url)
                        return {
                            'success': True,
                            'query': query,
                            'query_type': 'github_repo',
                            'opened_url': repo_url,
                            'title': repo.get('full_name'),
                            'description': repo.get('description', ''),
                            'message': f"Opened top GitHub repository: {repo.get('full_name')}"
                        }
            except Exception as e:
                logger.warning(f"GitHub API search failed: {e}")
            
            # Fallback to GitHub search page
            github_search_url = f"https://github.com/search?q={urllib.parse.quote_plus(repo_query)}&type=repositories"
            webbrowser.open(github_search_url)
            return {
                'success': True,
                'query': query,
                'query_type': 'github_repo',
                'opened_url': github_search_url,
                'title': f"GitHub Search: {repo_query}",
                'message': f"Opened GitHub search for: {repo_query}"
            }
            
        except Exception as e:
            logger.error(f"Error in GitHub search: {e}")
            return {'success': False, 'error': str(e)}
    
    def _handle_general_search(self, query: str, query_type: str) -> Dict[str, Any]:
        """Handle general searches with enhanced targeting."""
        try:
            # Get search results based on query type
            search_results = self._get_search_results(query, query_type)
            
            if not search_results:
                return {
                    'success': False,
                    'error': 'No search results found',
                    'query': query
                }
            
            # Select and open the best result
            best_result = self._select_best_result(search_results, query_type)
            
            if best_result:
                # Open the URL
                webbrowser.open(best_result['url'])
                
                return {
                    'success': True,
                    'query': query,
                    'query_type': query_type,
                    'opened_url': best_result['url'],
                    'title': best_result.get('title', 'Unknown'),
                    'description': best_result.get('description', ''),
                    'total_results': len(search_results),
                    'message': f"Successfully opened: {best_result.get('title', best_result['url'])}"
                }
            else:
                return {
                    'success': False,
                    'error': 'No suitable result found to open',
                    'query': query,
                    'total_results': len(search_results)
                }
                
        except Exception as e:
            logger.error(f"Error in general search: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'query': query
            }
    
    def _simplify_query(self, query: str) -> str:
        """Simplify query by removing common words and focusing on key terms."""
        # Remove common words that might limit search results
        stop_words = ['find', 'me', 'the', 'best', 'top', 'good', 'for', 'of', 'about', 'how', 'to']
        words = query.lower().split()
        
        # Keep important words
        important_words = []
        for word in words:
            if word not in stop_words or len(important_words) < 2:
                important_words.append(word)
        
        return ' '.join(important_words) if important_words else query
    
    def _search_github(self, query: str) -> List[Dict[str, Any]]:
        """Search GitHub repositories."""
        try:
            # Extract repository name from query
            match = re.search(self.search_patterns['github_repo'], query.lower())
            if match:
                repo_query = match.group(1).strip()
            else:
                repo_query = query
            
            # Clean up the query
            repo_query = re.sub(r'\b(?:the|for|of|a|an|in|on|by|about)\b', '', repo_query, flags=re.IGNORECASE).strip()
            
            # Search GitHub API
            api_url = f"https://api.github.com/search/repositories?q={urllib.parse.quote(repo_query)}&sort=stars&order=desc&per_page=5"
            response = self.session.get(api_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for repo in data.get('items', []):
                    results.append({
                        'url': repo.get('html_url'),
                        'title': repo.get('full_name'),
                        'description': repo.get('description', ''),
                        'score': repo.get('stargazers_count', 0),
                        'source': 'github',
                        'type': 'repository'
                    })
                
                return results
            
        except Exception as e:
            logger.error(f"Error searching GitHub: {str(e)}")
        
        return []
    
    def _search_npm(self, query: str) -> List[Dict[str, Any]]:
        """Search NPM packages."""
        try:
            # Extract package name from query
            match = re.search(self.search_patterns['npm_package'], query.lower())
            if match:
                package_query = match.group(1).strip()
            else:
                package_query = query
            
            # Search NPM registry
            api_url = f"https://registry.npmjs.org/-/v1/search?text={urllib.parse.quote(package_query)}&size=5"
            response = self.session.get(api_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for package in data.get('objects', []):
                    pkg_info = package.get('package', {})
                    results.append({
                        'url': f"https://www.npmjs.com/package/{pkg_info.get('name')}",
                        'title': pkg_info.get('name'),
                        'description': pkg_info.get('description', ''),
                        'score': package.get('score', {}).get('final', 0),
                        'source': 'npm',
                        'type': 'package'
                    })
                
                return results
            
        except Exception as e:
            logger.error(f"Error searching NPM: {str(e)}")
        
        return []
    
    def _search_pypi(self, query: str) -> List[Dict[str, Any]]:
        """Search PyPI packages."""
        try:
            # Extract package name from query
            match = re.search(self.search_patterns['pypi_package'], query.lower())
            if match:
                package_query = match.group(1).strip()
            else:
                package_query = query
            
            # Search PyPI
            api_url = f"https://pypi.org/search/?q={urllib.parse.quote(package_query)}"
            response = self.session.get(api_url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                results = []
                
                # Parse search results
                for result in soup.find_all('a', class_='package-snippet')[:5]:
                    package_name = result.find('span', class_='package-snippet__name')
                    package_desc = result.find('p', class_='package-snippet__description')
                    
                    if package_name:
                        results.append({
                            'url': f"https://pypi.org/project/{package_name.text.strip()}/",
                            'title': package_name.text.strip(),
                            'description': package_desc.text.strip() if package_desc else '',
                            'score': 1.0,
                            'source': 'pypi',
                            'type': 'package'
                        })
                
                return results
            
        except Exception as e:
            logger.error(f"Error searching PyPI: {str(e)}")
        
        return []

    def _search_google_scrape(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search Google using web scraping with proper headers and parsing."""
        results = []
        
        try:
            # Construct Google search URL
            search_url = f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}&num={max_results}"
            
            # Headers to mimic a real browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            response = requests.get(search_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find search result containers
            search_containers = soup.find_all('div', class_='g')
            
            for container in search_containers[:max_results]:
                try:
                    # Extract title and URL
                    title_elem = container.find('h3')
                    if not title_elem:
                        continue
                        
                    title = title_elem.get_text(strip=True)
                    
                    # Find the link
                    link_elem = container.find('a')
                    if not link_elem or not link_elem.get('href'):
                        continue
                        
                    url = link_elem['href']
                    
                    # Clean up the URL (Google sometimes wraps URLs)
                    if url.startswith('/url?q='):
                        url = urllib.parse.unquote(url.split('/url?q=')[1].split('&')[0])
                    
                    # Extract snippet/description
                    snippet_elem = container.find('span', class_=['aCOpRe', 'st'])
                    if not snippet_elem:
                        snippet_elem = container.find('div', class_=['VwiC3b', 's3v9rd'])
                    
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''
                    
                    # Skip if we don't have essential information
                    if not title or not url or url.startswith('#'):
                        continue
                    
                    # Calculate relevance score based on position and content
                    position_score = max(0, 10 - len(results))  # Higher score for earlier results
                    content_score = len(title) / 100 + len(snippet) / 500  # Bonus for detailed content
                    
                    result = {
                        'title': title,
                        'url': url,
                        'snippet': snippet,
                        'source': 'google',
                        'score': position_score + content_score
                    }
                    
                    results.append(result)
                    
                except Exception as e:
                    logger.warning(f"Error parsing Google search result: {e}")
                    continue
            
            logger.info(f"Google search returned {len(results)} results for query: {query}")
            
        except Exception as e:
            logger.error(f"Error searching Google: {e}")
        
        return results

    def _search_duckduckgo(self, query: str) -> List[Dict[str, Any]]:
        """Search using alternative methods since DuckDuckGo blocks scraping."""
        results = []
        
        # Try instant answers API first
        try:
            api_url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1&skip_disambig=1"
            response = self.session.get(api_url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                # Add abstract URL if available
                if data.get('AbstractURL'):
                    results.append({
                        'url': data['AbstractURL'],
                        'title': data.get('AbstractSource', 'DuckDuckGo Result'),
                        'description': data.get('Abstract', ''),
                        'score': 0.9,
                        'source': 'duckduckgo',
                        'type': 'instant_answer'
                    })
                
                # Add related topics
                for topic in data.get('RelatedTopics', [])[:3]:
                    if isinstance(topic, dict) and topic.get('FirstURL'):
                        results.append({
                            'url': topic['FirstURL'],
                            'title': topic.get('Text', '').split(' - ')[0],
                            'description': topic.get('Text', ''),
                            'score': 0.7,
                            'source': 'duckduckgo',
                            'type': 'related_topic'
                        })
            
        except Exception as e:
            logger.error(f"Error with DuckDuckGo API: {str(e)}")
        
        # If no results from API, generate smart URLs based on query type
        if not results:
            results.extend(self._generate_smart_urls(query))
        
        return results
    
    def _generate_smart_urls(self, query: str) -> List[Dict[str, Any]]:
        """Generate smart URLs based on query patterns when search APIs fail."""
        results = []
        query_lower = query.lower()
        
        # Product searches - direct to popular sites
        if any(word in query_lower for word in ['best', 'top', 'case', 'cover', 'buy', 'product']):
            # Extract main product terms
            product_terms = query_lower.replace('best', '').replace('top', '').replace('find me', '').replace('good', '').strip()
            
            results.extend([
                {
                    'url': f"https://www.amazon.com/s?k={urllib.parse.quote(product_terms)}",
                    'title': f"Amazon: {product_terms}",
                    'description': f"Shop for {product_terms} on Amazon",
                    'score': 0.9,
                    'source': 'smart_url',
                    'type': 'shopping'
                },
                {
                    'url': f"https://www.reddit.com/search/?q={urllib.parse.quote(query)}",
                    'title': f"Reddit discussions: {query}",
                    'description': f"Community discussions about {query}",
                    'score': 0.8,
                    'source': 'smart_url',
                    'type': 'community'
                }
            ])
        
        # Documentation searches
        if any(word in query_lower for word in ['docs', 'documentation', 'tutorial', 'guide', 'how to']):
            # Extract technology/tool name
            tech_terms = query_lower.replace('documentation', '').replace('docs', '').replace('tutorial', '').replace('guide', '').replace('how to', '').replace('for', '').strip()
            
            results.extend([
                {
                    'url': f"https://www.google.com/search?q={urllib.parse.quote(query + ' official documentation')}",
                    'title': f"Search: {query} official documentation",
                    'description': f"Find official documentation for {tech_terms}",
                    'score': 0.9,
                    'source': 'smart_url',
                    'type': 'documentation'
                },
                {
                    'url': f"https://stackoverflow.com/search?q={urllib.parse.quote(tech_terms)}",
                    'title': f"Stack Overflow: {tech_terms}",
                    'description': f"Programming questions and answers about {tech_terms}",
                    'score': 0.8,
                    'source': 'smart_url',
                    'type': 'qa'
                }
            ])
        
        # Download searches
        if 'download' in query_lower:
            software_name = query_lower.replace('download', '').strip()
            results.extend([
                {
                    'url': f"https://www.google.com/search?q={urllib.parse.quote(software_name + ' official download')}",
                    'title': f"Download {software_name}",
                    'description': f"Official download page for {software_name}",
                    'score': 0.9,
                    'source': 'smart_url',
                    'type': 'download'
                }
            ])
        
        # Latest/newest searches
        if any(word in query_lower for word in ['latest', 'newest', 'recent']):
            tech_terms = query_lower.replace('latest', '').replace('newest', '').replace('recent', '').replace('model', '').replace('version', '').strip()
            results.extend([
                {
                    'url': f"https://www.google.com/search?q={urllib.parse.quote(tech_terms + ' latest release 2024')}",
                    'title': f"Latest {tech_terms}",
                    'description': f"Find the latest version of {tech_terms}",
                    'score': 0.9,
                    'source': 'smart_url',
                    'type': 'latest'
                }
            ])
        
        # General fallback
        if not results:
            results.append({
                'url': f"https://www.google.com/search?q={urllib.parse.quote(query)}",
                'title': f"Search: {query}",
                'description': f"General web search for {query}",
                'score': 0.7,
                'source': 'smart_url',
                'type': 'general'
            })
        
        return results
    
    def _search_web_general(self, query: str) -> List[Dict[str, Any]]:
        """Perform general web search using multiple engines with robust fallbacks."""
        results = []
        
        # First try DuckDuckGo (more reliable)
        ddg_results = self._search_duckduckgo(query)
        results.extend(ddg_results)
        
        # Add Google search results for better coverage
        google_results = self._search_google_scrape(query)
        results.extend(google_results)
        
        # Add some common site-specific searches for better results
        enhanced_queries = self._generate_enhanced_queries(query)
        
        for enhanced_query in enhanced_queries:
            try:
                # Try DuckDuckGo with enhanced query
                enhanced_results = self._search_duckduckgo(enhanced_query)
                for result in enhanced_results[:2]:  # Take top 2 from each enhanced query
                    if result not in results:  # Avoid duplicates
                        result['score'] *= 0.9  # Slightly lower score for enhanced queries
                        results.append(result)
                
                if len(results) >= 12:  # Limit total results
                    break
                    
            except Exception as e:
                logger.error(f"Error with enhanced query '{enhanced_query}': {str(e)}")
                continue
        
        return results
    
    def _generate_enhanced_queries(self, query: str) -> List[str]:
        """Generate enhanced search queries for better results."""
        enhanced_queries = []
        
        # Product searches - add shopping sites
        if any(word in query.lower() for word in ['best', 'top', 'find', 'good', 'case', 'cover', 'buy']):
            enhanced_queries.extend([
                f"{query} site:amazon.com",
                f"{query} site:reddit.com",
                f"{query} reviews 2024",
                f"{query} comparison guide"
            ])
        
        # GitHub/code searches
        if any(word in query.lower() for word in ['github', 'repo', 'repository', 'code']):
            enhanced_queries.extend([
                f"{query} site:github.com",
                f"{query.replace('github repo', '').replace('repository', '').strip()} github"
            ])
        
        # Documentation searches
        if any(word in query.lower() for word in ['docs', 'documentation', 'tutorial', 'guide']):
            enhanced_queries.extend([
                f"{query} site:docs.python.org",
                f"{query} site:developer.mozilla.org",
                f"{query} official documentation"
            ])
        
        # Download searches
        if 'download' in query.lower():
            enhanced_queries.extend([
                f"{query} official site",
                f"{query.replace('download', '').strip()} download page"
            ])
        
        # Latest/newest searches
        if any(word in query.lower() for word in ['latest', 'newest', 'recent']):
            enhanced_queries.extend([
                f"{query} 2024",
                f"{query} release notes",
                f"{query} changelog"
            ])
        
        return enhanced_queries[:4]  # Limit to 4 enhanced queries
    
    def _select_best_result(self, results: List[Dict[str, Any]], query_type: str) -> Optional[Dict[str, Any]]:
        """Select the best result based on query type and intelligent scoring."""
        if not results:
            return None
        
        # Score results based on query type
        scored_results = []
        
        for result in results:
            score = result.get('score', 0)
            url = result.get('url', '').lower()
            title = result.get('title', '').lower()
            
            # Boost scores based on source relevance and quality
            if query_type == 'github_repo':
                if result.get('source') == 'github' or 'github.com' in url:
                    score *= 2.5
                elif any(word in title for word in ['repository', 'repo', 'github']):
                    score *= 1.8
                    
            elif query_type == 'npm_package':
                if result.get('source') == 'npm' or 'npmjs.com' in url:
                    score *= 2.5
                elif 'npm' in url or 'npm' in title:
                    score *= 1.8
                    
            elif query_type == 'pypi_package':
                if result.get('source') == 'pypi' or 'pypi.org' in url:
                    score *= 2.5
                elif 'python' in url or 'pip' in title:
                    score *= 1.8
                    
            elif query_type == 'product_search':
                # Prioritize shopping sites for product searches
                if 'amazon.com' in url:
                    score *= 2.0
                elif any(domain in url for domain in ['ebay.com', 'etsy.com', 'walmart.com', 'target.com']):
                    score *= 1.7
                elif 'reddit.com' in url and any(word in title for word in ['review', 'recommendation', 'best']):
                    score *= 1.6
                elif any(word in url for word in ['review', 'comparison', 'vs']):
                    score *= 1.4
                    
            elif query_type == 'documentation':
                # Prioritize official documentation sites
                if any(domain in url for domain in ['docs.', 'documentation', 'api.', 'developer.']):
                    score *= 2.0
                elif any(domain in url for domain in ['.org', 'official']):
                    score *= 1.5
                    
            elif query_type == 'tutorial':
                # Prioritize educational and tutorial sites
                if any(domain in url for domain in ['tutorial', 'guide', 'learn', 'course']):
                    score *= 1.8
                elif any(domain in url for domain in ['youtube.com', 'medium.com', 'dev.to']):
                    score *= 1.5
                    
            elif query_type == 'download':
                # Prioritize official download pages
                if any(word in url for word in ['download', 'releases', 'install']):
                    score *= 2.0
                elif any(domain in url for domain in ['.org', '.com', 'github.com']):
                    score *= 1.5
                    
            elif query_type == 'general':
                # For general searches, prioritize authoritative and popular sites
                if any(domain in url for domain in ['wikipedia.org', '.edu', '.gov']):
                    score *= 1.8
                elif any(domain in url for domain in ['stackoverflow.com', 'reddit.com']):
                    score *= 1.4
                elif result.get('source') == 'google':
                    score *= 1.2  # Slight boost for Google results
            
            # General quality indicators
            if any(domain in url for domain in ['github.com', 'npmjs.com', 'pypi.org', 'python.org', 'mozilla.org']):
                score *= 1.3
            
            # Penalize certain low-quality indicators
            if any(word in url for word in ['ads', 'spam', 'click', 'popup']):
                score *= 0.5
            
            # Boost results with good titles
            if len(title) > 10 and not any(word in title for word in ['untitled', 'page not found', 'error']):
                score *= 1.1
            
            scored_results.append((score, result))
        
        # Sort by score and return the best result
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        # Log the top results for debugging
        logger.info(f"Top 3 results for query type '{query_type}':")
        for i, (score, result) in enumerate(scored_results[:3]):
            logger.info(f"  {i+1}. {result.get('title', 'No title')} - {result.get('url', 'No URL')} (score: {score:.2f})")
        
        return scored_results[0][1] if scored_results else None
    
    def get_capability_info(self) -> Dict[str, Any]:
        """Get information about this capability."""
        return {
            'name': 'Enhanced Web Search Automation',
            'description': 'Intelligent web search with automatic link opening for diverse queries',
            'version': '1.0.0',
            'supported_query_types': list(self.search_patterns.keys()) + ['general'],
            'search_engines': list(self.search_engines.keys()),
            'specialized_sources': ['GitHub', 'NPM', 'PyPI', 'DuckDuckGo'],
            'features': [
                'Intelligent query analysis',
                'Multi-source search aggregation',
                'Automatic best result selection',
                'Specialized repository/package search',
                'Product and shopping search optimization',
                'Documentation and tutorial discovery'
            ]
        }

# Command-line interface
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python enhanced_web_search_automation.py <query>")
        sys.exit(1)
    
    query = " ".join(sys.argv[1:])
    search_automation = EnhancedWebSearchAutomation()
    
    try:
        result = search_automation.search_and_open(query)
        
        if result['success']:
            # Output format expected by the IPC handler
            print(f"SUCCESS:{result['success']}:{result.get('message', 'Search completed')}:{result.get('opened_url', '')}:{result.get('query_type', 'general')}")
        else:
            print(f"ERROR:{result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"ERROR:{str(e)}")
        sys.exit(1)