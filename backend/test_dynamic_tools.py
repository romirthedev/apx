#!/usr/bin/env python3
"""
Test script for the dynamic tool generation system.
This script tests the complete workflow from request to tool generation.
"""

import sys
import os
import json
from datetime import datetime

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.self_improvement import SelfImprovementEngine
from core.dynamic_tool_generator import DynamicToolGenerator
from core.tool_testing_framework import ToolTestingFramework
from core.gemini_ai import GeminiAI
from core.security_manager import SecurityManager

def test_dynamic_tool_generation():
    """Test the complete dynamic tool generation workflow."""
    
    print("🚀 Testing Dynamic Tool Generation System")
    print("=" * 50)
    
    try:
        # Initialize components
        print("📋 Initializing components...")
        
        # Mock GeminiAI for testing (you may need to adjust this)
        class MockGeminiAI:
            class MockModel:
                def generate_content(self, prompt):
                    # Return a simple spreadsheet tool for testing
                    class MockResponse:
                        text = '''
import pandas as pd
import os
from typing import Dict, Any, List
from datetime import datetime

class SpreadsheetTool:
    """Tool for creating and manipulating spreadsheets."""
    
    def __init__(self):
        self.current_file = None
        self.data = None
    
    def create_spreadsheet(self, data: List[Dict], filename: str) -> Dict[str, Any]:
        """Create a new spreadsheet with the provided data."""
        try:
            df = pd.DataFrame(data)
            filepath = os.path.expanduser(f"~/Desktop/{filename}")
            
            # For testing, just simulate file creation
            self.current_file = filepath
            self.data = df
            
            return {
                "success": True,
                "filepath": filepath,
                "rows": len(df),
                "columns": len(df.columns),
                "message": f"Spreadsheet created successfully at {filepath}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to create spreadsheet: {str(e)}"
            }
    
    def add_data(self, new_data: List[Dict]) -> Dict[str, Any]:
        """Add new data to the current spreadsheet."""
        try:
            if self.data is None:
                return {"success": False, "error": "No spreadsheet loaded"}
            
            new_df = pd.DataFrame(new_data)
            import pandas as pd
            self.data = pd.concat([self.data, new_df], ignore_index=True)
            
            return {
                "success": True,
                "rows_added": len(new_data),
                "total_rows": len(self.data),
                "message": f"Added {len(new_data)} rows successfully"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
'''
                    return MockResponse()
            
            model = MockModel()
        
        gemini_ai = MockGeminiAI()
        security_manager = SecurityManager()
        
        # Test Dynamic Tool Generator
        print("\n🔧 Testing Dynamic Tool Generator...")
        tool_generator = DynamicToolGenerator(gemini_ai, security_manager)
        
        # Test tool type detection
        test_requests = [
            "Create a spreadsheet with sales data",
            "Organize my files in folders",
            "Analyze the data in my CSV file",
            "Build a custom calculator tool"
        ]
        
        for request in test_requests:
            tool_type = tool_generator.detect_tool_type(request)
            print(f"  📝 '{request}' -> {tool_type}")
        
        # Test tool generation
        print("\n🏗️ Testing Tool Generation...")
        user_request = "Create a spreadsheet with my sales data"
        code, module_name = tool_generator.generate_specialized_tool(user_request)
        
        print(f"  ✅ Generated module: {module_name}")
        print(f"  📄 Code length: {len(code)} characters")
        
        # Test Testing Framework
        print("\n🧪 Testing Tool Testing Framework...")
        testing_framework = ToolTestingFramework(security_manager)
        
        test_results = testing_framework.test_generated_tool(
            code, module_name, 'spreadsheet', user_request
        )
        
        print(f"  🎯 Testing success: {test_results['success']}")
        if test_results['success']:
            test_summary = test_results['test_results']
            print(f"  📊 Tests passed: {test_summary['passed']}/{test_summary['total_tests']}")
            print(f"  📈 Success rate: {test_summary['success_rate']:.1%}")
        else:
            print(f"  ❌ Testing failed: {test_results.get('error', 'Unknown error')}")
        
        # Test Self-Improvement Engine
        print("\n🧠 Testing Self-Improvement Engine...")
        
        def progress_callback(stage, message, metadata=None):
            print(f"  🔄 {stage}: {message}")
        
        self_improvement = SelfImprovementEngine(
            gemini_ai, security_manager, max_iterations=2
        )
        
        available_actions = ['chat', 'web_search', 'browse_url']
        
        result = self_improvement.iterative_self_improve_for_task(
            user_request, available_actions, progress_callback
        )
        
        print(f"  🎯 Self-improvement success: {result['success']}")
        print(f"  🔄 Iterations used: {result['iterations']}")
        
        if result['success']:
            final_result = result.get('final_result', {})
            if 'test_results' in final_result:
                test_info = final_result['test_results']
                print(f"  🧪 Final tool testing: {test_info['success']}")
        
        print("\n✅ Dynamic Tool Generation System Test Complete!")
        print("=" * 50)
        
        return {
            'success': True,
            'tool_generation': True,
            'tool_testing': test_results['success'],
            'self_improvement': result['success'],
            'message': 'All systems operational'
        }
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'success': False,
            'error': str(e),
            'message': 'System test failed'
        }

if __name__ == '__main__':
    result = test_dynamic_tool_generation()
    
    print(f"\n📋 Final Test Result:")
    print(json.dumps(result, indent=2))
    
    # Exit with appropriate code
    sys.exit(0 if result['success'] else 1)