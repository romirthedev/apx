
import subprocess
import platform
import json
from typing import Dict, Any, List, Optional, Callable

class SecurityAuditTool:
    """
    A specialized Python tool for generating detailed security audit reports,
    including vulnerability assessments and recommendations.

    This tool is designed to be safe and does not perform any system modifications.
    It relies on external command-line tools to gather security information.
    Compatibility is primarily tested with macOS.

    The tool's core functionality is enhanced to address the user request for
    detailed security audits with vulnerability assessments and recommendations,
    leveraging a more structured approach to data collection and analysis.
    """

    def __init__(self, system_commands: Optional[Dict[str, str]] = None):
        """
        Initializes the SecurityAuditTool.

        Args:
            system_commands: A dictionary where keys are command names (e.g., 'system_info')
                             and values are the corresponding command-line strings.
                             If None, default commands will be used (optimized for macOS).
        """
        self.system_commands = system_commands if system_commands else self._get_default_commands()
        self._validate_commands()

    def _validate_commands(self):
        """Validates that all required command keys are present in system_commands."""
        required_keys = [
            "system_info",
            "network_listening_ports",
            "running_processes",
            "open_files",
            "firewall_status",
            "installed_software",
            "recent_system_logs",
            "disk_permissions",
            "scheduled_tasks"
        ]
        for key in required_keys:
            if key not in self.system_commands or not self.system_commands[key]:
                raise ValueError(f"Missing or empty command for '{key}'. Please provide a valid command string.")

    def _get_default_commands(self) -> Dict[str, str]:
        """
        Returns a dictionary of default command-line commands for various
        security audit tasks, optimized for macOS.
        """
        if platform.system() == "Darwin":
            return {
                "system_info": "system_profiler SPHardwareDataType SPSoftwareDataType SPNetworkDataType",
                "network_listening_ports": "lsof -i -P | grep LISTEN",
                "running_processes": "ps aux",
                "open_files": "lsof",
                "firewall_status": "sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate",
                "installed_software": "system_profiler SPApplicationsDataType",
                "recent_system_logs": "log show --last 1h --predicate 'eventMessage contains \"failed\" or eventMessage contains \"error\" or eventMessage contains \"denied\"' --style syslog",
                "disk_permissions": "diskutil list", # More basic disk info for wider compatibility, granular requires root
                "scheduled_tasks": "launchctl list"
            }
        else:
            # Placeholder for non-macOS systems, might require different commands.
            # For now, it will raise an error if not on macOS and no commands are provided.
            raise NotImplementedError("Default commands are not defined for this operating system. "
                                      "Please provide a custom 'system_commands' dictionary.")

    def _run_command(self, command: str) -> Dict[str, Any]:
        """
        Executes a shell command and returns the output and status.

        Args:
            command: The command string to execute.

        Returns:
            A dictionary containing:
            - 'success' (bool): True if the command executed successfully, False otherwise.
            - 'message' (str): A descriptive message of the outcome.
            - 'output' (str or None): The command's stdout if successful, None otherwise.
            - 'error' (str or None): The command's stderr if failed, None otherwise.
        """
        try:
            # Use check=False to capture non-zero exit codes as errors gracefully
            result = subprocess.run(
                command,
                shell=True,
                check=False,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            if result.returncode == 0:
                return {
                    "success": True,
                    "message": "Command executed successfully.",
                    "output": result.stdout,
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "message": f"Command failed with exit code {result.returncode}: {result.stderr.strip()}",
                    "output": None,
                    "error": result.stderr.strip()
                }
        except FileNotFoundError:
            return {
                "success": False,
                "message": f"Command not found: '{command.split()[0]}'. Ensure required tools are installed and in PATH.",
                "output": None,
                "error": f"Command not found: '{command.split()[0]}'"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"An unexpected error occurred during command execution: {e}",
                "output": None,
                "error": str(e)
            }

    def _parse_system_info(self, output: str) -> Dict[str, Any]:
        """Parses the output of 'system_profiler'."""
        info_data = {"hardware": {}, "software": {}, "network": {}, "system": {}}
        current_section = None
        lines = output.splitlines()
        for line in lines:
            stripped_line = line.strip()
            if not stripped_line:
                continue

            if stripped_line.endswith(':'):
                section_name = stripped_line[:-1].lower().replace(' ', '_')
                if section_name in ["hardware_overview", "software_overview", "network_overview"]:
                    current_section = section_name.split('_')[0] # Use hardware, software, network
                elif section_name == "system_report": # Special case for overall system info
                    current_section = "system"
                else:
                    # For specific details within a section, e.g., "Processor Name:"
                    # We'll associate it with the last known section.
                    pass

                if current_section and section_name not in info_data:
                    # Initialize sub-sections if they don't exist, but only for top-level ones
                    pass
                continue

            if current_section:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    if key: # Ensure key is not empty
                        if current_section == "hardware":
                            info_data["hardware"][key] = value
                        elif current_section == "software":
                            info_data["software"][key] = value
                        elif current_section == "network":
                            info_data["network"][key] = value
                        elif current_section == "system":
                            info_data["system"][key] = value
                else:
                    # Handle potential multiline values if needed, but for now, assume simple key-value
                    pass
        return info_data

    def _parse_network_listening_ports(self, output: str) -> List[Dict[str, str]]:
        """Parses the output of 'lsof -i -P | grep LISTEN'."""
        ports_data = []
        lines = output.splitlines()
        for line in lines:
            parts = line.split()
            if len(parts) >= 9:
                try:
                    ports_data.append({
                        "command": parts[0],
                        "pid": parts[1],
                        "user": parts[2],
                        "fd": parts[3],
                        "type": parts[4],
                        "device": parts[5],
                        "node": parts[6],
                        "name": " ".join(parts[7:]), # The rest is the connection info
                    })
                except IndexError:
                    # Skip malformed lines
                    continue
        return ports_data

    def _parse_running_processes(self, output: str) -> List[Dict[str, str]]:
        """Parses the output of 'ps aux'."""
        processes_data = []
        lines = output.splitlines()
        if not lines:
            return []

        # Split based on known fields and then assume the rest is the command
        # This is a heuristic and might fail for commands with specific whitespace patterns.
        header = lines[0].split()
        # Expected header fields: USER, PID, %CPU, %MEM, VSZ, RSS, TTY, STAT, START, TIME, COMMAND
        # We'll map them to indices. This assumes a standard ps aux output format.
        # A more robust solution might involve regex or more careful splitting.

        for line in lines[1:]:
            # Attempt to split command carefully
            parts = line.split(maxsplit=10)
            if len(parts) >= 11: # Expecting at least 10 fields + command
                processes_data.append({
                    "user": parts[0],
                    "pid": parts[1],
                    "cpu_percent": parts[2],
                    "mem_percent": parts[3],
                    "vsz": parts[4],
                    "rss": parts[5],
                    "tty": parts[6],
                    "stat": parts[7],
                    "start_time": parts[8],
                    "time": parts[9], # Added TIME field
                    "command": parts[10]
                })
            elif len(parts) > 0: # Handle cases where command might be missing or line is truncated
                # Try to fill as much as possible
                process_info = {
                    "user": parts[0] if len(parts) > 0 else "N/A",
                    "pid": parts[1] if len(parts) > 1 else "N/A",
                    "cpu_percent": parts[2] if len(parts) > 2 else "N/A",
                    "mem_percent": parts[3] if len(parts) > 3 else "N/A",
                    "vsz": parts[4] if len(parts) > 4 else "N/A",
                    "rss": parts[5] if len(parts) > 5 else "N/A",
                    "tty": parts[6] if len(parts) > 6 else "N/A",
                    "stat": parts[7] if len(parts) > 7 else "N/A",
                    "start_time": parts[8] if len(parts) > 8 else "N/A",
                    "time": parts[9] if len(parts) > 9 else "N/A",
                    "command": " ".join(parts[10:]) if len(parts) > 10 else " ".join(parts[10:]) # Fallback for command
                }
                processes_data.append(process_info)
        return processes_data


    def _parse_open_files(self, output: str) -> List[Dict[str, str]]:
        """Parses the output of 'lsof'."""
        files_data = []
        lines = output.splitlines()
        for line in lines[1:]: # Skip header
            parts = line.split()
            if len(parts) >= 9:
                try:
                    files_data.append({
                        "command": parts[0],
                        "pid": parts[1],
                        "user": parts[2],
                        "fd": parts[3],
                        "type": parts[4],
                        "device": parts[5],
                        "node": parts[6],
                        "name": " ".join(parts[7:])
                    })
                except IndexError:
                    continue # Skip malformed lines
        return files_data

    def _parse_firewall_status(self, output: str) -> Dict[str, Any]:
        """Parses the output of firewall status command."""
        status = {"enabled": False, "message": output.strip()}
        if "Firewall is enabled." in output or "Firewall is enabled" in output:
            status["enabled"] = True
        elif "Firewall is disabled." in output or "Firewall is disabled" in output:
            status["enabled"] = False
        else:
            status["message"] = f"Could not determine firewall status. Raw output: {output.strip()}"
        return status

    def _parse_installed_software(self, output: str) -> List[Dict[str, str]]:
        """Parses the output of 'system_profiler SPApplicationsDataType'."""
        software_data = []
        lines = output.splitlines()
        current_app = {}
        for line in lines:
            stripped_line = line.strip()
            if not stripped_line:
                if current_app.get("name"): # Only add if we have a name
                    software_data.append(current_app)
                current_app = {}
                continue

            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                if key == "Location":
                    current_app["path"] = value
                elif key == "Version":
                    current_app["version"] = value
                elif key == "Obtained from":
                    current_app["source"] = value
                elif key == "Last Modified":
                    current_app["last_modified"] = value
                elif key == "Bundle ID":
                    current_app["bundle_id"] = value
                elif key == "Name":
                    current_app["name"] = value
            elif "Applications" in line and "Information" in line:
                continue # Skip header lines
            elif "Total:" in line:
                continue # Skip summary lines

        if current_app.get("name"): # Add the last app if any
            software_data.append(current_app)

        return software_data

    def _parse_recent_system_logs(self, output: str) -> List[str]:
        """Parses the output of system logs, returning lines that indicate issues."""
        return output.splitlines()

    def _parse_disk_permissions(self, output: str) -> Dict[str, Any]:
        """
        Parses basic disk info using `diskutil list`.
        More granular permissions would require extensive parsing and likely root access.
        """
        disk_info = {"disks": []}
        current_disk = None
        lines = output.splitlines()
        for line in lines:
            stripped_line = line.strip()
            if not stripped_line:
                continue

            # Detect start of a new disk entry
            if stripped_line.startswith("/dev/disk"):
                if current_disk:
                    disk_info["disks"].append(current_disk)
                parts = stripped_line.split()
                if len(parts) > 1:
                    disk_identifier = parts[0]
                    disk_name = " ".join(parts[1:])
                    current_disk = {
                        "identifier": disk_identifier,
                        "name": disk_name,
                        "partitions": []
                    }
            # Detect partitions within a disk
            elif current_disk and (stripped_line.startswith("   #: ") or stripped_line.startswith("   # ")):
                # Example line: "   #:                TYPE NAME                    SIZE       IDENTIFIER"
                # Example partition: "    0:                Apple_HFS Macintosh HD           500.3 GB   disk1s1"
                partition_parts = stripped_line.split(maxsplit=4)
                if len(partition_parts) >= 4:
                    try:
                        partition_index = partition_parts[0].split(':')[-1] # "0:" -> "0"
                        partition_type = partition_parts[1]
                        partition_name = partition_parts[2]
                        partition_size = partition_parts[3]
                        partition_identifier = partition_parts[4] if len(partition_parts) > 4 else "N/A"
                        current_disk["partitions"].append({
                            "index": partition_index,
                            "type": partition_type,
                            "name": partition_name,
                            "size": partition_size,
                            "identifier": partition_identifier
                        })
                    except (IndexError, ValueError):
                        continue # Skip malformed partition lines
        if current_disk: # Add the last disk
            disk_info["disks"].append(current_disk)
        return disk_info

    def _parse_scheduled_tasks(self, output: str) -> List[Dict[str, str]]:
        """Parses the output of 'launchctl list'."""
        tasks_data = []
        lines = output.splitlines()
        for line in lines[1:]: # Skip header
            parts = line.split()
            if len(parts) >= 3:
                tasks_data.append({
                    "pid": parts[0],
                    "exit_status": parts[1],
                    "label": " ".join(parts[2:]) # Label can contain spaces
                })
        return tasks_data

    def get_vulnerability_assessments(self) -> Dict[str, Any]:
        """
        Performs a comprehensive security audit, gathering information from
        various system commands.

        This method collects data related to system information, network activity,
        running processes, open files, firewall status, installed software,
        recent logs, disk partitioning, and scheduled tasks.

        Returns:
            A dictionary containing:
            - 'success' (bool): True if all audits completed successfully, False otherwise.
            - 'message' (str): A summary message indicating the overall status.
            - 'assessments' (dict): A dictionary where keys are assessment types
              (e.g., 'system_info', 'network_listening_ports') and values are the
              parsed results of each assessment. If an assessment fails, its entry
              will contain an error message.
        """
        all_assessments: Dict[str, Any] = {}
        overall_success = True

        # Mapping of assessment names to command keys and parsing functions
        # Each tuple: (command_key, parser_function)
        assessment_map: Dict[str, tuple[str, Callable[[str], Any]]] = {
            "system_info": ("system_info", self._parse_system_info),
            "network_listening_ports": ("network_listening_ports", self._parse_network_listening_ports),
            "running_processes": ("running_processes", self._parse_running_processes),
            "open_files": ("open_files", self._parse_open_files),
            "firewall_status": ("firewall_status", self._parse_firewall_status),
            "installed_software": ("installed_software", self._parse_installed_software),
            "recent_system_logs": ("recent_system_logs", self._parse_recent_system_logs),
            "disk_info": ("disk_permissions", self._parse_disk_permissions), # Renamed for clarity
            "scheduled_tasks": ("scheduled_tasks", self._parse_scheduled_tasks)
        }

        for assessment_name, (command_key, parser_func) in assessment_map.items():
            command = self.system_commands.get(command_key)
            if not command:
                all_assessments[assessment_name] = {
                    "success": False,
                    "message": f"Command for '{assessment_name}' not defined in configuration.",
                    "data": None
                }
                overall_success = False
                continue

            command_result = self._run_command(command)

            if command_result["success"]:
                try:
                    parsed_data = parser_func(command_result["output"])
                    all_assessments[assessment_name] = {
                        "success": True,
                        "message": "Assessment completed successfully.",
                        "data": parsed_data
                    }
                except Exception as e:
                    all_assessments[assessment_name] = {
                        "success": False,
                        "message": f"Error parsing command output for '{assessment_name}': {e}",
                        "data": None
                    }
                    overall_success = False
            else:
                all_assessments[assessment_name] = {
                    "success": False,
                    "message": command_result["message"],
                    "data": None
                }
                overall_success = False

        return {
            "success": overall_success,
            "message": "Security audit data collection completed with " + ("no errors" if overall_success else "one or more errors/warnings"),
            "assessments": all_assessments
        }

    def _analyze_for_vulnerabilities(self, audit_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyzes audit results to identify potential vulnerabilities.
        This is where specialized vulnerability assessment logic resides.
        """
        vulnerabilities: List[Dict[str, Any]] = []

        if not audit_results.get("assessments"):
            return vulnerabilities # No assessments to analyze

        assessments = audit_results["assessments"]

        # Vulnerability 1: Firewall Status
        firewall_status_data = assessments.get("firewall_status", {}).get("data")
        if firewall_status_data and not firewall_status_data.get("enabled"):
            vulnerabilities.append({
                "id": "VULN-FW-001",
                "severity": "High",
                "description": "System firewall is disabled. This leaves the system exposed to unauthorized network access.",
                "impact": "Unauthorized access, data breaches, malware infections.",
                "recommendation": "Enable the system firewall and configure it with appropriate rules to block unwanted incoming traffic.",
                "related_assessment": "firewall_status"
            })

        # Vulnerability 2: Listening Services (unnecessary or unconfigured)
        listening_ports_data = assessments.get("network_listening_ports", {}).get("data")
        if listening_ports_data:
            # A more advanced tool would check against known vulnerable services or default configurations.
            # Here we flag any non-root process listening on common sensitive ports as a potential risk.
            sensitive_ports = {"21", "22", "23", "25", "80", "110", "143", "443", "445", "3306", "5432", "5900", "8080", "8443"}
            for port_info in listening_ports_data:
                port_str = port_info.get("name", "")
                try:
                    # Extract port number from string like '*:80 (LISTEN)' or 'localhost:443 (LISTEN)'
                    port_num = port_str.split(":")[-1].split(" ")[0]
                    if port_num in sensitive_ports and port_info.get("user") != "root":
                        vulnerabilities.append({
                            "id": "VULN-NET-002",
                            "severity": "Medium",
                            "description": f"Process '{port_info.get('command')}' (PID: {port_info.get('pid')}) is listening on port {port_num} with user '{port_info.get('user')}'. This could indicate an unprivileged service with potential vulnerabilities or misconfigurations.",
                            "impact": "Potential for privilege escalation, unauthorized data access, or service disruption.",
                            "recommendation": f"Review the service listening on port {port_num}. Ensure it is necessary, properly configured, and running with least privilege. Consider restricting access to this port.",
                            "related_assessment": "network_listening_ports"
                        })
                except IndexError:
                    pass # Ignore if port parsing fails

        # Vulnerability 3: Outdated Software (heuristic)
        installed_software_data = assessments.get("installed_software", {}).get("data")
        if installed_software_data:
            # This is a *very* basic heuristic. A real vulnerability scanner would cross-reference versions with CVE databases.
            # We flag applications with versions that might be considered old based on common patterns.
            outdated_patterns = ["1.0", "1.1", "1.2", "2.0"] # Example patterns that might indicate older versions
            for app in installed_software_data:
                version = app.get("version", "")
                if version:
                    for pattern in outdated_patterns:
                        if version.startswith(pattern) and "." in version[len(pattern):]: # e.g., 1.0.1, but not 1.0 (as is)
                            vulnerabilities.append({
                                "id": "VULN-SW-003",
                                "severity": "Low",
                                "description": f"Application '{app.get('name')}' has version '{version}'. This version might be outdated and contain known vulnerabilities. Check for updates.",
                                "impact": "Exploitation of known software vulnerabilities.",
                                "recommendation": f"Update '{app.get('name')}' to the latest available version to patch known security issues.",
                                "related_assessment": "installed_software"
                            })
                            break # No need to check other patterns for this app

        # Vulnerability 4: Excessive Errors in System Logs
        recent_logs_data = assessments.get("recent_system_logs", {}).get("data")
        if recent_logs_data and len(recent_logs_data) > 30: # Arbitrary threshold for "excessive"
            vulnerabilities.append({
                "id": "VULN-LOG-004",
                "severity": "Medium",
                "description": f"A high number of error/failure/denied messages ({len(recent_logs_data)}) were detected in recent system logs. This could indicate ongoing security incidents or system instability.",
                "impact": "May mask or indicate active attacks, system compromise, or critical failures.",
                "recommendation": "Investigate the specific log entries to identify the root cause of these errors. Look for patterns that suggest malicious activity.",
                "related_assessment": "recent_system_logs"
            })

        # Vulnerability 5: Running Processes with Suspicious Characteristics (Heuristic)
        running_processes_data = assessments.get("running_processes", {}).get("data")
        if running_processes_data:
            for process in running_processes_data:
                command = process.get("command", "").lower()
                user = process.get("user", "")
                # Example: processes with no TTY, running as root, with suspicious command names
                if not process.get("tty") and user == "root" and ("nc" in command or "netcat" in command or "bash -i" in command or "sh -i" in command):
                    vulnerabilities.append({
                        "id": "VULN-PROC-005",
                        "severity": "High",
                        "description": f"Process '{process.get('command')}' (PID: {process.get('pid')}) is running as root without a controlling terminal (TTY) and has suspicious command-line arguments often associated with reverse shells or network intrusion tools.",
                        "impact": "Potential for remote code execution and system compromise.",
                        "recommendation": "Immediately investigate this process. If it is not legitimate, terminate it and determine the source of its execution. Audit system for further signs of compromise.",
                        "related_assessment": "running_processes"
                    })
                # Example: unprivileged user running potentially sensitive system binaries
                if user != "root" and command.startswith(("/usr/bin/", "/bin/")):
                    vulnerabilities.append({
                        "id": "VULN-PROC-006",
                        "severity": "Medium",
                        "description": f"Process '{process.get('command')}' (PID: {process.get('pid')}) is running as user '{user}' but appears to be a core system binary. Ensure this is intentional and not a compromised or misconfigured process.",
                        "impact": "Could indicate a privilege escalation attempt or a misconfiguration leading to unexpected behavior.",
                        "recommendation": "Verify why this system binary is being executed by an unprivileged user. Ensure its execution context is appropriate.",
                        "related_assessment": "running_processes"
                    })

        # Vulnerability 6: Unsigned Applications (macOS specific, if possible)
        # This requires calling another command for each app, which can be slow.
        # For this example, we'll just add a placeholder note if the functionality were implemented.
        # try:
        #     for app in installed_software_data:
        #         app_path = app.get("path")
        #         if app_path and app_path.endswith(".app"):
        #             # Basic check for `.app` bundles
        #             codesign_cmd = f"codesign -dv '{app_path}'"
        #             codesign_result = self._run_command(codesign_cmd)
        #             if codesign_result["success"]:
        #                 if "Authority=Developer ID Application" not in codesign_result["output"] and \
        #                    "Authority=Apple Software" not in codesign_result["output"] and \
        #                    "signed at leaf" not in codesign_result["output"]: # Simplified check
        #                     vulnerabilities.append({
        #                         "id": "VULN-SW-007",
        #                         "severity": "Low",
        #                         "description": f"Application '{app.get('name')}' at '{app_path}' is not properly signed or is unsigned. This increases the risk of running malicious software.",
        #                         "impact": "Risk of running malware or tampered applications.",
        #                         "recommendation": "Ensure all installed applications are from trusted sources and are properly signed. Uninstall unsigned or untrusted applications.",
        #                         "related_assessment": "installed_software"
        #                     })
        #             else:
        #                 # Handle cases where codesign might fail (e.g., permissions)
        #                 pass # Silently skip or log as a potential issue if needed
        # except Exception as e:
        #     # Handle potential errors during codesign checks
        #     pass

        return vulnerabilities

    def generate_recommendations(self, audit_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates security recommendations based on identified vulnerabilities.

        Args:
            audit_results: The output dictionary from the `get_vulnerability_assessments` method.

        Returns:
            A dictionary containing:
            - 'success' (bool): True if recommendations were generated, False otherwise.
            - 'message' (str): A summary message.
            - 'recommendations' (list): A list of dictionaries, each representing a recommendation.
                                         Each recommendation has 'severity', 'description', and 'related_assessment'.
        """
        recommendations: List[Dict[str, Any]] = []
        overall_success = True

        if not audit_results.get("success", False) or not audit_results.get("assessments"):
            return {
                "success": False,
                "message": "No valid audit results provided for generating recommendations.",
                "recommendations": []
            }

        vulnerabilities = self._analyze_for_vulnerabilities(audit_results)

        if not vulnerabilities:
            recommendations.append({
                "severity": "Informational",
                "description": "No critical or high-severity vulnerabilities were automatically detected. Continue with regular security practices.",
                "related_assessment": None,
                "recommendation_id": "REC-INFO-001"
            })
        else:
            # Convert vulnerabilities into a more user-friendly recommendation format
            for vuln in vulnerabilities:
                recommendations.append({
                    "severity": vuln["severity"],
                    "description": f"({vuln['id']}) {vuln['description']} Impact: {vuln.get('impact', 'N/A')}",
                    "recommendation": vuln["recommendation"],
                    "related_assessment": vuln["related_assessment"],
                    "recommendation_id": vuln["id"] # Use vulnerability ID as recommendation ID
                })
            overall_success = not any(rec["severity"] in ["High", "Medium"] for rec in recommendations)

        return {
            "success": True, # Success here means we attempted to generate recommendations, not that the system is secure.
            "message": f"Generated {len(recommendations)} security recommendations based on {len(vulnerabilities)} detected potential vulnerabilities.",
            "recommendations": recommendations
        }

    def run_audit_and_recommendations(self) -> Dict[str, Any]:
        """
        Executes the full security audit and generates recommendations.

        This method first calls `get_vulnerability_assessments` to gather data
        and then uses these results to call `generate_recommendations`.

        Returns:
            A dictionary containing:
            - 'success' (bool): True if the entire process (audit and recommendations)
                                succeeded and no critical/high vulnerabilities were found, False otherwise.
            - 'message' (str): A summary message of the overall process.
            - 'audit_results' (dict): The detailed results from `get_vulnerability_assessments`.
            - 'recommendations' (dict): The results from `generate_recommendations`.
        """
        print("Step 1: Gathering security assessment data...")
        audit_results = self.get_vulnerability_assessments()

        print("Step 2: Analyzing findings and generating recommendations...")
        recommendations_results = self.generate_recommendations(audit_results)

        final_overall_success = audit_results.get("success", False)
        has_critical_or_high_severity = False
        if recommendations_results.get("recommendations"):
            for rec in recommendations_results["recommendations"]:
                if rec.get("severity") in ["High", "Medium"]:
                    has_critical_or_high_severity = True
                    break
        
        # Overall success is TRUE if no critical/high issues are found AND audit data was collected without major errors.
        overall_status_success = final_overall_success and not has_critical_or_high_severity

        return {
            "success": overall_status_success,
            "message": "Security audit and recommendation process completed. " +
                       ("System appears to be in a good security posture." if overall_status_success else 
                        "Security vulnerabilities/recommendations were identified. Please review the report."),
            "audit_results": audit_results,
            "recommendations": recommendations_results
        }

if __name__ == '__main__':
    # Example Usage
    print("Initializing Security Audit Tool...")
    try:
        # To test on systems other than macOS, you would need to provide custom commands:
        # custom_commands = {
        #     "system_info": "uname -a && lsb_release -a",
        #     "network_listening_ports": "sudo netstat -tulnp",
        #     "running_processes": "ps aux",
        #     "open_files": "lsof",
        #     "firewall_status": "sudo ufw status", # Example for Ubuntu/Debian
        #     "installed_software": "dpkg -l | grep -v \"^rc\" | grep -v \"^un\" | awk '{print $2, $3}'", # Example for Debian/Ubuntu
        #     "recent_system_logs": "journalctl -n 50 --priority=err --priority=warning", # Example for systemd systems
        #     "disk_permissions": "lsblk -o NAME,SIZE,TYPE", # Example for Linux
        #     "scheduled_tasks": "crontab -l" # Example for user cron jobs
        # }
        # tool = SecurityAuditTool(system_commands=custom_commands)
        
        tool = SecurityAuditTool()

        print("\nRunning full audit and generating recommendations...")
        report = tool.run_audit_and_recommendations()

        print("\n--- Security Audit Report ---")
        print(json.dumps(report, indent=2))

        # Enhanced reporting for user-friendliness
        print("\n--- Summary ---")
        if report.get("success"):
            print("Overall Security Status: Good (No critical or high-severity vulnerabilities detected)")
        else:
            print("Overall Security Status: Requires Attention (Critical or high-severity vulnerabilities detected)")
            
        audit_findings = report.get("audit_results", {})
        if not audit_findings.get("success"):
            print("Audit Data Collection Issues: Please review the 'audit_results' for specific errors.")

        print("\n--- Audit Findings Details ---")
        if audit_findings.get("success"):
            print("Audit assessments completed successfully.")
            for assessment_name, assessment_data in audit_findings.get("assessments", {}).items():
                print(f"\n{assessment_name.replace('_', ' ').title()}:")
                if assessment_data.get("success"):
                    print("  Status: Success")
                    data = assessment_data.get("data")
                    if isinstance(data, list) and data:
                        print(f"  Records found: {len(data)}")
                        for i, item in enumerate(data[:3]): # Print first few records as examples
                            print(f"    {i+1}. {item}")
                        if len(data) > 3:
                            print("    ...")
                    elif isinstance(data, dict) and data:
                        print(f"  Details:")
                        for k, v in list(data.items())[:3]: # Print first few key-value pairs
                            print(f"    {k}: {v}")
                        if len(data) > 3:
                            print("    ...")
                    elif data:
                        print(f"  Output snippet: {str(data)[:100]}...")
                    else:
                        print("  No specific data found.")
                else:
                    print(f"  Status: Failed - {assessment_data.get('message')}")
        else:
            print("Audit assessments encountered errors:")
            for assessment_name, assessment_data in audit_findings.get("assessments", {}).items():
                if not assessment_data.get("success"):
                    print(f"- {assessment_name.replace('_', ' ').title()}: {assessment_data.get('message')}")

        print("\n--- Security Recommendations ---")
        recommendations_section = report.get("recommendations", {})
        if recommendations_section.get("success"):
            if recommendations_section.get("recommendations"):
                for rec in recommendations_section["recommendations"]:
                    print(f"- [{rec['severity']}] {rec['description']}")
                    if rec.get('recommendation'):
                        print(f"  Recommendation: {rec['recommendation']}")
                    if rec.get('related_assessment'):
                        print(f"  Related to: {rec['related_assessment']}")
            else:
                print("No specific recommendations made.")
        else:
            print("Failed to generate recommendations.")

    except NotImplementedError as e:
        print(f"Error: {e}")
    except ValueError as e:
        print(f"Configuration Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during example execution: {e}")
