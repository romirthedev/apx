
import pandas as pd
from typing import Dict, Any, Optional, List
import logging
import random
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FinancialSpreadsheetGenerator:
    """
    A specialized tool to generate financial spreadsheets with past 5 years
    of financial information for a given company.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initializes the FinancialSpreadsheetGenerator.

        Args:
            api_key: Your API key for accessing financial data.
                     If None, the tool will operate in a simulated mode.
        """
        self.api_key = api_key
        self.base_url = "https://api.example-financial-data.com/v1/" # Placeholder for actual API
        self.simulated_mode = not bool(api_key)
        if self.simulated_mode:
            logging.warning("No API key provided. Operating in simulated mode with dummy data.")

    def _fetch_financial_data(self, symbol: str, metric: str, years: int) -> Dict[str, Any]:
        """
        Fetches financial data from an external API or simulates it.

        Args:
            symbol: The stock ticker symbol (e.g., 'AAPL').
            metric: The financial metric to fetch (e.g., 'revenue', 'net_income').
            years: The number of past years to fetch data for.

        Returns:
            A dictionary containing the fetched data or an error message.
            Successful response includes:
                'success': True
                'data': Dictionary of year-value pairs.
                'metric': The requested metric.
                'symbol': The requested symbol.
            Error response includes:
                'success': False
                'message': An error description.
        """
        logging.info(f"Attempting to fetch '{metric}' for symbol '{symbol}' for the past {years} years.")

        if self.simulated_mode:
            # --- SIMULATION START ---
            try:
                end_year = datetime.now().year
                data_points = {}
                for i in range(years):
                    year = end_year - i
                    # Generate more realistic-looking dummy data
                    base_value = random.uniform(1_000_000, 10_000_000_000)
                    if metric == 'earnings_per_share':
                        value = random.uniform(0.1, 50.0)
                    else:
                        # Simulate some growth/fluctuation
                        growth_factor = 1 + (random.random() - 0.5) * 0.2 # +/- 20% fluctuation
                        value = base_value * growth_factor
                    data_points[str(year)] = round(value, 2)

                # Simulate potential API errors
                if random.random() < 0.1: # 10% chance of a simulated error
                    raise ConnectionError("Simulated API connection error.")
                if random.random() < 0.05: # 5% chance of invalid symbol in simulation
                    return {"success": False, "message": f"Simulated invalid stock symbol: {symbol}"}
                if not data_points:
                    return {"success": False, "message": "No data points generated in simulation."}

                logging.info(f"Successfully simulated fetching '{metric}' for '{symbol}'.")
                return {"success": True, "data": data_points, "metric": metric, "symbol": symbol}

            except Exception as e:
                logging.error(f"Simulated data fetching error for '{symbol}', metric '{metric}': {e}")
                return {"success": False, "message": f"Error fetching data: {e}"}
            # --- SIMULATION END ---
        else:
            # --- REAL API CALL (Placeholder) ---
            # This section requires implementation with a real financial data API.
            # Example using a hypothetical API endpoint:
            # try:
            #     endpoint = f"{self.base_url}{symbol}/{metric}?years={years}&apiKey={self.api_key}"
            #     response = requests.get(endpoint)
            #     response.raise_for_status() # Raise an exception for bad status codes
            #     data = response.json()
            #
            #     if data.get("success"):
            #         # Ensure data is in the expected year: value format
            #         formatted_data = {str(item['year']): item['value'] for item in data.get('results', [])}
            #         logging.info(f"Successfully fetched '{metric}' for '{symbol}' from API.")
            #         return {"success": True, "data": formatted_data, "metric": metric, "symbol": symbol}
            #     else:
            #         logging.error(f"API returned an error for '{symbol}', metric '{metric}': {data.get('message', 'Unknown API error')}")
            #         return {"success": False, "message": data.get('message', 'Unknown API error')}
            #
            # except requests.exceptions.RequestException as e:
            #     logging.error(f"API request failed for '{symbol}', metric '{metric}': {e}")
            #     return {"success": False, "message": f"API request failed: {e}"}
            # except Exception as e:
            #     logging.error(f"An unexpected error occurred during API call for '{symbol}', metric '{metric}': {e}")
            #     return {"success": False, "message": f"An unexpected error occurred: {e}"}
            logging.error("Real API call is not implemented. Please implement it or run in simulated mode.")
            return {"success": False, "message": "Real API calls are not implemented."}
            # --- END REAL API CALL ---

    def generate_past_5_years_financial_report(self, symbol: str) -> Dict[str, Any]:
        """
        Generates a financial report for the past 5 years, including key financial metrics.

        Args:
            symbol: The stock ticker symbol of the company (e.g., 'AAPL').

        Returns:
            A dictionary indicating the success or failure of the generation.
            On success:
                'success': True
                'message': "Financial report generated successfully."
                'report_data': A Pandas DataFrame containing the financial information.
            On failure:
                'success': False
                'message': An error description.
        """
        logging.info(f"Starting financial report generation for symbol: {symbol}")

        # Input validation for symbol
        if not isinstance(symbol, str) or not symbol.strip():
            error_msg = "Invalid input: Stock symbol cannot be empty or non-string."
            logging.error(error_msg)
            return {"success": False, "message": error_msg}

        symbol = symbol.strip().upper() # Standardize symbol

        metrics_to_fetch = ['revenue', 'gross_profit', 'operating_income', 'net_income', 'earnings_per_share']
        all_financial_data = {}
        fetch_errors = []

        for metric in metrics_to_fetch:
            fetch_result = self._fetch_financial_data(symbol, metric, 5)
            if fetch_result.get("success"):
                data_points = fetch_result.get("data", {})
                if not data_points:
                    logging.warning(f"No data points returned for metric '{metric}' for symbol '{symbol}'.")
                    fetch_errors.append(f"No data for '{metric}'")
                    continue
                all_financial_data[metric] = data_points
            else:
                error_message = fetch_result.get('message', f'Unknown error for {metric}')
                logging.error(f"Failed to fetch '{metric}' for symbol '{symbol}': {error_message}")
                fetch_errors.append(f"'{metric}': {error_message}")

        if not all_financial_data:
            error_msg = f"Could not retrieve any financial data for symbol '{symbol}'. Errors encountered: {', '.join(fetch_errors)}"
            logging.error(error_msg)
            return {"success": False, "message": error_msg}

        # Structure the data into a Pandas DataFrame
        try:
            # Convert to DataFrame ensuring all metrics have entries for all years
            # If a metric is missing for a year, it will be NaN.
            df = pd.DataFrame.from_dict(all_financial_data, orient='index').T
            df.index.name = 'Year'
            df.columns.name = 'Metric'

            # Convert index to integer years and sort
            df.index = pd.to_numeric(df.index, errors='coerce')
            df = df.dropna(axis=0, subset=['Year']) # Remove rows where year conversion failed
            df.index = df.index.astype(int)
            df = df.sort_index(ascending=False)

            # Fill missing values with a placeholder or 0, depending on context
            # For financial data, NaN is often acceptable, but for presentation, 0 might be preferred if absence implies zero.
            # Let's stick with NaN for now as it's more informative.
            # df = df.fillna(0)

            logging.info(f"Financial report for '{symbol}' generated successfully with {len(df.index)} years of data.")
            return {
                "success": True,
                "message": "Financial report generated successfully.",
                "report_data": df
            }
        except Exception as e:
            error_msg = f"Error structuring financial data for symbol '{symbol}': {e}"
            logging.error(error_msg)
            return {"success": False, "message": error_msg}

    def save_report_to_csv(self, report_data: pd.DataFrame, filename: str) -> Dict[str, Any]:
        """
        Saves the generated financial report DataFrame to a CSV file.

        Args:
            report_data: The Pandas DataFrame containing the financial report.
            filename: The desired name for the CSV file (e.g., 'company_financials.csv').

        Returns:
            A dictionary indicating the success or failure of the save operation.
        """
        # Input validation for report_data
        if not isinstance(report_data, pd.DataFrame) or report_data.empty:
            error_msg = "Invalid input: No valid or empty financial report data provided to save."
            logging.error(error_msg)
            return {"success": False, "message": error_msg}

        # Input validation for filename
        if not isinstance(filename, str) or not filename.strip():
            error_msg = "Invalid input: Filename cannot be empty or non-string."
            logging.error(error_msg)
            return {"success": False, "message": error_msg}

        filename = filename.strip()
        if not filename.lower().endswith(".csv"):
            filename += ".csv" # Automatically append .csv if missing
            logging.warning(f"Filename did not end with .csv. Appended extension. New filename: '{filename}'")

        try:
            report_data.to_csv(filename)
            logging.info(f"Financial report successfully saved to '{filename}'.")
            return {"success": True, "message": f"Financial report successfully saved to '{filename}'."}
        except IOError as e:
            error_msg = f"IOError: Failed to save file to '{filename}'. Check permissions or path. Details: {e}"
            logging.error(error_msg)
            return {"success": False, "message": error_msg}
        except Exception as e:
            error_msg = f"An unexpected error occurred during file save to '{filename}': {e}"
            logging.error(error_msg)
            return {"success": False, "message": error_msg}

