import os
import json
import logging
import subprocess
import tempfile
import importlib.util
import sys
import re
import traceback
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import ast
import inspect
from .dynamic_tool_generator import DynamicToolGenerator
from .tool_testing_framework import ToolTestingFramework

logger = logging.getLogger(__name__)

class SelfImprovementEngine:
    """AI system that can detect capability gaps and write code to fill them."""
    
    def __init__(self, gemini_ai, security_manager, max_iterations=5, enable_trajectory=True):
        self.gemini_ai = gemini_ai
        self.security_manager = security_manager
        self.capabilities_registry = {}
        self.generated_modules = {}
        self.capability_cache = {}
        
        # Directory for storing generated code
        self.generated_code_dir = os.path.join(os.path.dirname(__file__), '..', 'generated_capabilities')
        os.makedirs(self.generated_code_dir, exist_ok=True)
        
        # Trae Agent-inspired configuration
        self.max_iterations = max_iterations
        self.enable_trajectory = enable_trajectory
        self.trajectory = []
        self.current_iteration = 0
        
        # Initialize dynamic tool generator and testing framework
        self.tool_generator = DynamicToolGenerator(gemini_ai, security_manager)
        self.testing_framework = ToolTestingFramework(security_manager)
        
        # Load existing capabilities
        self._load_existing_capabilities()
    
    def _record_trajectory_step(self, step_type, description, inputs=None, outputs=None, success=True, error=None):
        """Record a step in the trajectory for debugging and analysis."""
        if not self.enable_trajectory:
            return
            
        step = {
            'iteration': self.current_iteration,
            'step_type': step_type,
            'description': description,
            'timestamp': datetime.now().isoformat(),
            'inputs': inputs,
            'outputs': outputs,
            'success': success,
            'error': str(error) if error else None
        }
        self.trajectory.append(step)
        print(f"📝 Step {len(self.trajectory)}: {description}")

    def _analyze_trajectory(self):
        """Analyze the trajectory to determine next steps."""
        if not self.trajectory:
            return "No previous attempts to analyze."
            
        recent_steps = self.trajectory[-3:]  # Last 3 steps
        failures = [step for step in recent_steps if not step['success']]
        
        if len(failures) >= 2:
            return f"Multiple recent failures detected. Last errors: {[f['error'] for f in failures]}"
        
        return "Trajectory analysis: Ready for next iteration."

    def _should_continue_iteration(self, last_result):
        """Determine if we should continue iterating based on Trae Agent principles."""
        if self.current_iteration >= self.max_iterations:
            return False, "Maximum iterations reached"
            
        if last_result and last_result.get('success'):
            return False, "Task completed successfully"
            
        # Check trajectory for patterns
        if len(self.trajectory) > 0:
            recent_failures = [step for step in self.trajectory[-2:] if not step['success']]
            if len(recent_failures) >= 2:
                return False, "Too many consecutive failures"
                
        return True, "Continue iteration"

    def assess_capability_gap(self, user_request: str, available_actions: List[str]) -> Dict[str, Any]:
        """Assess if the AI has the capability to handle the user request."""
        
        # Check cache first
        cache_key = f"{user_request}_{hash(str(sorted(available_actions)))}"
        if cache_key in self.capability_cache:
            return self.capability_cache[cache_key]
        
        # First, check for basic commands that should always be handled by existing AI
        basic_commands = [
            'open', 'launch', 'start', 'close', 'quit', 'exit',
            'create file', 'delete file', 'edit file', 'find file', 'search file',
            'list files', 'show files', 'display files',
            'run command', 'execute', 'terminal', 'bash', 'shell',
            'system info', 'system status', 'date', 'time',
            'help', 'what can you do', 'capabilities'
        ]
        
        user_lower = user_request.lower()
        if any(cmd in user_lower for cmd in basic_commands):
            return {
                "can_handle": True,
                "confidence": 0.95,
                "missing_capability": None,
                "required_functions": [],
                "complexity_level": "simple",
                "estimated_lines_of_code": 0
            }
        
        assessment_prompt = f"""
Analyze this user request and determine if it requires SPECIALIZED NEW CODE GENERATION:

User Request: {user_request}
Available Actions: {available_actions}
Existing Capabilities: {list(self.capabilities_registry.keys())}

IMPORTANT: Only set can_handle=false for tasks that CLEARLY require:
- Specialized libraries (ML, crypto, image processing, etc.)
- Complex API integrations not already available
- Domain-specific algorithms or data processing
- Custom file format handling
- Advanced mathematical computations

Basic tasks should return can_handle=true:
- File operations (create, edit, delete, search)
- Application control (open, close, switch)
- System commands (ls, find, grep, etc.)
- Web browsing and searching
- Simple data manipulation
- Basic automation tasks

Respond with JSON in this format:
{{
    "can_handle": true/false,
    "confidence": 0.0-1.0,
    "missing_capability": "description of what's missing or null if can handle",
    "required_functions": ["list of specific functions/libraries needed"],
    "complexity_level": "simple/medium/complex",
    "estimated_lines_of_code": number
}}

Be CONSERVATIVE: Only trigger self-improvement for truly complex, specialized tasks.
"""
        
        try:
            response = self.gemini_ai.model.generate_content(assessment_prompt)
            response_text = response.text.strip()
            
            # Handle empty or malformed responses
            if not response_text:
                logger.warning("Empty response from Gemini AI for capability assessment")
                return self._get_default_assessment("Empty AI response")
            
            # Try to extract JSON from response (in case it's wrapped in markdown)
            json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)
            
            # Parse JSON
            assessment = json.loads(response_text)
            
            # Validate required fields
            required_fields = ['can_handle', 'confidence', 'missing_capability', 'required_functions']
            for field in required_fields:
                if field not in assessment:
                    logger.warning(f"Missing field '{field}' in assessment response")
                    return self._get_default_assessment(f"Missing field: {field}")
            
            # Cache the result
            self.capability_cache[cache_key] = assessment
            
            logger.info(f"Capability assessment: {assessment}")
            return assessment
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in capability assessment: {str(e)}")
            logger.error(f"Raw response: {response.text if 'response' in locals() else 'No response'}")
            return self._get_default_assessment("JSON parsing failed")
        except Exception as e:
            logger.error(f"Error in capability assessment: {str(e)}")
            return self._get_default_assessment("Assessment failed")
    
    def _get_default_assessment(self, reason: str) -> Dict[str, Any]:
        """Return a default assessment when the AI assessment fails."""
        return {
            "can_handle": True,  # Default to assuming we can handle it
            "confidence": 0.5,
            "missing_capability": reason,
            "required_functions": [],
            "complexity_level": "unknown",
            "estimated_lines_of_code": 0
        }
    
    def generate_capability_code(self, missing_capability: str, required_functions: List[str], user_request: str) -> Tuple[str, str]:
        """Generate Python code to implement the missing capability using the dynamic tool generator."""
        
        try:
            # Use the dynamic tool generator to create the capability
            generated_code, module_name = self.tool_generator.generate_specialized_tool(
                user_request=user_request,
                tool_type=None  # Let it auto-detect
            )
            
            # Enhance the tool with specific context if needed
            context = {
                'missing_capability': missing_capability,
                'required_functions': required_functions
            }
            
            enhanced_code = self.tool_generator.enhance_tool_with_context(
                base_code=generated_code,
                user_request=user_request,
                context=context
            )
            
            logger.info(f"Generated code for capability using dynamic tool generator: {missing_capability}")
            return enhanced_code, module_name
            
        except Exception as e:
            logger.error(f"Error generating capability code: {str(e)}")
            # Fallback to original method if dynamic tool generator fails
            return self._fallback_generate_capability_code(missing_capability, required_functions, user_request)
    
    def _fallback_generate_capability_code(self, missing_capability: str, required_functions: List[str], user_request: str) -> Tuple[str, str]:
        """Fallback method for generating capability code when dynamic tool generator fails."""
        
        code_generation_prompt = f"""
Generate Python code to implement the missing capability:

Missing Capability: {missing_capability}
Required Functions: {required_functions}
Original User Request: {user_request}

Generate a complete Python module with:
1. All necessary imports
2. A main class that implements the capability
3. Clear method names and docstrings
4. Error handling
5. Return values that can be easily used by other systems

The code should be production-ready and follow these guidelines:
- Use type hints
- Include proper error handling
- Make it compatible with macOS
- Avoid dangerous operations (no system modifications without explicit permission)
- Return structured data (dicts, lists) when possible

Provide ONLY the Python code, no explanations:
"""
        
        try:
            response = self.gemini_ai.model.generate_content(code_generation_prompt)
            generated_code = response.text.strip()
            
            # Clean up the code (remove markdown formatting if present)
            if generated_code.startswith('```python'):
                generated_code = generated_code[9:]
            if generated_code.endswith('```'):
                generated_code = generated_code[:-3]
            
            # Generate a module name
            module_name = f"capability_{len(self.generated_modules)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            logger.info(f"Generated code for capability using fallback method: {missing_capability}")
            return generated_code, module_name
            
        except Exception as e:
            logger.error(f"Error generating capability code with fallback method: {str(e)}")
            raise
    
    def validate_and_execute_code(self, code: str, module_name: str, max_retries: int = 3) -> Tuple[bool, Any, str]:
        """Validate and safely execute the generated code with recursive self-improvement."""
        
        for attempt in range(max_retries):
            try:
                # First, validate the syntax
                try:
                    ast.parse(code)
                except SyntaxError as e:
                    if attempt < max_retries - 1:
                        logger.info(f"Syntax error detected, attempting self-correction (attempt {attempt + 1}/{max_retries})")
                        code = self._fix_syntax_error(code, str(e))
                        continue
                    return False, None, f"Syntax error in generated code: {str(e)}"
                
                # Security check - basic validation
                dangerous_patterns = [
                    'os.system', 'subprocess.call', 'eval(', 'exec(',
                    '__import__', 'open(', 'file(', 'input(',
                    'raw_input(', 'compile(', 'reload('
                ]
                
                for pattern in dangerous_patterns:
                    if pattern in code:
                        logger.warning(f"Potentially dangerous pattern detected: {pattern}")
                        # For now, we'll allow it but log it
                
                # Save the code to a file
                module_file = os.path.join(self.generated_code_dir, f"{module_name}.py")
                with open(module_file, 'w') as f:
                    f.write(code)
                
                # Try to import and instantiate the module
                spec = importlib.util.spec_from_file_location(module_name, module_file)
                module = importlib.util.module_from_spec(spec)
                
                # Add to sys.modules to make it importable
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                
                # Find the main class in the module
                main_class = None
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and obj.__module__ == module_name:
                        main_class = obj
                        break
                
                if main_class is None:
                    if attempt < max_retries - 1:
                        logger.info(f"No main class found, attempting self-correction (attempt {attempt + 1}/{max_retries})")
                        code = self._fix_missing_class(code)
                        continue
                    return False, None, "No main class found in generated module"
                
                # Instantiate the class
                instance = main_class()
                
                # Store the module and instance
                self.generated_modules[module_name] = {
                    'module': module,
                    'instance': instance,
                    'file_path': module_file,
                    'created_at': datetime.now().isoformat()
                }
                
                logger.info(f"Successfully loaded and instantiated module: {module_name}")
                return True, instance, "Module loaded successfully"
                
            except ImportError as e:
                if attempt < max_retries - 1:
                    logger.info(f"Import error detected, attempting self-correction (attempt {attempt + 1}/{max_retries})")
                    code = self._fix_import_error(code, str(e))
                    continue
                logger.error(f"Import error after {max_retries} attempts: {str(e)}")
                return False, None, f"Import error: {str(e)}"
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.info(f"Execution error detected, attempting self-correction (attempt {attempt + 1}/{max_retries})")
                    code = self._fix_execution_error(code, str(e))
                    continue
                logger.error(f"Error validating/executing code after {max_retries} attempts: {str(e)}")
            return False, None, f"Execution error: {str(e)}"
    
    def _fix_syntax_error(self, code: str, error_message: str) -> str:
        """Attempt to fix syntax errors in generated code."""
        try:
            fix_prompt = f"""
The following Python code has a syntax error:

ERROR: {error_message}

CODE:
{code}

Please fix the syntax error and return the corrected code. Provide ONLY the corrected Python code, no explanations:
"""
            response = self.gemini_ai.model.generate_content(fix_prompt)
            fixed_code = response.text.strip()
            
            # Clean up the code (remove markdown formatting if present)
            if fixed_code.startswith('```python'):
                fixed_code = fixed_code[9:]
            if fixed_code.endswith('```'):
                fixed_code = fixed_code[:-3]
            
            logger.info("Generated syntax error fix")
            return fixed_code.strip()
        except Exception as e:
            logger.error(f"Failed to fix syntax error: {str(e)}")
            return code  # Return original code if fix fails
    
    def _fix_import_error(self, code: str, error_message: str) -> str:
        """Attempt to fix import errors in generated code."""
        try:
            fix_prompt = f"""
The following Python code has an import error:

ERROR: {error_message}

CODE:
{code}

Please fix the import error by:
1. Adding missing import statements
2. Using alternative libraries if the required one is not available
3. Implementing fallback functionality if needed
4. Installing required packages is not an option - work with what's available

Provide ONLY the corrected Python code, no explanations:
"""
            response = self.gemini_ai.model.generate_content(fix_prompt)
            fixed_code = response.text.strip()
            
            # Clean up the code (remove markdown formatting if present)
            if fixed_code.startswith('```python'):
                fixed_code = fixed_code[9:]
            if fixed_code.endswith('```'):
                fixed_code = fixed_code[:-3]
            
            logger.info("Generated import error fix")
            return fixed_code.strip()
        except Exception as e:
            logger.error(f"Failed to fix import error: {str(e)}")
            return code  # Return original code if fix fails
    
    def _fix_missing_class(self, code: str) -> str:
        """Attempt to fix missing main class in generated code."""
        try:
            fix_prompt = f"""
The following Python code is missing a main class:

CODE:
{code}

Please add a main class that implements the required functionality. The class should:
1. Have a clear, descriptive name
2. Implement the core functionality as methods
3. Be properly structured and documented

Provide ONLY the corrected Python code with the main class, no explanations:
"""
            response = self.gemini_ai.model.generate_content(fix_prompt)
            fixed_code = response.text.strip()
            
            # Clean up the code (remove markdown formatting if present)
            if fixed_code.startswith('```python'):
                fixed_code = fixed_code[9:]
            if fixed_code.endswith('```'):
                fixed_code = fixed_code[:-3]
            
            logger.info("Generated missing class fix")
            return fixed_code.strip()
        except Exception as e:
            logger.error(f"Failed to fix missing class: {str(e)}")
            return code  # Return original code if fix fails
    
    def _fix_execution_error(self, code: str, error_message: str) -> str:
        """Attempt to fix general execution errors in generated code."""
        try:
            fix_prompt = f"""
The following Python code has an execution error:

ERROR: {error_message}

CODE:
{code}

Please fix the execution error by:
1. Correcting any logical errors
2. Adding proper error handling
3. Fixing variable references and scope issues
4. Ensuring all required methods and attributes exist

Provide ONLY the corrected Python code, no explanations:
"""
            response = self.gemini_ai.model.generate_content(fix_prompt)
            fixed_code = response.text.strip()
            
            # Clean up the code (remove markdown formatting if present)
            if fixed_code.startswith('```python'):
                fixed_code = fixed_code[9:]
            if fixed_code.endswith('```'):
                fixed_code = fixed_code[:-3]
            
            logger.info("Generated execution error fix")
            return fixed_code.strip()
        except Exception as e:
            logger.error(f"Failed to fix execution error: {str(e)}")
            return code  # Return original code if fix fails
    
    def use_new_capability(self, module_name: str, method_name: str, *args, **kwargs) -> Any:
        """Use a newly generated capability."""
        
        if module_name not in self.generated_modules:
            raise ValueError(f"Module {module_name} not found")
        
        instance = self.generated_modules[module_name]['instance']
        
        if not hasattr(instance, method_name):
            raise ValueError(f"Method {method_name} not found in module {module_name}")
        
        method = getattr(instance, method_name)
        return method(*args, **kwargs)
    
    def iterative_self_improve_for_task(self, user_request: str, available_actions: List[str], progress_callback=None) -> Dict[str, Any]:
        """Trae Agent-inspired iterative self-improvement with multi-step reasoning and progress callbacks."""
        print(f"🚀 Starting iterative self-improvement (max {self.max_iterations} iterations)")
        self.current_iteration = 0
        self.trajectory = []
        
        # Send initial progress update
        if progress_callback:
            progress_callback("initialization", "🔍 Analyzing your request and detecting missing capabilities...")
        
        # Record initial assessment
        self._record_trajectory_step(
            'assessment', 
            'Initial capability assessment',
            inputs={'request': user_request, 'actions': available_actions}
        )
        
        last_result = None
        
        while True:
            self.current_iteration += 1
            print(f"\n🔄 Iteration {self.current_iteration}/{self.max_iterations}")
            
            if progress_callback:
                progress_callback(
                    f"iteration_{self.current_iteration}", 
                    f"🔧 Generating tool (attempt {self.current_iteration}/{self.max_iterations})...",
                    {"iteration": self.current_iteration, "max_iterations": self.max_iterations}
                )
            
            # Check if we should continue
            should_continue, reason = self._should_continue_iteration(last_result)
            if not should_continue:
                print(f"🛑 Stopping iteration: {reason}")
                break
                
            # Analyze trajectory for insights
            trajectory_analysis = self._analyze_trajectory()
            print(f"📊 Trajectory analysis: {trajectory_analysis}")
            
            # Perform one iteration of self-improvement
            try:
                result = self._single_improvement_iteration(user_request, available_actions, trajectory_analysis, progress_callback)
                last_result = result
                
                self._record_trajectory_step(
                    'improvement_iteration',
                    f'Iteration {self.current_iteration} completed',
                    outputs=result,
                    success=result.get('success', False)
                )
                
                # If successful, check if comprehensive testing was already done
                if result.get('success') and not result.get('used_existing_capability'):
                    if progress_callback:
                        progress_callback("testing", "✅ Tool generated successfully! Testing functionality...")
                    
                    # Use comprehensive test results if available, otherwise fall back to basic test
                    if 'test_results' in result:
                        test_result = result['test_results']
                        if test_result.get('success'):
                            print("✅ Generated capability tested successfully with comprehensive tests!")
                            result['test_result'] = test_result
                            if progress_callback:
                                progress_callback("success", "🎉 Tool is ready and working!")
                            break
                        else:
                            print(f"⚠️ Generated capability failed comprehensive testing: {test_result.get('error')}")
                            result['success'] = False
                            result['test_error'] = test_result.get('error')
                            if progress_callback:
                                progress_callback("test_failed", f"❌ Tool test failed: {test_result.get('error', 'Unknown error')[:100]}...")
                    else:
                        # Fall back to basic test if comprehensive tests weren't run
                        test_result = self._test_generated_capability(result)
                        if test_result.get('success'):
                            print("✅ Generated capability tested successfully!")
                            result['test_result'] = test_result
                            if progress_callback:
                                progress_callback("success", "🎉 Tool is ready and working!")
                            break
                        else:
                            print(f"⚠️ Generated capability failed testing: {test_result.get('error')}")
                            result['success'] = False
                            result['test_error'] = test_result.get('error')
                            if progress_callback:
                                progress_callback("test_failed", f"❌ Tool test failed: {test_result.get('error', 'Unknown error')[:100]}...")
                        
            except Exception as e:
                error_msg = f"Iteration {self.current_iteration} failed: {str(e)}"
                print(f"❌ {error_msg}")
                if progress_callback:
                    progress_callback(
                        "iteration_failed", 
                        f"❌ Attempt {self.current_iteration} failed: {str(e)[:100]}...",
                        {"error": str(e), "iteration": self.current_iteration}
                    )
                self._record_trajectory_step(
                    'iteration_error',
                    error_msg,
                    success=False,
                    error=e
                )
                last_result = {'success': False, 'error': error_msg}
        
        # Final summary
        if last_result and last_result.get('success'):
            print(f"🎉 Iterative self-improvement completed successfully in {self.current_iteration} iterations!")
        else:
            print(f"⚠️ Iterative self-improvement completed with limitations after {self.current_iteration} iterations")
            if progress_callback:
                progress_callback("final_failure", f"❌ Failed to generate tool after {self.current_iteration} attempts")
            
        return {
            'success': last_result.get('success', False) if last_result else False,
            'iterations': self.current_iteration,
            'trajectory': self.trajectory if self.enable_trajectory else [],
            'final_result': last_result,
            'trajectory_summary': self._summarize_trajectory(),
            'code': last_result.get('code', '')
        }

    def _single_improvement_iteration(self, user_request: str, available_actions: List[str], trajectory_analysis: str, progress_callback=None) -> Dict[str, Any]:
        """Perform a single iteration of self-improvement with trajectory-informed reasoning and progress updates."""
        # Enhanced assessment with trajectory context
        assessment_prompt = f"""
        Task: {user_request}
        Available actions: {available_actions}
        Trajectory analysis: {trajectory_analysis}
        Current iteration: {self.current_iteration}
        
        Based on the trajectory analysis and previous attempts, assess if we can handle this task.
        If previous iterations failed, consider what went wrong and how to improve.
        """
        
        if progress_callback:
            progress_callback("assessment", "🧠 Assessing capability gaps...")
        
        assessment = self.assess_capability_gap(user_request, available_actions)
        
        if assessment.get('can_handle', True):
            return {
                'success': True,
                'used_existing_capability': True,
                'message': 'Task can be handled with existing capabilities',
                'assessment': assessment
            }
        
        # Generate code with trajectory context
        print(f"🔧 Generating capability code (iteration {self.current_iteration})...")
        if progress_callback:
            progress_callback("code_generation", "💻 Writing specialized code for your task...")
        
        try:
            code, module_name = self.generate_capability_code(
                assessment.get('missing_capability', 'Unknown capability'),
                assessment.get('required_functions', []),
                user_request
            )
            
            # Validate and execute with enhanced error handling
            print(f"🧪 Validating and executing code (iteration {self.current_iteration})...")
            if progress_callback:
                progress_callback("validation", "🔍 Validating and testing generated code...")
            
            # First, basic validation and execution
            success, instance, message = self.validate_and_execute_code(
                code,
                module_name,
                max_retries=2
            )
            
            if not success:
                return {
                    'success': False,
                    'error': f"Code execution failed: {message}",
                    'assessment': assessment,
                    'iteration': self.current_iteration
                }
            
            # Run comprehensive testing
            print(f"🧪 Running comprehensive tests (iteration {self.current_iteration})...")
            if progress_callback:
                progress_callback("testing", "🔬 Running comprehensive tool tests...")
            
            tool_type = self.tool_generator.detect_tool_type(user_request)
            test_results = self.testing_framework.test_generated_tool(
                code, module_name, tool_type, user_request
            )
            
            # Log detailed test results for debugging
            if test_results.get('total_tests', 0) > 0:
                success_rate = test_results.get('passed', 0) / test_results['total_tests']
                logger.info(f"Test results for {module_name}: {test_results.get('passed', 0)}/{test_results['total_tests']} passed ({success_rate:.1%})")
                if not test_results.get('success', False):
                    failed_tests = [test for test in test_results.get('test_results', []) if not test.get('passed', False)]
                    for test in failed_tests:
                        logger.warning(f"Failed test '{test.get('name', 'Unknown')}': {test.get('error', 'Unknown error')}")
            
            if test_results['success']:
                return {
                    'success': True,
                    'generated_module': module_name,
                    'message': f'Successfully generated, validated, and tested capability: {assessment.get("missing_capability", "Unknown")}',
                    'assessment': assessment,
                    'iteration': self.current_iteration,
                    'test_results': test_results,
                    'tool_type': tool_type,
                    'code': code
                }
            else:
                return {
                    'success': False,
                    'error': f"Tool testing failed: {test_results.get('error', 'Unknown testing error')}",
                    'assessment': assessment,
                    'iteration': self.current_iteration,
                    'test_results': test_results,
                    'code': code
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Code generation failed: {str(e)}",
                'assessment': assessment,
                'iteration': self.current_iteration
            }

    def _test_generated_capability(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Test the generated capability to ensure it works correctly."""
        try:
            module_name = result.get('generated_module')
            if not module_name or module_name not in self.generated_modules:
                return {'success': False, 'error': 'Generated module not found'}
            
            instance = self.generated_modules[module_name]['instance']
            methods = [method for method in dir(instance) if not method.startswith('_')]
            
            if not methods:
                return {'success': False, 'error': 'No public methods found in generated capability'}
            
            # Test the first available method
            test_method = methods[0]
            print(f"🧪 Testing method: {test_method}")
            
            # Try to call the method (this is a basic test)
            test_result = getattr(instance, test_method)()
            
            return {
                'success': True,
                'tested_method': test_method,
                'result': str(test_result)[:200]  # Limit output
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Testing failed: {str(e)}"
            }

    def _summarize_trajectory(self) -> str:
        """Provide a concise summary of the trajectory for debugging."""
        if not self.trajectory:
            return "No trajectory recorded"
        
        total_steps = len(self.trajectory)
        successful_steps = len([step for step in self.trajectory if step['success']])
        failed_steps = total_steps - successful_steps
        
        summary = f"Trajectory: {total_steps} steps, {successful_steps} successful, {failed_steps} failed"
        
        if failed_steps > 0:
            recent_errors = [step['error'] for step in self.trajectory[-3:] if step['error']]
            if recent_errors:
                summary += f". Recent errors: {recent_errors[-1]}"
        
        return summary

    def self_improve_for_task(self, user_request: str, available_actions: List[str]) -> Dict[str, Any]:
        """Complete self-improvement workflow: assess, generate, implement, and use."""
        
        logger.info(f"Starting self-improvement for task: {user_request}")
        
        # Step 1: Assess capability gap
        assessment = self.assess_capability_gap(user_request, available_actions)
        
        if assessment['can_handle']:
            return {
                'success': True,
                'used_existing_capability': True,
                'message': 'Task can be handled with existing capabilities',
                'assessment': assessment
            }
        
        # Step 2: Generate code for missing capability
        try:
            code, module_name = self.generate_capability_code(
                assessment['missing_capability'],
                assessment['required_functions'],
                user_request
            )
            
            # Step 3: Validate and execute the code
            success, instance, message = self.validate_and_execute_code(code, module_name)
            
            if not success:
                return {
                    'success': False,
                    'error': f"Failed to implement capability: {message}",
                    'assessment': assessment
                }
            
            # Step 4: Try to use the new capability
            try:
                # Find the main method to call
                methods = [method for method in dir(instance) if not method.startswith('_')]
                if methods:
                    main_method = methods[0]  # Use the first public method
                    result = self.use_new_capability(module_name, main_method, user_request)
                    
                    return {
                        'success': True,
                        'used_existing_capability': False,
                        'generated_module': module_name,
                        'result': result,
                        'message': f'Successfully generated and used new capability: {assessment["missing_capability"]}',
                        'assessment': assessment
                    }
                else:
                    return {
                        'success': False,
                        'error': 'No public methods found in generated capability',
                        'assessment': assessment
                    }
                    
            except Exception as e:
                logger.error(f"Error using new capability: {str(e)}")
                return {
                    'success': False,
                    'error': f'Failed to use new capability: {str(e)}',
                    'assessment': assessment
                }
                
        except Exception as e:
            logger.error(f"Error in self-improvement process: {str(e)}")
            return {
                'success': False,
                'error': f'Self-improvement failed: {str(e)}',
                'assessment': assessment
            }
    
    def _load_existing_capabilities(self):
        """Load any existing generated capabilities from disk."""
        
        if not os.path.exists(self.generated_code_dir):
            return
        
        for filename in os.listdir(self.generated_code_dir):
            if filename.endswith('.py') and filename.startswith('capability_'):
                module_name = filename[:-3]  # Remove .py extension
                module_file = os.path.join(self.generated_code_dir, filename)
                
                try:
                    spec = importlib.util.spec_from_file_location(module_name, module_file)
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)
                    
                    # Find the main class
                    main_class = None
                    for name, obj in inspect.getmembers(module):
                        if inspect.isclass(obj) and obj.__module__ == module_name:
                            main_class = obj
                            break
                    
                    if main_class:
                        instance = main_class()
                        self.generated_modules[module_name] = {
                            'module': module,
                            'instance': instance,
                            'file_path': module_file,
                            'created_at': 'unknown'  # We don't know when it was created
                        }
                        logger.info(f"Loaded existing capability: {module_name}")
                        
                except Exception as e:
                    logger.error(f"Failed to load existing capability {module_name}: {str(e)}")
    
    def list_capabilities(self) -> Dict[str, Any]:
        """List all available capabilities (built-in and generated)."""
        
        return {
            'built_in_capabilities': list(self.capabilities_registry.keys()),
            'generated_capabilities': {
                name: {
                    'created_at': info['created_at'],
                    'file_path': info['file_path'],
                    'methods': [method for method in dir(info['instance']) if not method.startswith('_')]
                }
                for name, info in self.generated_modules.items()
            }
        }
    
    def cleanup_old_capabilities(self, max_age_days: int = 30):
        """Clean up old generated capabilities to prevent disk bloat."""
        
        current_time = datetime.now()
        
        for module_name, info in list(self.generated_modules.items()):
            try:
                if info['created_at'] != 'unknown':
                    created_time = datetime.fromisoformat(info['created_at'])
                    age_days = (current_time - created_time).days
                    
                    if age_days > max_age_days:
                        # Remove from memory
                        if module_name in sys.modules:
                            del sys.modules[module_name]
                        
                        # Remove file
                        if os.path.exists(info['file_path']):
                            os.remove(info['file_path'])
                        
                        # Remove from registry
                        del self.generated_modules[module_name]
                        
                        logger.info(f"Cleaned up old capability: {module_name}")
                        
            except Exception as e:
                logger.error(f"Error cleaning up capability {module_name}: {str(e)}")