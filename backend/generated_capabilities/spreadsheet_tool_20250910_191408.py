import pandas as pd
import os
from typing import Dict, List, Any

class SpreadsheetTool:
    """Advanced spreadsheet creation and manipulation tool."""
    
    def __init__(self):
        self.current_file = None
        self.data = None
    
    def create_spreadsheet(self, filename: str, data: List[Dict]) -> Dict[str, Any]:
        """Create a new spreadsheet with the provided data."""
        try:
            import pandas as pd
            df = pd.DataFrame(data)
            filepath = os.path.expanduser(f"~/Desktop/{filename}")
            
            # Save to Excel format
            df.to_excel(filepath, index=False)
            
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
            
            # Save updated data
            if self.current_file:
                self.data.to_excel(self.current_file, index=False)
            
            return {
                "success": True,
                "rows_added": len(new_data),
                "total_rows": len(self.data),
                "message": f"Added {len(new_data)} rows successfully"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_data(self) -> Dict[str, Any]:
        """Get current spreadsheet data."""
        if self.data is None:
            return {"success": False, "error": "No spreadsheet loaded"}
        
        return {
            "success": True,
            "data": self.data.to_dict('records'),
            "rows": len(self.data),
            "columns": list(self.data.columns)
        }