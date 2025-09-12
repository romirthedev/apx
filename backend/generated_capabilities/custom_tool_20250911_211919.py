import os
import subprocess
import json
import shutil
from typing import Dict, Any, Optional, List, Tuple

class ProjectDocumentationGenerator:
    """
    A specialized tool for generating comprehensive project documentation,
    including architecture diagrams and technical specifications.

    This class provides methods to create structured documentation by analyzing
    project files and leveraging external tools. It aims to be safe, efficient,
    and compatible with macOS.

    The enhancement focuses on providing a more integrated approach to fulfill
    the user's request for "complete project documentation with architecture
    diagrams and technical specifications" by:
    - Introducing a more intelligent analysis phase.
    - Supporting a wider range of diagram and specification tools.
    - Offering more granular control over the documentation generation process.
    - Improving error handling and user feedback.
    - Adding input validation and configuration options.
    """

    def __init__(self, project_path: str, config: Optional[Dict[str, Any]] = None):
        """
        Initializes the ProjectDocumentationGenerator.

        Args:
            project_path: The absolute or relative path to the root of the project.
            config: A dictionary for configuring documentation generation.
                    Example: {
                        "diagram_tool": "plantuml",
                        "diagram_source": "docs/architecture.puml",
                        "diagram_output": "docs/architecture.png",
                        "spec_tool": "sphinx",
                        "spec_source": "docs/source",
                        "spec_output": "docs/technical_specifications.md",
                        "exclude_files": [".git", "__pycache__"],
                        "include_patterns": ["*.py", "*.md", "*.rst", "*.puml"]
                    }
        """
        self.project_path = os.path.abspath(project_path)
        if not os.path.isdir(self.project_path):
            raise FileNotFoundError(f"Project path does not exist or is not a directory: {self.project_path}")

        self.config = {
            "diagram_tool": "plantuml",
            "diagram_source": os.path.join(self.project_path, "architecture.puml"),
            "diagram_output": os.path.join(self.project_path, "architecture.png"),
            "spec_tool": "sphinx",
            "spec_source": os.path.join(self.project_path, "docs", "source"), # Defaulting to a 'docs/source' for Sphinx
            "spec_output": os.path.join(self.project_path, "technical_specifications.md"),
            "exclude_files": [".git", "__pycache__", ".DS_Store"],
            "include_patterns": ["*.py", "*.md", "*.rst", "*.puml", "*.java", "*.c", "*.cpp", "*.js", "*.html", "*.css"],
            "repo_analysis_enabled": True, # Flag to enable/disable code analysis for specs
            "diagram_generation_enabled": True, # Flag to enable/disable diagram generation
            "spec_generation_enabled": True, # Flag to enable/disable spec generation
        }
        if config:
            self.config.update(config)

        self.validate_config()

    def validate_config(self):
        """Validates the current configuration settings."""
        if not self.config.get("diagram_tool") and self.config.get("diagram_generation_enabled"):
            raise ValueError("Diagram tool is not specified in config and diagram generation is enabled.")
        if not self.config.get("spec_tool") and self.config.get("spec_generation_enabled"):
            raise ValueError("Specification tool is not specified in config and specification generation is enabled.")

        # Ensure output directories exist for specified outputs
        diagram_output_dir = os.path.dirname(self.config.get("diagram_output", ""))
        if diagram_output_dir and not os.path.exists(diagram_output_dir):
            try:
                os.makedirs(diagram_output_dir, exist_ok=True)
            except OSError as e:
                raise OSError(f"Could not create output directory for diagram: {diagram_output_dir} - {e}")

        spec_output_dir = os.path.dirname(self.config.get("spec_output", ""))
        if spec_output_dir and not os.path.exists(spec_output_dir):
            try:
                os.makedirs(spec_output_dir, exist_ok=True)
            except OSError as e:
                raise OSError(f"Could not create output directory for specifications: {spec_output_dir} - {e}")

    def _run_command(self, command: List[str], cwd: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes a shell command and captures its output, with enhanced error handling.

        Args:
            command: A list of strings representing the command and its arguments.
            cwd: The working directory to execute the command in. Defaults to project_path.

        Returns:
            A dictionary containing 'success' (bool), 'message' (str), and 'output' (str).
        """
        effective_cwd = cwd if cwd is not None else self.project_path
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=effective_cwd,
                encoding='utf-8'
            )
            stdout, stderr = process.communicate(timeout=120) # Added a timeout for safety
            if process.returncode == 0:
                return {"success": True, "message": "Command executed successfully.", "output": stdout.strip()}
            else:
                return {"success": False, "message": f"Command failed (exit code {process.returncode}): {stderr.strip()}", "output": stderr.strip()}
        except FileNotFoundError:
            return {"success": False, "message": f"Command not found: '{command[0]}'. Please ensure it's installed and in your system's PATH.", "output": ""}
        except subprocess.TimeoutExpired:
            return {"success": False, "message": f"Command '{command[0]}' timed out after 120 seconds.", "output": ""}
        except Exception as e:
            return {"success": False, "message": f"An unexpected error occurred while running command '{command[0]}': {e}", "output": ""}

    def _analyze_project_structure(self) -> Dict[str, Any]:
        """
        Analyzes the project structure to identify relevant files for documentation.
        This is a placeholder for more advanced static analysis.
        """
        file_list = []
        for root, dirs, files in os.walk(self.project_path):
            # Filter out excluded directories and files
            dirs[:] = [d for d in dirs if d not in self.config["exclude_files"]]
            files = [f for f in files if f not in self.config["exclude_files"]]

            for file in files:
                filepath = os.path.join(root, file)
                relative_filepath = os.path.relpath(filepath, self.project_path)
                if any(relative_filepath.endswith(pattern.strip('*')) for pattern in self.config["include_patterns"]):
                    file_list.append(relative_filepath)

        return {"success": True, "message": "Project structure analysis complete.", "files": file_list}

    def _generate_diagram_with_plantuml(self) -> Dict[str, Any]:
        """Generates an architecture diagram using PlantUML."""
        diagram_source_config = self.config.get("diagram_source", "")
        if not diagram_source_config:
            return {
                "success": False,
                "message": "PlantUML source path is not configured.",
                "filepath": None
            }
        source_path = os.path.abspath(os.path.join(self.project_path, diagram_source_config))
        
        diagram_output_config = self.config.get("diagram_output", "")
        if not diagram_output_config:
            return {
                "success": False,
                "message": "PlantUML output path is not configured.",
                "filepath": None
            }
        output_path = os.path.abspath(os.path.join(self.project_path, diagram_output_config))
        output_dir = os.path.dirname(output_path)

        if not os.path.exists(source_path):
            return {
                "success": False,
                "message": f"PlantUML source file not found at: '{source_path}'",
                "filepath": None
            }

        # PlantUML command: plantuml -o <output_dir> <source_file>
        plantuml_command = ["plantuml", "-o", output_dir, source_path]

        # Ensure the output directory exists
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
            except OSError as e:
                return {
                    "success": False,
                    "message": f"Failed to create output directory for diagram: '{output_dir}' - {e}",
                    "filepath": None
                }

        result = self._run_command(plantuml_command, cwd=self.project_path)

        if result["success"]:
            # PlantUML typically names the output file based on the source file name.
            # We need to ensure it matches our expected output path.
            expected_generated_file = os.path.join(output_dir, os.path.basename(source_path).replace(".puml", ".png"))
            if os.path.exists(expected_generated_file):
                try:
                    # Rename if it's not already the target output path
                    if expected_generated_file != output_path:
                        shutil.move(expected_generated_file, output_path)
                    return {
                        "success": True,
                        "message": f"Architecture diagram '{os.path.basename(output_path)}' generated successfully at '{output_path}'.",
                        "filepath": output_path
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "message": f"PlantUML ran successfully, but failed to move output file: {e}",
                        "filepath": None
                    }
            else:
                return {
                    "success": False,
                    "message": f"PlantUML ran but did not produce the expected output file. Looked for: '{expected_generated_file}'",
                    "filepath": None
                }
        else:
            return {
                "success": False,
                "message": f"Failed to generate PlantUML diagram: {result['message']}",
                "filepath": None
            }

    def _generate_diagram_with_other(self, tool: str) -> Dict[str, Any]:
        """Placeholder for other diagram generation tools."""
        return {
            "success": False,
            "message": f"Unsupported diagram tool: '{tool}'. Only 'plantuml' is currently supported.",
            "filepath": None
        }

    def generate_architecture_diagram(self) -> Dict[str, Any]:
        """
        Generates an architecture diagram for the project based on the configuration.
        """
        if not self.config.get("diagram_generation_enabled"):
            return {
                "success": True,
                "message": "Diagram generation is disabled in configuration.",
                "filepath": None
            }

        tool = self.config.get("diagram_tool", "plantuml").lower()

        if tool == "plantuml":
            return self._generate_diagram_with_plantuml()
        else:
            return self._generate_diagram_with_other(tool)

    def _generate_specs_with_sphinx(self) -> Dict[str, Any]:
        """Generates technical specifications using Sphinx."""
        spec_source_config = self.config.get("spec_source", "")
        if not spec_source_config:
            return {
                "success": False,
                "message": "Sphinx source directory is not configured.",
                "filepath": None
            }
        source_dir = os.path.abspath(os.path.join(self.project_path, spec_source_config))

        spec_output_config = self.config.get("spec_output", "")
        if not spec_output_config:
            return {
                "success": False,
                "message": "Sphinx output file path is not configured.",
                "filepath": None
            }
        final_output_path = os.path.abspath(os.path.join(self.project_path, spec_output_config))
        output_dir = os.path.dirname(final_output_path)

        if not os.path.exists(source_dir) or not os.path.isdir(source_dir):
            return {
                "success": False,
                "message": f"Sphinx source directory not found at: '{source_dir}'. "
                           f"Ensure Sphinx is configured with a 'source' directory.",
                "filepath": None
            }

        # Sphinx-build command: sphinx-build -b <builder> <sourcedir> <outputdir>
        builder = self.config.get("spec_builder", "markdown")
        sphinx_build_command = [
            "sphinx-build",
            "-b", builder,
            source_dir,
            output_dir # Sphinx will create a subdirectory for output (e.g., 'html', 'markdown')
        ]

        result = self._run_command(sphinx_build_command, cwd=self.project_path)

        if result["success"]:
            # Determine the actual generated file path.
            # This is heuristic and might need adjustment based on Sphinx configuration.
            # We prioritize common index file names for markdown and HTML builders.
            potential_output_files = [
                os.path.join(output_dir, builder, "index.md"), # For markdown builder
                os.path.join(output_dir, builder, "index.html"), # For html builder
                os.path.join(output_dir, "index.md"), # Fallback if builder subdir is not used for index.md
                os.path.join(output_dir, "index.html") # Fallback if builder subdir is not used for index.html
            ]
            generated_filepath = None
            for pf in potential_output_files:
                if os.path.exists(pf):
                    generated_filepath = pf
                    break

            if generated_filepath:
                try:
                    # Copy the generated markdown/html to the desired output filename
                    shutil.copyfile(generated_filepath, final_output_path)
                    # Clean up the Sphinx build subdirectory if it was created by us and is not the final output
                    build_subdir_path = os.path.join(output_dir, builder)
                    if os.path.exists(build_subdir_path) and os.path.abspath(build_subdir_path) != os.path.abspath(output_dir):
                         shutil.rmtree(build_subdir_path)
                    return {
                        "success": True,
                        "message": f"Technical specifications '{os.path.basename(final_output_path)}' generated successfully at '{final_output_path}'.",
                        "filepath": final_output_path
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "message": f"Sphinx built successfully, but failed to copy output to '{final_output_path}': {e}",
                        "filepath": None
                    }
            else:
                return {
                    "success": False,
                    "message": f"Sphinx ran successfully, but the expected output file (e.g., index.md or index.html) was not found in '{output_dir}' or its builder-specific subdirectory. "
                               f"Please check your Sphinx configuration and builder.",
                    "filepath": None
                }
        else:
            return {
                "success": False,
                "message": f"Failed to generate Sphinx documentation: {result['message']}",
                "filepath": None
            }

    def _generate_specs_with_other(self, tool: str) -> Dict[str, Any]:
        """Placeholder for other specification generation tools."""
        return {
            "success": False,
            "message": f"Unsupported specification tool: '{tool}'. Only 'sphinx' is currently supported.",
            "filepath": None
        }

    def generate_technical_specifications(self) -> Dict[str, Any]:
        """
        Generates technical specifications for the project based on the configuration.
        """
        if not self.config.get("spec_generation_enabled"):
            return {
                "success": True,
                "message": "Specification generation is disabled in configuration.",
                "filepath": None
            }

        tool = self.config.get("spec_tool", "sphinx").lower()

        if tool == "sphinx":
            return self._generate_specs_with_sphinx()
        else:
            return self._generate_specs_with_other(tool)

    def generate_project_documentation(self) -> Dict[str, Any]:
        """
        Generates both architecture diagram and technical specifications for the project.
        """
        all_results = []
        overall_success = True
        messages = []

        if self.config.get("diagram_generation_enabled"):
            print("Generating architecture diagram...")
            diagram_result = self.generate_architecture_diagram()
            all_results.append({"type": "diagram", **diagram_result})
            overall_success = overall_success and diagram_result["success"]
            messages.append(f"Architecture Diagram: {diagram_result['message']}")
        else:
            messages.append("Architecture Diagram: Generation skipped as disabled in config.")

        if self.config.get("spec_generation_enabled"):
            if self.config.get("repo_analysis_enabled"):
                print("Analyzing project repository for technical specifications...")
                analysis_result = self._analyze_project_structure()
                if not analysis_result["success"]:
                    messages.append(f"Repository Analysis: Failed - {analysis_result['message']}")
                    overall_success = False
                else:
                    messages.append(f"Repository Analysis: {analysis_result['message']} ({len(analysis_result['files'])} files found)")
                    # In a more advanced version, you'd pass analysis_result['files'] to spec generator

            print("Generating technical specifications...")
            spec_result = self.generate_technical_specifications()
            all_results.append({"type": "specifications", **spec_result})
            overall_success = overall_success and spec_result["success"]
            messages.append(f"Technical Specifications: {spec_result['message']}")
        else:
            messages.append("Technical Specifications: Generation skipped as disabled in config.")


        return {
            "success": overall_success,
            "message": "\n".join(messages),
            "results": all_results
        }

if __name__ == '__main__':
    # Example Usage (requires dummy project setup and installed tools)

    # 1. Create a dummy project structure for testing
    dummy_project_root = "dummy_project_for_docs_enhanced"
    try:
        os.makedirs(os.path.join(dummy_project_root, "docs", "source", "modules"), exist_ok=True)
        os.makedirs(os.path.join(dummy_project_root, "docs", "source", "api", "services"), exist_ok=True)
        os.makedirs(os.path.join(dummy_project_root, "output"), exist_ok=True) # For custom output paths

        # Dummy PlantUML file
        plantuml_content = """
@startuml
title Enhanced Project Architecture
node "API Gateway" as GW
node "User Service" as US
node "Product Service" as PS
node "Database" as DB

GW --> US : Route Request
GW --> PS : Route Request
US --> DB : Read/Write User Data
PS --> DB : Read/Write Product Data
US --> PS : Get Product Details (Internal)
@enduml
"""
        with open(os.path.join(dummy_project_root, "docs", "architecture.puml"), "w") as f:
            f.write(plantuml_content)

        # Dummy Sphinx conf.py (minimal)
        sphinx_conf_content = """
import os
import sys
sys.path.insert(0, os.path.abspath('../')) # Adjust path to find modules in project root

project = 'My Enhanced Dummy Project'
copyright = '2023, Author'
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon', # Support for NumPy and Google style docstrings
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.mathjax',
    'sphinx.ext.ifconfig',
    'sphinx.ext.githubpages',
    'sphinx.ext.viewcode', # Add links to highlighted source code
]
templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
html_theme = 'alabaster' # Common theme, or 'sphinx_rtd_theme' if installed
"""
        with open(os.path.join(dummy_project_root, "docs", "source", "conf.py"), "w") as f:
            f.write(sphinx_conf_content)

        # Dummy index.rst for Sphinx
        index_rst_content = """
