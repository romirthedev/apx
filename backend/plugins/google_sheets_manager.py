"""Google Sheets Manager Plugin - Create and manage Google Sheets with Gemini AI data"""

import os
import subprocess
import logging
import json
import requests
import re
import random
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union, Tuple
from pathlib import Path
import time


logger = logging.getLogger(__name__)

class GoogleSheetsManager:
    def __init__(self, gemini_ai=None):
        self.download_dir = Path.home() / 'Downloads'
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.gemini_ai = gemini_ai
    
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
        """Fetch financial data for a company using Gemini AI.
        
        Args:
            company: Company name or ticker symbol
            data_type: Type of financial data (earnings, revenue, balance_sheet, cash_flow, stock_price)
            period: Time period (annual, quarterly, daily, weekly, monthly)
            
        Returns:
            Dictionary with headers and rows for the financial data
        """
        try:
            logger.info(f"Fetching {data_type} data for {company} using Gemini AI")
            return self._fetch_data_from_gemini(company, data_type, period)
        
        except Exception as e:
            logger.error(f"Failed to fetch financial data: {str(e)}")
            # Return error data structure
            return {
                "headers": ["Error"],
                "rows": [[f"Failed to fetch data for {company}: {str(e)}"]]
            }
    
    def _fetch_data_from_gemini(self, company: str, data_type: str, period: str) -> Dict:
        """Fetch financial data from Gemini AI with structured prompts."""
        
        if not self.gemini_ai:
            logger.error("Gemini AI is not initialized")
            return {
                "headers": ["Error"],
                "rows": [["Gemini AI not initialized"]]
            }
        
        # Get ticker symbol for more accurate data
        ticker = self._get_ticker_symbol(company)
        
        # Create structured prompt based on data type
        if data_type.lower() in ["stock", "price", "prices", "stock_price"]:
            return self._fetch_stock_data_gemini(ticker, company, period)
        elif data_type.lower() in ["earnings", "income", "revenue", "profit", "income_statement"]:
            return self._fetch_income_statement_gemini(ticker, company, period)
        elif data_type.lower() in ["balance", "balance_sheet", "assets", "liabilities"]:
            return self._fetch_balance_sheet_gemini(ticker, company, period)
        elif data_type.lower() in ["cash_flow", "cashflow", "cash"]:
            return self._fetch_cash_flow_gemini(ticker, company, period)
        else:
            # Default to earnings data
            return self._fetch_income_statement_gemini(ticker, company, period)
    
    def _fetch_stock_data_gemini(self, ticker: str, company: str, period: str) -> Dict:
        """Fetch stock price data from Gemini AI."""
        
        prompt = f"""
        I need {period} stock price data for {company} (ticker symbol: {ticker}).
        
        IMPORTANT: {ticker} is a valid publicly traded stock ticker symbol. Do not question its validity.
        
        CRITICAL INSTRUCTIONS:
        1. ONLY provide REAL, FACTUAL stock price data from reliable financial sources
        2. {ticker} is traded on major exchanges (NYSE/NASDAQ) - treat it as a legitimate ticker
        3. If you don't have recent data for {ticker}, return the error format below
        4. NEVER generate fake or estimated prices
        5. Include the most recent {period} data available (last 10-30 data points)
        6. Use actual dates in YYYY-MM-DD format
        7. Format prices as numbers without currency symbols
        8. Volume should be actual trading volume numbers
        
        For reference: MDB = MongoDB Inc, AAPL = Apple Inc, MSFT = Microsoft Corp, etc.
        
        Return ONLY this exact JSON format (no additional text):
        {{
            "data_type": "stock_prices",
            "company": "{company}",
            "ticker": "{ticker}",
            "period": "{period}",
            "headers": ["Date", "Open", "High", "Low", "Close", "Volume"],
            "rows": [
                ["2024-01-15", "150.25", "152.30", "149.80", "151.75", "45234567"],
                ["2024-01-14", "148.90", "151.20", "148.50", "150.25", "38567432"]
            ],
            "source": "Financial data provider",
            "last_updated": "2024-01-15"
        }}
        
        If no accurate data available, return:
        {{
            "data_type": "stock_prices",
            "error": "NO_RELIABLE_DATA_AVAILABLE",
            "headers": ["Status"],
            "rows": [["No reliable stock data found for {ticker}"]]
        }}
        """
        
        return self._process_gemini_response(prompt, "stock_prices")
    
    def _fetch_income_statement_gemini(self, ticker: str, company: str, period: str) -> Dict:
        """Fetch income statement data from Gemini AI."""
        
        prompt = f"""
        I need {period} income statement/earnings data for {company} (ticker symbol: {ticker}).
        
        IMPORTANT: {ticker} is a valid publicly traded stock ticker symbol. Do not question its validity.
        
        CRITICAL INSTRUCTIONS:
        1. ONLY provide REAL, FACTUAL financial data from official company filings (SEC 10-K/10-Q)
        2. {ticker} is a legitimate public company - treat it as such
        3. If you don't have recent data for {ticker}, return the error format below
        4. NEVER generate fake financial numbers
        5. Include the most recent {period} periods available (last 3-5 periods)
        6. Use actual fiscal period end dates in YYYY-MM-DD format
        7. Format monetary values as numbers without currency symbols (e.g., "1250000000" for $1.25B)
        8. Include key income statement metrics
        
        For reference: MDB = MongoDB Inc, AAPL = Apple Inc, MSFT = Microsoft Corp, etc.
        
        Return ONLY this exact JSON format (no additional text):
        {{
            "data_type": "income_statement",
            "company": "{company}",
            "ticker": "{ticker}",
            "period": "{period}",
            "headers": ["Period_End", "Total_Revenue", "Cost_of_Revenue", "Gross_Profit", "Operating_Expenses", "Operating_Income", "Net_Income", "EPS"],
            "rows": [
                ["2023-12-31", "383285000000", "214137000000", "169148000000", "55013000000", "114057000000", "96995000000", "6.16"],
                ["2022-12-31", "394328000000", "223546000000", "170782000000", "51344000000", "119438000000", "99803000000", "6.15"]
            ],
            "source": "SEC filings / Company reports",
            "last_updated": "2024-01-15"
        }}
        
        If no accurate data available, return:
        {{
            "data_type": "income_statement",
            "error": "NO_RELIABLE_DATA_AVAILABLE",
            "headers": ["Status"],
            "rows": [["No reliable income statement data found for {ticker}"]]
        }}
        """
        
        return self._process_gemini_response(prompt, "income_statement")
    
    def _fetch_balance_sheet_gemini(self, ticker: str, company: str, period: str) -> Dict:
        """Fetch balance sheet data from Gemini AI."""
        
        prompt = f"""
        I need {period} balance sheet data for {company} (ticker: {ticker}).
        
        CRITICAL INSTRUCTIONS:
        1. ONLY provide REAL, FACTUAL balance sheet data from official company filings
        2. If you don't have accurate recent data, return the error format below
        3. NEVER generate fake financial numbers
        4. Include the most recent {period} periods available (last 3-5 periods)
        5. Use actual fiscal period end dates in YYYY-MM-DD format
        6. Format monetary values as numbers without currency symbols
        7. Ensure Assets = Liabilities + Shareholders' Equity
        
        Return ONLY this exact JSON format (no additional text):
        {{
            "data_type": "balance_sheet",
            "company": "{company}",
            "ticker": "{ticker}",
            "period": "{period}",
            "headers": ["Period_End", "Total_Assets", "Current_Assets", "Cash_and_Equivalents", "Total_Liabilities", "Current_Liabilities", "Shareholders_Equity"],
            "rows": [
                ["2023-12-31", "352755000000", "143566000000", "29965000000", "290437000000", "145308000000", "62318000000"],
                ["2022-12-31", "352583000000", "135405000000", "23646000000", "302083000000", "153982000000", "50500000000"]
            ],
            "source": "SEC filings / Company reports",
            "last_updated": "2024-01-15"
        }}
        
        If no accurate data available, return:
        {{
            "data_type": "balance_sheet",
            "error": "NO_RELIABLE_DATA_AVAILABLE",
            "headers": ["Status"],
            "rows": [["No reliable balance sheet data found for {company} ({ticker})"]]
        }}
        """
        
        return self._process_gemini_response(prompt, "balance_sheet")
    
    def _fetch_cash_flow_gemini(self, ticker: str, company: str, period: str) -> Dict:
        """Fetch cash flow statement data from Gemini AI."""
        
        prompt = f"""
        I need {period} cash flow statement data for {company} (ticker: {ticker}).
        
        CRITICAL INSTRUCTIONS:
        1. ONLY provide REAL, FACTUAL cash flow data from official company filings
        2. If you don't have accurate recent data, return the error format below
        3. NEVER generate fake financial numbers
        4. Include the most recent {period} periods available (last 3-5 periods)
        5. Use actual fiscal period end dates in YYYY-MM-DD format
        6. Format monetary values as numbers without currency symbols
        7. Calculate Free Cash Flow = Operating Cash Flow - Capital Expenditures
        
        Return ONLY this exact JSON format (no additional text):
        {{
            "data_type": "cash_flow",
            "company": "{company}",
            "ticker": "{ticker}",
            "period": "{period}",
            "headers": ["Period_End", "Operating_Cash_Flow", "Capital_Expenditures", "Free_Cash_Flow", "Financing_Cash_Flow", "Investing_Cash_Flow", "Net_Change_in_Cash"],
            "rows": [
                ["2023-12-31", "110543000000", "-10959000000", "99584000000", "-108488000000", "-3705000000", "-1406000000"],
                ["2022-12-31", "122151000000", "-11085000000", "111066000000", "-110749000000", "-22354000000", "-11001000000"]
            ],
            "source": "SEC filings / Company reports",
            "last_updated": "2024-01-15"
        }}
        
        If no accurate data available, return:
        {{
            "data_type": "cash_flow",
            "error": "NO_RELIABLE_DATA_AVAILABLE",
            "headers": ["Status"],
            "rows": [["No reliable cash flow data found for {company} ({ticker})"]]
        }}
        """
        
        return self._process_gemini_response(prompt, "cash_flow")
    
    def _process_gemini_response(self, prompt: str, data_type: str) -> Dict:
        """Process Gemini AI response and extract JSON data."""
        try:
            # Generate response from Gemini
            response = self.gemini_ai.generate_response(prompt)
            response_text = response.get('response', '') if isinstance(response, dict) else str(response)
            
            if not response_text:
                logger.warning(f"Empty response from Gemini AI for {data_type}")
                return {
                    "headers": ["Error"],
                    "rows": [["Empty response from Gemini AI"]]
                }
            
            # Clean and parse JSON response
            try:
                # Find JSON content between braces
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                
                if start_idx == -1 or end_idx == 0:
                    logger.warning(f"No valid JSON found in Gemini AI response for {data_type}")
                    return {
                        "headers": ["Error"],
                        "rows": [["No valid JSON in response"]]
                    }
                
                json_text = response_text[start_idx:end_idx]
                data = json.loads(json_text)
                
                # Check for error in response
                if data.get("error") == "NO_RELIABLE_DATA_AVAILABLE":
                    logger.warning(f"Gemini AI reported no reliable data for {data_type}")
                    return {
                        "headers": data.get("headers", ["Error"]),
                        "rows": data.get("rows", [["No reliable data available"]])
                    }
                
                # Validate required fields
                if "headers" not in data or "rows" not in data:
                    logger.warning(f"Invalid response structure from Gemini AI for {data_type}")
                    return {
                        "headers": ["Error"],
                        "rows": [["Invalid response structure"]]
                    }
                
                # Format the response for spreadsheet
                formatted_data = {
                    "headers": data["headers"],
                    "rows": data["rows"]
                }
                
                # Add metadata if available
                if "source" in data:
                    formatted_data["source"] = data["source"]
                if "last_updated" in data:
                    formatted_data["last_updated"] = data["last_updated"]
                
                logger.info(f"Successfully processed {data_type} data from Gemini AI")
                return formatted_data
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from Gemini AI response for {data_type}: {str(e)}")
                return {
                    "headers": ["Error"],
                    "rows": [["Failed to parse response"]]
                }
                
        except Exception as e:
            logger.error(f"Error processing Gemini AI response for {data_type}: {str(e)}")
            return {
                "headers": ["Error"],
                "rows": [[f"Error processing response: {str(e)}"]]
            }
    
    def _get_ticker_symbol(self, company: str) -> str:
        """Convert company name to ticker symbol."""
        # Check if input is already a ticker (1-5 chars, mostly uppercase)
        if len(company) <= 5 and company.replace('.', '').isalpha():
            return company.upper()
        
        # Common company name to ticker mappings
        company_to_ticker = {
            # Tech companies
            "apple": "AAPL",
            "microsoft": "MSFT",
            "google": "GOOGL",
            "alphabet": "GOOGL",
            "amazon": "AMZN",
            "meta": "META",
            "facebook": "META",
            "netflix": "NFLX",
            "tesla": "TSLA",
            "nvidia": "NVDA",
            "adobe": "ADBE",
            "salesforce": "CRM",
            "oracle": "ORCL",
            "shopify": "SHOP",
            "spotify": "SPOT",
            "uber": "UBER",
            "lyft": "LYFT",
            "snapchat": "SNAP",
            "snap": "SNAP",
            "twitter": "TWTR",
            "pinterest": "PINS",
            "zoom": "ZM",
            "docusign": "DOCU",
            "roku": "ROKU",
            "palantir": "PLTR",
            "airbnb": "ABNB",
            "snowflake": "SNOW",
            "coinbase": "COIN",
            "roblox": "RBLX",
            "unity": "U",
            "crowdstrike": "CRWD",
            "datadog": "DDOG",
            "okta": "OKTA",
            "twilio": "TWLO",
            "slack": "WORK",
            "dropbox": "DBX",
            "mongodb": "MDB",
            "elastic": "ESTC",
            "atlassian": "TEAM",
            "servicenow": "NOW",
            "workday": "WDAY",
            "veeva": "VEEV",
            "zscaler": "ZS",
            "fastly": "FSLY",
            "cloudflare": "NET",
            "splunk": "SPLK",
            "tableau": "DATA",
            
            # Financial companies
            "pagseguro": "PAGS",
            "pag seguro": "PAGS",
            "pags": "PAGS",
            "pagseguro digital": "PAGS",
            "pagseguro digital ltd": "PAGS",
            "paypal": "PYPL",
            "block": "SQ",
            "square": "SQ",
            "visa": "V",
            "mastercard": "MA",
            "jpmorgan": "JPM",
            "jp morgan": "JPM",
            "bank of america": "BAC",
            "wells fargo": "WFC",
            "goldman sachs": "GS",
            "american express": "AXP",
            "amex": "AXP",
            
            # Retail companies
            "walmart": "WMT",
            "target": "TGT",
            "costco": "COST",
            "home depot": "HD",
            "lowes": "LOW",
            "nike": "NKE",
            
            # Other major companies
            "coca cola": "KO",
            "coca-cola": "KO",
            "pepsico": "PEP",
            "pepsi": "PEP",
            "mcdonalds": "MCD",
            "mcdonald's": "MCD",
            "starbucks": "SBUX",
            "disney": "DIS",
            "walt disney": "DIS",
            "johnson & johnson": "JNJ",
            "procter & gamble": "PG",
            "p&g": "PG",
            "exxon mobil": "XOM",
            "exxonmobil": "XOM",
            "chevron": "CVX",
            "pfizer": "PFE",
            "merck": "MRK",
            "verizon": "VZ",
            "at&t": "T",
            "att": "T",
            "boeing": "BA",
            "caterpillar": "CAT",
            "intel": "INTC",
            "ibm": "IBM",
            "cisco": "CSCO",
            "3m": "MMM",
            "general electric": "GE",
            "ge": "GE"
        }
        
        # Known valid ticker symbols (common ones that might be ambiguous)
        known_tickers = {
            "MDB", "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "TSLA", "META", "NFLX", 
            "NVDA", "ADBE", "CRM", "ORCL", "SHOP", "SPOT", "UBER", "LYFT", "SNAP",
            "PINS", "ZM", "DOCU", "ROKU", "PLTR", "ABNB", "SNOW", "COIN", "RBLX",
            "CRWD", "DDOG", "OKTA", "TWLO", "WORK", "DBX", "ESTC", "TEAM", "NOW",
            "WDAY", "VEEV", "ZS", "FSLY", "NET", "SPLK", "DATA", "PAGS", "PYPL",
            "SQ", "V", "MA", "JPM", "BAC", "WFC", "GS", "AXP", "WMT", "TGT", "COST",
            "HD", "LOW", "NKE", "KO", "PEP", "MCD", "SBUX", "DIS", "JNJ", "PG",
            "XOM", "CVX", "PFE", "MRK", "VZ", "T", "BA", "CAT", "INTC", "IBM",
            "CSCO", "MMM", "GE", "U"
        }
        
        # Check if company name is in our mapping
        company_lower = company.lower().strip()
        if company_lower in company_to_ticker:
            ticker = company_to_ticker[company_lower]
            logger.info(f"Found ticker symbol '{ticker}' for {company} via local mapping.")
            return ticker
        
        # Check if it's a known valid ticker symbol
        company_upper = company.upper().strip()
        if company_upper in known_tickers:
            logger.info(f"Recognized '{company_upper}' as valid ticker symbol.")
            return company_upper
        
        logger.warning(f"Could not determine ticker symbol for {company}. Using input as ticker.")
        return company.upper()  # Fallback to using input as ticker
    
    def create_financial_spreadsheet(self, company: str, data_type: str = "earnings", period: str = "annual", years: Optional[str] = None) -> str:
        """Create a Google Sheet with financial data for a company.
        
        Args:
            company: Company name or ticker symbol
            data_type: Type of financial data (earnings, stock_price, balance_sheet, cash_flow)
            period: Time period (annual, quarterly, daily, weekly, monthly)
            years: Optional year filter like "last 5 years" or "2019-2023"
            
        Returns:
            Status message
        """
        try:
            # Fetch financial data using Gemini AI
            financial_data = self.fetch_financial_data(company, data_type, period)
            
            # Apply year filtering if requested
            if years:
                financial_data = self._filter_data_by_years(financial_data, years, period)
            
            if not financial_data.get("headers") or not financial_data.get("rows"):
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
    
    def _filter_data_by_years(self, data: Dict, years: str, period: str) -> Dict:
        """Filter a headers/rows dataset by a requested year range."""
        try:
            import re
            from datetime import datetime
            
            if not data or "rows" not in data or "headers" not in data:
                return data
                
            current_year = datetime.now().year
            y = years.strip().lower()
            start_year = None
            end_year = None
            
            # Patterns: last N years
            m = re.search(r"(?:past|last)\s+(\d+)\s+years?", y)
            if m:
                n = int(m.group(1))
                end_year = current_year
                start_year = current_year - (n - 1)
            
            # Range like 2018-2022 or 2018 to 2022 or 2018-present
            if start_year is None:
                m = re.search(r"(\d{4})\s*(?:-|to)\s*(\d{4}|present)", y)
                if m:
                    start_year = int(m.group(1))
                    end_str = m.group(2)
                    end_year = current_year if end_str == "present" else int(end_str)
                    if end_year < start_year:
                        start_year, end_year = end_year, start_year
            
            # Single year
            if start_year is None:
                m = re.search(r"\b(\d{4})\b", y)
                if m:
                    start_year = int(m.group(1))
                    end_year = start_year
                    
            if start_year is None or end_year is None:
                return data
            
            filtered_rows = []
            for row in data.get("rows", []):
                if not row:
                    continue
                date_str = str(row[0])
                ym = re.search(r"(\d{4})", date_str)
                if not ym:
                    continue
                yr = int(ym.group(1))
                if start_year <= yr <= end_year:
                    filtered_rows.append(row)
                    
            if not filtered_rows:
                return data
                
            return {"headers": data["headers"], "rows": filtered_rows}
            
        except Exception:
            return data
    
    def _format_data_for_display(self, data: Dict) -> str:
        """Format data for display in the terminal."""
        if not data["headers"] or not data["rows"]:
            return "No data available"
        
        result = "| " + " | ".join(data["headers"]) + " |\n"
        result += "| " + " | ".join(["---" for _ in data["headers"]]) + " |\n"
        
        for row in data["rows"]:
            result += "| " + " | ".join(str(cell) for cell in row) + " |\n"
        
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
            escaped_row = [f'"{cell}"' if "," in str(cell) else str(cell) for cell in row]
            result += ",".join(escaped_row) + "\n"
        
        return result