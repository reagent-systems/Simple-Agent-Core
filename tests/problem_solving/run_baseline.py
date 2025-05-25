"""
Baseline Test Runner

This script runs the test cases with the current implementation only
to establish a baseline for comparison.
"""

import os
import sys
import json
import time
from datetime import datetime

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from test_framework import TestFramework, TaskStatus
from test_cases import TEST_CASES

def run_baseline_tests():
    """
    Run all test cases with the current implementation to establish a baseline.
    """
    print("Running baseline tests with current SimpleAgent implementation...")
    print("=" * 60)
    
    # Initialize test framework
    framework = TestFramework(output_dir="test_results")
    
    # Track baseline results
    baseline_results = {
        "timestamp": datetime.now().isoformat(),
        "implementation": "current",
        "test_cases": [],
        "summary": {
            "total_tests": len(TEST_CASES),
            "completed": 0,
            "failed": 0,
            "total_execution_time": 0,
            "total_steps": 0
        }
    }
    
    # Run each test case
    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"\n[{i}/{len(TEST_CASES)}] Running test case: {test_case.task_id}")
        print(f"Description: {test_case.description}")
        print("-" * 40)
        
        # Run the test with current implementation
        result = framework.run_test(test_case, "old")
        
        # Convert result to dictionary for JSON serialization
        result_dict = {
            "task_id": result.task_id,
            "status": result.status.value,
            "execution_time": result.execution_time,
            "steps_taken": result.steps_taken,
            "success_criteria_met": result.success_criteria_met,
            "success_criteria_failed": result.success_criteria_failed,
            "error_messages": result.error_messages,
            "feedback_loop_iterations": result.feedback_loop_iterations
        }
        
        baseline_results["test_cases"].append(result_dict)
        
        # Update summary
        if result.status == TaskStatus.COMPLETED:
            baseline_results["summary"]["completed"] += 1
        else:
            baseline_results["summary"]["failed"] += 1
        
        baseline_results["summary"]["total_execution_time"] += result.execution_time
        baseline_results["summary"]["total_steps"] += result.steps_taken
        
        # Print results
        print(f"Status: {result.status.value}")
        print(f"Execution Time: {result.execution_time:.2f}s")
        print(f"Steps Taken: {result.steps_taken}")
        print(f"Success Criteria Met: {len(result.success_criteria_met)}")
        print(f"Success Criteria Failed: {len(result.success_criteria_failed)}")
        
        if result.success_criteria_met:
            print(f"✅ Met: {', '.join(result.success_criteria_met)}")
        
        if result.success_criteria_failed:
            print(f"❌ Failed: {', '.join(result.success_criteria_failed)}")
        
        if result.error_messages:
            print(f"🚨 Errors: {', '.join(result.error_messages)}")
    
    # Save baseline results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    framework.save_results(
        baseline_results,
        f"baseline_results_{timestamp}.json"
    )
    
    # Print summary
    print("\n" + "=" * 60)
    print("BASELINE SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {baseline_results['summary']['total_tests']}")
    print(f"Completed Successfully: {baseline_results['summary']['completed']}")
    print(f"Failed: {baseline_results['summary']['failed']}")
    print(f"Success Rate: {(baseline_results['summary']['completed'] / baseline_results['summary']['total_tests'] * 100):.1f}%")
    print(f"Total Execution Time: {baseline_results['summary']['total_execution_time']:.2f}s")
    print(f"Average Execution Time: {(baseline_results['summary']['total_execution_time'] / baseline_results['summary']['total_tests']):.2f}s")
    print(f"Total Steps: {baseline_results['summary']['total_steps']}")
    print(f"Average Steps: {(baseline_results['summary']['total_steps'] / baseline_results['summary']['total_tests']):.1f}")
    
    print(f"\nBaseline results saved to: baseline_results_{timestamp}.json")
    
    return baseline_results

if __name__ == "__main__":
    run_baseline_tests() 