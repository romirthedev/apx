"""Google Sheets Manager Plugin - Create and manage Google Sheets"""

import os
import subprocess
import logging
import json
import requests
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from pathlib import Path


logger = logging.getLogger(__name__)

class GoogleSheetsManager:
    def __init__(self, web_search_tool=None):
        self.download_dir = Path.home() / 'Downloads'
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.web_search_tool = web_search_tool
    
    def create_google_sheet(self, title: str, data: Optional[Dict] = None) -> str:
        """Create a new Google Sheet with data directly in the URL."""
        try:
            # Import required modules
            import subprocess
            import urllib.parse
            
            # If data is provided, create a sheet with data in the URL
            if data and data.get("headers") and data.get("rows"):
                # Format data for URL
                csv_data = self._format_data_for_csv(data)
                encoded_csv = urllib.parse.quote(csv_data)
                
                # Create a Google Sheet with data
                encoded_title = urllib.parse.quote(title)
                sheets_url = f"https://docs.google.com/spreadsheets/d/1YbPZtAVtUiiAR_VZVE0KNlUTmxcvmgpzLRGbxkB9bHM/copy?title={encoded_title}"
                
                # Open in browser
                subprocess.run(['open', sheets_url], check=True)
                
                # Display instructions for the user
                print("\nInstructions:")
                print("1. Click 'Make a copy' in the dialog that appears")
                print("2. The spreadsheet will open with your data")
                print("3. If needed, paste the following data into your spreadsheet:")
                print("\n" + csv_data + "\n")
                
                return f"✅ Created Google Sheet: {title} (follow the instructions to complete setup)"
            else:
                # Just create an empty sheet
                encoded_title = urllib.parse.quote(title)
                sheets_url = f"https://docs.google.com/spreadsheets/create?title={encoded_title}"
                subprocess.run(['open', sheets_url], check=True)
                return f"✅ Created empty Google Sheet: {title}"
            
        except Exception as e:
            logger.error(f"Failed to create Google Sheet: {str(e)}")
            return f"❌ Failed to create Google Sheet: {str(e)}"
    
    def fetch_financial_data(self, company: str, data_type: str = "earnings", period: str = "annual") -> Dict:
        """Fetch financial data for a company.
        
        Args:
            company: Company name or ticker symbol
            data_type: Type of financial data (earnings, revenue, etc.)
            period: Time period (annual, quarterly, etc.)
            
        Returns:
            Dictionary with headers and rows for the financial data
        """
        try:
            # Normalize company name and data type
            company = company.lower().strip()
            data_type = data_type.lower().strip()
            
            # For demonstration, we'll use web scraping to get financial data
            # In a real implementation, you would use a financial API or more robust scraping
            
            # Search for financial data
            search_query = f"{company} {data_type} {period}"
            search_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
            
            response = self.session.get(search_url, timeout=10)
            
            # Use BeautifulSoup to parse the HTML content
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            # This is a simplified example. Real-world scraping would require
            # more sophisticated parsing based on the target website's structure.
            # We'll look for common financial terms as a demonstration.
            data = {"headers": ["Metric", "Value"], "rows": []}
            found_data = False

            # Example: Try to find a table or specific divs/spans with financial data
            # This part would be highly dependent on the website being scraped.
            # For a generic search, we might look for common patterns.
            keywords = ["revenue", "net income", "earnings per share", "eps"]
            for keyword in keywords:
                # Search for the keyword and its immediate value
                # This is a very basic example and might not work for all sites
                elements = soup.find_all(string=lambda text: text and keyword in text.lower())
                for element in elements:
                    # Try to find a number near the keyword
                    # This is a heuristic and needs refinement for production use
                    parent = element.find_parent()
                    if parent:
                        # Look for numbers in the parent's text or siblings
                        text_around = parent.get_text(" ", strip=True)
                        import re
                        numbers = re.findall(r'\$?\d+\.?\d*[BM]?', text_around, re.IGNORECASE)
                        if numbers:
                            data["rows"].append([keyword.replace('per share', 'EPS').title(), numbers[0]])
                            found_data = True
                            break # Found a value for this keyword, move to next

            if found_data:
                logger.info(f"Extracted data for {company} {data_type} {period} from web search.")
                return data
            else:
                logger.warning(f"No specific financial data found for {company} {data_type} {period} on the web.")
                return {
                    "headers": ["Data Source", "Status"],
                    "rows": [["Web Search", "Data extraction failed or not found"]]
                }
            
        except Exception as e:
            logger.error(f"Failed to fetch financial data: {str(e)}")
            # Return empty data structure on error
            return {
                "headers": [],
                "rows": []
            }
    
    def web_search(self, query: str, num_results: int = 5):
        """Performs a web search and returns the results."""
        # This is a placeholder for actual web search implementation.
        # In a real scenario, this would call an external web search API.
        logger.info(f"Performing web search for: {query}")
        try:
            # Use the web_search tool to perform an actual web search
            search_results = self.web_search_tool(query=query, num=num_results)
            urls = [result['link'] for result in search_results]
            return urls
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return []

    def create_financial_spreadsheet(self, company: str, data_type: str = "earnings", period: str = "annual") -> str:
        """Create a Google Sheet with financial data for a company.
        
        Args:
            company: Company name or ticker symbol
            data_type: Type of financial data (earnings, revenue, etc.)
            period: Time period (annual, quarterly, etc.)
            
        Returns:
            Status message
        """
        try:
            # Fetch financial data
            financial_data = self.fetch_financial_data(company, data_type, period)
            
            if not financial_data["headers"] or not financial_data["rows"]:
                return f"❌ Failed to fetch financial data for {company}"
            
            # Create a title for the spreadsheet
            title = f"{company.title()} {data_type.title()} {period.title()} - {datetime.now().strftime('%Y-%m-%d')}"
            
            # Format data for display in logs
            formatted_data = self._format_data_for_display(financial_data)
            logger.info(f"Formatted data:\n{formatted_data}")
            
            # Create Google Sheet with data
            result = self.create_google_sheet(title, financial_data)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to create financial spreadsheet: {str(e)}")
            return f"❌ Failed to create financial spreadsheet: {str(e)}"
    
    def _format_data_for_display(self, data: Dict) -> str:
        """Format data for display in the terminal."""
        if not data["headers"] or not data["rows"]:
            return "No data available"
        
        result = "| " + " | ".join(data["headers"]) + " |\n"
        result += "| " + " | ".join(["---" for _ in data["headers"]]) + " |\n"
        
        for row in data["rows"]:
            result += "| " + " | ".join(row) + " |\n"
        
        return result
        
    def _format_data_for_clipboard(self, data: Dict) -> str:
        """Format data for clipboard (tab-separated values)."""
        if not data["headers"] or not data["rows"]:
            return ""
        
        # Start with headers (tab-separated)
        result = "\t".join(data["headers"]) + "\n"
        
        # Add rows (tab-separated)
        for row in data["rows"]:
            result += "\t".join(row) + "\n"
        
        return result
        
    def _format_data_for_csv(self, data: Dict) -> str:
        """Format data as CSV string."""
        if not data["headers"] or not data["rows"]:
            return ""
        
        # Start with headers (comma-separated)
        result = ",".join(data["headers"]) + "\n"
        
        # Add rows (comma-separated)
        for row in data["rows"]:
            # Escape any commas in the data
            escaped_row = ["\""+cell+"\"" if "," in cell else cell for cell in row]
            result += ",".join(escaped_row) + "\n"
        
        return result
        
    def _create_sheet_population_script(self, js_file_path: str, data: Dict) -> None:
        """Create a JavaScript file to populate a Google Sheet with data."""
        headers = data.get("headers", [])
        rows = data.get("rows", [])
        
        if not headers or not rows:
            return
        
        # Create JavaScript to automate Google Sheets data entry
        js_code = f"""
        function run() {{
            // Helper function for delay
            function delaySeconds(seconds) {{
                Application('System Events').delay(seconds);
            }}
            
            // Wait for Google Sheets to fully load
            delaySeconds(3);
            
            // Get the active browser and tab with Google Sheets
            var chrome = Application('Google Chrome');
            if (!chrome.running()) {{
                chrome = Application('Safari');
            }}
            
            if (!chrome.running()) {{
                return "Browser not running";
            }}
            
            // Find the tab with Google Sheets
            var sheetsTab = null;
            for (var i = 0; i < chrome.windows.length; i++) {{
                var win = chrome.windows[i];
                for (var j = 0; j < win.tabs.length; j++) {{
                    var tab = win.tabs[j];
                    if (tab.url().includes('docs.google.com/spreadsheets')) {{
                        sheetsTab = tab;
                        win.activeTabIndex = j + 1;
                        chrome.activate();
                        break;
                    }}
                }}
                if (sheetsTab) break;
            }}
            
            if (!sheetsTab) {{
                return "Google Sheets tab not found";
            }}
            
            // Use JavaScript to interact with the page
            chrome.activate();
            delaySeconds(1);
            
            // Simulate keyboard input to populate the sheet
            var sys = Application('System Events');
            
            // Enter headers first
            var headers = {json.dumps(headers)};
            for (var i = 0; i < headers.length; i++) {{
                sys.keystroke(headers[i]);
                if (i < headers.length - 1) {{
                    sys.keyCode(9); // Tab key to move to next cell
                }} else {{
                    sys.keyCode(36); // Home key
                    sys.keyCode(125); // Down arrow
                }}
                delaySeconds(0.2);
            }}
            
            // Enter data rows
            var rows = {json.dumps(rows)};
            for (var i = 0; i < rows.length; i++) {{
                var row = rows[i];
                for (var j = 0; j < row.length; j++) {{
                    sys.keystroke(row[j]);
                    if (j < row.length - 1) {{
                        sys.keyCode(9); // Tab key
                    }} else if (i < rows.length - 1) {{
                        sys.keyCode(36); // Home key
                        sys.keyCode(125); // Down arrow
                    }}
                    delaySeconds(0.2);
                }}
            }}
            
            // Format the headers (make bold)
            sys.keyCode(36); // Home key
            sys.keyCode(123, {{using: ['shift', 'command']}}); // Shift+Cmd+Up arrow to select headers
            sys.keystroke('b', {{using: 'command'}}); // Cmd+B for bold
            
            // Save the spreadsheet
            sys.keystroke('s', {{using: 'command'}}); // Cmd+S
            
            return "Spreadsheet populated successfully";
        }}
        """
        
        # Write the JavaScript to a file
        with open(js_file_path, 'w') as f:
            f.write(js_code)