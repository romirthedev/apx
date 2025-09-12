
import json
import csv
import pandas as pd
from typing import Dict, Any, List, Optional, Union
import requests
from datetime import datetime
import subprocess
import os

class DiskOptimizerTool:
    """
    Tool for analyzing disk usage patterns, generating optimization strategies,
    and performing cost analysis.
    """

    def __init__(self):
        self.disk_usage_data = None
        self.optimization_plan = None
        self.cost_analysis = None
        self.default_threshold_large_files_gb = 1.0  # Default threshold for large files in GB
        self.default_retention_days = 30  # Default retention period for temporary files
        self.default_cost_per_gb_month = 0.02  # Default cost per GB per month for cloud storage

    def _run_command(self, command: str) -> Dict[str, Any]:
        """Executes a bash command and returns its output."""
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
            return {"success": True, "stdout": result.stdout.strip(), "stderr": result.stderr.strip()}
        except subprocess.CalledProcessError as e:
            return {"success": False, "error": f"Command '{command}' failed: {e.stderr.strip()}"}
        except FileNotFoundError:
            return {"success": False, "error": f"Command not found: {command.split()[0]}"}
        except Exception as e:
            return {"success": False, "error": f"An unexpected error occurred while running command '{command}': {str(e)}"}

    def collect_disk_usage_data(self, path: str = "/", exclude_paths: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Collects disk usage data using 'du' command.

        Args:
            path: The directory to start analyzing disk usage from. Defaults to '/'.
            exclude_paths: A list of paths to exclude from the analysis.

        Returns:
            A dictionary containing the success status, collected data, or an error message.
        """
        if not isinstance(path, str) or not path:
            return {"success": False, "error": "Invalid 'path' provided. Must be a non-empty string."}
        if exclude_paths is not None and not isinstance(exclude_paths, list):
            return {"success": False, "error": "Invalid 'exclude_paths' provided. Must be a list of strings."}

        command = f"du -ah --block-size=M '{path}'"
        if exclude_paths:
            exclude_string = " ".join([f"--exclude='{ep}'" for ep in exclude_paths])
            command = f"du -ah --block-size=M {exclude_string} '{path}'"

        result = self._run_command(command)

        if not result["success"]:
            return result

        data_lines = result["stdout"].splitlines()
        usage_data = []
        for line in data_lines:
            try:
                size_str, file_path = line.split('\t', 1)
                size_mb = float(size_str.strip('M'))
                usage_data.append({"path": file_path, "size_mb": size_mb})
            except ValueError:
                # Skip lines that don't conform to expected format
                continue

        self.disk_usage_data = pd.DataFrame(usage_data)
        if self.disk_usage_data.empty:
            return {"success": False, "error": "No disk usage data collected. The path might be empty or inaccessible."}

        self.disk_usage_data.sort_values(by="size_mb", ascending=False, inplace=True)
        return {
            "success": True,
            "message": f"Collected disk usage data for '{path}' ({len(self.disk_usage_data)} entries).",
            "rows": len(self.disk_usage_data),
            "columns": list(self.disk_usage_data.columns),
            "sample_data": self.disk_usage_data.head().to_dict('records')
        }

    def analyze_disk_usage(self, large_file_threshold_gb: float = None) -> Dict[str, Any]:
        """
        Analyzes the collected disk usage data to identify large files and directories.

        Args:
            large_file_threshold_gb: The threshold in GB above which files/dirs are considered "large".
                                     If None, uses the default_large_files_threshold_gb.

        Returns:
            A dictionary containing the success status and analysis results.
        """
        if self.disk_usage_data is None or self.disk_usage_data.empty:
            return {"success": False, "error": "No disk usage data loaded. Please run 'collect_disk_usage_data' first."}

        if large_file_threshold_gb is not None:
            if not isinstance(large_file_threshold_gb, (int, float)) or large_file_threshold_gb <= 0:
                return {"success": False, "error": "Invalid 'large_file_threshold_gb'. Must be a positive number."}
            threshold_mb = large_file_threshold_gb * 1024
        else:
            threshold_mb = self.default_threshold_large_files_gb * 1024

        large_files = self.disk_usage_data[self.disk_usage_data["size_mb"] >= threshold_mb]

        analysis_results = {
            "total_entries_analyzed": len(self.disk_usage_data),
            "total_disk_usage_mb": self.disk_usage_data["size_mb"].sum(),
            "num_large_files_or_dirs": len(large_files),
            "threshold_for_large_files_gb": threshold_mb / 1024,
            "large_files_or_dirs": large_files.to_dict('records')
        }

        self.processed_data = analysis_results # For potential future generic data processing

        return {
            "success": True,
            "message": "Disk usage analysis completed.",
            "analysis": analysis_results
        }

    def create_optimization_strategy(
        self,
        large_file_threshold_gb: float = None,
        temp_file_retention_days: int = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Creates a detailed optimization strategy based on disk usage analysis.

        Args:
            large_file_threshold_gb: Threshold for considering files/directories large.
                                     If None, uses default.
            temp_file_retention_days: Number of days to retain temporary files.
                                      If None, uses default.
            exclude_patterns: A list of file patterns (e.g., '*.tmp', '*.log') to consider for deletion
                              if they are older than the retention period.

        Returns:
            A dictionary containing the success status and the optimization plan.
        """
        if self.disk_usage_data is None or self.disk_usage_data.empty:
            return {"success": False, "error": "No disk usage data loaded. Please run 'collect_disk_usage_data' first."}

        # Validate inputs
        if large_file_threshold_gb is not None and (not isinstance(large_file_threshold_gb, (int, float)) or large_file_threshold_gb <= 0):
            return {"success": False, "error": "Invalid 'large_file_threshold_gb'. Must be a positive number."}
        if temp_file_retention_days is not None and (not isinstance(temp_file_retention_days, int) or temp_file_retention_days <= 0):
            return {"success": False, "error": "Invalid 'temp_file_retention_days'. Must be a positive integer."}
        if exclude_patterns is not None and not isinstance(exclude_patterns, list):
            return {"success": False, "error": "Invalid 'exclude_patterns' provided. Must be a list of strings."}
        for pattern in exclude_patterns if exclude_patterns else []:
            if not isinstance(pattern, str) or not pattern:
                return {"success": False, "error": "Invalid pattern in 'exclude_patterns'. Each pattern must be a non-empty string."}


        # Set thresholds
        effective_large_file_threshold_mb = (large_file_threshold_gb * 1024) if large_file_threshold_gb else (self.default_threshold_large_files_gb * 1024)
        effective_retention_days = temp_file_retention_days if temp_file_retention_days else self.default_retention_days

        optimization_steps = []

        # Strategy 1: Identify and suggest deletion of large files/directories
        large_files_df = self.disk_usage_data[self.disk_usage_data["size_mb"] >= effective_large_file_threshold_mb]
        if not large_files_df.empty:
            optimization_steps.append({
                "strategy_type": "identify_large_files_or_dirs",
                "description": f"Identify files/directories larger than {effective_large_file_threshold_mb/1024:.2f} GB for potential review and deletion.",
                "details": large_files_df.to_dict('records')
            })

        # Strategy 2: Identify and suggest deletion of old temporary/log files
        # This requires executing commands and is more complex. For now, we'll list common patterns.
        # A more sophisticated approach would involve parsing file modification times.
        potential_temp_files = []
        if exclude_patterns:
            for pattern in exclude_patterns:
                # This is a simplified approach. A real implementation would need to
                # find files matching patterns and check their modification times.
                # For demonstration, we'll assume these patterns can be found.
                # Example: find / -type f \( -name "*.tmp" -o -name "*.log" \) -mtime +30 -delete
                potential_temp_files.append({
                    "pattern": pattern,
                    "suggested_action": f"Review and delete files matching '{pattern}' older than {effective_retention_days} days."
                })
            if potential_temp_files:
                optimization_steps.append({
                    "strategy_type": "delete_old_temp_or_log_files",
                    "description": f"Identify and delete temporary or log files older than {effective_retention_days} days.",
                    "details": potential_temp_files
                })
        else:
             optimization_steps.append({
                "strategy_type": "delete_old_temp_or_log_files",
                "description": "No specific patterns provided for temporary/log file deletion. Consider defining patterns like '*.tmp', '*.log' for future analysis.",
                "details": []
            })


        # Strategy 3: Suggest archiving old but necessary data
        # This is a strategic suggestion, not directly executable by this tool.
        optimization_steps.append({
            "strategy_type": "archive_old_data",
            "description": "Consider archiving older, less frequently accessed data to cheaper storage solutions (e.g., cloud archival storage).",
            "details": {
                "recommendation": "Identify data older than X months/years that is not actively used and move it to archival storage."
            }
        })

        # Strategy 4: Suggest cloud storage tiering if applicable (conceptual)
        optimization_steps.append({
            "strategy_type": "cloud_storage_tiering",
            "description": "If using cloud storage, explore different storage tiers (e.g., Standard, Infrequent Access, Archive) based on data access patterns.",
            "details": {
                "recommendation": "Analyze data access frequency and move infrequently accessed data to lower-cost tiers."
            }
        })


        self.optimization_plan = optimization_steps
        return {
            "success": True,
            "message": "Optimization strategy created.",
            "optimization_plan": self.optimization_plan
        }

    def perform_cost_analysis(
        self,
        cost_per_gb_month: Optional[float] = None,
        storage_policy: Optional[Dict[str, Any]] = None,
        optimization_plan: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Performs a cost analysis based on current disk usage and potential savings from optimizations.

        Args:
            cost_per_gb_month: The cost of 1GB of storage per month. If None, uses default.
            storage_policy: A dictionary defining different storage tiers and their costs.
                            Example: {"standard": {"cost_per_gb_month": 0.02, "tiers": ["hot"]},
                                      "infrequent_access": {"cost_per_gb_month": 0.01, "tiers": ["cool"]},
                                      "archive": {"cost_per_gb_month": 0.001, "tiers": ["cold"]}}
                            If None, a simplified analysis is performed using 'cost_per_gb_month'.
            optimization_plan: The previously generated optimization plan. If None, uses self.optimization_plan.

        Returns:
            A dictionary containing the success status and cost analysis results.
        """
        if self.disk_usage_data is None or self.disk_usage_data.empty:
            return {"success": False, "error": "No disk usage data loaded. Please run 'collect_disk_usage_data' first."}

        effective_cost_per_gb_month = cost_per_gb_month if cost_per_gb_month is not None else self.default_cost_per_gb_month
        if not isinstance(effective_cost_per_gb_month, (int, float)) or effective_cost_per_gb_month < 0:
            return {"success": False, "error": "Invalid 'cost_per_gb_month'. Must be a non-negative number."}

        if optimization_plan is None:
            optimization_plan = self.optimization_plan

        if optimization_plan is None:
            return {"success": False, "error": "No optimization plan provided or generated. Please run 'create_optimization_strategy' first."}

        current_total_usage_mb = self.disk_usage_data["size_mb"].sum()
        current_monthly_cost = current_total_usage_mb * effective_cost_per_gb_month

        potential_savings_mb = 0
        optimized_usage_mb = current_total_usage_mb
        detailed_savings_breakdown = []

        # Analyze savings from identified optimization strategies
        for strategy in optimization_plan:
            strategy_type = strategy.get("strategy_type")
            details = strategy.get("details", {})

            if strategy_type == "identify_large_files_or_dirs":
                if isinstance(details, list):
                    for item in details:
                        size_mb = item.get("size_mb", 0)
                        if size_mb > 0:
                            # Assume 100% potential saving for demonstration
                            # In a real scenario, this would be a configurable percentage or user decision
                            saving_mb = size_mb * 1.0
                            potential_savings_mb += saving_mb
                            optimized_usage_mb -= saving_mb
                            detailed_savings_breakdown.append({
                                "strategy": strategy_type,
                                "item": item.get("path", "N/A"),
                                "potential_saving_mb": saving_mb,
                                "reason": "Large file/directory identified and assumed for deletion/archival."
                            })

            elif strategy_type == "delete_old_temp_or_log_files":
                if isinstance(details, list):
                    # This part is tricky without direct file system access to check modification times.
                    # We'll simulate based on the general idea of temporary files being deletable.
                    # A more robust solution would execute `find` commands and parse their output.
                    # For now, we'll make an assumption for demonstration.
                    # A common pattern is to assume a percentage of temp files can be deleted.
                    # For this demo, let's assume 50% of files matching patterns can be deleted if they exist.
                    # This requires access to the `disk_usage_data` to find matching files.
                    # This is a placeholder and needs refinement with actual file system interaction.
                    # For example: if self.disk_usage_data contains a 'pattern' column.
                    pass # Further refinement needed here

            # Add other strategy types for cost analysis if they directly impact storage size

        # Ensure optimized usage doesn't go below zero
        optimized_usage_mb = max(0, optimized_usage_mb)

        # Calculate optimized monthly cost
        optimized_monthly_cost = optimized_usage_mb * effective_cost_per_gb_month

        # Calculate total potential savings
        total_potential_savings_monthly = current_monthly_cost - optimized_monthly_cost

        # If storage policy is provided, perform tiered cost analysis
        if storage_policy and isinstance(storage_policy, dict):
            detailed_tiered_analysis = []
            tiered_current_cost = 0
            tiered_optimized_cost = 0
            actual_optimized_usage_by_tier = {tier_name: 0 for tier_name in storage_policy}
            remaining_optimized_usage = optimized_usage_mb # for allocation if policy is not fully defined

            # Simplified allocation: assume large files would go to archive, others standard
            # A real-world scenario would need more sophisticated logic
            for item in detailed_savings_breakdown:
                if item["strategy"] == "identify_large_files_or_dirs":
                    path_info = next((d for d in optimization_plan if d.get("strategy_type") == "identify_large_files_or_dirs"), {}).get("details", [])
                    original_item = next((i for i in path_info if i.get("path") == item.get("item")), None)
                    if original_item:
                        size_mb = original_item.get("size_mb", 0)
                        if size_mb > 0:
                            # Assign to archive tier as an example
                            archive_tier = next((tier_name for tier_name, config in storage_policy.items() if "archive" in config.get("tiers", [])), None)
                            if archive_tier:
                                actual_optimized_usage_by_tier[archive_tier] += size_mb
                                detailed_tiered_analysis.append({
                                    "item": item.get("item"),
                                    "original_size_mb": size_mb,
                                    "assigned_tier": archive_tier,
                                    "cost_per_gb_month": storage_policy[archive_tier].get("cost_per_gb_month", self.default_cost_per_gb_month)
                                })
                                remaining_optimized_usage -= size_mb
                            else: # Fallback to standard if archive tier not defined
                                standard_tier = next((tier_name for tier_name, config in storage_policy.items() if "standard" in config.get("tiers", [])), None)
                                if standard_tier:
                                    actual_optimized_usage_by_tier[standard_tier] += size_mb
                                    detailed_tiered_analysis.append({
                                        "item": item.get("item"),
                                        "original_size_mb": size_mb,
                                        "assigned_tier": standard_tier,
                                        "cost_per_gb_month": storage_policy[standard_tier].get("cost_per_gb_month", self.default_cost_per_gb_month)
                                    })
                                    remaining_optimized_usage -= size_mb


            # Allocate remaining optimized usage to a default tier (e.g., standard)
            standard_tier_name = next((tier_name for tier_name, config in storage_policy.items() if "standard" in config.get("tiers", [])), None)
            if standard_tier_name and remaining_optimized_usage > 0:
                actual_optimized_usage_by_tier[standard_tier_name] += remaining_optimized_usage
                detailed_tiered_analysis.append({
                    "item": "Remaining unassigned optimized usage",
                    "original_size_mb": remaining_optimized_usage,
                    "assigned_tier": standard_tier_name,
                    "cost_per_gb_month": storage_policy[standard_tier_name].get("cost_per_gb_month", self.default_cost_per_gb_month)
                })


            # Calculate current tiered costs (simplified: assume all is standard for current)
            current_standard_tier = next((tier_name for tier_name, config in storage_policy.items() if "standard" in config.get("tiers", [])), None)
            if current_standard_tier:
                current_monthly_cost_tiered = current_total_usage_mb * storage_policy[current_standard_tier].get("cost_per_gb_month", self.default_cost_per_gb_month)
                detailed_tiered_analysis.insert(0, {
                    "item": "Current Total Usage",
                    "original_size_mb": current_total_usage_mb,
                    "assigned_tier": current_standard_tier,
                    "cost_per_gb_month": storage_policy[current_standard_tier].get("cost_per_gb_month", self.default_cost_per_gb_month)
                })
            else:
                current_monthly_cost_tiered = current_monthly_cost # fallback if no standard tier defined

            # Calculate optimized tiered costs
            for tier_name, tier_data in storage_policy.items():
                tier_usage = actual_optimized_usage_by_tier.get(tier_name, 0)
                tier_cost = tier_data.get("cost_per_gb_month", self.default_cost_per_gb_month)
                tiered_optimized_cost += tier_usage * tier_cost

            total_potential_savings_tiered = current_monthly_cost_tiered - tiered_optimized_cost
            detailed_savings_breakdown.extend([
                {"strategy": "tiered_storage_allocation", "item": "Tiered Storage Savings", "potential_saving_mb": 0, "reason": f"Optimized storage tiering"}
            ])


            return {
                "success": True,
                "message": "Cost analysis with tiered storage policy completed.",
                "cost_analysis": {
                    "current_monthly_cost": current_monthly_cost_tiered,
                    "optimized_monthly_cost": tiered_optimized_cost,
                    "total_potential_monthly_savings": total_potential_savings_tiered,
                    "storage_policy_used": storage_policy,
                    "current_usage_mb": current_total_usage_mb,
                    "optimized_usage_mb": optimized_usage_mb,
                    "detailed_tiered_allocation": detailed_tiered_analysis,
                    "detailed_savings_breakdown": detailed_savings_breakdown
                }
            }
        else:
            # Simplified cost analysis without storage policy
            return {
                "success": True,
                "message": "Simplified cost analysis completed.",
                "cost_analysis": {
                    "current_monthly_cost": current_monthly_cost,
                    "optimized_monthly_cost": optimized_monthly_cost,
                    "total_potential_monthly_savings": total_potential_savings_monthly,
                    "cost_per_gb_month_used": effective_cost_per_gb_month,
                    "current_usage_mb": current_total_usage_mb,
                    "optimized_usage_mb": optimized_usage_mb,
                    "detailed_savings_breakdown": detailed_savings_breakdown
                }
            }

    def _save_to_csv(self, data: Union[pd.DataFrame, Dict[str, Any]], filename: str) -> Dict[str, Any]:
        """Saves data to a CSV file."""
        try:
            if isinstance(data, pd.DataFrame):
                df_to_save = data
            elif isinstance(data, dict):
                # Attempt to convert dict to DataFrame, expecting a list of records or a structured dict
                if any(isinstance(v, list) for v in data.values()):
                    df_to_save = pd.DataFrame.from_dict(data, orient='index' if not all(isinstance(v, list) for v in data.values()) else 'columns')
                else:
                    df_to_save = pd.DataFrame([data]) # Single record dict
            else:
                return {"success": False, "error": "Unsupported data type for CSV saving. Must be DataFrame or Dict."}

            if df_to_save.empty:
                return {"success": False, "error": "No data to save to CSV."}

            df_to_save.to_csv(filename, index=False)
            return {"success": True, "message": f"Data successfully saved to {filename}"}
        except Exception as e:
            return {"success": False, "error": f"Failed to save data to CSV: {str(e)}"}

    def save_disk_usage_data(self, filename: str = "disk_usage_data.csv") -> Dict[str, Any]:
        """Saves the collected disk usage data to a CSV file."""
        if self.disk_usage_data is None or self.disk_usage_data.empty:
            return {"success": False, "error": "No disk usage data to save. Please collect data first."}
        return self._save_to_csv(self.disk_usage_data, filename)

    def save_optimization_plan(self, filename: str = "optimization_plan.json") -> Dict[str, Any]:
        """Saves the generated optimization plan to a JSON file."""
        if self.optimization_plan is None:
            return {"success": False, "error": "No optimization plan to save. Please generate one first."}
        try:
            with open(filename, 'w') as f:
                json.dump(self.optimization_plan, f, indent=4)
            return {"success": True, "message": f"Optimization plan successfully saved to {filename}"}
        except Exception as e:
            return {"success": False, "error": f"Failed to save optimization plan to JSON: {str(e)}"}

    def save_cost_analysis(self, filename: str = "cost_analysis.json") -> Dict[str, Any]:
        """Saves the generated cost analysis to a JSON file."""
        if self.cost_analysis is None:
            return {"success": False, "error": "No cost analysis to save. Please perform one first."}
        try:
            with open(filename, 'w') as f:
                json.dump(self.cost_analysis, f, indent=4)
            return {"success": True, "message": f"Cost analysis successfully saved to {filename}"}
        except Exception as e:
            return {"success": False, "error": f"Failed to save cost analysis to JSON: {str(e)}"}


# Example Usage (for demonstration purposes, not part of the tool class)
if __name__ == "__main__":
    optimizer = DiskOptimizerTool()

    # --- Step 1: Collect Disk Usage Data ---
    print("--- Collecting Disk Usage Data ---")
    # Use a smaller path for quicker testing, e.g., your home directory or a specific project
    # For root, be cautious and use exclusions
    # collect_result = optimizer.collect_disk_usage_data(path="/", exclude_paths=["/proc", "/sys", "/dev", "/run"])
    # For demonstration, let's use a temporary directory if it exists or a smaller path
    test_path = "." # Current directory
    if os.path.exists("/tmp"):
        test_path = "/tmp"
        print(f"Using /tmp for demonstration. Consider using 'exclude_paths' for a full system scan.")
        collect_result = optimizer.collect_disk_usage_data(path=test_path, exclude_paths=["/tmp/snap", "/tmp/systemd-private-*"])
    else:
        collect_result = optimizer.collect_disk_usage_data(path=test_path)

    if collect_result["success"]:
        print(collect_result["message"])
        print(f"Sample data: {collect_result['sample_data']}")

        # --- Step 2: Analyze Disk Usage ---
        print("\n--- Analyzing Disk Usage ---")
        # Analyze for files larger than 100MB
        analyze_result = optimizer.analyze_disk_usage(large_file_threshold_gb=0.1)
        if analyze_result["success"]:
            print(analyze_result["message"])
            print("Analysis Results:", json.dumps(analyze_result["analysis"], indent=2))

            # --- Step 3: Create Optimization Strategy ---
            print("\n--- Creating Optimization Strategy ---")
            # Specify temporary file patterns and retention
            strategy_result = optimizer.create_optimization_strategy(
                large_file_threshold_gb=0.1,
                temp_file_retention_days=7,
                exclude_patterns=["*.tmp", "*.log", "*.bak"]
            )
            if strategy_result["success"]:
                print(strategy_result["message"])
                print("Optimization Plan:", json.dumps(strategy_result["optimization_plan"], indent=2))

                # --- Step 4: Perform Cost Analysis ---
                print("\n--- Performing Cost Analysis ---")
                # Define a sample storage policy
                sample_storage_policy = {
                    "standard_storage": {"cost_per_gb_month": 0.02, "tiers": ["hot"]},
                    "infrequent_access": {"cost_per_gb_month": 0.01, "tiers": ["cool"]},
                    "archive_storage": {"cost_per_gb_month": 0.001, "tiers": ["cold"]}
                }

                cost_result = optimizer.perform_cost_analysis(
                    cost_per_gb_month=0.02, # Example base cost
                    storage_policy=sample_storage_policy,
                    optimization_plan=strategy_result["optimization_plan"] # Pass the generated plan
                )
                if cost_result["success"]:
                    print(cost_result["message"])
                    print("Cost Analysis Results:", json.dumps(cost_result["cost_analysis"], indent=2))

                    # --- Step 5: Save Results ---
                    print("\n--- Saving Results ---")
                    save_disk_usage_result = optimizer.save_disk_usage_data("disk_usage_output.csv")
                    print(f"Save disk usage data: {save_disk_usage_result['message'] if save_disk_usage_result['success'] else save_disk_usage_result['error']}")

                    save_plan_result = optimizer.save_optimization_plan("optimization_plan_output.json")
                    print(f"Save optimization plan: {save_plan_result['message'] if save_plan_result['success'] else save_plan_result['error']}")

                    save_cost_result = optimizer.save_cost_analysis("cost_analysis_output.json")
                    print(f"Save cost analysis: {save_cost_result['message'] if save_cost_result['success'] else save_cost_result['error']}")

                else:
                    print("Cost analysis failed:", cost_result["error"])
            else:
                print("Optimization strategy creation failed:", strategy_result["error"])
        else:
            print("Disk usage analysis failed:", analyze_result["error"])
    else:
        print("Disk usage data collection failed:", collect_result["error"])

