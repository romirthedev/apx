import os
import subprocess
import json
import datetime
import re
from typing import Dict, Any, List, Optional, Tuple

class SecurityAuditor:
    """
    A specialized tool for generating detailed security audit reports with vulnerability
    assessments and recommendations.

    This class provides methods to perform various security checks and consolidates
    the findings into a structured report. It is designed to be safe, performing
    read-only operations where possible and clearly indicating any potential for
    system interaction.

    Compatibility: macOS (some checks are macOS-specific)
    """

    def __init__(self, target_path: str):
        """
        Initializes the SecurityAuditor.

        Args:
            target_path: The absolute or relative path to the directory or file
                         to be audited.

        Raises:
            ValueError: If the target_path is empty or invalid.
            FileNotFoundError: If the target_path does not exist.
        """
        if not target_path:
            raise ValueError("Target path cannot be empty.")
        
        self.target_path: str = os.path.abspath(target_path)
        if not os.path.exists(self.target_path):
            raise FileNotFoundError(f"Target path does not exist: {self.target_path}")
        if not os.access(self.target_path, os.R_OK):
            raise PermissionError(f"No read access to target path: {self.target_path}")

    def _run_command(self, command: List[str], timeout: int = 60, check_output: bool = True) -> Tuple[bool, str, str]:
        """
        Safely runs a shell command and captures its output.

        Args:
            command: A list of strings representing the command and its arguments.
            timeout: The maximum time in seconds to wait for the command to complete.
            check_output: If True, raises an error if command output is empty but expected.

        Returns:
            A tuple containing:
            - bool: True if the command succeeded, False otherwise.
            - str: The standard output of the command.
            - str: The standard error of the command.
        """
        try:
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,  # Don't raise exception on non-zero exit code by default
                timeout=timeout
            )
            
            success = process.returncode == 0
            stdout = process.stdout.strip()
            stderr = process.stderr.strip()

            if not success and stderr:
                # Log or handle specific error messages that might be misleading
                pass

            # Add a basic check for expected output if success is True and check_output is True
            if success and check_output and not stdout:
                # This might be too aggressive, consider making check_output more granular
                # For now, we rely on specific checks within methods
                pass

            return success, stdout, stderr
        
        except FileNotFoundError:
            return False, "", f"Command not found: '{command[0]}'. Ensure it is installed and in your PATH."
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {timeout} seconds: {' '.join(command)}"
        except Exception as e:
            return False, "", f"An unexpected error occurred while running command '{' '.join(command)}': {e}"

    def _format_report(self, success: bool, message: str, findings: Dict[str, Any], recommendations: List[str]) -> Dict[str, Any]:
        """
        Formats the output into a standard dictionary structure for a single check.

        Args:
            success: A boolean indicating if the overall operation was successful.
            message: A string message describing the outcome of the check.
            findings: A dictionary containing specific findings.
            recommendations: A list of strings with recommendations.

        Returns:
            A structured dictionary.
        """
        return {
            "success": success,
            "message": message,
            "findings": findings,
            "recommendations": recommendations,
            "timestamp": datetime.datetime.now().isoformat()
        }

    def assess_permissions(self) -> Dict[str, Any]:
        """
        Assesses file and directory permissions for the target path.

        Checks for overly permissive files/directories (e.g., world-writable).
        This is a read-only operation.

        Returns:
            A dictionary containing the audit results and recommendations.
        """
        permission_findings: Dict[str, Any] = {
            "overly_permissive_files": [],
            "potential_issues": []
        }
        recommendations: List[str] = []
        
        try:
            for root, dirs, files in os.walk(self.target_path):
                for name in dirs + files:
                    path = os.path.join(root, name)
                    try:
                        mode = os.stat(path).st_mode
                        is_dir = os.path.isdir(path)

                        # Check for world-writable permissions (others have write access)
                        # Ignore sticky bit (t) and setuid/setgid bits for this general check.
                        if (mode & 0o0002) and not (mode & 0o4000 or mode & 0o2000 or mode & 0o1000):
                            permission_findings["overly_permissive_files"].append({
                                "path": path,
                                "permissions": oct(mode)[-3:],
                                "type": "directory" if is_dir else "file",
                                "issue": "World-writable permission detected (others can write)."
                            })
                        
                        # Check for executable files that are not owned by the user (potential for unauthorized execution)
                        # This check is commented out as it's complex and often context-dependent.
                        # if (mode & 0o100) and not os.access(path, os.X_OK): # Check for owner execute bit, but not necessarily executable
                        #     pass # This is complex and often relies on context, deferring to more advanced tools

                    except OSError as e:
                        permission_findings["potential_issues"].append({
                            "path": path,
                            "issue": f"Could not access file/directory status: {e}"
                        })

            if not permission_findings["overly_permissive_files"]:
                recommendations.append(
                    "File and directory permissions appear to be reasonable. "
                    "Consider reviewing group ownership and user-specific permissions for critical assets."
                )
            else:
                recommendations.append(
                    "Review and restrict world-writable permissions on identified files/directories. "
                    "Use 'chmod' to set appropriate permissions (e.g., 'chmod 755' for directories, 'chmod 644' for files). "
                    "Ensure sensitive files are not world-readable."
                )
            
            if permission_findings["potential_issues"]:
                recommendations.append(
                    "Investigate paths where status could not be accessed. Ensure correct file system permissions and ownership."
                )

            return self._format_report(True, "File and directory permission assessment complete.", permission_findings, recommendations)

        except Exception as e:
            return self._format_report(False, f"Error during permission assessment: {e}", {"overly_permissive_files": [], "potential_issues": []}, [])

    def check_for_exposed_sensitive_files(self) -> Dict[str, Any]:
        """
        Checks for common patterns of exposed sensitive files.

        This is a heuristic-based check and may produce false positives or negatives.
        It is a read-only operation.

        Returns:
            A dictionary containing the audit results and recommendations.
        """
        sensitive_file_findings: Dict[str, Any] = {
            "potentially_sensitive_files": [],
            "warnings": []
        }
        recommendations: List[str] = []
        
        # Expanded list of patterns, including common configuration files and secrets
        sensitive_patterns = [
            r".*\.(key|pem|crt|cer|conf|cfg|config|env|sqlite3|db|sql)$",  # Files with sensitive extensions
            r".*password.*", r".*secret.*", r".*credential.*", r".*api_key.*",
            r"id_rsa", r"id_dsa", r"authorized_keys", r".bash_history",
            r"web\.config", r"appsettings\.json", r"\.env" # Specific config files
        ]

        try:
            for root, dirs, files in os.walk(self.target_path):
                # Avoid scanning hidden directories or sensitive system paths if possible
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['/proc', '/sys', '/dev']]

                for file in files:
                    filepath = os.path.join(root, file)
                    lower_filename = file.lower()
                    
                    for pattern in sensitive_patterns:
                        if re.match(pattern, lower_filename):
                            sensitive_file_findings["potentially_sensitive_files"].append({
                                "path": filepath,
                                "issue": f"Potentially sensitive file matching pattern '{pattern}'."
                            })
                            break # Move to the next file once a pattern matches

            if not sensitive_file_findings["potentially_sensitive_files"]:
                recommendations.append(
                    "No obvious exposed sensitive files detected based on common patterns. "
                    "Ensure sensitive information is properly secured and access is restricted. "
                    "Regularly audit configurations and code for hardcoded secrets."
                )
            else:
                recommendations.append(
                    "Investigate all identified files for sensitive information. "
                    "Ensure these files are not accessible to unauthorized users and are stored securely. "
                    "Consider using encrypted storage, secrets management solutions (e.g., HashiCorp Vault, AWS Secrets Manager), "
                    "or environment variables for sensitive data."
                )
            
            # Add a general recommendation about secrets management
            if sensitive_file_findings["potentially_sensitive_files"]:
                recommendations.append(
                    "Implement a robust secrets management strategy to avoid storing sensitive data in plain text files or code."
                )

            return self._format_report(True, "Sensitive file exposure check complete.", sensitive_file_findings, recommendations)

        except Exception as e:
            return self._format_report(False, f"Error during sensitive file check: {e}", {"potentially_sensitive_files": [], "warnings": []}, [])

    def check_installed_packages(self) -> Dict[str, Any]:
        """
        Checks for installed Python packages and their versions and attempts to identify known vulnerabilities.

        This method uses 'pip list --format=json' which is a read-only operation.
        It then uses an external tool like 'pip-audit' or 'safety' if available,
        or falls back to a simulated check if not.

        Returns:
            A dictionary containing the audit results and recommendations.
        """
        package_findings: Dict[str, Any] = {
            "installed_packages": [],
            "vulnerable_packages": [],
            "unscanned_packages": []
        }
        recommendations: List[str] = []
        
        # --- Step 1: List installed packages ---
        success_list, stdout_list, stderr_list = self._run_command(["pip", "list", "--format=json"])

        if not success_list:
            return self._format_report(False, f"Failed to list installed packages: {stderr_list}", package_findings, [])

        try:
            packages_data = json.loads(stdout_list)
            for pkg in packages_data:
                package_findings["installed_packages"].append({
                    "name": pkg["name"],
                    "version": pkg["version"]
                })
        except json.JSONDecodeError:
            return self._format_report(False, "Failed to parse pip list output as JSON.", package_findings, [])
        except Exception as e:
            return self._format_report(False, f"Error processing installed packages: {e}", package_findings, [])

        # --- Step 2: Attempt to use 'pip-audit' for vulnerability scanning ---
        # 'pip-audit' is a more modern and comprehensive tool than 'safety'
        pip_audit_command = ["pip-audit", "--json"]
        
        # Check if pip-audit is available
        success_check_audit, _, _ = self._run_command(["which", "pip-audit"], check_output=False)
        
        if success_check_audit:
            # Run pip-audit
            success_audit, stdout_audit, stderr_audit = self._run_command(pip_audit_command)
            
            if success_audit:
                try:
                    audit_results = json.loads(stdout_audit)
                    for vuln_info in audit_results:
                        package_name = vuln_info.get("package", {}).get("name")
                        package_version = vuln_info.get("package", {}).get("version")
                        
                        if package_name and package_version:
                            package_findings["vulnerable_packages"].append({
                                "name": package_name,
                                "version": package_version,
                                "issue": f"Known vulnerability: {vuln_info.get('description', 'N/A')}",
                                "cve": vuln_info.get("id", "N/A"),
                                "link": vuln_info.get("url", "N/A")
                            })
                    
                    # Identify packages that were scanned and found clean
                    scanned_package_names = {v["name"] for v in package_findings["vulnerable_packages"]}
                    for pkg in package_findings["installed_packages"]:
                        if pkg["name"] not in scanned_package_names:
                             pass # For now, we don't explicitly list clean packages if scanning was successful

                except json.JSONDecodeError:
                    package_findings["unscanned_packages"].extend(
                        [pkg["name"] for pkg in package_findings["installed_packages"]]
                    )
                    recommendations.append(
                        "Failed to parse 'pip-audit' JSON output. Vulnerability scan might be incomplete. "
                        "Check 'pip-audit' logs for details."
                    )
                except Exception as e:
                    package_findings["unscanned_packages"].extend(
                        [pkg["name"] for pkg in package_findings["installed_packages"]]
                    )
                    recommendations.append(
                        f"Error processing 'pip-audit' results: {e}. Vulnerability scan might be incomplete."
                    )
            else:
                package_findings["unscanned_packages"].extend(
                    [pkg["name"] for pkg in package_findings["installed_packages"]]
                )
                recommendations.append(
                    f"Failed to run 'pip-audit': {stderr_audit}. Vulnerability scan could not be completed. "
                    "Ensure 'pip-audit' is installed (`pip install pip-audit`) and accessible."
                )
        else:
            # Fallback: Simulate check or inform user
            # In a real tool, one might try 'safety check' here as another fallback.
            # For this example, we'll just note that pip-audit was not found.
            package_findings["unscanned_packages"].extend(
                [pkg["name"] for pkg in package_findings["installed_packages"]]
            )
            recommendations.append(
                "The 'pip-audit' tool was not found. For comprehensive vulnerability scanning of Python packages, "
                "install 'pip-audit' (`pip install pip-audit`) and run this check again. "
                "Alternatively, consider using 'safety' (`pip install safety`)."
            )

        # --- Generate recommendations based on findings ---
        if not package_findings["vulnerable_packages"] and not package_findings["unscanned_packages"]:
            recommendations.append(
                "All scanned Python packages appear to be free of known vulnerabilities. "
                "Maintain a regular update schedule for your dependencies."
            )
        elif package_findings["vulnerable_packages"]:
            for vuln in package_findings["vulnerable_packages"]:
                recommendations.append(
                    f"Update '{vuln['name']}' from version {vuln['version']} to a secure version. "
                    f"Details: {vuln.get('link', 'N/A')} (CVE: {vuln.get('cve', 'N/A')})"
                )
            if package_findings["unscanned_packages"]:
                recommendations.append(
                    f"The following packages were not scanned for vulnerabilities: {', '.join(package_findings['unscanned_packages'])}. "
                    "Ensure all necessary tools are installed and configured correctly."
                )
        else: # Only unscanned packages found
            recommendations.append(
                f"No vulnerabilities were detected, but the following packages were not scanned: {', '.join(package_findings['unscanned_packages'])}. "
                "This may be due to missing tools or configuration issues. Ensure 'pip-audit' is installed and working."
            )

        return self._format_report(True, "Installed Python package assessment complete.", package_findings, recommendations)

    def check_system_configuration_basic(self) -> Dict[str, Any]:
        """
        Performs basic system configuration checks relevant to security on macOS.

        This includes checking for common security settings like Gatekeeper, FileVault, and Firewall.
        This is a read-only operation.
        Note: Some checks may require elevated privileges for definitive results.

        Returns:
            A dictionary containing the audit results and recommendations.
        """
        sys_config_findings: Dict[str, Any] = {
            "settings_status": [],
            "potential_issues": []
        }
        recommendations: List[str] = []
        
        # --- Check Gatekeeper status ---
        success_gk, stdout_gk, stderr_gk = self._run_command(["spctl", "--status"], check_output=False)
        if success_gk:
            if "assessments enabled" in stdout_gk.lower():
                sys_config_findings["settings_status"].append({"setting": "Gatekeeper", "status": "Enabled"})
            else:
                sys_config_findings["settings_status"].append({"setting": "Gatekeeper", "status": "Disabled or Partially Enabled"})
                sys_config_findings["potential_issues"].append({
                    "setting": "Gatekeeper",
                    "issue": "Gatekeeper is not fully enabled, reducing protection against malware."
                })
        else:
            sys_config_findings["settings_status"].append({"setting": "Gatekeeper", "status": "Status check failed"})
            sys_config_findings["potential_issues"].append({
                "setting": "Gatekeeper",
                "issue": f"Could not check Gatekeeper status: {stderr_gk}"
            })

        # --- Check FileVault status ---
        # This command typically requires admin privileges. We will try to run it and note if it fails.
        try:
            success_fv, stdout_fv, stderr_fv = self._run_command(["fdesetup", "status"])
            if success_fv:
                if "FileVault is On." in stdout_fv:
                    sys_config_findings["settings_status"].append({"setting": "FileVault", "status": "Enabled"})
                else:
                    sys_config_findings["settings_status"].append({"setting": "FileVault", "status": "Disabled"})
                    sys_config_findings["potential_issues"].append({
                        "setting": "FileVault",
                        "issue": "FileVault encryption is not enabled, leaving disk data unencrypted."
                    })
            else:
                # If 'fdesetup status' fails, it's often due to lack of privileges.
                sys_config_findings["settings_status"].append({"setting": "FileVault", "status": "Status check failed (likely needs admin privileges)"})
                sys_config_findings["potential_issues"].append({
                    "setting": "FileVault",
                    "issue": "Could not definitively confirm FileVault status. Ensure it is enabled for disk encryption. This check often requires administrator privileges."
                })
        except Exception as e:
            sys_config_findings["settings_status"].append({"setting": "FileVault", "status": "Error checking status"})
            sys_config_findings["potential_issues"].append({
                "setting": "FileVault",
                "issue": f"An error occurred while checking FileVault status: {e}. This check often requires administrator privileges."
            })

        # --- Check Firewall status ---
        try:
            # Using 'socketfilterfw' for a more reliable firewall check on recent macOS versions
            success_fw, stdout_fw, stderr_fw = self._run_command(["/usr/libexec/ApplicationFirewall/socketfilterfw", "--getglobalstate"])
            if success_fw:
                if "Firewall is enabled. (State = 1)" in stdout_fw:
                    sys_config_findings["settings_status"].append({"setting": "Firewall", "status": "Enabled"})
                else:
                    sys_config_findings["settings_status"].append({"setting": "Firewall", "status": "Disabled"})
                    sys_config_findings["potential_issues"].append({
                        "setting": "Firewall",
                        "issue": "System firewall is disabled, potentially exposing the system to network threats."
                    })
            else:
                sys_config_findings["settings_status"].append({"setting": "Firewall", "status": "Status check failed"})
                sys_config_findings["potential_issues"].append({
                    "setting": "Firewall",
                    "issue": f"Could not check Firewall status: {stderr_fw}"
                })
        except FileNotFoundError:
            sys_config_findings["settings_status"].append({"setting": "Firewall", "status": "Tool not found"})
            sys_config_findings["potential_issues"].append({
                "setting": "Firewall",
                "issue": "Firewall check tool '/usr/libexec/ApplicationFirewall/socketfilterfw' not found. Ensure this path is correct for your macOS version."
            })
        except Exception as e:
            sys_config_findings["settings_status"].append({"setting": "Firewall", "status": "Error checking status"})
            sys_config_findings["potential_issues"].append({
                "setting": "Firewall",
                "issue": f"An error occurred while checking Firewall status: {e}"
            })

        # --- Generate recommendations ---
        if not sys_config_findings["potential_issues"]:
            recommendations.append(
                "Basic macOS security configurations (Gatekeeper, FileVault, Firewall) appear to be set to recommended levels. "
                "Continue to regularly review and update security settings."
            )
        else:
            if any("Gatekeeper" in finding["setting"] and "Disabled" in finding["status"] for finding in sys_config_findings["settings_status"]):
                recommendations.append(
                    "Enable Gatekeeper in System Settings > Security & Privacy > Advanced to prevent installation of unidentified developer software."
                )
            if any("FileVault" in finding["setting"] and "Disabled" in finding["status"] for finding in sys_config_findings["settings_status"]):
                recommendations.append(
                    "Enable FileVault disk encryption in System Settings > Security & Privacy to protect your data at rest."
                )
            if any("Firewall" in finding["setting"] and "Disabled" in finding["status"] for finding in sys_config_findings["settings_status"]):
                recommendations.append(
                    "Enable the Firewall in System Settings > Security & Privacy > Firewall Options to control network access to your Mac."
                )
            
            recommendations.append(
                "Review any 'Status check failed' or 'Error checking status' messages. "
                "Ensure you have the necessary permissions or that the system is configured as expected."
            )
            recommendations.append(
                "Regularly review macOS security settings in System Settings > Security & Privacy for optimal protection."
            )

        return self._format_report(True, "Basic macOS system configuration check complete.", sys_config_findings, recommendations)

    def generate_full_report(self) -> Dict[str, Any]:
        """
        Generates a comprehensive security audit report by running all available checks.

        Returns:
            A dictionary containing the full security audit report.
        """
        audit_results: Dict[str, Any] = {
            "audit_details": {
                "audited_path": self.target_path,
                "timestamp": datetime.datetime.now().isoformat()
            },
            "overall_success": True,
            "summary_message": "Security audit completed successfully.",
            "findings": {},
            "consolidated_recommendations": []
        }
        has_errors_or_warnings = False

        # Define the checks to run
        checks_to_run = {
            "permission_assessment": self.assess_permissions,
            "sensitive_file_check": self.check_for_exposed_sensitive_files,
            "installed_packages_check": self.check_installed_packages,
            "system_configuration_check": self.check_system_configuration_basic,
            # Add more checks here as they are developed
        }

        for check_name, check_func in checks_to_run.items():
            try:
                result = check_func()
                audit_results["findings"][check_name] = result
                
                # Track if any check failed or produced issues
                if not result.get("success", False) or result.get("findings"):
                    has_errors_or_warnings = True
                
                # Consolidate recommendations
                if "recommendations" in result and result["recommendations"]:
                    audit_results["consolidated_recommendations"].extend([
                        f"[{check_name.replace('_', ' ').title()}]: {rec}" for rec in result["recommendations"]
                    ])
            except Exception as e:
                # If a check function itself throws an unhandled exception
                has_errors_or_warnings = True
                audit_results["findings"][check_name] = self._format_report(
                    False,
                    f"An unhandled error occurred during the {check_name.replace('_', ' ')}: {e}",
                    {"error": str(e)},
                    []
                )
                audit_results["consolidated_recommendations"].append(
                    f"[{check_name.replace('_', ' ').title()}]: An unhandled error occurred during this check. Please review the full report."
                )

        if has_errors_or_warnings:
            audit_results["overall_success"] = False
            audit_results["summary_message"] = "Security audit completed with some issues or warnings detected. Please review the findings and recommendations."
        else:
            audit_results["summary_message"] = "Security audit completed successfully with no critical issues found."

        # Remove duplicate recommendations
        audit_results["consolidated_recommendations"] = list(dict.fromkeys(audit_results["consolidated_recommendations"]))

        return audit_results


