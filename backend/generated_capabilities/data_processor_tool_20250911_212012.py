
import json
import csv
import pandas as pd
from typing import Dict, Any, List, Optional, Union
import requests
from datetime import datetime
import subprocess
import os

class DiskUsageAnalyzerTool:
    """
    Tool for analyzing disk usage patterns, generating optimization strategies,
    and performing cost analysis.
    """

    def __init__(self):
        self.disk_usage_data = None
        self.optimization_strategies = []
        self.cost_analysis_results = {}

    def _run_command(self, command: List[str]) -> Dict[str, Any]:
        """
        Executes a bash command and returns its output.
        Handles potential errors during command execution.
        """
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True, shell=False)
            return {"success": True, "stdout": result.stdout, "stderr": result.stderr}
        except subprocess.CalledProcessError as e:
            return {"success": False, "error": f"Command failed: {e.cmd}\nStderr: {e.stderr}\nStdout: {e.stdout}"}
        except FileNotFoundError:
            return {"success": False, "error": f"Command not found: {command[0]}"}
        except Exception as e:
            return {"success": False, "error": f"An unexpected error occurred: {str(e)}"}

    def gather_disk_usage_data(self, directory: str = "/", exclude_dirs: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Gathers detailed disk usage data for a given directory.
        Uses 'du' command for detailed analysis and 'df' for filesystem info.

        Args:
            directory (str): The directory to analyze disk usage for. Defaults to root '/'.
            exclude_dirs (Optional[List[str]]): A list of directories to exclude from analysis.

        Returns:
            Dict[str, Any]: A dictionary containing analysis results or an error message.
        """
        if not isinstance(directory, str) or not directory:
            return {"success": False, "error": "Invalid 'directory' provided. Must be a non-empty string."}
        if exclude_dirs is not None and not isinstance(exclude_dirs, list):
            return {"success": False, "error": "Invalid 'exclude_dirs' provided. Must be a list of strings."}

        # Validate directory existence
        if not os.path.isdir(directory):
            return {"success": False, "error": f"Directory '{directory}' not found or is not a directory."}

        exclude_options = []
        if exclude_dirs:
            for edir in exclude_dirs:
                if isinstance(edir, str) and edir:
                    exclude_options.extend(["--exclude", edir])
                else:
                    return {"success": False, "error": f"Invalid item in 'exclude_dirs': '{edir}'. All items must be non-empty strings."}

        # Gather filesystem information
        df_command = ["df", "-h", directory]
        df_result = self._run_command(df_command)
        if not df_result["success"]:
            return df_result

        # Gather detailed disk usage
        du_command = ["du", "-ah", directory] + exclude_options
        du_result = self._run_command(du_command)
        if not du_result["success"]:
            return du_result

        self.disk_usage_data = {
            "filesystem_info": df_result["stdout"],
            "detailed_usage": du_result["stdout"]
        }

        return {
            "success": True,
            "message": f"Disk usage data gathered for '{directory}'."
        }

    def parse_disk_usage(self) -> Dict[str, Any]:
        """
        Parses the raw disk usage data into a pandas DataFrame for easier analysis.
        """
        if self.disk_usage_data is None or "detailed_usage" not in self.disk_usage_data:
            return {"success": False, "error": "No disk usage data gathered yet. Call 'gather_disk_usage_data' first."}

        try:
            usage_lines = self.disk_usage_data["detailed_usage"].splitlines()
            data = []
            for line in usage_lines:
                if line:
                    size, path = line.split('\t', 1)
                    data.append({"size": size, "path": path})

            df = pd.DataFrame(data)

            # Convert size to numeric (handling 'K', 'M', 'G', 'T')
            def convert_size_to_bytes(size_str):
                size_str = size_str.strip()
                if not size_str:
                    return 0
                units = {"K": 1024, "M": 1024 ** 2, "G": 1024 ** 3, "T": 1024 ** 4}
                if size_str[-1].upper() in units:
                    num = float(size_str[:-1])
                    unit = size_str[-1].upper()
                    return num * units[unit]
                else:
                    try:
                        return float(size_str) # Assume bytes if no unit
                    except ValueError:
                        return 0 # Or handle as an error if preferred

            df['size_bytes'] = df['size'].apply(convert_size_to_bytes)
            df = df.sort_values(by='size_bytes', ascending=False)

            self.processed_disk_usage = df
            return {
                "success": True,
                "message": "Disk usage data parsed into DataFrame.",
                "rows": len(df),
                "columns": list(df.columns),
                "sample_data": df.head().to_dict('records')
            }
        except Exception as e:
            return {"success": False, "error": f"Error parsing disk usage data: {str(e)}"}

    def analyze_disk_usage_patterns(self) -> Dict[str, Any]:
        """
        Analyzes the parsed disk usage data to identify patterns and potential optimization areas.
        Identifies top N largest files/directories.
        """
        if not hasattr(self, 'processed_disk_usage') or self.processed_disk_usage is None:
            return {"success": False, "error": "No processed disk usage data available. Call 'parse_disk_usage' first."}

        try:
            df = self.processed_disk_usage
            top_n = 10  # Default to top 10

            # Identify top N largest files/directories
            top_files_dirs = df.head(top_n).to_dict('records')

            # Simple analysis of common large file types (e.g., log files, temp files)
            log_files = df[df['path'].str.contains(r'\.log$', case=False)]
            temp_files = df[df['path'].str.contains(r'(tmp|temp)/', case=False)]
            large_log_files = log_files[log_files['size_bytes'] > 100 * 1024 * 1024].to_dict('records') # > 100MB
            large_temp_files = temp_files[temp_files['size_bytes'] > 50 * 1024 * 1024].to_dict('records') # > 50MB

            analysis_results = {
                "top_largest_files_directories": top_files_dirs,
                "large_log_files": large_log_files,
                "large_temp_files": large_temp_files,
                "total_unique_paths": len(df),
                "total_disk_usage_bytes": df['size_bytes'].sum()
            }

            return {
                "success": True,
                "analysis": analysis_results,
                "message": "Disk usage patterns analyzed."
            }
        except Exception as e:
            return {"success": False, "error": f"Error analyzing disk usage patterns: {str(e)}"}

    def generate_optimization_strategies(self, threshold_mb: int = 500, log_retention_days: int = 30) -> Dict[str, Any]:
        """
        Generates optimization strategies based on analyzed disk usage patterns.

        Args:
            threshold_mb (int): Minimum size in MB for a file/directory to be considered for archival/deletion.
            log_retention_days (int): Number of days to retain log files before suggesting deletion.

        Returns:
            Dict[str, Any]: A dictionary containing optimization strategies.
        """
        if not hasattr(self, 'processed_disk_usage') or self.processed_disk_usage is None:
            return {"success": False, "error": "No processed disk usage data available. Call 'parse_disk_usage' first."}

        try:
            df = self.processed_disk_usage
            threshold_bytes = threshold_mb * 1024 * 1024
            self.optimization_strategies = []

            # Strategy 1: Identify large files/directories for potential cleanup or archival
            large_items = df[df['size_bytes'] >= threshold_bytes]
            if not large_items.empty:
                self.optimization_strategies.append({
                    "strategy_name": "Cleanup/Archive Large Items",
                    "description": f"Identify files and directories exceeding {threshold_mb}MB for potential cleanup or archival.",
                    "items_to_consider": large_items[['size', 'path']].to_dict('records')
                })

            # Strategy 2: Log file management
            log_files = df[df['path'].str.contains(r'\.log$', case=False)]
            # This part would ideally use file modification times, which 'du' doesn't directly provide.
            # For a more robust solution, one might need to integrate with file metadata tools or system logs.
            # For now, we'll flag large log files.
            large_log_files = log_files[log_files['size_bytes'] > 100 * 1024 * 1024] # Example: > 100MB
            if not large_log_files.empty:
                self.optimization_strategies.append({
                    "strategy_name": "Log File Management",
                    "description": f"Review log files. Consider implementing a retention policy (e.g., keep last {log_retention_days} days) and compressing or deleting old logs.",
                    "potential_actions": "Compress or delete log files older than {log_retention_days} days.",
                    "items_to_consider": large_log_files[['size', 'path']].to_dict('records')
                })

            # Strategy 3: Temporary file cleanup
            temp_files_dirs = df[df['path'].str.contains(r'(tmp|temp)/', case=False)]
            # Similar to logs, precise age would require more metadata. Flagging them.
            large_temp_files = temp_files_dirs[temp_files_dirs['size_bytes'] > 50 * 1024 * 1024] # Example: > 50MB
            if not large_temp_files.empty:
                self.optimization_strategies.append({
                    "strategy_name": "Temporary File Cleanup",
                    "description": "Regularly clean up temporary files and directories.",
                    "potential_actions": "Delete temporary files that are no longer needed.",
                    "items_to_consider": large_temp_files[['size', 'path']].to_dict('records')
                })

            # Strategy 4: Identify duplicate files (advanced, requires hashing)
            # This is computationally intensive and complex, so it's noted as a potential future enhancement.
            self.optimization_strategies.append({
                "strategy_name": "Duplicate File Detection (Advanced)",
                "description": "Implement a strategy to detect and remove duplicate files to reclaim space.",
                "potential_actions": "Use hashing algorithms to identify identical files and remove duplicates.",
                "note": "This is computationally intensive and not implemented in this version."
            })

            return {
                "success": True,
                "strategies": self.optimization_strategies,
                "message": "Optimization strategies generated."
            }
        except Exception as e:
            return {"success": False, "error": f"Error generating optimization strategies: {str(e)}"}

    def analyze_cost_implications(self, cloud_storage_cost_per_gb_per_month: float = 0.02,
                                 archive_storage_cost_per_gb_per_month: float = 0.005) -> Dict[str, Any]:
        """
        Analyzes the potential cost savings from implementing optimization strategies.

        Args:
            cloud_storage_cost_per_gb_per_month (float): Cost per GB per month for standard cloud storage.
            archive_storage_cost_per_gb_per_month (float): Cost per GB per month for archival cloud storage.

        Returns:
            Dict[str, Any]: A dictionary containing cost analysis results.
        """
        if not hasattr(self, 'processed_disk_usage') or self.processed_disk_usage is None:
            return {"success": False, "error": "No processed disk usage data available. Call 'parse_disk_usage' first."}
        if not self.optimization_strategies:
            return {"success": False, "error": "No optimization strategies generated. Call 'generate_optimization_strategies' first."}

        try:
            df = self.processed_disk_usage
            total_disk_usage_bytes = df['size_bytes'].sum()
            total_disk_usage_gb = total_disk_usage_bytes / (1024 ** 3)

            potential_savings = 0
            strategies_with_cost_impact = []

            for strategy in self.optimization_strategies:
                strategy_name = strategy.get("strategy_name")
                items_to_consider = strategy.get("items_to_consider", [])
                potential_storage_to_save_gb = 0

                if strategy_name == "Cleanup/Archive Large Items":
                    for item in items_to_consider:
                        size_bytes = self._convert_size_to_bytes(item['size'])
                        potential_storage_to_save_gb += size_bytes / (1024 ** 3)
                    cost_saving_per_month = potential_storage_to_save_gb * cloud_storage_cost_per_gb_per_month
                    strategies_with_cost_impact.append({
                        "strategy": strategy_name,
                        "potential_gb_saved": round(potential_storage_to_save_gb, 2),
                        "estimated_monthly_savings": round(cost_saving_per_month, 2),
                        "notes": f"Assumes these items can be deleted or moved to cheaper storage. Cost based on standard cloud storage rate."
                    })
                    potential_savings += cost_saving_per_month

                elif strategy_name == "Log File Management":
                    # A more precise analysis would involve filtering items_to_consider by age.
                    # For this example, we'll estimate based on the size of identified large logs.
                    for item in items_to_consider:
                        size_bytes = self._convert_size_to_bytes(item['size'])
                        potential_storage_to_save_gb += size_bytes / (1024 ** 3)
                    # Option 1: Moving to archive storage
                    cost_saving_moving_to_archive = potential_storage_to_save_gb * (cloud_storage_cost_per_gb_per_month - archive_storage_cost_per_gb_per_month)
                    # Option 2: Deleting old logs (complete savings) - This is more impactful if logs are truly obsolete.
                    # For simplicity, we'll estimate savings based on moving to archive, as deletion is a more extreme action.
                    strategies_with_cost_impact.append({
                        "strategy": strategy_name,
                        "potential_gb_saved": round(potential_storage_to_save_gb, 2),
                        "estimated_monthly_savings": round(cost_saving_moving_to_archive, 2),
                        "notes": f"Assumes log files can be moved to archive storage. Savings calculated as difference between standard and archive rates. Actual savings depend on how much can be deleted vs archived."
                    })
                    potential_savings += cost_saving_moving_to_archive

                elif strategy_name == "Temporary File Cleanup":
                    for item in items_to_consider:
                        size_bytes = self._convert_size_to_bytes(item['size'])
                        potential_storage_to_save_gb += size_bytes / (1024 ** 3)
                    cost_saving_per_month = potential_storage_to_save_gb * cloud_storage_cost_per_gb_per_month
                    strategies_with_cost_impact.append({
                        "strategy": strategy_name,
                        "potential_gb_saved": round(potential_storage_to_save_gb, 2),
                        "estimated_monthly_savings": round(cost_saving_per_month, 2),
                        "notes": "Assumes temporary files can be safely deleted. Savings calculated based on standard cloud storage rate."
                    })
                    potential_savings += cost_saving_per_month
                
                # Duplicate file detection is advanced, savings are hard to estimate without implementation.
                # if strategy_name == "Duplicate File Detection (Advanced)":
                #     # Placeholder for savings estimation once implemented.
                #     pass

            self.cost_analysis_results = {
                "total_disk_usage_gb": round(total_disk_usage_gb, 2),
                "estimated_total_monthly_savings": round(potential_savings, 2),
                "cost_analysis_per_strategy": strategies_with_cost_impact,
                "assumptions": {
                    "cloud_storage_cost_per_gb_per_month": cloud_storage_cost_per_gb_per_month,
                    "archive_storage_cost_per_gb_per_month": archive_storage_cost_per_gb_per_month
                }
            }

            return {
                "success": True,
                "cost_analysis": self.cost_analysis_results,
                "message": "Cost implications analyzed."
            }
        except Exception as e:
            return {"success": False, "error": f"Error analyzing cost implications: {str(e)}"}

    def _convert_size_to_bytes(self, size_str: str) -> float:
        """Helper to convert size string to bytes."""
        size_str = size_str.strip()
        if not size_str:
            return 0
        units = {"K": 1024, "M": 1024 ** 2, "G": 1024 ** 3, "T": 1024 ** 4}
        if size_str[-1].upper() in units:
            try:
                num = float(size_str[:-1])
                unit = size_str[-1].upper()
                return num * units[unit]
            except ValueError:
                return 0
        else:
            try:
                return float(size_str)
            except ValueError:
                return 0
