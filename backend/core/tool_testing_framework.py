import os
import sys
import json
import logging
import tempfile
import importlib.util
import traceback
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class ToolTestingFramework:
    """Framework for testing newly generated tools and capabilities."""
    
    def __init__(self, security_manager):
        self.security_manager = security_manager
        self.test_results = []
        
    def create_test_suite(self, tool_type: str, user_request: str) -> List[Dict[str, Any]]:
        """Create a test suite based on the tool type and user request."""
        
        base_tests = [
            {
                'name': 'import_test',
                'description': 'Test if the module can be imported successfully',
                'test_type': 'import'
            },
            {
                'name': 'instantiation_test',
                'description': 'Test if the main class can be instantiated',
                'test_type': 'instantiation'
            }
        ]
        
        # Add specific tests based on tool type
        if tool_type == 'spreadsheet':
            base_tests.extend([
                {
                    'name': 'spreadsheet_creation_test',
                    'description': 'Test spreadsheet creation functionality',
                    'test_type': 'adaptive_functional',
                    'method_patterns': ['create', 'spreadsheet', 'financial', 'model'],
                    'test_args': [
                        [{'name': 'Test', 'value': 123}],
                        'test_spreadsheet'
                    ],
                    'expected_keys': ['success']
                },
                {
                    'name': 'data_manipulation_test',
                    'description': 'Test data manipulation functionality',
                    'test_type': 'adaptive_functional',
                    'method_patterns': ['add', 'data', 'current'],
                    'test_args': [[{'name': 'Test2', 'value': 456}]],
                    'expected_keys': ['success']
                },
                {
                    'name': 'method_detection_test',
                    'description': 'Test if spreadsheet-related methods exist',
                    'test_type': 'method_detection',
                    'method_patterns': ['create', 'add', 'save', 'load']
                }
            ])
        
        elif tool_type == 'file_manager':
            base_tests.extend([
                {
                    'name': 'safe_path_test',
                    'description': 'Test safe path validation',
                    'test_type': 'functional',
                    'method': '_is_safe_path',
                    'args': [os.path.expanduser('~/Desktop/test')],
                    'expected_result': True
                },
                {
                    'name': 'list_files_test',
                    'description': 'Test file listing functionality',
                    'test_type': 'functional',
                    'method': 'list_files',
                    'args': [os.path.expanduser('~/Desktop')],
                    'expected_keys': ['success', 'files', 'count']
                }
            ])
        
        elif tool_type == 'data_processor':
            base_tests.extend([
                {
                    'name': 'analyze_data_test',
                    'description': 'Test data analysis without loaded data',
                    'test_type': 'functional',
                    'method': 'analyze_data',
                    'args': [],
                    'expected_keys': ['success'],
                    'expected_success': False
                }
            ])
        
        elif tool_type == 'custom':
            # For custom tools, create adaptive tests based on user request
            if 'qr' in user_request.lower():
                # Add flexible QR code tests that adapt to different method names
                base_tests.extend([
                    {
                        'name': 'qr_method_detection',
                        'description': 'Detect available QR code generation methods',
                        'test_type': 'method_detection',
                        'method_patterns': ['generate_qr', 'qr_code', 'create_qr', 'generate_and_save'],
                        'expected_result': True
                    },
                    {
                        'name': 'qr_generation_adaptive',
                        'description': 'Test QR code generation with adaptive method calling',
                        'test_type': 'adaptive_functional',
                        'method_patterns': ['generate_qr', 'qr_code', 'create_qr', 'generate_and_save'],
                        'test_args': ['https://example.com', 'test_qr.png'],
                        'expected_keys': ['success', 'message']
                    }
                ])
        
        return base_tests
    
    def run_test_suite(self, module_instance, test_suite: List[Dict[str, Any]], module_name: str) -> Dict[str, Any]:
        """Run a complete test suite on a module instance."""
        
        results = {
            'module_name': module_name,
            'total_tests': len(test_suite),
            'passed': 0,
            'failed': 0,
            'test_results': [],
            'overall_success': False,
            'timestamp': datetime.now().isoformat()
        }
        
        for test in test_suite:
            test_result = self._run_single_test(module_instance, test)
            results['test_results'].append(test_result)
            
            if test_result['passed']:
                results['passed'] += 1
            else:
                results['failed'] += 1
        
        # Consider the test suite successful if at least 80% of tests pass
        success_rate = results['passed'] / results['total_tests']
        results['overall_success'] = success_rate >= 0.8
        results['success_rate'] = success_rate
        
        self.test_results.append(results)
        return results
    
    def _run_single_test(self, module_instance, test: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single test on the module instance."""
        
        test_result = {
            'name': test['name'],
            'description': test['description'],
            'passed': False,
            'error': None,
            'output': None,
            'execution_time': None
        }
        
        start_time = datetime.now()
        
        try:
            if test['test_type'] == 'import':
                # Import test is already passed if we have the instance
                test_result['passed'] = module_instance is not None
                test_result['output'] = 'Module imported successfully'
            
            elif test['test_type'] == 'instantiation':
                # Instantiation test is already passed if we have the instance
                test_result['passed'] = module_instance is not None
                test_result['output'] = 'Class instantiated successfully'
            
            elif test['test_type'] == 'method_check':
                # Check if required methods exist
                method_name = test.get('method', 'create_spreadsheet')  # Default method
                has_method = hasattr(module_instance, method_name)
                test_result['passed'] = has_method
                test_result['output'] = f'Method {method_name} exists: {has_method}'
            
            elif test['test_type'] == 'method_detection':
                # Check if any method matching the patterns exists
                method_patterns = test.get('method_patterns', [])
                found_methods = []
                
                for pattern in method_patterns:
                    for attr_name in dir(module_instance):
                        if pattern in attr_name.lower() and callable(getattr(module_instance, attr_name)):
                            found_methods.append(attr_name)
                
                test_result['passed'] = len(found_methods) > 0
                test_result['output'] = f'Found methods: {found_methods}'
                if not found_methods:
                    test_result['error'] = f'No methods found matching patterns: {method_patterns}'
            
            elif test['test_type'] == 'adaptive_functional':
                # Find and test the first matching method
                method_patterns = test.get('method_patterns', [])
                test_args = test.get('test_args', [])
                found_method = None
                
                for pattern in method_patterns:
                    for attr_name in dir(module_instance):
                        if pattern in attr_name.lower() and callable(getattr(module_instance, attr_name)):
                            found_method = attr_name
                            break
                    if found_method:
                        break
                
                if found_method:
                    method = getattr(module_instance, found_method)
                    try:
                        # Try with different argument combinations
                        result = None
                        if len(test_args) >= 2:
                            # Try with URL and filename
                            result = method(test_args[0], test_args[1])
                        elif len(test_args) == 1:
                            # Try with just URL
                            result = method(test_args[0])
                        else:
                            # Try with no args
                            result = method()
                        
                        test_result['output'] = result
                        
                        # Check expected keys
                        if 'expected_keys' in test:
                            if isinstance(result, dict):
                                has_all_keys = all(key in result for key in test['expected_keys'])
                                test_result['passed'] = has_all_keys
                            else:
                                test_result['passed'] = False
                                test_result['error'] = 'Result is not a dictionary'
                        else:
                            test_result['passed'] = True
                    except Exception as e:
                        test_result['passed'] = False
                        test_result['error'] = f'Method {found_method} failed: {str(e)}'
                else:
                    test_result['passed'] = False
                    test_result['error'] = f'No methods found matching patterns: {method_patterns}'
            
            elif test['test_type'] == 'functional':
                # Run functional test
                method_name = test['method']
                args = test.get('args', [])
                kwargs = test.get('kwargs', {})
                
                if hasattr(module_instance, method_name):
                    method = getattr(module_instance, method_name)
                    result = method(*args, **kwargs)
                    
                    test_result['output'] = result
                    
                    # Check expected keys
                    if 'expected_keys' in test:
                        if isinstance(result, dict):
                            has_all_keys = all(key in result for key in test['expected_keys'])
                            test_result['passed'] = has_all_keys
                        else:
                            test_result['passed'] = False
                            test_result['error'] = 'Result is not a dictionary'
                    
                    # Check expected result
                    elif 'expected_result' in test:
                        test_result['passed'] = result == test['expected_result']
                    
                    # Check expected success value
                    elif 'expected_success' in test:
                        if isinstance(result, dict) and 'success' in result:
                            test_result['passed'] = result['success'] == test['expected_success']
                        else:
                            test_result['passed'] = False
                    
                    else:
                        # Default: just check if method runs without error
                        test_result['passed'] = True
                else:
                    test_result['passed'] = False
                    test_result['error'] = f'Method {method_name} not found'
        
        except Exception as e:
            test_result['passed'] = False
            test_result['error'] = str(e)
            test_result['traceback'] = traceback.format_exc()
        
        finally:
            end_time = datetime.now()
            test_result['execution_time'] = (end_time - start_time).total_seconds()
        
        return test_result
    
    def test_generated_tool(self, code: str, module_name: str, tool_type: str, user_request: str) -> Dict[str, Any]:
        """Test a newly generated tool comprehensively."""
        
        logger.info(f"Testing generated tool: {module_name} (type: {tool_type})")
        
        # Create test suite
        test_suite = self.create_test_suite(tool_type, user_request)
        
        try:
            # Create temporary file for the module
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
                temp_file.write(code)
                temp_file_path = temp_file.name
            
            # Import the module
            spec = importlib.util.spec_from_file_location(module_name, temp_file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find the main class in the module
            main_class = None
            for name in dir(module):
                obj = getattr(module, name)
                if (isinstance(obj, type) and 
                    not name.startswith('_') and 
                    name not in ['type', 'object', 'Exception'] and
                    hasattr(obj, '__module__') and 
                    obj.__module__ == module.__name__):
                    main_class = obj
                    break
            
            if main_class is None:
                return {
                    'success': False,
                    'error': 'No main tool class found in module',
                    'module_name': module_name
                }
            
            # Instantiate the class
            instance = main_class()
            
            # Run test suite
            test_results = self.run_test_suite(instance, test_suite, module_name)
            
            # Clean up
            os.unlink(temp_file_path)
            
            return {
                'success': test_results['overall_success'],
                'test_results': test_results,
                'module_name': module_name,
                'tool_type': tool_type,
                'message': f"Testing completed. Success rate: {test_results['success_rate']:.1%}"
            }
        
        except Exception as e:
            # Clean up on error
            if 'temp_file_path' in locals():
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
            
            return {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc(),
                'module_name': module_name,
                'tool_type': tool_type
            }
    
    def get_test_summary(self) -> Dict[str, Any]:
        """Get a summary of all test results."""
        
        if not self.test_results:
            return {
                'total_modules_tested': 0,
                'overall_success_rate': 0,
                'message': 'No tests have been run yet'
            }
        
        total_tests = sum(result['total_tests'] for result in self.test_results)
        total_passed = sum(result['passed'] for result in self.test_results)
        successful_modules = sum(1 for result in self.test_results if result['overall_success'])
        
        return {
            'total_modules_tested': len(self.test_results),
            'successful_modules': successful_modules,
            'total_tests_run': total_tests,
            'total_tests_passed': total_passed,
            'overall_success_rate': total_passed / total_tests if total_tests > 0 else 0,
            'module_success_rate': successful_modules / len(self.test_results),
            'recent_results': self.test_results[-5:] if len(self.test_results) > 5 else self.test_results
        }