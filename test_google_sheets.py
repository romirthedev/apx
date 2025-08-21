import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import required modules
from backend.plugins.google_sheets_manager import GoogleSheetsManager
from backend.core.command_processor import CommandProcessor
from backend.core.security_manager import SecurityManager
from backend.core.action_logger import ActionLogger

# Part 1: Test GoogleSheetsManager directly
print("\n=== Testing GoogleSheetsManager Methods ===\n")

# Initialize GoogleSheetsManager
google_sheets_manager = GoogleSheetsManager()

# Test creating a Google Sheet
print("1. Testing create_google_sheet method:")
result = google_sheets_manager.create_google_sheet("Test Spreadsheet")
print(f"Result: {result}\n")

# Test fetching financial data for Microsoft earnings
print("2. Testing fetch_financial_data method for Microsoft earnings:")
result = google_sheets_manager.fetch_financial_data("microsoft", "earnings", "quarterly")
print(f"Result: {result}\n")

# Test creating a financial spreadsheet for Tesla
print("3. Testing create_financial_spreadsheet method for Tesla:")
result = google_sheets_manager.create_financial_spreadsheet("tesla", "earnings")
print(f"Result: {result}\n")

# Part 2: Test CommandProcessor integration
print("\n=== Testing CommandProcessor Integration ===\n")

# Initialize dependencies
security_manager = SecurityManager()
action_logger = ActionLogger()

# Initialize CommandProcessor with required dependencies
command_processor = CommandProcessor(
    security_manager=security_manager,
    action_logger=action_logger
)

# Test commands
test_commands = [
    "Create a Google spreadsheet about Microsoft earnings",
    "Create a financial spreadsheet for Apple revenue",
    "Fill a Google spreadsheet with Tesla earnings information"
]

# Process each command and print the result
for command in test_commands:
    print(f"\nTesting command: {command}")
    try:
        result = command_processor.process(command)
        print(f"Success: {result.get('success', False)}")
        print(f"Method: {result.get('metadata', {}).get('method', 'unknown')}")
        print(f"Result: {result.get('result', 'No result')}")
    except Exception as e:
        print(f"Error processing command: {e}")