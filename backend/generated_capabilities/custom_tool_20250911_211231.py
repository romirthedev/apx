
import platform
import psutil
import time
import threading
from typing import Dict, Any, Optional, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PerformanceDashboard:
    """
    A sophisticated Python tool class for generating detailed performance monitoring data,
    designed to provide comprehensive metrics for a performance monitoring dashboard.

    This class retrieves various system performance metrics and is built to be
    compatible with macOS and other Unix-like systems. It prioritizes safe
    operations without system modifications.

    Note: Generating a truly "detailed performance monitoring dashboard" with real-time
    updates, complex visualizations, and historical data storage typically requires
    integration with specialized monitoring tools (e.g., Prometheus, Grafana),
    dedicated data visualization libraries (e.g., Plotly, Bokeh), and robust
    API interactions. This class provides the foundational data collection capabilities.
    """

    def __init__(self):
        """
        Initializes the PerformanceDashboard.
        Sets up a data buffer for historical tracking (basic implementation).
        """
        self.data_buffer: List[Dict[str, Any]] = []
        self.buffer_max_size = 100  # Maximum number of historical data points to keep
        self._stop_event = threading.Event()
        self._data_collection_thread: Optional[threading.Thread] = None

    def _log_error(self, message: str, exception: Exception):
        """Logs an error with context."""
        logging.error(f"{message}: {exception}", exc_info=True)

    def _build_response(self, success: bool, message: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Constructs a standardized response dictionary.

        Args:
            success: A boolean indicating if the operation was successful.
            message: A string message describing the result.
            data: An optional dictionary containing relevant performance data.

        Returns:
            A dictionary representing the response.
        """
        response = {
            "success": success,
            "message": message,
            "data": data if data is not None else {}
        }
        return response

    def _validate_limit(self, limit: int, min_val: int = 1, max_val: int = 1000) -> bool:
        """Validates the limit input."""
        if not isinstance(limit, int):
            logging.warning(f"Input 'limit' must be an integer. Received: {type(limit)}")
            return False
        if not (min_val <= limit <= max_val):
            logging.warning(f"Input 'limit' out of range ({min_val}-{max_val}). Received: {limit}")
            return False
        return True

    def get_cpu_usage(self) -> Dict[str, Any]:
        """
        Retrieves current CPU usage information.

        Returns:
            A dictionary with the following structure:
            {
                "success": bool,
                "message": str,
                "data": {
                    "physical_cores": int,
                    "logical_cores": int,
                    "percent_usage": float,
                    "per_cpu_percent_usage": List[float]
                }
            }
        """
        try:
            physical_cores = psutil.cpu_count(logical=False)
            logical_cores = psutil.cpu_count(logical=True)
            # Use a small interval for current snapshot; for long-term trend, adjust interval
            percent_usage = psutil.cpu_percent(interval=0.1)
            per_cpu_percent_usage = psutil.cpu_percent(interval=0.1, percpu=True)

            response_data = {
                "physical_cores": physical_cores,
                "logical_cores": logical_cores,
                "percent_usage": round(percent_usage, 2),
                "per_cpu_percent_usage": [round(p, 2) for p in per_cpu_percent_usage]
            }
            return self._build_response(True, "CPU usage retrieved successfully.", response_data)
        except Exception as e:
            self._log_error("Error retrieving CPU usage", e)
            return self._build_response(False, f"Error retrieving CPU usage: {e}")

    def get_memory_usage(self) -> Dict[str, Any]:
        """
        Retrieves current memory (RAM) usage information.

        Returns:
            A dictionary with the following structure:
            {
                "success": bool,
                "message": str,
                "data": {
                    "total_gb": float,
                    "available_gb": float,
                    "percent_used": float,
                    "used_gb": float,
                    "free_gb": float
                }
            }
        """
        try:
            mem = psutil.virtual_memory()
            response_data = {
                "total_gb": round(mem.total / (1024**3), 2),
                "available_gb": round(mem.available / (1024**3), 2),
                "percent_used": round(mem.percent, 2),
                "used_gb": round(mem.used / (1024**3), 2),
                "free_gb": round(mem.free / (1024**3), 2)
            }
            return self._build_response(True, "Memory usage retrieved successfully.", response_data)
        except Exception as e:
            self._log_error("Error retrieving memory usage", e)
            return self._build_response(False, f"Error retrieving memory usage: {e}")

    def get_disk_usage(self) -> Dict[str, Any]:
        """
        Retrieves disk usage information for all mounted partitions.

        Returns:
            A dictionary with the following structure:
            {
                "success": bool,
                "message": str,
                "data": {
                    "partitions": [
                        {
                            "device": str,
                            "mountpoint": str,
                            "fstype": str,
                            "total_gb": float,
                            "used_gb": float,
                            "free_gb": float,
                            "percent_used": float
                        },
                        ...
                    ]
                }
            }
        """
        try:
            partitions_data = []
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    partitions_data.append({
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "fstype": partition.fstype,
                        "total_gb": round(usage.total / (1024**3), 2),
                        "used_gb": round(usage.used / (1024**3), 2),
                        "free_gb": round(usage.free / (1024**3), 2),
                        "percent_used": round(usage.percent, 2)
                    })
                except PermissionError:
                    error_msg = "N/A (Permission denied)"
                    partitions_data.append({
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "fstype": partition.fstype,
                        "total_gb": error_msg,
                        "used_gb": error_msg,
                        "free_gb": error_msg,
                        "percent_used": error_msg
                    })
                    self._log_error(f"Permission denied for disk partition: {partition.mountpoint}", PermissionError())
                except Exception as e:
                    error_msg = f"Error: {e}"
                    partitions_data.append({
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "fstype": partition.fstype,
                        "total_gb": error_msg,
                        "used_gb": error_msg,
                        "free_gb": error_msg,
                        "percent_used": error_msg
                    })
                    self._log_error(f"Error retrieving disk usage for {partition.mountpoint}", e)

            response_data = {"partitions": partitions_data}
            return self._build_response(True, "Disk usage retrieved successfully.", response_data)
        except Exception as e:
            self._log_error("Error retrieving disk partitions", e)
            return self._build_response(False, f"Error retrieving disk usage: {e}")

    def get_network_io(self) -> Dict[str, Any]:
        """
        Retrieves current network input/output statistics.

        Returns:
            A dictionary with the following structure:
            {
                "success": bool,
                "message": str,
                "data": {
                    "bytes_sent_mb": float,
                    "bytes_recv_mb": float,
                    "packets_sent": int,
                    "packets_recv": int
                }
            }
        """
        try:
            net_io = psutil.net_io_counters()
            response_data = {
                "bytes_sent_mb": round(net_io.bytes_sent / (1024**2), 2),
                "bytes_recv_mb": round(net_io.bytes_recv / (1024**2), 2),
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv
            }
            return self._build_response(True, "Network I/O retrieved successfully.", response_data)
        except Exception as e:
            self._log_error("Error retrieving network I/O", e)
            return self._build_response(False, f"Error retrieving network I/O: {e}")

    def get_system_info(self) -> Dict[str, Any]:
        """
        Retrieves basic system information.

        Returns:
            A dictionary with the following structure:
            {
                "success": bool,
                "message": str,
                "data": {
                    "system": str,
                    "node_name": str,
                    "release": str,
                    "version": str,
                    "machine": str,
                    "processor": str,
                    "os_details": Dict[str, Any] # More detailed OS info
                }
            }
        """
        try:
            uname = platform.uname()
            response_data = {
                "system": uname.system,
                "node_name": uname.node,
                "release": uname.release,
                "version": uname.version,
                "machine": uname.machine,
                "processor": uname.processor,
                "os_details": {
                    "platform_name": platform.platform(),
                    "platform_version": platform.version(),
                    "python_version": platform.python_version()
                }
            }
            return self._build_response(True, "System information retrieved successfully.", response_data)
        except Exception as e:
            self._log_error("Error retrieving system information", e)
            return self._build_response(False, f"Error retrieving system information: {e}")

    def get_process_list(self, limit: int = 10) -> Dict[str, Any]:
        """
        Retrieves a list of running processes, ordered by CPU usage.

        Args:
            limit: The maximum number of processes to return. Must be between 1 and 1000.

        Returns:
            A dictionary with the following structure:
            {
                "success": bool,
                "message": str,
                "data": {
                    "processes": [
                        {
                            "pid": int,
                            "name": str,
                            "username": Optional[str],
                            "cpu_percent": float,
                            "memory_percent": float,
                            "status": str,
                            "create_time": float # Timestamp of process creation
                        },
                        ...
                    ]
                }
            }
        """
        if not self._validate_limit(limit):
            return self._build_response(False, "Invalid limit provided for process list.")

        try:
            processes_info = []
            # Fetching all process details in one go for efficiency
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'status', 'create_time'], ad_value=None):
                try:
                    pinfo = proc.info
                    # cpu_percent with interval=0.1 provides a snapshot over a short period
                    # For real-time dashboard, a dedicated background thread polling more frequently is better.
                    pinfo['cpu_percent'] = proc.cpu_percent(interval=0.05) # Even shorter for quick snapshot
                    pinfo['memory_percent'] = proc.memory_percent()
                    pinfo['create_time'] = proc.create_time()
                    processes_info.append(pinfo)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                    # Log these specific, common exceptions if needed, but generally they are expected
                    # logging.debug(f"Skipping process due to {type(e).__name__}: {proc.pid if 'proc' in locals() else 'N/A'}")
                    pass
                except Exception as e:
                    self._log_error(f"Unexpected error processing process {proc.pid if 'proc' in locals() else 'N/A'}", e)
                    pass

            # Sort processes by CPU usage in descending order
            processes_info.sort(key=lambda p: p['cpu_percent'], reverse=True)

            # Trim to limit and prepare for response
            limited_processes = []
            for proc in processes_info[:limit]:
                limited_processes.append({
                    "pid": proc['pid'],
                    "name": proc.get('name', 'N/A'),
                    "username": proc.get('username', 'N/A'),
                    "cpu_percent": round(proc['cpu_percent'], 2),
                    "memory_percent": round(proc['memory_percent'], 2),
                    "status": proc.get('status', 'N/A'),
                    "create_time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(proc.get('create_time', 0))) if proc.get('create_time') else 'N/A'
                })

            response_data = {"processes": limited_processes}
            return self._build_response(True, f"{len(limited_processes)} top processes retrieved successfully.", response_data)
        except Exception as e:
            self._log_error("Error retrieving process list", e)
            return self._build_response(False, f"Error retrieving process list: {e}")

    def _collect_and_buffer_data(self, interval: int = 5):
        """
        Periodically collects all performance data and buffers it.
        This is a basic implementation for historical data.
        """
        while not self._stop_event.is_set():
            try:
                current_data = self.get_all_performance_data()
                if current_data["success"]:
                    self.data_buffer.append(current_data["data"])
                    if len(self.data_buffer) > self.buffer_max_size:
                        self.data_buffer.pop(0) # Remove oldest data point
                else:
                    logging.warning(f"Failed to collect data for buffering: {current_data['message']}")
            except Exception as e:
                self._log_error("Error during background data collection", e)

            # Wait for the specified interval, but check stop event frequently
            for _ in range(interval * 10): # Check every 0.1 seconds
                if self._stop_event.is_set():
                    break
                time.sleep(0.1)

    def start_data_collection(self, interval: int = 5):
        """
        Starts a background thread to periodically collect performance data.

        Args:
            interval: The interval in seconds between data collection cycles.
                      Must be at least 1 second.
        """
        if self._data_collection_thread is not None and self._data_collection_thread.is_alive():
            logging.warning("Data collection is already running.")
            return

        if not isinstance(interval, int) or interval < 1:
            logging.error("Interval must be an integer and at least 1 second.")
            return

        self._stop_event.clear()
        self._data_collection_thread = threading.Thread(target=self._collect_and_buffer_data, args=(interval,), daemon=True)
        self._data_collection_thread.start()
        logging.info(f"Background data collection started with interval {interval} seconds.")

    def stop_data_collection(self):
        """Stops the background data collection thread."""
        if self._data_collection_thread and self._data_collection_thread.is_alive():
            self._stop_event.set()
            self._data_collection_thread.join(timeout=5) # Wait for thread to finish
            if self._data_collection_thread.is_alive():
                logging.warning("Data collection thread did not stop gracefully.")
            else:
                logging.info("Background data collection stopped.")
            self._data_collection_thread = None
        else:
            logging.warning("No background data collection thread is running.")

    def get_historical_data(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Retrieves the collected historical performance data.

        Args:
            limit: The maximum number of historical data points to return.
                   If None, all buffered data is returned.

        Returns:
            A dictionary containing a list of historical data snapshots.
        """
        if limit is not None and not isinstance(limit, int) or (limit is not None and limit < 0):
            return self._build_response(False, "Invalid limit provided for historical data.")

        if limit is None or limit >= len(self.data_buffer):
            data_to_return = self.data_buffer
        else:
            data_to_return = self.data_buffer[-limit:]

        return self._build_response(True, f"{len(data_to_return)} historical data points retrieved.", {"historical_data": data_to_return})


    def get_all_performance_data(self, process_limit: int = 10) -> Dict[str, Any]:
        """
        Retrieves a comprehensive set of performance monitoring data.

        Args:
            process_limit: The limit for the number of top processes to retrieve.
                           Must be between 1 and 1000.

        Returns:
            A dictionary containing all the data retrieved by individual methods.
            {
                "success": bool,
                "message": str,
                "data": {
                    "timestamp": str, # Timestamp of when data was collected
                    "system_info": Dict[str, Any],
                    "cpu_usage": Dict[str, Any],
                    "memory_usage": Dict[str, Any],
                    "disk_usage": Dict[str, Any],
                    "network_io": Dict[str, Any],
                    "top_processes": Dict[str, Any]
                }
            }
        """
        all_data = {}
        messages = []
        overall_success = True
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())

        # System Info
        sys_info_res = self.get_system_info()
        all_data["system_info"] = sys_info_res["data"]
        if not sys_info_res["success"]:
            messages.append(f"System Info Error: {sys_info_res['message']}")
            overall_success = False

        # CPU Usage
        cpu_res = self.get_cpu_usage()
        all_data["cpu_usage"] = cpu_res["data"]
        if not cpu_res["success"]:
            messages.append(f"CPU Usage Error: {cpu_res['message']}")
            overall_success = False

        # Memory Usage
        mem_res = self.get_memory_usage()
        all_data["memory_usage"] = mem_res["data"]
        if not mem_res["success"]:
            messages.append(f"Memory Usage Error: {mem_res['message']}")
            overall_success = False

        # Disk Usage
        disk_res = self.get_disk_usage()
        all_data["disk_usage"] = disk_res["data"]
        if not disk_res["success"]:
            messages.append(f"Disk Usage Error: {disk_res['message']}")
            overall_success = False

        # Network I/O
        net_res = self.get_network_io()
        all_data["network_io"] = net_res["data"]
        if not net_res["success"]:
            messages.append(f"Network I/O Error: {net_res['message']}")
            overall_success = False

        # Top Processes
        proc_res = self.get_process_list(limit=process_limit)
        all_data["top_processes"] = proc_res["data"]
        if not proc_res["success"]:
            messages.append(f"Top Processes Error: {proc_res['message']}")
            overall_success = False

        # Add timestamp to the collected data
        all_data["timestamp"] = timestamp

        if overall_success:
            return self._build_response(True, "All performance data retrieved successfully.", all_data)
        else:
            error_message = "Some performance data could not be retrieved. Details: " + "; ".join(messages)
            logging.warning(error_message)
            return self._build_response(False, error_message, all_data)

