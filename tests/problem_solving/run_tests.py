"""
Test Runner for Problem-Solving Implementation

This script runs the test cases and generates comparison reports between
the old and new implementations.
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, Any, List

from test_framework import TestFramework
from test_cases import TEST_CASES

def run_comparison_tests():
    """
    Run all test cases and generate comparison reports.
    """
    # Initialize test framework
    framework = TestFramework(output_dir="test_results")
    
    # Track overall results
    overall_results = {
        "timestamp": datetime.now().isoformat(),
        "test_cases": [],
        "summary": {
            "total_tests": len(TEST_CASES),
            "improvements": 0,
            "regressions": 0,
            "no_change": 0
        }
    }
    
    # Run each test case
    for test_case in TEST_CASES:
        print(f"\nRunning test case: {test_case.task_id}")
        print(f"Description: {test_case.description}")
        
        # Compare implementations
        comparison = framework.compare_implementations(test_case)
        overall_results["test_cases"].append(comparison)
        
        # Update summary
        metrics = comparison["improvement_metrics"]
        if (metrics["execution_time_improvement"] > 0 or
            metrics["steps_improvement"] > 0 or
            metrics["success_criteria_improvement"] > 0):
            overall_results["summary"]["improvements"] += 1
        elif (metrics["execution_time_improvement"] < 0 or
              metrics["steps_improvement"] < 0 or
              metrics["success_criteria_improvement"] < 0):
            overall_results["summary"]["regressions"] += 1
        else:
            overall_results["summary"]["no_change"] += 1
        
        # Print results
        print("\nResults:")
        print(f"Old Implementation:")
        print(f"  Status: {comparison['old_implementation']['status']}")
        print(f"  Execution Time: {comparison['old_implementation']['execution_time']:.2f}s")
        print(f"  Steps Taken: {comparison['old_implementation']['steps_taken']}")
        print(f"  Success Criteria Met: {comparison['old_implementation']['success_criteria_met']}")
        
        print(f"\nNew Implementation:")
        print(f"  Status: {comparison['new_implementation']['status']}")
        print(f"  Execution Time: {comparison['new_implementation']['execution_time']:.2f}s")
        print(f"  Steps Taken: {comparison['new_implementation']['steps_taken']}")
        print(f"  Success Criteria Met: {comparison['new_implementation']['success_criteria_met']}")
        
        print("\nImprovements:")
        print(f"  Execution Time: {metrics['execution_time_improvement']:.2f}s")
        print(f"  Steps: {metrics['steps_improvement']}")
        print(f"  Success Criteria: {metrics['success_criteria_improvement']}")
    
    # Save overall results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    framework.save_results(
        overall_results,
        f"comparison_results_{timestamp}.json"
    )
    
    # Print summary
    print("\nOverall Summary:")
    print(f"Total Tests: {overall_results['summary']['total_tests']}")
    print(f"Improvements: {overall_results['summary']['improvements']}")
    print(f"Regressions: {overall_results['summary']['regressions']}")
    print(f"No Change: {overall_results['summary']['no_change']}")

if __name__ == "__main__":
    run_comparison_tests() 