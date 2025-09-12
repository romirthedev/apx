
import os
import sys
from typing import Dict, Any, List, Optional

class SimpleTextTool:
    """
    A specialized Python tool class for performing simple text-based actions.

    This class provides methods to interact with text files in a safe and structured manner.
    It is designed to be compatible with macOS and includes enhanced error handling,
    input validation, and robustness.
    """

    def __init__(self):
        """Initializes the SimpleTextTool."""
        pass

    def _validate_file_path(self, file_path: str) -> Dict[str, Any]:
        """
        Internal helper to validate file path existence and read permissions.

        Args:
            file_path: The absolute or relative path to the text file.

        Returns:
            A dictionary with 'success' (bool) and 'message' (str).
            If successful, 'success' is True. If not, 'success' is False and
            'message' contains the error description.
        """
        if not isinstance(file_path, str) or not file_path.strip():
            return {
                'success': False,
                'message': "Error: Invalid file path provided. Path cannot be empty or non-string."
            }

        if not os.path.exists(file_path):
            return {
                'success': False,
                'message': f"Error: File not found at '{file_path}'."
            }
        if not os.path.isfile(file_path):
            return {
                'success': False,
                'message': f"Error: Path '{file_path}' is not a file."
            }
        if not os.access(file_path, os.R_OK):
            return {
                'success': False,
                'message': f"Error: Permission denied to read file '{file_path}'."
            }
        return {'success': True, 'message': ''}

    def read_file_content(self, file_path: str) -> Dict[str, Any]:
        """
        Reads the entire content of a text file.

        Args:
            file_path: The absolute or relative path to the text file.

        Returns:
            A dictionary containing:
            - 'success' (bool): True if the operation was successful, False otherwise.
            - 'message' (str): A descriptive message about the operation's outcome.
            - 'content' (str | None): The content of the file if successful, None otherwise.
        """
        validation_result = self._validate_file_path(file_path)
        if not validation_result['success']:
            return {
                'success': False,
                'message': validation_result['message'],
                'content': None
            }

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {
                'success': True,
                'message': f"Successfully read content from '{file_path}'.",
                'content': content
            }
        except UnicodeDecodeError:
            return {
                'success': False,
                'message': f"Error: Could not decode file '{file_path}' using UTF-8 encoding. Please check file encoding.",
                'content': None
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"An unexpected error occurred while reading '{file_path}': {e}",
                'content': None
            }

    def write_to_file(self, file_path: str, content: str, append: bool = False) -> Dict[str, Any]:
        """
        Writes content to a text file.

        Args:
            file_path: The absolute or relative path to the text file.
            content: The string content to write to the file.
            append: If True, append content to the end of the file; otherwise, overwrite the file.

        Returns:
            A dictionary containing:
            - 'success' (bool): True if the operation was successful, False otherwise.
            - 'message' (str): A descriptive message about the operation's outcome.
            - 'file_path' (str | None): The absolute path of the file that was written to, if successful.
        """
        if not isinstance(file_path, str) or not file_path.strip():
            return {
                'success': False,
                'message': "Error: Invalid file path provided. Path cannot be empty or non-string.",
                'file_path': None
            }
        if not isinstance(content, str):
            return {
                'success': False,
                'message': "Error: Content to write must be a string.",
                'file_path': None
            }

        directory = os.path.dirname(file_path)
        if directory:
            if not os.path.exists(directory):
                try:
                    os.makedirs(directory)
                except OSError as e:
                    return {
                        'success': False,
                        'message': f"Error: Failed to create directory '{directory}'. {e}",
                        'file_path': None
                    }
            elif not os.path.isdir(directory):
                return {
                    'success': False,
                    'message': f"Error: Path '{directory}' exists but is not a directory.",
                    'file_path': None
                }

        # Check write permissions for the directory or file if it exists
        if os.path.exists(file_path):
            if not os.access(file_path, os.W_OK):
                return {
                    'success': False,
                    'message': f"Error: Permission denied to write to file '{file_path}'.",
                    'file_path': None
                }
        else:
            # Check write permission for the directory if file doesn't exist
            if not os.access(directory or '.', os.W_OK):
                return {
                    'success': False,
                    'message': f"Error: Permission denied to write to directory '{directory or '.'}' to create '{file_path}'.",
                    'file_path': None
                }

        mode = 'a' if append else 'w'
        try:
            with open(file_path, mode, encoding='utf-8') as f:
                f.write(content)
            return {
                'success': True,
                'message': f"Successfully {'appended to' if append else 'wrote to'} '{file_path}'.",
                'file_path': os.path.abspath(file_path)
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"An unexpected error occurred while writing to '{file_path}': {e}",
                'file_path': None
            }

    def count_lines(self, file_path: str) -> Dict[str, Any]:
        """
        Counts the number of lines in a text file.

        Args:
            file_path: The absolute or relative path to the text file.

        Returns:
            A dictionary containing:
            - 'success' (bool): True if the operation was successful, False otherwise.
            - 'message' (str): A descriptive message about the operation's outcome.
            - 'line_count' (int | None): The number of lines in the file if successful, None otherwise.
        """
        validation_result = self._validate_file_path(file_path)
        if not validation_result['success']:
            return {
                'success': False,
                'message': validation_result['message'],
                'line_count': None
            }

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                line_count = sum(1 for _ in f)
            return {
                'success': True,
                'message': f"Successfully counted {line_count} lines in '{file_path}'.",
                'line_count': line_count
            }
        except UnicodeDecodeError:
            return {
                'success': False,
                'message': f"Error: Could not decode file '{file_path}' using UTF-8 encoding. Please check file encoding.",
                'line_count': None
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"An unexpected error occurred while counting lines in '{file_path}': {e}",
                'line_count': None
            }

    def search_text(self, file_path: str, search_string: str, case_sensitive: bool = True) -> Dict[str, Any]:
        """
        Searches for occurrences of a string within a text file.

        Args:
            file_path: The absolute or relative path to the text file.
            search_string: The string to search for.
            case_sensitive: If True, the search is case-sensitive.

        Returns:
            A dictionary containing:
            - 'success' (bool): True if the operation was successful, False otherwise.
            - 'message' (str): A descriptive message about the operation's outcome.
            - 'matches' (list[int] | None): A list of line numbers (1-based index) where the string was found, or None if an error occurred.
            - 'match_count' (int | None): The total number of lines containing the search string, or None if an error occurred.
        """
        validation_result = self._validate_file_path(file_path)
        if not validation_result['success']:
            return {
                'success': False,
                'message': validation_result['message'],
                'matches': None,
                'match_count': None
            }

        if not isinstance(search_string, str) or not search_string:
            return {
                'success': False,
                'message': "Error: Search string must be a non-empty string.",
                'matches': None,
                'match_count': None
            }

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            return {
                'success': False,
                'message': f"Error: Could not decode file '{file_path}' using UTF-8 encoding. Please check file encoding.",
                'matches': None,
                'match_count': None
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"An unexpected error occurred while reading '{file_path}' for search: {e}",
                'matches': None,
                'match_count': None
            }

        matches: List[int] = []
        search_term = search_string if case_sensitive else search_string.lower()

        try:
            for i, line in enumerate(lines):
                line_to_check = line if case_sensitive else line.lower()
                if search_term in line_to_check:
                    matches.append(i + 1)  # 1-based line numbering

            message = f"Found {len(matches)} occurrence(s) of '{search_string}' in '{file_path}'."
            if not matches:
                message = f"'{search_string}' not found in '{file_path}'."

            return {
                'success': True,
                'message': message,
                'matches': matches,
                'match_count': len(matches)
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"An unexpected error occurred during text search in '{file_path}': {e}",
                'matches': None,
                'match_count': None
            }

    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Retrieves basic information about a file.

        Args:
            file_path: The absolute or relative path to the text file.

        Returns:
            A dictionary containing:
            - 'success' (bool): True if the operation was successful, False otherwise.
            - 'message' (str): A descriptive message about the operation's outcome.
            - 'file_info' (dict | None): A dictionary with file details (size, last modified, etc.)
                                         if successful, None otherwise.
        """
        validation_result = self._validate_file_path(file_path)
        if not validation_result['success']:
            return {
                'success': False,
                'message': validation_result['message'],
                'file_info': None
            }

        try:
            file_stat = os.stat(file_path)
            file_info = {
                'size_bytes': file_stat.st_size,
                'last_modified': file_stat.st_mtime,
                'created_time': file_stat.st_ctime,
                'absolute_path': os.path.abspath(file_path)
            }
            return {
                'success': True,
                'message': f"Successfully retrieved info for '{file_path}'.",
                'file_info': file_info
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"An unexpected error occurred while getting info for '{file_path}': {e}",
                'file_info': None
            }

    def delete_file(self, file_path: str) -> Dict[str, Any]:
        """
        Deletes a file.

        Args:
            file_path: The absolute or relative path to the file to delete.

        Returns:
            A dictionary containing:
            - 'success' (bool): True if the operation was successful, False otherwise.
            - 'message' (str): A descriptive message about the operation's outcome.
        """
        if not isinstance(file_path, str) or not file_path.strip():
            return {
                'success': False,
                'message': "Error: Invalid file path provided. Path cannot be empty or non-string."
            }

        if not os.path.exists(file_path):
            return {
                'success': False,
                'message': f"Error: File not found at '{file_path}'. Cannot delete."
            }
        if not os.path.isfile(file_path):
            return {
                'success': False,
                'message': f"Error: Path '{file_path}' is not a file. Cannot delete."
            }
        if not os.access(file_path, os.W_OK):
            return {
                'success': False,
                'message': f"Error: Permission denied to delete file '{file_path}'."
            }

        try:
            os.remove(file_path)
            return {
                'success': True,
                'message': f"Successfully deleted '{file_path}'."
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"An unexpected error occurred while deleting '{file_path}': {e}"
            }

if __name__ == '__main__':
    # Example Usage
    tool = SimpleTextTool()
    test_file_path = "my_enhanced_test_document.txt"
    test_content = "This is the first line.\nThis is the second line.\nAnd a third line.\nAnother line with 'test' in it."

    print("--- Enhanced Tool Demonstrations ---")

    # 1. Write to a file
    print("\n1. Writing to a file:")
    write_result = tool.write_to_file(test_file_path, test_content)
    print(f"Write Result: {write_result}")

    # 2. Read content from the file
    print("\n2. Reading content from the file:")
    read_result = tool.read_file_content(test_file_path)
    print(f"Read Result: {read_result}")

    # 3. Count lines
    print("\n3. Counting lines:")
    line_count_result = tool.count_lines(test_file_path)
    print(f"Line Count Result: {line_count_result}")

    # 4. Search for text (case-insensitive)
    print("\n4. Searching for text (case-insensitive 'line'):")
    search_result_insensitive = tool.search_text(test_file_path, "line", case_sensitive=False)
    print(f"Search Result: {search_result_insensitive}")

    # 5. Search for text (case-sensitive)
    print("\n5. Searching for text (case-sensitive 'test'):")
    search_result_sensitive = tool.search_text(test_file_path, "test", case_sensitive=True)
    print(f"Search Result: {search_result_sensitive}")

    # 6. Search for non-existent text
    print("\n6. Searching for non-existent text:")
    search_result_not_found = tool.search_text(test_file_path, "nonexistent")
    print(f"Search Result: {search_result_not_found}")

    # 7. Append to the file
    print("\n7. Appending to the file:")
    append_result = tool.write_to_file(test_file_path, "\nThis is an appended line.", append=True)
    print(f"Append Result: {append_result}")

    # Verify append
    print("\nVerifying append:")
    read_after_append = tool.read_file_content(test_file_path)
    print(f"Read after append: {read_after_append}")

    # 8. Get file info
    print("\n8. Getting file info:")
    file_info_result = tool.get_file_info(test_file_path)
    print(f"File Info Result: {file_info_result}")
    if file_info_result['success']:
        print(f"  File size: {file_info_result['file_info']['size_bytes']} bytes")
        print(f"  Absolute path: {file_info_result['file_info']['absolute_path']}")

    # 9. Test invalid inputs
    print("\n9. Testing invalid inputs:")
    print("  Writing with invalid content type:")
    invalid_write = tool.write_to_file(test_file_path, 123)
    print(f"  Result: {invalid_write}")

    print("  Reading with invalid file path:")
    invalid_read = tool.read_file_content("")
    print(f"  Result: {invalid_read}")

    print("  Searching with empty string:")
    invalid_search = tool.search_text(test_file_path, "")
    print(f"  Result: {invalid_search}")

    # 10. Test file not found during read
    print("\n10. Testing file not found:")
    not_found_result = tool.read_file_content("non_existent_file.txt")
    print(f"Read Non-existent File Result: {not_found_result}")

    # 11. Test directory creation and write
    print("\n11. Testing directory creation and write:")
    nested_dir_file = os.path.join("temp_test_dir", "nested", "another_file.txt")
    nested_content = "Content for a nested file."
    nested_write_result = tool.write_to_file(nested_dir_file, nested_content)
    print(f"Nested Write Result: {nested_write_result}")
    if nested_write_result['success']:
        nested_read_result = tool.read_file_content(nested_dir_file)
        print(f"Nested Read Result: {nested_read_result}")

    # 12. Delete files and directories
    print("\n12. Deleting files and directories:")
    delete_original_result = tool.delete_file(test_file_path)
    print(f"Delete original file result: {delete_original_result}")

    delete_nested_result = tool.delete_file(nested_dir_file)
    print(f"Delete nested file result: {delete_nested_result}")

    # Attempt to remove the created directories if they are empty
    try:
        if os.path.exists(os.path.join("temp_test_dir", "nested")):
            os.rmdir(os.path.join("temp_test_dir", "nested"))
            print("Removed directory: temp_test_dir/nested")
        if os.path.exists("temp_test_dir"):
            os.rmdir("temp_test_dir")
            print("Removed directory: temp_test_dir")
    except OSError as e:
        print(f"Error removing directories: {e}")

    print("\n--- Enhanced Tool Demonstrations Complete ---")