if __name__ == '__main__':
    # Example Usage
    dashboard = PerformanceDashboard()

    print("--- System Information ---")
    sys_info_result = dashboard.get_system_info()
    print(sys_info_result)
    print("\n")

    print("--- CPU Usage ---")
    cpu_result = dashboard.get_cpu_usage()
    print(cpu_result)
    print("\n")

    print("--- Memory Usage ---")
    memory_result = dashboard.get_memory_usage()
    print(memory_result)
    print("\n")

    print("--- Disk Usage ---")
    disk_result = dashboard.get_disk_usage()
    print(disk_result)
    print("\n")

    print("--- Network I/O ---")
    network_result = dashboard.get_network_io()
    print(network_result)
    print("\n")

    print("--- Top Processes (limit 5) ---")
    processes_result = dashboard.get_process_list(limit=5)
    print(processes_result)
    print("\n")

    print("--- All Performance Data (limit 3) ---")
    all_performance_result = dashboard.get_all_performance_data(process_limit=3)
    print(all_performance_result)
    print("\n")

    print("--- Starting background data collection (interval 3 seconds) ---")
    dashboard.start_data_collection(interval=3)
    time.sleep(7) # Let it collect a couple of data points

    print("--- Retrieving recent historical data (last 2 points) ---")
    historical_data_result = dashboard.get_historical_data(limit=2)
    print(historical_data_result)
    print("\n")

    print("--- Stopping background data collection ---")
    dashboard.stop_data_collection()
    print("Background collection stopped.")
    print("\n")

    print("--- Testing invalid inputs ---")
    print("Invalid process limit:", dashboard.get_process_list(limit=0))
    print("Invalid process limit:", dashboard.get_process_list(limit=1001))
    print("Invalid interval for collection:", dashboard.start_data_collection(interval=0))
    print("Invalid limit for historical data:", dashboard.get_historical_data(limit=-1))
