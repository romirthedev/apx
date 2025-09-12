
import os
import shutil
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
import ast
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CodeAnalyzerTool:
    """
    Tool for analyzing project files, generating documentation structures,
    and providing detailed explanations.
    """

    def __init__(self):
        # Define safer default directories, expandable by user if needed.
        # For a real-world scenario, this might involve more sophisticated security checks
        # or user confirmation for arbitrary directories.
        self.safe_directories = [os.path.expanduser("~/Desktop"), os.path.expanduser("~/Documents")]
        self.project_root: Optional[Path] = None

    def _is_safe_path(self, path: str) -> bool:
        """
        Check if the given path is within one of the predefined safe directories.
        This is a basic security measure.
        """
        try:
            abs_path = Path(path).resolve()
            return any(abs_path.is_relative_to(safe_dir) for safe_dir in self.safe_directories)
        except Exception as e:
            logging.error(f"Error checking safe path for {path}: {e}")
            return False

    def set_project_root(self, project_path: str) -> Dict[str, Any]:
        """
        Sets the root directory for project analysis.
        Validates if the path exists and is within safe directories.
        """
        try:
            path = Path(project_path)
            if not path.exists():
                return {"success": False, "error": f"Project path does not exist: {project_path}"}
            if not path.is_dir():
                return {"success": False, "error": f"Project path is not a directory: {project_path}"}
            if not self._is_safe_path(project_path):
                return {"success": False, "error": f"Project path is not in a safe directory: {project_path}"}

            self.project_root = path
            logging.info(f"Project root set to: {self.project_root}")
            return {
                "success": True,
                "message": f"Project root set to {project_path}"
            }
        except Exception as e:
            logging.error(f"Error setting project root for {project_path}: {e}")
            return {"success": False, "error": str(e)}

    def _analyze_python_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Analyzes a single Python file to extract functions, classes, and their docstrings.
        This is a custom code analysis engine for Python.
        """
        analysis_results = {
            "functions": [],
            "classes": [],
            "summary": "No significant definitions found."
        }
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_info = {
                        "name": node.name,
                        "args": [arg.arg for arg in node.args.args],
                        "docstring": ast.get_docstring(node),
                        "lineno": node.lineno,
                        "end_lineno": node.end_lineno
                    }
                    analysis_results["functions"].append(func_info)
                elif isinstance(node, ast.ClassDef):
                    class_info = {
                        "name": node.name,
                        "docstring": ast.get_docstring(node),
                        "methods": [],
                        "lineno": node.lineno,
                        "end_lineno": node.end_lineno
                    }
                    for body_node in node.body:
                        if isinstance(body_node, ast.FunctionDef):
                            method_info = {
                                "name": body_node.name,
                                "args": [arg.arg for arg in body_node.args.args],
                                "docstring": ast.get_docstring(body_node),
                                "lineno": body_node.lineno,
                                "end_lineno": body_node.end_lineno
                            }
                            class_info["methods"].append(method_info)
                    analysis_results["classes"].append(class_info)

            # Basic summarization based on found definitions
            if analysis_results["functions"] or analysis_results["classes"]:
                summary_parts = []
                if analysis_results["classes"]:
                    summary_parts.append(f"Defines {len(analysis_results['classes'])} class(es): {', '.join([c['name'] for c in analysis_results['classes']])}.")
                if analysis_results["functions"]:
                    summary_parts.append(f"Defines {len(analysis_results['functions'])} function(s): {', '.join([f['name'] for f in analysis_results['functions']])}.")
                analysis_results["summary"] = " ".join(summary_parts)

        except SyntaxError as e:
            logging.warning(f"Syntax error in {file_path}: {e}")
            analysis_results["errors"] = [f"Syntax Error: {e}"]
        except Exception as e:
            logging.error(f"Failed to analyze {file_path}: {e}")
            analysis_results["errors"] = [f"Analysis Error: {e}"]

        return analysis_results

    def _generate_natural_language_explanation(self, analysis_results: Dict[str, Any], file_name: str) -> str:
        """
        Generates a detailed, human-readable explanation from the analysis results.
        This is a natural language generation component.
        """
        explanation = f"## Documentation for: `{file_name}`\n\n"
        explanation += f"### Overview\n{analysis_results.get('summary', 'No summary available.')}\n\n"

        if analysis_results.get("errors"):
            explanation += "### Errors During Analysis\n"
            for error in analysis_results["errors"]:
                explanation += f"- {error}\n"
            explanation += "\n"

        if analysis_results.get("classes"):
            explanation += "### Classes\n"
            for cls in analysis_results["classes"]:
                explanation += f"- **`{cls['name']}`** (Lines {cls.get('lineno', 'N/A')}-{cls.get('end_lineno', 'N/A')})\n"
                if cls.get("docstring"):
                    explanation += f"  - **Docstring:** `{cls['docstring'].strip()}`\n"
                else:
                    explanation += "  - No docstring found.\n"

                if cls.get("methods"):
                    explanation += "  ### Methods\n"
                    for method in cls["methods"]:
                        args_str = ", ".join(method.get("args", []))
                        explanation += f"  - **`{method['name']}({args_str})`** (Lines {method.get('lineno', 'N/A')}-{method.get('end_lineno', 'N/A')})\n"
                        if method.get("docstring"):
                            explanation += f"    - **Docstring:** `{method['docstring'].strip()}`\n"
                        else:
                            explanation += "    - No docstring found.\n"
                explanation += "\n"
            explanation += "\n"

        if analysis_results.get("functions"):
            explanation += "### Functions\n"
            for func in analysis_results["functions"]:
                args_str = ", ".join(func.get("args", []))
                explanation += f"- **`{func['name']}({args_str})`** (Lines {func.get('lineno', 'N/A')}-{func.get('end_lineno', 'N/A')})\n"
                if func.get("docstring"):
                    explanation += f"  - **Docstring:** `{func['docstring'].strip()}`\n"
                else:
                    explanation += "  - No docstring found.\n"
            explanation += "\n"

        return explanation

    def analyze_project_and_generate_docs(self, output_dir: str) -> Dict[str, Any]:
        """
        Analyzes all files in the project root, generates a structured documentation,
        and saves it to the specified output directory.
        This function orchestrates the project structure analysis, code analysis,
        and natural language generation.
        """
        if not self.project_root:
            return {"success": False, "error": "Project root not set. Use set_project_root first."}

        if not self._is_safe_path(output_dir):
            return {"success": False, "error": f"Output directory is not in a safe directory: {output_dir}"}

        output_path = Path(output_dir)
        try:
            output_path.mkdir(parents=True, exist_ok=True)
            logging.info(f"Documentation output directory created/ensured: {output_path}")
        except Exception as e:
            logging.error(f"Failed to create output directory {output_path}: {e}")
            return {"success": False, "error": f"Could not create output directory: {e}"}

        documentation_structure: Dict[str, Any] = {"project_name": self.project_root.name, "files": {}}

        for root, _, files in os.walk(self.project_root):
            current_dir_path = Path(root)
            relative_dir_path = current_dir_path.relative_to(self.project_root)

            # Skip output directory if it's within the project root
            if current_dir_path.resolve() == output_path.resolve():
                continue

            for file_name in files:
                file_path = current_dir_path / file_name
                if file_path.suffix == ".py":  # Focus on Python files for now
                    logging.info(f"Analyzing file: {file_path}")
                    analysis_results = self._analyze_python_file(file_path)
                    explanation = self._generate_natural_language_explanation(analysis_results, str(relative_dir_path / file_name))

                    # Save individual file documentation
                    doc_file_name = f"{file_name.replace('.py', '')}_docs.md"
                    doc_file_path = output_path / doc_file_name
                    try:
                        with open(doc_file_path, "w", encoding="utf-8") as doc_f:
                            doc_f.write(explanation)
                        logging.info(f"Generated documentation for {file_path} at {doc_file_path}")
                    except Exception as e:
                        logging.error(f"Failed to write documentation for {file_path} to {doc_file_path}: {e}")

                    # Add to the overall documentation structure
                    documentation_structure["files"][str(relative_dir_path / file_name)] = {
                        "analysis": analysis_results,
                        "doc_path": str(doc_file_path.relative_to(output_path))
                    }
                else:
                    # For non-Python files, we can just list them
                    documentation_structure["files"][str(relative_dir_path / file_name)] = {
                        "type": "other",
                        "info": f"Non-Python file, consider adding specific handlers."
                    }

        # Save the overall JSON structure
        structure_file_path = output_path / "documentation_structure.json"
        try:
            with open(structure_file_path, "w", encoding="utf-8") as sf:
                json.dump(documentation_structure, sf, indent=4)
            logging.info(f"Generated overall documentation structure at {structure_file_path}")
        except Exception as e:
            logging.error(f"Failed to write documentation structure to {structure_file_path}: {e}")

        return {
            "success": True,
            "message": f"Project analysis complete. Documentation generated in {output_dir}",
            "documentation_structure_path": str(structure_file_path)
        }

    def create_directory(self, path: str) -> Dict[str, Any]:
        """
        Create a new directory. Enhanced with validation.
        """
        try:
            if not self._is_safe_path(path):
                return {"success": False, "error": f"Path not in safe directory: {path}"}
            
            dir_path = Path(path)
            dir_path.mkdir(parents=True, exist_ok=True)
            return {
                "success": True,
                "path": str(dir_path.resolve()),
                "message": f"Directory created or already exists: {path}"
            }
        except Exception as e:
            logging.error(f"Error creating directory {path}: {e}")
            return {"success": False, "error": str(e)}
    
    def list_files(self, directory: str) -> Dict[str, Any]:
        """
        List files and directories in a given directory. Enhanced with validation.
        """
        try:
            dir_path = Path(directory)
            if not dir_path.exists():
                return {"success": False, "error": f"Directory does not exist: {directory}"}
            if not dir_path.is_dir():
                return {"success": False, "error": f"Path is not a directory: {directory}"}
            if not self._is_safe_path(directory):
                return {"success": False, "error": f"Path not in safe directory: {directory}"}
            
            files_list = []
            for item_path in dir_path.iterdir():
                item_info = {
                    "name": item_path.name,
                    "type": "directory" if item_path.is_dir() else "file",
                    "size": item_path.stat().st_size if item_path.is_file() else None,
                    "path": str(item_path.resolve())
                }
                files_list.append(item_info)
            
            return {
                "success": True,
                "directory": str(dir_path.resolve()),
                "files": files_list,
                "count": len(files_list)
            }
        except Exception as e:
            logging.error(f"Error listing files in {directory}: {e}")
            return {"success": False, "error": str(e)}
    
    def copy_file(self, source: str, destination: str) -> Dict[str, Any]:
        """
        Copy a file from source to destination. Enhanced with validation.
        """
        try:
            source_path = Path(source)
            destination_path = Path(destination)

            if not source_path.exists():
                return {"success": False, "error": f"Source file does not exist: {source}"}
            if not source_path.is_file():
                return {"success": False, "error": f"Source is not a file: {source}"}
            
            # Ensure destination directory exists if it's a directory path
            if destination_path.suffix == "" and not destination_path.exists():
                destination_path.mkdir(parents=True, exist_ok=True)
            elif destination_path.parent.exists() is False and destination_path.suffix != "":
                 destination_path.parent.mkdir(parents=True, exist_ok=True)

            if not self._is_safe_path(str(source_path.resolve())):
                return {"success": False, "error": f"Source path not in safe directory: {source}"}
            if not self._is_safe_path(str(destination_path.resolve())):
                return {"success": False, "error": f"Destination path not in safe directory: {destination}"}
            
            shutil.copy2(source, destination)
            return {
                "success": True,
                "source": str(source_path.resolve()),
                "destination": str(destination_path.resolve()),
                "message": f"File copied from {source} to {destination}"
            }
        except Exception as e:
            logging.error(f"Error copying file from {source} to {destination}: {e}")
            return {"success": False, "error": str(e)}

    def delete_file(self, file_path: str) -> Dict[str, Any]:
        """
        Deletes a file. Added for completeness and robustness.
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return {"success": False, "error": f"File not found: {file_path}"}
            if not path.is_file():
                return {"success": False, "error": f"Path is not a file: {file_path}"}
            if not self._is_safe_path(str(path.resolve())):
                return {"success": False, "error": f"Path not in safe directory: {file_path}"}
            
            path.unlink()
            return {
                "success": True,
                "message": f"File deleted: {file_path}"
            }
        except Exception as e:
            logging.error(f"Error deleting file {file_path}: {e}")
            return {"success": False, "error": str(e)}

    def delete_directory(self, dir_path: str) -> Dict[str, Any]:
        """
        Deletes a directory and its contents. Added for completeness and robustness.
        """
        try:
            path = Path(dir_path)
            if not path.exists():
                return {"success": False, "error": f"Directory not found: {dir_path}"}
            if not path.is_dir():
                return {"success": False, "error": f"Path is not a directory: {dir_path}"}
            if not self._is_safe_path(str(path.resolve())):
                return {"success": False, "error": f"Path not in safe directory: {dir_path}"}

            shutil.rmtree(dir_path)
            return {
                "success": True,
                "message": f"Directory deleted: {dir_path}"
            }
        except Exception as e:
            logging.error(f"Error deleting directory {dir_path}: {e}")
            return {"success": False, "error": str(e)}

    def read_file(self, file_path: str) -> Dict[str, Any]:
        """
        Reads the content of a file.
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return {"success": False, "error": f"File not found: {file_path}"}
            if not path.is_file():
                return {"success": False, "error": f"Path is not a file: {file_path}"}
            if not self._is_safe_path(str(path.resolve())):
                return {"success": False, "error": f"Path not in safe directory: {file_path}"}

            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            return {
                "success": True,
                "file_path": str(path.resolve()),
                "content": content
            }
        except Exception as e:
            logging.error(f"Error reading file {file_path}: {e}")
            return {"success": False, "error": str(e)}

