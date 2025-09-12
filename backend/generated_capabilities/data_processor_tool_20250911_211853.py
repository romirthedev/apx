
import json
import csv
import pandas as pd
from typing import Dict, Any, List, Optional, Union
import requests
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PerformanceAnalyzerTool:
    """
    Tool for analyzing system performance metrics and creating optimization recommendations
    with implementation plans. This tool is designed to integrate with external systems
    or models for advanced analysis and recommendation generation.
    """

    def __init__(self, recommendation_api_url: Optional[str] = None, analysis_api_url: Optional[str] = None):
        """
        Initializes the PerformanceAnalyzerTool.

        Args:
            recommendation_api_url: URL of an external API for generating recommendations.
            analysis_api_url: URL of an external API for performing advanced performance analysis.
        """
        self.performance_data: Optional[pd.DataFrame] = None
        self.recommendation_api_url = recommendation_api_url
        self.analysis_api_url = analysis_api_url
        logging.info("PerformanceAnalyzerTool initialized.")

    def _validate_filepath(self, filepath: str):
        """Validates if the provided filepath is a non-empty string."""
        if not isinstance(filepath, str) or not filepath:
            raise ValueError("Filepath must be a non-empty string.")

    def _validate_data_loaded(self):
        """Checks if any data has been loaded."""
        if self.performance_data is None:
            raise RuntimeError("No performance data loaded. Please load data first using 'load_performance_data'.")

    def load_performance_data(self, filepath: str, data_format: str = 'csv') -> Dict[str, Any]:
        """
        Load system performance metrics from a file. Supports CSV and JSON formats.

        Args:
            filepath: The path to the data file.
            data_format: The format of the data file ('csv' or 'json'). Defaults to 'csv'.

        Returns:
            A dictionary containing the status, number of rows, columns, sample data, and a message.
        """
        try:
            self._validate_filepath(filepath)
            logging.info(f"Attempting to load data from {filepath} in {data_format} format.")

            if data_format.lower() == 'csv':
                df = pd.read_csv(filepath)
            elif data_format.lower() == 'json':
                df = pd.read_json(filepath)
            else:
                raise ValueError("Unsupported data format. Please use 'csv' or 'json'.")

            if df.empty:
                logging.warning(f"Data file {filepath} is empty.")
                return {"success": False, "message": f"Data file {filepath} is empty."}

            self.performance_data = df
            logging.info(f"Successfully loaded {len(df)} rows from {filepath}.")
            return {
                "success": True,
                "rows": len(df),
                "columns": list(df.columns),
                "sample_data": df.head(5).to_dict('records'),
                "message": f"Loaded {len(df)} rows from {filepath}"
            }
        except FileNotFoundError:
            logging.error(f"Error loading data: File not found at {filepath}")
            return {"success": False, "error": f"File not found at {filepath}"}
        except ValueError as ve:
            logging.error(f"Error loading data: Invalid input - {ve}")
            return {"success": False, "error": str(ve)}
        except Exception as e:
            logging.error(f"An unexpected error occurred while loading data from {filepath}: {e}")
            return {"success": False, "error": f"An unexpected error occurred: {str(e)}"}

    def basic_performance_analysis(self) -> Dict[str, Any]:
        """
        Performs basic descriptive analysis on the loaded performance data.

        Returns:
            A dictionary containing analysis results like shape, data types, missing values,
            and summary statistics for numeric columns.
        """
        try:
            self._validate_data_loaded()
            df = self.performance_data
            logging.info("Performing basic performance data analysis.")

            analysis = {
                "shape": df.shape,
                "columns": list(df.columns),
                "data_types": df.dtypes.apply(lambda x: x.name).to_dict(), # More readable data types
                "missing_values_count": df.isnull().sum().to_dict(),
                "missing_values_percentage": (df.isnull().sum() / len(df) * 100).round(2).to_dict()
            }

            numeric_df = df.select_dtypes(include=['number'])
            if not numeric_df.empty:
                analysis["numeric_summary"] = numeric_df.describe().to_dict()
            else:
                analysis["numeric_summary"] = "No numeric columns found for statistical summary."

            logging.info("Basic performance analysis completed.")
            return {
                "success": True,
                "analysis": analysis,
                "message": "Basic performance data analysis completed."
            }
        except RuntimeError as re:
            logging.error(re)
            return {"success": False, "error": str(re)}
        except Exception as e:
            logging.error(f"An unexpected error occurred during basic analysis: {e}")
            return {"success": False, "error": f"An unexpected error occurred: {str(e)}"}

    def filter_performance_data(self, conditions: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filters the loaded performance data based on specified conditions.

        Args:
            conditions: A dictionary where keys are column names and values are conditions.
                        Conditions can be a single value, or a dictionary with 'min', 'max', 'equals', 'isin'.
                        Example: {'CPU_Usage': {'min': 50, 'max': 90}, 'Status': 'Error'}

        Returns:
            A dictionary containing the status, number of filtered rows, original rows,
            and a sample of the filtered data.
        """
        try:
            self._validate_data_loaded()
            if not isinstance(conditions, dict) or not conditions:
                raise ValueError("Conditions must be a non-empty dictionary.")

            df = self.performance_data.copy()
            original_rows = len(df)
            logging.info(f"Applying filters: {conditions}")

            for column, condition in conditions.items():
                if column not in df.columns:
                    logging.warning(f"Column '{column}' not found in the data. Skipping filter for this column.")
                    continue

                if isinstance(condition, dict):
                    if 'min' in condition:
                        min_val = condition['min']
                        if pd.api.types.is_numeric_dtype(df[column]):
                            df = df[df[column] >= min_val]
                        else:
                            logging.warning(f"Cannot apply 'min' filter on non-numeric column '{column}'. Skipping.")
                    if 'max' in condition:
                        max_val = condition['max']
                        if pd.api.types.is_numeric_dtype(df[column]):
                            df = df[df[column] <= max_val]
                        else:
                            logging.warning(f"Cannot apply 'max' filter on non-numeric column '{column}'. Skipping.")
                    if 'equals' in condition:
                        df = df[df[column] == condition['equals']]
                    if 'isin' in condition and isinstance(condition['isin'], list):
                        df = df[df[column].isin(condition['isin'])]
                    if 'not_equals' in condition:
                         df = df[df[column] != condition['not_equals']]
                    if 'not_isin' in condition and isinstance(condition['not_isin'], list):
                        df = df[~df[column].isin(condition['not_isin'])]
                else:
                    # Direct equality check for non-dict conditions
                    df = df[df[column] == condition]

            filtered_rows = len(df)
            logging.info(f"Filtering complete. Reduced to {filtered_rows} rows from {original_rows}.")
            return {
                "success": True,
                "filtered_rows": filtered_rows,
                "original_rows": original_rows,
                "filtered_data_sample": df.head(10).to_dict('records'),
                "message": f"Filtered to {filtered_rows} rows."
            }
        except RuntimeError as re:
            logging.error(re)
            return {"success": False, "error": str(re)}
        except ValueError as ve:
            logging.error(f"Invalid input for filtering: {ve}")
            return {"success": False, "error": str(ve)}
        except Exception as e:
            logging.error(f"An unexpected error occurred during filtering: {e}")
            return {"success": False, "error": f"An unexpected error occurred: {str(e)}"}

    def analyze_system_performance_with_ai(self, analysis_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Uses an external AI service to perform advanced analysis of system performance metrics.
        This requires the `analysis_api_url` to be configured.

        Args:
            analysis_params: Optional dictionary of parameters to pass to the analysis API.

        Returns:
            A dictionary containing the analysis results and recommendations from the AI service.
        """
        if not self.analysis_api_url:
            logging.error("Analysis API URL is not configured. Cannot perform AI-driven analysis.")
            return {
                "success": False,
                "error": "AI-driven analysis is not configured. Please set the 'analysis_api_url' parameter during initialization."
            }
        try:
            self._validate_data_loaded()
            if self.performance_data is None:
                return {"success": False, "error": "No performance data loaded to analyze."}

            logging.info(f"Sending performance data for AI-driven analysis to {self.analysis_api_url}")

            # Prepare data for API call. Convert DataFrame to a suitable format (e.g., list of dicts).
            data_payload = self.performance_data.to_dict(orient='records')

            response = requests.post(self.analysis_api_url, json={"data": data_payload, "params": analysis_params})
            response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

            result = response.json()
            logging.info("AI-driven analysis completed successfully.")
            return result # Expecting the API to return a structured JSON with analysis and recommendations

        except RuntimeError as re:
            logging.error(re)
            return {"success": False, "error": str(re)}
        except requests.exceptions.RequestException as req_err:
            logging.error(f"Error communicating with the analysis API: {req_err}")
            return {"success": False, "error": f"Failed to connect to analysis API: {req_err}"}
        except json.JSONDecodeError:
            logging.error("Failed to decode JSON response from analysis API.")
            return {"success": False, "error": "Invalid JSON response received from analysis API."}
        except Exception as e:
            logging.error(f"An unexpected error occurred during AI-driven analysis: {e}")
            return {"success": False, "error": f"An unexpected error occurred: {str(e)}"}

    def generate_optimization_recommendations(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates optimization recommendations and implementation plans using an external AI service.
        This requires the `recommendation_api_url` to be configured.
        This function acts as a wrapper to call the recommendation API.

        Args:
            analysis_results: The output from a previous analysis step (e.g., from `analyze_system_performance_with_ai`
                              or a direct analysis result).

        Returns:
            A dictionary containing optimization recommendations and implementation plans.
        """
        if not self.recommendation_api_url:
            logging.error("Recommendation API URL is not configured. Cannot generate recommendations.")
            return {
                "success": False,
                "error": "Recommendation generation is not configured. Please set the 'recommendation_api_url' parameter during initialization."
            }
        try:
            if not isinstance(analysis_results, dict):
                raise ValueError("Analysis results must be provided as a dictionary.")

            logging.info(f"Sending analysis results for recommendation generation to {self.recommendation_api_url}")

            response = requests.post(self.recommendation_api_url, json={"analysis_results": analysis_results})
            response.raise_for_status()

            result = response.json()
            logging.info("Optimization recommendations generated successfully.")
            return result

        except RuntimeError as re:
            logging.error(re)
            return {"success": False, "error": str(re)}
        except ValueError as ve:
            logging.error(f"Invalid input for generating recommendations: {ve}")
            return {"success": False, "error": str(ve)}
        except requests.exceptions.RequestException as req_err:
            logging.error(f"Error communicating with the recommendation API: {req_err}")
            return {"success": False, "error": f"Failed to connect to recommendation API: {req_err}"}
        except json.JSONDecodeError:
            logging.error("Failed to decode JSON response from recommendation API.")
            return {"success": False, "error": "Invalid JSON response received from recommendation API."}
        except Exception as e:
            logging.error(f"An unexpected error occurred during recommendation generation: {e}")
            return {"success": False, "error": f"An unexpected error occurred: {str(e)}"}

    def provide_optimization_plan(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        A convenience method to perform both advanced analysis and generate recommendations.
        This will first call `analyze_system_performance_with_ai` and then pass its output
        to `generate_optimization_recommendations`.

        Args:
            analysis_results: The output from a previous analysis step.

        Returns:
            A dictionary containing the final optimization recommendations and implementation plans.
        """
        logging.info("Executing comprehensive optimization plan generation.")
        analysis_response = self.analyze_system_performance_with_ai()

        if not analysis_response.get("success", False):
            logging.error("Failed to perform advanced analysis. Cannot proceed to generate recommendations.")
            return analysis_response # Return the error from the analysis step

        # Assuming analysis_results from the AI model is directly usable or needs minor adaptation
        # For this example, we'll pass the entire analysis_response as 'analysis_results' to the next step
        # In a real scenario, you might need to extract specific parts if the API expects them.
        recommendation_response = self.generate_optimization_recommendations(analysis_response)

        if not recommendation_response.get("success", False):
            logging.error("Failed to generate recommendations.")
            return recommendation_response # Return the error from the recommendation step

        return recommendation_response

