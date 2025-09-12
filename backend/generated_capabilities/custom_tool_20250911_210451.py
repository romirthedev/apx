
import platform
import psutil
import os
import datetime
import logging
import subprocess
import re
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SystemPerformanceReporter:
    """
    A specialized tool to generate detailed system performance reports and save them to a file.

    This class provides methods to collect various system performance metrics,
    format them into a human-readable report, and save the report to a specified file.
    It is designed to be safe, not modifying any system configurations without explicit
    user action (which is not part of this reporter's functionality).
    Compatibility with macOS is considered. It also incorporates Bash commands for
    more granular system monitoring where psutil might be limited or for specific details.
    """

    def __init__(self, report_filename: str = "performance_report.txt"):
        """
        Initializes the SystemPerformanceReporter.

        Args:
            report_filename: The name of the file where the performance report will be saved.
                             Must be a non-empty string. Defaults to "performance_report.txt".
        """
        self.report_filename = self._validate_filename(report_filename)
        self.report_data = {}

    def _validate_filename(self, filename: str) -> str:
        """
        Validates that the report filename is a non-empty string.

        Args:
            filename: The filename to validate.

        Returns:
            The validated filename.

        Raises:
            ValueError: If the filename is empty or not a string.
        """
        if not isinstance(filename, str) or not filename.strip():
            raise ValueError("Report filename must be a non-empty string.")
        return filename.strip()

    def _run_bash_command(self, command: str) -> Dict[str, Any]:
        """
        Executes a bash command and returns its output, handling errors.

        Args:
            command: The bash command to execute.

        Returns:
            A dictionary containing 'success' (bool), 'output' (str), and 'error' (str) keys.
        """
        try:
            # Use shell=True with caution, ensuring commands are trusted or sanitized.
            # For this tool, we assume commands are defined internally and safe.
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate()
            if process.returncode == 0:
                return {'success': True, 'output': stdout.strip(), 'error': None}
            else:
                return {'success': False, 'output': None, 'error': stderr.strip()}
        except Exception as e:
            logging.error(f"Error executing bash command '{command}': {e}")
            return {'success': False, 'output': None, 'error': str(e)}

    def _collect_system_details(self) -> Dict[str, Any]:
        """
        Collects general system details like OS name, version, and architecture.

        Returns:
            A dictionary containing system details.
            Example:
            {
                'success': True,
                'message': 'System details collected successfully.',
                'system': 'Darwin',
                'node_name': 'MyMacBookPro',
                'release': '22.6.0',
                'version': 'macOS 13.6.1 (22G313)',
                'machine': 'x86_64',
                'processor': 'Intel(R) Core(TM) i7-8850H CPU @ 2.60GHz'
            }
            or
            {
                'success': False,
                'message': 'Failed to collect system details: <error_message>'
            }
        """
        try:
            system = platform.system()
            node_name = platform.node()
            release = platform.release()
            version = platform.version()
            machine = platform.machine()
            # platform.processor() can be inconsistent. Use a bash command for potentially more detail if available.
            processor_info = self._run_bash_command("uname -m && sysctl -n machdep.cpu.brand_string || cat /proc/cpuinfo | grep 'model name' | uniq")
            processor = processor_info['output'] if processor_info['success'] and processor_info['output'] else platform.processor()

            return {
                'success': True,
                'message': 'System details collected successfully.',
                'system': system,
                'node_name': node_name,
                'release': release,
                'version': version,
                'machine': machine,
                'processor': processor.replace('\n', ' ').strip()
            }
        except Exception as e:
            logging.error(f"Error collecting system details: {e}")
            return {'success': False, 'message': f'Failed to collect system details: {e}'}

    def _collect_cpu_info(self) -> Dict[str, Any]:
        """
        Collects CPU information including core count and usage.
        Uses psutil for general info and potentially bash for more specific metrics if needed.

        Returns:
            A dictionary containing CPU information.
            Example:
            {
                'success': True,
                'message': 'CPU information collected successfully.',
                'physical_cores': 4,
                'logical_cores': 8,
                'usage_percent': 15.5,
                'cpu_load_1m': 0.5,
                'cpu_load_5m': 0.6,
                'cpu_load_15m': 0.7
            }
            or
            {
                'success': False,
                'message': 'Failed to collect CPU information: <error_message>'
            }
        """
        try:
            cpu_count_physical = psutil.cpu_count(logical=False)
            cpu_count_logical = psutil.cpu_count(logical=True)
            # Measure usage over a short interval to get a snapshot
            cpu_usage = psutil.cpu_percent(interval=0.5)

            # Attempt to get load averages using psutil (cross-platform)
            load_avg = psutil.getloadavg()
            cpu_load_1m, cpu_load_5m, cpu_load_15m = load_avg if len(load_avg) == 3 else (None, None, None)

            return {
                'success': True,
                'message': 'CPU information collected successfully.',
                'physical_cores': cpu_count_physical,
                'logical_cores': cpu_count_logical,
                'usage_percent': cpu_usage,
                'cpu_load_1m': cpu_load_1m,
                'cpu_load_5m': cpu_load_5m,
                'cpu_load_15m': cpu_load_15m
            }
        except Exception as e:
            logging.error(f"Error collecting CPU information: {e}")
            return {'success': False, 'message': f'Failed to collect CPU information: {e}'}

    def _collect_memory_info(self) -> Dict[str, Any]:
        """
        Collects system memory information including total, available, and used RAM.

        Returns:
            A dictionary containing memory information.
            Example:
            {
                'success': True,
                'message': 'Memory information collected successfully.',
                'total_gb': 16.0,
                'available_gb': 8.0,
                'used_gb': 8.0,
                'used_percent': 50.0,
                'swap_total_gb': 2.0,
                'swap_used_gb': 0.5,
                'swap_free_gb': 1.5,
                'swap_used_percent': 25.0
            }
            or
            {
                'success': False,
                'message': 'Failed to collect memory information: <error_message>'
            }
        """
        try:
            memory_info = psutil.virtual_memory()
            total_gb = round(memory_info.total / (1024**3), 2)
            available_gb = round(memory_info.available / (1024**3), 2)
            used_gb = round(memory_info.used / (1024**3), 2)
            used_percent = memory_info.percent

            # Collect swap information if available
            swap_info = psutil.swap_memory()
            swap_total_gb = round(swap_info.total / (1024**3), 2)
            swap_used_gb = round(swap_info.used / (1024**3), 2)
            swap_free_gb = round(swap_info.free / (1024**3), 2)
            swap_used_percent = swap_info.percent

            return {
                'success': True,
                'message': 'Memory information collected successfully.',
                'total_gb': total_gb,
                'available_gb': available_gb,
                'used_gb': used_gb,
                'used_percent': used_percent,
                'swap_total_gb': swap_total_gb,
                'swap_used_gb': swap_used_gb,
                'swap_free_gb': swap_free_gb,
                'swap_used_percent': swap_used_percent
            }
        except Exception as e:
            logging.error(f"Error collecting memory information: {e}")
            return {'success': False, 'message': f'Failed to collect memory information: {e}'}

    def _collect_disk_info(self) -> Dict[str, Any]:
        """
        Collects disk usage information for all mounted partitions.

        Returns:
            A dictionary containing disk usage information for each partition.
            Example:
            {
                'success': True,
                'message': 'Disk information collected successfully.',
                'partitions': [
                    {
                        'device': '/',
                        'mountpoint': '/',
                        'fstype': 'ext4',
                        'total_gb': 500.0,
                        'used_gb': 200.0,
                        'free_gb': 300.0,
                        'used_percent': 40.0
                    },
                    ...
                ]
            }
            or
            {
                'success': False,
                'message': 'Failed to collect disk information: <error_message>'
            }
        """
        try:
            partitions = psutil.disk_partitions()
            disk_usage_list = []
            for partition in partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_usage_list.append({
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype,
                        'total_gb': round(usage.total / (1024**3), 2),
                        'used_gb': round(usage.used / (1024**3), 2),
                        'free_gb': round(usage.free / (1024**3), 2),
                        'used_percent': usage.percent
                    })
                except (OSError, PermissionError) as e:
                    logging.warning(f"Could not access disk usage for {partition.mountpoint}: {e}")
                    disk_usage_list.append({
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype,
                        'total_gb': 'N/A',
                        'used_gb': 'N/A',
                        'free_gb': 'N/A',
                        'used_percent': 'N/A',
                        'error': str(e)
                    })

            return {
                'success': True,
                'message': 'Disk information collected successfully.',
                'partitions': disk_usage_list
            }
        except Exception as e:
            logging.error(f"Error collecting disk information: {e}")
            return {'success': False, 'message': f'Failed to collect disk information: {e}'}

    def _collect_network_info(self) -> Dict[str, Any]:
        """
        Collects network interface statistics.

        Returns:
            A dictionary containing network interface statistics.
            Example:
            {
                'success': True,
                'message': 'Network information collected successfully.',
                'interfaces': {
                    'en0': {
                        'mac_address': '00:1A:2B:3C:4D:5E',
                        'bytes_sent': 123456789,
                        'bytes_recv': 987654321,
                        'packets_sent': 10000,
                        'packets_recv': 20000,
                        'errors_sent': 5,
                        'errors_recv': 3
                    },
                    ...
                }
            }
            or
            {
                'success': False,
                'message': 'Failed to collect network information: <error_message>'
            }
        """
        try:
            net_io_counters = psutil.net_io_counters(pernic=True)
            network_stats = {}
            for interface, stats in net_io_counters.items():
                # Get MAC address - this can fail on some interfaces or OS versions
                mac_address = psutil.get_device_addresses(interface)[0].address if interface in psutil.net_if_addrs() and psutil.net_if_addrs()[interface] else 'N/A'
                
                network_stats[interface] = {
                    'mac_address': mac_address,
                    'bytes_sent': stats.bytes_sent,
                    'bytes_recv': stats.bytes_recv,
                    'packets_sent': stats.packets_sent,
                    'packets_recv': stats.packets_recv,
                    # psutil doesn't directly provide sent/recv errors in a cross-platform way.
                    # This might require platform-specific calls or parsing netstat.
                    # For simplicity and robustness, we'll omit them unless a reliable cross-platform method is found.
                    # Example of what could be added with platform-specific code:
                    # 'errors_sent': getattr(stats, 'errin', 'N/A'),
                    # 'errors_recv': getattr(stats, 'errout', 'N/A'),
                }
            return {
                'success': True,
                'message': 'Network information collected successfully.',
                'interfaces': network_stats
            }
        except Exception as e:
            logging.error(f"Error collecting network information: {e}")
            return {'success': False, 'message': f'Failed to collect network information: {e}'}

    def generate_report_data(self) -> Dict[str, Any]:
        """
        Generates a comprehensive system performance report by collecting data
        from various system components.

        This method aggregates the results from individual data collection methods.

        Returns:
            A dictionary containing the complete report data.
            Example:
            {
                'success': True,
                'message': 'System performance report generated successfully.',
                'report_details': {
                    'timestamp': '2023-10-27 10:30:00',
                    'system_info': {...},
                    'cpu_info': {...},
                    'memory_info': {...},
                    'disk_info': {...},
                    'network_info': {...}
                }
            }
            or
            {
                'success': False,
                'message': 'Failed to generate report: <error_message>'
            }
        """
        self.report_data.clear()
        self.report_data['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Collect system details
        sys_details_result = self._collect_system_details()
        if not sys_details_result['success']:
            logging.error(f"Report generation failed: {sys_details_result['message']}")
            return {'success': False, 'message': f'Report generation failed: {sys_details_result["message"]}'}
        self.report_data['system_info'] = sys_details_result

        # Collect CPU information
        cpu_info_result = self._collect_cpu_info()
        if not cpu_info_result['success']:
            logging.warning(f"CPU info collection failed: {cpu_info_result['message']}")
            self.report_data['cpu_info'] = {'success': False, 'message': cpu_info_result['message']}
        else:
            self.report_data['cpu_info'] = cpu_info_result

        # Collect Memory information
        memory_info_result = self._collect_memory_info()
        if not memory_info_result['success']:
            logging.warning(f"Memory info collection failed: {memory_info_result['message']}")
            self.report_data['memory_info'] = {'success': False, 'message': memory_info_result['message']}
        else:
            self.report_data['memory_info'] = memory_info_result

        # Collect Disk information
        disk_info_result = self._collect_disk_info()
        if not disk_info_result['success']:
            logging.warning(f"Disk info collection failed: {disk_info_result['message']}")
            self.report_data['disk_info'] = {'success': False, 'message': disk_info_result['message']}
        else:
            self.report_data['disk_info'] = disk_info_result

        # Collect Network information
        network_info_result = self._collect_network_info()
        if not network_info_result['success']:
            logging.warning(f"Network info collection failed: {network_info_result['message']}")
            self.report_data['network_info'] = {'success': False, 'message': network_info_result['message']}
        else:
            self.report_data['network_info'] = network_info_result

        return {
            'success': True,
            'message': 'System performance report data generated successfully.',
            'report_details': self.report_data
        }

    def _format_report(self, report_data: Dict[str, Any]) -> str:
        """
        Formats the collected report data into a human-readable string.

        Args:
            report_data: A dictionary containing the raw report data, typically
                         generated by generate_report_data().

        Returns:
            A formatted string representation of the report.
        """
        if not report_data or 'report_details' not in report_data:
            return "Error: No report data available to format."

        details = report_data['report_details']
        lines = []

        lines.append("=" * 70)
        lines.append("        SYSTEM PERFORMANCE REPORT")
        lines.append("=" * 70)
        lines.append(f"Report Generated: {details.get('timestamp', 'N/A')}\n")

        # System Information
        lines.append("--- System Information ---")
        sys_info = details.get('system_info', {})
        if sys_info.get('success', False):
            lines.append(f"  Operating System: {sys_info.get('system', 'N/A')} ({sys_info.get('release', 'N/A')})")
            lines.append(f"  Version:          {sys_info.get('version', 'N/A')}")
            lines.append(f"  Hostname:         {sys_info.get('node_name', 'N/A')}")
            lines.append(f"  Architecture:     {sys_info.get('machine', 'N/A')}")
            lines.append(f"  Processor:        {sys_info.get('processor', 'N/A')}")
        else:
            lines.append(f"  Error: {sys_info.get('message', 'Unknown error')}")
        lines.append("")

        # CPU Information
        lines.append("--- CPU Information ---")
        cpu_info = details.get('cpu_info', {})
        if cpu_info.get('success', False):
            lines.append(f"  Physical Cores:   {cpu_info.get('physical_cores', 'N/A')}")
            lines.append(f"  Logical Cores:    {cpu_info.get('logical_cores', 'N/A')}")
            lines.append(f"  Current Usage:    {cpu_info.get('usage_percent', 'N/A'):.2f}%")
            lines.append(f"  Load Average (1m):{cpu_info.get('cpu_load_1m', 'N/A'):.2f}")
            lines.append(f"  Load Average (5m):{cpu_info.get('cpu_load_5m', 'N/A'):.2f}")
            lines.append(f"  Load Average (15m):{cpu_info.get('cpu_load_15m', 'N/A'):.2f}")
        else:
            lines.append(f"  Error: {cpu_info.get('message', 'Unknown error')}")
        lines.append("")

        # Memory Information
        lines.append("--- Memory Information ---")
        mem_info = details.get('memory_info', {})
        if mem_info.get('success', False):
            lines.append(f"  Total RAM:        {mem_info.get('total_gb', 'N/A'):.2f} GB")
            lines.append(f"  Available RAM:    {mem_info.get('available_gb', 'N/A'):.2f} GB")
            lines.append(f"  Used RAM:         {mem_info.get('used_gb', 'N/A'):.2f} GB")
            lines.append(f"  Usage:            {mem_info.get('used_percent', 'N/A'):.2f}%")
            lines.append(f"  Swap Total:       {mem_info.get('swap_total_gb', 'N/A'):.2f} GB")
            lines.append(f"  Swap Used:        {mem_info.get('swap_used_gb', 'N/A'):.2f} GB")
            lines.append(f"  Swap Free:        {mem_info.get('swap_free_gb', 'N/A'):.2f} GB")
            lines.append(f"  Swap Usage:       {mem_info.get('swap_used_percent', 'N/A'):.2f}%")
        else:
            lines.append(f"  Error: {mem_info.get('message', 'Unknown error')}")
        lines.append("")

        # Disk Information
        lines.append("--- Disk Information ---")
        disk_info = details.get('disk_info', {})
        if disk_info.get('success', False):
            partitions = disk_info.get('partitions', [])
            if partitions:
                for part in partitions:
                    lines.append(f"  Mountpoint: {part.get('mountpoint', 'N/A')} ({part.get('device', 'N/A')})")
                    lines.append(f"    Filesystem Type: {part.get('fstype', 'N/A')}")
                    lines.append(f"    Total:           {part.get('total_gb', 'N/A') if isinstance(part.get('total_gb'), (int, float)) else part.get('total_gb')} GB")
                    lines.append(f"    Used:            {part.get('used_gb', 'N/A') if isinstance(part.get('used_gb'), (int, float)) else part.get('used_gb')} GB")
                    lines.append(f"    Free:            {part.get('free_gb', 'N/A') if isinstance(part.get('free_gb'), (int, float)) else part.get('free_gb')} GB")
                    lines.append(f"    Usage:           {part.get('used_percent', 'N/A'):.2f}%" if isinstance(part.get('used_percent'), (int, float)) else f"    Usage:           {part.get('used_percent', 'N/A')}")
                    if 'error' in part:
                        lines.append(f"    Warning: {part['error']}")
            else:
                lines.append("  No disk partitions found or accessible.")
        else:
            lines.append(f"  Error: {disk_info.get('message', 'Unknown error')}")
        lines.append("")

        # Network Information
        lines.append("--- Network Information ---")
        net_info = details.get('network_info', {})
        if net_info.get('success', False):
            interfaces = net_info.get('interfaces', {})
            if interfaces:
                for iface, stats in interfaces.items():
                    lines.append(f"  Interface: {iface}")
                    lines.append(f"    MAC Address:    {stats.get('mac_address', 'N/A')}")
                    lines.append(f"    Bytes Sent:     {stats.get('bytes_sent', 'N/A'):,}")
                    lines.append(f"    Bytes Received: {stats.get('bytes_recv', 'N/A'):,}")
                    lines.append(f"    Packets Sent:   {stats.get('packets_sent', 'N/A'):,}")
                    lines.append(f"    Packets Received:{stats.get('packets_recv', 'N/A'):,}")
            else:
                lines.append("  No network interfaces found or accessible.")
        else:
            lines.append(f"  Error: {net_info.get('message', 'Unknown error')}")
        lines.append("")
        
        # Example of adding process list - requires more sophisticated logic or external tools for detailed analysis
        # For a basic report, listing top N processes by CPU usage might be useful
        try:
            lines.append("--- Top Processes (by CPU Usage) ---")
            # Use psutil to get top processes. Limit to a reasonable number.
            top_processes = sorted(
                psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']),
                key=lambda p: p.info['cpu_percent'],
                reverse=True
            )[:5] # Get top 5 processes
            
            if top_processes:
                for proc in top_processes:
                    try:
                        pinfo = proc.info
                        lines.append(
                            f"  PID: {pinfo['pid']:<7} Name: {pinfo['name'][:30]:<30} User: {pinfo.get('username', 'N/A'):<10} CPU: {pinfo.get('cpu_percent', 0.0):.2f}% Mem: {pinfo.get('memory_percent', 0.0):.2f}%"
                        )
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        continue
            else:
                lines.append("  Could not retrieve top process information.")
        except Exception as e:
            logging.warning(f"Could not fetch top processes: {e}")
            lines.append("  Error retrieving top process information.")
        lines.append("")


        lines.append("=" * 70)
        lines.append("                  END OF REPORT")
        lines.append("=" * 70)

        return "\n".join(lines)

    def save_report(self, report_content: str) -> Dict[str, Any]:
        """
        Saves the formatted report content to a file.

        Args:
            report_content: The string content of the report to be saved.

        Returns:
            A dictionary indicating the success or failure of the save operation.
            Example:
            {
                'success': True,
                'message': f'Performance report successfully saved to {self.report_filename}',
                'filename': 'performance_report.txt'
            }
            or
            {
                'success': False,
                'message': f'Failed to save performance report to {self.report_filename}: <error_message>',
                'filename': 'performance_report.txt'
            }
        """
        if not report_content:
            logging.error("No report content provided to save.")
            return {
                'success': False,
                'message': 'No report content provided to save.',
                'filename': self.report_filename
            }

        try:
            with open(self.report_filename, "w", encoding="utf-8") as f:
                f.write(report_content)
            logging.info(f"Performance report saved to {self.report_filename}")
            return {
                'success': True,
                'message': f'Performance report successfully saved to {self.report_filename}',
                'filename': self.report_filename
            }
        except IOError as e:
            logging.error(f"Error saving report to {self.report_filename}: {e}")
            return {
                'success': False,
                'message': f'Failed to save performance report to {self.report_filename}: {e}',
                'filename': self.report_filename
            }
        except Exception as e:
            logging.error(f"An unexpected error occurred while saving the report: {e}")
            return {
                'success': False,
                'message': f'An unexpected error occurred while saving the report: {e}',
                'filename': self.report_filename
            }

    def create_and_save_report(self) -> Dict[str, Any]:
        """
        Orchestrates the entire process of generating and saving the performance report.

        This is the main method to call for creating the report file.

        Returns:
            A dictionary indicating the overall success or failure of the report creation and saving process.
            The dictionary will contain 'success', 'message', and 'filename' if successful.
        """
        logging.info(f"Starting system performance report generation for: {self.report_filename}")
        report_data_result = self.generate_report_data()

        if not report_data_result['success']:
            logging.error(f"Report data generation failed: {report_data_result['message']}")
            return {
                'success': False,
                'message': f'Failed to generate report data: {report_data_result["message"]}',
                'filename': None
            }

        # Ensure we have report details before formatting
        if 'report_details' not in report_data_result:
             logging.error("Report generation succeeded but 'report_details' are missing.")
             return {
                'success': False,
                'message': 'Report generation succeeded but missing required details.',
                'filename': None
            }

        formatted_report = self._format_report(report_data_result)
        save_result = self.save_report(formatted_report)

        if not save_result['success']:
            logging.error(f"Report saving failed: {save_result['message']}")
            return {
                'success': False,
                'message': f'Report generated but failed to save: {save_result["message"]}',
                'filename': save_result.get('filename')
            }
        else:
            logging.info("System performance report created and saved successfully.")
            return {
                'success': True,
                'message': f'System performance report created and saved successfully to {save_result["filename"]}',
                'filename': save_result['filename']
            }

if __name__ == '__main__':
    # Example usage:
    print("--- Generating default performance_report.txt ---")
    try:
        reporter = SystemPerformanceReporter()
        result = reporter.create_and_save_report()

        if result['success']:
            print(f"Report created: {result['message']}")
            # Optionally, you can read and print the report file
            try:
                with open(reporter.report_filename, 'r', encoding='utf-8') as f:
                    print("\n--- Content of performance_report.txt ---")
                    print(f.read())
            except FileNotFoundError:
                print(f"Error: Report file '{reporter.report_filename}' not found after creation attempt.")
        else:
            print(f"Error creating report: {result['message']}")
    except ValueError as ve:
        print(f"Initialization Error: {ve}")
    except Exception as e:
        print(f"An unexpected error occurred during the default report generation: {e}")


    # Example with a different filename
    print("\n--- Generating report with a custom filename ---")
    try:
        custom_reporter = SystemPerformanceReporter("my_custom_performance_report.txt")
        custom_result = custom_reporter.create_and_save_report()
        if custom_result['success']:
            print(f"Report created: {custom_result['message']}")
        else:
            print(f"Error creating report: {custom_result['message']}")
    except ValueError as ve:
        print(f"Initialization Error: {ve}")
    except Exception as e:
        print(f"An unexpected error occurred during the custom report generation: {e}")

    # Example with an invalid filename to demonstrate validation
    print("\n--- Attempting to generate report with an invalid filename ---")
    try:
        invalid_reporter = SystemPerformanceReporter("") # Empty filename
        invalid_reporter.create_and_save_report()
    except ValueError as ve:
        print(f"Caught expected error: {ve}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
