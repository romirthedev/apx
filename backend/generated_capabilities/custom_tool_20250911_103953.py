
import subprocess
import shlex
from typing import Dict, Any, Optional, List, Union

class AdvancedCommandExecutor:
    """
    A specialized tool for executing complex, multi-word command-line actions
    with detailed instructions, designed for macOS compatibility.

    This class provides a safe and structured way to run external commands,
    returning detailed results in a dictionary format. It emphasizes clarity,
    robustness, and user-friendliness for handling diverse command execution needs.
    """

    def __init__(self, default_shell: str = "/bin/zsh"):
        """
        Initializes the AdvancedCommandExecutor.

        Args:
            default_shell: The default shell to use for executing commands.
                           Defaults to '/bin/zsh' for macOS.
        """
        if not isinstance(default_shell, str) or not default_shell:
            raise ValueError("default_shell must be a non-empty string.")
        self.default_shell = default_shell

    def _validate_command_execution_params(
        self,
        command: str,
        input_data: Optional[str],
        timeout: Optional[int],
        capture_output: bool,
        text_mode: bool,
        shell_mode: bool,
        environment: Optional[Dict[str, str]]
    ) -> None:
        """Internal helper to validate parameters for execute_detailed_command."""
        if not isinstance(command, str) or not command:
            raise ValueError("command must be a non-empty string.")
        if input_data is not None and not isinstance(input_data, (str, bytes)):
            raise ValueError("input_data must be a string or bytes, or None.")
        if timeout is not None and not isinstance(timeout, int):
            raise ValueError("timeout must be an integer or None.")
        if not isinstance(capture_output, bool):
            raise ValueError("capture_output must be a boolean.")
        if not isinstance(text_mode, bool):
            raise ValueError("text_mode must be a boolean.")
        if not isinstance(shell_mode, bool):
            raise ValueError("shell_mode must be a boolean.")
        if environment is not None and not isinstance(environment, dict):
            raise ValueError("environment must be a dictionary or None.")
        if environment:
            for key, value in environment.items():
                if not isinstance(key, str) or not isinstance(value, str):
                    raise ValueError("environment keys and values must be strings.")

    def execute_detailed_command(
        self,
        command: str,
        input_data: Optional[Union[str, bytes]] = None,
        timeout: Optional[int] = None,
        capture_output: bool = True,
        text_mode: bool = True,
        shell_mode: bool = True,
        environment: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Executes a potentially very long and detailed command with optional input.

        This method is designed to handle complex commands that might span
        multiple words and require specific execution parameters. It ensures
        safe execution by not performing system modifications without explicit
        user action via the command itself. It provides comprehensive error
        reporting.

        Args:
            command: The full command string to execute. This can include
                     arguments, options, and redirection. For `shell_mode=True`,
                     this is passed directly to the shell. For `shell_mode=False`,
                     it's treated as a list of arguments if `command` is a string,
                     or expected to be a list of strings.
            input_data: Optional data to be passed as standard input to the command.
                        Can be str (if text_mode=True) or bytes (if text_mode=False).
                        Defaults to None.
            timeout: Optional timeout in seconds for the command execution.
                     If None, the command will run until completion or an external
                     interrupt. Defaults to None.
            capture_output: Whether to capture stdout and stderr. Defaults to True.
            text_mode: If True, stdin, stdout, and stderr are treated as text.
                       If False, they are treated as bytes. Defaults to True.
            shell_mode: If True, the command is executed through the shell.
                        This is generally required for complex commands with
                        pipes, redirections, environment variable expansions, etc.
                        Defaults to True. If False, `command` should be a list
                        of strings.
            environment: A dictionary of environment variables to set for the
                         command. If None, inherits the current environment.
                         Defaults to None.

        Returns:
            A dictionary containing the execution results:
            {
                'success': bool,          # True if the command exited with status 0, False otherwise.
                'message': str,           # A descriptive message about the outcome or error.
                'returncode': Optional[int], # The exit code of the command, None if execution failed before run.
                'stdout': Optional[str],  # Captured standard output (if capture_output=True and text_mode=True).
                'stderr': Optional[str],  # Captured standard error (if capture_output=True and text_mode=True).
                'stdout_bytes': Optional[bytes], # Captured standard output (if capture_output=True and text_mode=False).
                'stderr_bytes': Optional[bytes]  # Captured standard error (if capture_output=True and text_mode=False).
            }
        """
        self._validate_command_execution_params(
            command, input_data, timeout, capture_output, text_mode, shell_mode, environment
        )

        # Ensure input_data type matches text_mode
        if text_mode and isinstance(input_data, bytes):
            input_data = input_data.decode('utf-8', errors='replace')
        elif not text_mode and isinstance(input_data, str):
            input_data = input_data.encode('utf-8')

        try:
            process = subprocess.run(
                command,
                shell=shell_mode,
                input=input_data,
                timeout=timeout,
                capture_output=capture_output,
                text=text_mode,
                env=environment,
                executable=self.default_shell if shell_mode else None,
                check=False # Do not raise CalledProcessError on non-zero exit codes
            )

            result_base = {
                'returncode': process.returncode,
                'stdout': process.stdout if capture_output and text_mode else None,
                'stderr': process.stderr if capture_output and text_mode else None,
                'stdout_bytes': process.stdout if capture_output and not text_mode else None,
                'stderr_bytes': process.stderr if capture_output and not text_mode else None,
            }

            if process.returncode == 0:
                return {
                    'success': True,
                    'message': "Command executed successfully.",
                    **result_base
                }
            else:
                error_message = f"Command failed with exit code {process.returncode}."
                if process.stderr:
                    error_message += f" Stderr: {process.stderr}"
                elif process.stdout and not process.stderr and process.returncode != 0:
                    # Sometimes error messages are printed to stdout for specific commands
                    error_message += f" Stdout (may contain error info): {process.stdout}"

                return {
                    'success': False,
                    'message': error_message,
                    **result_base
                }

        except FileNotFoundError:
            # This occurs if the executable itself is not found when shell_mode=False
            # or if the shell is not found. For shell_mode=True, the shell typically
            # handles "command not found" with a non-zero exit code, which is caught above.
            cmd_name = command.split()[0] if isinstance(command, str) and command else "command"
            return {
                'success': False,
                'message': f"Error: Executable '{cmd_name}' not found. Ensure it's in your system's PATH or that the command is correctly specified.",
                'returncode': None,
                'stdout': None,
                'stderr': None,
                'stdout_bytes': None,
                'stderr_bytes': None,
            }
        except subprocess.TimeoutExpired as e:
            return {
                'success': False,
                'message': f"Command timed out after {timeout} seconds.",
                'returncode': None,
                'stdout': e.stdout.decode('utf-8', errors='replace') if e.stdout and text_mode else e.stdout,
                'stderr': e.stderr.decode('utf-8', errors='replace') if e.stderr and text_mode else e.stderr,
                'stdout_bytes': e.stdout if e.stdout and not text_mode else None,
                'stderr_bytes': e.stderr if e.stderr and not text_mode else None,
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"An unexpected error occurred during command execution: {type(e).__name__}: {e}",
                'returncode': None,
                'stdout': None,
                'stderr': None,
                'stdout_bytes': None,
                'stderr_bytes': None,
            }

    def run_with_detailed_instructions(
        self,
        action_description: str,
        command_template: str,
        arguments: List[str],
        input_data: Optional[Union[str, bytes]] = None,
        timeout: Optional[int] = None,
        environment: Optional[Dict[str, str]] = None,
        shell_mode: bool = True  # Added for flexibility, default to True for complex commands
    ) -> Dict[str, Any]:
        """
        Executes a command based on a template and provided arguments,
        incorporating a descriptive action. This is the primary method for
        handling "long action commands" with detailed instructions.

        This method constructs the final command string and then executes it
        using `execute_detailed_command`. It is designed to interpret and
        execute arbitrary 'long action commands' with detailed instructions,
        which may involve custom logic or parsing beyond the scope of
        predefined actions, by leveraging the shell's power.

        Args:
            action_description: A human-readable description of the action being performed.
                                This is crucial for logging and user feedback, and is
                                included in the output message.
            command_template: A string template for the command. Placeholders for
                              arguments should be marked with '{0}', '{1}', etc.
                              Example: "echo 'Processing file {0}' | xargs -I {} processing_script.sh {}"
                              This template is formatted using Python's `str.format()`.
            arguments: A list of strings to be formatted into the command_template.
                       The order of arguments must match the placeholders in the template.
                       Special characters within arguments are handled by `str.format`.
                       If `shell_mode` is True, the shell will interpret these arguments
                       within the constructed command.
            input_data: Optional data to be passed as standard input to the command.
                        Can be str (if text_mode=True) or bytes (if text_mode=False).
                        Defaults to None.
            timeout: Optional timeout in seconds for the command execution.
            environment: A dictionary of environment variables to set for the command.
            shell_mode: Whether to execute the command through the shell. Defaults to True,
                        which is generally recommended for complex, multi-part commands.
                        If False, `command_template` must not contain shell syntax
                        and `arguments` should be safely quoted if they contain spaces or
                        special characters that need to be passed as single arguments.
                        However, `str.format` does not inherently quote for shell
                        if `shell_mode=False`, making manual quoting necessary if needed.
                        For "long action commands" with detailed instructions, `shell_mode=True`
                        is usually the most flexible and intended approach.

        Returns:
            A dictionary containing the execution results from `execute_detailed_command`.
            The 'message' field will include the action description for context.
        """
        if not isinstance(action_description, str) or not action_description:
            raise ValueError("action_description must be a non-empty string.")
        if not isinstance(command_template, str) or not command_template:
            raise ValueError("command_template must be a non-empty string.")
        if not isinstance(arguments, list):
            raise ValueError("arguments must be a list of strings.")
        for arg in arguments:
            if not isinstance(arg, str):
                raise ValueError("All elements in the 'arguments' list must be strings.")
        if not isinstance(shell_mode, bool):
            raise ValueError("shell_mode must be a boolean.")

        try:
            # Construct the command using str.format. This is generally safe for
            # interpolating Python strings. If the command_template itself contained
            # format specifiers that should not be processed, a different templating
            # approach or explicit escaping would be needed. For the purpose of
            # user-provided "long action commands", str.format is suitable.
            full_command = command_template.format(*arguments)

            # For shell_mode=False, the `subprocess.run` expects a list.
            # If shell_mode is True, it expects a string.
            command_for_subprocess = full_command if shell_mode else shlex.split(full_command)
            # shlex.split is used here to attempt to correctly parse the formatted command
            # into a list of arguments if shell_mode is False. However, complex shell
            # constructs might not be perfectly handled by shlex.split if shell_mode=False.
            # It's generally safer to use shell_mode=True for complex commands.

            result = self.execute_detailed_command(
                command=command_for_subprocess,
                input_data=input_data,
                timeout=timeout,
                capture_output=True,
                text_mode=True, # Defaulting to text mode for user-friendly output
                shell_mode=shell_mode,
                environment=environment
            )

            # Enhance the message with the action description
            if result['success']:
                result['message'] = f"Action: '{action_description}' executed successfully. {result['message']}"
            else:
                result['message'] = f"Action: '{action_description}' failed. {result['message']}"

            return result

        except IndexError:
            # Calculate the number of expected placeholders more robustly
            expected_placeholders = command_template.count('{') + command_template.count('}')
            # A simple count of '{' might be sufficient if assuming balanced placeholders.
            # More sophisticated parsing could be used if needed.
            num_placeholders = command_template.count('{}') # If using simple {}
            if num_placeholders == 0 and command_template.count('{') > 0: # Handle {0}, {1} etc.
                # A basic heuristic for {0}, {1}... format specifiers
                try:
                    import re
                    num_placeholders = len(re.findall(r'\{\d+\}', command_template))
                except ImportError:
                    pass # Fallback if re is not available

            return {
                'success': False,
                'message': f"Error: Argument mismatch for command template '{command_template}'. Expected placeholders for {num_placeholders} arguments, but {len(arguments)} were provided.",
                'returncode': None,
                'stdout': None,
                'stderr': None,
                'stdout_bytes': None,
                'stderr_bytes': None,
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"An unexpected error occurred while preparing or executing the command for action '{action_description}': {type(e).__name__}: {e}",
                'returncode': None,
                'stdout': None,
                'stderr': None,
                'stdout_bytes': None,
                'stderr_bytes': None,
            }

if __name__ == '__main__':
    # Example Usage
    executor = AdvancedCommandExecutor()

    # 1. Simple command
    print("--- Example 1: Simple Command ---")
    result1 = executor.execute_detailed_command("ls -l")
    print(result1)
    print("\n")

    # 2. Command with arguments and stderr
    print("--- Example 2: Command with stderr ---")
    result2 = executor.execute_detailed_command("ls /nonexistent_directory")
    print(result2)
    print("\n")

    # 3. Command with input and pipes (shell mode is crucial here)
    print("--- Example 3: Command with input and pipes ---")
    input_text = "hello world\nthis is a test\nend of input"
    command_with_pipes = "grep test | wc -l"
    result3 = executor.execute_detailed_command(command_with_pipes, input_data=input_text)
    print(result3)
    print("\n")

    # 4. Using run_with_detailed_instructions (simple template)
    print("--- Example 4: Using run_with_detailed_instructions (simple template) ---")
    action_desc_simple = "Count lines in output of 'ls -la ~'."
    cmd_template_simple = "ls -la ~ | wc -l"
    args_list_simple = [] # No arguments needed for this specific template
    result4 = executor.run_with_detailed_instructions(
        action_description=action_desc_simple,
        command_template=cmd_template_simple,
        arguments=args_list_simple
    )
    print(result4)
    print("\n")

    # 5. Using run_with_detailed_instructions with arguments and input
    # This demonstrates a more "long action command" scenario.
    print("--- Example 5: Complex command with arguments and input ---")
    action_desc_complex = "Create a temporary file with specific content, display it, and then clean up."
    # The command template itself is quite detailed, using shell features like && and redirection.
    cmd_template_complex = "echo 'Processing file for task {0}' && echo '{1}' > /tmp/{0}.txt && cat /tmp/{0}.txt && echo '--- Cleanup ---' && rm /tmp/{0}.txt"
    args_complex = ["my_unique_task_id_12345", "This is the actual content for the temporary file. It can be quite long and detailed."]
    result5 = executor.run_with_detailed_instructions(
        action_description=action_desc_complex,
        command_template=cmd_template_complex,
        arguments=args_complex
    )
    print(result5)
    print("\n")

    # 6. Command with timeout
    print("--- Example 6: Command with timeout ---")
    # This command will likely hang indefinitely without a timeout.
    # Using a short timeout to demonstrate the TimeoutExpired exception.
    result6 = executor.execute_detailed_command("sleep 5", timeout=2)
    print(result6)
    print("\n")

    # 7. Command not found (demonstrates improved FileNotFoundError handling)
    print("--- Example 7: Command not found ---")
    result7 = executor.execute_detailed_command("this_command_definitely_does_not_exist_12345")
    print(result7)
    print("\n")

    # 8. Mismatched arguments for run_with_detailed_instructions
    print("--- Example 8: Mismatched arguments for run_with_detailed_instructions ---")
    action_desc_mismatch = "Attempt to run command with too few arguments."
    cmd_template_mismatch = "echo 'Arg1: {0}, Arg2: {1}, Arg3: {2}'"
    args_mismatch = ["only_one_arg", "second_arg"] # Missing third argument
    result8 = executor.run_with_detailed_instructions(
        action_description=action_desc_mismatch,
        command_template=cmd_template_mismatch,
        arguments=args_mismatch
    )
    print(result8)
    print("\n")

    # 9. Executing as bytes
    print("--- Example 9: Executing as bytes ---")
    result9 = executor.execute_detailed_command("echo -n 'Hello Bytes'", text_mode=False)
    print(f"Success: {result9['success']}")
    print(f"Stdout (bytes): {result9['stdout_bytes']}")
    print(f"Stderr (bytes): {result9['stderr_bytes']}")
    print("\n")

    # 10. Long action command with complex instructions and piping
    print("--- Example 10: Long action command with complex instructions and piping ---")
    action_desc_long = "Find all Python files modified in the last 7 days, extract their names, and count the lines of code in each."
    # This command is an example of a detailed instruction set:
    # find . -name "*.py" -mtime -7 -print0 | xargs -0 wc -l
    cmd_template_long = 'find . -name "*.py" -mtime -7 -print0 | xargs -0 wc -l'
    args_long = [] # No arguments needed for this template, it's self-contained.
    result10 = executor.run_with_detailed_instructions(
        action_description=action_desc_long,
        command_template=cmd_template_long,
        arguments=args_long,
        shell_mode=True # Explicitly true, but it's the default and necessary for pipes/xargs
    )
    print(result10)
    print("\n")

    # 11. Demonstrating invalid input parameters
    print("--- Example 11: Demonstrating invalid input parameters ---")
    try:
        executor.execute_detailed_command(command=123) # Invalid command type
    except ValueError as e:
        print(f"Caught expected error: {e}")

    try:
        executor.run_with_detailed_instructions(
            action_description="Test",
            command_template="echo {0}",
            arguments=["hello"],
            timeout="invalid" # Invalid timeout type
        )
    except ValueError as e:
        print(f"Caught expected error: {e}")
    print("\n")
