import requests
import webbrowser
import logging
import os
import time
import urllib.parse
import re
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)

class WebController:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.download_dir = Path.home() / 'Downloads'
    
    def search_github_repo(self, query: str) -> Tuple[bool, str, str]:
        """Search for a GitHub repository and return the URL if found.
        
        Args:
            query: The search query for a GitHub repository
            
        Returns:
            Tuple of (success, url, message)
        """
        try:
            # Check if query is specifically about a GitHub repo
            github_repo_pattern = r'(?:github|gh)\s+repo(?:sitory)?\s+(?:for|of|about)?\s+(.+)'
            match = re.search(github_repo_pattern, query, re.IGNORECASE)
            
            if match:
                repo_query = match.group(1).strip()
            else:
                repo_query = query
            
            # Extract potential organization/owner name
            org_pattern = r'(?:from|by|of|apple\'?s?)\s+([\w.-]+)'
            org_match = re.search(org_pattern, repo_query, re.IGNORECASE)
            org_name = org_match.group(1) if org_match else None
            
            # Check for Apple specifically
            if 'apple' in repo_query_lower:
                org_name = 'apple'
            
            # Improve search query with organization if available
            if org_name:
                # Try to make the search more specific by including the organization
                search_query = f"user:{org_name} {repo_query}"
            else:
                # Try to extract key terms for better search results
                # Remove common words like "the", "for", etc.
                key_terms = re.sub(r'\b(?:the|for|of|a|an|in|on|by|about)\b', '', repo_query, flags=re.IGNORECASE)
                search_query = key_terms.strip()
            
            # Search for the repository using GitHub's API
            search_url = f"https://api.github.com/search/repositories?q={urllib.parse.quote(search_query)}&sort=stars&order=desc"
            response = self.session.get(search_url, timeout=10)
            
            if response.status_code != 200:
                # If the specific search failed, try a more general search
                search_url = f"https://api.github.com/search/repositories?q={urllib.parse.quote(repo_query)}"
                response = self.session.get(search_url, timeout=10)
                
                if response.status_code != 200:
                    return False, "", f"GitHub API error: {response.status_code}"
            
            data = response.json()
            
            if data.get('total_count', 0) == 0 or not data.get('items'):
                return False, "", f"No GitHub repositories found for '{repo_query}'"
            
            # Get the top result
            top_repo = data['items'][0]
            repo_url = top_repo.get('html_url')
            repo_name = top_repo.get('full_name')
            repo_description = top_repo.get('description', 'No description available')
            
            if not repo_url:
                return False, "", "Repository URL not found in API response"
            
            return True, repo_url, f"Found GitHub repository: {repo_name}\n{repo_description}"
            
        except Exception as e:
            logger.error(f"Error searching GitHub repository: {str(e)}")
            return False, "", f"Error searching GitHub repository: {str(e)}"
    
    def search_web(self, query: str) -> str:
        """Perform a web search and return results."""
        try:
            # Check for Python version page requests
            python_version_pattern = r'python\s+(?:version|release)\s*(\d+(?:\.\d+)*)'  
            python_match = re.search(python_version_pattern, query, re.IGNORECASE)
            
            if python_match:
                version = python_match.group(1)
                # Direct URL to Python version documentation
                python_url = f"https://docs.python.org/{version.split('.')[0]}/whatsnew/{version}.html"
                return self.browse_url(python_url)
            
            # Check if this is a GitHub repository search
            if re.search(r'(?:github|gh)\s+repo(?:sitory)?|repo(?:sitory)?\s+(?:for|of|about|on)\s+(?:github|gh)', query, re.IGNORECASE):
                # Try to find and open the GitHub repository directly
                success, repo_url, message = self.search_github_repo(query)
                
                if success and repo_url:
                    # Open the repository URL directly
                    webbrowser.open(repo_url)
                    # Return a more detailed message with the exact URL
                    return f"Found: {message}\nURL: {repo_url}\n\nOpened in browser."
            
            # Check if this looks like a natural language request for a specific website
            # If so, try to use the site mapping first
            site_mapping = {
                'openai': 'https://openai.com',
                'github': 'https://github.com',
                'python': 'https://python.org',
                'python docs': 'https://docs.python.org',
                'apple': 'https://apple.com',
                'apple developer': 'https://developer.apple.com',
                'microsoft': 'https://microsoft.com',
                'google': 'https://google.com',
                'stack overflow': 'https://stackoverflow.com',
                'reddit': 'https://reddit.com',
                'twitter': 'https://twitter.com',
                'linkedin': 'https://linkedin.com',
                'facebook': 'https://facebook.com',
                'instagram': 'https://instagram.com',
                'youtube': 'https://youtube.com',
                'netflix': 'https://netflix.com',
                'amazon': 'https://amazon.com',
                'spotify': 'https://spotify.com',
                'discord': 'https://discord.com',
                'slack': 'https://slack.com',
                'zoom': 'https://zoom.us',
                'notion': 'https://notion.so',
                'figma': 'https://figma.com',
                'trello': 'https://trello.com',
                'asana': 'https://asana.com',
                'dropbox': 'https://dropbox.com',
                'google drive': 'https://drive.google.com',
                'gmail': 'https://gmail.com',
                'outlook': 'https://outlook.com',
                'yahoo': 'https://yahoo.com',
                'bing': 'https://bing.com',
                'duckduckgo': 'https://duckduckgo.com',
                'wikipedia': 'https://wikipedia.org',
                'medium': 'https://medium.com',
                'dev.to': 'https://dev.to',
                'hashnode': 'https://hashnode.dev',
                'producthunt': 'https://producthunt.com',
                'hackernews': 'https://news.ycombinator.com',
                'techcrunch': 'https://techcrunch.com',
                'the verge': 'https://theverge.com',
                'ars technica': 'https://arstechnica.com',
                'wired': 'https://wired.com',
                'mit technology review': 'https://technologyreview.com',
                'nvidia': 'https://nvidia.com',
                'amd': 'https://amd.com',
                'intel': 'https://intel.com',
                'linux': 'https://linux.org',
                'ubuntu': 'https://ubuntu.com',
                'debian': 'https://debian.org',
                'fedora': 'https://fedora.org',
                'arch linux': 'https://archlinux.org',
                'docker': 'https://docker.com',
                'kubernetes': 'https://kubernetes.io',
                'terraform': 'https://terraform.io',
                'ansible': 'https://ansible.com',
                'jenkins': 'https://jenkins.io',
                'gitlab': 'https://gitlab.com',
                'bitbucket': 'https://bitbucket.org',
                'jira': 'https://atlassian.com/software/jira',
                'confluence': 'https://atlassian.com/software/confluence',
                'vscode': 'https://code.visualstudio.com',
                'sublime text': 'https://sublimetext.com',
                'atom': 'https://atom.io',
                'vim': 'https://vim.org',
                'emacs': 'https://gnu.org/software/emacs',
                'postman': 'https://postman.com',
                'insomnia': 'https://insomnia.rest',
                'swagger': 'https://swagger.io',
                'openapi': 'https://openapis.org',
                'graphql': 'https://graphql.org',
                'react': 'https://reactjs.org',
                'vue': 'https://vuejs.org',
                'angular': 'https://angular.io',
                'node.js': 'https://nodejs.org',
                'npm': 'https://npmjs.com',
                'yarn': 'https://yarnpkg.com',
                'webpack': 'https://webpack.js.org',
                'babel': 'https://babeljs.io',
                'eslint': 'https://eslint.org',
                'prettier': 'https://prettier.io',
                'typescript': 'https://typescriptlang.org',
                'sass': 'https://sass-lang.com',
                'less': 'https://lesscss.org',
                'bootstrap': 'https://getbootstrap.com',
                'tailwind': 'https://tailwindcss.com',
                'material ui': 'https://mui.com',
                'ant design': 'https://ant.design',
                'django': 'https://djangoproject.com',
                'flask': 'https://flask.palletsprojects.com',
                'fastapi': 'https://fastapi.tiangolo.com',
                'express': 'https://expressjs.com',
                'koa': 'https://koajs.com',
                'spring': 'https://spring.io',
                'laravel': 'https://laravel.com',
                'rails': 'https://rubyonrails.org',
                'asp.net': 'https://dotnet.microsoft.com',
                'php': 'https://php.net',
                'java': 'https://java.com',
                'kotlin': 'https://kotlinlang.org',
                'swift': 'https://swift.org',
                'rust': 'https://rust-lang.org',
                'go': 'https://golang.org',
                'c++': 'https://isocpp.org',
                'c#': 'https://docs.microsoft.com/en-us/dotnet/csharp',
                'scala': 'https://scala-lang.org',
                'clojure': 'https://clojure.org',
                'haskell': 'https://haskell.org',
                'erlang': 'https://erlang.org',
                'elixir': 'https://elixir-lang.org',
                'f#': 'https://fsharp.org',
                'ocaml': 'https://ocaml.org',
                'nim': 'https://nim-lang.org',
                'zig': 'https://ziglang.org',
                'crystal': 'https://crystal-lang.org',
                'julia': 'https://julialang.org',
                'r': 'https://r-project.org',
                'matlab': 'https://mathworks.com/products/matlab.html',
                'octave': 'https://octave.org',
                'scipy': 'https://scipy.org',
                'numpy': 'https://numpy.org',
                'pandas': 'https://pandas.pydata.org',
                'matplotlib': 'https://matplotlib.org',
                'seaborn': 'https://seaborn.pydata.org',
                'plotly': 'https://plotly.com',
                'bokeh': 'https://bokeh.org',
                'tensorflow': 'https://tensorflow.org',
                'pytorch': 'https://pytorch.org',
                'keras': 'https://keras.io',
                'scikit-learn': 'https://scikit-learn.org',
                'xgboost': 'https://xgboost.readthedocs.io',
                'lightgbm': 'https://lightgbm.readthedocs.io',
                'catboost': 'https://catboost.ai',
                'hugging face': 'https://huggingface.co',
                'openai api': 'https://platform.openai.com',
                'anthropic': 'https://anthropic.com',
                'cohere': 'https://cohere.ai',
                'ai21': 'https://ai21.com',
                'replicate': 'https://replicate.com',
                'gradio': 'https://gradio.app',
                'streamlit': 'https://streamlit.io',
                'dash': 'https://plotly.com/dash',
                'voila': 'https://voila.readthedocs.io',
                'jupyter': 'https://jupyter.org',
                'colab': 'https://colab.research.google.com',
                'kaggle': 'https://kaggle.com',
                'datacamp': 'https://datacamp.com',
                'coursera': 'https://coursera.org',
                'edx': 'https://edx.org',
                'udemy': 'https://udemy.com',
                'udacity': 'https://udacity.com',
                'freecodecamp': 'https://freecodecamp.org',
                'the odin project': 'https://theodinproject.com',
                'mdn': 'https://developer.mozilla.org',
                'w3schools': 'https://w3schools.com',
                'css-tricks': 'https://css-tricks.com',
                'smashing magazine': 'https://smashingmagazine.com',
                'a list apart': 'https://alistapart.com',
                'codrops': 'https://tympanus.net/codrops',
                'dribbble': 'https://dribbble.com',
                'behance': 'https://behance.net',
                'pinterest': 'https://pinterest.com',
                'unsplash': 'https://unsplash.com',
                'pexels': 'https://pexels.com',
                'pixabay': 'https://pixabay.com',
                'flaticon': 'https://flaticon.com',
                'fontawesome': 'https://fontawesome.com',
                'google fonts': 'https://fonts.google.com',
                'adobe fonts': 'https://fonts.adobe.com',
                'canva': 'https://canva.com',
                'sketch': 'https://sketch.com',
                'invision': 'https://invisionapp.com',
                'framer': 'https://framer.com',
                'webflow': 'https://webflow.com',
                'bubble': 'https://bubble.io',
                'glide': 'https://glideapps.com',
                'airtable': 'https://airtable.com',
                'roam research': 'https://roamresearch.com',
                'obsidian': 'https://obsidian.md',
                'logseq': 'https://logseq.com',
                'remnote': 'https://remnote.com',
                'craft': 'https://craft.do',
                'bear': 'https://bear.app',
                'ulysses': 'https://ulysses.app',
                'scrivener': 'https://literatureandlatte.com/scrivener',
                'grammarly': 'https://grammarly.com',
                'hemingway': 'https://hemingwayapp.com',
                'prowritingaid': 'https://prowritingaid.com',
                'quillbot': 'https://quillbot.com',
                'chatgpt': 'https://chat.openai.com',
                'claude': 'https://anthropic.com/claude',
                'bard': 'https://bard.google.com',
                'bing chat': 'https://bing.com/chat',
                'perplexity': 'https://perplexity.ai',
                'you.com': 'https://you.com',
                'phind': 'https://phind.com',
                'cursor': 'https://cursor.sh',
                'copilot': 'https://github.com/features/copilot',
                'tabnine': 'https://tabnine.com',
                'kite': 'https://kite.com',
                'intellicode': 'https://visualstudio.microsoft.com/services/intellicode',
                'github copilot': 'https://github.com/features/copilot',
                'gitlab copilot': 'https://docs.gitlab.com/ee/user/project/repository/copilot',
                'amazon codewhisperer': 'https://aws.amazon.com/codewhisperer',
                'replit': 'https://replit.com',
                'codesandbox': 'https://codesandbox.io',
                'stackblitz': 'https://stackblitz.com',
                'glitch': 'https://glitch.com',
                'codepen': 'https://codepen.io',
                'jsfiddle': 'https://jsfiddle.net',
                'plunker': 'https://plnkr.co',
                'fiddle': 'https://fiddle.md',
                'playcode': 'https://playcode.io',
                'typescript playground': 'https://typescriptlang.org/play',
                'babel repl': 'https://babeljs.io/repl',
                'es6 console': 'https://es6console.com',
                'python tutor': 'http://pythontutor.com',
                'rust playground': 'https://play.rust-lang.org',
                'go playground': 'https://play.golang.org',
                'kotlin playground': 'https://play.kotlinlang.org',
                'swift playground': 'https://swiftfiddle.com',
                'c++ compiler': 'https://godbolt.org',
                'leetcode': 'https://leetcode.com',
                'hackerrank': 'https://hackerrank.com',
                'codewars': 'https://codewars.com',
                'topcoder': 'https://topcoder.com',
                'codeforces': 'https://codeforces.com',
                'atcoder': 'https://atcoder.jp',
                'project euler': 'https://projecteuler.net',
                'rosalind': 'http://rosalind.info',
                'kaggle competitions': 'https://kaggle.com/competitions',
                'driven data': 'https://drivendata.org',
                'zindi': 'https://zindi.africa',
                'analytics vidhya': 'https://analyticsvidhya.com',
                'data science central': 'https://datasciencecentral.com',
                'kdnuggets': 'https://kdnuggets.com',
                'towards data science': 'https://towardsdatascience.com',
                'machine learning mastery': 'https://machinelearningmastery.com',
                'distill': 'https://distill.pub',
                'papers with code': 'https://paperswithcode.com',
                'arxiv': 'https://arxiv.org',
                'scholar': 'https://scholar.google.com',
                'researchgate': 'https://researchgate.net',
                'academia': 'https://academia.edu',
                'mendeley': 'https://mendeley.com',
                'zotero': 'https://zotero.org',
                'endnote': 'https://endnote.com',
                'refworks': 'https://refworks.com',
                'easybib': 'https://easybib.com',
                'citation machine': 'https://citationmachine.net',
                'bibme': 'https://bibme.org',
                'cite this for me': 'https://citethisforme.com'
            }
            
            # Try to match the query to a known site
            query_lower = query.lower()
            
            # Check for specific website patterns
            specific_patterns = {
                r'(github|gh)\s+(?:repo|repository)\s+(?:for|of|about)?\s+([\w.-]+/[\w.-]+)': lambda m: f"https://github.com/{m.group(2)}",
                r'npm\s+package\s+(?:for|of|about)?\s+([\w.-]+)': lambda m: f"https://www.npmjs.com/package/{m.group(1)}",
                r'pypi\s+(?:package|module)\s+(?:for|of|about)?\s+([\w.-]+)': lambda m: f"https://pypi.org/project/{m.group(1)}",
                r'(?:documentation|docs)\s+(?:for|of|about)?\s+([\w.-]+)\s+version\s+([\d.]+)': lambda m: self._get_docs_url(m.group(1), m.group(2)),
                r'([\w.-]+)\s+version\s+([\d.]+)\s+(?:documentation|docs)': lambda m: self._get_docs_url(m.group(1), m.group(2))
            }
            
            for pattern, url_generator in specific_patterns.items():
                match = re.search(pattern, query_lower)
                if match:
                    generated_url = url_generator(match)
                    logger.info(f"[DEBUG] Found specific pattern match in search_web: '{pattern}' -> {generated_url}")
                    return self.browse_url(generated_url)
            
            # General site mapping
            for site_name, url in site_mapping.items():
                if site_name in query_lower:
                    logger.info(f"[DEBUG] Found site match in search_web: '{site_name}' -> {url}")
                    return self.browse_url(url)
            
            # If not a GitHub repo search or if GitHub search failed, perform regular web search
            search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
            
            # Also try to get some quick results
            try:
                # Use DuckDuckGo Instant Answer API for quick results
                api_url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1&skip_disambig=1"
                
                response = self.session.get(api_url, timeout=5)
                data = response.json()
                
                # Check if there's a direct URL to open
                first_result_url = None
                if data.get('AbstractURL'):
                    first_result_url = data.get('AbstractURL')
                
                # Initialize result variable for information extraction
                result = ""
                
                # Extract useful information if needed
                if data.get('Abstract'):
                    result += f"\nQuick Answer: {data['Abstract']}\n"
                
                if data.get('Definition'):
                    result += f"Definition: {data['Definition']}\n"
                
                if data.get('RelatedTopics'):
                    result += f"\nRelated Topics:\n"
                    for topic in data['RelatedTopics'][:3]:
                        if isinstance(topic, dict) and topic.get('Text'):
                            result += f"• {topic['Text']}\n"
                
                # Open the first result URL if available, otherwise open the search URL
                if first_result_url and first_result_url.startswith(('http://', 'https://')):
                    webbrowser.open(first_result_url)
                    return f"Searched online for '{query}', found: {first_result_url}.\n\nActions performed:\nOpened website: {first_result_url}{result}"
                else:
                    webbrowser.open(search_url)
                    return f"Searched online for '{query}'.\n\nActions performed:\nOpened search results page for '{query}'\nPlease specify which URL you'd like to browse."
                
            except Exception as e:
                logger.warning(f"Failed to get quick results: {str(e)}")
                # Still open the search URL in case of error
                webbrowser.open(search_url)
                return f"Searched online for '{query}'.\n\nActions performed:\nOpened search results page for '{query}'\nPlease specify which URL you'd like to browse."
            
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
    
    def _get_docs_url(self, package_name: str, version: str) -> str:
        """Generate documentation URL for a package and version."""
        package_lower = package_name.lower()
        
        # Common documentation URL patterns
        docs_patterns = {
            'python': f"https://docs.python.org/{version.split('.')[0]}/whatsnew/{version}.html",
            'django': f"https://docs.djangoproject.com/{version}/",
            'flask': f"https://flask.palletsprojects.com/en/{version}/",
            'react': f"https://legacy.reactjs.org/blog/",  # React doesn't have version-specific docs URLs
            'vue': f"https://v{version.split('.')[0]}.vuejs.org/",
            'angular': f"https://v{version.angular.io}/",
            'tensorflow': f"https://www.tensorflow.org/versions/r{version}/api_docs/python/tf",
            'pytorch': f"https://pytorch.org/docs/{version}/",
            'numpy': f"https://numpy.org/doc/{version}/",
            'pandas': f"https://pandas.pydata.org/pandas-docs/version/{version}/"
        }
        
        if package_lower in docs_patterns:
            return docs_patterns[package_lower]
        
        # Default to a search for the documentation
        return f"https://www.google.com/search?q={urllib.parse.quote(f'{package_name} {version} documentation')}"
    
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
    
    def resolve_and_open_url(self, user_request: str, gemini_ai=None) -> str:
        """Use AI to resolve the correct URL for a user request and open it.
        
        Args:
            user_request: The user's request (e.g., "open the openai website")
            gemini_ai: Optional GeminiAI instance for URL resolution
            
        Returns:
            String describing the result
        """
        try:
            # If we have Gemini AI, use it to resolve the URL
            if gemini_ai:
                resolution_prompt = f"""
                The user wants to: "{user_request}"
                
                Your task is to determine the exact URL they want to visit. Think step by step:
                
                1. What website or service are they asking for?
                2. What is the most likely official URL for that website?
                3. If it's a specific page or section, what would that URL be?
                
                For GitHub repositories, be very specific and accurate:
                - "open the github repo for the apple diffucoder model" → https://github.com/apple/ml-diffucoder
                - "open the apple diffucoder github repo" → https://github.com/apple/ml-diffucoder
                - "open the react github repo" → https://github.com/facebook/react
                - "open the vue github repo" → https://github.com/vuejs/vue
                - "open the angular github repo" → https://github.com/angular/angular
                - "open the tensorflow github repo" → https://github.com/tensorflow/tensorflow
                - "open the pytorch github repo" → https://github.com/pytorch/pytorch
                
                For other websites:
                - "open the openai website" → https://openai.com
                - "open the python docs" → https://docs.python.org
                - "open the apple developer website" → https://developer.apple.com
                - "open the microsoft github" → https://github.com/microsoft
                
                CRITICAL: Return ONLY the URL, nothing else. No explanations, no JSON, just the URL.
                For GitHub repositories, you MUST find the exact repository URL. Do not guess or approximate.
                If you're not sure about a repository, search for the most popular/well-known one that matches the request.
                """
                
                ai_response = gemini_ai.generate_response(resolution_prompt, [], [])
                
                if ai_response.get('success'):
                    resolved_url = ai_response.get('response', '').strip()
                    logger.info(f"[DEBUG] AI resolved URL: '{resolved_url}' for request: '{user_request}'")
                    
                    # Try to extract URL from JSON response if it's a JSON structure
                    if resolved_url.startswith('```json') or resolved_url.startswith('{'):
                        try:
                            # Extract JSON content
                            json_match = re.search(r'```json\s*(\{.*?\})\s*```', resolved_url, re.DOTALL)
                            if json_match:
                                json_str = json_match.group(1)
                            else:
                                json_str = resolved_url
                            
                            import json
                            json_data = json.loads(json_str)
                            
                            # Look for URL in actions
                            if 'actions' in json_data:
                                for action in json_data['actions']:
                                    if action.get('action') == 'navigate_url' and 'url' in action:
                                        resolved_url = action['url']
                                        logger.info(f"[DEBUG] Extracted URL from JSON actions: {resolved_url}")
                                        break
                        except (json.JSONDecodeError, KeyError, TypeError) as e:
                            logger.warning(f"[DEBUG] Failed to parse JSON response: {e}")
                    
                    # Clean up the URL (remove quotes, extra text, etc.)
                    resolved_url = re.sub(r'^["\']|["\']$', '', resolved_url)
                    
                    # If it doesn't start with http, add https://
                    if not resolved_url.startswith(('http://', 'https://')):
                        resolved_url = f"https://{resolved_url}"
                    
                    # Validate it's a reasonable URL
                    if re.match(r'^https://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', resolved_url):
                        logger.info(f"[DEBUG] AI URL validation passed, opening: {resolved_url}")
                        # Open the resolved URL
                        return self.browse_url(resolved_url)
                    else:
                        logger.warning(f"[DEBUG] AI URL validation failed: {resolved_url}")
                else:
                    logger.warning(f"[DEBUG] AI response failed: {ai_response}")
            
            # Fallback: Use a simple mapping for common sites
            site_mapping = {
                'openai': 'https://openai.com',
                'github': 'https://github.com',
                'python': 'https://python.org',
                'python docs': 'https://docs.python.org',
                'apple': 'https://apple.com',
                'apple developer': 'https://developer.apple.com',
                'microsoft': 'https://microsoft.com',
                'google': 'https://google.com',
                'stack overflow': 'https://stackoverflow.com',
                'reddit': 'https://reddit.com',
                'twitter': 'https://twitter.com',
                'linkedin': 'https://linkedin.com',
                'facebook': 'https://facebook.com',
                'instagram': 'https://instagram.com',
                'youtube': 'https://youtube.com',
                'netflix': 'https://netflix.com',
                'amazon': 'https://amazon.com',
                'spotify': 'https://spotify.com',
                'discord': 'https://discord.com',
                'slack': 'https://slack.com',
                'zoom': 'https://zoom.us',
                'notion': 'https://notion.so',
                'figma': 'https://figma.com',
                'trello': 'https://trello.com',
                'asana': 'https://asana.com',
                'dropbox': 'https://dropbox.com',
                'google drive': 'https://drive.google.com',
                'gmail': 'https://gmail.com',
                'outlook': 'https://outlook.com',
                'yahoo': 'https://yahoo.com',
                'bing': 'https://bing.com',
                'duckduckgo': 'https://duckduckgo.com',
                'wikipedia': 'https://wikipedia.org',
                'medium': 'https://medium.com',
                'dev.to': 'https://dev.to',
                'hashnode': 'https://hashnode.dev',
                'producthunt': 'https://producthunt.com',
                'hackernews': 'https://news.ycombinator.com',
                'techcrunch': 'https://techcrunch.com',
                'the verge': 'https://theverge.com',
                'ars technica': 'https://arstechnica.com',
                'wired': 'https://wired.com',
                'mit technology review': 'https://technologyreview.com',
                'nvidia': 'https://nvidia.com',
                'amd': 'https://amd.com',
                'intel': 'https://intel.com',
                'linux': 'https://linux.org',
                'ubuntu': 'https://ubuntu.com',
                'debian': 'https://debian.org',
                'fedora': 'https://fedora.org',
                'arch linux': 'https://archlinux.org',
                'docker': 'https://docker.com',
                'kubernetes': 'https://kubernetes.io',
                'terraform': 'https://terraform.io',
                'ansible': 'https://ansible.com',
                'jenkins': 'https://jenkins.io',
                'gitlab': 'https://gitlab.com',
                'bitbucket': 'https://bitbucket.org',
                'jira': 'https://atlassian.com/software/jira',
                'confluence': 'https://atlassian.com/software/confluence',
                'vscode': 'https://code.visualstudio.com',
                'sublime text': 'https://sublimetext.com',
                'atom': 'https://atom.io',
                'vim': 'https://vim.org',
                'emacs': 'https://gnu.org/software/emacs',
                'postman': 'https://postman.com',
                'insomnia': 'https://insomnia.rest',
                'swagger': 'https://swagger.io',
                'openapi': 'https://openapis.org',
                'graphql': 'https://graphql.org',
                'react': 'https://reactjs.org',
                'vue': 'https://vuejs.org',
                'angular': 'https://angular.io',
                'node.js': 'https://nodejs.org',
                'npm': 'https://npmjs.com',
                'yarn': 'https://yarnpkg.com',
                'webpack': 'https://webpack.js.org',
                'babel': 'https://babeljs.io',
                'eslint': 'https://eslint.org',
                'prettier': 'https://prettier.io',
                'typescript': 'https://typescriptlang.org',
                'sass': 'https://sass-lang.com',
                'less': 'https://lesscss.org',
                'bootstrap': 'https://getbootstrap.com',
                'tailwind': 'https://tailwindcss.com',
                'material ui': 'https://mui.com',
                'ant design': 'https://ant.design',
                'django': 'https://djangoproject.com',
                'flask': 'https://flask.palletsprojects.com',
                'fastapi': 'https://fastapi.tiangolo.com',
                'express': 'https://expressjs.com',
                'koa': 'https://koajs.com',
                'spring': 'https://spring.io',
                'laravel': 'https://laravel.com',
                'rails': 'https://rubyonrails.org',
                'asp.net': 'https://dotnet.microsoft.com',
                'php': 'https://php.net',
                'java': 'https://java.com',
                'kotlin': 'https://kotlinlang.org',
                'swift': 'https://swift.org',
                'rust': 'https://rust-lang.org',
                'go': 'https://golang.org',
                'c++': 'https://isocpp.org',
                'c#': 'https://docs.microsoft.com/en-us/dotnet/csharp',
                'scala': 'https://scala-lang.org',
                'clojure': 'https://clojure.org',
                'haskell': 'https://haskell.org',
                'erlang': 'https://erlang.org',
                'elixir': 'https://elixir-lang.org',
                'f#': 'https://fsharp.org',
                'ocaml': 'https://ocaml.org',
                'nim': 'https://nim-lang.org',
                'zig': 'https://ziglang.org',
                'crystal': 'https://crystal-lang.org',
                'julia': 'https://julialang.org',
                'r': 'https://r-project.org',
                'matlab': 'https://mathworks.com/products/matlab.html',
                'octave': 'https://octave.org',
                'scipy': 'https://scipy.org',
                'numpy': 'https://numpy.org',
                'pandas': 'https://pandas.pydata.org',
                'matplotlib': 'https://matplotlib.org',
                'seaborn': 'https://seaborn.pydata.org',
                'plotly': 'https://plotly.com',
                'bokeh': 'https://bokeh.org',
                'tensorflow': 'https://tensorflow.org',
                'pytorch': 'https://pytorch.org',
                'keras': 'https://keras.io',
                'scikit-learn': 'https://scikit-learn.org',
                'xgboost': 'https://xgboost.readthedocs.io',
                'lightgbm': 'https://lightgbm.readthedocs.io',
                'catboost': 'https://catboost.ai',
                'hugging face': 'https://huggingface.co',
                'openai api': 'https://platform.openai.com',
                'anthropic': 'https://anthropic.com',
                'cohere': 'https://cohere.ai',
                'ai21': 'https://ai21.com',
                'replicate': 'https://replicate.com',
                'gradio': 'https://gradio.app',
                'streamlit': 'https://streamlit.io',
                'dash': 'https://plotly.com/dash',
                'voila': 'https://voila.readthedocs.io',
                'jupyter': 'https://jupyter.org',
                'colab': 'https://colab.research.google.com',
                'kaggle': 'https://kaggle.com',
                'datacamp': 'https://datacamp.com',
                'coursera': 'https://coursera.org',
                'edx': 'https://edx.org',
                'udemy': 'https://udemy.com',
                'udacity': 'https://udacity.com',
                'freecodecamp': 'https://freecodecamp.org',
                'the odin project': 'https://theodinproject.com',
                'mdn': 'https://developer.mozilla.org',
                'w3schools': 'https://w3schools.com',
                'css-tricks': 'https://css-tricks.com',
                'smashing magazine': 'https://smashingmagazine.com',
                'a list apart': 'https://alistapart.com',
                'codrops': 'https://tympanus.net/codrops',
                'dribbble': 'https://dribbble.com',
                'behance': 'https://behance.net',
                'pinterest': 'https://pinterest.com',
                'unsplash': 'https://unsplash.com',
                'pexels': 'https://pexels.com',
                'pixabay': 'https://pixabay.com',
                'flaticon': 'https://flaticon.com',
                'fontawesome': 'https://fontawesome.com',
                'google fonts': 'https://fonts.google.com',
                'adobe fonts': 'https://fonts.adobe.com',
                'canva': 'https://canva.com',
                'sketch': 'https://sketch.com',
                'invision': 'https://invisionapp.com',
                'framer': 'https://framer.com',
                'webflow': 'https://webflow.com',
                'bubble': 'https://bubble.io',
                'glide': 'https://glideapps.com',
                'airtable': 'https://airtable.com',
                'roam research': 'https://roamresearch.com',
                'obsidian': 'https://obsidian.md',
                'logseq': 'https://logseq.com',
                'remnote': 'https://remnote.com',
                'craft': 'https://craft.do',
                'bear': 'https://bear.app',
                'ulysses': 'https://ulysses.app',
                'scrivener': 'https://literatureandlatte.com/scrivener',
                'grammarly': 'https://grammarly.com',
                'hemingway': 'https://hemingwayapp.com',
                'prowritingaid': 'https://prowritingaid.com',
                'quillbot': 'https://quillbot.com',
                'chatgpt': 'https://chat.openai.com',
                'claude': 'https://anthropic.com/claude',
                'bard': 'https://bard.google.com',
                'bing chat': 'https://bing.com/chat',
                'perplexity': 'https://perplexity.ai',
                'you.com': 'https://you.com',
                'phind': 'https://phind.com',
                'cursor': 'https://cursor.sh',
                'copilot': 'https://github.com/features/copilot',
                'tabnine': 'https://tabnine.com',
                'kite': 'https://kite.com',
                'intellicode': 'https://visualstudio.microsoft.com/services/intellicode',
                'github copilot': 'https://github.com/features/copilot',
                'gitlab copilot': 'https://docs.gitlab.com/ee/user/project/repository/copilot',
                'amazon codewhisperer': 'https://aws.amazon.com/codewhisperer',
                'replit': 'https://replit.com',
                'codesandbox': 'https://codesandbox.io',
                'stackblitz': 'https://stackblitz.com',
                'glitch': 'https://glitch.com',
                'codepen': 'https://codepen.io',
                'jsfiddle': 'https://jsfiddle.net',
                'plunker': 'https://plnkr.co',
                'fiddle': 'https://fiddle.md',
                'playcode': 'https://playcode.io',
                'typescript playground': 'https://typescriptlang.org/play',
                'babel repl': 'https://babeljs.io/repl',
                'es6 console': 'https://es6console.com',
                'python tutor': 'http://pythontutor.com',
                'rust playground': 'https://play.rust-lang.org',
                'go playground': 'https://play.golang.org',
                'kotlin playground': 'https://play.kotlinlang.org',
                'swift playground': 'https://swiftfiddle.com',
                'c++ compiler': 'https://godbolt.org',
                'leetcode': 'https://leetcode.com',
                'hackerrank': 'https://hackerrank.com',
                'codewars': 'https://codewars.com',
                'topcoder': 'https://topcoder.com',
                'codeforces': 'https://codeforces.com',
                'atcoder': 'https://atcoder.jp',
                'project euler': 'https://projecteuler.net',
                'rosalind': 'http://rosalind.info',
                'kaggle competitions': 'https://kaggle.com/competitions',
                'driven data': 'https://drivendata.org',
                'zindi': 'https://zindi.africa',
                'analytics vidhya': 'https://analyticsvidhya.com',
                'data science central': 'https://datasciencecentral.com',
                'kdnuggets': 'https://kdnuggets.com',
                'towards data science': 'https://towardsdatascience.com',
                'machine learning mastery': 'https://machinelearningmastery.com',
                'distill': 'https://distill.pub',
                'papers with code': 'https://paperswithcode.com',
                'arxiv': 'https://arxiv.org',
                'scholar': 'https://scholar.google.com',
                'researchgate': 'https://researchgate.net',
                'academia': 'https://academia.edu',
                'mendeley': 'https://mendeley.com',
                'zotero': 'https://zotero.org',
                'endnote': 'https://endnote.com',
                'refworks': 'https://refworks.com',
                'easybib': 'https://easybib.com',
                'citation machine': 'https://citationmachine.net',
                'bibme': 'https://bibme.org',
                'cite this for me': 'https://citethisforme.com'
            }
            
            # Try to match the user request to a known site
            user_request_lower = user_request.lower()
            logger.info(f"[DEBUG] Checking site mapping for: '{user_request_lower}'")
            for site_name, url in site_mapping.items():
                if site_name in user_request_lower:
                    logger.info(f"[DEBUG] Found site match: '{site_name}' -> {url}")
                    return self.browse_url(url)
            
            logger.info(f"[DEBUG] No site mapping found, falling back to web search")
            
            # If no direct match, try AI resolution for complex requests
            if gemini_ai:
                try:
                    # For complex requests like GitHub repositories, ask AI directly
                    ai_prompt = f"""
                    The user wants to: "{user_request}"
                    
                    Determine the exact URL they want to visit. For GitHub repositories, return the direct repository URL.
                    For other sites, return the most appropriate URL.
                    
                    Examples:
                    - "open the github repo for the apple diffucoder model" → https://github.com/apple/ml-diffusers
                    - "open the openai website" → https://openai.com
                    - "open the python docs" → https://docs.python.org
                    
                    Return ONLY the URL, nothing else.
                    """
                    
                    ai_response = gemini_ai.generate_response(ai_prompt, [], [])
                    
                    if ai_response.get('success'):
                        resolved_url = ai_response.get('response', '').strip()
                        logger.info(f"[DEBUG] AI resolved complex URL: '{resolved_url}' for request: '{user_request}'")
                        
                        # Clean up the URL
                        resolved_url = re.sub(r'^["\']|["\']$', '', resolved_url)
                        
                        # If it doesn't start with http, add https://
                        if not resolved_url.startswith(('http://', 'https://')):
                            resolved_url = f"https://{resolved_url}"
                        
                        # Validate it's a reasonable URL
                        if re.match(r'^https://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', resolved_url):
                            logger.info(f"[DEBUG] AI URL validation passed, opening: {resolved_url}")
                            return self.browse_url(resolved_url)
                        else:
                            logger.warning(f"[DEBUG] AI URL validation failed: {resolved_url}")
                except Exception as e:
                    logger.warning(f"[DEBUG] AI resolution for complex request failed: {e}")
            
            # Final fallback: web search
            return self.search_web(user_request)
            
        except Exception as e:
            logger.error(f"Error resolving and opening URL: {str(e)}")
            return f"Error resolving URL: {str(e)}"