# Example Usage (for testing purposes)
if __name__ == '__main__':
    # In a real application, you would get the API key securely.
    # For this example, we use None to test simulated mode or a placeholder.
    # Replace with your actual API key to test real data fetching (if implemented).
    API_KEY = None # Set to your actual API key or None for simulation

    try:
        generator = FinancialSpreadsheetGenerator(api_key=API_KEY)
        logging.info("FinancialSpreadsheetGenerator initialized.")
    except Exception as e:
        logging.critical(f"Failed to initialize FinancialSpreadsheetGenerator: {e}")
        exit()

    # --- Test Case 1: Successful generation and saving ---
    print("\n--- Testing successful report generation and saving ---")
    symbol_to_check = "MSFT" # Example ticker symbol
    generation_result = generator.generate_past_5_years_financial_report(symbol_to_check)

    if generation_result["success"]:
        print(generation_result["message"])
        report_df = generation_result["report_data"]
        print("Generated Report Data:")
        print(report_df)

        # --- Test Case 1.1: Saving to CSV ---
        print("\n--- Testing saving report to CSV ---")
        csv_filename = f"{symbol_to_check}_financials_5_years" # .csv will be appended
        save_result = generator.save_report_to_csv(report_df, csv_filename)
        print(save_result["message"])
    else:
        print(f"Error generating report: {generation_result['message']}")

    # --- Test Case 2: Invalid symbol (empty string) ---
    print("\n--- Testing with an empty symbol ---")
    empty_symbol = ""
    generation_result_empty = generator.generate_past_5_years_financial_report(empty_symbol)
    print(f"Result for empty symbol: {generation_result_empty['message']}")

    # --- Test Case 3: Invalid symbol (whitespace) ---
    print("\n--- Testing with a whitespace symbol ---")
    whitespace_symbol = "   "
    generation_result_whitespace = generator.generate_past_5_years_financial_report(whitespace_symbol)
    print(f"Result for whitespace symbol: {generation_result_whitespace['message']}")

    # --- Test Case 4: Invalid symbol (non-string) ---
    print("\n--- Testing with a non-string symbol ---")
    non_string_symbol = 12345
    generation_result_non_string = generator.generate_past_5_years_financial_report(non_string_symbol)
    print(f"Result for non-string symbol: {generation_result_non_string['message']}")

    # --- Test Case 5: Report generation failure (simulated with bad symbol) ---
    print("\n--- Testing report generation failure with a potentially invalid symbol ---")
    invalid_symbol = "INVALIDXYZ123" # May or may not cause a simulated error
    generation_result_invalid = generator.generate_past_5_years_financial_report(invalid_symbol)
    print(f"Result for '{invalid_symbol}': {generation_result_invalid['message']}")


    # --- Test Case 6: Invalid input for saving ---
    print("\n--- Testing invalid input for saving ---")
    # Assuming generation_result was successful in Test Case 1
    if generation_result["success"]:
        print("\nTesting saving with invalid DataFrame:")
        save_result_invalid_df = generator.save_report_to_csv(None, "test_invalid_df.csv")
        print(save_result_invalid_df["message"])

        save_result_empty_df = generator.save_report_to_csv(pd.DataFrame(), "test_empty_df.csv")
        print(save_result_empty_df["message"])

        print("\nTesting saving with invalid filename:")
        save_result_invalid_filename_type = generator.save_report_to_csv(report_df, 123)
        print(f"Save result (invalid filename type): {save_result_invalid_filename_type['message']}")

        save_result_invalid_filename_empty = generator.save_report_to_csv(report_df, "")
        print(f"Save result (empty filename): {save_result_invalid_filename_empty['message']}")

        save_result_invalid_filename_non_csv = generator.save_report_to_csv(report_df, "report.txt")
        print(f"Save result (non-csv extension): {save_result_invalid_filename_non_csv['message']}")

