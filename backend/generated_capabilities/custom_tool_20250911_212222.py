
import json
import os
import shutil
import stat
import sys
import uuid
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime

class DisasterRecoveryTool:
    """
    A comprehensive tool for creating, managing, and testing disaster recovery plans.

    This class provides functionalities to define DR components, generate recovery
    procedures, and simulate testing scenarios. It is designed to be safe and
    non-intrusive, operating on provided file paths and configurations without
    making unauthorized system modifications.

    Key Enhancements:
    - Comprehensive DR Plan Generation: Includes risk assessment, business impact analysis,
      detailed recovery procedures, and robust testing/validation frameworks.
    - Enhanced Input Validation: Robust checks for user inputs to prevent unexpected behavior.
    - Improved Error Handling: More specific error messages and graceful failure handling.
    - Detailed Testing & Validation: Expanded simulation capabilities for recovery steps and validation procedures.
    - Risk Assessment and BIA Integration: Placeholders and mechanisms to incorporate these crucial elements.
    - Component Dependencies Management: Explicit handling and validation of inter-component dependencies.
    - Audit Trail: Basic logging for actions performed.
    - Versioning: Basic versioning for the DR plan configuration.
    """

    def __init__(self, config_path: str = "dr_config.json"):
        """
        Initializes the DisasterRecoveryTool.

        Args:
            config_path: The file path for storing and loading the DR configuration.
                         Defaults to "dr_config.json" in the current directory.
        """
        if not isinstance(config_path, str) or not config_path:
            raise ValueError("config_path must be a non-empty string.")

        self.config_path = config_path
        self.config: Dict[str, Any] = self._load_config()
        self._initialize_config_structure()
        self._audit_log("Tool initialized", {"config_path": config_path})

    def _initialize_config_structure(self):
        """Ensures the basic structure of the configuration dictionary exists."""
        if "components" not in self.config:
            self.config["components"] = {}
        if "dr_plan" not in self.config:
            self.config["dr_plan"] = {
                "plan_name": "Disaster Recovery Plan",
                "version": "1.0",
                "created_date": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "risk_assessment": {},
                "business_impact_analysis": {}
            }
        if "testing_framework" not in self.config:
            self.config["testing_framework"] = {
                "procedures": {},
                "validation_steps": {}
            }

    def _audit_log(self, action: str, details: Optional[Dict[str, Any]] = None):
        """Logs actions performed by the tool."""
        if "audit_trail" not in self.config:
            self.config["audit_trail"] = []
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details if details is not None else {}
        }
        self.config["audit_trail"].append(log_entry)
        # We don't auto-save here to avoid excessive writes, but it's good practice to consider.

    def _load_config(self) -> Dict[str, Any]:
        """
        Loads the DR configuration from a JSON file.

        If the file does not exist, an empty configuration is returned.

        Returns:
            A dictionary representing the DR configuration.
        """
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config_data = json.load(f)
                    if not isinstance(config_data, dict):
                        print(f"Warning: Configuration file '{self.config_path}' is not a valid JSON object. Starting with empty configuration.", file=sys.stderr)
                        return {}
                    return config_data
            except (IOError, json.JSONDecodeError) as e:
                print(f"Warning: Could not load configuration from {self.config_path}: {e}. Starting with empty configuration.", file=sys.stderr)
                return {}
        return {}

    def _save_config(self) -> Dict[str, Any]:
        """
        Saves the current DR configuration to a JSON file.

        Returns:
            A dictionary indicating the success status and a message.
        """
        self.config["dr_plan"]["last_updated"] = datetime.now().isoformat()
        try:
            os.makedirs(os.path.dirname(self.config_path) or '.', exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            self._audit_log("Configuration saved", {"path": self.config_path})
            return {"success": True, "message": f"Configuration saved to {self.config_path}"}
        except IOError as e:
            self._audit_log("Configuration save failed", {"path": self.config_path, "error": str(e)})
            return {"success": False, "message": f"Failed to save configuration to {self.config_path}: {e}"}

    def _validate_component_details(self, component_type: str, details: Dict[str, Any]) -> List[str]:
        """Validates essential details based on component type."""
        errors = []
        if component_type in ["server", "database", "application", "network_device", "storage"]:
            if "backup_location" not in details or not details["backup_location"]:
                errors.append("Missing 'backup_location' detail. Specify where backups are stored or how they can be accessed.")
            if "restore_target" not in details or not details["restore_target"]:
                errors.append("Missing 'restore_target' detail. Specify the intended location for restored data/configurations.")
        if component_type == "application":
            if "dependencies" in details and not isinstance(details["dependencies"], list):
                errors.append("Invalid 'dependencies' format. It should be a list of component names.")
            if "entrypoint" not in details or not details["entrypoint"]:
                errors.append("Missing 'entrypoint' detail for application. Specify how to start the application.")
        if component_type == "database":
            if "db_type" not in details or not details["db_type"]:
                errors.append("Missing 'db_type' detail for database.")
        return errors

    def add_component(self, component_name: str, component_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adds a new component to the disaster recovery plan.

        Args:
            component_name: A unique name for the component.
            component_type: The type of the component (e.g., "server", "database", "application", "network_device", "storage", "service").
            details: A dictionary containing specific details about the component.
                     This can include paths, IP addresses, dependencies, criticality, etc.

        Returns:
            A dictionary indicating the success status and a message.
        """
        if not isinstance(component_name, str) or not component_name:
            return {"success": False, "message": "Invalid input: component_name must be a non-empty string."}
        if not isinstance(component_type, str) or not component_type:
            return {"success": False, "message": "Invalid input: component_type must be a non-empty string."}
        if not isinstance(details, dict):
            return {"success": False, "message": "Invalid input: details must be a dictionary."}

        if component_name in self.config["components"]:
            return {"success": False, "message": f"Component '{component_name}' already exists."}

        validation_errors = self._validate_component_details(component_type, details)
        if validation_errors:
            return {"success": False, "message": f"Component details validation failed for '{component_name}': " + " ".join(validation_errors)}

        self.config["components"][component_name] = {
            "type": component_type,
            "details": details
        }
        self._audit_log("Component added", {"name": component_name, "type": component_type})
        return self._save_config()

    def remove_component(self, component_name: str) -> Dict[str, Any]:
        """
        Removes a component from the disaster recovery plan.

        Args:
            component_name: The name of the component to remove.

        Returns:
            A dictionary indicating the success status and a message.
        """
        if not isinstance(component_name, str) or not component_name:
            return {"success": False, "message": "Invalid input: component_name must be a non-empty string."}

        if component_name not in self.config["components"]:
            return {"success": False, "message": f"Component '{component_name}' not found."}

        del self.config["components"][component_name]
        self._audit_log("Component removed", {"name": component_name})
        return self._save_config()

    def get_component(self, component_name: str) -> Dict[str, Any]:
        """
        Retrieves details for a specific component.

        Args:
            component_name: The name of the component.

        Returns:
            A dictionary containing the component details or an error message.
        """
        if not isinstance(component_name, str) or not component_name:
            return {"success": False, "message": "Invalid input: component_name must be a non-empty string."}

        if component_name not in self.config["components"]:
            return {"success": False, "message": f"Component '{component_name}' not found."}

        return {
            "success": True,
            "message": f"Details for component '{component_name}' retrieved successfully.",
            "data": {
                "name": component_name,
                "component": self.config["components"][component_name]
            }
        }

    def list_components(self) -> Dict[str, Any]:
        """
        Lists all components defined in the disaster recovery plan.

        Returns:
            A dictionary containing a list of components or an error message.
        """
        if not self.config["components"]:
            return {"success": True, "message": "No components defined in the DR plan.", "data": []}

        components_list = []
        for name, data in self.config["components"].items():
            components_list.append({"name": name, "type": data.get("type", "unknown")})

        return {
            "success": True,
            "message": "Components listed successfully.",
            "data": components_list
        }

    def _generate_component_readme(self, component_dir: str, name: str, component_data: Dict[str, Any]) -> str:
        """Generates the README.md content for a component."""
        readme_content = f"# {name}\n\n"
        readme_content += f"**Type:** {component_data.get('type', 'N/A')}\n\n"

        readme_content += "## Disaster Recovery Procedures\n\n"
        readme_content += "The following steps outline the typical recovery process:\n\n"
        readme_content += "1.  **Backup Verification:** Confirm the integrity and accessibility of backups.\n"
        readme_content += "2.  **Resource Provisioning:** Ensure necessary infrastructure (servers, cloud instances) is available.\n"
        readme_content += "3.  **System/Data Restore:** Restore the component's data and configurations from verified backups.\n"
        readme_content += "4.  **Dependency Resolution:** Verify and bring up all prerequisite components.\n"
        readme_content += "5.  **Component Startup:** Initiate the component's services or applications.\n"
        readme_content += "6.  **Functional Testing:** Execute predefined tests to ensure operational readiness.\n"
        readme_content += "7.  **Final Validation:** Conduct comprehensive checks and user acceptance testing.\n\n"

        readme_content += "## Component Details:\n\n"
        for key, value in component_data.get("details", {}).items():
            if isinstance(value, list):
                value_str = ", ".join(map(str, value))
            else:
                value_str = str(value)
            readme_content += f"- **{key.replace('_', ' ').title()}:** {value_str}\n"

        # Add pointers to testing and validation procedures
        if name in self.config["testing_framework"]["procedures"]:
            readme_content += "\n## Testing Procedures:\n\n"
            for proc_name, proc_details in self.config["testing_framework"]["procedures"][name].items():
                readme_content += f"- **{proc_name.replace('_', ' ').title()}:** {proc_details.get('description', 'No description available.')}\n"

        if name in self.config["testing_framework"]["validation_steps"]:
            readme_content += "\n## Validation Steps:\n\n"
            for val_name, val_details in self.config["testing_framework"]["validation_steps"][name].items():
                readme_content += f"- **{val_name.replace('_', ' ').title()}:** {val_details.get('description', 'No description available.')}\n"

        return readme_content

    def generate_recovery_plan(self, output_dir: str = "recovery_plan") -> Dict[str, Any]:
        """
        Generates a structured disaster recovery plan document based on the configured components.

        This method creates a directory and populates it with subdirectories and files
        representing the recovery steps for each component. It also includes sections for
        Risk Assessment and Business Impact Analysis placeholders.

        Args:
            output_dir: The directory where the recovery plan will be generated.

        Returns:
            A dictionary indicating the success status and a message.
        """
        if not isinstance(output_dir, str) or not output_dir:
            return {"success": False, "message": "Invalid input: output_dir must be a non-empty string."}

        if not self.config["components"]:
            return {"success": False, "message": "No components defined to generate a recovery plan."}

        try:
            if os.path.exists(output_dir):
                print(f"Warning: Output directory '{output_dir}' already exists. It will be cleared and recreated.", file=sys.stderr)
                shutil.rmtree(output_dir)
            os.makedirs(output_dir, exist_ok=True)

            plan_summary = {
                "plan_name": self.config["dr_plan"].get("plan_name", "Disaster Recovery Plan"),
                "version": self.config["dr_plan"].get("version", "N/A"),
                "generated_on": datetime.now().isoformat(),
                "components_count": len(self.config["components"]),
                "risk_assessment_file": "RISK_ASSESSMENT.md",
                "business_impact_analysis_file": "BUSINESS_IMPACT_ANALYSIS.md",
                "components_documentation": {}
            }

            # Create placeholder files for Risk Assessment and Business Impact Analysis
            risk_assessment_path = os.path.join(output_dir, "RISK_ASSESSMENT.md")
            with open(risk_assessment_path, "w") as f:
                f.write("# Risk Assessment\n\n")
                f.write("This section should detail potential threats, vulnerabilities, and their likelihood and impact.\n")
                for threat, details in self.config["dr_plan"]["risk_assessment"].items():
                    f.write(f"\n## {threat}\n")
                    for key, value in details.items():
                        f.write(f"- **{key.replace('_', ' ').title()}:** {value}\n")
                f.write("\n*Last updated in config: {self.config['dr_plan']['last_updated']}*")

            bia_path = os.path.join(output_dir, "BUSINESS_IMPACT_ANALYSIS.md")
            with open(bia_path, "w") as f:
                f.write("# Business Impact Analysis (BIA)\n\n")
                f.write("This section should detail the impact of disruptions on business operations, including RTO and RPO.\n")
                for criticality, details in self.config["dr_plan"]["business_impact_analysis"].items():
                    f.write(f"\n## Criticality Level: {criticality.upper()}\n")
                    for key, value in details.items():
                        f.write(f"- **{key.replace('_', ' ').title()}:** {value}\n")
                f.write("\n*Last updated in config: {self.config['dr_plan']['last_updated']}*")


            for name, component_data in self.config["components"].items():
                component_dir = os.path.join(output_dir, "components", name)
                os.makedirs(component_dir, exist_ok=True)

                readme_path = os.path.join(component_dir, "README.md")
                readme_content = self._generate_component_readme(component_dir, name, component_data)
                with open(readme_path, "w") as f:
                    f.write(readme_content)

                plan_summary["components_documentation"][name] = f"components/{name}/README.md"

            # Create a main summary file
            summary_path = os.path.join(output_dir, "DR_PLAN_SUMMARY.json")
            with open(summary_path, "w") as f:
                json.dump(plan_summary, f, indent=4)

            self._audit_log("Recovery plan generated", {"output_dir": output_dir})
            return {"success": True, "message": f"Disaster recovery plan generated successfully in '{output_dir}'."}

        except OSError as e:
            self._audit_log("Recovery plan generation failed", {"output_dir": output_dir, "error": str(e)})
            return {"success": False, "message": f"Failed to generate recovery plan: {e}"}
        except Exception as e:
            self._audit_log("Recovery plan generation failed (unexpected)", {"output_dir": output_dir, "error": str(e)})
            return {"success": False, "message": f"An unexpected error occurred during plan generation: {e}"}

    # --- Simulation Helper Functions ---

    def _simulate_file_operation(self, source_path: str, destination_path: str, operation_type: str, simulate_success: bool = True) -> Dict[str, Any]:
        """
        Simulates file operations like backup or restore.

        Args:
            source_path: The simulated source path.
            destination_path: The simulated destination path.
            operation_type: 'backup' or 'restore'.
            simulate_success: If True, simulates a successful operation. If False, simulates failure.

        Returns:
            A dictionary indicating the success status and a message.
        """
        if not source_path or not destination_path:
            return {"success": False, "message": f"Invalid input: source_path and destination_path are required for {operation_type} simulation."}

        log_message = f"Simulated {operation_type} "
        if operation_type == "backup":
            # Simulate checking if backup source exists
            if not os.path.exists(source_path):
                return {"success": False, "message": f"Simulated {operation_type} source not found at '{source_path}'."}
            log_message += f"from '{source_path}'."
        elif operation_type == "restore":
            # Simulate creating directory and a dummy file
            try:
                os.makedirs(os.path.dirname(destination_path), exist_ok=True)
                if simulate_success:
                    with open(destination_path, "w") as f:
                        f.write(f"Simulated restored content from {source_path}\n")
                    log_message += f"to '{destination_path}' from '{source_path}'."
                else:
                    log_message += f"to '{destination_path}' from '{source_path}' (simulated failure)."
            except OSError as e:
                return {"success": False, "message": f"Simulated {operation_type} failed due to OS error: {e}"}
        else:
            return {"success": False, "message": f"Unknown operation type '{operation_type}'."}

        if simulate_success:
            return {"success": True, "message": log_message}
        else:
            return {"success": False, "message": log_message + " (Simulated Failure)"}

    def _simulate_service_operation(self, component_name: str, operation_type: str, simulate_success: bool = True) -> Dict[str, Any]:
        """
        Simulates starting or stopping a component service.

        Args:
            component_name: The name of the component.
            operation_type: 'start' or 'stop'.
            simulate_success: If True, simulates a successful operation. If False, simulates failure.

        Returns:
            A dictionary indicating the success status and a message.
        """
        if not component_name:
            return {"success": False, "message": "Invalid input: component_name is required."}

        component_info = self.get_component(component_name)
        if not component_info["success"]:
            return component_info # Return the error from get_component

        message = f"Simulated {operation_type} of component '{component_name}'."
        if simulate_success:
            return {"success": True, "message": message}
        else:
            return {"success": False, "message": message + " (Simulated Failure)"}

    def _simulate_dependency_check(self, component_name: str, dependency_name: str, simulate_success: bool = True) -> Dict[str, Any]:
        """
        Simulates checking a dependency for a given component.

        Args:
            component_name: The name of the component whose dependency is being validated.
            dependency_name: The name of the dependency.
            simulate_success: If True, simulates a successful validation. If False, simulates failure.

        Returns:
            A dictionary indicating the success status and a message.
        """
        if not component_name or not dependency_name:
            return {"success": False, "message": "Invalid input: component_name and dependency_name are required."}

        message = f"Simulated dependency check for '{dependency_name}' (required by '{component_name}')."
        if simulate_success:
            return {"success": True, "message": message}
        else:
            return {"success": False, "message": message + " (Simulated Failure)"}

    def _simulate_validation_procedure(self, component_name: str, procedure_name: str, simulate_success: bool = True) -> Dict[str, Any]:
        """
        Simulates execution of a specific validation procedure for a component.

        Args:
            component_name: The name of the component being tested.
            procedure_name: The name of the validation procedure.
            simulate_success: If True, simulates a successful test. If False, simulates failure.

        Returns:
            A dictionary indicating the success status and a message.
        """
        if not component_name or not procedure_name:
            return {"success": False, "message": "Invalid input: component_name and procedure_name are required."}

        message = f"Simulated execution of validation procedure '{procedure_name}' for component '{component_name}'."
        if simulate_success:
            return {"success": True, "message": message}
        else:
            return {"success": False, "message": message + " (Simulated Failure)"}

    # --- Recovery Step Testing ---

    def test_recovery_step(self, component_name: str, step_name: str, simulate_success: bool = True) -> Dict[str, Any]:
        """
        Simulates the execution of a specific recovery step for a component.

        This method simulates common recovery actions.

        Args:
            component_name: The name of the component for which to test a recovery step.
            step_name: The name of the recovery step to simulate. Common steps include:
                       "backup_verification", "resource_provisioning", "system_restore",
                       "dependency_check", "application_startup", "final_validation".
            simulate_success: If True, simulates a successful execution of the step.
                              If False, simulates a failure.

        Returns:
            A dictionary indicating the success status and a message.
        """
        if not isinstance(component_name, str) or not component_name:
            return {"success": False, "message": "Invalid input: component_name must be a non-empty string."}
        if not isinstance(step_name, str) or not step_name:
            return {"success": False, "message": "Invalid input: step_name must be a non-empty string."}

        component_info = self.get_component(component_name)
        if not component_info["success"]:
            return component_info # Return the error from get_component

        details = component_info["data"]["component"].get("details", {})

        if step_name == "backup_verification":
            backup_location = details.get("backup_location")
            if not backup_location:
                return {"success": False, "message": f"Component '{component_name}' has no 'backup_location' defined for backup verification."}
            # Simulate checking if backup exists or is accessible
            return self._simulate_file_operation(backup_location, "/dev/null", "backup", simulate_success)

        elif step_name == "resource_provisioning":
            # Simulate provisioning of resources (e.g., cloud instances, VMs)
            # This is often a precursor to startup, so we can use a simplified simulation.
            return self._simulate_service_operation(component_name, "provision_resources", simulate_success)

        elif step_name == "system_restore":
            backup_location = details.get("backup_location")
            restore_target = details.get("restore_target")
            if not backup_location:
                return {"success": False, "message": f"Component '{component_name}' has no 'backup_location' defined for system restore."}
            if not restore_target:
                return {"success": False, "message": f"Component '{component_name}' has no 'restore_target' defined for system restore."}
            return self._simulate_file_operation(backup_location, restore_target, "restore", simulate_success)

        elif step_name == "dependency_check":
            dependencies = details.get("dependencies", [])
            if not dependencies:
                return {"success": True, "message": f"Component '{component_name}' has no explicit dependencies listed. Skipping check."}

            results = []
            all_dependencies_ok = True
            for dep_name in dependencies:
                # Check if the dependency is actually defined as a component
                if dep_name not in self.config["components"]:
                    results.append({"dependency": dep_name, "success": False, "message": f"Dependency '{dep_name}' is not defined as a component."})
                    all_dependencies_ok = False
                    continue

                # Simulate checking the dependency
                dep_result = self._simulate_dependency_check(component_name, dep_name, simulate_success)
                results.append({"dependency": dep_name, "success": dep_result["success"], "message": dep_result["message"]})
                if not dep_result["success"]:
                    all_dependencies_ok = False

            if simulate_success and not all_dependencies_ok:
                return {"success": False, "message": f"Dependency check for '{component_name}' failed for one or more dependencies.", "details": results}
            elif simulate_success:
                return {"success": True, "message": f"Simulated successful dependency check for '{component_name}'.", "details": results}
            else: # simulate_success is False, so the overall step fails
                return {"success": False, "message": f"Simulated failed dependency check for '{component_name}'.", "details": results}

        elif step_name == "application_startup":
            entrypoint = details.get("entrypoint")
            if not entrypoint:
                return {"success": False, "message": f"Component '{component_name}' (application) has no 'entrypoint' defined for startup."}
            # Simulate starting the application using its entrypoint
            return self._simulate_service_operation(component_name, "start_application", simulate_success)

        elif step_name == "final_validation":
            # This is a placeholder for more complex validation procedures.
            # In a real scenario, you'd call specific validation functions or
            # trigger registered validation procedures for this component.
            return self._simulate_validation_procedure(component_name, "comprehensive_functional_test", simulate_success)

        else:
            return {"success": False, "message": f"Unknown recovery step '{step_name}' for component '{component_name}'."}

    def run_validation_procedure(self, component_name: str, procedure_name: str, simulate_success: bool = True) -> Dict[str, Any]:
        """
        Runs a specific validation procedure for a component.

        This method simulates the execution of pre-defined validation checks.

        Args:
            component_name: The name of the component to validate.
            procedure_name: The name of the validation procedure to execute.
                            Examples: "check_database_connection", "verify_api_endpoint",
                                      "test_user_login".
            simulate_success: If True, simulates a successful execution of the procedure.
                              If False, simulates a failure.

        Returns:
            A dictionary indicating the success status and a message.
        """
        if not isinstance(component_name, str) or not component_name:
            return {"success": False, "message": "Invalid input: component_name must be a non-empty string."}
        if not isinstance(procedure_name, str) or not procedure_name:
            return {"success": False, "message": "Invalid input: procedure_name must be a non-empty string."}

        component_info = self.get_component(component_name)
        if not component_info["success"]:
            return component_info # Return the error from get_component

        # In a real implementation, you would map procedure_name to actual validation logic
        # based on component_type or specific configurations.
        # For simulation purposes, we directly call the simulation function.
        # We also check if this procedure is registered in the testing framework.
        component_validations = self.config["testing_framework"]["validation_steps"].get(component_name, {})
        if procedure_name not in component_validations:
            print(f"Warning: Validation procedure '{procedure_name}' for component '{component_name}' is not explicitly defined in the testing framework. Proceeding with simulation.", file=sys.stderr)

        self._audit_log("Validation procedure run (simulated)", {"component": component_name, "procedure": procedure_name, "success": simulate_success})
        return self._simulate_validation_procedure(component_name, procedure_name, simulate_success)

    # --- DR Plan Management and Analysis ---

    def update_risk_assessment(self, threat_name: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adds or updates a risk assessment entry.

        Args:
            threat_name: The name of the threat or risk.
            details: A dictionary of details for this threat (e.g., likelihood, impact, mitigation).

        Returns:
            A dictionary indicating the success status and a message.
        """
        if not isinstance(threat_name, str) or not threat_name:
            return {"success": False, "message": "Invalid input: threat_name must be a non-empty string."}
        if not isinstance(details, dict):
            return {"success": False, "message": "Invalid input: details must be a dictionary."}

        self.config["dr_plan"]["risk_assessment"][threat_name] = details
        self._audit_log("Risk assessment updated", {"threat": threat_name})
        return self._save_config()

    def update_business_impact_analysis(self, criticality_level: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adds or updates a business impact analysis entry.

        Args:
            criticality_level: The criticality level (e.g., "high", "medium", "low").
            details: A dictionary of details for this level (e.g., RTO, RPO, business impact).

        Returns:
            A dictionary indicating the success status and a message.
        """
        if not isinstance(criticality_level, str) or not criticality_level:
            return {"success": False, "message": "Invalid input: criticality_level must be a non-empty string."}
        if not isinstance(details, dict):
            return {"success": False, "message": "Invalid input: details must be a dictionary."}

        self.config["dr_plan"]["business_impact_analysis"][criticality_level.lower()] = details
        self._audit_log("Business Impact Analysis updated", {"criticality": criticality_level})
        return self._save_config()

    def add_testing_procedure(self, component_name: str, procedure_name: str, description: str, steps: List[str]) -> Dict[str, Any]:
        """
        Adds a specific testing procedure for a component.

        Args:
            component_name: The name of the component.
            procedure_name: The name of the testing procedure.
            description: A brief description of the procedure.
            steps: A list of steps to execute for this procedure.

        Returns:
            A dictionary indicating the success status and a message.
        """
        if not isinstance(component_name, str) or not component_name:
            return {"success": False, "message": "Invalid input: component_name must be a non-empty string."}
        if not isinstance(procedure_name, str) or not procedure_name:
            return {"success": False, "message": "Invalid input: procedure_name must be a non-empty string."}
        if not isinstance(description, str):
            return {"success": False, "message": "Invalid input: description must be a string."}
        if not isinstance(steps, list):
            return {"success": False, "message": "Invalid input: steps must be a list."}

        if component_name not in self.config["testing_framework"]["procedures"]:
            self.config["testing_framework"]["procedures"][component_name] = {}

        if procedure_name in self.config["testing_framework"]["procedures"][component_name]:
            return {"success": False, "message": f"Testing procedure '{procedure_name}' already exists for component '{component_name}'."}

        self.config["testing_framework"]["procedures"][component_name][procedure_name] = {
            "description": description,
            "steps": steps
        }
        self._audit_log("Testing procedure added", {"component": component_name, "procedure": procedure_name})
        return self._save_config()

    def add_validation_step(self, component_name: str, step_name: str, description: str, validation_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adds a specific validation step for a component.

        Args:
            component_name: The name of the component.
            step_name: The name of the validation step.
            description: A brief description of the validation.
            validation_criteria: A dictionary of criteria for this validation (e.g., expected output, thresholds).

        Returns:
            A dictionary indicating the success status and a message.
        """
        if not isinstance(component_name, str) or not component_name:
            return {"success": False, "message": "Invalid input: component_name must be a non-empty string."}
        if not isinstance(step_name, str) or not step_name:
            return {"success": False, "message": "Invalid input: step_name must be a non-empty string."}
        if not isinstance(description, str):
            return {"success": False, "message": "Invalid input: description must be a string."}
        if not isinstance(validation_criteria, dict):
            return {"success": False, "message": "Invalid input: validation_criteria must be a dictionary."}

        if component_name not in self.config["testing_framework"]["validation_steps"]:
            self.config["testing_framework"]["validation_steps"][component_name] = {}

        if step_name in self.config["testing_framework"]["validation_steps"][component_name]:
            return {"success": False, "message": f"Validation step '{step_name}' already exists for component '{component_name}'."}

        self.config["testing_framework"]["validation_steps"][component_name][step_name] = {
            "description": description,
            "criteria": validation_criteria
        }
        self._audit_log("Validation step added", {"component": component_name, "step": step_name})
        return self._save_config()


    def validate_dr_plan_completeness(self) -> Dict[str, Any]:
        """
        Performs a comprehensive check for completeness of the configured DR plan.

        Checks essential details for components, dependencies, and configuration of
        risk assessment, BIA, testing, and validation procedures.

        Returns:
            A dictionary indicating the success status and a message, along with
            details of any identified gaps.
        """
        gaps = []

        # Check DR Plan structure
        if not self.config["dr_plan"].get("plan_name"):
            gaps.append({"area": "DR Plan Metadata", "issue": "Missing 'plan_name'.", "recommendation": "Define a name for the DR plan."})
        if not self.config["dr_plan"].get("version"):
            gaps.append({"area": "DR Plan Metadata", "issue": "Missing 'version'.", "recommendation": "Assign a version number to the DR plan."})
        if not self.config["dr_plan"]["risk_assessment"]:
            gaps.append({"area": "Risk Assessment", "issue": "Risk assessment data is empty.", "recommendation": "Populate the risk assessment with potential threats and vulnerabilities."})
        if not self.config["dr_plan"]["business_impact_analysis"]:
            gaps.append({"area": "Business Impact Analysis", "issue": "BIA data is empty.", "recommendation": "Populate the BIA with RTO/RPO and business impacts."})

        # Check Components
        if not self.config["components"]:
            gaps.append({"area": "Components", "issue": "No components defined in the DR plan.", "recommendation": "Add components that are critical to your operations."})
        else:
            for name, component_data in self.config["components"].items():
                comp_type = component_data.get("type")
                details = component_data.get("details", {})

                # Check component-specific details
                component_detail_gaps = self._validate_component_details(comp_type, details)
                for gap_msg in component_detail_gaps:
                    gaps.append({
                        "area": f"Component: {name}",
                        "issue": gap_msg,
                        "recommendation": "Ensure all required details for this component type are provided."
                    })

                # Check dependencies
                dependencies = details.get("dependencies", [])
                if dependencies:
                    for dep in dependencies:
                        if dep not in self.config["components"]:
                            gaps.append({
                                "area": f"Component: {name} (Dependencies)",
                                "issue": f"Dependency '{dep}' is listed but not defined as a component.",
                                "recommendation": f"Define '{dep}' as a component or remove it from dependencies."
                            })

                # Check if component is covered by testing/validation
                if name not in self.config["testing_framework"]["procedures"] and name not in self.config["testing_framework"]["validation_steps"]:
                     gaps.append({
                        "area": f"Component: {name} (Testing/Validation)",
                        "issue": "No specific testing or validation procedures defined.",
                        "recommendation": "Define relevant testing and validation procedures for this component to ensure recovery success."
                    })


        if not gaps:
            return {"success": True, "message": "DR plan appears to be comprehensive and complete based on configured elements.", "data": []}
        else:
            return {"success": False, "message": "Identified potential gaps in the DR plan's completeness.", "data": gaps}

    def get_dr_plan_details(self) -> Dict[str, Any]:
        """
        Retrieves the overall DR plan metadata.

        Returns:
            A dictionary containing DR plan metadata.
        """
        return {
            "success": True,
            "message": "DR plan metadata retrieved.",
            "data": self.config.get("dr_plan", {})
        }

    def get_audit_trail(self) -> Dict[str, Any]:
        """
        Retrieves the audit trail of actions performed by the tool.

        Returns:
            A dictionary containing the audit trail log.
        """
        return {
            "success": True,
            "message": "Audit trail retrieved.",
            "data": self.config.get("audit_trail", [])
        }

# Example Usage (for demonstration purposes, typically run in a separate script)
if __name__ == "__main__":
    # Ensure macOS compatibility: paths are generally fine, no specific issues expected with standard file ops.
    # The use of os and shutil is cross-platform.

    dr_tool = DisasterRecoveryTool("my_dr_plan_config.json")

    # --- Add Components ---
    print("\n--- Adding Components ---")
    add_server_result = dr_tool.add_component(
        component_name="webserver_01",
        component_type="server",
        details={
            "hostname": "webserver.example.com",
            "ip_address": "192.168.1.10",
            "os": "macOS Ventura",
            "backup_location": "/Volumes/Backup/webserver_01/full_backup.tar.gz",
            "restore_target": "/Applications/WebServer",
            "criticality": "high",
            "tags": ["web", "production"]
        }
    )
    print(f"Add webserver_01: {add_server_result}")

    add_db_result = dr_tool.add_component(
        component_name="database_prod",
        component_type="database",
        details={
            "db_type": "PostgreSQL",
            "version": "14.5",
            "host": "db.example.com",
            "port": 5432,
            "backup_location": "/Volumes/Backup/db_prod/daily_snapshot.sql.gz",
            "restore_target": "/usr/local/pgsql/data",
            "replication_lag_threshold": "5 minutes",
            "criticality": "high"
        }
    )
    print(f"Add database_prod: {add_db_result}")

    add_app_result = dr_tool.add_component(
        component_name="api_service",
        component_type="application",
        details={
            "service_name": "api_svc",
            "language": "Python",
            "framework": "FastAPI",
            "dependencies": ["webserver_01", "database_prod"],
            "config_path": "/etc/api_service/config.yaml",
            "backup_location": "/Volumes/Backup/api_service/config_backup.zip",
            "restore_target": "/etc/api_service",
            "entrypoint": "uvicorn main:app --host 0.0.0.0 --port 8000",
            "criticality": "high"
        }
    )
    print(f"Add api_service: {add_app_result}")

    # Add a component without critical details to test validation later
    add_logging_result = dr_tool.add_component(
        component_name="logging_service",
        component_type="service",
        details={
            "description": "Centralized logging service.",
            "criticality": "medium"
            # Missing backup_location and restore_target
        }
    )
    print(f"Add logging_service: {add_logging_result}")


    # --- Add Testing and Validation Procedures ---
    print("\n--- Adding Testing Procedures ---")
    add_test_webserver_proc = dr_tool.add_testing_procedure(
        component_name="webserver_01",
        procedure_name="check_http_response",
        description="Verify the webserver responds to HTTP requests on its primary port.",
        steps=["Connect to webserver_01:80", "Send GET request to /", "Assert status code 200"]
    )
    print(f"Add test procedure for webserver_01: {add_test_webserver_proc}")

    add_test_db_proc = dr_tool.add_testing_procedure(
        component_name="database_prod",
        procedure_name="verify_data_integrity",
        description="Perform a checksum on a key table to ensure data integrity post-restore.",
        steps=["Connect to database_prod", "SELECT MD5(table_name) FROM some_table LIMIT 1", "Compare checksum against baseline"]
    )
    print(f"Add test procedure for database_prod: {add_test_db_proc}")


    print("\n--- Adding Validation Steps ---")
    add_validation_api_conn = dr_tool.add_validation_step(
        component_name="api_service",
        step_name="api_endpoint_availability",
        description="Check if the main API endpoint is reachable and responding.",
        validation_criteria={"endpoint": "/health", "expected_status": 200, "response_time_ms": 500}
    )
    print(f"Add validation step for api_service: {add_validation_api_conn}")

    add_validation_db_query = dr_tool.add_validation_step(
        component_name="database_prod",
        step_name="sample_query_success",
        description="Execute a simple query to confirm database operational status.",
        validation_criteria={"query": "SELECT 1;", "expected_result": 1}
    )
    print(f"Add validation step for database_prod: {add_validation_db_query}")

    # --- List Components ---
    print("\n--- Listing Components ---")
    list_comps_result = dr_tool.list_components()
    print(json.dumps(list_comps_result, indent=2))

    # --- Get Component Details ---
    print("\n--- Getting Component Details ---")
    get_server_result = dr_tool.get_component("webserver_01")
    print(json.dumps(get_server_result, indent=2))

    # --- Update DR Plan Metadata ---
    print("\n--- Updating DR Plan Metadata ---")
    update_plan_name = dr_tool.config["dr_plan"]["plan_name"] = "Production Systems DR Plan"
    update_plan_version = dr_tool.config["dr_plan"]["version"] = "1.1"

    update_risk_result = dr_tool.update_risk_assessment(
        threat_name="Ransomware Attack",
        details={"likelihood": "medium", "impact": "high", "mitigation": "Regular backups, network segmentation, endpoint detection"}
    )
    print(f"Update risk assessment: {update_risk_result}")

    update_bia_result = dr_tool.update_business_impact_analysis(
        criticality_level="high",
        details={"rto_hours": 4, "rpo_minutes": 15, "business_impact": "Complete service outage, significant financial loss."}
    )
    print(f"Update BIA: {update_bia_result}")

    # --- Generate Recovery Plan ---
    print("\n--- Generating Recovery Plan ---")
    generate_plan_result = dr_tool.generate_recovery_plan("my_disaster_recovery_plan")
    print(generate_plan_result)
    if generate_plan_result["success"]:
        print(f"Check the directory 'my_disaster_recovery_plan' for generated files.")

    # --- Test Recovery Steps ---
    print("\n--- Testing Recovery Steps (Simulated Success) ---")

    # Test backup verification for webserver_01
    test_backup_webserver = dr_tool.test_recovery_step(
        component_name="webserver_01",
        step_name="backup_verification",
        simulate_success=True
    )
    print(f"Test 'backup_verification' for webserver_01: {test_backup_webserver}")

    # Test system restore for database_prod
    test_restore_db = dr_tool.test_recovery_step(
        component_name="database_prod",
        step_name="system_restore",
        simulate_success=True
    )
    print(f"Test 'system_restore' for database_prod: {test_restore_db}")

    # Test dependency check for api_service
    test_deps_api = dr_tool.test_recovery_step(
        component_name="api_service",
        step_name="dependency_check",
        simulate_success=True
    )
    print(f"Test 'dependency_check' for api_service: {test_deps_api}")

    # Test application startup for api_service
    test_startup_api = dr_tool.test_recovery_step(
        component_name="api_service",
        step_name="application_startup",
        simulate_success=True
    )
    print(f"Test 'application_startup' for api_service: {test_startup_api}")

    print("\n--- Testing Recovery Steps (Simulated Failure) ---")
    # Test backup verification for webserver_01 (simulating failure)
    test_backup_webserver_fail = dr_tool.test_recovery_step(
        component_name="webserver_01",
        step_name="backup_verification",
        simulate_success=False
    )
    print(f"Test 'backup_verification' for webserver_01 (fail): {test_backup_webserver_fail}")

    # Test dependency check for api_service (simulating failure)
    test_deps_api_fail = dr_tool.test_recovery_step(
        component_name="api_service",
        step_name="dependency_check",
        simulate_success=False
    )
    print(f"Test 'dependency_check' for api_service (fail): {test_deps_api_fail}")

    # --- Run Validation Procedures ---
    print("\n--- Running Validation Procedures (Simulated Success) ---")
    validate_db_conn = dr_tool.run_validation_procedure(
        component_name="database_prod",
        procedure_name="sample_query_success", # Using the added validation step
        simulate_success=True
    )
    print(f"Validate 'sample_query_success' for database_prod: {validate_db_conn}")

    validate_api_endpoint = dr_tool.run_validation_procedure(
        component_name="api_service",
        procedure_name="api_endpoint_availability", # Using the added validation step
        simulate_success=True
    )
    print(f"Validate 'api_endpoint_availability' for api_service: {validate_api_endpoint}")

    print("\n--- Running Validation Procedures (Simulated Failure) ---")
    validate_api_endpoint_fail = dr_tool.run_validation_procedure(
        component_name="api_service",
        procedure_name="api_endpoint_availability",
        simulate_success=False
    )
    print(f"Validate 'api_endpoint_availability' for api_service (fail): {validate_api_endpoint_fail}")

    # --- Validate DR Plan Completeness ---
    print("\n--- Validating DR Plan Completeness ---")
    completeness_check = dr_tool.validate_dr_plan_completeness()
    print(json.dumps(completeness_check, indent=2))

    # Example: Remove a component that is a dependency to see completeness fail
    dr_tool.remove_component("webserver_01")
    print("\n--- Re-validating DR Plan Completeness after removing webserver_01 ---")
    completeness_check_after_remove_dep = dr_tool.validate_dr_plan_completeness()
    print(json.dumps(completeness_check_after_remove_dep, indent=2))


    # --- Clean up generated config file and directory ---
    # Uncomment to clean up after execution
    # if os.path.exists("my_dr_plan_config.json"):
    #     os.remove("my_dr_plan_config.json")
    # if os.path.exists("my_disaster_recovery_plan"):
    #     shutil.rmtree("my_disaster_recovery_plan")

    print("\n--- Audit Trail ---")
    audit_trail = dr_tool.get_audit_trail()
    print(json.dumps(audit_trail["data"], indent=2))
