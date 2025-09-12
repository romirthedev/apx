
import subprocess
import json
import os
import shutil
from typing import Dict, Any, Optional, List, Union

class ComplexActionTool:
    """
    A specialized tool class for performing complex multi-step actions with parameters.

    This tool orchestrates a series of operations, including file manipulation,
    script execution, and data processing, designed to be flexible and extensible.
    It prioritizes safety and returns structured results for easy integration.

    The primary method `perform_complex_action` allows users to execute a script
    with specific input data, arguments, and manage its output and logs.
    """

    def __init__(self, base_dir: str = "."):
        """
        Initializes the ComplexActionTool.

        Args:
            base_dir: The base directory for operations. Defaults to the current directory.
                      All file paths will be relative to this directory.

        Raises:
            ValueError: If the base_dir does not exist or is not a directory.
        """
        if not os.path.isdir(base_dir):
            raise ValueError(f"Base directory '{base_dir}' does not exist or is not a directory.")
        self.base_dir = os.path.abspath(base_dir)
        print(f"ComplexActionTool initialized with base directory: {self.base_dir}")

    def _run_command(self, command: List[str], check: bool = True, capture_output: bool = True, text: bool = True, shell: bool = False, cwd: Optional[str] = None) -> Dict[str, Any]:
        """
        Safely executes a shell command.

        Args:
            command: A list of strings representing the command and its arguments.
            check: If True, raise a CalledProcessError if the command returns a non-zero exit code.
            capture_output: If True, capture stdout and stderr.
            text: If True, decode stdout and stderr as text.
            shell: If True, execute command through the shell. Use with caution.
            cwd: The working directory to execute the command in. Defaults to self.base_dir.

        Returns:
            A dictionary containing 'returncode', 'stdout', and 'stderr'.
            Raises CalledProcessError on failure if check is True.
        """
        effective_cwd = os.path.join(self.base_dir, cwd) if cwd else self.base_dir
        if not os.path.isdir(effective_cwd):
            return {
                "returncode": 1,
                "stdout": "",
                "stderr": f"Working directory '{effective_cwd}' does not exist.",
            }

        try:
            result = subprocess.run(
                command,
                check=check,
                capture_output=capture_output,
                text=text,
                shell=shell,
                cwd=effective_cwd
            )
            return {
                "returncode": result.returncode,
                "stdout": result.stdout if result.stdout is not None else "",
                "stderr": result.stderr if result.stderr is not None else "",
            }
        except FileNotFoundError:
            return {
                "returncode": 1,
                "stdout": "",
                "stderr": f"Command not found: {command[0]} in directory {effective_cwd}",
            }
        except subprocess.CalledProcessError as e:
            return {
                "returncode": e.returncode,
                "stdout": e.stdout if e.stdout is not None else "",
                "stderr": e.stderr if e.stderr is not None else "",
            }
        except Exception as e:
            return {
                "returncode": 1,
                "stdout": "",
                "stderr": f"An unexpected error occurred while running command in '{effective_cwd}': {e}",
            }

    def _create_file(self, filename: str, content: str = "", overwrite: bool = False, sub_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Creates a file within the base directory or a subdirectory.

        Args:
            filename: The name of the file to create.
            content: The content to write to the file.
            overwrite: If True, overwrite the file if it already exists.
            sub_dir: An optional subdirectory within base_dir to create the file in.

        Returns:
            A dictionary with 'success' (bool) and 'message' (str).
        """
        if sub_dir:
            target_dir = os.path.join(self.base_dir, sub_dir)
            if not os.path.isdir(target_dir):
                try:
                    os.makedirs(target_dir, exist_ok=True)
                except OSError as e:
                    return {"success": False, "message": f"Failed to create subdirectory '{sub_dir}': {e}"}
            filepath = os.path.join(target_dir, filename)
        else:
            filepath = os.path.join(self.base_dir, filename)

        if os.path.exists(filepath) and not overwrite:
            return {"success": False, "message": f"File '{os.path.relpath(filepath, self.base_dir)}' already exists. Set overwrite=True to replace."}

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return {"success": True, "message": f"File '{os.path.relpath(filepath, self.base_dir)}' created successfully."}
        except IOError as e:
            return {"success": False, "message": f"Failed to create file '{os.path.relpath(filepath, self.base_dir)}': {e}"}
        except Exception as e:
            return {"success": False, "message": f"An unexpected error occurred while creating file '{os.path.relpath(filepath, self.base_dir)}': {e}"}

    def _read_file(self, filename: str, sub_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Reads the content of a file from the base directory or a subdirectory.

        Args:
            filename: The name of the file to read.
            sub_dir: An optional subdirectory within base_dir where the file is located.

        Returns:
            A dictionary with 'success' (bool), 'message' (str), and 'content' (str) if successful.
        """
        if sub_dir:
            filepath = os.path.join(self.base_dir, sub_dir, filename)
        else:
            filepath = os.path.join(self.base_dir, filename)

        if not os.path.exists(filepath):
            return {"success": False, "message": f"File '{os.path.relpath(filepath, self.base_dir)}' not found."}
        if not os.path.isfile(filepath):
            return {"success": False, "message": f"'{os.path.relpath(filepath, self.base_dir)}' is not a file."}

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            return {"success": True, "message": f"File '{os.path.relpath(filepath, self.base_dir)}' read successfully.", "content": content}
        except IOError as e:
            return {"success": False, "message": f"Failed to read file '{os.path.relpath(filepath, self.base_dir)}': {e}"}
        except Exception as e:
            return {"success": False, "message": f"An unexpected error occurred while reading file '{os.path.relpath(filepath, self.base_dir)}': {e}"}

    def _delete_file_safely(self, filename: str, sub_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Safely deletes a file from the base directory or a subdirectory.

        Args:
            filename: The name of the file to delete.
            sub_dir: An optional subdirectory within base_dir from which to delete the file.

        Returns:
            A dictionary with 'success' (bool), 'message' (str), and 'deleted' (bool).
        """
        if sub_dir:
            filepath = os.path.join(self.base_dir, sub_dir, filename)
        else:
            filepath = os.path.join(self.base_dir, filename)

        if not os.path.exists(filepath):
            return {"success": False, "message": f"File '{os.path.relpath(filepath, self.base_dir)}' does not exist.", "deleted": False}

        if not os.path.isfile(filepath):
            return {"success": False, "message": f"'{os.path.relpath(filepath, self.base_dir)}' is not a file.", "deleted": False}

        try:
            os.remove(filepath)
            return {"success": True, "message": f"File '{os.path.relpath(filepath, self.base_dir)}' deleted successfully.", "deleted": True}
        except OSError as e:
            return {"success": False, "message": f"Failed to delete file '{os.path.relpath(filepath, self.base_dir)}': {e}", "deleted": False}
        except Exception as e:
            return {"success": False, "message": f"An unexpected error occurred while deleting file '{os.path.relpath(filepath, self.base_dir)}': {e}", "deleted": False}

    def _ensure_script_executable(self, script_path: str) -> Dict[str, Any]:
        """
        Ensures a script file has execute permissions.

        Args:
            script_path: The absolute path to the script.

        Returns:
            A dictionary with 'success' (bool) and 'message' (str).
        """
        if not os.path.exists(script_path):
            return {"success": False, "message": f"Script '{os.path.basename(script_path)}' not found at '{script_path}'."}
        if not os.path.isfile(script_path):
            return {"success": False, "message": f"'{os.path.basename(script_path)}' is not a file."}

        if not os.access(script_path, os.X_OK):
            try:
                os.chmod(script_path, 0o755)
                return {"success": True, "message": f"Set execute permissions for '{os.path.basename(script_path)}'."}
            except Exception as e:
                return {"success": False, "message": f"Could not set execute permissions for '{os.path.basename(script_path)}': {e}"}
        return {"success": True, "message": f"Script '{os.path.basename(script_path)}' already has execute permissions."}

    def perform_complex_action(
        self,
        input_data: Dict[str, Any],
        script_path: str,
        script_args: Optional[List[str]] = None,
        input_filename: str = "temp_input.json",
        output_filename: str = "output.json",
        log_filename: str = "action.log",
        script_cwd: Optional[str] = None,
        input_sub_dir: Optional[str] = None,
        output_sub_dir: Optional[str] = None,
        log_sub_dir: Optional[str] = None,
        cleanup_input: bool = True,
        cleanup_output: bool = False
    ) -> Dict[str, Any]:
        """
        Performs a complex multi-step action by executing a script.

        This method orchestrates the following steps:
        1. Creates an input file with the provided JSON data.
        2. Ensures the script has execute permissions.
        3. Executes the specified script with given arguments, passing the input file.
        4. Captures and logs the script's stdout and stderr.
        5. Optionally saves script's stdout to an output file.
        6. Optionally cleans up input and output files.
        7. Returns structured data about the action's success.

        Args:
            input_data: A dictionary containing the data to be used as input for the script.
            script_path: The relative path to the executable script from the base_dir.
                         (e.g., 'scripts/process_data.sh').
            script_args: An optional list of additional arguments to pass to the script.
            input_filename: The filename for the temporary input JSON file.
            output_filename: The filename to save the script's JSON output to.
            log_filename: The filename to log script execution messages (stderr) to.
            script_cwd: The working directory for the script execution, relative to base_dir.
            input_sub_dir: Subdirectory within base_dir for the input file.
            output_sub_dir: Subdirectory within base_dir for the output file.
            log_sub_dir: Subdirectory within base_dir for the log file.
            cleanup_input: If True, the temporary input file will be deleted after execution.
            cleanup_output: If True, the output file will be deleted after execution.

        Returns:
            A dictionary with 'success' (bool), 'message' (str), 'output_data' (dict or None),
            'output_file' (str or None), and 'log_file' (str or None).
        """
        if script_args is None:
            script_args = []

        # --- Step 1: Create input file ---
        create_input_result = self._create_file(input_filename, json.dumps(input_data, indent=2), sub_dir=input_sub_dir)
        if not create_input_result["success"]:
            return {"success": False, "message": f"Failed to create input file: {create_input_result['message']}", "output_data": None, "output_file": None, "log_file": None}
        
        temp_input_filepath_rel = os.path.join(input_sub_dir, input_filename) if input_sub_dir else input_filename

        # --- Step 2: Ensure script is executable ---
        full_script_path = os.path.join(self.base_dir, script_path)
        exec_permission_result = self._ensure_script_executable(full_script_path)
        if not exec_permission_result["success"]:
            # Log the error but try to proceed, as some scripts might not need explicit chmod
            print(f"Warning: {exec_permission_result['message']}")

        # --- Step 3: Construct and execute the command ---
        command = [full_script_path] + script_args + [temp_input_filepath_rel]
        print(f"Executing command: {' '.join(command)} in cwd: {os.path.join(self.base_dir, script_cwd) if script_cwd else self.base_dir}")

        command_execution_result = self._run_command(command, check=False, cwd=script_cwd)

        # --- Step 4: Log stderr to a file ---
        log_filepath_rel = log_filename
        if command_execution_result["stderr"]:
            log_creation_result = self._create_file(log_filename, command_execution_result["stderr"], overwrite=True, sub_dir=log_sub_dir)
            if not log_creation_result["success"]:
                print(f"Warning: Failed to write to log file '{log_filename}': {log_creation_result['message']}")
            else:
                log_filepath_rel = os.path.join(log_sub_dir, log_filename) if log_sub_dir else log_filename
        else:
            # Ensure log file is created even if no stderr, for consistency
            self._create_file(log_filename, content="", overwrite=True, sub_dir=log_sub_dir)
            log_filepath_rel = os.path.join(log_sub_dir, log_filename) if log_sub_dir else log_filename

        # --- Step 5: Check if the command executed successfully ---
        if command_execution_result["returncode"] != 0:
            return {
                "success": False,
                "message": f"Script execution failed. Return code: {command_execution_result['returncode']}. Check '{os.path.relpath(os.path.join(self.base_dir, log_filepath_rel), self.base_dir)}' for details.",
                "output_data": None,
                "output_file": None,
                "log_file": os.path.relpath(os.path.join(self.base_dir, log_filepath_rel), self.base_dir) if command_execution_result["stderr"] else None
            }

        # --- Step 6: Parse stdout as JSON ---
        script_output_data = None
        try:
            script_output_data = json.loads(command_execution_result["stdout"])
        except json.JSONDecodeError:
            # Log the malformed output as an error, but don't necessarily fail the whole operation
            # if we can still save it as raw text or if it's expected to be non-JSON.
            # For this tool's primary purpose, we expect JSON output.
            error_message = "Script stdout is not valid JSON. Check script logic and logging."
            print(f"Warning: {error_message}")
            self._create_file(log_filename, f"JSON Decode Error: {error_message}\n--- STDOUT ---\n{command_execution_result['stdout']}", overwrite=True, sub_dir=log_sub_dir)
            return {
                "success": False,
                "message": error_message,
                "output_data": None,
                "output_file": None,
                "log_file": os.path.relpath(os.path.join(self.base_dir, log_filepath_rel), self.base_dir) if command_execution_result["stderr"] else None
            }

        # --- Step 7: Save output to file ---
        output_filepath_rel = output_filename
        save_output_result = self._create_file(output_filename, json.dumps(script_output_data, indent=2), overwrite=True, sub_dir=output_sub_dir)
        if not save_output_result["success"]:
            print(f"Warning: Failed to save output to '{output_filename}': {save_output_result['message']}")
            # We can still return the parsed data if saving failed
            output_filepath_rel = None # Indicate that saving failed
        else:
            output_filepath_rel = os.path.join(output_sub_dir, output_filename) if output_sub_dir else output_filename

        # --- Step 8: Cleanup ---
        if cleanup_input:
            self._delete_file_safely(input_filename, sub_dir=input_sub_dir)
            
        if cleanup_output and output_filepath_rel:
            self._delete_file_safely(output_filename, sub_dir=output_sub_dir)

        return {
            "success": True,
            "message": f"Complex action completed successfully. Output processed and saved to '{os.path.relpath(os.path.join(self.base_dir, output_filepath_rel), self.base_dir)}' if saving was successful.",
            "output_data": script_output_data,
            "output_file": os.path.relpath(os.path.join(self.base_dir, output_filepath_rel), self.base_dir) if output_filepath_rel else None,
            "log_file": os.path.relpath(os.path.join(self.base_dir, log_filepath_rel), self.base_dir) if command_execution_result["stderr"] else None
        }

    def get_file_content(self, filename: str, sub_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Reads and returns the content of a specified file.

        Args:
            filename: The name of the file to read.
            sub_dir: An optional subdirectory within base_dir where the file is located.

        Returns:
            A dictionary with 'success' (bool), 'message' (str), and 'content' (str or None).
        """
        return self._read_file(filename, sub_dir=sub_dir)

    def create_configuration_file(self, filename: str, config_data: Dict[str, Any], overwrite: bool = False, sub_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Creates a configuration file in JSON format.

        Args:
            filename: The name of the configuration file.
            config_data: A dictionary containing the configuration data.
            overwrite: If True, overwrite the file if it already exists.
            sub_dir: An optional subdirectory within base_dir to create the file in.

        Returns:
            A dictionary with 'success' (bool) and 'message' (str).
        """
        if not isinstance(config_data, dict):
            return {"success": False, "message": "config_data must be a dictionary."}
        try:
            config_content = json.dumps(config_data, indent=4)
            return self._create_file(filename, config_content, overwrite, sub_dir=sub_dir)
        except TypeError as e:
            return {"success": False, "message": f"Failed to serialize config_data to JSON: {e}"}

    def cleanup_files(self, filenames: Union[str, List[str]], sub_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Deletes a list of files from the base directory or a subdirectory.

        Args:
            filenames: A single filename or a list of filenames to delete.
            sub_dir: An optional subdirectory within base_dir from which to delete files.

        Returns:
            A dictionary with 'success' (bool), 'message' (str), and 'details' (list of dicts).
        """
        if isinstance(filenames, str):
            filenames = [filenames]

        results = []
        all_successful = True
        for filename in filenames:
            delete_result = self._delete_file_safely(filename, sub_dir=sub_dir)
            results.append({"filename": filename, "result": delete_result})
            if not delete_result["success"]:
                all_successful = False

        summary_message = "Cleanup completed."
        if not all_successful:
            summary_message += " Some files could not be deleted."

        return {
            "success": all_successful,
            "message": summary_message,
            "details": results
        }

    def cleanup_directory(self, directory_to_cleanup: str) -> Dict[str, Any]:
        """
        Recursively removes a directory within the base directory.

        Args:
            directory_to_cleanup: The name of the directory to remove, relative to base_dir.

        Returns:
            A dictionary with 'success' (bool) and 'message' (str).
        """
        full_path = os.path.join(self.base_dir, directory_to_cleanup)
        if not os.path.exists(full_path):
            return {"success": False, "message": f"Directory '{directory_to_cleanup}' does not exist."}
        if not os.path.isdir(full_path):
            return {"success": False, "message": f"'{directory_to_cleanup}' is not a directory."}

        try:
            shutil.rmtree(full_path)
            return {"success": True, "message": f"Directory '{directory_to_cleanup}' and its contents removed successfully."}
        except OSError as e:
            return {"success": False, "message": f"Failed to remove directory '{directory_to_cleanup}': {e}"}
        except Exception as e:
            return {"success": False, "message": f"An unexpected error occurred while removing directory '{directory_to_cleanup}': {e}"}

if __name__ == '__main__':
    # Example Usage (requires a dummy script for testing)

    # --- Setup Test Environment ---
    test_dir_name = "temp_tool_test_env"
    scripts_subdir_name = "scripts"
    outputs_subdir_name = "outputs"
    logs_subdir_name = "logs"

    # Clean up previous test run if it exists
    if os.path.exists(test_dir_name):
        print(f"Removing existing test directory: {test_dir_name}")
        try:
            shutil.rmtree(test_dir_name)
        except OSError as e:
            print(f"Error removing existing test directory '{test_dir_name}': {e}")

    try:
        os.makedirs(test_dir_name, exist_ok=True)
        print(f"Created test directory: {test_dir_name}")
    except OSError as e:
        print(f"Error creating test directory '{test_dir_name}': {e}")
        exit(1)

    # Create script and output directories within the test environment
    os.makedirs(os.path.join(test_dir_name, scripts_subdir_name), exist_ok=True)
    os.makedirs(os.path.join(test_dir_name, outputs_subdir_name), exist_ok=True)
    os.makedirs(os.path.join(test_dir_name, logs_subdir_name), exist_ok=True)


    # Dummy script content
    dummy_script_content = """#!/bin/bash
    # This is a dummy script for ComplexActionTool testing.
    # It expects one argument: the path to an input JSON file.
    # It reads the JSON, processes it minimally, and prints a JSON output to stdout.

    INPUT_FILE=$1
    VERBOSE="false"
    MODE="normal"

    # Parse optional arguments (e.g., --verbose, --mode=batch)
    while [[ "$#" -gt 0 ]]; do
        case $1 in
            --verbose) VERBOSE="true"; shift ;;
            --mode=*) MODE="${1#*=}"; shift ;;
            -*) echo "Unknown option: $1" >&2; exit 1 ;;
            *) break ;; # Assume this is the input file
        esac
    done

    INPUT_FILE=$1 # The last remaining argument is the input file

    if [ -z "$INPUT_FILE" ]; then
        echo "Error: Input file not provided." >&2
        exit 1
    fi

    if [ ! -f "$INPUT_FILE" ]; then
        echo "Error: Input file '$INPUT_FILE' not found." >&2
        exit 1
    fi

    # Use jq for robust JSON parsing/manipulation
    if ! jq -e . "$INPUT_FILE" > /dev/null 2>&1; then
        echo "Error: Input file '$INPUT_FILE' is not valid JSON." >&2
        exit 1
    fi

    if [ "$VERBOSE" = "true" ]; then
        echo "Processing started with mode: $MODE" >&2
    fi

    # Example: Add a processing status and timestamp to the input data
    NEW_DATA=$(jq --argjson input_data "$(cat "$INPUT_FILE")" \
                --arg status "processed" \
                --arg mode "$MODE" \
                --arg timestamp "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
                '. + {processing_status: $status, mode_used: $mode, timestamp: $timestamp}' "$INPUT_FILE")

    if [ "$VERBOSE" = "true" ]; then
        echo "Processing complete." >&2
    fi

    echo "$NEW_DATA"
    exit 0
    """

    script_filename = "process_data.sh"
    script_path_relative_to_base = os.path.join(scripts_subdir_name, script_filename)
    script_full_path = os.path.join(test_dir_name, script_path_relative_to_base)

    try:
        with open(script_full_path, "w") as f:
            f.write(dummy_script_content)
        os.chmod(script_full_path, 0o755) # Make it executable
        print(f"Created dummy script at: {script_full_path}")
    except Exception as e:
        print(f"Error creating dummy script: {e}")
        exit(1)

    # Initialize the tool with the temporary directory
    tool = ComplexActionTool(base_dir=test_dir_name)

    # --- Test Case 1: Basic Complex Action ---
    print("\n--- Test Case 1: Performing Basic Complex Action ---")
    sample_input_data = {
        "user_id": "12345",
        "task_name": "data_ingestion",
        "parameters": {
            "source": "api",
            "destination": "database"
        }
    }
    sample_script_args = ["--verbose", "--mode=batch"]

    action_result = tool.perform_complex_action(
        input_data=sample_input_data,
        script_path=script_path_relative_to_base,
        script_args=sample_script_args,
        input_filename="sample_input.json",
        output_filename="processed_data.json",
        log_filename="processing.log",
        input_sub_dir="temp_inputs", # Test subdirectory for input
        output_sub_dir=outputs_subdir_name,
        log_sub_dir=logs_subdir_name,
        cleanup_input=True,
        cleanup_output=False # Keep output file for verification
    )

    print("\nAction Result:")
    print(json.dumps(action_result, indent=2))

    if action_result["success"]:
        print("\n--- Verifying Output and Logs (Test Case 1) ---")
        # Check the output file
        output_file_check = tool.get_file_content("processed_data.json", sub_dir=outputs_subdir_name)
        print("Content of processed_data.json:")
        print(json.dumps(output_file_check.get("content"), indent=2) if output_file_check["success"] else "Failed to read output file.")

        # Check the log file
        log_file_check = tool.get_file_content("processing.log", sub_dir=logs_subdir_name)
        print("\nContent of processing.log:")
        print(log_file_check.get("content") if log_file_check["success"] else "Failed to read log file.")

        # Cleanup specific files
        print("\n--- Cleaning up generated files (Test Case 1) ---")
        cleanup_result_files = tool.cleanup_files(
            ["processed_data.json", "processing.log"],
            sub_dir=None # Note: cleanup_files needs to know the sub_dir if the files are not in base_dir
        )
        # Correcting cleanup_files call to specify subdirs if needed
        cleanup_output_result = tool.cleanup_files("processed_data.json", sub_dir=outputs_subdir_name)
        cleanup_log_result = tool.cleanup_files("processing.log", sub_dir=logs_subdir_name)
        print("Cleanup Output File Result:", json.dumps(cleanup_output_result, indent=2))
        print("Cleanup Log File Result:", json.dumps(cleanup_log_result, indent=2))


    # --- Test Case 2: Configuration File Creation and Reading ---
    print("\n--- Test Case 2: Creating and Reading Configuration File ---")
    config_data = {
        "api_key": "dummy_key_123",
        "timeout_seconds": 30,
        "retries": 3,
        "features": ["logging", "caching"]
    }
    config_creation_result = tool.create_configuration_file("app_config.json", config_data, overwrite=True, sub_dir="configs")
    print("Config Creation Result:")
    print(json.dumps(config_creation_result, indent=2))

    if config_creation_result["success"]:
        print("\n--- Verifying Configuration File (Test Case 2) ---")
        config_file_content = tool.get_file_content("app_config.json", sub_dir="configs")
        print("Content of app_config.json:")
        print(json.dumps(config_file_content.get("content"), indent=2) if config_file_content["success"] else "Failed to read config file.")

        print("\n--- Cleaning up config file (Test Case 2) ---")
        cleanup_config_result = tool.cleanup_files("app_config.json", sub_dir="configs")
        print("Cleanup Config Result:", json.dumps(cleanup_config_result, indent=2))

    # --- Test Case 3: Error Handling - Script Not Found ---
    print("\n--- Test Case 3: Testing Error Handling (Script Not Found) ---")
    error_action_result_not_found = tool.perform_complex_action(
        input_data={"test": "data"},
        script_path="scripts/non_existent_script.sh",
        output_filename="error_output.json"
    )
    print("Error Action Result (Script Not Found):")
    print(json.dumps(error_action_result_not_found, indent=2))

    # --- Test Case 4: Error Handling - Script Returns Error Code ---
    print("\n--- Test Case 4: Testing Error Handling (Script Returns Error Code) ---")
    error_script_content = """#!/bin/bash
    echo "This is an error message on stderr." >&2
    exit 42
    """
    error_script_path_relative = os.path.join(scripts_subdir_name, "error_script.sh")
    error_script_full_path = os.path.join(test_dir_name, error_script_path_relative)

    try:
        with open(error_script_full_path, "w") as f:
            f.write(error_script_content)
        os.chmod(error_script_full_path, 0o755)
        print(f"\nCreated error script at: {error_script_full_path}")
    except Exception as e:
        print(f"Error creating error script: {e}")

    error_code_action_result = tool.perform_complex_action(
        input_data={"test": "data"},
        script_path=error_script_path_relative,
        output_filename="error_code_output.json",
        log_filename="error_code.log",
        log_sub_dir=logs_subdir_name
    )
    print("Error Code Action Result:")
    print(json.dumps(error_code_action_result, indent=2))

    if not error_code_action_result["success"]:
        print("\n--- Verifying Error Log (Test Case 4) ---")
        error_log_content = tool.get_file_content("error_code.log", sub_dir=logs_subdir_name)
        print("Content of error_code.log:")
        print(error_log_content.get("content") if error_log_content["success"] else "Failed to read error log.")

    # --- Test Case 5: Error Handling - Malformed JSON Output ---
    print("\n--- Test Case 5: Testing Error Handling (Malformed JSON Output) ---")
    malformed_json_script_content = """#!/bin/bash
    echo "This is not valid JSON."
    exit 0
    """
    malformed_json_script_path_relative = os.path.join(scripts_subdir_name, "malformed_json_script.sh")
    malformed_json_script_full_path = os.path.join(test_dir_name, malformed_json_script_path_relative)

    try:
        with open(malformed_json_script_full_path, "w") as f:
            f.write(malformed_json_script_content)
        os.chmod(malformed_json_script_full_path, 0o755)
        print(f"\nCreated malformed JSON script at: {malformed_json_script_full_path}")
    except Exception as e:
        print(f"Error creating malformed JSON script: {e}")

    malformed_json_action_result = tool.perform_complex_action(
        input_data={"test": "data"},
        script_path=malformed_json_script_path_relative,
        output_filename="malformed_output.json",
        log_filename="malformed_output.log",
        log_sub_dir=logs_subdir_name
    )
    print("Malformed JSON Action Result:")
    print(json.dumps(malformed_json_action_result, indent=2))

    # --- Test Case 6: Cleanup Directory ---
    print("\n--- Test Case 6: Testing Directory Cleanup ---")
    # Create some dummy files in a temporary directory to clean up
    temp_dir_to_cleanup = "temp_dir_for_cleanup"
    os.makedirs(os.path.join(test_dir_name, temp_dir_to_cleanup), exist_ok=True)
    with open(os.path.join(test_dir_name, temp_dir_to_cleanup, "file1.txt"), "w") as f:
        f.write("content1")
    with open(os.path.join(test_dir_name, temp_dir_to_cleanup, "file2.log"), "w") as f:
        f.write("content2")
    
    print(f"Created directory '{temp_dir_to_cleanup}' with files for cleanup.")

    cleanup_dir_result = tool.cleanup_directory(temp_dir_to_cleanup)
    print("Directory Cleanup Result:")
    print(json.dumps(cleanup_dir_result, indent=2))
    print(f"Directory '{temp_dir_to_cleanup}' exists after cleanup: {os.path.exists(os.path.join(test_dir_name, temp_dir_to_cleanup))}")


    # --- Final Cleanup of the test environment ---
    print(f"\n--- Cleaning up main test environment directory: {test_dir_name} ---")
    try:
        # Using shutil.rmtree directly on the main test directory
        shutil.rmtree(test_dir_name)
        print(f"Removed test directory: {test_dir_name}")
    except OSError as e:
        print(f"Error removing test directory '{test_dir_name}': {e}")

