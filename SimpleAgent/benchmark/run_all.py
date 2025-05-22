#!/usr/bin/env python3
"""
Run all SimpleAgent benchmark tests.

This script is a simple shortcut to run benchmark tests for all SimpleAgent commands
and generate a status.md file with the results.
"""

import os
import sys

# Add parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import test framework
from benchmark.test_framework import (
    discover_and_run_tests,
    generate_status_markdown,
    save_status_file
)

if __name__ == "__main__":
    print("Running SimpleAgent benchmark tests...")
    
    # Run all tests
    results = discover_and_run_tests()
    
    # Generate status markdown
    status_md = generate_status_markdown(results)
    
    # Save status file
    output_path = save_status_file(status_md)
    
    print(f"\nBenchmark tests completed!")
    print(f"Status file saved to: {output_path}")
    
    # Print summary
    total = 0
    working = 0
    failed = 0
    not_tested = 0
    
    for category, commands in results.items():
        for cmd, result in commands.items():
            total += 1
            if result['status'] == 'Working':
                working += 1
            elif result['status'] == 'Failed':
                failed += 1
            else:
                not_tested += 1
    
    print(f"\nSummary:")
    print(f"- Total Commands: {total}")
    if total > 0:
        print(f"- Working: {working} ({working/total*100:.1f}%)")
        print(f"- Failed: {failed} ({failed/total*100:.1f}%)")
        print(f"- Not Tested: {not_tested} ({not_tested/total*100:.1f}%)")
    else:
        print("- No commands found to test") 