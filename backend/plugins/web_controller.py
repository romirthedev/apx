import requests
import webbrowser
import logging
import os
import time
import urllib.parse
import re
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)

class WebController:
    def __init__(self):
        """Initialize the WebController with enhanced capabilities."""
        # Initialize session with custom headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        })
        
        # Set up download directory
        self.download_dir = Path.home() / 'Downloads'
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize site mappings with rich metadata
        self.site_mappings = {
            'openai': {
                'base_url': 'https://openai.com',
                'search_url': 'https://openai.com/search?q={query}',
                'docs_url': 'https://platform.openai.com/docs',
                'api_url': 'https://api.openai.com/v1',
                'patterns': ['openai', 'gpt', 'chatgpt', 'dall-e']
            },
            'github': {
                'base_url': 'https://github.com',
                'search_url': 'https://github.com/search?q={query}',
                'api_url': 'https://api.github.com',
                'raw_url': 'https://raw.githubusercontent.com',
                'patterns': ['github', 'gh', 'repo', 'repository']
            },
            'python': {
                'base_url': 'https://python.org',
                'docs_url': 'https://docs.python.org',
                'package_url': 'https://pypi.org/project/{package}',
                'search_url': 'https://pypi.org/search/?q={query}',
                'patterns': ['python', 'pip', 'pypi', 'package']
            },
            'apple': {
                'base_url': 'https://apple.com',
                'developer_url': 'https://developer.apple.com',
                'support_url': 'https://support.apple.com',
                'search_url': 'https://support.apple.com/kb/index?page=search&q={query}',
                'patterns': ['apple', 'macos', 'ios', 'ipados', 'watchos']
            },
            'google': {
                'base_url': 'https://www.google.com',
                'search_url': 'https://www.google.com/search?q={query}',
                'maps_url': 'https://www.google.com/maps/search/{query}',
                'drive_url': 'https://drive.google.com',
                'patterns': ['google', 'search', 'maps', 'drive']
            },
            'stackoverflow': {
                'base_url': 'https://stackoverflow.com',
                'search_url': 'https://stackoverflow.com/search?q={query}',
                'patterns': ['stackoverflow', 'stack overflow', 'coding question']
            },
            'linkedin': {
                'base_url': 'https://www.linkedin.com',
                'search_url': 'https://www.linkedin.com/search/results/all/?keywords={query}',
                'patterns': ['linkedin', 'professional', 'job', 'career']
            },
            'twitter': {
                'base_url': 'https://twitter.com',
                'search_url': 'https://twitter.com/search?q={query}',
                'patterns': ['twitter', 'tweet', '@']
            }
        }
        
        # Initialize protocol handlers
        self.protocol_handlers = {
            'mailto': self._handle_mailto,
            'tel': self._handle_tel,
            'slack': self._handle_slack,
            'zoom': self._handle_zoom,
            'teams': self._handle_teams
        }
        
        # Initialize browser preferences
        self.browser_prefs = {
            'new_window': 2,  # Open in new tab
            'autoraise': True  # Bring browser window to front
        }
        
    def open_gmail_compose(self, to: str = "", subject: str = "", body: str = "") -> str:
        """Open Gmail compose window with pre-filled fields.
        
        Args:
            to: Email recipient
            subject: Email subject
            body: Email body content
            
        Returns:
            Status message
        """
        try:
            # Build Gmail compose URL
            base_url = "https://mail.google.com/mail/?view=cm"
            params = {}
            
            if to:
                params['to'] = to
            if subject:
                params['subject'] = subject
            if body:
                params['body'] = body
                
            # Create the full URL
            gmail_url = base_url
            if params:
                query_string = urllib.parse.urlencode(params)
                gmail_url += f"&{query_string}"
            
            # Open in browser
            webbrowser.open(gmail_url)
            
            recipient_info = f" to {to}" if to else ""
            return f"✅ Opened Gmail compose{recipient_info}"
            
        except Exception as e:
            logger.error(f"Failed to open Gmail compose: {str(e)}")
            return f"❌ Failed to open Gmail compose: {str(e)}"
            
    def open_mail_compose(self, to: str = "", subject: str = "", body: str = "") -> str:
        """Open Mac Mail app compose window with pre-filled fields.
        
        Args:
            to: Email recipient
            subject: Email subject
            body: Email body content
            
        Returns:
            Status message
        """
        try:
            # Build mailto URL for Mail app
            params = {}
            if subject:
                params['subject'] = subject
            if body:
                # Use quote_plus to prevent '+' characters in the body
                params['body'] = body
                
            # Create mailto URL
            mailto_url = f"mailto:{to}"
            if params:
                # Use safe='' to prevent spaces from being converted to '+'
                query_string = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
                mailto_url += f"?{query_string}"
            
            # Open Mail app with mailto URL
            subprocess.run(['open', '-a', 'Mail', mailto_url], check=True)
            
            recipient_info = f" to {to}" if to else ""
            return f"✅ Opened Mail app compose{recipient_info}"
            
        except Exception as e:
            logger.error(f"Failed to open Mail app compose: {str(e)}")
            return f"❌ Failed to open Mail app compose: {str(e)}"
    
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
    
    def _handle_mailto(self, url: str) -> str:
        """Handle mailto protocol URLs.
        
        Args:
            url: The mailto URL to handle
            
        Returns:
            Status message
        """
        try:
            # Parse mailto URL
            parsed = urllib.parse.urlparse(url)
            params = dict(urllib.parse.parse_qsl(parsed.query))
            
            # Extract email components
            to = parsed.path
            subject = params.get('subject', '')
            body = params.get('body', '')
            
            # Try Gmail first, fallback to system mail app
            try:
                return self.open_gmail_compose(to, subject, body)
            except Exception:
                return self.open_mail_compose(to, subject, body)
                
        except Exception as e:
            logger.error(f"Failed to handle mailto URL: {str(e)}")
            return f"Failed to handle mailto URL: {str(e)}"
    
    def _handle_tel(self, url: str) -> str:
        """Handle tel protocol URLs.
        
        Args:
            url: The tel URL to handle
            
        Returns:
            Status message
        """
        try:
            # Extract phone number
            phone = urllib.parse.unquote(url.replace('tel:', ''))
            
            # Platform-specific phone handling
            if sys.platform == 'darwin':
                # Use FaceTime on macOS
                subprocess.run(['open', '-a', 'FaceTime', f'tel://{phone}'])
                return f"Opened FaceTime with {phone}"
            else:
                # Open in default handler
                webbrowser.open(url)
                return f"Opened phone handler for {phone}"
                
        except Exception as e:
            logger.error(f"Failed to handle tel URL: {str(e)}")
            return f"Failed to handle tel URL: {str(e)}"
    
    def _handle_slack(self, url: str) -> str:
        """Handle Slack protocol URLs.
        
        Args:
            url: The slack URL to handle
            
        Returns:
            Status message
        """
        try:
            # Try native app first
            try:
                if sys.platform == 'darwin':
                    subprocess.run(['open', '-a', 'Slack', url])
                else:
                    webbrowser.open(url)
                return "Opened in Slack app"
            except Exception:
                # Fallback to web version
                web_url = url.replace('slack://', 'https://app.slack.com/')
                webbrowser.open(web_url)
                return "Opened in Slack web app"
                
        except Exception as e:
            logger.error(f"Failed to handle Slack URL: {str(e)}")
            return f"Failed to handle Slack URL: {str(e)}"
    
    def _handle_zoom(self, url: str) -> str:
        """Handle Zoom protocol URLs.
        
        Args:
            url: The zoom URL to handle
            
        Returns:
            Status message
        """
        try:
            # Try native app first
            try:
                if sys.platform == 'darwin':
                    subprocess.run(['open', '-a', 'zoom.us', url])
                else:
                    webbrowser.open(url)
                return "Opened in Zoom app"
            except Exception:
                # Fallback to web version
                web_url = url.replace('zoommtg://', 'https://zoom.us/j/')
                webbrowser.open(web_url)
                return "Opened in Zoom web app"
                
        except Exception as e:
            logger.error(f"Failed to handle Zoom URL: {str(e)}")
            return f"Failed to handle Zoom URL: {str(e)}"
    
    def _handle_teams(self, url: str) -> str:
        """Handle Microsoft Teams protocol URLs.
        
        Args:
            url: The teams URL to handle
            
        Returns:
            Status message
        """
        try:
            # Try native app first
            try:
                if sys.platform == 'darwin':
                    subprocess.run(['open', '-a', 'Microsoft Teams', url])
                else:
                    webbrowser.open(url)
                return "Opened in Teams app"
            except Exception:
                # Fallback to web version
                web_url = url.replace('msteams://', 'https://teams.microsoft.com/')
                webbrowser.open(web_url)
                return "Opened in Teams web app"
                
        except Exception as e:
            logger.error(f"Failed to handle Teams URL: {str(e)}")
            return f"Failed to handle Teams URL: {str(e)}"
    
    def search_web(self, query: str) -> str:
        """Perform an intelligent web search based on query analysis.
        
        Args:
            query: The search query to process
            
        Returns:
            Status message
        """
        try:
            # Check for protocol URLs first
            url_match = re.match(r'^([a-z]+):.+', query)
            if url_match:
                protocol = url_match.group(1)
                if protocol in self.protocol_handlers:
                    return self.protocol_handlers[protocol](query)
            
            # Check for site-specific patterns
            for site, config in self.site_mappings.items():
                if any(pattern in query.lower() for pattern in config['patterns']):
                    # Check for search vs direct access
                    if 'search' in query.lower():
                        search_terms = re.sub(r'.*?search\s+(?:for|about)?\s*', '', query, flags=re.IGNORECASE)
                        url = config['search_url'].format(query=urllib.parse.quote(search_terms))
                    else:
                        # Try to determine the most appropriate URL
                        if 'api' in query.lower() and 'api_url' in config:
                            url = config['api_url']
                        elif 'doc' in query.lower() and 'docs_url' in config:
                            url = config['docs_url']
                        else:
                            url = config['base_url']
                    
                    webbrowser.open(url, new=self.browser_prefs['new_window'], autoraise=self.browser_prefs['autoraise'])
                    return f"Opened {site} at {url}"
            
            # Check for Python version documentation
            python_version_match = re.search(r'python\s+(?:version|release)\s*(\d+(?:\.\d+)*)', query, re.IGNORECASE)
            if python_version_match:
                version = python_version_match.group(1)
                url = f"https://docs.python.org/{version.split('.')[0]}/whatsnew/{version}.html"
                webbrowser.open(url, **self.browser_prefs)
                return f"Opened Python {version} documentation"
            
            # Check for GitHub repository search
            if re.search(r'(?:github|gh)\s+repo(?:sitory)?|repo(?:sitory)?\s+(?:for|of|about|on)\s+(?:github|gh)', query, re.IGNORECASE):
                success, repo_url, message = self.search_github_repo(query)
                if success and repo_url:
                    webbrowser.open(repo_url, **self.browser_prefs)
                    return f"Found: {message}\nURL: {repo_url}\n\nOpened in browser."
            
            # Default to Google search
            search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
            webbrowser.open(search_url, **self.browser_prefs)
            return f"Performed Google search for: {query}"
            
        except Exception as e:
            logger.error(f"Failed to process web search: {str(e)}")
            return f"Failed to process web search: {str(e)}"

        # Site mappings
        site_mapping = {
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
             try:
                 webbrowser.open(search_url)
                 return f"Searched online for '{query}'.\n\nActions performed:\nOpened search results page for '{query}'\nPlease specify which URL you'd like to browse."
             except Exception as e:
                 logger.error(f"Error performing web search: {str(e)}")
                 return f"Failed to search web: {str(e)}"
    
    def browse_url(self, url: str, validate: bool = True, new_window: bool = None, autoraise: bool = None) -> str:
        """Open a URL in the default browser with enhanced validation and handling.
        
        Args:
            url: The URL to open
            validate: Whether to perform URL validation and normalization
            new_window: Whether to open in a new window (overrides preferences)
            autoraise: Whether to bring browser window to front (overrides preferences)
            
        Returns:
            Status message
        """
        try:
            if validate:
                # Validate and normalize URL
                parsed = urllib.parse.urlparse(url)
                
                # Handle special protocols
                if parsed.scheme in self.protocol_handlers:
                    return self.protocol_handlers[parsed.scheme](url)
                
                # Add https:// if no scheme
                if not parsed.scheme:
                    url = 'https://' + url
                    parsed = urllib.parse.urlparse(url)
                
                # Validate components
                if not parsed.netloc:
                    return f"❌ Invalid URL: {url} (missing domain)"
                
                # Check for common typos
                if parsed.scheme not in ['http', 'https', 'file', 'ftp']:
                    suggested_scheme = 'https'
                    if parsed.scheme in ['htttp', 'htps', 'http:', 'https:']:
                        url = f"{suggested_scheme}://{parsed.netloc}{parsed.path}"
                        if parsed.query:
                            url += f"?{parsed.query}"
                        if parsed.fragment:
                            url += f"#{parsed.fragment}"
                
                # Normalize URL
                url = urllib.parse.urlunparse(parsed)
            
            # Set browser preferences
            browser_prefs = self.browser_prefs.copy()
            if new_window is not None:
                browser_prefs['new_window'] = 2 if new_window else 0
            if autoraise is not None:
                browser_prefs['autoraise'] = autoraise
            
            # Open URL in browser
            webbrowser.open(url, new=browser_prefs['new_window'], autoraise=browser_prefs['autoraise'])
            
            # Try to get page title and metadata
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    content = response.text
                    
                    # Extract title
                    title = None
                    title_match = re.search(r'<title[^>]*>([^<]+)</title>', content)
                    if title_match:
                        title = title_match.group(1).strip()
                    
                    # Extract description
                    description = None
                    desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\'>]+)["\'][^>]*>', content)
                    if desc_match:
                        description = desc_match.group(1).strip()
                    
                    # Build response message
                    window_type = "new window" if browser_prefs['new_window'] == 2 else "current window"
                    focus_info = " and brought to front" if browser_prefs['autoraise'] else ""
                    
                    msg = f"✅ Opened in {window_type}{focus_info}:\n"
                    if title:
                        msg += f"Title: {title}\n"
                    if description:
                        msg += f"Description: {description}\n"
                    msg += f"URL: {url}"
                    return msg
                
                return f"✅ Opened URL: {url}"
                
            except Exception as e:
                logger.warning(f"Failed to get page info: {str(e)}")
                return f"✅ Opened URL: {url}"
            
        except Exception as e:
            logger.error(f"Error browsing URL: {str(e)}")
            return f"❌ Failed to open URL: {str(e)}"
    
    def download_file(self, url: str, filename: Optional[str] = None, directory: Optional[str] = None, overwrite: bool = False) -> str:
        """Download a file from URL with enhanced handling and progress tracking.
        
        Args:
            url: The URL to download from
            filename: Optional custom filename (default: extracted from URL)
            directory: Optional custom download directory (default: self.download_dir)
            overwrite: Whether to overwrite existing files (default: False)
            
        Returns:
            Status message with download details
        """
        try:
            # Validate and normalize URL
            parsed = urllib.parse.urlparse(url)
            if not parsed.scheme:
                url = 'https://' + url
                parsed = urllib.parse.urlparse(url)
            
            # Validate URL
            if not parsed.netloc:
                return f"❌ Invalid URL: {url} (missing domain)"
            
            # Set download directory
            download_dir = Path(directory) if directory else self.download_dir
            download_dir.mkdir(parents=True, exist_ok=True)
            
            
            if not filename:
                filename = os.path.basename(parsed.path)
                if not filename:
                    # Try to get filename from Content-Disposition header
                    response = self.session.head(url, allow_redirects=True)
                    if 'Content-Disposition' in response.headers:
                        content_disposition = response.headers['Content-Disposition']
                        matches = re.findall('filename=([^;]+)', content_disposition)
                        if matches:
                            filename = matches[0].strip('"\'')
                    
                    # If still no filename, use timestamp
                    if not filename:
                        ext = mimetypes.guess_extension(response.headers.get('Content-Type', '')) or '.txt'
                        filename = f"download_{int(time.time())}{ext}"
            
            # Clean filename
            filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
            
            # Build full file path
            file_path = download_dir / filename
            
            # Check if file exists
            if file_path.exists() and not overwrite:
                return f"❌ File already exists: {file_path}\nUse overwrite=True to replace"
            
            # Download with progress tracking
            response = self.session.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            block_size = 8192
            downloaded_size = 0
            
            with open(file_path, 'wb') as f:
                for data in response.iter_content(block_size):
                    downloaded_size += len(data)
                    f.write(data)
            
            # Get file details
            file_size = file_path.stat().st_size
            file_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
            
            # Format size for display
            def format_size(size):
                for unit in ['B', 'KB', 'MB', 'GB']:
                    if size < 1024:
                        return f"{size:.1f} {unit}"
                    size /= 1024
                return f"{size:.1f} TB"
            
            return f"✅ Downloaded successfully:\nFile: {filename}\nSize: {format_size(file_size)}\nType: {file_type}\nLocation: {file_path}"
            
        except Exception as e:
            logger.error(f"Error downloading file: {str(e)}")
            return f"❌ Failed to download file: {str(e)}"
    
    def _get_docs_url(self, package: str, version: str) -> str:
        """Generate documentation URL for a given package and version.
        
        Args:
            package: The package name
            version: The version number
            
        Returns:
            Documentation URL
        """
        # Common documentation URL patterns
        docs_patterns = {
            # Programming Languages
            'python': {
                'pattern': 'https://docs.python.org/{major}/whatsnew/{version}.html',
                'fallback': 'https://docs.python.org/{major}/',
                'version_format': lambda v: {'major': v.split('.')[0], 'version': v}
            },
            'node': {
                'pattern': 'https://nodejs.org/docs/v{version}/api/',
                'fallback': 'https://nodejs.org/docs/latest/api/',
                'version_format': lambda v: {'version': v}
            },
            'typescript': {
                'pattern': 'https://www.typescriptlang.org/docs/handbook/release-notes/{version}.html',
                'fallback': 'https://www.typescriptlang.org/docs/',
                'version_format': lambda v: {'version': v}
            },
            'rust': {
                'pattern': 'https://doc.rust-lang.org/{version}/book/',
                'fallback': 'https://doc.rust-lang.org/stable/book/',
                'version_format': lambda v: {'version': 'stable' if v == 'stable' else v}
            },
            'go': {
                'pattern': 'https://golang.org/doc/go{version}',
                'fallback': 'https://golang.org/doc/',
                'version_format': lambda v: {'version': v}
            },
            'kotlin': {
                'pattern': 'https://kotlinlang.org/docs/releases.html#{version}',
                'fallback': 'https://kotlinlang.org/docs/',
                'version_format': lambda v: {'version': v}
            },
            'swift': {
                'pattern': 'https://docs.swift.org/swift-book/{version}/',
                'fallback': 'https://docs.swift.org/swift-book/',
                'version_format': lambda v: {'version': v}
            },
            
            # Web Frameworks
            'django': {
                'pattern': 'https://docs.djangoproject.com/{version}/',
                'fallback': 'https://docs.djangoproject.com/en/stable/',
                'version_format': lambda v: {'version': v}
            },
            'flask': {
                'pattern': 'https://flask.palletsprojects.com/en/{version}/',
                'fallback': 'https://flask.palletsprojects.com/en/latest/',
                'version_format': lambda v: {'version': v}
            },
            'fastapi': {
                'pattern': 'https://fastapi.tiangolo.com/{version}/',
                'fallback': 'https://fastapi.tiangolo.com/release-notes/',
                'version_format': lambda v: {'version': v}
            },
            'react': {
                'pattern': 'https://react.dev/reference/react/{version}',
                'fallback': 'https://react.dev/learn',
                'version_format': lambda v: {'version': v}
            },
            'vue': {
                'pattern': 'https://v{version}.vuejs.org/guide/',
                'fallback': 'https://vuejs.org/guide/introduction.html',
                'version_format': lambda v: {'version': v}
            },
            'angular': {
                'pattern': 'https://angular.io/guide/update-to-version-{version}',
                'fallback': 'https://angular.io/docs',
                'version_format': lambda v: {'version': v}
            },
            'express': {
                'pattern': 'https://expressjs.com/{version}/',
                'fallback': 'https://expressjs.com/',
                'version_format': lambda v: {'version': v}
            },
            'spring': {
                'pattern': 'https://docs.spring.io/{version}/reference/',
                'fallback': 'https://spring.io/guides',
                'version_format': lambda v: {'version': v}
            },
            'laravel': {
                'pattern': 'https://laravel.com/docs/{version}',
                'fallback': 'https://laravel.com/docs',
                'version_format': lambda v: {'version': v}
            },
            
            # Infrastructure & Tools
            'docker': {
                'pattern': 'https://docs.docker.com/engine/release-notes/{version}/',
                'fallback': 'https://docs.docker.com/',
                'version_format': lambda v: {'version': v}
            },
            'kubernetes': {
                'pattern': 'https://kubernetes.io/docs/reference/kubernetes-api/v{version}/',
                'fallback': 'https://kubernetes.io/docs/home/',
                'version_format': lambda v: {'version': v}
            },
            'terraform': {
                'pattern': 'https://www.terraform.io/docs/language/{version}.html',
                'fallback': 'https://www.terraform.io/docs',
                'version_format': lambda v: {'version': v}
            },
            'nginx': {
                'pattern': 'https://nginx.org/en/docs/{version}/',
                'fallback': 'https://nginx.org/en/docs/',
                'version_format': lambda v: {'version': v}
            },
            'redis': {
                'pattern': 'https://redis.io/docs/{version}/',
                'fallback': 'https://redis.io/documentation',
                'version_format': lambda v: {'version': v}
            },
            'postgresql': {
                'pattern': 'https://www.postgresql.org/docs/{version}/',
                'fallback': 'https://www.postgresql.org/docs/',
                'version_format': lambda v: {'version': v}
            },
            
            # Data Science & ML Libraries
            'pandas': {
                'pattern': 'https://pandas.pydata.org/pandas-docs/version/{version}/',
                'fallback': 'https://pandas.pydata.org/docs/',
                'version_format': lambda v: {'version': v}
            },
            'numpy': {
                'pattern': 'https://numpy.org/doc/{version}/',
                'fallback': 'https://numpy.org/doc/stable/',
                'version_format': lambda v: {'version': v}
            },
            'scipy': {
                'pattern': 'https://docs.scipy.org/doc/{version}/',
                'fallback': 'https://docs.scipy.org/doc/scipy/',
                'version_format': lambda v: {'version': v}
            },
            'scikit-learn': {
                'pattern': 'https://scikit-learn.org/{version}/',
                'fallback': 'https://scikit-learn.org/stable/',
                'version_format': lambda v: {'version': v}
            },
            'tensorflow': {
                'pattern': 'https://www.tensorflow.org/versions/{version}/',
                'fallback': 'https://www.tensorflow.org/guide',
                'version_format': lambda v: {'version': v}
            },
            'pytorch': {
                'pattern': 'https://pytorch.org/docs/{version}/',
                'fallback': 'https://pytorch.org/docs/stable/',
                'version_format': lambda v: {'version': v}
            },
            
            # Cloud Platforms
            'aws-sdk': {
                'pattern': 'https://docs.aws.amazon.com/sdk-for-javascript/v{version}/',
                'fallback': 'https://docs.aws.amazon.com/sdk-for-javascript/',
                'version_format': lambda v: {'version': v}
            },
            'google-cloud': {
                'pattern': 'https://cloud.google.com/python/docs/{version}/',
                'fallback': 'https://cloud.google.com/python/docs/',
                'version_format': lambda v: {'version': v}
            },
            'azure-sdk': {
                'pattern': 'https://docs.microsoft.com/python/azure/sdk/{version}/',
                'fallback': 'https://docs.microsoft.com/azure/developer/python/',
                'version_format': lambda v: {'version': v}
            },
            
            # JavaScript Libraries & Frameworks
            'jquery': {
                'pattern': 'https://api.jquery.com/{version}/',
                'fallback': 'https://api.jquery.com/',
                'version_format': lambda v: {'version': v}
            },
            'lodash': {
                'pattern': 'https://lodash.com/docs/{version}',
                'fallback': 'https://lodash.com/docs',
                'version_format': lambda v: {'version': v}
            },
            'moment': {
                'pattern': 'https://momentjs.com/docs/#{version}',
                'fallback': 'https://momentjs.com/docs/',
                'version_format': lambda v: {'version': v}
            },
            'axios': {
                'pattern': 'https://axios-http.com/docs/v{version}/',
                'fallback': 'https://axios-http.com/docs/intro',
                'version_format': lambda v: {'version': v}
            },
            'next': {
                'pattern': 'https://nextjs.org/docs/v{version}',
                'fallback': 'https://nextjs.org/docs',
                'version_format': lambda v: {'version': v}
            },
            'nuxt': {
                'pattern': 'https://nuxtjs.org/docs/v{version}/',
                'fallback': 'https://nuxtjs.org/docs',
                'version_format': lambda v: {'version': v}
            },
            'gatsby': {
                'pattern': 'https://www.gatsbyjs.com/docs/v{version}/',
                'fallback': 'https://www.gatsbyjs.com/docs/',
                'version_format': lambda v: {'version': v}
            },
            'svelte': {
                'pattern': 'https://svelte.dev/docs/v{version}',
                'fallback': 'https://svelte.dev/docs',
                'version_format': lambda v: {'version': v}
            },
            'remix': {
                'pattern': 'https://remix.run/docs/v{version}',
                'fallback': 'https://remix.run/docs',
                'version_format': lambda v: {'version': v}
            },
            'astro': {
                'pattern': 'https://docs.astro.build/v{version}/',
                'fallback': 'https://docs.astro.build/',
                'version_format': lambda v: {'version': v}
            },
            
            # Mobile Development
            'react-native': {
                'pattern': 'https://reactnative.dev/docs/v{version}/',
                'fallback': 'https://reactnative.dev/docs/getting-started',
                'version_format': lambda v: {'version': v}
            },
            'flutter': {
                'pattern': 'https://docs.flutter.dev/release/{version}',
                'fallback': 'https://docs.flutter.dev/',
                'version_format': lambda v: {'version': v}
            },
            'ionic': {
                'pattern': 'https://ionicframework.com/docs/v{version}/',
                'fallback': 'https://ionicframework.com/docs/',
                'version_format': lambda v: {'version': v}
            },
            'xamarin': {
                'pattern': 'https://docs.microsoft.com/xamarin/xamarin-forms/{version}/',
                'fallback': 'https://docs.microsoft.com/xamarin/',
                'version_format': lambda v: {'version': v}
            },
            
            # Databases
            'mongodb': {
                'pattern': 'https://www.mongodb.com/docs/v{version}/',
                'fallback': 'https://www.mongodb.com/docs/',
                'version_format': lambda v: {'version': v}
            },
            'mysql': {
                'pattern': 'https://dev.mysql.com/doc/{version}/',
                'fallback': 'https://dev.mysql.com/doc/',
                'version_format': lambda v: {'version': v}
            },
            'sqlite': {
                'pattern': 'https://sqlite.org/docs/{version}/',
                'fallback': 'https://sqlite.org/docs.html',
                'version_format': lambda v: {'version': v}
            },
            'cassandra': {
                'pattern': 'https://cassandra.apache.org/doc/{version}/',
                'fallback': 'https://cassandra.apache.org/doc/latest/',
                'version_format': lambda v: {'version': v}
            },
            'elasticsearch': {
                'pattern': 'https://www.elastic.co/guide/en/elasticsearch/{version}/index.html',
                'fallback': 'https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html',
                'version_format': lambda v: {'version': v}
            },
            'neo4j': {
                'pattern': 'https://neo4j.com/docs/cypher-manual/{version}/',
                'fallback': 'https://neo4j.com/docs/',
                'version_format': lambda v: {'version': v}
            },
            
            # Testing Frameworks
            'jest': {
                'pattern': 'https://jestjs.io/docs/{version}/',
                'fallback': 'https://jestjs.io/docs/getting-started',
                'version_format': lambda v: {'version': v}
            },
            'mocha': {
                'pattern': 'https://mochajs.org/api/{version}/',
                'fallback': 'https://mochajs.org/',
                'version_format': lambda v: {'version': v}
            },
            'pytest': {
                'pattern': 'https://docs.pytest.org/en/{version}/',
                'fallback': 'https://docs.pytest.org/en/stable/',
                'version_format': lambda v: {'version': v}
            },
            'junit': {
                'pattern': 'https://junit.org/junit{version}/docs/current/user-guide/',
                'fallback': 'https://junit.org/junit5/docs/current/user-guide/',
                'version_format': lambda v: {'version': v}
            },
            'selenium': {
                'pattern': 'https://www.selenium.dev/documentation/{version}/',
                'fallback': 'https://www.selenium.dev/documentation/',
                'version_format': lambda v: {'version': v}
            },
            'cypress': {
                'pattern': 'https://docs.cypress.io/guides/references/legacy-browsers#{version}',
                'fallback': 'https://docs.cypress.io/',
                'version_format': lambda v: {'version': v}
            },
            
            # DevOps Tools
            'jenkins': {
                'pattern': 'https://www.jenkins.io/doc/book/{version}/',
                'fallback': 'https://www.jenkins.io/doc/',
                'version_format': lambda v: {'version': v}
            },
            'gitlab': {
                'pattern': 'https://docs.gitlab.com/{version}/',
                'fallback': 'https://docs.gitlab.com/',
                'version_format': lambda v: {'version': v}
            },
            'ansible': {
                'pattern': 'https://docs.ansible.com/ansible/{version}/index.html',
                'fallback': 'https://docs.ansible.com/',
                'version_format': lambda v: {'version': v}
            },
            'prometheus': {
                'pattern': 'https://prometheus.io/docs/prometheus/{version}/',
                'fallback': 'https://prometheus.io/docs/introduction/overview/',
                'version_format': lambda v: {'version': v}
            },
            'grafana': {
                'pattern': 'https://grafana.com/docs/grafana/{version}/',
                'fallback': 'https://grafana.com/docs/',
                'version_format': lambda v: {'version': v}
            },
            'helm': {
                'pattern': 'https://helm.sh/docs/v{version}/',
                'fallback': 'https://helm.sh/docs/',
                'version_format': lambda v: {'version': v}
            },
            
            # State Management
            'redux': {
                'pattern': 'https://redux.js.org/introduction/{version}',
                'fallback': 'https://redux.js.org/introduction/getting-started',
                'version_format': lambda v: {'version': v}
            },
            'mobx': {
                'pattern': 'https://mobx.js.org/README{version}.html',
                'fallback': 'https://mobx.js.org/README.html',
                'version_format': lambda v: {'version': v}
            },
            'vuex': {
                'pattern': 'https://vuex.vuejs.org/{version}/',
                'fallback': 'https://vuex.vuejs.org/',
                'version_format': lambda v: {'version': v}
            },
            'pinia': {
                'pattern': 'https://pinia.vuejs.org/v{version}/',
                'fallback': 'https://pinia.vuejs.org/',
                'version_format': lambda v: {'version': v}
            },
            'recoil': {
                'pattern': 'https://recoiljs.org/docs/v{version}/',
                'fallback': 'https://recoiljs.org/docs/introduction/getting-started',
                'version_format': lambda v: {'version': v}
            },
            'zustand': {
                'pattern': 'https://docs.pmnd.rs/zustand/v{version}/',
                'fallback': 'https://docs.pmnd.rs/zustand/getting-started/introduction',
                'version_format': lambda v: {'version': v}
            },
            
            # UI Libraries
            'material-ui': {
                'pattern': 'https://mui.com/material-ui/getting-started/{version}/',
                'fallback': 'https://mui.com/material-ui/getting-started/overview/',
                'version_format': lambda v: {'version': v}
            },
            'ant-design': {
                'pattern': 'https://ant.design/docs/react/{version}/',
                'fallback': 'https://ant.design/docs/react/introduce',
                'version_format': lambda v: {'version': v}
            },
            'chakra-ui': {
                'pattern': 'https://chakra-ui.com/docs/{version}/',
                'fallback': 'https://chakra-ui.com/getting-started',
                'version_format': lambda v: {'version': v}
            },
            'tailwindcss': {
                'pattern': 'https://v{version}.tailwindcss.com/docs',
                'fallback': 'https://tailwindcss.com/docs',
                'version_format': lambda v: {'version': v}
            },
            'bootstrap': {
                'pattern': 'https://getbootstrap.com/docs/{version}/',
                'fallback': 'https://getbootstrap.com/docs/5.3/getting-started/introduction/',
                'version_format': lambda v: {'version': v}
            },
            'bulma': {
                'pattern': 'https://bulma.io/documentation/v{version}/',
                'fallback': 'https://bulma.io/documentation/',
                'version_format': lambda v: {'version': v}
            },
            
            # API Documentation
            'swagger': {
                'pattern': 'https://swagger.io/docs/specification/{version}/',
                'fallback': 'https://swagger.io/docs/',
                'version_format': lambda v: {'version': v}
            },
            'openapi': {
                'pattern': 'https://spec.openapis.org/oas/{version}',
                'fallback': 'https://www.openapis.org/what-is-openapi',
                'version_format': lambda v: {'version': v}
            },
            'graphql': {
                'pattern': 'https://graphql.org/learn/{version}/',
                'fallback': 'https://graphql.org/learn/',
                'version_format': lambda v: {'version': v}
            },
            'postman': {
                'pattern': 'https://learning.postman.com/docs/v{version}/',
                'fallback': 'https://learning.postman.com/docs/getting-started/introduction/',
                'version_format': lambda v: {'version': v}
            },
            
            # Authentication & Authorization
            'passport': {
                'pattern': 'https://www.passportjs.org/docs/{version}/',
                'fallback': 'https://www.passportjs.org/docs/',
                'version_format': lambda v: {'version': v}
            },
            'auth0': {
                'pattern': 'https://auth0.com/docs/v{version}/',
                'fallback': 'https://auth0.com/docs/',
                'version_format': lambda v: {'version': v}
            },
            'oauth2': {
                'pattern': 'https://oauth.net/{version}/',
                'fallback': 'https://oauth.net/2/',
                'version_format': lambda v: {'version': v}
            },
            'jwt': {
                'pattern': 'https://jwt.io/introduction/{version}',
                'fallback': 'https://jwt.io/introduction',
                'version_format': lambda v: {'version': v}
            },
            'keycloak': {
                'pattern': 'https://www.keycloak.org/docs/{version}/',
                'fallback': 'https://www.keycloak.org/documentation',
                'version_format': lambda v: {'version': v}
            },
            'okta': {
                'pattern': 'https://developer.okta.com/docs/reference/{version}/',
                'fallback': 'https://developer.okta.com/docs/guides/',
                'version_format': lambda v: {'version': v}
            },
            
            # Game Development
            'unity': {
                'pattern': 'https://docs.unity3d.com/{version}/Documentation/',
                'fallback': 'https://docs.unity3d.com/Manual/',
                'version_format': lambda v: {'version': v}
            },
            'unreal': {
                'pattern': 'https://docs.unrealengine.com/{version}/',
                'fallback': 'https://docs.unrealengine.com/5.0/',
                'version_format': lambda v: {'version': v}
            },
            'godot': {
                'pattern': 'https://docs.godotengine.org/{version}/',
                'fallback': 'https://docs.godotengine.org/en/stable/',
                'version_format': lambda v: {'version': v}
            },
            'phaser': {
                'pattern': 'https://photonstorm.github.io/phaser{version}-docs/',
                'fallback': 'https://phaser.io/learn',
                'version_format': lambda v: {'version': v}
            },
            'threejs': {
                'pattern': 'https://threejs.org/docs/#manual/en/{version}/',
                'fallback': 'https://threejs.org/docs/',
                'version_format': lambda v: {'version': v}
            },
            
            # Graphics & Visualization
            'd3': {
                'pattern': 'https://d3js.org/d3-{version}',
                'fallback': 'https://d3js.org/',
                'version_format': lambda v: {'version': v}
            },
            'chart.js': {
                'pattern': 'https://www.chartjs.org/docs/{version}/',
                'fallback': 'https://www.chartjs.org/docs/latest/',
                'version_format': lambda v: {'version': v}
            },
            'plotly': {
                'pattern': 'https://plotly.com/javascript-{version}/',
                'fallback': 'https://plotly.com/javascript/',
                'version_format': lambda v: {'version': v}
            },
            'webgl': {
                'pattern': 'https://www.khronos.org/registry/webgl/specs/{version}/',
                'fallback': 'https://www.khronos.org/webgl/',
                'version_format': lambda v: {'version': v}
            },
            'canvas-api': {
                'pattern': 'https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API/{version}',
                'fallback': 'https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API',
                'version_format': lambda v: {'version': v}
            },
            'svg': {
                'pattern': 'https://developer.mozilla.org/en-US/docs/Web/SVG/{version}',
                'fallback': 'https://developer.mozilla.org/en-US/docs/Web/SVG',
                'version_format': lambda v: {'version': v}
            },
            
            # Build Tools
            'webpack': {
                'pattern': 'https://webpack.js.org/concepts/{version}/',
                'fallback': 'https://webpack.js.org/concepts/',
                'version_format': lambda v: {'version': v}
            },
            'vite': {
                'pattern': 'https://vitejs.dev/guide/{version}/',
                'fallback': 'https://vitejs.dev/guide/',
                'version_format': lambda v: {'version': v}
            },
            'rollup': {
                'pattern': 'https://rollupjs.org/guide/en/#{version}',
                'fallback': 'https://rollupjs.org/guide/en/',
                'version_format': lambda v: {'version': v}
            },
            'parcel': {
                'pattern': 'https://parceljs.org/docs/{version}/',
                'fallback': 'https://parceljs.org/getting-started/webapp/',
                'version_format': lambda v: {'version': v}
            },
            'esbuild': {
                'pattern': 'https://esbuild.github.io/api/{version}/',
                'fallback': 'https://esbuild.github.io/',
                'version_format': lambda v: {'version': v}
            },
            'babel': {
                'pattern': 'https://babeljs.io/docs/en/{version}',
                'fallback': 'https://babeljs.io/docs/en/',
                'version_format': lambda v: {'version': v}
            },
            
            # Package Managers
            'npm': {
                'pattern': 'https://docs.npmjs.com/v{version}/',
                'fallback': 'https://docs.npmjs.com/',
                'version_format': lambda v: {'version': v}
            },
            'yarn': {
                'pattern': 'https://yarnpkg.com/getting-started/{version}',
                'fallback': 'https://yarnpkg.com/getting-started',
                'version_format': lambda v: {'version': v}
            },
            'pnpm': {
                'pattern': 'https://pnpm.io/v{version}/',
                'fallback': 'https://pnpm.io/',
                'version_format': lambda v: {'version': v}
            },
            'pip': {
                'pattern': 'https://pip.pypa.io/en/{version}/',
                'fallback': 'https://pip.pypa.io/en/stable/',
                'version_format': lambda v: {'version': v}
            },
            'poetry': {
                'pattern': 'https://python-poetry.org/docs/{version}/',
                'fallback': 'https://python-poetry.org/docs/',
                'version_format': lambda v: {'version': v}
            },
            'cargo': {
                'pattern': 'https://doc.rust-lang.org/cargo/{version}/',
                'fallback': 'https://doc.rust-lang.org/cargo/guide/',
                'version_format': lambda v: {'version': v}
            },
            
            # Code Editors & IDEs
            'vscode': {
                'pattern': 'https://code.visualstudio.com/docs/{version}/',
                'fallback': 'https://code.visualstudio.com/docs',
                'version_format': lambda v: {'version': v}
            },
            'intellij': {
                'pattern': 'https://www.jetbrains.com/help/idea/{version}/',
                'fallback': 'https://www.jetbrains.com/help/idea/getting-started.html',
                'version_format': lambda v: {'version': v}
            },
            'pycharm': {
                'pattern': 'https://www.jetbrains.com/help/pycharm/{version}/',
                'fallback': 'https://www.jetbrains.com/help/pycharm/getting-started.html',
                'version_format': lambda v: {'version': v}
            },
            'webstorm': {
                'pattern': 'https://www.jetbrains.com/help/webstorm/{version}/',
                'fallback': 'https://www.jetbrains.com/help/webstorm/getting-started.html',
                'version_format': lambda v: {'version': v}
            },
            'eclipse': {
                'pattern': 'https://help.eclipse.org/{version}/',
                'fallback': 'https://help.eclipse.org/',
                'version_format': lambda v: {'version': v}
            },
            'sublime': {
                'pattern': 'https://www.sublimetext.com/docs/{version}/',
                'fallback': 'https://www.sublimetext.com/docs/',
                'version_format': lambda v: {'version': v}
            },
            'atom': {
                'pattern': 'https://flight-manual.atom.io/{version}/',
                'fallback': 'https://flight-manual.atom.io/',
                'version_format': lambda v: {'version': v}
            },
            'vim': {
                'pattern': 'https://vimhelp.org/{version}.txt.html',
                'fallback': 'https://vimhelp.org/',
                'version_format': lambda v: {'version': v}
            },
            'emacs': {
                'pattern': 'https://www.gnu.org/software/emacs/manual/{version}/',
                'fallback': 'https://www.gnu.org/software/emacs/manual/html_node/emacs/',
                'version_format': lambda v: {'version': v}
            },
            'neovim': {
                'pattern': 'https://neovim.io/doc/{version}/',
                'fallback': 'https://neovim.io/doc/user/',
                'version_format': lambda v: {'version': v}
            },
            
            # CI/CD Platforms
            'github-actions': {
                'pattern': 'https://docs.github.com/en/actions/{version}',
                'fallback': 'https://docs.github.com/en/actions',
                'version_format': lambda v: {'version': v}
            },
            'gitlab-ci': {
                'pattern': 'https://docs.gitlab.com/ee/ci/{version}/',
                'fallback': 'https://docs.gitlab.com/ee/ci/',
                'version_format': lambda v: {'version': v}
            },
            'circleci': {
                'pattern': 'https://circleci.com/docs/{version}/',
                'fallback': 'https://circleci.com/docs/',
                'version_format': lambda v: {'version': v}
            },
            'travis-ci': {
                'pattern': 'https://docs.travis-ci.com/{version}/',
                'fallback': 'https://docs.travis-ci.com/',
                'version_format': lambda v: {'version': v}
            },
            'jenkins': {
                'pattern': 'https://www.jenkins.io/doc/book/{version}/',
                'fallback': 'https://www.jenkins.io/doc/',
                'version_format': lambda v: {'version': v}
            },
            
            # Container Technologies
            'docker': {
                'pattern': 'https://docs.docker.com/engine/{version}/',
                'fallback': 'https://docs.docker.com/get-started/',
                'version_format': lambda v: {'version': v}
            },
            'kubernetes': {
                'pattern': 'https://kubernetes.io/docs/reference/generated/kubernetes-api/{version}/',
                'fallback': 'https://kubernetes.io/docs/home/',
                'version_format': lambda v: {'version': v}
            },
            'podman': {
                'pattern': 'https://docs.podman.io/en/{version}/',
                'fallback': 'https://docs.podman.io/en/latest/',
                'version_format': lambda v: {'version': v}
            },
            'containerd': {
                'pattern': 'https://containerd.io/docs/{version}/',
                'fallback': 'https://containerd.io/docs/',
                'version_format': lambda v: {'version': v}
            },
            'helm': {
                'pattern': 'https://helm.sh/docs/{version}/',
                'fallback': 'https://helm.sh/docs/',
                'version_format': lambda v: {'version': v}
            },
            
            # Cloud Platforms
            'aws': {
                'pattern': 'https://docs.aws.amazon.com/{version}/',
                'fallback': 'https://docs.aws.amazon.com/',
                'version_format': lambda v: {'version': v}
            },
            'gcp': {
                'pattern': 'https://cloud.google.com/docs/{version}',
                'fallback': 'https://cloud.google.com/docs',
                'version_format': lambda v: {'version': v}
            },
            'azure': {
                'pattern': 'https://learn.microsoft.com/en-us/azure/{version}',
                'fallback': 'https://learn.microsoft.com/en-us/azure/',
                'version_format': lambda v: {'version': v}
            },
            'digitalocean': {
                'pattern': 'https://docs.digitalocean.com/{version}/',
                'fallback': 'https://docs.digitalocean.com/',
                'version_format': lambda v: {'version': v}
            },
            'heroku': {
                'pattern': 'https://devcenter.heroku.com/{version}',
                'fallback': 'https://devcenter.heroku.com/',
                'version_format': lambda v: {'version': v}
            },
            
            # Serverless Frameworks
            'serverless': {
                'pattern': 'https://www.serverless.com/framework/docs/{version}/',
                'fallback': 'https://www.serverless.com/framework/docs/',
                'version_format': lambda v: {'version': v}
            },
            'aws-sam': {
                'pattern': 'https://docs.aws.amazon.com/serverless-application-model/{version}/',
                'fallback': 'https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/',
                'version_format': lambda v: {'version': v}
            },
            'netlify': {
                'pattern': 'https://docs.netlify.com/{version}/',
                'fallback': 'https://docs.netlify.com/',
                'version_format': lambda v: {'version': v}
            },
            'vercel': {
                'pattern': 'https://vercel.com/docs/{version}',
                'fallback': 'https://vercel.com/docs',
                'version_format': lambda v: {'version': v}
            },
            'firebase': {
                'pattern': 'https://firebase.google.com/docs/{version}',
                'fallback': 'https://firebase.google.com/docs',
                'version_format': lambda v: {'version': v}
            },
            
            # Monitoring & Observability
            'prometheus': {
                'pattern': 'https://prometheus.io/docs/prometheus/{version}/',
                'fallback': 'https://prometheus.io/docs/introduction/overview/',
                'version_format': lambda v: {'version': v}
            },
            'grafana': {
                'pattern': 'https://grafana.com/docs/grafana/{version}/',
                'fallback': 'https://grafana.com/docs/grafana/latest/',
                'version_format': lambda v: {'version': v}
            },
            'datadog': {
                'pattern': 'https://docs.datadoghq.com/{version}/',
                'fallback': 'https://docs.datadoghq.com/',
                'version_format': lambda v: {'version': v}
            },
            'newrelic': {
                'pattern': 'https://docs.newrelic.com/{version}',
                'fallback': 'https://docs.newrelic.com/',
                'version_format': lambda v: {'version': v}
            },
            'elastic': {
                'pattern': 'https://www.elastic.co/guide/en/elasticsearch/reference/{version}/',
                'fallback': 'https://www.elastic.co/guide/en/elasticsearch/reference/current/',
                'version_format': lambda v: {'version': v}
            },
            'kibana': {
                'pattern': 'https://www.elastic.co/guide/en/kibana/reference/{version}/',
                'fallback': 'https://www.elastic.co/guide/en/kibana/current/',
                'version_format': lambda v: {'version': v}
            },
            'logstash': {
                'pattern': 'https://www.elastic.co/guide/en/logstash/{version}/',
                'fallback': 'https://www.elastic.co/guide/en/logstash/current/',
                'version_format': lambda v: {'version': v}
            },
            'splunk': {
                'pattern': 'https://docs.splunk.com/{version}',
                'fallback': 'https://docs.splunk.com/',
                'version_format': lambda v: {'version': v}
            },
            'jaeger': {
                'pattern': 'https://www.jaegertracing.io/docs/{version}/',
                'fallback': 'https://www.jaegertracing.io/docs/latest/',
                'version_format': lambda v: {'version': v}
            },
            'zipkin': {
                'pattern': 'https://zipkin.io/pages/{version}.html',
                'fallback': 'https://zipkin.io/',
                'version_format': lambda v: {'version': v}
            },
            
            # Security Tools
            'vault': {
                'pattern': 'https://developer.hashicorp.com/vault/docs/{version}',
                'fallback': 'https://developer.hashicorp.com/vault/docs',
                'version_format': lambda v: {'version': v}
            },
            'owasp': {
                'pattern': 'https://owasp.org/www-project-{version}',
                'fallback': 'https://owasp.org/projects/',
                'version_format': lambda v: {'version': v}
            },
            'snyk': {
                'pattern': 'https://docs.snyk.io/{version}',
                'fallback': 'https://docs.snyk.io/',
                'version_format': lambda v: {'version': v}
            },
            'sonarqube': {
                'pattern': 'https://docs.sonarqube.org/{version}/',
                'fallback': 'https://docs.sonarqube.org/latest/',
                'version_format': lambda v: {'version': v}
            },
            'burpsuite': {
                'pattern': 'https://portswigger.net/burp/{version}',
                'fallback': 'https://portswigger.net/burp/documentation',
                'version_format': lambda v: {'version': v}
            },
            
            # Messaging Systems
            'rabbitmq': {
                'pattern': 'https://www.rabbitmq.com/docs/v{version}',
                'fallback': 'https://www.rabbitmq.com/documentation.html',
                'version_format': lambda v: {'version': v}
            },
            'kafka': {
                'pattern': 'https://kafka.apache.org/{version}/documentation/',
                'fallback': 'https://kafka.apache.org/documentation/',
                'version_format': lambda v: {'version': v}
            },
            'redis': {
                'pattern': 'https://redis.io/docs/{version}/',
                'fallback': 'https://redis.io/docs/',
                'version_format': lambda v: {'version': v}
            },
            'activemq': {
                'pattern': 'https://activemq.apache.org/components/classic/documentation/{version}',
                'fallback': 'https://activemq.apache.org/components/classic/documentation',
                'version_format': lambda v: {'version': v}
            },
            'zeromq': {
                'pattern': 'https://zguide.zeromq.org/{version}/',
                'fallback': 'https://zguide.zeromq.org/',
                'version_format': lambda v: {'version': v}
            },
            
            # Mobile Development
            'android': {
                'pattern': 'https://developer.android.com/guide/{version}',
                'fallback': 'https://developer.android.com/guide',
                'version_format': lambda v: {'version': v}
            },
            'ios': {
                'pattern': 'https://developer.apple.com/documentation/ios/{version}',
                'fallback': 'https://developer.apple.com/documentation/ios',
                'version_format': lambda v: {'version': v}
            },
            'swift': {
                'pattern': 'https://docs.swift.org/{version}/',
                'fallback': 'https://docs.swift.org/',
                'version_format': lambda v: {'version': v}
            },
            'kotlin': {
                'pattern': 'https://kotlinlang.org/docs/{version}/',
                'fallback': 'https://kotlinlang.org/docs/home.html',
                'version_format': lambda v: {'version': v}
            },
            'xamarin': {
                'pattern': 'https://docs.microsoft.com/en-us/xamarin/{version}',
                'fallback': 'https://docs.microsoft.com/en-us/xamarin/',
                'version_format': lambda v: {'version': v}
            },
            
            # Cross-Platform Frameworks
            'react-native': {
                'pattern': 'https://reactnative.dev/docs/{version}/',
                'fallback': 'https://reactnative.dev/docs/getting-started',
                'version_format': lambda v: {'version': v}
            },
            'flutter': {
                'pattern': 'https://docs.flutter.dev/{version}',
                'fallback': 'https://docs.flutter.dev/',
                'version_format': lambda v: {'version': v}
            },
            'ionic': {
                'pattern': 'https://ionicframework.com/docs/{version}/',
                'fallback': 'https://ionicframework.com/docs/',
                'version_format': lambda v: {'version': v}
            },
            'capacitor': {
                'pattern': 'https://capacitorjs.com/docs/{version}/',
                'fallback': 'https://capacitorjs.com/docs/',
                'version_format': lambda v: {'version': v}
            },
            'electron': {
                'pattern': 'https://www.electronjs.org/docs/v{version}/',
                'fallback': 'https://www.electronjs.org/docs/latest/',
                'version_format': lambda v: {'version': v}
            },
            
            # Data Science & Machine Learning
            'pandas': {
                'pattern': 'https://pandas.pydata.org/pandas-docs/version/{version}/',
                'fallback': 'https://pandas.pydata.org/docs/',
                'version_format': lambda v: {'version': v}
            },
            'numpy': {
                'pattern': 'https://numpy.org/doc/{version}/',
                'fallback': 'https://numpy.org/doc/stable/',
                'version_format': lambda v: {'version': v}
            },
            'scipy': {
                'pattern': 'https://docs.scipy.org/doc/{version}/',
                'fallback': 'https://docs.scipy.org/doc/scipy/',
                'version_format': lambda v: {'version': v}
            },
            'scikit-learn': {
                'pattern': 'https://scikit-learn.org/{version}/',
                'fallback': 'https://scikit-learn.org/stable/',
                'version_format': lambda v: {'version': v}
            },
            'tensorflow': {
                'pattern': 'https://www.tensorflow.org/versions/{version}/',
                'fallback': 'https://www.tensorflow.org/guide/',
                'version_format': lambda v: {'version': v}
            },
            'pytorch': {
                'pattern': 'https://pytorch.org/docs/{version}/',
                'fallback': 'https://pytorch.org/docs/stable/',
                'version_format': lambda v: {'version': v}
            },
            'keras': {
                'pattern': 'https://keras.io/{version}/',
                'fallback': 'https://keras.io/',
                'version_format': lambda v: {'version': v}
            },
            'matplotlib': {
                'pattern': 'https://matplotlib.org/stable/{version}/',
                'fallback': 'https://matplotlib.org/stable/',
                'version_format': lambda v: {'version': v}
            },
            'seaborn': {
                'pattern': 'https://seaborn.pydata.org/{version}/',
                'fallback': 'https://seaborn.pydata.org/',
                'version_format': lambda v: {'version': v}
            },
            'huggingface': {
                'pattern': 'https://huggingface.co/docs/{version}',
                'fallback': 'https://huggingface.co/docs',
                'version_format': lambda v: {'version': v}
            },
            
            # Databases & ORMs
            'postgresql': {
                'pattern': 'https://www.postgresql.org/docs/{version}/',
                'fallback': 'https://www.postgresql.org/docs/current/',
                'version_format': lambda v: {'version': v}
            },
            'mysql': {
                'pattern': 'https://dev.mysql.com/doc/refman/{version}/',
                'fallback': 'https://dev.mysql.com/doc/',
                'version_format': lambda v: {'version': v}
            },
            'mongodb': {
                'pattern': 'https://docs.mongodb.com/v{version}/',
                'fallback': 'https://docs.mongodb.com/manual/',
                'version_format': lambda v: {'version': v}
            },
            'cassandra': {
                'pattern': 'https://cassandra.apache.org/doc/{version}/',
                'fallback': 'https://cassandra.apache.org/doc/latest/',
                'version_format': lambda v: {'version': v}
            },
            'couchdb': {
                'pattern': 'https://docs.couchdb.org/{version}/',
                'fallback': 'https://docs.couchdb.org/',
                'version_format': lambda v: {'version': v}
            },
            'sequelize': {
                'pattern': 'https://sequelize.org/v{version}/',
                'fallback': 'https://sequelize.org/',
                'version_format': lambda v: {'version': v}
            },
            'prisma': {
                'pattern': 'https://www.prisma.io/docs/{version}',
                'fallback': 'https://www.prisma.io/docs',
                'version_format': lambda v: {'version': v}
            },
            'typeorm': {
                'pattern': 'https://typeorm.io/#{version}',
                'fallback': 'https://typeorm.io/',
                'version_format': lambda v: {'version': v}
            },
            'sqlalchemy': {
                'pattern': 'https://docs.sqlalchemy.org/{version}/',
                'fallback': 'https://docs.sqlalchemy.org/en/latest/',
                'version_format': lambda v: {'version': v}
            },
            'hibernate': {
                'pattern': 'https://docs.jboss.org/hibernate/orm/{version}/userguide/html_single/',
                'fallback': 'https://hibernate.org/orm/documentation/',
                'version_format': lambda v: {'version': v}
            },
            
            # Testing Frameworks
            'jest': {
                'pattern': 'https://jestjs.io/docs/{version}/',
                'fallback': 'https://jestjs.io/docs/getting-started',
                'version_format': lambda v: {'version': v}
            },
            'mocha': {
                'pattern': 'https://mochajs.org/api/{version}/',
                'fallback': 'https://mochajs.org/',
                'version_format': lambda v: {'version': v}
            },
            'pytest': {
                'pattern': 'https://docs.pytest.org/en/{version}/',
                'fallback': 'https://docs.pytest.org/en/stable/',
                'version_format': lambda v: {'version': v}
            },
            'junit': {
                'pattern': 'https://junit.org/junit{version}/docs/current/user-guide/',
                'fallback': 'https://junit.org/junit5/docs/current/user-guide/',
                'version_format': lambda v: {'version': v}
            },
            'testng': {
                'pattern': 'https://testng.org/doc/{version}/',
                'fallback': 'https://testng.org/doc/',
                'version_format': lambda v: {'version': v}
            },
            
            # Test Automation
            'selenium': {
                'pattern': 'https://www.selenium.dev/documentation/{version}/',
                'fallback': 'https://www.selenium.dev/documentation/',
                'version_format': lambda v: {'version': v}
            },
            'cypress': {
                'pattern': 'https://docs.cypress.io/v{version}/',
                'fallback': 'https://docs.cypress.io/',
                'version_format': lambda v: {'version': v}
            },
            'playwright': {
                'pattern': 'https://playwright.dev/docs/v{version}/',
                'fallback': 'https://playwright.dev/docs/intro',
                'version_format': lambda v: {'version': v}
            },
            'puppeteer': {
                'pattern': 'https://pptr.dev/v{version}/',
                'fallback': 'https://pptr.dev/',
                'version_format': lambda v: {'version': v}
            },
            'appium': {
                'pattern': 'https://appium.io/docs/{version}/',
                'fallback': 'https://appium.io/docs/en/2.0/',
                'version_format': lambda v: {'version': v}
            },
            
            # API Development
            'express': {
                'pattern': 'https://expressjs.com/{version}/',
                'fallback': 'https://expressjs.com/',
                'version_format': lambda v: {'version': v}
            },
            'fastapi': {
                'pattern': 'https://fastapi.tiangolo.com/{version}/',
                'fallback': 'https://fastapi.tiangolo.com/',
                'version_format': lambda v: {'version': v}
            },
            'django-rest': {
                'pattern': 'https://www.django-rest-framework.org/{version}/',
                'fallback': 'https://www.django-rest-framework.org/',
                'version_format': lambda v: {'version': v}
            },
            'spring-boot': {
                'pattern': 'https://docs.spring.io/spring-boot/docs/{version}/reference/html/',
                'fallback': 'https://docs.spring.io/spring-boot/docs/current/reference/html/',
                'version_format': lambda v: {'version': v}
            },
            'graphql': {
                'pattern': 'https://graphql.org/learn/{version}/',
                'fallback': 'https://graphql.org/learn/',
                'version_format': lambda v: {'version': v}
            },
            
            # API Documentation
            'swagger': {
                'pattern': 'https://swagger.io/docs/{version}/',
                'fallback': 'https://swagger.io/docs/',
                'version_format': lambda v: {'version': v}
            },
            'openapi': {
                'pattern': 'https://spec.openapis.org/oas/{version}',
                'fallback': 'https://spec.openapis.org/',
                'version_format': lambda v: {'version': v}
            },
            'postman': {
                'pattern': 'https://learning.postman.com/docs/{version}/',
                'fallback': 'https://learning.postman.com/docs/',
                'version_format': lambda v: {'version': v}
            },
            'insomnia': {
                'pattern': 'https://docs.insomnia.rest/{version}/',
                'fallback': 'https://docs.insomnia.rest/',
                'version_format': lambda v: {'version': v}
            },
            'apiblueprint': {
                'pattern': 'https://apiblueprint.org/documentation/{version}/',
                'fallback': 'https://apiblueprint.org/documentation/',
                'version_format': lambda v: {'version': v}
            },
            
            # Authentication & Authorization
            'passport': {
                'pattern': 'https://www.passportjs.org/docs/{version}/',
                'fallback': 'https://www.passportjs.org/docs/',
                'version_format': lambda v: {'version': v}
            },
            'auth0': {
                'pattern': 'https://auth0.com/docs/{version}/',
                'fallback': 'https://auth0.com/docs/',
                'version_format': lambda v: {'version': v}
            },
            'oauth2': {
                'pattern': 'https://oauth.net/{version}/',
                'fallback': 'https://oauth.net/2/',
                'version_format': lambda v: {'version': v}
            },
            'jwt': {
                'pattern': 'https://jwt.io/introduction/{version}',
                'fallback': 'https://jwt.io/introduction',
                'version_format': lambda v: {'version': v}
            },
            'keycloak': {
                'pattern': 'https://www.keycloak.org/docs/{version}/',
                'fallback': 'https://www.keycloak.org/documentation',
                'version_format': lambda v: {'version': v}
            },
            'okta': {
                'pattern': 'https://developer.okta.com/docs/{version}/',
                'fallback': 'https://developer.okta.com/docs/guides/',
                'version_format': lambda v: {'version': v}
            },
            'cognito': {
                'pattern': 'https://docs.aws.amazon.com/cognito/{version}/',
                'fallback': 'https://docs.aws.amazon.com/cognito/latest/developerguide/',
                'version_format': lambda v: {'version': v}
            },
            'firebase-auth': {
                'pattern': 'https://firebase.google.com/docs/auth/{version}',
                'fallback': 'https://firebase.google.com/docs/auth',
                'version_format': lambda v: {'version': v}
            },
            'spring-security': {
                'pattern': 'https://docs.spring.io/spring-security/reference/{version}/',
                'fallback': 'https://docs.spring.io/spring-security/reference/current/',
                'version_format': lambda v: {'version': v}
            },
            'django-auth': {
                'pattern': 'https://docs.djangoproject.com/en/{version}/topics/auth/',
                'fallback': 'https://docs.djangoproject.com/en/stable/topics/auth/',
                'version_format': lambda v: {'version': v}
            },
            
            # Web Frameworks
            'django': {
                'pattern': 'https://docs.djangoproject.com/en/{version}/',
                'fallback': 'https://docs.djangoproject.com/en/stable/',
                'version_format': lambda v: {'version': v}
            },
            'flask': {
                'pattern': 'https://flask.palletsprojects.com/en/{version}/',
                'fallback': 'https://flask.palletsprojects.com/en/latest/',
                'version_format': lambda v: {'version': v}
            },
            'rails': {
                'pattern': 'https://guides.rubyonrails.org/v{version}/',
                'fallback': 'https://guides.rubyonrails.org/',
                'version_format': lambda v: {'version': v}
            },
            'laravel': {
                'pattern': 'https://laravel.com/docs/{version}',
                'fallback': 'https://laravel.com/docs/',
                'version_format': lambda v: {'version': v}
            },
            'asp-net': {
                'pattern': 'https://learn.microsoft.com/en-us/aspnet/core/{version}/',
                'fallback': 'https://learn.microsoft.com/en-us/aspnet/core/',
                'version_format': lambda v: {'version': v}
            },
            
            # Static Site Generators
            'gatsby': {
                'pattern': 'https://www.gatsbyjs.com/docs/{version}/',
                'fallback': 'https://www.gatsbyjs.com/docs/',
                'version_format': lambda v: {'version': v}
            },
            'nextjs': {
                'pattern': 'https://nextjs.org/docs/{version}',
                'fallback': 'https://nextjs.org/docs',
                'version_format': lambda v: {'version': v}
            },
            'nuxt': {
                'pattern': 'https://nuxtjs.org/docs/{version}/',
                'fallback': 'https://nuxtjs.org/docs/',
                'version_format': lambda v: {'version': v}
            },
            'hugo': {
                'pattern': 'https://gohugo.io/documentation/{version}/',
                'fallback': 'https://gohugo.io/documentation/',
                'version_format': lambda v: {'version': v}
            },
            'jekyll': {
                'pattern': 'https://jekyllrb.com/docs/{version}/',
                'fallback': 'https://jekyllrb.com/docs/',
                'version_format': lambda v: {'version': v}
            }
        }
        
        # Normalize package name and version
        package_lower = package.lower()
        version = version.lower().strip()
        
        # Handle known packages
        if package_lower in docs_patterns:
            config = docs_patterns[package_lower]
            
            try:
                # Format version according to package rules
                version_params = config['version_format'](version)
                url = config['pattern'].format(**version_params)
                
                # Verify URL exists (optional HEAD request)
                try:
                    response = self.session.head(url, timeout=5)
                    if response.status_code == 404:
                        url = config['fallback']
                except Exception:
                    url = config['fallback']
                
                return url
                
            except Exception as e:
                logger.warning(f"Error formatting docs URL for {package}: {str(e)}")
                return config['fallback']
        
        # Try package registry URLs
        registry_patterns = {
            'npm': 'https://www.npmjs.com/package/{package}/v/{version}',
            'pypi': 'https://pypi.org/project/{package}/{version}',
            'maven': 'https://mvnrepository.com/artifact/{group}/{package}/{version}',
            'nuget': 'https://www.nuget.org/packages/{package}/{version}',
            'rubygems': 'https://rubygems.org/gems/{package}/versions/{version}',
            'crates': 'https://crates.io/crates/{package}/{version}'
        }
        
        # Check if package exists in common registries
        for registry, pattern in registry_patterns.items():
            try:
                url = pattern.format(package=package_lower, version=version, group=package_lower.split(':')[0])
                response = self.session.head(url, timeout=5)
                if response.status_code == 200:
                    return url
            except Exception:
                continue
        
        # Default to searching package documentation
        search_url = f"https://www.google.com/search?q={urllib.parse.quote(f'{package} {version} documentation')}"
        return search_url
        # Ensure download directory exists
        self.download_dir.mkdir(exist_ok=True)
        
        file_path = self.download_dir / filename
        
        # Download the file
        try:
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
            'angular': f"https://v{version}.angular.io/",
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
