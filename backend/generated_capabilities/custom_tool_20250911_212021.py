import os
import json
import subprocess
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import ast
import graphviz

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ProjectDocumentationGenerator:
    """
    A specialized tool class for generating comprehensive project documentation,
    including architecture diagrams and detailed technical specifications.
    This tool analyzes project code to extract relevant information and
    leverages external tools like Graphviz for diagram generation.
    """

    def __init__(self, project_root: str):
        """
        Initializes the ProjectDocumentationGenerator.

        Args:
            project_root: The absolute or relative path to the root directory of the project.
                          This directory will be scanned for code and configuration.

        Raises:
            ValueError: If the project root directory does not exist or is not accessible.
        """
        self.project_root = Path(project_root).resolve()
        if not self.project_root.is_dir():
            raise ValueError(f"Project root directory does not exist or is not accessible: {self.project_root}")
        logging.info(f"Initialized ProjectDocumentationGenerator for project root: {self.project_root}")

    def _run_command(self, command: List[str], cwd: Optional[Path] = None) -> Dict[str, Any]:
        """
        Runs a shell command and captures its output, with enhanced error handling and logging.

        Args:
            command: A list of strings representing the command and its arguments.
            cwd: The current working directory for the command. Defaults to self.project_root.

        Returns:
            A dictionary containing 'success' (bool), 'message' (str), and 'output' (str).
        """
        command_str = " ".join(command)
        logging.debug(f"Executing command: '{command_str}' in '{cwd or self.project_root}'")
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                cwd=cwd or self.project_root
            )
            logging.debug(f"Command '{command_str}' succeeded. Output:\n{result.stdout}")
            return {"success": True, "message": "Command executed successfully.", "output": result.stdout}
        except FileNotFoundError:
            error_msg = f"Command not found: '{command[0]}'. Please ensure it is installed and in your PATH."
            logging.error(error_msg)
            return {"success": False, "message": error_msg, "output": ""}
        except subprocess.CalledProcessError as e:
            error_msg = f"Command failed: '{command_str}'. Stderr:\n{e.stderr}\nStdout:\n{e.stdout}"
            logging.error(error_msg)
            return {"success": False, "message": error_msg, "output": e.stdout}
        except Exception as e:
            error_msg = f"An unexpected error occurred while running command '{command_str}': {e}"
            logging.exception(error_msg)
            return {"success": False, "message": error_msg, "output": ""}

    def _parse_python_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Parses a Python file to extract class definitions, methods, and docstrings.

        Args:
            file_path: The absolute path to the Python file.

        Returns:
            A dictionary containing 'classes' (list of dicts) and 'functions' (list of dicts).
            Each dict represents a callable and contains 'name', 'docstring', and 'type' ('class' or 'function').
        """
        file_info = {"classes": [], "functions": []}
        try:
            with file_path.open('r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=str(file_path))

            for node in ast.walk(tree):
                if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                    name = node.name
                    docstring = ast.get_docstring(node)
                    if isinstance(node, ast.ClassDef):
                        callable_type = "class"
                        methods = []
                        for body_item in node.body:
                            if isinstance(body_item, ast.FunctionDef):
                                method_name = body_item.name
                                method_docstring = ast.get_docstring(body_item)
                                # Filter out private/special methods by default, can be made configurable
                                if not method_name.startswith('_'):
                                    methods.append({
                                        "name": method_name,
                                        "docstring": method_docstring,
                                        "type": "method"
                                    })
                        file_info["classes"].append({
                            "name": name,
                            "docstring": docstring,
                            "type": callable_type,
                            "methods": methods
                        })
                    elif isinstance(node, ast.FunctionDef):
                        callable_type = "function"
                        # Filter out private/special functions by default
                        if not name.startswith('_'):
                            file_info["functions"].append({
                                "name": name,
                                "docstring": docstring,
                                "type": callable_type
                            })
        except SyntaxError as e:
            logging.warning(f"Syntax error in {file_path}: {e}. Skipping file parsing.")
        except Exception as e:
            logging.error(f"Error parsing {file_path}: {e}")
        return file_info

    def generate_technical_specifications(self, output_file: Path = Path("technical_specifications.md")) -> Dict[str, Any]:
        """
        Generates a Markdown file containing detailed technical specifications by analyzing Python code.

        This method scans Python files, extracts class definitions, methods, and docstrings,
        and compiles them into a structured Markdown document.

        Args:
            output_file: The path to the output Markdown file. Defaults to "technical_specifications.md"
                         relative to the project root.

        Returns:
            A dictionary indicating success or failure, with a message and the path to the generated file.
        """
        # Ensure output_file is a Path object relative to project_root if it's a string
        if isinstance(output_file, str):
            output_file = Path(output_file)
            
        output_path = self.project_root / output_file
        spec_content = "# Project Technical Specifications\n\n"

        python_files_data: Dict[str, Dict[str, Any]] = {}
        total_files_scanned = 0

        # Walk through the project directory, excluding virtual environments
        for item in self.project_root.rglob("*.py"):
            if any(part in str(item) for part in [".venv", "env", "__pycache__", "venv"]):
                continue
            
            relative_path = str(item.relative_to(self.project_root))
            total_files_scanned += 1
            logging.info(f"Scanning file for technical specs: {relative_path}")
            python_files_data[relative_path] = self._parse_python_file(item)

        if not python_files_data:
            message = "No Python files found in the project after excluding virtual environments."
            logging.warning(message)
            return {"success": False, "message": message, "output_file": None}

        spec_content += f"## Overview\n\n"
        spec_content += f"- Project Root: `{self.project_root}`\n"
        spec_content += f"- Total Python files scanned: {total_files_scanned}\n"
        spec_content += f"- Number of files with extracted information: {len(python_files_data)}\n\n"

        spec_content += "## Module Details\n\n"
        for relative_path, info in sorted(python_files_data.items()):
            spec_content += f"### `{relative_path}`\n\n"

            if info["classes"]:
                spec_content += "**Classes:**\n\n"
                for cls in info["classes"]:
                    spec_content += f"- **`{cls['name']}`**\n"
                    if cls["docstring"]:
                        spec_content += f"  - Docstring: `{cls['docstring']}`\n"
                    if cls["methods"]:
                        spec_content += "  - **Methods:**\n"
                        for method in cls["methods"]:
                            spec_content += f"    - `{method['name']}`"
                            if method["docstring"]:
                                spec_content += f": `{method['docstring']}`"
                            spec_content += "\n"
                    spec_content += "\n"

            if info["functions"]:
                spec_content += "**Functions:**\n\n"
                for func in info["functions"]:
                    spec_content += f"- **`{func['name']}`**"
                    if func["docstring"]:
                        spec_content += f": `{func['docstring']}`"
                    spec_content += "\n"
                spec_content += "\n"

            if not info["classes"] and not info["functions"]:
                spec_content += "*No public classes or functions with docstrings found in this file.*\n\n"

        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(spec_content, encoding='utf-8')
            logging.info(f"Technical specifications generated successfully at: {output_path}")
            return {"success": True, "message": "Technical specifications generated successfully.", "output_file": str(output_path)}
        except IOError as e:
            error_msg = f"Failed to write output file {output_path}: {e}"
            logging.error(error_msg)
            return {"success": False, "message": error_msg, "output_file": None}

    def _get_project_files(self) -> List[Path]:
        """
        Retrieves a list of Python files within the project, excluding virtual environments.
        """
        python_files = []
        for item in self.project_root.rglob("*.py"):
            if not any(part in str(item) for part in [".venv", "env", "__pycache__", "venv"]):
                python_files.append(item)
        return python_files

    def generate_architecture_diagram(self, output_file: Path = Path("architecture.png"), format: str = "png") -> Dict[str, Any]:
        """
        Generates an architecture diagram using Graphviz to visualize Python file dependencies.

        This method requires Graphviz to be installed and accessible in the system's PATH.
        It analyzes import statements to build a dependency graph.

        Args:
            output_file: The path for the output diagram file. Defaults to "architecture.png"
                         relative to the project root.
            format: The output format (e.g., 'png', 'svg', 'pdf'). Defaults to 'png'.

        Returns:
            A dictionary indicating success or failure, with a message and the path to the generated file.
        """
        if not self._is_graphviz_installed():
            message = "Graphviz is not installed or not found in PATH. Please install Graphviz (e.g., 'sudo apt-get install graphviz' or 'brew install graphviz') and ensure 'dot' is in your PATH."
            logging.error(message)
            return {"success": False, "message": message, "output_file": None}

        dot = graphviz.Digraph(comment='Project Architecture Diagram')
        dot.attr(rankdir='LR') # Left-to-Right layout for better readability
        dot.attr('node', shape='box', style='rounded', fontname='Arial')
        dot.attr('edge', arrowhead='vee', fontname='Arial')

        project_files = self._get_project_files()
        relative_paths_map = {f.relative_to(self.project_root): f for f in project_files}
        
        file_nodes = {}
        for rel_path in relative_paths_map:
            file_nodes[str(rel_path)] = str(rel_path)
            dot.node(str(rel_path), label=str(rel_path))

        dependencies: Dict[Path, List[Path]] = {f: [] for f in relative_paths_map.values()}

        for current_file_path in relative_paths_map.values():
            logging.debug(f"Analyzing imports for: {current_file_path.relative_to(self.project_root)}")
            try:
                with current_file_path.open('r', encoding='utf-8') as f:
                    tree = ast.parse(f.read(), filename=str(current_file_path))

                for node in ast.walk(tree):
                    if isinstance(node, (ast.Import, ast.ImportFrom)):
                        imported_modules = []
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                imported_modules.append(alias.name)
                        elif isinstance(node, ast.ImportFrom):
                            if node.module: # Handle relative imports like 'from .'
                                base_module_name = node.module
                                for alias in node.names:
                                    # Construct the potential fully qualified name, handling relative imports
                                    if node.level > 0: # Relative import
                                        # This is a simplified approach; full relative import resolution is complex.
                                        # We'll try to match against known project files.
                                        # For `from . import foo`, `from ..bar import baz`, etc.
                                        # We'll rely on direct file path matching below.
                                        pass # Defer to the path matching logic for simplicity
                                    else:
                                        imported_modules.append(f"{base_module_name}.{alias.name}")
                            else: # from . import module (relative import at top level)
                                for alias in node.names:
                                    # Again, rely on path matching for relative imports.
                                    pass
                        
                        for imported_module_str in imported_modules:
                            # Attempt to resolve imported module to a local file
                            resolved_dependency = None
                            
                            # Direct module name matching
                            for rel_proj_file_str, proj_file_path in relative_paths_map.items():
                                if str(rel_proj_file_str).replace(os.sep, '.') == imported_module_str:
                                    resolved_dependency = proj_file_path
                                    break
                                # Handle package imports like 'import my_package' where my_package has an __init__.py
                                elif str(rel_proj_file_str).replace(os.sep, '.') == f"{imported_module_str}.__init__":
                                    resolved_dependency = proj_file_path
                                    break
                            
                            # Handle relative imports like `from . import sibling` or `from ..parent import module`
                            if resolved_dependency is None and isinstance(node, ast.ImportFrom) and node.level > 0:
                                current_module_parts = str(current_file_path.relative_to(self.project_root)).split(os.sep)
                                import_level = node.level - 1 # 1 means current dir, 2 means parent dir, etc.
                                
                                if import_level < len(current_module_parts):
                                    target_dir_parts = current_module_parts[:len(current_module_parts) - 1 - import_level]
                                    base_import_name = node.module if node.module else "" # For 'from .module import'
                                    
                                    # Construct the path to the potential imported module
                                    potential_import_path_parts = target_dir_parts + base_import_name.split('.')
                                    potential_import_path_str = os.path.join(*potential_import_path_parts)
                                    
                                    # Check for direct file match
                                    for rel_proj_file_str, proj_file_path in relative_paths_map.items():
                                        if str(rel_proj_file_str).replace(os.sep, '.') == potential_import_path_str:
                                            resolved_dependency = proj_file_path
                                            break
                                        # Also check for __init__.py within a directory
                                        if str(rel_proj_file_str).replace(os.sep, '.') == f"{potential_import_path_str}.__init__":
                                            resolved_dependency = proj_file_path
                                            break

                            if resolved_dependency and resolved_dependency != current_file_path:
                                if resolved_dependency not in dependencies[current_file_path]:
                                    dependencies[current_file_path].append(resolved_dependency)
                                    logging.debug(f"  '{current_file_path.relative_to(self.project_root)}' depends on '{resolved_dependency.relative_to(self.project_root)}'")
                            else:
                                # If it's not a local file, treat as an external dependency
                                # Use the top-level module name for external dependencies
                                top_level_module = imported_module_str.split('.')[0]
                                if top_level_module not in file_nodes:
                                    file_nodes[top_level_module] = top_level_module
                                    dot.node(top_level_module, label=top_level_module, shape='ellipse', style='dashed')
                                    logging.debug(f"  '{current_file_path.relative_to(self.project_root)}' depends on external module '{top_level_module}'")

            except SyntaxError as e:
                logging.warning(f"Syntax error in {current_file_path.relative_to(self.project_root)}: {e}. Skipping import analysis for this file.")
            except Exception as e:
                logging.warning(f"Could not fully analyze imports for {current_file_path.relative_to(self.project_root)}: {e}")

        for file_path, deps in dependencies.items():
            for dep_path in deps:
                dot.edge(str(file_path.relative_to(self.project_root)), str(dep_path.relative_to(self.project_root)))

        # Ensure output_file is a Path object relative to project_root if it's a string
        if isinstance(output_file, str):
            output_file = Path(output_file)

        output_path = self.project_root / output_file
        try:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            dot.render(str(output_path.with_suffix('')), format=format, cleanup=True)
            logging.info(f"Architecture diagram generated successfully at: {output_path}")
            return {"success": True, "message": "Architecture diagram generated successfully.", "output_file": str(output_path)}
        except graphviz.backend.execute.ExecutableNotFound:
            message = "Graphviz 'dot' command not found. Please ensure Graphviz is installed and its 'bin' directory is in your system's PATH."
            logging.error(message)
            return {"success": False, "message": message, "output_file": None}
        except Exception as e:
            error_msg = f"Failed to generate diagram: {e}"
            logging.exception(error_msg)
            return {"success": False, "message": error_msg, "output_file": None}

    def _is_graphviz_installed(self) -> bool:
        """
        Checks if Graphviz is installed by trying to run the 'dot' command.
        """
        try:
            # Use subprocess.run with check=True and capture_output=True
            subprocess.run(["dot", "-V"], capture_output=True, text=True, check=True)
            return True
        except (FileNotFoundError, subprocess.CalledProcessError):
            return False

    def generate_complete_documentation(self, output_dir: str = "docs", tech_spec_filename: str = "technical_specifications.md", arch_diagram_filename: str = "architecture.png") -> Dict[str, Any]:
        """
        Generates a complete project documentation package, including technical specifications
        and an architecture diagram, in a specified output directory.

        Args:
            output_dir: The directory where the documentation will be saved.
                        Defaults to 'docs' relative to the project root.
            tech_spec_filename: The filename for the technical specifications Markdown file.
            arch_diagram_filename: The filename for the architecture diagram image file.

        Returns:
            A dictionary indicating success or failure, with a message and details
            about the generated files.
        """
        full_output_dir = self.project_root / output_dir
        logging.info(f"Starting generation of complete documentation in: {full_output_dir}")

        # Ensure the output directory exists
        try:
            full_output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            error_msg = f"Could not create output directory {full_output_dir}: {e}"
            logging.error(error_msg)
            return {"success": False, "message": error_msg, "output_directory": None, "generated_files": []}

        # Generate Technical Specifications
        # Pass Path objects to the generation methods
        tech_spec_result = self.generate_technical_specifications(Path(output_dir) / tech_spec_filename)

        # Generate Architecture Diagram
        arch_diagram_result = self.generate_architecture_diagram(Path(output_dir) / arch_diagram_filename)

        generated_files = []
        messages = []

        if tech_spec_result["success"]:
            generated_files.append(tech_spec_result["output_file"])
            messages.append("Technical specifications generated successfully.")
        else:
            messages.append(f"Technical specifications generation failed: {tech_spec_result['message']}")

        if arch_diagram_result["success"]:
            generated_files.append(arch_diagram_result["output_file"])
            messages.append("Architecture diagram generated successfully.")
        else:
            messages.append(f"Architecture diagram generation failed: {arch_diagram_result['message']}")

        final_message = "Complete project documentation generation finished. " + " ".join(messages)
        success = tech_spec_result["success"] and arch_diagram_result["success"]

        logging.info(f"Complete documentation generation status: {'Success' if success else 'Partial/Failed'}. Message: {final_message}")

        return {
            "success": success,
            "message": final_message,
            "output_directory": str(full_output_dir),
            "generated_files": generated_files
        }

if __name__ == '__main__':
    # This is an example of how to use the class.
    # To run this, you would need a dummy project directory with some Python files.

    # Create a dummy project structure for demonstration
    dummy_project_root_path = Path("dummy_project_for_docs_enhanced")
    
    # Clean up previous runs
    if dummy_project_root_path.exists():
        import shutil
        shutil.rmtree(dummy_project_root_path)

    dummy_project_root_path.mkdir(parents=True, exist_ok=True)
    (dummy_project_root_path / "src").mkdir(exist_ok=True)
    (dummy_project_root_path / "utils").mkdir(exist_ok=True)
    (dummy_project_root_path / "tests").mkdir(exist_ok=True) # Example of a dir to be excluded

    # Create dummy files
    (dummy_project_root_path / "main.py").write_text("""
