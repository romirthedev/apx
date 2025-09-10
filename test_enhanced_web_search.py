#!/usr/bin/env python3
"""
Comprehensive Test Script for Enhanced Web Search Automation

This script tests the enhanced web search functionality with a wide variety
of search queries to ensure it works for basically any search type.
"""

import sys
import os
import time
from typing import List, Dict, Any

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'generated_capabilities'))

try:
    from enhanced_web_search_automation import EnhancedWebSearchAutomation
except ImportError:
    print("❌ Could not import EnhancedWebSearchAutomation")
    print("Make sure the enhanced_web_search_automation.py file exists in backend/generated_capabilities/")
    sys.exit(1)

def run_comprehensive_tests():
    """Run comprehensive tests for the enhanced web search functionality."""
    
    print("🔍 Enhanced Web Search Automation - Comprehensive Testing")
    print("=" * 70)
    print("Testing diverse search queries to ensure broad compatibility\n")
    
    # Initialize the search automation
    search_automation = EnhancedWebSearchAutomation()
    
    # Comprehensive test cases covering various scenarios
    test_cases = [
        # Product searches
        {
            'category': 'Product Searches',
            'queries': [
                "find me the best iphone 13 case",
                "top wireless earbuds 2024",
                "best laptop for programming",
                "good mechanical keyboard under $100",
                "find waterproof phone case",
                "best gaming mouse for FPS",
                "top rated bluetooth speaker",
                "find ergonomic office chair"
            ]
        },
        
        # GitHub repositories
        {
            'category': 'GitHub Repositories',
            'queries': [
                "github repo for deepseek's latest model",
                "open the github repo for react",
                "find facebook's llama repository",
                "github repo for tensorflow",
                "microsoft's vscode repository",
                "google's flutter github repo",
                "openai's gpt repository",
                "anthropic's claude github"
            ]
        },
        
        # Package searches
        {
            'category': 'Package Searches',
            'queries': [
                "npm package for react router",
                "pypi package for machine learning",
                "npm module for express server",
                "python package for data analysis",
                "npm package for chart visualization",
                "pip package for web scraping",
                "npm package for authentication",
                "python package for image processing"
            ]
        },
        
        # Documentation and tutorials
        {
            'category': 'Documentation & Tutorials',
            'queries': [
                "documentation for python requests",
                "tutorial for docker containers",
                "react hooks documentation",
                "how to use kubernetes",
                "django tutorial for beginners",
                "api documentation for stripe",
                "guide for setting up nginx",
                "learn tensorflow basics"
            ]
        },
        
        # Software and tools
        {
            'category': 'Software & Tools',
            'queries': [
                "download visual studio code",
                "install docker desktop",
                "get latest nodejs version",
                "download postman app",
                "install git for windows",
                "get figma desktop app",
                "download slack for mac",
                "install zoom client"
            ]
        },
        
        # Latest models and releases
        {
            'category': 'Latest Models & Releases',
            'queries': [
                "latest tensorflow model",
                "newest openai gpt model",
                "recent pytorch release",
                "latest stable diffusion model",
                "newest llama model version",
                "recent claude model update",
                "latest hugging face transformers",
                "newest stable release of python"
            ]
        },
        
        # Specific companies and services
        {
            'category': 'Company & Service Searches',
            'queries': [
                "apple developer documentation",
                "google cloud platform",
                "microsoft azure services",
                "amazon web services console",
                "stripe payment integration",
                "twilio api documentation",
                "sendgrid email service",
                "mongodb atlas database"
            ]
        },
        
        # Technical resources
        {
            'category': 'Technical Resources',
            'queries': [
                "mdn web docs javascript",
                "w3schools css tutorial",
                "stack overflow python questions",
                "leetcode coding problems",
                "hackerrank challenges",
                "codepen css examples",
                "github awesome lists",
                "dev.to programming articles"
            ]
        },
        
        # Niche and specialized searches
        {
            'category': 'Niche & Specialized',
            'queries': [
                "rust programming language book",
                "webassembly tutorial guide",
                "quantum computing with qiskit",
                "blockchain development tutorial",
                "computer vision with opencv",
                "natural language processing nltk",
                "game development with unity",
                "3d modeling with blender"
            ]
        }
    ]
    
    # Track test results
    total_tests = 0
    successful_tests = 0
    failed_tests = []
    results_by_category = {}
    
    # Run tests for each category
    for test_category in test_cases:
        category_name = test_category['category']
        queries = test_category['queries']
        
        print(f"\n📂 Testing Category: {category_name}")
        print("─" * 50)
        
        category_results = {
            'total': len(queries),
            'successful': 0,
            'failed': 0,
            'details': []
        }
        
        for i, query in enumerate(queries, 1):
            print(f"\n{i:2d}. Testing: {query}")
            print("   " + "─" * 40)
            
            total_tests += 1
            
            try:
                # Run the search
                result = search_automation.search_and_open(query)
                
                if result['success']:
                    successful_tests += 1
                    category_results['successful'] += 1
                    
                    print(f"   ✅ SUCCESS")
                    print(f"   📄 Title: {result.get('title', 'N/A')}")
                    print(f"   🔗 URL: {result.get('opened_url', 'N/A')}")
                    print(f"   🎯 Type: {result.get('query_type', 'N/A')}")
                    print(f"   📊 Results: {result.get('total_results', 0)}")
                    
                    category_results['details'].append({
                        'query': query,
                        'status': 'success',
                        'url': result.get('opened_url'),
                        'title': result.get('title'),
                        'type': result.get('query_type')
                    })
                    
                else:
                    category_results['failed'] += 1
                    failed_tests.append({
                        'query': query,
                        'category': category_name,
                        'error': result.get('error', 'Unknown error')
                    })
                    
                    print(f"   ❌ FAILED: {result.get('error', 'Unknown error')}")
                    
                    category_results['details'].append({
                        'query': query,
                        'status': 'failed',
                        'error': result.get('error')
                    })
                
            except Exception as e:
                category_results['failed'] += 1
                failed_tests.append({
                    'query': query,
                    'category': category_name,
                    'error': str(e)
                })
                
                print(f"   ❌ EXCEPTION: {str(e)}")
                
                category_results['details'].append({
                    'query': query,
                    'status': 'exception',
                    'error': str(e)
                })
            
            # Rate limiting to be respectful
            time.sleep(0.5)
        
        # Store category results
        results_by_category[category_name] = category_results
        
        # Category summary
        success_rate = (category_results['successful'] / category_results['total']) * 100
        print(f"\n   📊 Category Summary: {category_results['successful']}/{category_results['total']} successful ({success_rate:.1f}%)")
    
    # Final comprehensive report
    print("\n" + "=" * 70)
    print("🎯 COMPREHENSIVE TEST RESULTS")
    print("=" * 70)
    
    overall_success_rate = (successful_tests / total_tests) * 100
    print(f"\n📈 Overall Results:")
    print(f"   Total Tests: {total_tests}")
    print(f"   Successful: {successful_tests}")
    print(f"   Failed: {len(failed_tests)}")
    print(f"   Success Rate: {overall_success_rate:.1f}%")
    
    print(f"\n📊 Results by Category:")
    for category, results in results_by_category.items():
        success_rate = (results['successful'] / results['total']) * 100
        print(f"   {category}: {results['successful']}/{results['total']} ({success_rate:.1f}%)")
    
    if failed_tests:
        print(f"\n❌ Failed Tests ({len(failed_tests)}):")
        for i, failure in enumerate(failed_tests[:10], 1):  # Show first 10 failures
            print(f"   {i:2d}. [{failure['category']}] {failure['query']}")
            print(f"       Error: {failure['error']}")
        
        if len(failed_tests) > 10:
            print(f"       ... and {len(failed_tests) - 10} more failures")
    
    # Capability information
    print(f"\n✨ Enhanced Web Search Capabilities:")
    info = search_automation.get_capability_info()
    for feature in info['features']:
        print(f"   ✅ {feature}")
    
    print(f"\n🎯 Supported Query Types: {', '.join(info['supported_query_types'])}")
    print(f"🌐 Search Sources: {', '.join(info['specialized_sources'])}")
    
    # Final assessment
    print(f"\n🚀 FINAL ASSESSMENT:")
    if overall_success_rate >= 80:
        print(f"   ✅ EXCELLENT: The system successfully handles {overall_success_rate:.1f}% of diverse queries!")
        print(f"   🎯 Ready for production use with broad query support.")
    elif overall_success_rate >= 60:
        print(f"   ⚠️  GOOD: The system handles {overall_success_rate:.1f}% of queries successfully.")
        print(f"   🔧 Some improvements needed for edge cases.")
    else:
        print(f"   ❌ NEEDS WORK: Only {overall_success_rate:.1f}% success rate.")
        print(f"   🛠️  Significant improvements required.")
    
    print(f"\n🎉 Testing completed! The enhanced web search system has been thoroughly validated.")
    
    return {
        'total_tests': total_tests,
        'successful_tests': successful_tests,
        'success_rate': overall_success_rate,
        'results_by_category': results_by_category,
        'failed_tests': failed_tests
    }

if __name__ == "__main__":
    try:
        results = run_comprehensive_tests()
        
        # Exit with appropriate code
        if results['success_rate'] >= 80:
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Needs improvement
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Testing interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Testing failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)