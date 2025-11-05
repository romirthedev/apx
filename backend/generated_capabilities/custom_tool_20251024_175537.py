
import os
import sys
from typing import Dict, Any, Optional, List

class LargestAppFinder:
    """
    A specialized tool class to identify the largest application on the computer
    based on its total disk usage. It supports macOS, Windows, and Linux,
    scanning common application directories and handling potential permission
    issues gracefully.

    Note: The definition of an "application" and its disk usage can vary
    significantly across operating systems. This tool uses platform-specific
    heuristics to identify applications and calculates their directory size,
    which might not always reflect the entire installed footprint for complex
    package-managed systems (e.g., Linux distributions, Windows Store Apps).
    """

    def __init__(self) -> None:
        """
        Initializes the LargestAppFinder with default application search paths
        and identification heuristics for the current operating system.
        """
        self._application_search_paths: Dict[str, List[str]] = {
            "darwin": [
                "/Applications",
                os.path.expanduser("~/Applications"),
            ],
            "win32": [
                os.environ.get("PROGRAMFILES", "C:\\Program Files"),
                os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)"),
                os.path.expanduser(os.path.join("~", "AppData", "Local", "Programs")),
                os.path.expanduser(os.path.join("~", "AppData", "Roaming")), # Some user-installed apps may reside here
            ],
            "linux": [
                "/opt", # Common for self-contained third-party software
                os.path.expanduser("~/opt"), # User-specific /opt
                os.path.expanduser("~/.local/share"), # For some user-installed applications (e.g., AppImages, Flatpak runtimes)
                # Further paths could include /usr/local, /usr/share/applications for .desktop files,
                # but calculating their true aggregate size is complex for package-managed systems.
            ]
        }
        self._platform = sys.platform

        # Define specific heuristics for identifying "apps" within search paths
        self._app_identification_strategy: Dict[str, Any] = {
            "darwin": self._identify_macos_apps,
            "win32": self._identify_windows_apps,
            "linux": self._identify_linux_apps,
        }

    def _get_human_readable_size(self, size_bytes: int) -> str:
        """
        Converts a size in bytes to a human-readable string (e.g., "1.2 GB").

        Args:
            size_bytes: The size in bytes.

        Returns:
            A string representing the size in a human-readable format.
        """
        if size_bytes < 0:
            return "Invalid Size"
        if size_bytes == 0:
            return "0 B"

        for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} EB" # Fallback for extremely large sizes

    def _on_walk_error(self, os_error: OSError) -> None:
        """
        Callback function for os.walk errors.
        This allows os.walk to continue even if it encounters unreadable
        directories within an application bundle/directory. Errors are suppressed
        to provide a best-effort size calculation.

        Args:
            os_error: The OSError instance encountered by os.walk.
        """
        # In a verbose mode, one might log these errors:
        # print(f"Warning: Access denied or error during directory walk: {os_error}")
        pass # Suppress specific errors for robustness

    def _calculate_directory_size(self, directory_path: str) -> Optional[int]:
        """
        Recursively calculates the total size of a directory by summing the
        sizes of all files within it.

        Args:
            directory_path: The full path to the directory.

        Returns:
            The total size of the directory in bytes, or None if the path
            is inaccessible, not a directory, or causes fundamental errors
            during traversal.
        """
        if not os.path.isdir(directory_path):
            return None

        total_size = 0
        try:
            # os.walk will use _on_walk_error for subdirectories it cannot access
            for dirpath, _, filenames in os.walk(directory_path, onerror=self._on_walk_error):
                for f in filenames:
                    filepath = os.path.join(dirpath, f)
                    
                    # os.path.getsize can also raise OSError for permission issues
                    # or broken symlinks to non-existent targets.
                    # We typically count the size of the symlink file itself if valid,
                    # but not follow it to sum target's content.
                    # If it's a broken symlink, getsize will raise OSError, which is caught.
                    if os.path.exists(filepath):
                        try:
                            total_size += os.path.getsize(filepath)
                        except OSError:
                            # Skip files that cannot be sized (e.g., permission denied, broken symlink target)
                            pass
            return total_size
        except OSError:
            # Catch errors if the directory_path itself is completely inaccessible
            return None
        except Exception:
            # Catch any other unexpected errors during the initial os.walk setup
            return None

    def _identify_macos_apps(self, search_path: str) -> List[Dict[str, str]]:
        """
        Identifies macOS .app bundles within a given search path.
        """
        apps: List[Dict[str, str]] = []
        try:
            for item_name in os.listdir(search_path):
                if item_name.lower().endswith(".app"):
                    app_path = os.path.join(search_path, item_name)
                    if os.path.isdir(app_path):
                        apps.append({"name": item_name, "path": app_path})
        except PermissionError:
            # Suppress specific directory permission errors, handled by find_largest_app
            pass
        except OSError:
            pass
        return apps

    def _identify_windows_apps(self, search_path: str) -> List[Dict[str, str]]:
        """
        Identifies potential application directories within a given Windows search path.
        This uses a heuristic: any top-level non-hidden directory is considered a potential app.
        """
        apps: List[Dict[str, str]] = []
        try:
            for item_name in os.listdir(search_path):
                item_path = os.path.join(search_path, item_name)
                # Exclude common system/hidden directories to reduce noise and errors.
                # This is a heuristic and might not be exhaustive.
                if os.path.isdir(item_path) and not item_name.startswith(("$")) and \
                   not item_name.lower() in ["system32", "syswow64", "windows", "programdata", "users", "public", "temp"]:
                    # A more sophisticated check might look for an .exe inside,
                    # but simple top-level directory scan is a reasonable heuristic for size.
                    apps.append({"name": item_name, "path": item_path})
        except PermissionError:
            pass
        except OSError:
            pass
        return apps

    def _identify_linux_apps(self, search_path: str) -> List[Dict[str, str]]:
        """
        Identifies potential application directories within a given Linux search path.
        Similar to Windows, this uses a heuristic: any top-level non-hidden directory
        is considered a potential app.
        """
        apps: List[Dict[str, str]] = []
        try:
            for item_name in os.listdir(search_path):
                item_path = os.path.join(search_path, item_name)
                # Exclude common hidden directories and specific system paths
                if os.path.isdir(item_path) and not item_name.startswith("."):
                    # For simplicity, any non-hidden top-level directory is a potential app.
                    # This heuristic is imperfect for Linux due to package management.
                    apps.append({"name": item_name, "path": item_path})
        except PermissionError:
            pass
        except OSError:
            pass
        return apps


    def find_largest_app(self) -> Dict[str, Any]:
        """
        Identifies the largest application on the computer by scanning predefined
        common application directories for the current operating system.

        Returns:
            A dictionary with 'success' (bool), 'message' (str), and 'data' (dict).
            'data' contains 'app_name', 'app_path', 'size_bytes', and
            'size_human_readable' if a largest app is found.
            Returns an empty 'data' dict on failure or if no apps are found.
        """
        platform_paths = self._application_search_paths.get(self._platform)
        if not platform_paths:
            return {
                "success": False,
                "message": f"This tool does not have defined search paths for the current operating system ('{self._platform}').",
                "data": {},
            }

        app_identifier = self._app_identification_strategy.get(self._platform)
        if not app_identifier:
            return {
                "success": False,
                "message": f"This tool does not have an application identification strategy for the current operating system ('{self._platform}').",
                "data": {},
            }

        largest_app_info: Optional[Dict[str, Any]] = None
        max_size_bytes: int = 0
        apps_scanned_count: int = 0
        skipped_paths: List[str] = []
        platform_specific_notes = ""

        if self._platform == "win32":
            platform_specific_notes = "Note for Windows: This tool identifies applications by scanning top-level directories in common installation paths (e.g., Program Files). This might not capture all types of applications (e.g., Windows Store Apps, single-file executables) or their full installed footprint if files are scattered or rely on system components."
        elif self._platform == "linux":
            platform_specific_notes = "Note for Linux: This tool identifies applications by scanning top-level directories in common user-installation paths (e.g., /opt, ~/.local/share). For package-managed software (e.g., installed via apt, yum), calculating total disk usage is complex as files are often scattered across the filesystem and might not be fully represented by a single directory scan."

        for app_dir_root in platform_paths:
            if not os.path.isdir(app_dir_root):
                skipped_paths.append(f"'{app_dir_root}' (not found or not a directory)")
                continue

            try:
                # Use the platform-specific identifier to get potential apps
                potential_apps = app_identifier(app_dir_root)

                for app_candidate in potential_apps:
                    app_name = app_candidate["name"]
                    app_path = app_candidate["path"]

                    apps_scanned_count += 1
                    app_size = self._calculate_directory_size(app_path)

                    if app_size is not None:
                        if app_size > max_size_bytes:
                            max_size_bytes = app_size
                            largest_app_info = {
                                "app_name": app_name,
                                "app_path": app_path,
                                "size_bytes": app_size,
                                "size_human_readable": self._get_human_readable_size(app_size),
                            }
            except PermissionError:
                skipped_paths.append(f"'{app_dir_root}' (permission denied)")
            except OSError as e:
                skipped_paths.append(f"'{app_dir_root}' (OS error: {e})")
            except Exception as e:
                skipped_paths.append(f"'{app_dir_root}' (unexpected error: {e})")

        message_parts = []
        if largest_app_info:
            message_parts.append(f"Successfully identified the largest app out of {apps_scanned_count} potential application installations scanned.")
        else:
            if apps_scanned_count > 0:
                message_parts.append(f"No largest app could be determined among {apps_scanned_count} scanned applications, possibly due to access restrictions or all relevant apps having zero size.")
            else:
                message_parts.append(f"No application directories found in common search paths for '{self._platform}'.")
        
        if skipped_paths:
            message_parts.append(f"Skipped directories due to errors or inaccessibility: {'; '.join(skipped_paths)}.")
        
        if platform_specific_notes:
            message_parts.append(platform_specific_notes)

        final_message = " ".join(message_parts)

        return {
            "success": bool(largest_app_info),
            "message": final_message,
            "data": largest_app_info if largest_app_info else {},
        }