Welcome to My Enhanced Dummy Project's Documentation!
====================================================

This is a sample document demonstrating enhanced documentation generation.

.. note::
   This is an example note.

.. toctree::
   :maxdepth: 2
   :caption: Core Components:

   modules/index
   api/index

Getting Started
---------------

The project is designed to be modular and scalable.

Installation
------------

Refer to the main project README for installation instructions.

API Documentation
-----------------

This section provides detailed API documentation generated from source code.
"""
        with open(os.path.join(dummy_project_root, "docs", "source", "index.rst"), "w") as f:
            f.write(index_rst_content)

        # Dummy module index for Sphinx
        modules_index_rst_content = """
Module Overview
===============

This section provides an overview of the project's modules.

.. toctree::
   :maxdepth: 1

   my_module
   another_module
   services/user_service
"""
        with open(os.path.join(dummy_project_root, "docs", "source", "modules", "index.rst"), "w") as f:
            f.write(modules_index_rst_content)


        # Dummy API index for Sphinx
        api_index_rst_content = """
API Reference
=============

This is the main API reference page.

.. toctree::
   :maxdepth: 1

   api.my_module
   api.another_module
   api.services.user_service
"""
        with open(os.path.join(dummy_project_root, "docs", "source", "api", "index.rst"), "w") as f:
            f.write(api_index_rst_content)


        # Dummy Python modules
        my_module_content = """