import os
from src.module_a import ModuleA
from utils.helper import utility_function

def main_entry_point():
    \"\"\"The main entry point of the application.

    This function orchestrates the startup process, initializing core components
    and starting the main application loop. It also handles basic configuration loading.
    \"\"\"
    print("Hello from main!")
    config_path = os.environ.get("APP_CONFIG", "config.yaml")
    print(f"Loading configuration from: {config_path}")
    module_a_instance = ModuleA()
    result = module_a_instance.do_something(10)
    print(f"ModuleA result: {result}")
    print(f"Utility function output: {utility_function()}")

class MainApp:
    \"\"\"Represents the main application class.\"\"\"
    def __init__(self, config_data: Dict[str, Any]):
        self.config = config_data
        self.module_a = ModuleA()

    def run(self):
        \"\"\"Starts the application execution flow.\"\"\"
        print(f"Running with config: {self.config}")
        self._process_data()

    def _process_data(self):
        \"\"\"Internal method to process data using configured modules.\"\"\"
        # Placeholder for actual data processing logic
        pass
""")

    (dummy_project_root_path / "src" / "module_a.py").write_text("""
class ModuleA:
    \"\"\"A module for handling specific data manipulation tasks.\"\"\"
    def __init__(self):
        \"\"\"Initializes ModuleA.\"\"\"
        pass

    def do_something(self, value: int) -> int:
        \"\"\"Performs a doubling operation on the input value.

        Args:
            value: An integer to be doubled.

        Returns:
            The doubled integer value.
        \"\"\"
        return value * 2

    def _private_helper(self):
        \"\"\"A private helper method.\"\"\"
        pass
