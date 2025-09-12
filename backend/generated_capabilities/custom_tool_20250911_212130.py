
import time
import statistics
import subprocess
import platform
import json
from typing import Dict, Any, List, Optional, Union, Callable
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

class PerformanceBenchmarker:
    """
    A specialized tool for generating detailed performance benchmarking reports
    with comparative analysis and trends.

    This class provides methods to:
    - Measure execution time of code snippets and system commands.
    - Collect system-level metrics during runs.
    - Analyze and compare performance metrics across multiple runs.
    - Identify performance trends over time.
    - Generate structured reports with visualizations.

    Utilizes libraries like pandas, numpy, matplotlib, and seaborn for advanced analysis and reporting.
    """

    def __init__(self):
        """
        Initializes the PerformanceBenchmarker.
        """
        self.results_history: List[Dict[str, Any]] = []
        self.current_run_id: Optional[int] = None
        self._system_metrics_collectors: Dict[str, Callable] = {}
        self._register_default_system_metrics()

    def _register_default_system_metrics(self):
        """Registers common system metric collection functions."""
        try:
            import psutil
            self._system_metrics_collectors["cpu_percent"] = lambda: psutil.cpu_percent(interval=0.1)
            self._system_metrics_collectors["memory_percent"] = lambda: psutil.virtual_memory().percent
            self._system_metrics_collectors["disk_usage_percent"] = lambda: psutil.disk_usage('/').percent
            self._system_metrics_collectors["network_io_sent"] = lambda: psutil.net_io_counters().bytes_sent
            self._system_metrics_collectors["network_io_recv"] = lambda: psutil.net_io_counters().bytes_recv
        except ImportError:
            print("Warning: psutil not found. System metrics like CPU, Memory, Disk, and Network will not be collected.")
        except Exception as e:
            print(f"Warning: Could not initialize all system metrics collectors: {e}")

    def register_system_metric(self, name: str, collector_func: Callable[[], Any]):
        """
        Registers a custom function to collect a system metric.

        Args:
            name: The name of the metric.
            collector_func: A callable that returns the metric value.
        """
        if not callable(collector_func):
            raise ValueError("collector_func must be a callable.")
        self._system_metrics_collectors[name] = collector_func

    def _collect_system_metrics(self, interval: Optional[float] = None) -> Dict[str, Any]:
        """
        Collects all registered system metrics.

        Args:
            interval: Optional interval for metrics that support it (e.g., CPU usage).

        Returns:
            A dictionary of collected system metrics.
        """
        metrics = {}
        for name, collector in self._system_metrics_collectors.items():
            try:
                if interval is not None and name == "cpu_percent":
                    # Special handling for psutil.cpu_percent with interval
                    metrics[name] = collector() # Assuming collector itself handles interval if needed
                else:
                    metrics[name] = collector()
            except Exception as e:
                metrics[name] = f"Error: {e}"
        return metrics

    def _record_result(self, test_name: str, metric_name: str, value: Any, unit: str = "", metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Internal helper to record a single performance metric.

        Args:
            test_name: The name of the benchmark test.
            metric_name: The name of the performance metric (e.g., 'execution_time').
            value: The measured value of the metric.
            unit: The unit of the metric (e.g., 'seconds', 'ms', 'ops/sec').
            metadata: Optional dictionary for additional context.

        Returns:
            A dictionary representing the recorded metric and its status.
        """
        if self.current_run_id is None:
            return {"success": False, "message": "No active run. Use start_new_run() first.", "data": None}

        if test_name not in self.results_history[self.current_run_id]["tests"]:
            self.results_history[self.current_run_id]["tests"][test_name] = []

        metric_entry = {
            "metric_name": metric_name,
            "value": value,
            "unit": unit,
            "metadata": metadata if metadata is not None else {}
        }
        self.results_history[self.current_run_id]["tests"][test_name].append(metric_entry)

        return {
            "success": True,
            "message": f"Recorded metric '{metric_name}' for test '{test_name}' in run {self.current_run_id}.",
            "data": {
                "run_id": self.current_run_id,
                "test_name": test_name,
                "metric_name": metric_name,
                "value": value,
                "unit": unit
            }
        }

    def start_new_run(self) -> Dict[str, Any]:
        """
        Starts a new benchmarking run, resetting the current run context.
        Subsequent measurements will be associated with this new run.

        Returns:
            A dictionary indicating the success of starting a new run.
        """
        self.current_run_id = len(self.results_history)
        run_data = {
            "run_id": self.current_run_id,
            "timestamp": time.time(),
            "tests": {},
            "system_metrics": {}
        }
        self.results_history.append(run_data)
        
        # Collect initial system metrics for the new run
        run_data["system_metrics"] = self._collect_system_metrics()
        
        return {"success": True, "message": f"Started new benchmarking run with ID {self.current_run_id}.", "data": {"run_id": self.current_run_id}}

    def stop_current_run(self) -> Dict[str, Any]:
        """
        Marks the end of the current benchmarking run. No more metrics
        will be added to the current run. A new run must be started.

        Returns:
            A dictionary indicating the success of stopping the current run.
        """
        if self.current_run_id is None:
            return {"success": False, "message": "No active run to stop.", "data": None}
        
        # Collect final system metrics for the run being stopped
        if self.current_run_id < len(self.results_history):
            final_metrics = self._collect_system_metrics()
            for key, value in final_metrics.items():
                if key not in self.results_history[self.current_run_id]["system_metrics"]:
                    self.results_history[self.current_run_id]["system_metrics"][key] = []
                self.results_history[self.current_run_id]["system_metrics"][key].append(value)

        self.current_run_id = None
        return {"success": True, "message": "Current benchmarking run has been finalized."}

    def measure_code_execution(self, test_name: str, func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """
        Measures the execution time and optionally collects system metrics during
        the execution of a given Python function.

        Args:
            test_name: A descriptive name for this performance test.
            func: The Python function to measure.
            *args: Positional arguments to pass to the function.
            **kwargs: Keyword arguments to pass to the function.

        Returns:
            A dictionary containing the benchmark result, including success status,
            message, and the measured execution time and system metrics.
        """
        if not callable(func):
            return {"success": False, "message": "Provided 'func' is not a callable function.", "data": None}
        if self.current_run_id is None:
            return {"success": False, "message": "No active run. Use start_new_run() first.", "data": None}
            
        initial_metrics = self._collect_system_metrics()
        
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            execution_time = end_time - start_time
            final_metrics = self._collect_system_metrics()

            # Record execution time
            record_result = self._record_result(
                test_name=test_name,
                metric_name="execution_time",
                value=execution_time,
                unit="seconds",
                metadata={"original_return_value": result}
            )

            # Record system metrics during this specific measurement
            for key, initial_val in initial_metrics.items():
                final_val = final_metrics.get(key)
                if final_val is not None and not isinstance(final_val, str): # Avoid recording errors as metrics
                    # For metrics like CPU/memory, we might record average or delta.
                    # Here, we are recording the state *during* the execution.
                    # For simplicity, let's record the initial and final state.
                    self._record_result(
                        test_name=test_name,
                        metric_name=f"{key}_start",
                        value=initial_val,
                        unit="", # Unit depends on the metric
                        metadata={"run_id": self.current_run_id}
                    )
                    self._record_result(
                        test_name=test_name,
                        metric_name=f"{key}_end",
                        value=final_val,
                        unit="",
                        metadata={"run_id": self.current_run_id}
                    )
            
            record_result["data"]["original_return_value"] = result
            return record_result

        except Exception as e:
            return {"success": False, "message": f"Error executing function '{func.__name__}': {e}", "data": None}

    def measure_system_command(self, test_name: str, command: List[str], repeat: int = 1) -> Dict[str, Any]:
        """
        Measures the execution time and optionally collects system metrics during
        the execution of a system command.

        Args:
            test_name: A descriptive name for this performance test.
            command: A list of strings representing the command and its arguments
                     (e.g., ['ls', '-l']).
            repeat: The number of times to repeat the command execution to get
                    more stable measurements.

        Returns:
            A dictionary containing the benchmark result, including success status,
            message, and the average execution time of the command.
        """
        if not isinstance(command, list) or not all(isinstance(item, str) for item in command):
            return {"success": False, "message": "Command must be a list of strings.", "data": None}
        if repeat < 1:
            return {"success": False, "message": "Repeat count must be at least 1.", "data": None}
        if self.current_run_id is None:
            return {"success": False, "message": "No active run. Use start_new_run() first.", "data": None}

        execution_times = []
        run_metrics = []

        for i in range(repeat):
            initial_metrics = self._collect_system_metrics()
            start_time = time.perf_counter()
            try:
                process = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    check=True,
                    shell=False
                )
                end_time = time.perf_counter()
                execution_time = end_time - start_time
                execution_times.append(execution_time)
                final_metrics = self._collect_system_metrics()
                
                self._record_result(
                    test_name=test_name,
                    metric_name="command_execution_time",
                    value=execution_time,
                    unit="seconds",
                    metadata={
                        "command": " ".join(command),
                        "return_code": process.returncode,
                        "stdout": process.stdout.strip(),
                        "stderr": process.stderr.strip(),
                        "repeat_index": i
                    }
                )
                run_metrics.append({"initial": initial_metrics, "final": final_metrics, "command_time": execution_time})

            except FileNotFoundError:
                return {"success": False, "message": f"Command not found: {command[0]}", "data": None}
            except subprocess.CalledProcessError as e:
                return {"success": False, "message": f"Command '{' '.join(command)}' failed with exit code {e.returncode}.\nStderr: {e.stderr}", "data": None}
            except Exception as e:
                return {"success": False, "message": f"An unexpected error occurred during command execution: {e}", "data": None}
        
        avg_time = statistics.mean(execution_times)
        
        # Aggregate and record system metrics across repetitions for this command
        for i, metrics_set in enumerate(run_metrics):
            for key, initial_val in metrics_set["initial"].items():
                final_val = metrics_set["final"].get(key)
                if final_val is not None and not isinstance(final_val, str):
                    self._record_result(
                        test_name=test_name,
                        metric_name=f"{key}_start",
                        value=initial_val,
                        unit="",
                        metadata={"run_id": self.current_run_id, "repeat_index": i}
                    )
                    self._record_result(
                        test_name=test_name,
                        metric_name=f"{key}_end",
                        value=final_val,
                        unit="",
                        metadata={"run_id": self.current_run_id, "repeat_index": i}
                    )
            # Record average command execution time for this run
            self._record_result(
                test_name=test_name,
                metric_name="average_command_execution_time",
                value=avg_time,
                unit="seconds",
                metadata={"command": " ".join(command), "repeat_count": repeat}
            )

        return {
            "success": True,
            "message": f"Measured average execution time for command '{' '.join(command)}' over {repeat} runs.",
            "data": {
                "command": " ".join(command),
                "average_execution_time": avg_time,
                "unit": "seconds",
                "repeat_count": repeat
            }
        }

    def get_run_summary(self, run_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Retrieves a summary of a specific benchmarking run or the latest run if none specified.
        Includes average, min, max, stdev for metrics within the run.

        Args:
            run_id: The ID of the run to summarize. If None, the latest completed run is used.

        Returns:
            A dictionary containing the summary of the specified run or the latest run.
        """
        target_run_id = run_id if run_id is not None else (len(self.results_history) - 1 if self.results_history else None)

        if target_run_id is None or not (0 <= target_run_id < len(self.results_history)):
            return {"success": False, "message": f"Run ID {run_id} not found.", "data": None}

        run_data = self.results_history[target_run_id]
        summary = {
            "run_id": run_data["run_id"],
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(run_data["timestamp"])),
            "tests_summarized": {},
            "system_metrics_summary": {}
        }

        # Summarize test-specific metrics
        for test_name, metrics_list in run_data["tests"].items():
            test_metrics_summary = {}
            # Group metrics by name to calculate statistics
            metrics_grouped = {}
            for metric in metrics_list:
                m_name = metric["metric_name"]
                if m_name not in metrics_grouped:
                    metrics_grouped[m_name] = []
                metrics_grouped[m_name].append(metric["value"])
            
            for m_name, values in metrics_grouped.items():
                if values:
                    try:
                        # Filter out non-numeric values if any (e.g., error strings)
                        numeric_values = [v for v in values if isinstance(v, (int, float))]
                        if numeric_values:
                            test_metrics_summary[m_name] = {
                                "min": min(numeric_values),
                                "max": max(numeric_values),
                                "avg": statistics.mean(numeric_values),
                                "stdev": statistics.stdev(numeric_values) if len(numeric_values) > 1 else 0,
                                "unit": next((m["unit"] for m in metrics_list if m["metric_name"] == m_name), ""), # Get unit from first occurrence
                                "count": len(numeric_values)
                            }
                        else:
                            test_metrics_summary[m_name] = {"values": values, "unit": "", "count": len(values), "status": "Non-numeric data"}
                    except statistics.StatisticsError:
                         test_metrics_summary[m_name] = {"values": values, "unit": "", "count": len(values), "status": "Calculation error"}
            
            summary["tests_summarized"][test_name] = test_metrics_summary

        # Summarize system metrics
        for metric_name, values in run_data["system_metrics"].items():
            numeric_values = [v for v in values if isinstance(v, (int, float))]
            if numeric_values:
                try:
                    summary["system_metrics_summary"][metric_name] = {
                        "min": min(numeric_values),
                        "max": max(numeric_values),
                        "avg": statistics.mean(numeric_values),
                        "stdev": statistics.stdev(numeric_values) if len(numeric_values) > 1 else 0,
                        "count": len(numeric_values)
                    }
                except statistics.StatisticsError:
                    summary["system_metrics_summary"][metric_name] = {"values": values, "count": len(values), "status": "Calculation error"}
            elif values: # Handle cases where all values are errors or non-numeric
                summary["system_metrics_summary"][metric_name] = {"values": values, "count": len(values), "status": "All non-numeric or errors"}

        return {"success": True, "message": f"Summary for run ID {target_run_id}.", "data": summary}

    def get_comparative_analysis(self, test_name: str, metric_name: str, run_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Performs a comparative analysis of a specific metric for a given test across multiple runs.

        Args:
            test_name: The name of the test to analyze.
            metric_name: The name of the metric to compare.
            run_ids: A list of run IDs to include in the analysis. If None, all completed runs are used.

        Returns:
            A dictionary containing the comparative analysis results, including average, min, max,
            and standard deviation of the metric across the specified runs.
        """
        selected_runs_data = []
        if run_ids is None:
            selected_runs_data = self.results_history
        else:
            for rid in run_ids:
                if 0 <= rid < len(self.results_history):
                    selected_runs_data.append(self.results_history[rid])
                else:
                    return {"success": False, "message": f"Run ID {rid} not found for comparison.", "data": None}
        
        if not selected_runs_data:
            return {"success": False, "message": "No runs available for comparison.", "data": None}

        metric_values = []
        run_details = []
        metric_unit = ""

        for run_data in selected_runs_data:
            if test_name in run_data["tests"]:
                for metric in run_data["tests"][test_name]:
                    if metric["metric_name"] == metric_name:
                        value = metric["value"]
                        # Ensure value is numeric for calculations
                        if isinstance(value, (int, float)):
                            metric_values.append(value)
                            metric_unit = metric.get("unit", "")
                            run_details.append({
                                "run_id": run_data["run_id"],
                                "timestamp": run_data["timestamp"],
                                "value": value,
                                "unit": metric_unit
                            })
                        else:
                            # Log or handle non-numeric values if necessary, but don't include in stats
                            print(f"Warning: Non-numeric value '{value}' for metric '{metric_name}' in run {run_data['run_id']} skipped for statistical analysis.")

        if not metric_values:
            return {"success": False, "message": f"No numeric data found for metric '{metric_name}' in test '{test_name}' across selected runs.", "data": None}

        try:
            analysis_results = {
                "test_name": test_name,
                "metric_name": metric_name,
                "unit": metric_unit,
                "runs_analyzed": len(run_details),
                "average": statistics.mean(metric_values),
                "min": min(metric_values),
                "max": max(metric_values),
                "stdev": statistics.stdev(metric_values) if len(metric_values) > 1 else 0,
                "individual_run_data": run_details
            }
            return {"success": True, "message": f"Comparative analysis for '{metric_name}' in '{test_name}'.", "data": analysis_results}
        except statistics.StatisticsError as e:
            return {"success": False, "message": f"Error calculating statistics for metric '{metric_name}': {e}", "data": None}

    def get_performance_trends(self, test_name: str, metric_name: str, runs_to_consider: Optional[int] = None) -> Dict[str, Any]:
        """
        Analyzes performance trends for a specific metric of a given test across recorded runs.
        Uses linear regression for trend estimation.

        Args:
            test_name: The name of the test to analyze trends for.
            metric_name: The name of the metric to analyze trends for.
            runs_to_consider: If specified, only consider the latest `runs_to_consider` runs.

        Returns:
            A dictionary containing trend analysis, including data points, slope, and trend direction.
        """
        trend_data_points = []
        unit = ""

        runs_to_process = self.results_history
        if runs_to_consider is not None and runs_to_consider > 0:
            runs_to_process = self.results_history[-runs_to_consider:]

        for run_data in runs_to_process:
            if test_name in run_data["tests"]:
                for metric in run_data["tests"][test_name]:
                    if metric["metric_name"] == metric_name:
                        value = metric["value"]
                        if isinstance(value, (int, float)):
                            trend_data_points.append({
                                "timestamp": run_data["timestamp"],
                                "value": value,
                                "run_id": run_data["run_id"],
                                "unit": metric["unit"]
                            })
                            if not unit: unit = metric["unit"] # Capture unit from first valid entry
        
        if not trend_data_points:
            return {"success": False, "message": f"No numeric trend data found for metric '{metric_name}' in test '{test_name}'.", "data": None}
        
        trend_data_points.sort(key=lambda x: x["timestamp"])

        values = np.array([d["value"] for d in trend_data_points])
        timestamps = np.array([d["timestamp"] for d in trend_data_points])

        trend_summary = {
            "test_name": test_name,
            "metric_name": metric_name,
            "unit": unit,
            "data_points": trend_data_points,
            "analysis": {}
        }

        if len(values) > 1:
            try:
                # Use numpy for robust linear regression
                # Fit a line to the data (timestamps vs values)
                coeffs = np.polyfit(timestamps, values, 1)
                slope = coeffs[0]  # Slope of the line
                intercept = coeffs[1]

                trend_summary["analysis"]["slope"] = slope # Units per second
                trend_summary["analysis"]["intercept"] = intercept
                trend_summary["analysis"]["linear_regression_equation"] = f"y = {slope:.6f}x + {intercept:.6f}"

                # Determine trend direction based on slope
                # We need to consider the context of the metric. E.g., lower execution time is better.
                # This assumes lower values are generally better for performance metrics.
                # A more sophisticated approach might require user-defined metric behavior.
                if slope < -abs(slope * 0.01): # Consider a small tolerance for 'stable'
                    trend_summary["analysis"]["trend"] = "Improving"
                elif slope > abs(slope * 0.01):
                    trend_summary["analysis"]["trend"] = "Degrading"
                else:
                    trend_summary["analysis"]["trend"] = "Stable"
                
                trend_summary["analysis"]["start_value"] = values[0]
                trend_summary["analysis"]["end_value"] = values[-1]
                trend_summary["analysis"]["start_timestamp"] = timestamps[0]
                trend_summary["analysis"]["end_timestamp"] = timestamps[-1]

            except Exception as e:
                trend_summary["analysis"]["error"] = f"Could not perform trend analysis: {e}"
        else:
            trend_summary["analysis"]["trend"] = "Insufficient data (need at least 2 points)"

        return {"success": True, "message": f"Performance trend analysis for '{metric_name}' in '{test_name}'.", "data": trend_summary}

    def _plot_trend(self, trend_data: Dict[str, Any], output_path: Optional[str] = None) -> Optional[str]:
        """
        Generates a plot for trend analysis.

        Args:
            trend_data: The trend analysis dictionary from get_performance_trends.
            output_path: Optional path to save the plot. If None, plot is not saved.

        Returns:
            The path where the plot was saved, or None.
        """
        if not trend_data or not trend_data.get("success"):
            print("Cannot plot trend: invalid trend data provided.")
            return None
        
        data = trend_data["data"]
        metric_name = data["metric_name"]
        test_name = data["test_name"]
        analysis = data["analysis"]
        
        if "error" in analysis or analysis.get("trend") == "Insufficient data (need at least 2 points)":
            print(f"Skipping plot for {test_name}/{metric_name}: {analysis.get('trend', analysis.get('error'))}")
            return None

        try:
            plt.figure(figsize=(12, 6))
            sns.set_theme(style="whitegrid")

            # Plot individual data points
            sns.scatterplot(x=[d['timestamp'] for d in data['data_points']], y=[d['value'] for d in data['data_points']], label='Measured Values', s=50)

            # Plot the linear regression line
            if "linear_regression_equation" in analysis:
                timestamps = np.array([d['timestamp'] for d in data['data_points']])
                # Ensure we are using the same range for plotting the line as for data points
                # Or use start/end timestamps from analysis if available
                min_ts = min(timestamps)
                max_ts = max(timestamps)
                
                if "start_timestamp" in analysis and "end_timestamp" in analysis:
                    min_ts = analysis["start_timestamp"]
                    max_ts = analysis["end_timestamp"]
                
                regression_line_ts = np.array([min_ts, max_ts])
                regression_line_vals = analysis["slope"] * regression_line_ts + analysis["intercept"]
                plt.plot(regression_line_ts, regression_line_vals, color='red', linestyle='--', label=f'Trend Line ({analysis["trend"]})')

            plt.title(f"Performance Trend: {test_name} - {metric_name}", fontsize=16)
            plt.xlabel("Timestamp", fontsize=12)
            plt.ylabel(f"{metric_name} ({data.get('unit', '')})", fontsize=12)
            plt.legend()
            plt.grid(True, linestyle='--', alpha=0.6)
            plt.tight_layout()

            if output_path:
                plt.savefig(output_path)
                print(f"Trend plot saved to: {output_path}")
                plt.close()
                return output_path
            else:
                plt.show()
                plt.close()
                return None
        except Exception as e:
            print(f"Error generating plot for {test_name}/{metric_name}: {e}")
            return None

    def generate_full_report(self, title: str = "Performance Benchmark Report", run_ids: Optional[List[int]] = None, output_dir: str = ".") -> Dict[str, Any]:
        """
        Generates a comprehensive performance benchmarking report with comparative analysis,
        trend analysis, and visualizations.

        Args:
            title: The title for the report.
            run_ids: A list of run IDs to include in the report. If None, all completed runs are included.
            output_dir: The directory where generated report files (JSON, plots) will be saved.

        Returns:
            A dictionary containing the structured report data and file paths.
        """
        import os
        os.makedirs(output_dir, exist_ok=True)

        report_data = {
            "title": title,
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "benchmark_runs_summary": [],
            "comparative_analysis_summary": [],
            "trend_analysis_summary": [],
            "plot_paths": {}
        }

        runs_to_report_ids = []
        if run_ids is None:
            runs_to_report_ids = list(range(len(self.results_history)))
        else:
            for rid in run_ids:
                if 0 <= rid < len(self.results_history):
                    runs_to_report_ids.append(rid)
                else:
                    return {"success": False, "message": f"Run ID {rid} not found for report generation.", "data": None}
        
        if not runs_to_report_ids:
            return {"success": False, "message": "No runs available to generate report.", "data": None}

        # Collect all unique tests and metrics across the selected runs
        all_tests_and_metrics = set()
        for rid in runs_to_report_ids:
            run_data = self.results_history[rid]
            for test_name, metrics in run_data["tests"].items():
                for metric in metrics:
                    # Only consider numeric metrics for trend and comparative analysis
                    if isinstance(metric["value"], (int, float)):
                        all_tests_and_metrics.add((test_name, metric["metric_name"]))

        # Generate comparative analysis and trend data for all unique tests/metrics
        comparative_analysis_results = {}
        trend_analysis_results = {}

        for test_name, metric_name in all_tests_and_metrics:
            comp_analysis = self.get_comparative_analysis(test_name, metric_name, run_ids=runs_to_report_ids)
            if comp_analysis["success"]:
                comparative_analysis_results[(test_name, metric_name)] = comp_analysis["data"]
            
            trend_analysis = self.get_performance_trends(test_name, metric_name, runs_to_consider=len(runs_to_report_ids))
            if trend_analysis["success"]:
                trend_analysis_results[(test_name, metric_name)] = trend_analysis["data"]

        # Structure the report
        for rid in runs_to_report_ids:
            run_summary = self.get_run_summary(rid)
            if run_summary["success"]:
                report_data["benchmark_runs_summary"].append(run_summary["data"])

        for (test_name, metric_name), data in comparative_analysis_results.items():
            report_data["comparative_analysis_summary"].append({
                "test_name": test_name,
                "metric_name": metric_name,
                "analysis": data
            })
        
        for (test_name, metric_name), data in trend_analysis_results.items():
            report_data["trend_analysis_summary"].append({
                "test_name": test_name,
                "metric_name": metric_name,
                "trend": data
            })
            # Generate and save plots for trend analysis
            plot_path = os.path.join(output_dir, f"trend_{test_name.replace(' ', '_')}_{metric_name.replace(' ', '_')}.png")
            saved_plot_path = self._plot_trend(trend_analysis_results[(test_name, metric_name)], output_path=plot_path)
            if saved_plot_path:
                report_data["plot_paths"][(test_name, metric_name)] = saved_plot_path

        # Save the full report as JSON
        report_filename = os.path.join(output_dir, f"{title.replace(' ', '_').lower()}_report.json")
        try:
            with open(report_filename, 'w') as f:
                json.dump(report_data, f, indent=4)
            report_data["report_filepath"] = report_filename
            return {"success": True, "message": "Comprehensive performance benchmark report generated.", "data": report_data}
        except IOError as e:
            return {"success": False, "message": f"Error writing report file {report_filename}: {e}", "data": None}

    def export_results_json(self, filepath: str) -> Dict[str, Any]:
        """
        Exports all recorded benchmark results to a JSON file.

        Args:
            filepath: The path to the JSON file where results will be saved.

        Returns:
            A dictionary indicating the success status and a message.
        """
        if not self.results_history:
            return {"success": False, "message": "No benchmark results to export.", "data": None}

        try:
            with open(filepath, 'w') as f:
                json.dump(self.results_history, f, indent=4)
            return {"success": True, "message": f"Benchmark results exported successfully to {filepath}.", "data": {"filepath": filepath}}
        except IOError as e:
            return {"success": False, "message": f"Error writing to file {filepath}: {e}", "data": None}
        except Exception as e:
            return {"success": False, "message": f"An unexpected error occurred during export: {e}", "data": None}

    def load_results_json(self, filepath: str) -> Dict[str, Any]:
        """
        Loads benchmark results from a JSON file, replacing current results.

        Args:
            filepath: The path to the JSON file to load.

        Returns:
            A dictionary indicating the success status and a message.
        """
        try:
            with open(filepath, 'r') as f:
                loaded_data = json.load(f)
            
            # Basic validation for loaded data structure
            if not isinstance(loaded_data, list):
                return {"success": False, "message": "Invalid data format: expected a list of runs.", "data": None}
            
            for i, run in enumerate(loaded_data):
                if not isinstance(run, dict) or 'run_id' not in run or 'timestamp' not in run or 'tests' not in run:
                    return {"success": False, "message": f"Invalid data format: run object at index {i} is malformed.", "data": None}

            self.results_history = loaded_data
            # Reset current run to avoid confusion if the loaded data represents a finished state
            self.current_run_id = None 
            return {"success": True, "message": f"Benchmark results loaded successfully from {filepath}.", "data": {"filepath": filepath, "num_runs_loaded": len(loaded_data)}}
        except FileNotFoundError:
            return {"success": False, "message": f"File not found: {filepath}", "data": None}
        except json.JSONDecodeError:
            return {"success": False, "message": f"Error decoding JSON from {filepath}. Ensure it's a valid JSON file.", "data": None}
        except IOError as e:
            return {"success": False, "message": f"Error reading from file {filepath}: {e}", "data": None}
        except Exception as e:
            return {"success": False, "message": f"An unexpected error occurred during load: {e}", "data": None}

if __name__ == '__main__':
    # Example Usage:

    def fibonacci_recursive(n):
        if n <= 1:
            return n
        else:
            return fibonacci_recursive(n-1) + fibonacci_recursive(n-2)

    def fibonacci_iterative(n):
        a, b = 0, 1
        for _ in range(n):
            a, b = b, a + b
        return a

    def process_list(data):
        return [x * 2 for x in data]

    def simulate_workload(duration_sec):
        start = time.time()
        while time.time() - start < duration_sec:
            pass # Busy waiting

    print("Initializing PerformanceBenchmarker...")
    benchmarker = PerformanceBenchmarker()

    # --- Run 1 ---
    print("\n--- Starting Run 1 ---")
    benchmarker.start_new_run()
    
    print("Measuring recursive Fibonacci calculation (n=30)...")
    fib_recursive_result = benchmarker.measure_code_execution("Fibonacci", fibonacci_recursive, 30)
    print(f"Fibonacci (Recursive) result: {fib_recursive_result}")

    print("Measuring list processing (1000 elements)...")
    sample_list = list(range(1000))
    list_result = benchmarker.measure_code_execution("List Processing", process_list, sample_list)
    print(f"List processing result: {list_result}")

    print("Measuring 'ls -l' command (5 repetitions)...")
    ls_command_result = benchmarker.measure_system_command("List Directory", ["ls", "-l"], repeat=5)
    print(f"'ls -l' command result: {ls_command_result}")
    
    benchmarker.stop_current_run()
    print("--- Run 1 Finished ---")

    # --- Run 2 ---
    print("\n--- Starting Run 2 ---")
    benchmarker.start_new_run()
    
    print("Measuring iterative Fibonacci calculation (n=30)...")
    fib_iterative_result = benchmarker.measure_code_execution("Fibonacci", fibonacci_iterative, 30)
    print(f"Fibonacci (Iterative) result: {fib_iterative_result}")

    print("Measuring 'uptime' command...")
    uptime_result = benchmarker.measure_system_command("System Uptime", ["uptime"])
    print(f"'uptime' command result: {uptime_result}")
    
    print("Simulating 0.5s workload...")
    simulate_result = benchmarker.measure_code_execution("Simulated Workload", simulate_workload, 0.5)
    print(f"Simulated workload result: {simulate_result}")

    benchmarker.stop_current_run()
    print("--- Run 2 Finished ---")

    # --- Run 3 (for trend analysis) ---
    print("\n--- Starting Run 3 ---")
    benchmarker.start_new_run()
    
    print("Measuring list processing with larger list (5000 elements)...")
    large_list = list(range(5000))
    large_list_result = benchmarker.measure_code_execution("List Processing", process_list, large_list)
    print(f"List processing large result: {large_list_result}")

    print("Measuring 'echo' command...")
    echo_result = benchmarker.measure_system_command("Echo Test", ["echo", "hello_benchmark"])
    print(f"'echo' command result: {echo_result}")

    benchmarker.stop_current_run()
    print("--- Run 3 Finished ---")

    # --- Run 4 (for trend analysis - slight degradation) ---
    print("\n--- Starting Run 4 ---")
    benchmarker.start_new_run()
    
    print("Measuring list processing with even larger list (7000 elements) - simulating degradation...")
    very_large_list = list(range(7000))
    very_large_list_result = benchmarker.measure_code_execution("List Processing", process_list, very_large_list)
    print(f"List processing very large result: {very_large_list_result}")

    benchmarker.stop_current_run()
    print("--- Run 4 Finished ---")


    # --- Reporting and Analysis ---
    print("\n--- Generating Full Report ---")
    report_output_dir = "benchmark_reports"
    full_report = benchmarker.generate_full_report("Application Performance Report", output_dir=report_output_dir)
    
    if full_report["success"]:
        print(f"Report generated successfully at: {full_report['data']['report_filepath']}")
        print(f"Plots saved in: {report_output_dir}")
        print("\nReport Summary:")
        print(f"Title: {full_report['data']['title']}")
        print(f"Platform: {full_report['data']['platform']}")
        print(f"Python Version: {full_report['data']['python_version']}")
        print(f"Number of Benchmark Runs Included: {len(full_report['data']['benchmark_runs_summary'])}")
        
        print("\n--- Comparative Analysis Excerpt (Fibonacci) ---")
        for comp_data in full_report["data"].get("comparative_analysis_summary", []):
            if comp_data["test_name"] == "Fibonacci":
                 print(f"  Metric: {comp_data['metric_name']}")
                 analysis = comp_data['analysis']
                 print(f"  Avg: {analysis['average']:.6f} {analysis['unit']}")
                 print(f"  Min: {analysis['min']:.6f} {analysis['unit']}")
                 print(f"  Max: {analysis['max']:.6f} {analysis['unit']}")
                 print(f"  Stdev: {analysis['stdev']:.6f} {analysis['unit']}")

        print("\n--- Trend Analysis Excerpt (List Processing) ---")
        for trend_data_entry in full_report["data"].get("trend_analysis_summary", []):
            if trend_data_entry["test_name"] == "List Processing":
                trend_info = trend_data_entry['trend']
                print(f"  Metric: {trend_data_entry['metric_name']}")
                print(f"  Trend: {trend_info['trend']}")
                print(f"  Start Value: {trend_info['start_value']:.2f} {trend_info['unit']}")
                print(f"  End Value: {trend_info['end_value']:.2f} {trend_info['unit']}")
                if "slope" in trend_info:
                    print(f"  Slope: {trend_info['slope']:.6f} {trend_info['unit']}/sec")
                if (trend_data_entry["test_name"], trend_data_entry["metric_name"]) in full_report["data"]["plot_paths"]:
                    print(f"  Plot available: {full_report['data']['plot_paths'][(trend_data_entry['test_name'], trend_data_entry['metric_name'])]}")
    else:
        print(f"Error generating report: {full_report['message']}")

    # --- Exporting and Loading ---
    export_path = "benchmark_results.json"
    print(f"\nExporting results to {export_path}...")
    export_status = benchmarker.export_results_json(export_path)
    print(export_status["message"])

    print(f"\nClearing current results and loading from {export_path}...")
    benchmarker_loaded = PerformanceBenchmarker()
    load_status = benchmarker_loaded.load_results_json(export_path)
    print(load_status["message"])

    if load_status["success"]:
        print("\nVerifying loaded data by generating a summary of run ID 0:")
        loaded_summary = benchmarker_loaded.get_run_summary(0)
        if loaded_summary["success"]:
            print("Summary of loaded Run 0:")
            print(json.dumps(loaded_summary["data"], indent=2))
        else:
            print(f"Error getting summary from loaded data: {loaded_summary['message']}")