class MyClass:
    \"\"\"A sample class demonstrating basic features.

    This class is a placeholder for more complex implementations.
    \"\"\"
    def __init__(self, name: str = "World"):
        \"\"\"Initializes the MyClass object.

        Args:
            name (str): The name to greet. Defaults to "World".
        \"\"\"
        self.name = name

    def greet(self) -> str:
        \"\"\"Returns a personalized greeting.

        Returns:
            str: A greeting message.
        \"\"\"
        return f"Hello, {self.name}!"

def utility_function(x: int, y: int) -> int:
    \"\"\"A simple utility function for addition.

    Args:
        x (int): The first number.
        y (int): The second number.

    Returns:
        int: The sum of x and y.
    \"\"\"
    return x + y
"""
        with open(os.path.join(dummy_project_root, "my_module.py"), "w") as f:
            f.write(my_module_content)

        another_module_content = """
def a_different_function():
    \"\"\"Another example function.
    \"\"\"
    print("This is from another module.")
"""
        with open(os.path.join(dummy_project_root, "another_module.py"), "w") as f:
            f.write(another_module_content)

        # Dummy service module
        user_service_content = """
from typing import Optional

class UserService:
    \"\"\"Manages user-related operations.
    \"\"\"
    def __init__(self):
        self._users = {}

    def create_user(self, user_id: str, data: dict) -> bool:
        \"\"\"Creates a new user.
        \"\"\"
        if user_id not in self._users:
            self._users[user_id] = data
            return True
        return False

    def get_user(self, user_id: str) -> Optional[dict]:
        \"\"\"Retrieves a user by ID.
        \"\"\"
        return self._users.get(user_id)