""")

    (dummy_project_root_path / "src" / "module_b.py").write_text("""
from src.module_a import ModuleA
import logging

class ModuleB:
    \"\"\"Another module that leverages ModuleA for its operations.\"\"\"
    def __init__(self):
        \"\"\"Initializes ModuleB and its dependency.\"\"\"
        self.module_a = ModuleA()
        logging.info("ModuleB initialized.")

    def perform_action(self, x: int) -> int:
        \"\"\"Performs an action using ModuleA's capabilities.

        Args:
            x: The input integer for the action.

        Returns:
            The result from ModuleA after processing.
        \"\"\"
        return self.module_a.do_something(x)

def standalone_function_in_b():
    \"\"\"A standalone function within Module B.\"\"\"
    return "This is a function from module_b"
""")
    (dummy_project_root_path / "utils" / "helper.py").write_text("""
def utility_function():
    \"\"\"A simple utility function for common tasks.\"\"\"
    return "Helper utility output"
""")
    
    # Create a file that might cause parsing issues or be in a virtual env
    (dummy_project_root_path / "tests" / "test_module_a.py").write_text("""
# This file should ideally be ignored by the generator
import unittest
from src.module_a import ModuleA

class TestModuleA(unittest.TestCase):
    def test_do_something(self):
        module = ModuleA()
        self.assertEqual(module.do_something(5), 10)
