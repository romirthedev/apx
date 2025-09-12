
import subprocess
import os
from typing import Dict, Any

class DirectoryNavigator:
    """
    A class to handle directory navigation and application launching on macOS.
    """

    def open_directory(self, directory_path: str) -> Dict[str, Any]:
        """
        Opens the specified directory in the Finder application.

        Args:
            directory_path: The absolute or relative path to the directory to open.

        Returns:
            A dictionary containing the status of the operation and a message.
            Example:
            {
                "success": True,
                "message": "Directory opened successfully."
            }
            or
            {
                "success": False,
                "message": "Error: Directory not found."
            }
        """
        if not directory_path:
            return {"success": False, "message": "Error: Directory path cannot be empty."}

        # Resolve the path to an absolute path
        absolute_path = os.path.abspath(directory_path)

        if not os.path.isdir(absolute_path):
            return {"success": False, "message": f"Error: Directory not found at '{directory_path}'."}

        try:
            # Use osascript to tell Finder to open the directory
            command = f'tell application "Finder" to open POSIX file "{absolute_path}"'
            subprocess.run(["osascript", "-e", command], check=True, capture_output=True, text=True)
            return {"success": True, "message": f"Directory '{directory_path}' opened successfully in Finder."}
        except FileNotFoundError:
            return {"success": False, "message": "Error: 'osascript' command not found. Is this running on macOS?"}
        except subprocess.CalledProcessError as e:
            return {"success": False, "message": f"Error opening directory '{directory_path}' in Finder: {e.stderr.strip()}"}
        except Exception as e:
            return {"success": False, "message": f"An unexpected error occurred: {e}"}

    def launch_application_with_path(self, app_name: str, path_to_open: str = None) -> Dict[str, Any]:
        """
        Launches a specified application, optionally opening a specific path within it.

        Args:
            app_name: The name of the application to launch (e.g., "TextEdit", "Finder").
            path_to_open: An optional path to open within the application.

        Returns:
            A dictionary containing the status of the operation and a message.
            Example:
            {
                "success": True,
                "message": "Application launched successfully."
            }
            or
            {
                "success": False,
                "message": "Error: Application not found."
            }
        """
        if not app_name:
            return {"success": False, "message": "Error: Application name cannot be empty."}

        try:
            command_parts = ["open"]
            if path_to_open:
                absolute_path = os.path.abspath(path_to_open)
                if not os.path.exists(absolute_path):
                    return {"success": False, "message": f"Error: Path '{path_to_open}' does not exist."}
                command_parts.extend(["-a", app_name, absolute_path])
            else:
                command_parts.extend(["-a", app_name])

            subprocess.run(command_parts, check=True, capture_output=True, text=True)
            return {"success": True, "message": f"Application '{app_name}' launched successfully."}
        except FileNotFoundError:
            return {"success": False, "message": "Error: 'open' command not found. Is this running on macOS?"}
        except subprocess.CalledProcessError as e:
            return {"success": False, "message": f"Error launching application '{app_name}': {e.stderr.strip()}"}
        except Exception as e:
            return {"success": False, "message": f"An unexpected error occurred: {e}"}

if __name__ == '__main__':
    navigator = DirectoryNavigator()

    # Example 1: Open Finder and navigate to Documents
    print("--- Opening Documents in Finder ---")
    result_docs = navigator.open_directory("Documents")
    print(f"Result: {result_docs}\n")

    # Example 2: Open a specific non-existent directory
    print("--- Attempting to open a non-existent directory ---")
    result_nonexistent = navigator.open_directory("non_existent_directory_xyz")
    print(f"Result: {result_nonexistent}\n")

    # Example 3: Launch TextEdit without specifying a path
    print("--- Launching TextEdit ---")
    result_launch_textedit = navigator.launch_application_with_path("TextEdit")
    print(f"Result: {result_launch_textedit}\n")

    # Example 4: Launch TextEdit and open a file (create a dummy file for testing)
    print("--- Launching TextEdit with a file ---")
    dummy_file_path = "my_test_document.txt"
    with open(dummy_file_path, "w") as f:
        f.write("This is a test document.")
    result_launch_with_file = navigator.launch_application_with_path("TextEdit", dummy_file_path)
    print(f"Result: {result_launch_with_file}\n")
    # Clean up the dummy file
    if os.path.exists(dummy_file_path):
        os.remove(dummy_file_path)

    # Example 5: Launch a non-existent application
    print("--- Attempting to launch a non-existent application ---")
    result_nonexistent_app = navigator.launch_application_with_path("NonExistentAppXYZ")
    print(f"Result: {result_nonexistent_app}\n")

    # Example 6: Launch TextEdit and try to open a non-existent file
    print("--- Launching TextEdit with a non-existent file ---")
    result_launch_nonexistent_file = navigator.launch_application_with_path("TextEdit", "non_existent_file.txt")
    print(f"Result: {result_launch_nonexistent_file}\n")

    # Example 7: Open the current directory
    print("--- Opening the current directory ---")
    result_current_dir = navigator.open_directory(".")
    print(f"Result: {result_current_dir}\n")