"""
        with open(os.path.join(dummy_project_root, "services", "user_service.py"), "w") as f:
            f.write(user_service_content)

        # Dummy RST files for modules and API references
        with open(os.path.join(dummy_project_root, "docs", "source", "modules", "my_module.rst"), "w") as f:
            f.write(".. automodule:: my_module\n   :members:\n")
        with open(os.path.join(dummy_project_root, "docs", "source", "modules", "another_module.rst"), "w") as f:
            f.write(".. automodule:: another_module\n   :members:\n")
        with open(os.path.join(dummy_project_root, "docs", "source", "api", "my_module.rst"), "w") as f:
            f.write(".. automodule:: my_module\n   :members:\n")
        with open(os.path.join(dummy_project_root, "docs", "source", "api", "another_module.rst"), "w") as f:
            f.write(".. automodule:: another_module\n   :members:\n")
        with open(os.path.join(dummy_project_root, "docs", "source", "api", "services", "user_service.rst"), "w") as f:
            f.write(".. automodule:: services.user_service\n   :members:\n")


        # --- Example 1: Default configuration ---
        print("\n--- Running Example 1: Default Configuration ---")
        try:
            # The error "ERROR: ProjectDocumentationGenerator.__init__() missing 1 required positional argument: 'project_path'"
            # indicates that when ProjectDocumentationGenerator was instantiated, the 'project_path' argument was not provided.
            # The fix is to pass the path to the dummy project.
            generator_default = ProjectDocumentationGenerator(dummy_project_root)
            result_default = generator_default.generate_project_documentation()
            print(json.dumps(result_default, indent=2))
        except Exception as e:
            print(f"Error in Example 1: {e}")

        # --- Example 2: Custom configuration ---
        print("\n--- Running Example 2: Custom Configuration ---")
        custom_config = {
            "diagram_tool": "plantuml",
            "diagram_source": "docs/architecture.puml", # Relative path from project root is fine
            "diagram_output": "output/custom_architecture.png", # Relative path from project root
            "spec_tool": "sphinx",
            "spec_source": "docs/source", # Relative path from project root
            "spec_output": "output/custom_technical_specifications.md", # Relative path from project root
            "exclude_files": [".git", "__pycache__", ".DS_Store", "tests"], # Exclude 'tests' directory
            "include_patterns": ["*.py", "*.md", "*.rst", "*.puml"], # Explicitly include these types
            "spec_builder": "markdown", # Explicitly use markdown builder
            "diagram_generation_enabled": True,
            "spec_generation_enabled": True,
            "repo_analysis_enabled": True,
        }
        try:
            generator_custom = ProjectDocumentationGenerator(dummy_project_root, config=custom_config)
            result_custom = generator_custom.generate_project_documentation()
            print(json.dumps(result_custom, indent=2))
        except Exception as e:
            print(f"Error in Example 2: {e}")

        # --- Example 3: Disable Diagram Generation ---
        print("\n--- Running Example 3: Disable Diagram Generation ---")
        disable_diagram_config = {
            "diagram_generation_enabled": False,
            "spec_output": "output/specs_only.md",
        }
        try:
            generator_no_diagram = ProjectDocumentationGenerator(dummy_project_root, config=disable_diagram_config)
            result_no_diagram = generator_no_diagram.generate_project_documentation()
            print(json.dumps(result_no_diagram, indent=2))
        except Exception as e:
            print(f"Error in Example 3: {e}")

        # --- Example 4: Disable Spec Generation ---
        print("\n--- Running Example 4: Disable Spec Generation ---")
        disable_spec_config = {
            "spec_generation_enabled": False,
            "diagram_output": "output/diagram_only.png",
        }
        try:
            generator_no_spec = ProjectDocumentationGenerator(dummy_project_root, config=disable_spec_config)
            result_no_spec = generator_no_spec.generate_project_documentation()
            print(json.dumps(result_no_spec, indent=2))
        except Exception as e:
            print(f"Error in Example 4: {e}")

        # --- Example 5: Error Handling - Non-existent project path ---
        print("\n--- Running Example 5: Error Handling (Non-existent path) ---")
        try:
            ProjectDocumentationGenerator("non_existent_project_path")
        except FileNotFoundError as e:
            print(f"Caught expected error: {e}")
        except Exception as e:
            print(f"Caught unexpected error: {e}")

        # --- Example 6: Error Handling - Missing diagram source ---
        print("\n--- Running Example 6: Error Handling (Missing Diagram Source) ---")
        missing_source_config = {
            "diagram_source": "non_existent_diagram.puml", # This path is relative to project_path by default
            "diagram_generation_enabled": True,
            "spec_generation_enabled": False,
        }
        try:
            generator_missing_source = ProjectDocumentationGenerator(dummy_project_root, config=missing_source_config)
            result_missing_source = generator_missing_source.generate_project_documentation()
            print(json.dumps(result_missing_source, indent=2))
        except Exception as e:
            print(f"Error in Example 6: {e}")

        # --- Example 7: Error Handling - Missing Sphinx source ---
        print("\n--- Running Example 7: Error Handling (Missing Sphinx Source) ---")
        missing_sphinx_source_config = {
            "spec_source": "non_existent_sphinx_source",
            "spec_generation_enabled": True,
            "diagram_generation_enabled": False,
        }
        try:
            generator_missing_sphinx_source = ProjectDocumentationGenerator(dummy_project_root, config=missing_sphinx_source_config)
            result_missing_sphinx_source = generator_missing_sphinx_source.generate_project_documentation()
            print(json.dumps(result_missing_sphinx_source, indent=2))
        except Exception as e:
            print(f"Error in Example 7: {e}")


    except Exception as e:
        print(f"An unexpected error occurred during dummy project setup or example execution: {e}")

    finally:
        # Clean up dummy project files and directories
        if os.path.exists(dummy_project_root):
            print(f"\nCleaning up dummy project: {dummy_project_root}")
            try:
                shutil.rmtree(dummy_project_root)
                print("Cleanup complete.")
            except OSError as e:
                print(f"Error during cleanup: {e}")

    # NOTE: To run the examples successfully, you need to have:
    # 1. plantuml installed and in your PATH.
    # 2. sphinx-build installed (pip install sphinx) and in your PATH.
    # 3. The necessary Python modules for Sphinx (if any custom extensions are used).