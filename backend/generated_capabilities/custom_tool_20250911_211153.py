
import os
import platform
import subprocess
import json
import sys
from typing import Dict, Any, List, Optional, Union
from collections import defaultdict

class SecurityAuditTool:
    """
    A comprehensive security audit tool for macOS systems.

    This tool provides methods to perform various security checks and generate
    structured audit reports. It is designed to be safe and does not modify
    system configurations without explicit user permission.

    The current implementation focuses on system-level configurations and
    basic checks. For advanced security scanning and vulnerability assessment,
    integration with specialized external tools would be necessary, as noted
    in the initial context.
    """

    def __init__(self):
        """Initializes the SecurityAuditTool."""
        if platform.system() != "Darwin":
            raise EnvironmentError("This tool is designed for macOS only.")
        self.os_type = platform.system()
        self.os_version = platform.mac_ver()[0]

        # Define required functions for context fulfillment
        self.required_functions = [
            "security scanning tools",
            "vulnerability assessment tools",
            "log analysis tools",
            "security reporting frameworks"
        ]
        self.missing_capability = (
            "The ability to perform security scans, analyze security vulnerabilities, "
            "and generate a report based on audit findings. This requires specialized "
            "security tools and domain expertise. This tool provides foundational "
            "system checks, but not full-scale vulnerability scanning."
        )

    def _run_command(
        self,
        command: List[str],
        capture_output: bool = True,
        text: bool = True,
        shell: bool = False,
        timeout: Optional[int] = 60  # Added timeout for commands
    ) -> Dict[str, Any]:
        """
        Safely runs a system command with enhanced error handling and logging.

        Args:
            command: A list of strings representing the command and its arguments.
            capture_output: Whether to capture the command's output.
            text: Whether to decode stdout and stderr as text.
            shell: Whether to use the shell.
            timeout: Maximum time in seconds to wait for the command to complete.

        Returns:
            A dictionary containing 'success', 'message', 'stdout', 'stderr',
            and 'returncode'.
        """
        command_str = " ".join(command)
        try:
            process = subprocess.run(
                command,
                capture_output=capture_output,
                text=text,
                check=False,  # Don't raise exception for non-zero exit codes
                shell=shell,
                timeout=timeout
            )
            if process.returncode == 0:
                return {
                    "success": True,
                    "message": f"Command '{command_str}' executed successfully.",
                    "stdout": process.stdout.strip() if capture_output and process.stdout else "",
                    "stderr": "",
                    "returncode": process.returncode
                }
            else:
                return {
                    "success": False,
                    "message": f"Command '{command_str}' execution failed.",
                    "stdout": process.stdout.strip() if capture_output and process.stdout else "",
                    "stderr": process.stderr.strip() if capture_output and process.stderr else "No stderr output.",
                    "returncode": process.returncode
                }
        except FileNotFoundError:
            error_msg = f"Command not found: '{command[0]}'. Please ensure it is installed and in your PATH."
            print(f"ERROR: {error_msg}", file=sys.stderr)
            return {
                "success": False,
                "message": error_msg,
                "stdout": "",
                "stderr": error_msg,
                "returncode": -1
            }
        except subprocess.TimeoutExpired:
            error_msg = f"Command '{command_str}' timed out after {timeout} seconds."
            print(f"ERROR: {error_msg}", file=sys.stderr)
            return {
                "success": False,
                "message": error_msg,
                "stdout": "",
                "stderr": error_msg,
                "returncode": -2
            }
        except Exception as e:
            error_msg = f"An unexpected error occurred while running '{command_str}': {str(e)}"
            print(f"ERROR: {error_msg}", file=sys.stderr)
            return {
                "success": False,
                "message": error_msg,
                "stdout": "",
                "stderr": str(e),
                "returncode": -3
            }

    def get_system_info(self) -> Dict[str, Any]:
        """
        Retrieves basic system information.

        Returns:
            A dictionary with system information, including OS type, version, and hostname.
        """
        try:
            hostname = platform.node()
            return {
                "status": "SUCCESS",
                "message": "System information retrieved successfully.",
                "data": {
                    "os_type": self.os_type,
                    "os_version": self.os_version,
                    "hostname": hostname
                }
            }
        except Exception as e:
            return {
                "status": "FAILURE",
                "message": f"Failed to retrieve system information: {str(e)}",
                "data": {
                    "os_type": None,
                    "os_version": None,
                    "hostname": None
                }
            }

    def check_firewall_status(self) -> Dict[str, Any]:
        """
        Checks the status of the macOS built-in firewall (Application Firewall).

        Returns:
            A dictionary indicating whether the firewall is enabled or disabled.
        """
        command = ["/usr/bin/defaults", "read", "/Library/Preferences/com.apple.alf.plist", "globalstate"]
        result = self._run_command(command)

        if not result["success"]:
            # If the globalstate key is missing or command fails, it implies firewall might be managed differently
            # or is off by default. Check plist existence as a fallback.
            if os.path.exists("/Library/Preferences/com.apple.alf.plist"):
                # If the file exists but globalstate key is not found, it usually means default (disabled).
                return {
                    "status": "SUCCESS",
                    "message": "Firewall status determined.",
                    "data": {
                        "firewall_enabled": False,
                        "details": "Global state key not found, but configuration file exists. Assuming disabled."
                    }
                }
            else:
                return {
                    "status": "WARNING",
                    "message": "Could not definitively determine firewall status.",
                    "data": {
                        "firewall_enabled": None,
                        "details": "Neither globalstate key nor configuration file found. Firewall may be managed externally or is not configured."
                    }
                }

        firewall_state = result.get("stdout", "").strip()
        is_enabled = firewall_state == "1"

        return {
            "status": "SUCCESS",
            "message": "Firewall status retrieved successfully.",
            "data": {
                "firewall_enabled": is_enabled,
                "details": f"Firewall is {'enabled' if is_enabled else 'disabled'}."
            }
        }

    def check_gatekeeper_status(self) -> Dict[str, Any]:
        """
        Checks the status of macOS Gatekeeper.

        Gatekeeper settings control from where apps can be opened.
        This checks the primary Gatekeeper settings and `spctl --status`.

        Returns:
            A dictionary indicating the Gatekeeper security settings.
        """
        gatekeeper_settings = {}
        messages = []

        # Check for apps downloaded from App Store and identified developers
        command_store = ["/usr/bin/defaults", "read", "/System/Library/Security/SecurityServer.plist", "Gatekeeper"]
        result_store = self._run_command(command_store)

        if result_store["success"]:
            try:
                defaults_output = result_store["stdout"].strip()
                # The exact output can vary, this is a common pattern
                if "App Store" in defaults_output and "App Store and identified developers" in defaults_output:
                    gatekeeper_settings["from_app_store"] = True
                    gatekeeper_settings["from_identified_developers"] = True
                    gatekeeper_settings["from_anywhere"] = False
                    messages.append("Gatekeeper set to allow apps from App Store and identified developers.")
                elif "App Store" in defaults_output:
                    gatekeeper_settings["from_app_store"] = True
                    gatekeeper_settings["from_identified_developers"] = False
                    gatekeeper_settings["from_anywhere"] = False
                    messages.append("Gatekeeper set to allow apps only from the App Store.")
                else:
                    gatekeeper_settings["from_app_store"] = False
                    gatekeeper_settings["from_identified_developers"] = False
                    gatekeeper_settings["from_anywhere"] = True # Modern macOS defaults to preventing this
                    messages.append("Gatekeeper may be less restrictive than expected (not enforcing App Store/identified developers).")
            except Exception as e:
                messages.append(f"Error parsing Gatekeeper info: {str(e)}")
                gatekeeper_settings["error_parsing"] = str(e)
        else:
            messages.append(f"Could not retrieve Gatekeeper primary settings: {result_store['stderr']}")
            gatekeeper_settings["from_app_store"] = None
            gatekeeper_settings["from_identified_developers"] = None
            gatekeeper_settings["from_anywhere"] = None

        # Check overall system policy status
        command_anywhere = ["/usr/bin/spctl", "--status"]
        result_anywhere = self._run_command(command_anywhere)

        if result_anywhere["success"]:
            spctl_status = result_anywhere["stdout"].strip()
            gatekeeper_settings["spctl_status"] = spctl_status
            if "evaluated system policy" in spctl_status:
                gatekeeper_settings["overall_security_level"] = "Strict (policy evaluated)"
                messages.append("System policy evaluation is active (strict Gatekeeper).")
            else:
                gatekeeper_settings["overall_security_level"] = "Potentially Less Strict"
                messages.append("Warning: 'spctl --status' does not indicate strict policy evaluation.")
        else:
            gatekeeper_settings["spctl_status"] = "Unknown"
            messages.append(f"Could not retrieve 'spctl --status': {result_anywhere['stderr']}")

        full_message = " ".join(messages)
        if not messages:
            full_message = "Gatekeeper status could not be fully determined."

        return {
            "status": "SUCCESS", # Even if parts failed, we collected some info.
            "message": full_message,
            "data": gatekeeper_settings
        }

    def check_sip_status(self) -> Dict[str, Any]:
        """
        Checks the status of System Integrity Protection (SIP) on macOS.

        SIP protects system files and processes from modification.

        Returns:
            A dictionary indicating whether SIP is enabled or disabled.
        """
        command = ["/usr/bin/csrutil", "status"]
        result = self._run_command(command)

        if not result["success"]:
            if "not found" in result["stderr"].lower():
                return {
                    "status": "WARNING",
                    "message": "csrutil command not found. SIP status cannot be determined.",
                    "data": {
                        "sip_enabled": None,
                        "details": "csrutil executable missing. This is highly unusual for macOS."
                    }
                }
            else:
                return {
                    "status": "FAILURE",
                    "message": f"Failed to check SIP status: {result['stderr']}",
                    "data": {
                        "sip_enabled": None,
                        "details": result["stderr"]
                    }
                }

        output = result.get("stdout", "").strip()
        is_enabled = "System Integrity Protection status: enabled." in output

        return {
            "status": "SUCCESS",
            "message": "SIP status retrieved successfully.",
            "data": {
                "sip_enabled": is_enabled,
                "details": "SIP is enabled." if is_enabled else "SIP is disabled."
            }
        }

    def check_login_items(self) -> Dict[str, Any]:
        """
        Lists applications that launch automatically at login.

        This checks user-specific and system-wide login items using plutil
        for robust parsing.

        Returns:
            A dictionary containing a list of login items.
        """
        login_items: List[Dict[str, Any]] = []
        messages = []

        # Helper function to parse plist files
        def parse_plist(filepath: str, item_type_prefix: str) -> None:
            command_plutil = ["/usr/bin/plutil", "-convert", "json", "-o", "-", filepath]
            result_plutil = self._run_command(command_plutil)

            if result_plutil["success"]:
                try:
                    data = json.loads(result_plutil["stdout"])
                    # Handle different potential structures for login items
                    potential_keys = ["UserAgents", "AutoLaunchAgents", "Services",
                                      "systemHomeDirectoryServices", "Item", "LaunchAgents", "LaunchDaemons"]
                    for key in potential_keys:
                        if key in data and isinstance(data[key], list):
                            for item_data in data[key]:
                                item_name = item_data.get("Comment", item_data.get("Label", os.path.basename(filepath)))
                                item_path = item_data.get("Path", "N/A")
                                is_enabled = item_data.get("Enabled", True) if "Enabled" in item_data else not item_data.get("Disabled", False)
                                run_at_load = item_data.get("RunAtLoad", False)

                                login_items.append({
                                    "type": f"{item_type_prefix}_{key}",
                                    "name": item_name,
                                    "path": item_path,
                                    "enabled": is_enabled,
                                    "run_at_load": run_at_load,
                                    "source_file": filepath
                                })
                except json.JSONDecodeError:
                    messages.append(f"Could not parse JSON from {filepath}.")
                except Exception as e:
                    messages.append(f"Error processing {filepath}: {str(e)}")
            else:
                messages.append(f"Could not convert {filepath} to JSON: {result_plutil['stderr']}")

        # User-specific login items
        user_prefs_path = os.path.expanduser("~/Library/Preferences/com.apple.loginitems.plist")
        if os.path.exists(user_prefs_path):
            parse_plist(user_prefs_path, "User")
        else:
            messages.append("User-specific login items preference file not found.")

        # System-wide login items (LaunchAgents and LaunchDaemons)
        system_dirs = ["/Library/LaunchAgents", "/Library/LaunchDaemons", "/Users/Shared/Library/LaunchAgents"] # Added Users/Shared
        for directory in system_dirs:
            if os.path.isdir(directory):
                for filename in os.listdir(directory):
                    if filename.endswith(".plist"):
                        filepath = os.path.join(directory, filename)
                        parse_plist(filepath, "System")
            # else: messages.append(f"System directory not found: {directory}") # Optional: log missing dirs

        if not login_items:
            messages.append("No login items found.")

        return {
            "status": "SUCCESS",
            "message": " ".join(messages) if messages else "Login items checked.",
            "data": {
                "login_items": login_items
            }
        }

    def check_unauthorized_ports(self) -> Dict[str, Any]:
        """
        Checks for listening network ports that might be considered unauthorized
        or unnecessary for a typical secure system.

        This function checks for common sensitive ports and any open TCP/UDP ports
        that are not part of standard macOS services. It's a heuristic and
        may flag legitimate services on some systems.

        Returns:
            A dictionary containing a list of potentially unauthorized open ports.
        """
        open_ports: List[Dict[str, Any]] = []
        messages = []

        # Use lsof to get listening ports
        command = ["/usr/sbin/lsof", "-i", "-P", "-n"]
        result = self._run_command(command)

        if not result["success"]:
            return {
                "status": "FAILURE",
                "message": f"Failed to perform network port scan: {result['stderr']}",
                "data": {
                    "all_listening_ports": [],
                    "unauthorized_listening_ports": [],
                    "details": result["stderr"]
                }
            }

        output_lines = result.get("stdout", "").strip().splitlines()

        # Known common ports for macOS services (not exhaustive)
        # A more advanced audit would involve a service identification database.
        known_mac_ports = {
            22: {"name": "SSH", "sensitive": True},
            548: {"name": "AFP", "sensitive": True},
            80: {"name": "HTTP", "sensitive": False},
            443: {"name": "HTTPS", "sensitive": False},
            323: {"name": "Apple Remote Desktop", "sensitive": True},
            6000: {"name": "X11", "sensitive": True}, # Often needs to be restricted
            3000: {"name": "Web Server (dev)", "sensitive": False},
            8080: {"name": "HTTP Proxy/Alt", "sensitive": False},
            8443: {"name": "HTTPS Alt", "sensitive": False},
            5353: {"name": "Bonjour/mDNS", "sensitive": False}, # Usually harmless
            5354: {"name": "Bonjour/LLMNR", "sensitive": False},
            5900: {"name": "VNC Server", "sensitive": True}, # If enabled, needs strong auth
        }
        # Ports commonly used by malicious software, but also by legitimate apps
        suspicious_ports = {4444, 54321}

        # Parse lsof output
        for line in output_lines:
            parts = line.split()
            if len(parts) > 8 and (parts[3].startswith("TCP") or parts[3].startswith("UDP")):
                process_name = parts[0]
                pid = parts[1]
                user = parts[2]
                proto = parts[3]
                address_info = parts[4]

                if "->LISTEN" in line:
                    try:
                        if ":" in address_info:
                            port_str = address_info.split(":")[-1]
                            if port_str.isdigit():
                                port = int(port_str)
                                is_known_info = known_mac_ports.get(port)
                                is_known_service = bool(is_known_info)
                                service_name = is_known_info["name"] if is_known_info else "Unknown"
                                is_sensitive = is_known_info["sensitive"] if is_known_info else False
                                is_suspicious = port in suspicious_ports

                                port_data = {
                                    "process": process_name,
                                    "pid": pid,
                                    "user": user,
                                    "protocol": proto,
                                    "address": address_info,
                                    "port": port,
                                    "is_known_service": is_known_service,
                                    "service_name": service_name,
                                    "is_sensitive": is_sensitive,
                                    "is_suspicious": is_suspicious
                                }
                                open_ports.append(port_data)

                                # Define criteria for "unauthorized" for reporting
                                # - Not a known service
                                # - A known sensitive service (like SSH, VNC)
                                # - A port flagged as suspicious
                                if not is_known_service or is_sensitive or is_suspicious:
                                    if port_data not in open_ports: # Avoid duplicates if logic expands
                                        open_ports.append(port_data)
                    except ValueError:
                        messages.append(f"Warning: Could not parse port from line: {line}")
                    except Exception as e:
                        messages.append(f"Warning: Error processing line '{line}': {str(e)}")

        # Filter to only include potentially unauthorized ports for the report summary
        unauthorized_ports = [
            port_info for port_info in open_ports
            if not port_info["is_known_service"] or port_info["is_sensitive"] or port_info["is_suspicious"]
        ]

        if not unauthorized_ports:
            messages.append("No potentially unauthorized or sensitive listening ports found.")
        else:
            messages.append(f"Found {len(unauthorized_ports)} potentially unauthorized or sensitive listening port(s).")

        return {
            "status": "SUCCESS",
            "message": " ".join(messages),
            "data": {
                "all_listening_ports": open_ports,
                "unauthorized_listening_ports": unauthorized_ports
            }
        }

    def check_disk_encryption_status(self) -> Dict[str, Any]:
        """
        Checks the status of FileVault disk encryption.

        Returns:
            A dictionary indicating whether FileVault is enabled or disabled.
        """
        command = ["/usr/sbin/fdesetup", "status"]
        result = self._run_command(command)

        if not result["success"]:
            # fdesetup status might fail if not run as root or other system issues
            return {
                "status": "FAILURE",
                "message": f"Failed to check disk encryption status: {result['stderr']}",
                "data": {
                    "filevault_enabled": None,
                    "details": result["stderr"]
                }
            }

        output = result.get("stdout", "").strip()
        is_enabled = "FileVault is On." in output

        return {
            "status": "SUCCESS",
            "message": "Disk encryption status retrieved successfully.",
            "data": {
                "filevault_enabled": is_enabled,
                "details": "FileVault is enabled." if is_enabled else "FileVault is disabled."
            }
        }

    def check_network_interfaces(self) -> Dict[str, Any]:
        """
        Retrieves information about network interfaces.

        Returns:
            A dictionary with a list of active network interfaces and their IP addresses.
        """
        interfaces_info: List[Dict[str, Any]] = []
        messages = []

        try:
            # Use networksetup to list hardware ports and their devices
            command_list_ports = ["/usr/sbin/networksetup", "-listallhardwareports"]
            result_list = self._run_command(command_list_ports)

            if not result_list["success"]:
                messages.append(f"Failed to list network hardware ports: {result_list['stderr']}")
                return {
                    "status": "FAILURE",
                    "message": " ".join(messages),
                    "data": {
                        "interfaces": [],
                        "details": result_list["stderr"]
                    }
                }

            hardware_ports_output = result_list.get("stdout", "").strip()
            current_hardware_port = None
            devices_to_check = []

            for line in hardware_ports_output.splitlines():
                if line.startswith("Hardware Port:"):
                    current_hardware_port = line.split(":", 1)[1].strip()
                elif line.startswith("Device:"):
                    device_name = line.split(":", 1)[1].strip()
                    if device_name:
                        devices_to_check.append({"hardware_port": current_hardware_port, "device": device_name})
                        current_hardware_port = None # Reset

            # Get IP addresses for each device using ifconfig
            for interface_data in devices_to_check:
                device_name = interface_data["device"]
                command_ifconfig = ["/usr/sbin/ifconfig", device_name]
                result_ifconfig = self._run_command(command_ifconfig)

                interface_entry = {
                    "hardware_port": interface_data["hardware_port"],
                    "device": device_name,
                    "ip_addresses": [],
                    "mac_address": None,
                    "ipv6_addresses": []
                }

                if result_ifconfig["success"]:
                    ifconfig_output = result_ifconfig["stdout"].strip()
                    for if_line in ifconfig_output.splitlines():
                        ifconfig_line_stripped = if_line.strip()
                        if "ether " in ifconfig_line_stripped:
                            interface_entry["mac_address"] = ifconfig_line_stripped.split("ether ")[1]
                        elif "inet " in ifconfig_line_stripped and not "inet6" in ifconfig_line_stripped:
                            ip_address = ifconfig_line_stripped.split("inet ")[1].split(" ")[0]
                            if ip_address != "127.0.0.1": # Exclude loopback for external view
                                interface_entry["ip_addresses"].append(ip_address)
                        elif "inet6 " in ifconfig_line_stripped:
                            ipv6_address = ifconfig_line_stripped.split("inet6 ")[1].split(" ")[0]
                            if ipv6_address != "::1": # Exclude loopback
                                interface_entry["ipv6_addresses"].append(ipv6_address)
                    interfaces_info.append(interface_entry)
                else:
                    messages.append(f"Warning: Could not get details for {device_name}: {result_ifconfig['stderr']}")

        except Exception as e:
            messages.append(f"An error occurred while checking network interfaces: {str(e)}")
            return {
                "status": "FAILURE",
                "message": " ".join(messages),
                "data": {
                    "interfaces": [],
                    "details": str(e)
                }
            }

        return {
            "status": "SUCCESS",
            "message": " ".join(messages) if messages else "Network interface information retrieved.",
            "data": {
                "interfaces": interfaces_info
            }
        }

    def check_running_processes(self, exclude_system_processes: bool = True) -> Dict[str, Any]:
        """
        Lists currently running processes. Can optionally exclude common system processes.

        Args:
            exclude_system_processes: If True, attempts to filter out standard macOS processes.

        Returns:
            A dictionary containing a list of running processes.
        """
        messages = []
        processes: List[Dict[str, Any]] = []

        command = ["/bin/ps", "aux"] # 'aux' provides process list with user, cpu, mem, and command
        result = self._run_command(command, timeout=30)

        if not result["success"]:
            return {
                "status": "FAILURE",
                "message": f"Failed to list running processes: {result['stderr']}",
                "data": {"processes": [], "details": result["stderr"]}
            }

        lines = result["stdout"].splitlines()
        if not lines:
            return {
                "status": "WARNING",
                "message": "No running processes found.",
                "data": {"processes": []}
            }

        # Skip the header line
        header = lines[0]
        process_lines = lines[1:]

        # Simple system process exclusion list (can be expanded)
        # This is a heuristic and might miss some or exclude necessary ones if too aggressive.
        system_process_names = {
            "launchd", "kernel_task", "loginwindow", "WindowServer", "sysmond",
            "distnoted", "UserEventAgent", "powerd", "dasd", "ReportCrash",
            "mDNSResponder", "installd", "opendirectoryd", "coreaudiod",
            "coreservicesd", "launchservicesd", "systemuiserver", "cfprefsd",
            "configd", "TrustEvaluationAgent", "trustd", "securityd",
            "apfs_control", "fseventsd", "logd", "taskgated", "diskarbitrationd"
        }

        for line in process_lines:
            try:
                parts = line.split(None, 10) # Split into at most 11 parts
                if len(parts) < 11: continue # Malformed line

                user = parts[0]
                pid = int(parts[1])
                cpu_usage = float(parts[2])
                mem_usage = float(parts[3])
                command = parts[10]

                # Basic check for process name
                process_name = command.split('/')[-1]

                if exclude_system_processes and process_name in system_process_names:
                    continue

                processes.append({
                    "user": user,
                    "pid": pid,
                    "cpu_usage": cpu_usage,
                    "mem_usage": mem_usage,
                    "command": command,
                    "name": process_name
                })
            except (ValueError, IndexError) as e:
                messages.append(f"Warning: Could not parse process line: '{line}' - {str(e)}")

        if exclude_system_processes and not processes:
            messages.append("No non-system processes found (all were filtered out).")
        elif not processes:
            messages.append("No running processes found.")
        else:
            messages.append(f"Found {len(processes)} running process(es).")


        return {
            "status": "SUCCESS",
            "message": " ".join(messages),
            "data": {
                "processes": processes,
                "all_processes_count": len(lines) -1 if lines else 0,
                "filtered_count": (len(lines) -1) - len(processes) if lines else 0
            }
        }


    def generate_report(self, audit_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates a comprehensive security audit report from collected results.

        This method structures the raw audit data into a human-readable and
        structured report format. It can also highlight critical findings.

        Args:
            audit_results: A dictionary containing the results of individual audit checks.

        Returns:
            A structured report dictionary.
        """
        report: Dict[str, Any] = {
            "report_title": "macOS Security Audit Report",
            "system_information": None,
            "security_posture": {
                "overall_score": "N/A", # Placeholder for future scoring
                "critical_findings": [],
                "recommendations": []
            },
            "audit_details": {},
            "tool_information": {
                "tool_name": "SecurityAuditTool",
                "version": "1.0.0",
                "platform": platform.platform(),
                "python_version": sys.version,
                "missing_capabilities": [self.missing_capability],
                "required_external_functionality": self.required_functions
            }
        }

        # Populate system information
        system_info = audit_results.get("system_info")
        if system_info and system_info["status"] == "SUCCESS":
            report["system_information"] = system_info["data"]
            report["report_title"] += f" - {system_info['data'].get('hostname', 'UnknownHost')}"
        else:
            report["system_information"] = {"error": "Failed to retrieve system info."}

        # Process each audit check and add to report, identifying potential risks
        for key, result in audit_results.items():
            report["audit_details"][key] = result
            data = result.get("data", {})
            status = result.get("status", "UNKNOWN")
            message = result.get("message", "No details.")

            # Identify critical findings and recommendations
            finding = {"category": key, "details": message, "status": status}

            if status == "FAILURE":
                report["security_posture"]["critical_findings"].append(finding)
                report["security_posture"]["recommendations"].append({
                    "category": key,
                    "recommendation": f"Address the reported failure in '{key}'. Review details for specific actions.",
                    "severity": "HIGH"
                })
            elif status == "WARNING":
                report["security_posture"]["critical_findings"].append(finding)
                report["security_posture"]["recommendations"].append({
                    "category": key,
                    "recommendation": f"Review the warning for '{key}'. Consider implementing best practices.",
                    "severity": "MEDIUM"
                })

            # Specific checks for recommendations
            if key == "firewall_status" and data.get("firewall_enabled") is False:
                report["security_posture"]["recommendations"].append({
                    "category": key,
                    "recommendation": "Enable the macOS firewall (Application Firewall) to block unsolicited incoming network connections.",
                    "severity": "HIGH"
                })
            if key == "gatekeeper_status" and (data.get("from_app_store") is False or data.get("from_identified_developers") is False):
                 report["security_posture"]["recommendations"].append({
                    "category": key,
                    "recommendation": "Ensure Gatekeeper is configured to allow apps from the App Store and identified developers to protect against malware.",
                    "severity": "HIGH"
                })
            if key == "sip_status" and data.get("sip_enabled") is False:
                report["security_posture"]["recommendations"].append({
                    "category": key,
                    "recommendation": "System Integrity Protection (SIP) is disabled. Enable it for enhanced system security against malware and unauthorized modifications.",
                    "severity": "CRITICAL"
                })
            if key == "disk_encryption" and data.get("filevault_enabled") is False:
                report["security_posture"]["recommendations"].append({
                    "category": key,
                    "recommendation": "FileVault disk encryption is disabled. Enable it to encrypt your entire startup disk and protect data at rest.",
                    "severity": "HIGH"
                })
            if key == "unauthorized_ports" and data.get("unauthorized_listening_ports"):
                unauthorized_list = [f"Port {p['port']} ({p['process']})" for p in data["unauthorized_listening_ports"]]
                report["security_posture"]["recommendations"].append({
                    "category": key,
                    "recommendation": f"Investigate unauthorized/sensitive listening ports: {', '.join(unauthorized_list)}. Ensure they are necessary and properly secured.",
                    "severity": "HIGH"
                })
            if key == "login_items" and data.get("login_items"):
                suspicious_login_items = [
                    item for item in data["login_items"]
                    if "System" in item.get("type", "") and item.get("enabled", True)
                ]
                if suspicious_login_items:
                    report["security_posture"]["recommendations"].append({
                        "category": key,
                        "recommendation": f"Review system-level login items for unexpected entries: {', '.join([item.get('name', item.get('path')) for item in suspicious_login_items[:5]])}...", # Limit to first 5
                        "severity": "MEDIUM"
                    })

        # Finalize overall status
        if not report["security_posture"]["critical_findings"]:
            report["security_posture"]["overall_score"] = "Excellent"
            report["security_posture"]["recommendations"].append({
                "category": "General",
                "recommendation": "System security posture is good. Continue to regularly update macOS and applications.",
                "severity": "INFO"
            })
        elif len(report["security_posture"]["critical_findings"]) <= 2:
            report["security_posture"]["overall_score"] = "Good"
        else:
            report["security_posture"]["overall_score"] = "Needs Improvement"

        return report


    def run_full_audit(self) -> Dict[str, Any]:
        """
        Runs all available security audit checks.

        Returns:
            A dictionary containing the aggregated results of all audit checks,
            and a structured report.
        """
        audit_results: Dict[str, Any] = {}

        print("Starting comprehensive security audit...", file=sys.stderr)

        # 1. System Information
        print("  - Checking System Information...", file=sys.stderr)
        audit_results["system_info"] = self.get_system_info()

        # 2. Firewall Status
        print("  - Checking Firewall Status...", file=sys.stderr)
        audit_results["firewall_status"] = self.check_firewall_status()

        # 3. Gatekeeper Status
        print("  - Checking Gatekeeper Status...", file=sys.stderr)
        audit_results["gatekeeper_status"] = self.check_gatekeeper_status()

        # 4. SIP Status
        print("  - Checking SIP Status...", file=sys.stderr)
        audit_results["sip_status"] = self.check_sip_status()

        # 5. Login Items
        print("  - Checking Login Items...", file=sys.stderr)
        audit_results["login_items"] = self.check_login_items()

        # 6. Disk Encryption Status
        print("  - Checking Disk Encryption Status...", file=sys.stderr)
        audit_results["disk_encryption"] = self.check_disk_encryption_status()

        # 7. Network Interfaces
        print("  - Checking Network Interfaces...", file=sys.stderr)
        audit_results["network_interfaces"] = self.check_network_interfaces()

        # 8. Unauthorized Ports (can be resource intensive)
        print("  - Checking for Unauthorized Ports...", file=sys.stderr)
        audit_results["unauthorized_ports"] = self.check_unauthorized_ports()

        # 9. Running Processes (can be resource intensive)
        print("  - Checking Running Processes...", file=sys.stderr)
        audit_results["running_processes"] = self.check_running_processes(exclude_system_processes=True)

        print("Audit checks completed. Generating report...", file=sys.stderr)

        # Generate the comprehensive report
        full_report = self.generate_report(audit_results)

        return full_report


if __name__ == '__main__':
    # Example Usage
    print("Initializing Security Audit Tool...", file=sys.stderr)
    try:
        tool = SecurityAuditTool()
        print(f"Running on macOS version: {tool.os_version}", file=sys.stderr)

        print("\n--- Performing Comprehensive Security Audit ---", file=sys.stderr)
        full_report = tool.run_full_audit()

        # Output the report as JSON
        print(json.dumps(full_report, indent=4, sort_keys=True))

    except EnvironmentError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)
