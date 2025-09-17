#!/usr/bin/env python3
"""
Test script to verify financial data accuracy
"""

import requests
import json

def test_financial_data():
    """Test the financial data generation endpoint"""
    
    # Test cases with known financial data
    test_cases = [
        {
            "company": "Apple",
            "request": "Create Apple financial spreadsheet for 2022-2023",
            "expected_ranges": {
                "2023": {"revenue_billions": (380, 390), "net_income_billions": (95, 100)},
                "2022": {"revenue_billions": (390, 400), "net_income_billions": (95, 105)}
            }
        },
        {
            "company": "Tesla", 
            "request": "Create Tesla financial data for 2022-2023",
            "expected_ranges": {
                "2023": {"revenue_billions": (95, 100), "net_income_billions": (14, 16)},
                "2022": {"revenue_billions": (80, 85), "net_income_billions": (12, 14)}
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n=== Testing {test_case['company']} ===")
        
        # Make request to backend
        response = requests.post(
            "http://localhost:8888/command",
            headers={"Content-Type": "application/json"},
            json={
                "command": test_case["request"],
                "action_mode": True
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Request successful: {result['success']}")
            if 'metadata' in result and 'file_path' in result['metadata']:
                print(f"📁 File created: {result['metadata']['file_path']}")
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")

if __name__ == "__main__":
    test_financial_data()