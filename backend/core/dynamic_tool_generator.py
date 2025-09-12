import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class DynamicToolGenerator:
    """Enhanced tool generation system for creating specialized capabilities."""
    
    def __init__(self, gemini_ai, security_manager):
        self.gemini_ai = gemini_ai
        self.security_manager = security_manager
        self.tool_templates = self._load_tool_templates()
        
    def _load_tool_templates(self) -> Dict[str, str]:
        """Load predefined tool templates for common use cases."""
        return {
            'spreadsheet': '''
import pandas as pd
import openpyxl
from typing import Dict, Any, List, Optional
import os

class SpreadsheetTool:
    """Tool for creating and manipulating spreadsheets."""
    
    def __init__(self):
        self.current_file = None
        self.data = None
    
    def create_spreadsheet(self, data: List[Dict], filename: str, sheet_name: str = "Sheet1") -> Dict[str, Any]:
        """Create a new spreadsheet with the provided data."""
        try:
            df = pd.DataFrame(data)
            filepath = os.path.expanduser(f"~/Desktop/{filename}")
            
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
            
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
            self.data = pd.concat([self.data, new_df], ignore_index=True)
            
            return {
                "success": True,
                "rows_added": len(new_data),
                "total_rows": len(self.data),
                "message": f"Added {len(new_data)} rows successfully"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def save_spreadsheet(self, filename: str = None) -> Dict[str, Any]:
        """Save the current spreadsheet."""
        try:
            if self.data is None:
                return {"success": False, "error": "No data to save"}
            
            filepath = filename or self.current_file
            if not filepath:
                filepath = os.path.expanduser(f"~/Desktop/spreadsheet_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
            
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                self.data.to_excel(writer, sheet_name="Sheet1", index=False)
            
            return {
                "success": True,
                "filepath": filepath,
                "message": f"Spreadsheet saved to {filepath}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
''',
            'file_manager': '''
import os
import shutil
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

class FileManagerTool:
    """Tool for file and directory operations."""
    
    def __init__(self):
        self.safe_directories = [os.path.expanduser("~/Desktop"), os.path.expanduser("~/Documents")]
    
    def _is_safe_path(self, path: str) -> bool:
        """Check if the path is in a safe directory."""
        abs_path = os.path.abspath(path)
        return any(abs_path.startswith(safe_dir) for safe_dir in self.safe_directories)
    
    def create_directory(self, path: str) -> Dict[str, Any]:
        """Create a new directory."""
        try:
            if not self._is_safe_path(path):
                return {"success": False, "error": "Path not in safe directory"}
            
            os.makedirs(path, exist_ok=True)
            return {
                "success": True,
                "path": path,
                "message": f"Directory created: {path}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def list_files(self, directory: str) -> Dict[str, Any]:
        """List files in a directory."""
        try:
            if not self._is_safe_path(directory):
                return {"success": False, "error": "Path not in safe directory"}
            
            files = []
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                files.append({
                    "name": item,
                    "type": "directory" if os.path.isdir(item_path) else "file",
                    "size": os.path.getsize(item_path) if os.path.isfile(item_path) else None
                })
            
            return {
                "success": True,
                "directory": directory,
                "files": files,
                "count": len(files)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def copy_file(self, source: str, destination: str) -> Dict[str, Any]:
        """Copy a file from source to destination."""
        try:
            if not (self._is_safe_path(source) and self._is_safe_path(destination)):
                return {"success": False, "error": "Paths not in safe directories"}
            
            shutil.copy2(source, destination)
            return {
                "success": True,
                "source": source,
                "destination": destination,
                "message": f"File copied from {source} to {destination}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
''',
            'data_processor': '''
import json
import csv
import pandas as pd
from typing import Dict, Any, List, Optional, Union
import requests
from datetime import datetime

class DataProcessorTool:
    """Tool for processing and analyzing data."""
    
    def __init__(self):
        self.processed_data = None
    
    def load_csv(self, filepath: str) -> Dict[str, Any]:
        """Load data from a CSV file."""
        try:
            df = pd.read_csv(filepath)
            self.processed_data = df
            
            return {
                "success": True,
                "rows": len(df),
                "columns": list(df.columns),
                "sample_data": df.head().to_dict('records'),
                "message": f"Loaded {len(df)} rows from {filepath}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def analyze_data(self) -> Dict[str, Any]:
        """Perform basic analysis on loaded data."""
        try:
            if self.processed_data is None:
                return {"success": False, "error": "No data loaded"}
            
            df = self.processed_data
            analysis = {
                "shape": df.shape,
                "columns": list(df.columns),
                "data_types": df.dtypes.to_dict(),
                "missing_values": df.isnull().sum().to_dict(),
                "numeric_summary": df.describe().to_dict() if len(df.select_dtypes(include='number').columns) > 0 else None
            }
            
            return {
                "success": True,
                "analysis": analysis,
                "message": "Data analysis completed"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def filter_data(self, conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Filter data based on conditions."""
        try:
            if self.processed_data is None:
                return {"success": False, "error": "No data loaded"}
            
            df = self.processed_data.copy()
            
            for column, condition in conditions.items():
                if column in df.columns:
                    if isinstance(condition, dict):
                        if 'min' in condition:
                            df = df[df[column] >= condition['min']]
                        if 'max' in condition:
                            df = df[df[column] <= condition['max']]
                        if 'equals' in condition:
                            df = df[df[column] == condition['equals']]
                    else:
                        df = df[df[column] == condition]
            
            return {
                "success": True,
                "filtered_rows": len(df),
                "original_rows": len(self.processed_data),
                "filtered_data": df.head(10).to_dict('records'),
                "message": f"Filtered to {len(df)} rows"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
'''
        }
    
    def detect_tool_type(self, user_request: str) -> str:
        """Detect what type of tool is needed based on the user request."""
        request_lower = user_request.lower()
        
        # Spreadsheet-related keywords
        if any(keyword in request_lower for keyword in ['spreadsheet', 'excel', 'csv', 'table', 'data entry', 'xlsx']):
            return 'spreadsheet'
        
        # File management keywords
        elif any(keyword in request_lower for keyword in ['file', 'folder', 'directory', 'copy', 'move', 'organize']):
            return 'file_manager'
        
        # Data processing keywords
        elif any(keyword in request_lower for keyword in ['analyze', 'process', 'filter', 'data', 'statistics']):
            return 'data_processor'
        
        # Default to custom generation
        return 'custom'
    
    def generate_specialized_tool(self, user_request: str, tool_type: str = None) -> Tuple[str, str]:
        """Generate a specialized tool based on the user request."""
        
        if tool_type is None:
            tool_type = self.detect_tool_type(user_request)
        
        # Use template if available
        if tool_type in self.tool_templates:
            base_code = self.tool_templates[tool_type]
            module_name = f"{tool_type}_tool_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            return base_code, module_name
        
        # Generate custom tool
        return self._generate_custom_tool(user_request)
    
    def _generate_custom_tool(self, user_request: str) -> Tuple[str, str]:
        """Generate a custom tool for specific user requests."""
        
        generation_prompt = f"""
Create a specialized Python tool class for this user request: {user_request}

Generate a complete Python module with:
1. A main class that implements the required functionality
2. Methods that handle the specific user request
3. Proper error handling and return values
4. Type hints and docstrings
5. Safe operations (no system modifications without permission)
6. Compatibility with macOS

The class should return structured data (dicts) with 'success', 'message', and relevant data fields.

Provide ONLY the Python code, no explanations:
"""
        
        try:
            response = self.gemini_ai.model.generate_content(generation_prompt)
            generated_code = response.text.strip()
            
            # Clean up the code
            if generated_code.startswith('```python'):
                generated_code = generated_code[9:]
            if generated_code.endswith('```'):
                generated_code = generated_code[:-3]
            
            module_name = f"custom_tool_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            logger.info(f"Generated custom tool for request: {user_request}")
            return generated_code, module_name
            
        except Exception as e:
            logger.error(f"Error generating custom tool: {str(e)}")
            raise
    
    def enhance_tool_with_context(self, base_code: str, user_request: str, context: Dict[str, Any] = None) -> str:
        """Enhance a tool with additional context and specific requirements."""
        
        enhancement_prompt = f"""
Enhance this Python tool code to better handle the specific user request:

User Request: {user_request}
Context: {json.dumps(context or {}, indent=2)}

Current Code:
{base_code}

Enhance the code to:
1. Better handle the specific user request
2. Add any missing functionality
3. Improve error handling
4. Add validation for user inputs
5. Make it more robust and user-friendly

Provide ONLY the enhanced Python code, no explanations:
"""
        
        try:
            response = self.gemini_ai.model.generate_content(enhancement_prompt)
            enhanced_code = response.text.strip()
            
            # Clean up the code
            if enhanced_code.startswith('```python'):
                enhanced_code = enhanced_code[9:]
            if enhanced_code.endswith('```'):
                enhanced_code = enhanced_code[:-3]
            
            return enhanced_code
            
        except Exception as e:
            logger.error(f"Error enhancing tool: {str(e)}")
            return base_code  # Return original if enhancement fails