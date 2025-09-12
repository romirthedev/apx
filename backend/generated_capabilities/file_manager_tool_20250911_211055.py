
import os
import shutil
import json
import ast
import re
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

class CodeDocumentationTool:
    """
    Tool for generating comprehensive project documentation, including file structure analysis
    and code-level documentation extraction.
    """

    def __init__(self):
        # Define safe directories for operations to prevent unintended modifications
        self.safe_directories = [os.path.expanduser("~/Desktop"), os.path.expanduser("~/Documents")]

    def _is_safe_path(self, path: str) -> bool:
        """Check if the path is in a safe directory."""
        try:
            abs_path = os.path.abspath(path)
            return any(abs_path.startswith(os.path.abspath(safe_dir)) for safe_dir in self.safe_directories)
        except Exception:
            return False

    def _validate_path(self, path: str, check_exists: bool = False, is_directory: bool = False) -> Tuple[bool, str]:
        """
        Validates a given path.

        Args:
            path: The path to validate.
            check_exists: If True, checks if the path exists.
            is_directory: If True, checks if the path is a directory.

        Returns:
            A tuple containing a boolean indicating validation success and an error message if any.
        """
        if not isinstance(path, str) or not path.strip():
            return False, "Path cannot be empty."

        if not self._is_safe_path(path):
            return False, f"Path '{path}' is not within a permitted safe directory."

        if check_exists:
            if not os.path.exists(path):
                return False, f"Path '{path}' does not exist."
            if is_directory and not os.path.isdir(path):
                return False, f"Path '{path}' is not a directory."
            if not is_directory and not os.path.isfile(path):
                return False, f"Path '{path}' is not a file."

        return True, ""

    def create_directory(self, path: str) -> Dict[str, Any]:
        """
        Create a new directory.

        Args:
            path: The path to the directory to create.

        Returns:
            A dictionary containing the operation status, path, and a message.
        """
        is_valid, error_msg = self._validate_path(path)
        if not is_valid:
            return {"success": False, "error": error_msg}

        try:
            os.makedirs(path, exist_ok=True)
            return {
                "success": True,
                "path": path,
                "message": f"Directory created successfully: {path}"
            }
        except OSError as e:
            return {"success": False, "error": f"Failed to create directory '{path}': {e}"}
        except Exception as e:
            return {"success": False, "error": f"An unexpected error occurred: {e}"}

    def list_files_and_structure(self, directory: str) -> Dict[str, Any]:
        """
        List files and directories within a given directory, recursively.
        Also captures basic file information.

        Args:
            directory: The path to the directory to list.

        Returns:
            A dictionary containing the operation status, directory, file structure, and counts.
        """
        is_valid, error_msg = self._validate_path(directory, check_exists=True, is_directory=True)
        if not is_valid:
            return {"success": False, "error": error_msg}

        def build_structure(current_dir: Path) -> List[Dict[str, Any]]:
            items = []
            try:
                for item in sorted(current_dir.iterdir()):
                    item_info = {
                        "name": item.name,
                        "type": "directory" if item.is_dir() else "file",
                    }
                    if item.is_file():
                        try:
                            item_info["size"] = item.stat().st_size
                        except OSError:
                            item_info["size"] = None # Handle potential permission errors
                    if item.is_dir():
                        item_info["children"] = build_structure(item)
                    items.append(item_info)
                return items
            except OSError as e:
                # Log or handle permission errors gracefully
                print(f"Warning: Could not access directory '{current_dir}': {e}")
                return []

        try:
            file_structure = build_structure(Path(directory))
            return {
                "success": True,
                "directory": directory,
                "file_structure": file_structure,
                "message": f"File structure generated for: {directory}"
            }
        except Exception as e:
            return {"success": False, "error": f"An unexpected error occurred while building structure: {e}"}

    def copy_file(self, source: str, destination: str) -> Dict[str, Any]:
        """
        Copy a file from source to destination.

        Args:
            source: The path to the source file.
            destination: The path to the destination file or directory.

        Returns:
            A dictionary containing the operation status, source, destination, and a message.
        """
        is_valid_source, error_msg_source = self._validate_path(source, check_exists=True, is_directory=False)
        if not is_valid_source:
            return {"success": False, "error": error_msg_source}

        # For destination, we check if it's a safe path. If it's a directory, we'll copy into it.
        is_valid_dest, error_msg_dest = self._validate_path(destination)
        if not is_valid_dest:
            return {"success": False, "error": error_msg_dest}

        try:
            # Ensure destination directory exists if it's a directory path
            dest_path = Path(destination)
            if dest_path.is_dir():
                dest_file_path = dest_path / Path(source).name
            else:
                dest_file_path = dest_path

            # Ensure parent directory of destination file exists
            dest_file_path.parent.mkdir(parents=True, exist_ok=True)

            shutil.copy2(source, dest_file_path)
            return {
                "success": True,
                "source": source,
                "destination": str(dest_file_path),
                "message": f"File copied from '{source}' to '{dest_file_path}'"
            }
        except OSError as e:
            return {"success": False, "error": f"File copy failed: {e}"}
        except Exception as e:
            return {"success": False, "error": f"An unexpected error occurred during file copy: {e}"}

    def read_file_content(self, file_path: str) -> Dict[str, Any]:
        """
        Reads the content of a file.

        Args:
            file_path: The path to the file to read.

        Returns:
            A dictionary containing the operation status, file path, content, and a message.
        """
        is_valid, error_msg = self._validate_path(file_path, check_exists=True, is_directory=False)
        if not is_valid:
            return {"success": False, "error": error_msg}

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {
                "success": True,
                "file_path": file_path,
                "content": content,
                "message": f"Successfully read file: {file_path}"
            }
        except UnicodeDecodeError:
            return {"success": False, "error": f"Could not decode file '{file_path}' as UTF-8. It might be a binary file."}
        except OSError as e:
            return {"success": False, "error": f"Error reading file '{file_path}': {e}"}
        except Exception as e:
            return {"success": False, "error": f"An unexpected error occurred: {e}"}

    def code_analysis_engine(self, file_path: str) -> Dict[str, Any]:
        """
        Analyzes a Python file to extract function definitions, class definitions,
        and docstrings.

        Args:
            file_path: The path to the Python file.

        Returns:
            A dictionary containing the analysis results: functions, classes, and their docstrings.
        """
        is_valid, error_msg = self._validate_path(file_path, check_exists=True, is_directory=False)
        if not is_valid:
            return {"success": False, "error": error_msg}

        if not file_path.lower().endswith('.py'):
            return {"success": False, "error": f"File '{file_path}' is not a Python file (.py)."}

        file_content_result = self.read_file_content(file_path)
        if not file_content_result["success"]:
            return file_content_result

        content = file_content_result["content"]
        analysis_results = {
            "functions": [],
            "classes": []
        }

        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    docstring = ast.get_docstring(node)
                    analysis_results["functions"].append({
                        "name": node.name,
                        "args": [arg.arg for arg in node.args.args],
                        "docstring": docstring if docstring else "No docstring found."
                    })
                elif isinstance(node, ast.ClassDef):
                    docstring = ast.get_docstring(node)
                    class_info = {
                        "name": node.name,
                        "docstring": docstring if docstring else "No docstring found.",
                        "methods": []
                    }
                    for body_item in node.body:
                        if isinstance(body_item, ast.FunctionDef):
                            class_info["methods"].append({
                                "name": body_item.name,
                                "args": [arg.arg for arg in body_item.args.args],
                                "docstring": ast.get_docstring(body_item) if ast.get_docstring(body_item) else "No docstring found."
                            })
                    analysis_results["classes"].append(class_info)
            return {"success": True, "file_path": file_path, "analysis": analysis_results}
        except SyntaxError as e:
            return {"success": False, "error": f"Syntax error in file '{file_path}': {e}"}
        except Exception as e:
            return {"success": False, "error": f"An unexpected error occurred during code analysis: {e}"}

    def nlp_for_documentation(self, text: str) -> Dict[str, Any]:
        """
        A placeholder for Natural Language Processing tasks related to documentation.
        In a real implementation, this could involve summarizing docstrings,
        identifying key entities, or generating introductory paragraphs.

        For this enhanced version, it will perform basic text cleaning and
        highlighting of function/method calls within a given text (e.g., a docstring).

        Args:
            text: The input text to process.

        Returns:
            A dictionary with processed text and identified code elements.
        """
        if not isinstance(text, str):
            return {"success": False, "error": "Input must be a string."}

        cleaned_text = re.sub(r'\s+', ' ', text).strip() # Normalize whitespace
        
        # Simple attempt to identify function/method calls using regex
        # This is a basic heuristic and might not catch all cases.
        potential_calls = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*\s*\(', cleaned_text)
        
        identified_elements = {
            "original_text": text,
            "cleaned_text": cleaned_text,
            "potential_code_elements": list(set(potential_calls)) # Unique calls
        }
        return {"success": True, "processed_text": identified_elements}


    def documentation_generator(self, project_path: str, output_dir: str) -> Dict[str, Any]:
        """
        Generates a complete project documentation with file structure and code analysis.

        Args:
            project_path: The root path of the project to document.
            output_dir: The directory where the documentation will be saved.

        Returns:
            A dictionary indicating the success of the documentation generation,
            along with the path to the generated documentation.
        """
        is_valid_proj_path, error_msg_proj = self._validate_path(project_path, check_exists=True, is_directory=True)
        if not is_valid_proj_path:
            return {"success": False, "error": f"Invalid project path: {error_msg_proj}"}

        is_valid_out_dir, error_msg_out = self._validate_path(output_dir)
        if not is_valid_out_dir:
            return {"success": False, "error": f"Invalid output directory: {error_msg_out}"}
        
        # Ensure output directory exists
        create_dir_result = self.create_directory(output_dir)
        if not create_dir_result["success"]:
            return {"success": False, "error": f"Failed to create output directory: {create_dir_result['error']}"}

        documentation_data = {
            "project_name": Path(project_path).name,
            "file_structure": {},
            "code_details": {}
        }

        # 1. Generate File Structure
        list_files_result = self.list_files_and_structure(project_path)
        if not list_files_result["success"]:
            return {"success": False, "error": f"Failed to generate file structure: {list_files_result['error']}"}
        documentation_data["file_structure"] = list_files_result["file_structure"]

        # 2. Analyze Python Files and collect code details
        python_files_to_analyze = []
        for dirpath, _, filenames in os.walk(project_path):
            for filename in filenames:
                if filename.endswith(".py"):
                    python_files_to_analyze.append(os.path.join(dirpath, filename))

        for py_file in python_files_to_analyze:
            analysis_result = self.code_analysis_engine(py_file)
            if analysis_result["success"]:
                relative_path = os.path.relpath(py_file, project_path)
                documentation_data["code_details"][relative_path] = analysis_result["analysis"]
            else:
                relative_path = os.path.relpath(py_file, project_path)
                documentation_data["code_details"][relative_path] = {"error": analysis_result["error"]}
                print(f"Warning: Could not analyze {py_file}: {analysis_result['error']}")

        # 3. Generate Documentation Files (e.g., README.md, docs.json)
        try:
            # Generate a JSON file with all collected data
            json_output_path = Path(output_dir) / f"{Path(project_path).name}_documentation.json"
            with open(json_output_path, 'w', encoding='utf-8') as f:
                json.dump(documentation_data, f, indent=4)

            # Generate a README.md with summary
            readme_content = f"# Project Documentation: {documentation_data['project_name']}\n\n"
            readme_content += "## File Structure\n\n"
            readme_content += self._format_file_structure_for_readme(documentation_data["file_structure"]) + "\n\n"
            
            readme_content += "## Code Details\n\n"
            if documentation_data["code_details"]:
                for file_path, details in documentation_data["code_details"].items():
                    readme_content += f"### `{file_path}`\n\n"
                    if "error" in details:
                        readme_content += f"- **Analysis Error:** {details['error']}\n"
                    else:
                        if details.get("functions"):
                            readme_content += "- **Functions:**\n"
                            for func in details["functions"]:
                                readme_content += f"  - `{func['name']}({', '.join(func['args'])})`\n"
                                if func["docstring"] and func["docstring"] != "No docstring found.":
                                    processed_doc = self.nlp_for_documentation(func["docstring"])["processed_text"]
                                    readme_content += f"    - Summary: {processed_doc['cleaned_text'][:100]}...\n" # Truncate for README
                        if details.get("classes"):
                            readme_content += "- **Classes:**\n"
                            for cls in details["classes"]:
                                readme_content += f"  - `{cls['name']}`\n"
                                if cls["docstring"] and cls["docstring"] != "No docstring found.":
                                    processed_doc = self.nlp_for_documentation(cls["docstring"])["processed_text"]
                                    readme_content += f"    - Summary: {processed_doc['cleaned_text'][:100]}...\n" # Truncate for README
                                if cls.get("methods"):
                                    readme_content += "    - **Methods:**\n"
                                    for method in cls["methods"]:
                                        readme_content += f"      - `{method['name']}({', '.join(method['args'])})`\n"
                                        if method["docstring"] and method["docstring"] != "No docstring found.":
                                            processed_doc = self.nlp_for_documentation(method["docstring"])["processed_text"]
                                            readme_content += f"        - Summary: {processed_doc['cleaned_text'][:100]}...\n" # Truncate for README
                    readme_content += "\n"
            else:
                readme_content += "No Python files found or analyzed.\n"

            readme_output_path = Path(output_dir) / "README.md"
            with open(readme_output_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)

            return {
                "success": True,
                "message": "Project documentation generated successfully.",
                "documentation_json": str(json_output_path),
                "documentation_readme": str(readme_output_path)
            }

        except OSError as e:
            return {"success": False, "error": f"Error writing documentation files: {e}"}
        except Exception as e:
            return {"success": False, "error": f"An unexpected error occurred during documentation file generation: {e}"}

    def _format_file_structure_for_readme(self, structure: List[Dict[str, Any]], indent: int = 0) -> str:
        """
        Recursively formats the file structure for a Markdown README.
        """
        md_string = ""
        prefix = "  " * indent
        for item in structure:
            if item["type"] == "directory":
                md_string += f"{prefix}- 📁 **{item['name']}/**\n"
                if "children" in item:
                    md_string += self._format_file_structure_for_readme(item["children"], indent + 1)
            else:
                md_string += f"{prefix}- 📄 {item['name']} ({item.get('size', '?')} bytes)\n"
        return md_string

