"""
Run benchmarks for SimpleAgent commands.

This script runs tests for all SimpleAgent commands and 
generates a status.md file with the results.
"""

import os
import sys
import argparse

from benchmark.test_framework import (
    discover_and_run_tests,
    generate_status_markdown,
    save_status_file
)

def main():
    parser = argparse.ArgumentParser(description='Run benchmark tests for SimpleAgent commands.')
    parser.add_argument('--output', '-o', default=None, 
                        help='Output file path for status.md (default: SimpleAgent/status.md)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Ensure we can import SimpleAgent modules
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    print("Starting SimpleAgent benchmark tests...")
    
    try:
        # Run all tests
        results = discover_and_run_tests()
        
        # Generate status markdown
        status_md = generate_status_markdown(results)
        
        # Save status file
        output_path = save_status_file(status_md, args.output)
        
        print(f"\nBenchmark tests completed!")
        print(f"Status file saved to: {output_path}")
        
        return 0
    
    except Exception as e:
        print(f"Error running benchmark tests: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 