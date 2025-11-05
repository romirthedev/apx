import subprocess
import sys
import os
import tempfile
import logging
from pathlib import Path
from typing import Optional, List

logger = logging.getLogger(__name__)

class ScriptRunner:
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / 'apex_scripts'
        self.temp_dir.mkdir(exist_ok=True)
        
        # Security: List of allowed script extensions
        self.allowed_extensions = {'.py', '.sh', '.bash', '.zsh', '.ps1', '.bat', '.js', '.rb'}
    
    def run_script(self, script_path: str) -> str:
        """Run a script file."""
        try:
            path = Path(script_path).expanduser().resolve()
            
            if not path.exists():
                return f"Script not found: {path}"
            
            if not path.is_file():
                return f"Not a file: {path}"
            
            if path.suffix not in self.allowed_extensions:
                return f"Script type not allowed: {path.suffix}"
            
            # Determine how to run the script
            if path.suffix == '.py':
                return self._run_python_file(str(path))
            elif path.suffix in {'.sh', '.bash', '.zsh'}:
                return self._run_bash_file(str(path))
            elif path.suffix in {'.ps1'}:
                return self._run_powershell_file(str(path))
            elif path.suffix in {'.bat'}:
                return self._run_batch_file(str(path))
            elif path.suffix == '.js':
                return self._run_javascript_file(str(path))
            elif path.suffix == '.rb':
                return self._run_ruby_file(str(path))
            else:
                return f"Don't know how to run {path.suffix} files"
            
        except Exception as e:
            logger.error(f"Error running script: {str(e)}")
            return f"Failed to run script: {str(e)}"
    
    def run_python(self, code_or_file: str) -> str:
        """Run Python code or file."""
        try:
            # Check if it's a file path
            if os.path.exists(code_or_file):
                return self._run_python_file(code_or_file)
            else:
                # Treat as code
                return self._run_python_code(code_or_file)
            
        except Exception as e:
            logger.error(f"Error running Python: {str(e)}")
            return f"Failed to run Python code: {str(e)}"
    
    def run_bash(self, command: str) -> str:
        """Run a bash command."""
        try:
            return self._run_bash_command(command)
            
        except Exception as e:
            logger.error(f"Error running bash command: {str(e)}")
            return f"Failed to run bash command: {str(e)}"
    
    def _run_python_code(self, code: str) -> str:
        """Run Python code string."""
        try:
            # Create temporary file
            temp_file = self.temp_dir / f"temp_script_{os.getpid()}.py"
            
            with open(temp_file, 'w') as f:
                f.write(code)
            
            try:
                result = self._run_python_file(str(temp_file))
                return result
            finally:
                # Clean up
                if temp_file.exists():
                    temp_file.unlink()
            
        except Exception as e:
            return f"Error executing Python code: {str(e)}"
    
    def _run_python_file(self, file_path: str) -> str:
        """Run a Python file."""
        try:
            # Use the same Python interpreter
            cmd = [sys.executable, file_path]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,  # 30 second timeout
                cwd=Path(file_path).parent
            )
            
            output = []
            if result.stdout:
                output.append(f"Output:\n{result.stdout}")
            
            if result.stderr:
                output.append(f"Errors:\n{result.stderr}")
            
            if result.returncode != 0:
                output.append(f"Exit code: {result.returncode}")
            
            if not output:
                output.append("Script completed successfully with no output")
            
            return "\n\n".join(output)
            
        except subprocess.TimeoutExpired:
            return "Script execution timed out (30 seconds)"
        except Exception as e:
            return f"Error running Python file: {str(e)}"
    
    def _run_bash_command(self, command: str) -> str:
        """Run a single bash command."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            output = []
            if result.stdout:
                output.append(f"Output:\n{result.stdout}")
            
            if result.stderr:
                output.append(f"Errors:\n{result.stderr}")
            
            if result.returncode != 0:
                output.append(f"Exit code: {result.returncode}")
            
            if not output:
                output.append("Command completed successfully with no output")
            
            return "\n\n".join(output)
            
        except subprocess.TimeoutExpired:
            return "Command execution timed out (30 seconds)"
        except Exception as e:
            return f"Error running bash command: {str(e)}"
    
    def _run_bash_file(self, file_path: str) -> str:
        """Run a bash script file."""
        try:
            cmd = ['/bin/bash', file_path]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=Path(file_path).parent
            )
            
            output = []
            if result.stdout:
                output.append(f"Output:\n{result.stdout}")
            
            if result.stderr:
                output.append(f"Errors:\n{result.stderr}")
            
            if result.returncode != 0:
                output.append(f"Exit code: {result.returncode}")
            
            if not output:
                output.append("Script completed successfully with no output")
            
            return "\n\n".join(output)
            
        except subprocess.TimeoutExpired:
            return "Script execution timed out (30 seconds)"
        except Exception as e:
            return f"Error running bash script: {str(e)}"
    
    def _run_powershell_file(self, file_path: str) -> str:
        """Run a PowerShell script file."""
        try:
            cmd = ['powershell', '-ExecutionPolicy', 'Bypass', '-File', file_path]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=Path(file_path).parent
            )
            
            output = []
            if result.stdout:
                output.append(f"Output:\n{result.stdout}")
            
            if result.stderr:
                output.append(f"Errors:\n{result.stderr}")
            
            if result.returncode != 0:
                output.append(f"Exit code: {result.returncode}")
            
            if not output:
                output.append("Script completed successfully with no output")
            
            return "\n\n".join(output)
            
        except subprocess.TimeoutExpired:
            return "Script execution timed out (30 seconds)"
        except FileNotFoundError:
            return "PowerShell not found. Is it installed?"
        except Exception as e:
            return f"Error running PowerShell script: {str(e)}"
    
    def _run_batch_file(self, file_path: str) -> str:
        """Run a Windows batch file."""
        try:
            cmd = [file_path]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=Path(file_path).parent,
                shell=True
            )
            
            output = []
            if result.stdout:
                output.append(f"Output:\n{result.stdout}")
            
            if result.stderr:
                output.append(f"Errors:\n{result.stderr}")
            
            if result.returncode != 0:
                output.append(f"Exit code: {result.returncode}")
            
            if not output:
                output.append("Script completed successfully with no output")
            
            return "\n\n".join(output)
            
        except subprocess.TimeoutExpired:
            return "Script execution timed out (30 seconds)"
        except Exception as e:
            return f"Error running batch file: {str(e)}"
    
    def _run_javascript_file(self, file_path: str) -> str:
        """Run a JavaScript file with Node.js."""
        try:
            cmd = ['node', file_path]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=Path(file_path).parent
            )
            
            output = []
            if result.stdout:
                output.append(f"Output:\n{result.stdout}")
            
            if result.stderr:
                output.append(f"Errors:\n{result.stderr}")
            
            if result.returncode != 0:
                output.append(f"Exit code: {result.returncode}")
            
            if not output:
                output.append("Script completed successfully with no output")
            
            return "\n\n".join(output)
            
        except subprocess.TimeoutExpired:
            return "Script execution timed out (30 seconds)"
        except FileNotFoundError:
            return "Node.js not found. Is it installed?"
        except Exception as e:
            return f"Error running JavaScript file: {str(e)}"
    
    def _run_ruby_file(self, file_path: str) -> str:
        """Run a Ruby script file."""
        try:
            cmd = ['ruby', file_path]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=Path(file_path).parent
            )
            
            output = []
            if result.stdout:
                output.append(f"Output:\n{result.stdout}")
            
            if result.stderr:
                output.append(f"Errors:\n{result.stderr}")
            
            if result.returncode != 0:
                output.append(f"Exit code: {result.returncode}")
            
            if not output:
                output.append("Script completed successfully with no output")
            
            return "\n\n".join(output)
            
        except subprocess.TimeoutExpired:
            return "Script execution timed out (30 seconds)"
        except FileNotFoundError:
            return "Ruby not found. Is it installed?"
        except Exception as e:
            return f"Error running Ruby script: {str(e)}"
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported scripting languages."""
        return [
            "Python (.py)",
            "Bash/Shell (.sh, .bash, .zsh)",
            "PowerShell (.ps1)",
            "Batch (.bat)",
            "JavaScript (.js) - requires Node.js",
            "Ruby (.rb) - requires Ruby"
        ]
