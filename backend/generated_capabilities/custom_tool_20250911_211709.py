
import os
import json
import platform
from typing import Dict, Any, List, Optional
from datetime import datetime

class BackupStrategyGenerator:
    """
    A specialized tool class for generating comprehensive backup strategy documents.

    This class provides methods to create a detailed backup strategy document
    with step-by-step procedures and best practices, tailored for various
    backup scenarios and operating systems. It focuses on generating structured
    documentation rather than performing actual backup operations.
    """

    def __init__(self, strategy_name: str = "General Data Backup Strategy"):
        """
        Initializes the BackupStrategyGenerator.

        Args:
            strategy_name: A descriptive name for the backup strategy.
        """
        if not isinstance(strategy_name, str) or not strategy_name.strip():
            raise ValueError("Strategy name must be a non-empty string.")

        self.strategy_name = strategy_name
        self.document: Dict[str, Any] = {
            "title": f"Comprehensive Backup Strategy: {self.strategy_name}",
            "overview": "A default overview if none was provided. This document outlines a comprehensive backup strategy to ensure data resilience against various threats.",
            "scope": ["Default: All critical data and system configurations."],
            "backup_types": [
                {"name": "Full Backup", "description": "A complete copy of all selected data. Performed less frequently.", "tools": []},
                {"name": "Incremental Backup", "description": "Backs up only the data that has changed since the last backup (full or incremental). Performed frequently.", "tools": []},
                {"name": "Differential Backup", "description": "Backs up all data that has changed since the last full backup. Performed less frequently than incremental.", "tools": []}
            ],
            "retention_policy": {
                "description": "Define how long different backup versions are kept.",
                "example": {"daily": "7 days", "weekly": "4 weeks", "monthly": "12 months", "yearly": "3 years"}
            },
            "backup_schedule": {
                "description": "Define the frequency and timing of different backup types.",
                "example": {"full_backup": "Sunday 02:00", "incremental_backup": "Daily 03:00"}
            },
            "storage_locations": [
                {"type": "Local", "location": "/path/to/default/storage", "description": "Default local storage location. Consider using an external drive or NAS."}
            ],
            "security_considerations": [
                "Encrypt sensitive data at rest and in transit.",
                "Use strong, unique passwords for all backup systems.",
                "Implement access control to restrict who can access backup data and systems.",
                "Regularly update backup software and firmware to patch vulnerabilities."
            ],
            "testing_and_validation": [
                "Schedule regular test restores to verify data integrity and recoverability.",
                "Perform full system recovery tests periodically.",
                "Document all testing procedures and outcomes."
            ],
            "disaster_recovery_plan_link": None,
            "procedures": [
                {
                    "title": "Initial Backup Configuration",
                    "description": "1. Install and configure chosen backup software.\n2. Define backup sources (files, folders, system images).\n3. Set up destination storage locations.\n4. Configure initial backup job.",
                    "os_compatibility": ["macOS", "Linux", "Windows"]
                }
            ],
            "best_practices": [
                "Follow the 3-2-1 backup rule: 3 copies of your data, on 2 different media types, with 1 copy offsite.",
                "Automate your backups to ensure consistency and reduce human error.",
                "Never store your only copy of data on a single device.",
                "Keep backup media physically secure and protected from environmental hazards.",
                "Regularly review and update your backup strategy as your data and needs evolve.",
                "Ensure sufficient free space on backup destinations.",
                "Use multiple backup destinations (e.g., local and cloud) for redundancy."
            ],
            "version_history": [
                {"version": "1.0", "date": datetime.now().strftime("%Y-%m-%d"), "description": "Initial document creation."}
            ]
        }

    def _create_response(self, success: bool, message: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Creates a standardized response dictionary.

        Args:
            success: Boolean indicating the success of the operation.
            message: A human-readable message describing the outcome.
            data: Optional dictionary containing relevant data.

        Returns:
            A dictionary representing the operation's result.
        """
        response = {"success": success, "message": message}
        if data:
            response.update(data)
        return response

    def _validate_string_input(self, input_value: Any, field_name: str) -> bool:
        """Validates if an input is a non-empty string."""
        if not isinstance(input_value, str) or not input_value.strip():
            print(f"Error: {field_name} cannot be empty.")
            return False
        return True

    def _validate_list_input(self, input_value: Any, field_name: str, item_type: type = str) -> bool:
        """Validates if an input is a list of a specific item type."""
        if not isinstance(input_value, list):
            print(f"Error: {field_name} must be provided as a list.")
            return False
        if item_type is not None:
            for item in input_value:
                if not isinstance(item, item_type):
                    print(f"Error: All items in {field_name} must be of type {item_type.__name__}.")
                    return False
        return True

    def set_overview(self, overview_text: str) -> Dict[str, Any]:
        """
        Sets the overview section of the backup strategy document.

        Args:
            overview_text: The text for the overview section.

        Returns:
            A dictionary with the result of the operation.
        """
        if not self._validate_string_input(overview_text, "Overview text"):
            return self._create_response(False, "Overview text cannot be empty.")
        self.document["overview"] = overview_text
        return self._create_response(True, "Overview updated successfully.")

    def add_scope_item(self, item_description: str) -> Dict[str, Any]:
        """
        Adds an item to the scope section of the backup strategy document.

        Args:
            item_description: A description of what is included in the backup scope.

        Returns:
            A dictionary with the result of the operation.
        """
        if not self._validate_string_input(item_description, "Scope item description"):
            return self._create_response(False, "Scope item description cannot be empty.")
        self.document["scope"].append(item_description)
        return self._create_response(True, f"Scope item '{item_description}' added.")

    def add_backup_type(self, type_name: str, description: str, tools: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Adds a backup type to the document.

        Args:
            type_name: The name of the backup type (e.g., "Full", "Incremental", "Differential").
            description: A description of the backup type.
            tools: A list of tools or software used for this backup type.

        Returns:
            A dictionary with the result of the operation.
        """
        if not self._validate_string_input(type_name, "Backup type name"):
            return self._create_response(False, "Backup type name cannot be empty.")
        if not self._validate_string_input(description, "Backup type description"):
            return self._create_response(False, "Backup type description cannot be empty.")
        if tools is not None and not self._validate_list_input(tools, "Tools", str):
            return self._create_response(False, "Tools must be provided as a list of strings.")

        backup_type_data = {"name": type_name, "description": description}
        if tools is not None:
            backup_type_data["tools"] = tools
        self.document["backup_types"].append(backup_type_data)
        return self._create_response(True, f"Backup type '{type_name}' added.")

    def set_retention_policy(self, policy_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sets the retention policy for backups.

        Args:
            policy_details: A dictionary detailing the retention policy.
                            Example: {"daily": "7 days", "weekly": "4 weeks", "monthly": "12 months", "yearly": "3 years"}

        Returns:
            A dictionary with the result of the operation.
        """
        if not isinstance(policy_details, dict) or not policy_details:
            return self._create_response(False, "Retention policy details must be a non-empty dictionary.")
        # Basic check for structure, can be more thorough
        if "description" not in policy_details and "example" not in policy_details and not any(k.endswith("_backups") for k in policy_details):
             print("Warning: Retention policy might be missing a description or example. Please ensure clarity.")
        self.document["retention_policy"] = policy_details
        return self._create_response(True, "Retention policy updated.")

    def set_backup_schedule(self, schedule_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sets the backup schedule for different types of backups.

        Args:
            schedule_details: A dictionary detailing the schedule.
                              Example: {"full_backup": "Sunday 02:00", "incremental_backup": "Daily 03:00"}

        Returns:
            A dictionary with the result of the operation.
        """
        if not isinstance(schedule_details, dict) or not schedule_details:
            return self._create_response(False, "Backup schedule details must be a non-empty dictionary.")
        # Basic check for structure
        if "description" not in schedule_details and "example" not in schedule_details and not any(k.endswith("_backup") for k in schedule_details):
             print("Warning: Backup schedule might be missing a description or example. Please ensure clarity.")
        self.document["backup_schedule"] = schedule_details
        return self._create_response(True, "Backup schedule updated.")

    def add_storage_location(self, location_type: str, path_or_url: str, description: Optional[str] = None) -> Dict[str, Any]:
        """
        Adds a storage location for backups.

        Args:
            location_type: The type of storage (e.g., "Local Disk", "NAS", "Cloud Storage", "External Drive").
            path_or_url: The path to the local directory, URL for cloud storage, etc.
            description: An optional description for the storage location.

        Returns:
            A dictionary with the result of the operation.
        """
        if not self._validate_string_input(location_type, "Storage location type"):
            return self._create_response(False, "Storage location type cannot be empty.")
        if not self._validate_string_input(path_or_url, "Storage location path or URL"):
            return self._create_response(False, "Storage location path or URL cannot be empty.")
        if description is not None and not isinstance(description, str):
             return self._create_response(False, "Storage location description must be a string or None.")

        storage_info = {"type": location_type, "location": path_or_url}
        if description:
            storage_info["description"] = description
        self.document["storage_locations"].append(storage_info)
        return self._create_response(True, f"Storage location '{path_or_url}' added.")

    def add_security_consideration(self, consideration: str) -> Dict[str, Any]:
        """
        Adds a security consideration to the document.

        Args:
            consideration: A description of a security measure or consideration.

        Returns:
            A dictionary with the result of the operation.
        """
        if not self._validate_string_input(consideration, "Security consideration"):
            return self._create_response(False, "Security consideration cannot be empty.")
        self.document["security_considerations"].append(consideration)
        return self._create_response(True, f"Security consideration '{consideration}' added.")

    def add_testing_procedure(self, procedure_description: str) -> Dict[str, Any]:
        """
        Adds a testing and validation procedure to the document.

        Args:
            procedure_description: A description of a testing or validation step.

        Returns:
            A dictionary with the result of the operation.
        """
        if not self._validate_string_input(procedure_description, "Testing procedure description"):
            return self._create_response(False, "Testing procedure description cannot be empty.")
        self.document["testing_and_validation"].append(procedure_description)
        return self._create_response(True, f"Testing procedure '{procedure_description}' added.")

    def set_disaster_recovery_link(self, dr_plan_link: str) -> Dict[str, Any]:
        """
        Sets a link to the disaster recovery plan document.

        Args:
            dr_plan_link: The URL or path to the disaster recovery plan.

        Returns:
            A dictionary with the result of the operation.
        """
        if not self._validate_string_input(dr_plan_link, "Disaster recovery plan link"):
            return self._create_response(False, "Disaster recovery plan link cannot be empty.")
        self.document["disaster_recovery_plan_link"] = dr_plan_link
        return self._create_response(True, "Disaster recovery plan link set.")

    def add_procedure_step(self, step_title: str, step_description: str, os_compatibility: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Adds a step-by-step procedure to the document.

        Args:
            step_title: The title or summary of the procedure step.
            step_description: A detailed description of how to perform the step.
            os_compatibility: A list of operating systems this step is compatible with (e.g., ["macOS", "Linux", "Windows"]).

        Returns:
            A dictionary with the result of the operation.
        """
        if not self._validate_string_input(step_title, "Procedure step title"):
            return self._create_response(False, "Procedure step title cannot be empty.")
        if not self._validate_string_input(step_description, "Procedure step description"):
            return self._create_response(False, "Procedure step description cannot be empty.")
        if os_compatibility is not None and not self._validate_list_input(os_compatibility, "OS compatibility", str):
            return self._create_response(False, "OS compatibility must be provided as a list of strings.")

        procedure_data = {"title": step_title, "description": step_description}
        if os_compatibility:
            procedure_data["os_compatibility"] = os_compatibility
        self.document["procedures"].append(procedure_data)
        return self._create_response(True, f"Procedure step '{step_title}' added.")

    def add_best_practice(self, practice_description: str) -> Dict[str, Any]:
        """
        Adds a best practice to the document.

        Args:
            practice_description: A description of a recommended best practice.

        Returns:
            A dictionary with the result of the operation.
        """
        if not self._validate_string_input(practice_description, "Best practice description"):
            return self._create_response(False, "Best practice description cannot be empty.")
        self.document["best_practices"].append(practice_description)
        return self._create_response(True, f"Best practice '{practice_description}' added.")

    def _update_version_history(self):
        """Adds a new entry to the version history."""
        now = datetime.now()
        latest_version_str = "0.0"
        if self.document["version_history"]:
            latest_version_str = self.document["version_history"][-1]["version"]
            try:
                major, minor = map(int, latest_version_str.split('.'))
                minor += 1
                latest_version_str = f"{major}.{minor}"
            except ValueError:
                latest_version_str = "1.0" # Fallback if version format is unexpected

        self.document["version_history"].append({
            "version": latest_version_str,
            "date": now.strftime("%Y-%m-%d %H:%M:%S"),
            "description": "Document updated."
        })

    def generate_document(self) -> Dict[str, Any]:
        """
        Generates the complete backup strategy document as a dictionary.
        Performs basic content validation before returning.

        Returns:
            A dictionary representing the complete backup strategy document.
        """
        # Basic validation to ensure essential sections have some content
        if not self.document.get("overview") or self.document["overview"] == "A default overview if none was provided. This document outlines a comprehensive backup strategy to ensure data resilience against various threats.":
            print("Warning: Overview section is empty or using default text. Please provide a detailed overview.")
        if not self.document.get("scope") or self.document["scope"] == ["Default: All critical data and system configurations."]:
            print("Warning: Scope section is empty or using default text. Please define what data is included in the backup scope.")
        if not self.document.get("backup_types") or len(self.document["backup_types"]) == 3 and all(t["name"] in ["Full Backup", "Incremental Backup", "Differential Backup"] for t in self.document["backup_types"]):
             print("Warning: Backup types section is empty or using default types. Please specify relevant backup types.")
        if not self.document.get("retention_policy") or "example" in self.document["retention_policy"]:
            print("Warning: Retention policy is empty or uses default example. Please define your specific retention rules.")
        if not self.document.get("backup_schedule") or "example" in self.document["backup_schedule"]:
            print("Warning: Backup schedule is empty or uses default example. Please define your specific backup schedule.")
        if not self.document.get("storage_locations") or "Default local storage location." in self.document["storage_locations"][0].get("description",""):
            print("Warning: Storage locations section is empty or using default. Please define your backup storage destinations.")
        if not self.document.get("procedures") or len(self.document["procedures"]) == 1 and self.document["procedures"][0]["title"] == "Initial Backup Configuration":
             print("Warning: Procedures section is empty or using default. Please add specific step-by-step procedures.")
        if not self.document.get("best_practices") or len(self.document["best_practices"]) == 7 and all(bp.startswith("Follow the 3-2-1 backup rule") for bp in self.document["best_practices"]):
             print("Warning: Best practices section is empty or using defaults. Please add relevant best practices.")


        self._update_version_history() # Ensure version history is updated on generation
        return self._create_response(True, "Backup strategy document generated successfully.", data={"document": self.document})

    def save_document_to_json(self, filepath: str) -> Dict[str, Any]:
        """
        Saves the generated backup strategy document to a JSON file.

        Args:
            filepath: The path where the JSON file should be saved.

        Returns:
            A dictionary with the result of the operation.
        """
        if not self._validate_string_input(filepath, "Filepath"):
            return self._create_response(False, "Filepath cannot be empty.")

        if not filepath.lower().endswith(".json"):
            filepath += ".json"

        generation_result = self.generate_document()
        if not generation_result["success"]:
            return self._create_response(False, f"Failed to generate document before saving: {generation_result['message']}")

        document_data = generation_result["document"]

        try:
            # Ensure the directory exists before writing the file
            dir_path = os.path.dirname(filepath)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True) # Use exist_ok=True to avoid error if dir already exists

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(document_data, f, indent=4)
            return self._create_response(True, f"Backup strategy document saved to '{filepath}'.")
        except IOError as e:
            return self._create_response(False, f"Error writing to file '{filepath}': {e}")
        except Exception as e:
            return self._create_response(False, f"An unexpected error occurred while saving: {e}")

    def load_document_from_json(self, filepath: str) -> Dict[str, Any]:
        """
        Loads a backup strategy document from a JSON file.
        This will overwrite the current document being built.

        Args:
            filepath: The path to the JSON file to load.

        Returns:
            A dictionary with the result of the operation.
        """
        if not self._validate_string_input(filepath, "Filepath"):
            return self._create_response(False, "Filepath cannot be empty.")
        if not os.path.exists(filepath):
            return self._create_response(False, f"File not found at '{filepath}'.")
        if not filepath.lower().endswith(".json"):
            return self._create_response(False, "Invalid file format. Please provide a JSON file.")

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)

            # Basic validation of loaded structure
            if not isinstance(loaded_data, dict):
                return self._create_response(False, "Invalid document structure: root element is not a dictionary.")
            # Check for essential keys
            required_keys = ["title", "overview", "scope", "backup_types", "retention_policy", "backup_schedule", "storage_locations", "security_considerations", "testing_and_validation", "procedures", "best_practices", "version_history"]
            for key in required_keys:
                if key not in loaded_data:
                    return self._create_response(False, f"Invalid document structure: missing required key '{key}'.")

            self.document = loaded_data
            self.strategy_name = self.document.get("title", "Loaded Backup Strategy").replace("Comprehensive Backup Strategy: ", "")
            return self._create_response(True, f"Backup strategy document loaded from '{filepath}'.")
        except json.JSONDecodeError as e:
            return self._create_response(False, f"Error decoding JSON from '{filepath}': {e}")
        except IOError as e:
            return self._create_response(False, f"Error reading file '{filepath}': {e}")
        except Exception as e:
            return self._create_response(False, f"An unexpected error occurred while loading: {e}")

# Example of how to use the class (this part is for demonstration and not part of the class itself)
if __name__ == "__main__":
    print("--- Initializing Backup Strategy Generator ---")
    try:
        generator = BackupStrategyGenerator(strategy_name="My Personal Data Backup")
    except ValueError as e:
        print(f"Initialization Error: {e}")
        exit()

    # Setting Overview
    print("\n--- Setting Overview ---")
    overview_text = (
        "This document outlines a comprehensive backup strategy for personal data stored on my macOS system. "
        "The goal is to ensure data resilience against hardware failure, accidental deletion, and malware attacks. "
        "It covers data types, backup methods, storage, security, and recovery procedures."
    )
    response = generator.set_overview(overview_text)
    print(json.dumps(response, indent=4))

    # Adding Scope Items
    print("\n--- Adding Scope Items ---")
    scope_items = [
        "Documents folder (~/Documents)",
        "Photos library (~/Pictures)",
        "Desktop items (~/Desktop)",
        "Application settings and configurations (specific paths like ~/.config, ~/Library/Preferences)",
        "Source code repositories",
        "Downloads folder (~/Downloads) - with caution, may contain temporary files",
        "System configuration files (e.g., /etc, ~/.ssh)"
    ]
    for item in scope_items:
        response = generator.add_scope_item(item)
        print(json.dumps(response, indent=4))

    # Adding Backup Types
    print("\n--- Adding Backup Types ---")
    generator.add_backup_type("Full Backup", "A complete copy of all selected data. Performed less frequently, usually monthly or quarterly.", ["Time Machine", "rsync", "Carbon Copy Cloner"])
    generator.add_backup_type("Incremental Backup", "Backs up only the data that has changed since the last backup (full or incremental). Performed daily or multiple times a day.", ["Time Machine", "rsync", "Arq Backup"])
    generator.add_backup_type("Local Snapshot", "Point-in-time snapshots of the local filesystem. Useful for quick recovery from accidental changes.", ["Time Machine", "APFS Snapshots"])
    generator.add_backup_type("Cloud Backup", "Offsite copy of data, usually incremental or differential, managed by a cloud provider.", ["Backblaze", "iDrive", "Arq Backup"])


    # Setting Retention Policy
    print("\n--- Setting Retention Policy ---")
    retention_policy = {
        "description": "This policy defines how long different backup versions are retained to balance storage costs with recovery needs.",
        "hourly_snapshots": "Keep last 24 hours",
        "daily_backups": "Keep for 14 days",
        "weekly_backups": "Keep for 8 weeks",
        "monthly_backups": "Keep for 12 months",
        "yearly_backups": "Keep for 5 years",
        "note": "Sensitive data may require longer retention periods or immutable storage."
    }
    response = generator.set_retention_policy(retention_policy)
    print(json.dumps(response, indent=4))

    # Setting Backup Schedule
    print("\n--- Setting Backup Schedule ---")
    backup_schedule = {
        "description": "The following schedule ensures regular backups are performed without impacting system performance.",
        "full_backup": "First Sunday of the month at 03:00 AM",
        "daily_incremental_backup": "Every day at 01:00 AM and 06:00 PM",
        "local_snapshot_retention": "Hourly snapshots for the last 24 hours",
        "cloud_backup_sync": "Daily, initiated after local backups complete",
        "verification_check": "Weekly, automated check"
    }
    response = generator.set_backup_schedule(backup_schedule)
    print(json.dumps(response, indent=4))

    # Adding Storage Locations
    print("\n--- Adding Storage Locations ---")
    generator.add_storage_location("External HDD", "/Volumes/MyBackupDrive/MacBackup", "Primary local backup destination. Encrypted with APFS.")
    generator.add_storage_location("Cloud Storage (Backblaze B2)", "b2://my-mac-backups/", "Offsite backup for disaster recovery. Data is encrypted client-side.")
    generator.add_storage_location("Network Attached Storage (NAS)", "smb://192.168.1.100/backups/mac_pro", "Secondary local backup destination. Accessed via SMB, backups are encrypted.")

    # Adding Security Considerations
    print("\n--- Adding Security Considerations ---")
    generator.add_security_consideration("Encrypt all backups stored on external media and cloud using AES-256 encryption.")
    generator.add_security_consideration("Use strong, unique passwords for cloud storage accounts and NAS access. Implement Multi-Factor Authentication (MFA) where available.")
    generator.add_security_consideration("Limit administrative access to backup systems and storage. Employ the principle of least privilege.")
    generator.add_security_consideration("Regularly scan backups for malware using dedicated tools or features within backup software. Consider immutability for critical backups.")
    generator.add_security_consideration("Store sensitive backup credentials securely (e.g., in a password manager).")

    # Adding Testing Procedures
    print("\n--- Adding Testing Procedures ---")
    generator.add_testing_procedure("Perform a test restore of a single file weekly to verify basic functionality.")
    generator.add_testing_procedure("Perform a test restore of a folder or application quarterly to ensure data integrity.")
    generator.add_testing_procedure("Conduct a full system recovery test on a virtual machine or spare hardware annually to validate the entire restore process.")
    generator.add_testing_procedure("Verify backup integrity by checking checksums or using built-in verification tools after each backup cycle.")

    # Setting Disaster Recovery Link
    print("\n--- Setting Disaster Recovery Link ---")
    response = generator.set_disaster_recovery_link("https://docs.example.com/my-disaster-recovery-plan")
    print(json.dumps(response, indent=4))

    # Adding Procedure Steps (macOS focused example)
    print("\n--- Adding Procedure Steps ---")
    generator.add_procedure_step(
        step_title="Configure Time Machine for Local Backups",
        step_description="1. Connect your external backup drive (e.g., SSD or HDD).\n2. Go to System Settings > General > Time Machine.\n3. Click 'Add Backup Disk' and select your external drive.\n4. Ensure 'Back Up Automatically' is enabled.\n5. Optionally, enable 'Encrypt Backups' for added security.",
        os_compatibility=["macOS"]
    )
    generator.add_procedure_step(
        step_title="Set up rsync for specific directories to NAS",
        step_description="1. Open Terminal.\n2. Create a backup script (e.g., `~/scripts/backup_to_nas.sh`) using rsync. Example command:\n   `rsync -avz --delete /Users/youruser/Documents/ /Volumes/MyBackupDrive/MacBackup/Documents/`\n   Ensure correct source and destination paths.\n3. Make the script executable: `chmod +x ~/scripts/backup_to_nas.sh`\n4. Schedule the script using `launchd` for macOS. Create a `.plist` file in `~/Library/LaunchAgents/`.",
        os_compatibility=["macOS", "Linux"]
    )
    generator.add_procedure_step(
        step_title="Configure Cloud Backup Agent (Backblaze Example)",
        step_description="1. Download and install the Backblaze client from their website.\n2. Log in with your Backblaze account credentials.\n3. Select the folders/files to back up from the 'My Computer' settings.\n4. Configure encryption settings (client-side encryption is recommended for sensitive data).\n5. Set bandwidth throttles if necessary.\n6. Allow the initial full backup to complete.",
        os_compatibility=["macOS", "Windows"]
    )
    generator.add_procedure_step(
        step_title="Test a File Restore from Time Machine",
        step_description="1. Open Finder and navigate to a folder where a file was backed up.\n2. Enter Time Machine by clicking the Time Machine icon in the menu bar and selecting 'Enter Time Machine'.\n3. Use the arrows and timeline to go back to a previous version of the folder.\n4. Select the file you wish to restore and click 'Restore'.",
        os_compatibility=["macOS"]
    )

    # Adding Best Practices
    print("\n--- Adding Best Practices ---")
    generator.add_best_practice("Follow the 3-2-1 backup rule: 3 copies of your data, on 2 different media types, with 1 copy offsite.")
    generator.add_best_practice("Automate your backups to ensure consistency and reduce human error. Schedule them during off-peak hours.")
    generator.add_best_practice("Never store your only copy of data on a single device. Redundancy is key.")
    generator.add_best_practice("Keep backup media physically secure and protected from environmental hazards (fire, flood, extreme temperatures).")
    generator.add_best_practice("Regularly review and update your backup strategy as your data, systems, and threats evolve.")
    generator.add_best_practice("Ensure sufficient free space on all backup destinations to accommodate growth and retention policies.")
    generator.add_best_practice("Use encryption for all backups, especially those stored offsite or on portable media.")
    generator.add_best_practice("Document your backup procedures and recovery steps thoroughly. Test them periodically.")

    # Generate and print the document
    print("\n--- Generating Document ---")
    generation_result = generator.generate_document()
    if generation_result["success"]:
        print("Document generated successfully. Displaying content:")
        print(json.dumps(generation_result["document"], indent=4))
        print("\n--- Document Generation Complete ---")
    else:
        print(f"Error generating document: {generation_result['message']}")

    # Save the document to a JSON file
    print("\n--- Saving Document to JSON ---")
    save_filepath = "my_comprehensive_backup_strategy.json"
    save_result = generator.save_document_to_json(save_filepath)
    print(json.dumps(save_result, indent=4))

    # Example of loading a document
    print("\n--- Loading Document from JSON ---")
    new_generator = BackupStrategyGenerator(strategy_name="Initial State")
    load_result = new_generator.load_document_from_json(save_filepath)
    print(json.dumps(load_result, indent=4))
    if load_result["success"]:
        print(f"\n--- Document '{save_filepath}' Loaded Successfully. Current Document State: ---")
        print(json.dumps(new_generator.document, indent=4))
    else:
        print(f"Error loading document: {load_result['message']}")

    # Example of saving to a non-existent directory
    print("\n--- Saving Document to a New Directory ---")
    new_dir_filepath = "backups/my_strategy.json"
    save_result_new_dir = generator.save_document_to_json(new_dir_filepath)
    print(json.dumps(save_result_new_dir, indent=4))

    # Example of error handling for invalid input
    print("\n--- Testing Invalid Inputs ---")
    print("Attempting to set overview with empty string:")
    invalid_response = generator.set_overview("")
    print(json.dumps(invalid_response, indent=4))

    print("\nAttempting to add scope item with non-string:")
    invalid_response = generator.add_scope_item(123)
    print(json.dumps(invalid_response, indent=4))

    print("\nAttempting to add backup type with invalid tools list:")
    invalid_response = generator.add_backup_type("Test", "Test Desc", ["tool1", 123])
    print(json.dumps(invalid_response, indent=4))

    print("\nAttempting to load non-existent file:")
    invalid_response = generator.load_document_from_json("non_existent_file.json")
    print(json.dumps(invalid_response, indent=4))