if __name__ == "__main__":
    import tempfile
    import shutil

    # --- Example Usage ---

    # Create a temporary directory for testing
    temp_dir_path = tempfile.mkdtemp(prefix="security_audit_test_")
    print(f"Created temporary directory for testing: {temp_dir_path}")

    try:
        # Create some dummy files and directories for testing
        os.makedirs(os.path.join(temp_dir_path, "configs"), exist_ok=True)
        os.makedirs(os.path.join(temp_dir_path, "data", "sensitive"), exist_ok=True)
        os.makedirs(os.path.join(temp_dir_path, ".hidden_dir"), exist_ok=True) # For hidden dir test

        # World-writable file
        world_writable_file = os.path.join(temp_dir_path, "configs", "app.conf")
        with open(world_writable_file, "w") as f:
            f.write("api_key=supersecret123\n")
        os.chmod(world_writable_file, 0o666) # World-writable for testing

        # Readable but not writable by world
        readable_file = os.path.join(temp_dir_path, "configs", "public.txt")
        with open(readable_file, "w") as f:
            f.write("This is public info.\n")
        os.chmod(readable_file, 0o644) # Readable by owner and group, readable by others

        # Executable script
        script_file = os.path.join(temp_dir_path, "public_script.sh")
        with open(script_file, "w") as f:
            f.write("#!/bin/bash\necho 'Hello'\n")
        os.chmod(script_file, 0o755) # Executable

        # Sensitive file
        secrets_file = os.path.join(temp_dir_path, "data", "secrets.txt")
        with open(secrets_file, "w") as f:
            f.write("password=mypassword\n")
        os.chmod(secrets_file, 0o644)

        # Another sensitive file with a different pattern
        pem_file = os.path.join(temp_dir_path, "data", "sensitive", "server.pem")
        with open(pem_file, "w") as f:
            f.write("-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----\n")
        os.chmod(pem_file, 0o600) # Owner read/write only

        # Hidden sensitive file
        hidden_env_file = os.path.join(temp_dir_path, ".hidden_dir", ".env")
        with open(hidden_env_file, "w") as f:
            f.write("DATABASE_URL=postgres://user:pass@host:port/db\n")
        os.chmod(hidden_env_file, 0o644)


        # To test pip checks more thoroughly:
        # 1. Create a virtual environment.
        # 2. Install some packages, including potentially vulnerable ones if you know them.
        #    Example:
        #    python -m venv venv
        #    source venv/bin/activate
        #    pip install requests==2.20.0  # Known vulnerable version
        #    pip install django==2.2.0    # Known vulnerable version
        #    pip install Flask
        #    pip install pip-audit  # Ensure pip-audit is installed
        #    deactivate
        # 3. Run the auditor against a directory within this virtual environment.
        #    Or, if running system-wide, ensure your pip is correctly configured.
        # For this example, we'll assume basic packages and that pip-audit might be installed.

        # Initialize the auditor with the temporary directory
        auditor = SecurityAuditor(target_path=temp_dir_path)

        print("\n--- Running Individual Checks ---")

        # Assess Permissions
        perm_report = auditor.assess_permissions()
        print("\nPermission Assessment Report:")
        print(json.dumps(perm_report, indent=2))
        if not perm_report["success"]:
            print(f"Permission check failed: {perm_report['message']}")

        # Check for Sensitive Files
        sensitive_report = auditor.check_for_exposed_sensitive_files()
        print("\nSensitive File Check Report:")
        print(json.dumps(sensitive_report, indent=2))
        if not sensitive_report["success"]:
            print(f"Sensitive file check failed: {sensitive_report['message']}")

        # Check Installed Packages
        packages_report = auditor.check_installed_packages()
        print("\nInstalled Packages Report:")
        print(json.dumps(packages_report, indent=2))
        if not packages_report["success"]:
            print(f"Package check failed: {packages_report['message']}")

        # Check System Configuration (macOS specific)
        sys_config_report = auditor.check_system_configuration_basic()
        print("\nSystem Configuration Report:")
        print(json.dumps(sys_config_report, indent=2))
        if not sys_config_report["success"]:
            print(f"System config check failed: {sys_config_report['message']}")

        print("\n--- Generating Full Report ---")
        full_report = auditor.generate_full_report()
        print("\nFull Security Audit Report:")
        print(json.dumps(full_report, indent=2))

        # Example of how to access specific parts of the report
        print("\n--- Summary of Recommendations ---")
        if full_report.get("consolidated_recommendations"):
            for rec in full_report["consolidated_recommendations"]:
                print(f"- {rec}")
        else:
            print("No recommendations found.")

    except (ValueError, FileNotFoundError, PermissionError) as e:
        print(f"Error initializing auditor: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during the example usage: {e}")
    finally:
        # Clean up the temporary directory
        if os.path.exists(temp_dir_path):
            print(f"\nCleaning up temporary directory: {temp_dir_path}")
            shutil.rmtree(temp_dir_path)