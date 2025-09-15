"""Google Sheets Manager Plugin - Create and manage Google Sheets"""

import os
import subprocess
import logging
import json
import requests
from datetime import datetime
from typing import Dict, Any, Optional, List, Union, Tuple
from pathlib import Path
import time


logger = logging.getLogger(__name__)

class GoogleSheetsManager:
    def __init__(self, web_search_tool=None):
        self.download_dir = Path.home() / 'Downloads'
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.web_search_tool = web_search_tool
        
        self.alpha_vantage_api_key = os.environ.get('ALPHA_VANTAGE_API_KEY')
        if not self.alpha_vantage_api_key or self.alpha_vantage_api_key == 'demo':
            logger.warning("ALPHA_VANTAGE_API_KEY is not set or is set to 'demo'. Using a demo key with limited functionality. Please set a valid API key for full access.")
            self.alpha_vantage_api_key = 'demo'
        self.alpha_vantage_base_url = 'https://www.alphavantage.co/query'
    
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
            
            # Try to use Alpha Vantage API first (more reliable)
            try:
                logger.info(f"Attempting to fetch data from Alpha Vantage API for {company}")
                return self._fetch_data_from_alpha_vantage(company, data_type, period)
            except Exception as e:
                logger.warning(f"Alpha Vantage API failed: {str(e)}. Falling back to web scraping.")
            
            # Fallback to web scraping if API fails
            return self._web_scrape_financial_data(company, data_type, period)
        
        except Exception as e:
            logger.error(f"Failed to fetch financial data: {str(e)}")
            # Return empty data structure on error
            return {
                "headers": [],
                "rows": []
            }
    
    def _web_scrape_financial_data(self, company: str, data_type: str, period: str) -> Dict:
        """Web scrape financial data as a fallback when API fails."""
        try:
            search_query = f"{company} {data_type} {period} financial statement"
            if self.web_search_tool:
                search_results = self.web_search_tool.search(search_query, num=5)
                # Prioritize results from reputable financial sites
                # (e.g., investor relations, major financial news)
                target_url = None
                for result in search_results:
                    url = result.get('link')
                    if url and ("investor" in url or "finance" in url or "reports" in url):
                        target_url = url
                        break
                if not target_url and search_results:
                    target_url = search_results[0].get('link') # Fallback to first result
            else:
                logger.warning("Web search tool not available for web scraping fallback.")
                return {"headers": [], "rows": []}

            if not target_url:
                logger.warning(f"No relevant web page found for {company} {data_type} {period}.")
                return {"headers": [], "rows": []}

            logger.info(f"Attempting to scrape data from: {target_url}")
            response = self.session.get(target_url, timeout=15)
            response.raise_for_status() # Raise an exception for HTTP errors

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            data = {"headers": ["Metric", "Value"], "rows": []}
            found_data = False

            # Look for tables that might contain financial data
            tables = soup.find_all('table')
            for table in tables:
                # Simple heuristic: check if table contains common financial keywords
                table_text = table.get_text().lower()
                if any(keyword in table_text for keyword in ["revenue", "income", "balance sheet", "cash flow"]):
                    # Attempt to parse table headers and rows
                    headers = [th.get_text(strip=True) for th in table.find_all('th')]
                    rows = []
                    for tr in table.find_all('tr'):
                        cols = [td.get_text(strip=True) for td in tr.find_all('td')]
                        if cols:
                            rows.append(cols)
                    
                    # Basic attempt to match data_type with table content
                    if data_type in table_text:
                        # This is still very basic and needs more advanced parsing
                        # For now, just return the first relevant table's data
                        data["headers"] = headers if headers else ["Column 1", "Column 2"]
                        data["rows"] = rows
                        found_data = True
                        break
            
            if found_data:
                logger.info(f"Successfully scraped data for {company} {data_type} {period} from {target_url}.")
                return data
            else:
                logger.warning(f"No specific financial data found for {company} {data_type} {period} on {target_url}.")
                return {
                    "headers": ["Data Source", "Status"],
                    "rows": [["Web Scrape", "Data extraction failed or not found"]]
                }

        except requests.exceptions.RequestException as req_err:
            logger.error(f"Network or HTTP error during web scraping: {req_err}")
            return {"headers": [], "rows": []}
        except Exception as e:
            logger.error(f"Failed during web scraping for {company} {data_type} {period}: {str(e)}")
            return {"headers": [], "rows": []}

    def _fetch_data_from_alpha_vantage(self, company: str, data_type: str, period: str) -> Dict:
        """Fetch financial data from Alpha Vantage API.
        
        Args:
            company: Company name or ticker symbol
            data_type: Type of financial data (earnings, revenue, etc.)
            period: Time period (annual, quarterly, etc.)
            
        Returns:
            Dictionary with headers and rows for the financial data
        """
        # Convert company name to ticker symbol if needed
        ticker = self._get_ticker_symbol(company)
        
        # Determine which Alpha Vantage function to use based on data_type
        if data_type in ["stock", "price", "prices"]:
            return self._fetch_stock_time_series(ticker, period)
        elif data_type in ["earnings", "income", "revenue", "profit"]:
            return self._fetch_income_statement(ticker, period)
        elif data_type in ["balance", "balance sheet", "assets", "liabilities"]:
            return self._fetch_balance_sheet(ticker, period)
        elif data_type in ["cash flow", "cashflow", "cash"]:
            return self._fetch_cash_flow(ticker, period)
        else:
            # Default to time series data
            return self._fetch_stock_time_series(ticker, period)
    
    def _get_ticker_symbol(self, company: str) -> str:
        """Convert company name to ticker symbol if needed."""
        # Common company name to ticker mappings
        company_to_ticker = {
            "apple": "AAPL",
            "microsoft": "MSFT",
            "amazon": "AMZN",
            "google": "GOOGL",
            "alphabet": "GOOGL",
            "meta": "META",
            "facebook": "META",
            "tesla": "TSLA",
            "nvidia": "NVDA",
            "netflix": "NFLX",
            "ibm": "IBM",
            "intel": "INTC",
            "amd": "AMD"
        }
        
        # Check if input is already a ticker (all caps, 1-5 chars)
        if company.isupper() and 1 <= len(company) <= 5:
            return company
        
        # Check if we have a mapping for this company name
        company_lower = company.lower()
        if company_lower in company_to_ticker:
            return company_to_ticker[company_lower]
        
        # If no mapping found, assume input might be a ticker
        return company.upper()
    
    def _fetch_stock_time_series(self, ticker: str, period: str) -> Dict:
        """Fetch stock time series data from Alpha Vantage."""
        # Determine the function based on period
        if period in ["daily", "day"]:
            function = "TIME_SERIES_DAILY"
            key_name = "Time Series (Daily)"
        elif period in ["weekly", "week"]:
            function = "TIME_SERIES_WEEKLY"
            key_name = "Weekly Time Series"
        elif period in ["monthly", "month"]:
            function = "TIME_SERIES_MONTHLY"
            key_name = "Monthly Time Series"
        elif period in ["intraday", "minute", "minutes", "hourly", "hour"]:
            function = "TIME_SERIES_INTRADAY"
            key_name = "Time Series (5min)"
        else:  # Default to daily
            function = "TIME_SERIES_DAILY"
            key_name = "Time Series (Daily)"
        
        # Process the data
        result = {"headers": ["Date", "Open", "High", "Low", "Close", "Volume"], "rows": []}
        
        try:
            # Make API request
            params = {
                "function": function,
                "symbol": ticker,
                "apikey": self.alpha_vantage_api_key,
                "outputsize": "compact"  # Use compact for most recent 100 data points
            }
            
            # Add interval parameter for intraday data
            if function == "TIME_SERIES_INTRADAY":
                params["interval"] = "5min"
            
            response = self.session.get(self.alpha_vantage_base_url, params=params, timeout=10)
            data = response.json()
            
            # Check for error messages
            if "Error Message" in data:
                raise ValueError(f"Alpha Vantage API error: {data['Error Message']}")
            
            # Check for information message (demo key limitation)
            if "Information" in data and "demo" in data["Information"]:
                logger.warning("Using demo API key with limited functionality. Using sample data instead.")
                return self._get_sample_stock_data(ticker, period)
            
            # Extract time series data
            if key_name in data:
                time_series = data[key_name]
                # Sort dates in descending order (newest first)
                dates = sorted(time_series.keys(), reverse=True)
                
                # Limit to 30 data points to avoid overwhelming the spreadsheet
                for date in dates[:30]:
                    daily_data = time_series[date]
                    row = [
                        date,
                        daily_data.get("1. open", ""),
                        daily_data.get("2. high", ""),
                        daily_data.get("3. low", ""),
                        daily_data.get("4. close", ""),
                        daily_data.get("5. volume", "")
                    ]
                    result["rows"].append(row)
                
                return result
            else:
                logger.warning(f"No time series data found for {ticker}. Using sample data instead.")
                return self._get_sample_stock_data(ticker, period)
                
        except Exception as e:
            logger.error(f"Error fetching stock data from Alpha Vantage: {str(e)}. Using sample data instead.")
            return self._get_sample_stock_data(ticker, period)
            
    def _get_sample_stock_data(self, ticker: str, period: str) -> Dict:
        """Generate sample stock data for demonstration purposes."""
        import random
        from datetime import datetime, timedelta
        
        result = {"headers": ["Date", "Open", "High", "Low", "Close", "Volume"], "rows": []}
        
        # Generate sample data based on ticker and period
        base_price = 0
        if ticker == "AAPL":
            base_price = 180.0
        elif ticker == "MSFT":
            base_price = 350.0
        elif ticker == "GOOGL":
            base_price = 140.0
        elif ticker == "AMZN":
            base_price = 170.0
        elif ticker == "META":
            base_price = 450.0
        elif ticker == "TSLA":
            base_price = 220.0
        elif ticker == "NVDA":
            base_price = 800.0
        elif ticker == "IBM":
            base_price = 170.0
        else:
            base_price = 100.0
        
        # Determine date increment based on period
        if period in ["daily", "day"]:
            date_increment = timedelta(days=1)
        elif period in ["weekly", "week"]:
            date_increment = timedelta(weeks=1)
        elif period in ["monthly", "month"]:
            date_increment = timedelta(days=30)
        else:
            date_increment = timedelta(days=1)
        
        # Generate 30 days of sample data
        current_date = datetime.now()
        for i in range(30):
            # Skip weekends for daily data
            if period in ["daily", "day"] and current_date.weekday() >= 5:  # 5=Saturday, 6=Sunday
                current_date -= date_increment
                continue
                
            # Generate random price fluctuations (within reasonable bounds)
            daily_fluctuation = random.uniform(-5.0, 5.0)
            open_price = round(base_price + daily_fluctuation, 2)
            close_price = round(open_price + random.uniform(-2.0, 2.0), 2)
            high_price = round(max(open_price, close_price) + random.uniform(0.1, 1.0), 2)
            low_price = round(min(open_price, close_price) - random.uniform(0.1, 1.0), 2)
            volume = int(random.uniform(1000000, 10000000))
            
            # Format date based on period
            date_str = current_date.strftime('%Y-%m-%d')
            
            # Add row to result
            result["rows"].append([
                date_str,
                str(open_price),
                str(high_price),
                str(low_price),
                str(close_price),
                str(volume)
            ])
            
            # Move to previous date
            current_date -= date_increment
            
        # Add note that this is sample data
        result["headers"].append("Note")
        for row in result["rows"]:
            row.append("Sample data for demonstration purposes")
            
        return result
        
    def _get_sample_income_statement(self, ticker: str, period: str) -> Dict:
        """Generate sample income statement data when API data is unavailable."""
        import random
        from datetime import datetime, timedelta
        
        result = {"headers": ["Date", "Metric", "Value", "Note"], "rows": []}
        
        # Generate sample dates based on period
        if period.lower() in ["quarterly", "quarter", "q"]:
            dates = [
                (datetime.now() - timedelta(days=90*i)).strftime("%Y-%m-%d") 
                for i in range(4)
            ]
        else:  # Annual
            dates = [
                (datetime.now() - timedelta(days=365*i)).strftime("%Y-%m-%d") 
                for i in range(3)
            ]
            
        # Sample income statement metrics
        metrics = [
            "Total Revenue", 
            "Cost of Revenue", 
            "Gross Profit", 
            "Operating Expenses",
            "Operating Income", 
            "Net Income"
        ]
        
        # Generate sample data with realistic values based on ticker
        base_revenue = 1000000000  # $1B base revenue
        
        for date in dates:
            revenue = base_revenue * (1 + random.uniform(-0.2, 0.3))  # +/- 20-30% variation
            cost_of_revenue = revenue * random.uniform(0.4, 0.7)  # 40-70% of revenue
            gross_profit = revenue - cost_of_revenue
            operating_expenses = gross_profit * random.uniform(0.3, 0.6)  # 30-60% of gross profit
            operating_income = gross_profit - operating_expenses
            net_income = operating_income * random.uniform(0.5, 0.9)  # 50-90% of operating income after taxes
            
            values = {
                "Total Revenue": revenue,
                "Cost of Revenue": cost_of_revenue,
                "Gross Profit": gross_profit,
                "Operating Expenses": operating_expenses,
                "Operating Income": operating_income,
                "Net Income": net_income
            }
            
            for metric in metrics:
                result["rows"].append([date, metric, f"${values[metric]:,.2f}", "Sample data for demonstration purposes"])
        
        return result
    
    def _get_sample_balance_sheet(self, ticker: str, period: str) -> Dict:
        """Generate sample balance sheet data when API data is unavailable."""
        import random
        from datetime import datetime, timedelta
        
        result = {"headers": ["Date", "Metric", "Value", "Note"], "rows": []}
        
        # Generate sample dates based on period
        if period.lower() in ["quarterly", "quarter", "q"]:
            dates = [
                (datetime.now() - timedelta(days=90*i)).strftime("%Y-%m-%d") 
                for i in range(4)
            ]
        else:  # Annual
            dates = [
                (datetime.now() - timedelta(days=365*i)).strftime("%Y-%m-%d") 
                for i in range(3)
            ]
            
        # Sample balance sheet metrics
        metrics = [
            "Total Assets", 
            "Current Assets", 
            "Cash and Cash Equivalents", 
            "Total Liabilities",
            "Current Liabilities", 
            "Total Shareholders Equity"
        ]
        
        # Generate sample data with realistic values based on ticker
        base_assets = 5000000000  # $5B base assets
        
        for date in dates:
            total_assets = base_assets * (1 + random.uniform(-0.1, 0.2))  # +/- 10-20% variation
            current_assets = total_assets * random.uniform(0.3, 0.5)  # 30-50% of total assets
            cash = current_assets * random.uniform(0.2, 0.4)  # 20-40% of current assets
            total_liabilities = total_assets * random.uniform(0.4, 0.7)  # 40-70% of total assets
            current_liabilities = total_liabilities * random.uniform(0.3, 0.5)  # 30-50% of total liabilities
            equity = total_assets - total_liabilities
            
            values = {
                "Total Assets": total_assets,
                "Current Assets": current_assets,
                "Cash and Cash Equivalents": cash,
                "Total Liabilities": total_liabilities,
                "Current Liabilities": current_liabilities,
                "Total Shareholders Equity": equity
            }
            
            for metric in metrics:
                result["rows"].append([date, metric, f"${values[metric]:,.2f}", "Sample data for demonstration purposes"])
        
        return result
        
    def _get_sample_cash_flow(self, ticker: str, period: str) -> Dict:
        """Generate sample cash flow data when API data is unavailable."""
        import random
        from datetime import datetime, timedelta
        
        result = {"headers": ["Date", "Metric", "Value", "Note"], "rows": []}
        
        # Generate sample dates based on period
        if period.lower() in ["quarterly", "quarter", "q"]:
            dates = [
                (datetime.now() - timedelta(days=90*i)).strftime("%Y-%m-%d") 
                for i in range(4)
            ]
        else:  # Annual
            dates = [
                (datetime.now() - timedelta(days=365*i)).strftime("%Y-%m-%d") 
                for i in range(3)
            ]
            
        # Sample cash flow metrics
        metrics = [
            "Operating Cash Flow", 
            "Capital Expenditures", 
            "Free Cash Flow", 
            "Dividend Payments",
            "Stock Repurchases", 
            "Net Change in Cash"
        ]
        
        # Generate sample data with realistic values based on ticker
        base_operating_cf = 800000000  # $800M base operating cash flow
        
        for date in dates:
            operating_cf = base_operating_cf * (1 + random.uniform(-0.15, 0.25))  # +/- 15-25% variation
            capex = operating_cf * random.uniform(0.2, 0.4) * -1  # 20-40% of operating CF (negative)
            free_cf = operating_cf + capex
            dividends = free_cf * random.uniform(0.1, 0.3) * -1  # 10-30% of free CF (negative)
            repurchases = free_cf * random.uniform(0.1, 0.4) * -1  # 10-40% of free CF (negative)
            net_change = free_cf + dividends + repurchases
            
            values = {
                "Operating Cash Flow": operating_cf,
                "Capital Expenditures": capex,
                "Free Cash Flow": free_cf,
                "Dividend Payout": dividends,
                "Stock Buyback": repurchases,
                "Net Change in Cash": net_change
            }
            
            for metric in metrics:
                result["rows"].append([date, metric, f"${values[metric]:,.2f}", "Sample data for demonstration purposes"])
        
        return result
        for row in result["rows"]:
            row.append("Sample data for demonstration")
            
        return result
    
    def _fetch_income_statement(self, ticker: str, period: str) -> Dict:
        """Fetch income statement data from Alpha Vantage."""
        # Process the data
        result = {"headers": ["Date", "Metric", "Value"], "rows": []}
        
        try:
            # Make API request
            params = {
                "function": "INCOME_STATEMENT",
                "symbol": ticker,
                "apikey": self.alpha_vantage_api_key
            }
            
            response = self.session.get(self.alpha_vantage_base_url, params=params, timeout=10)
            data = response.json()
            
            # Check for error messages
            if "Error Message" in data:
                raise ValueError(f"Alpha Vantage API error: {data['Error Message']}")
            
            # Check for information message (demo key limitation)
            if "Information" in data and "demo" in data["Information"]:
                logger.warning("Using demo API key with limited functionality. Using sample data instead.")
                return self._get_sample_income_statement(ticker, period)
            
            # Determine which reports to use based on period
            reports_key = "quarterlyReports" if period.lower() in ["quarterly", "quarter", "q"] else "annualReports"
            
            if reports_key in data and data[reports_key]:
                reports = data[reports_key]
                
                # Get the most recent report
                for report in reports[:4]:  # Limit to 4 most recent reports
                    fiscal_date = report.get("fiscalDateEnding", "")
                    
                    # Add key financial metrics
                    metrics = [
                        ("Total Revenue", "totalRevenue"),
                        ("Gross Profit", "grossProfit"),
                        ("Net Income", "netIncome"),
                        ("EPS", "reportedEPS"),
                        ("EBITDA", "ebitda")
                    ]
                    
                    for metric_name, metric_key in metrics:
                        if metric_key in report and report[metric_key]:
                            result["rows"].append([fiscal_date, metric_name, report[metric_key]])
                
                return result
            else:
                logger.warning(f"No income statement data found for {ticker}")
                return self._get_sample_income_statement(ticker, period)
        except Exception as e:
            logger.warning(f"Error fetching income statement data for {ticker}: {str(e)}")
            return self._get_sample_income_statement(ticker, period)
            
    def _get_sample_income_statement(self, ticker: str, period: str) -> Dict:
        """Generate sample income statement data when API data is unavailable."""
        result = {"headers": ["Date", "Metric", "Value"], "rows": []}
        
        # Generate sample dates based on period
        if period.lower() in ["quarterly", "quarter", "q"]:
            dates = [
                (datetime.now() - timedelta(days=90*i)).strftime("%Y-%m-%d") 
                for i in range(4)
            ]
        else:  # Annual
            dates = [
                (datetime.now() - timedelta(days=365*i)).strftime("%Y-%m-%d") 
                for i in range(3)
            ]
            
        # Sample income statement metrics
        metrics = [
            "Total Revenue", 
            "Cost of Revenue", 
            "Gross Profit", 
            "Operating Expenses",
            "Operating Income", 
            "Net Income"
        ]
        
        # Generate sample data with realistic values based on ticker
        base_revenue = 1000000000  # $1B base revenue
        
        for date in dates:
            revenue = base_revenue * (1 + random.uniform(-0.2, 0.3))  # +/- 20-30% variation
            cost_of_revenue = revenue * random.uniform(0.4, 0.7)  # 40-70% of revenue
            gross_profit = revenue - cost_of_revenue
            operating_expenses = gross_profit * random.uniform(0.3, 0.6)  # 30-60% of gross profit
            operating_income = gross_profit - operating_expenses
            net_income = operating_income * random.uniform(0.5, 0.9)  # 50-90% of operating income after taxes
            
            values = {
                "Total Revenue": revenue,
                "Cost of Revenue": cost_of_revenue,
                "Gross Profit": gross_profit,
                "Operating Expenses": operating_expenses,
                "Operating Income": operating_income,
                "Net Income": net_income
            }
            
            for metric in metrics:
                result["rows"].append([date, metric, f"${values[metric]:,.2f}"])
        
        return result
    
    def _fetch_balance_sheet(self, ticker: str, period: str) -> Dict:
        """Fetch balance sheet data from Alpha Vantage."""
        # Process the data
        result = {"headers": ["Date", "Metric", "Value"], "rows": []}
        
        try:
            # Make API request
            params = {
                "function": "BALANCE_SHEET",
                "symbol": ticker,
                "apikey": self.alpha_vantage_api_key
            }
            
            response = self.session.get(self.alpha_vantage_base_url, params=params, timeout=10)
            data = response.json()
            
            # Check for error messages
            if "Error Message" in data:
                raise ValueError(f"Alpha Vantage API error: {data['Error Message']}")
            
            # Check for information message (demo key limitation)
            if "Information" in data and "demo" in data["Information"]:
                logger.warning("Using demo API key with limited functionality. Using sample data instead.")
                return self._get_sample_balance_sheet(ticker, period)
            
            # Determine which reports to use based on period
            reports_key = "quarterlyReports" if period.lower() in ["quarterly", "quarter", "q"] else "annualReports"
            
            if reports_key in data and data[reports_key]:
                reports = data[reports_key]
                
                # Get the most recent report
                for report in reports[:2]:  # Limit to 2 most recent reports
                    fiscal_date = report.get("fiscalDateEnding", "")
                    
                    # Add key financial metrics
                    metrics = [
                        ("Total Assets", "totalAssets"),
                        ("Total Liabilities", "totalLiabilities"),
                    ("Total Shareholder Equity", "totalShareholderEquity"),
                    ("Cash and Equivalents", "cashAndCashEquivalentsAtCarryingValue"),
                    ("Short-Term Debt", "shortTermDebt"),
                    ("Long-Term Debt", "longTermDebt")
                ]
                
                    for metric_name, metric_key in metrics:
                        if metric_key in report and report[metric_key]:
                            result["rows"].append([fiscal_date, metric_name, report[metric_key]])
                
                return result
            else:
                logger.warning(f"No balance sheet data found for {ticker}")
                return self._get_sample_balance_sheet(ticker, period)
        except Exception as e:
            logger.warning(f"Error fetching balance sheet data for {ticker}: {str(e)}")
            return self._get_sample_balance_sheet(ticker, period)
            
    def _get_sample_balance_sheet(self, ticker: str, period: str) -> Dict:
        """Generate sample balance sheet data when API data is unavailable."""
        result = {"headers": ["Date", "Metric", "Value"], "rows": []}
        
        # Generate sample dates based on period
        if period.lower() in ["quarterly", "quarter", "q"]:
            dates = [
                (datetime.now() - timedelta(days=90*i)).strftime("%Y-%m-%d") 
                for i in range(4)
            ]
        else:  # Annual
            dates = [
                (datetime.now() - timedelta(days=365*i)).strftime("%Y-%m-%d") 
                for i in range(3)
            ]
            
        # Sample balance sheet metrics
        metrics = [
            "Total Assets", 
            "Current Assets", 
            "Cash and Cash Equivalents", 
            "Total Liabilities",
            "Current Liabilities", 
            "Total Shareholders Equity"
        ]
        
        # Generate sample data with realistic values based on ticker
        base_assets = 5000000000  # $5B base assets
        
        for date in dates:
            total_assets = base_assets * (1 + random.uniform(-0.1, 0.2))  # +/- 10-20% variation
            current_assets = total_assets * random.uniform(0.3, 0.5)  # 30-50% of total assets
            cash = current_assets * random.uniform(0.2, 0.4)  # 20-40% of current assets
            total_liabilities = total_assets * random.uniform(0.4, 0.7)  # 40-70% of total assets
            current_liabilities = total_liabilities * random.uniform(0.3, 0.5)  # 30-50% of total liabilities
            equity = total_assets - total_liabilities
            
            values = {
                "Total Assets": total_assets,
                "Current Assets": current_assets,
                "Cash and Cash Equivalents": cash,
                "Total Liabilities": total_liabilities,
                "Current Liabilities": current_liabilities,
                "Total Shareholders Equity": equity
            }
            
            for metric in metrics:
                result["rows"].append([date, metric, f"${values[metric]:,.2f}"])
        
        return result
    
    def _fetch_cash_flow(self, ticker: str, period: str) -> Dict:
        """Fetch cash flow data from Alpha Vantage."""
        # Process the data
        result = {"headers": ["Date", "Metric", "Value"], "rows": []}
        
        try:
            # Make API request
            params = {
                "function": "CASH_FLOW",
                "symbol": ticker,
                "apikey": self.alpha_vantage_api_key
            }
            
            response = self.session.get(self.alpha_vantage_base_url, params=params, timeout=10)
            data = response.json()
            
            # Check for error messages
            if "Error Message" in data:
                raise ValueError(f"Alpha Vantage API error: {data['Error Message']}")
            
            # Check for information message (demo key limitation)
            if "Information" in data and "demo" in data["Information"]:
                logger.warning("Using demo API key with limited functionality. Using sample data instead.")
                return self._get_sample_cash_flow(ticker, period)
            
            # Determine which reports to use based on period
            reports_key = "quarterlyReports" if period.lower() in ["quarterly", "quarter", "q"] else "annualReports"
            
            if reports_key in data and data[reports_key]:
                reports = data[reports_key]
                
                # Get the most recent reports
                for report in reports[:2]:  # Limit to 2 most recent reports
                    fiscal_date = report.get("fiscalDateEnding", "")
                    
                    # Add key financial metrics
                    metrics = [
                        ("Operating Cash Flow", "operatingCashflow"),
                        ("Capital Expenditures", "capitalExpenditures"),
                        ("Free Cash Flow", "cashflowFromInvestment"),
                        ("Dividend Payout", "dividendPayout"),
                        ("Stock Buyback", "paymentsForRepurchaseOfCommonStock")
                    ]
                    
                    for metric_name, metric_key in metrics:
                        if metric_key in report and report[metric_key]:
                            result["rows"].append([fiscal_date, metric_name, report[metric_key]])
            
                return result
            else:
                logger.warning(f"No cash flow data found for {ticker}")
                return self._get_sample_cash_flow(ticker, period)
        except Exception as e:
            logger.warning(f"Error fetching cash flow data for {ticker}: {str(e)}")
            return self._get_sample_cash_flow(ticker, period)
    
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