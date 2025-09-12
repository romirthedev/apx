
import os
import shutil
import json
import ast
import re
from typing import Dict, Any, List, Optional
from pathlib import Path

class CodeDocumentationTool:
    """
    Tool for generating comprehensive project documentation, including file structure,
    code analysis, and docstring extraction.
    """

    def __init__(self, safe_directories: Optional[List[str]] = None):
        """
        Initializes the CodeDocumentationTool.

        Args:
            safe_directories: A list of directories that are considered safe for operations.
                              Defaults to user's Desktop and Documents if None.
        """
        if safe_directories is None:
            self.safe_directories = [os.path.expanduser("~/Desktop"), os.path.expanduser("~/Documents")]
        else:
            self.safe_directories = [os.path.abspath(d) for d in safe_directories]

    def _is_safe_path(self, path: str) -> bool:
        """Check if the path is in a safe directory."""
        try:
            abs_path = os.path.abspath(path)
            return any(abs_path.startswith(safe_dir) for safe_dir in self.safe_directories)
        except Exception as e:
            print(f"Error checking safe path {path}: {e}")
            return False

    def _validate_path(self, path: str, operation_type: str = "read") -> Dict[str, Any]:
        """
        Validates a given path for safety and existence based on the operation type.

        Args:
            path: The path to validate.
            operation_type: The type of operation ('read', 'write', 'create').

        Returns:
            A dictionary indicating success or failure with an error message if applicable.
        """
        if not path or not isinstance(path, str):
            return {"success": False, "error": "Invalid path provided. Path must be a non-empty string."}

        if not self._is_safe_path(path):
            return {"success": False, "error": f"Operation on path '{path}' is not allowed. It is outside of the permitted safe directories."}

        path_obj = Path(path)
        if operation_type == "read" or operation_type == "list":
            if not path_obj.exists():
                return {"success": False, "error": f"The specified path '{path}' does not exist."}
            if operation_type == "read" and not path_obj.is_file():
                return {"success": False, "error": f"The specified path '{path}' is not a file."}
            if operation_type == "list" and not path_obj.is_dir():
                return {"success": False, "error": f"The specified path '{path}' is not a directory."}
        elif operation_type == "write" or operation_type == "create":
            if path_obj.exists():
                if operation_type == "create" and not path_obj.is_dir():
                    return {"success": False, "error": f"Cannot create directory. Path '{path}' already exists and is a file."}
                if operation_type == "write" and not path_obj.is_file():
                    return {"success": False, "error": f"Cannot write to path '{path}'. It is not a file."}
            else:
                parent_dir = path_obj.parent
                if not parent_dir.exists():
                    return {"success": False, "error": f"The parent directory '{parent_dir}' for path '{path}' does not exist."}
                if not parent_dir.is_dir():
                    return {"success": False, "error": f"The parent directory '{parent_dir}' for path '{path}' is not a directory."}
        return {"success": True}

    def create_directory(self, path: str) -> Dict[str, Any]:
        """
        Create a new directory at the specified path.

        Args:
            path: The path where the directory should be created.

        Returns:
            A dictionary containing success status, the created path, and a message,
            or success status and an error message.
        """
        validation_result = self._validate_path(path, operation_type="create")
        if not validation_result["success"]:
            return validation_result

        try:
            os.makedirs(path, exist_ok=True)
            return {
                "success": True,
                "path": os.path.abspath(path),
                "message": f"Directory created successfully: '{path}'"
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to create directory '{path}': {str(e)}"}

    def list_files_and_directories(self, directory: str) -> Dict[str, Any]:
        """
        List files and subdirectories within a given directory.

        Args:
            directory: The path to the directory to list.

        Returns:
            A dictionary containing success status, the directory path, a list of items,
            and their count, or success status and an error message.
        """
        validation_result = self._validate_path(directory, operation_type="list")
        if not validation_result["success"]:
            return validation_result

        try:
            items_list = []
            for item_name in os.listdir(directory):
                item_path = os.path.join(directory, item_name)
                item_info = {
                    "name": item_name,
                    "path": os.path.abspath(item_path),
                    "type": "directory" if os.path.isdir(item_path) else "file",
                }
                if os.path.isfile(item_path):
                    item_info["size"] = os.path.getsize(item_path)
                items_list.append(item_info)

            return {
                "success": True,
                "directory": os.path.abspath(directory),
                "items": items_list,
                "count": len(items_list)
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to list contents of directory '{directory}': {str(e)}"}

    def copy_item(self, source: str, destination: str) -> Dict[str, Any]:
        """
        Copy a file or directory from source to destination.

        Args:
            source: The path to the source file or directory.
            destination: The path to the destination.

        Returns:
            A dictionary containing success status, source and destination paths,
            and a message, or success status and an error message.
        """
        source_validation = self._validate_path(source, operation_type="read")
        if not source_validation["success"]:
            return source_validation

        # For destination, we need to check if the parent directory exists and is writable.
        # If destination is a directory, it should exist and be a directory.
        # If destination is a file, its parent directory should exist and be writable.
        dest_path_obj = Path(destination)
        if dest_path_obj.is_dir():
            dest_validation = self._validate_path(destination, operation_type="write")
        else:
            dest_validation = self._validate_path(str(dest_path_obj.parent), operation_type="write")
            if dest_validation["success"]:
                # If parent is valid, ensure destination doesn't exist if it's meant to be overwritten.
                # For simplicity, shutil.copy2 handles overwriting, so we focus on parent dir existence.
                pass

        if not dest_validation["success"]:
            return dest_validation

        try:
            if os.path.isdir(source):
                # If destination is a directory, copy into it. Otherwise, copy and rename.
                if os.path.isdir(destination):
                    dest_dir_path = os.path.join(destination, os.path.basename(source))
                else:
                    dest_dir_path = destination
                shutil.copytree(source, dest_dir_path, dirs_exist_ok=True)
                message = f"Directory copied from '{source}' to '{dest_dir_path}'"
            elif os.path.isfile(source):
                shutil.copy2(source, destination)
                message = f"File copied from '{source}' to '{destination}'"
            else:
                return {"success": False, "error": f"Source '{source}' is neither a file nor a directory."}

            return {
                "success": True,
                "source": os.path.abspath(source),
                "destination": os.path.abspath(destination),
                "message": message
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to copy item from '{source}' to '{destination}': {str(e)}"}

    def read_file_content(self, file_path: str) -> Dict[str, Any]:
        """
        Read the content of a file.

        Args:
            file_path: The path to the file to read.

        Returns:
            A dictionary containing success status, the file path, and its content,
            or success status and an error message.
        """
        validation_result = self._validate_path(file_path, operation_type="read")
        if not validation_result["success"]:
            return validation_result

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {
                "success": True,
                "file_path": os.path.abspath(file_path),
                "content": content
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to read file '{file_path}': {str(e)}"}

    def write_to_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Write content to a file. Creates the file if it doesn't exist.

        Args:
            file_path: The path to the file to write to.
            content: The content to write to the file.

        Returns:
            A dictionary containing success status, the file path, and a message,
            or success status and an error message.
        """
        validation_result = self._validate_path(file_path, operation_type="write")
        if not validation_result["success"]:
            return validation_result

        if not isinstance(content, str):
            return {"success": False, "error": "Content to write must be a string."}

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return {
                "success": True,
                "file_path": os.path.abspath(file_path),
                "message": f"Content written to '{file_path}' successfully."
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to write to file '{file_path}': {str(e)}"}

    # --- New Functionality for Code Documentation ---

    def _extract_docstrings(self, code_content: str) -> List[Dict[str, Any]]:
        """
        Extracts docstrings from Python code using AST.

        Args:
            code_content: The string content of a Python file.

        Returns:
            A list of dictionaries, where each dictionary represents a found docstring
            with its type (module, class, function) and content.
        """
        docstrings = []
        try:
            tree = ast.parse(code_content)
            for node in ast.walk(tree):
                docstring = None
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Str):
                        docstring = node.body[0].value.s
                        node_type = node.__class__.__name__.lower()
                        docstrings.append({
                            "type": node_type,
                            "name": node.name,
                            "docstring": docstring.strip() if docstring else ""
                        })
                elif isinstance(node, ast.Module):
                    if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Str):
                        docstring = node.body[0].value.s
                        docstrings.append({
                            "type": "module",
                            "name": "module", # Representing the whole module
                            "docstring": docstring.strip() if docstring else ""
                        })
        except SyntaxError as e:
            print(f"Warning: Could not parse code for docstrings due to SyntaxError: {e}")
        except Exception as e:
            print(f"Warning: An unexpected error occurred during docstring extraction: {e}")
        return docstrings

    def _analyze_code_structure(self, file_path: str) -> Dict[str, Any]:
        """
        Analyzes a single Python file to extract structure, function/class definitions,
        and their docstrings.

        Args:
            file_path: The path to the Python file.

        Returns:
            A dictionary containing file name, path, and extracted code elements (functions, classes) with docstrings.
        """
        file_info = {
            "name": os.path.basename(file_path),
            "path": os.path.abspath(file_path),
            "functions": [],
            "classes": [],
            "module_docstring": None
        }

        read_result = self.read_file_content(file_path)
        if not read_result["success"]:
            file_info["analysis_error"] = read_result["error"]
            return file_info

        code_content = read_result["content"]
        docstrings_data = self._extract_docstrings(code_content)

        for item in docstrings_data:
            if item["type"] == "module":
                file_info["module_docstring"] = item["docstring"]
            elif item["type"] == "function":
                file_info["functions"].append(item)
            elif item["type"] == "class":
                file_info["classes"].append(item)

        # Basic static analysis for function signatures (simplified)
        try:
            tree = ast.parse(code_content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_name = node.name
                    # Find the corresponding function in our extracted data
                    for func_data in file_info["functions"]:
                        if func_data["name"] == func_name:
                            func_data["signature"] = ast.unparse(node) # Use ast.unparse for modern Python
                            break
                elif isinstance(node, ast.ClassDef):
                    class_name = node.name
                    for class_data in file_info["classes"]:
                        if class_data["name"] == class_name:
                            class_data["signature"] = ast.unparse(node)
                            break
        except Exception as e:
            print(f"Warning: Could not extract signatures for {file_path}: {e}")

        return file_info

    def _generate_file_structure_markdown(self, directory: str, prefix: str = "", current_level: int = 0, max_depth: int = 5) -> str:
        """
        Recursively generates a markdown representation of the file structure.

        Args:
            directory: The current directory to list.
            prefix: The string prefix for indentation.
            current_level: The current depth of recursion.
            max_depth: The maximum depth to traverse.

        Returns:
            A markdown string representing the file structure.
        """
        if current_level > max_depth:
            return ""

        items_result = self.list_files_and_directories(directory)
        if not items_result["success"]:
            return f"{prefix}- Error listing directory: {items_result['error']}\n"

        markdown_output = ""
        sorted_items = sorted(items_result["items"], key=lambda x: (x["type"] == "directory", x["name"]))

        for i, item in enumerate(sorted_items):
            connector = "└── " if i == len(sorted_items) - 1 else "├── "
            item_name = item["name"]
            item_path = item["path"]

            if item["type"] == "directory":
                markdown_output += f"{prefix}{connector}[{item_name}]({item_name}/)\n"
                # Recursive call for subdirectories, increasing level and adjusting prefix
                sub_prefix = prefix + ("    " if i == len(sorted_items) - 1 else "│   ")
                markdown_output += self._generate_file_structure_markdown(item_path, sub_prefix, current_level + 1, max_depth)
            else:
                markdown_output += f"{prefix}{connector}[{item_name}]({item_name})\n"
        return markdown_output

    def generate_project_documentation(self, project_root: str, output_file: str = "PROJECT_DOCUMENTATION.md", max_depth: int = 5) -> Dict[str, Any]:
        """
        Generates a complete project documentation file including:
        1. Project file structure.
        2. Analysis of Python files (module docstring, class/function definitions, docstrings, signatures).

        Args:
            project_root: The root directory of the project to document.
            output_file: The name of the markdown file to generate.
            max_depth: The maximum directory depth to include in the file structure.

        Returns:
            A dictionary containing success status and a message, or success status and an error message.
        """
        validation_result = self._validate_path(project_root, operation_type="list")
        if not validation_result["success"]:
            return {
                "success": False,
                "error": f"Invalid project root path: {validation_result['error']}"
            }

        output_path = Path(project_root) / output_file
        output_path_validation = self._validate_path(str(output_path), operation_type="write")
        if not output_path_validation["success"]:
            return {
                "success": False,
                "error": f"Invalid output file path: {output_path_validation['error']}"
            }

        documentation_content = f"# Project Documentation\n\n"
        documentation_content += f"**Project Root:** `{os.path.abspath(project_root)}`\n\n"

        # 1. Generate File Structure
        documentation_content += "## File Structure\n\n"
        file_structure_markdown = self._generate_file_structure_markdown(project_root, max_depth=max_depth)
        if not file_structure_markdown.strip():
            documentation_content += "Could not generate file structure or directory is empty.\n"
        else:
            documentation_content += file_structure_markdown

        documentation_content += "\n---\n\n" # Separator

        # 2. Analyze Python Files
        documentation_content += "## Code Analysis\n\n"
        total_python_files_analyzed = 0
        python_files_details = []

        for root, dirs, files in os.walk(project_root):
            # Skip hidden directories and virtual environments
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('venv', '.venv', 'env', '.env')]
            
            for file in files:
                if file.endswith(".py"):
                    total_python_files_analyzed += 1
                    file_path = os.path.join(root, file)
                    # Ensure analysis is done only on files within the safe project_root
                    if self._is_safe_path(file_path) and os.path.abspath(file_path).startswith(os.path.abspath(project_root)):
                        file_analysis = self._analyze_code_structure(file_path)
                        python_files_details.append(file_analysis)
                    else:
                        python_files_details.append({
                            "name": file,
                            "path": os.path.abspath(file_path),
                            "analysis_error": "File is outside of the project root or not in a safe directory."
                        })

        if total_python_files_analyzed == 0:
            documentation_content += "No Python files (.py) found in the project.\n"
        else:
            for file_detail in python_files_details:
                doc_section = f"### `{file_detail['name']}`\n\n"
                doc_section += f"* **Path:** `{file_detail['path']}`\n"

                if "analysis_error" in file_detail:
                    doc_section += f"* **Analysis Status:** Failed\n"
                    doc_section += f"* **Error:** {file_detail['analysis_error']}\n\n"
                    documentation_content += doc_section
                    continue

                doc_section += f"* **Analysis Status:** Success\n"

                if file_detail.get("module_docstring"):
                    doc_section += f"\n**Module Docstring:**\n```\n{file_detail['module_docstring']}\n```\n"

                if file_detail.get("classes"):
                    doc_section += "\n**Classes:**\n"
                    for cls in file_detail["classes"]:
                        doc_section += f"- **`{cls['name']}`**\n"
                        if cls.get("signature"):
                            doc_section += f"  - Signature: `{cls['signature']}`\n"
                        if cls.get("docstring"):
                            doc_section += f"  - Docstring: `{cls['docstring'][:100]}{'...' if len(cls['docstring']) > 100 else ''}`\n" # Truncate for brevity
                
                if file_detail.get("functions"):
                    doc_section += "\n**Functions:**\n"
                    for func in file_detail["functions"]:
                        doc_section += f"- **`{func['name']}`**\n"
                        if func.get("signature"):
                            doc_section += f"  - Signature: `{func['signature']}`\n"
                        if func.get("docstring"):
                            doc_section += f"  - Docstring: `{func['docstring'][:100]}{'...' if len(func['docstring']) > 100 else ''}`\n" # Truncate for brevity
                
                documentation_content += doc_section + "\n"

        # Write the documentation to the output file
        write_result = self.write_to_file(str(output_path), documentation_content)
        if write_result["success"]:
            return {
                "success": True,
                "message": f"Project documentation generated successfully at: {os.path.abspath(str(output_path))}",
                "output_file": os.path.abspath(str(output_path))
            }
        else:
            return {
                "success": False,
                "error": f"Failed to write documentation file: {write_result['error']}"
            }