""")
    (dummy_project_root_path / ".venv" / "some_package" / "__init__.py").write_text("pass") # Simulate venv content


    print("\n--- Testing ProjectDocumentationGenerator ---")

    try:
        # Initialize the generator
        generator = ProjectDocumentationGenerator(str(dummy_project_root_path))

        # Generate technical specifications
        print("\n--- Generating technical specifications ---")
        tech_spec_result = generator.generate_technical_specifications(Path("documentation") / "tech_specs.md")
        print(json.dumps(tech_spec_result, indent=2))

        # Generate architecture diagram
        print("\n--- Generating architecture diagram ---")
        arch_diagram_result = generator.generate_architecture_diagram(Path("documentation") / "architecture_diagram.png", format="png")
        print(json.dumps(arch_diagram_result, indent=2))

        # Generate complete documentation
        print("\n--- Generating complete documentation ---")
        complete_doc_result = generator.generate_complete_documentation("project_docs_output", tech_spec_filename="tech_details.md", arch_diagram_filename="project_structure.svg")
        print(json.dumps(complete_doc_result, indent=2))

        # Example of an error case (non-existent project root)
        print("\n--- Testing with non-existent project root ---")
        try:
            ProjectDocumentationGenerator("/non/existent/path/to/project")
        except ValueError as e:
            print(f"Caught expected error: {e}")

        # Example of Graphviz not being installed (if applicable)
        if not generator._is_graphviz_installed():
            print("\n--- Testing architecture diagram generation when Graphviz is NOT installed ---")
            # Temporarily unset Graphviz path for this test if it's found
            original_path = os.environ.get("PATH", "")
            os.environ["PATH"] = "" 
            try:
                # Re-initialize generator to re-check Graphviz status
                generator_no_gv = ProjectDocumentationGenerator(str(dummy_project_root_path))
                arch_diag_no_gv_result = generator_no_gv.generate_architecture_diagram(Path("docs") / "no_gv_arch.png")
                print(json.dumps(arch_diag_no_gv_result, indent=2))
            finally:
                os.environ["PATH"] = original_path # Restore original PATH

    except Exception as e:
        print(f"\nAn unexpected error occurred during testing: {e}")
        logging.exception("An unexpected error occurred during testing.")

    finally:
        # Clean up dummy project files and generated docs
        if dummy_project_root_path.exists():
            print(f"\nCleaning up dummy project directory: {dummy_project_root_path}")
            import shutil
            shutil.rmtree(dummy_project_root_path)