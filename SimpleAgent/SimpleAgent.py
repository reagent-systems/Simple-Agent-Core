"""
SimpleAgent - A minimalist AI agent framework

This script implements a simple AI agent that can perform basic operations
through function calling. It uses the OpenAI API to generate responses and
execute functions based on user instructions.
"""

import os
import sys
import json
import time
import argparse
import logging
from typing import List, Dict, Any, Optional, Callable

# Set up basic logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Import commands package
import commands
from commands import REGISTERED_COMMANDS, COMMAND_SCHEMAS

# Import core modules
from core.agent import SimpleAgent
from core.config import OPENAI_API_KEY, MAX_STEPS

# Import benchmark modules
try:
    from benchmark.test_framework import discover_and_run_tests, generate_status_markdown, save_status_file
    BENCHMARK_AVAILABLE = True
except ImportError:
    BENCHMARK_AVAILABLE = False

# Initialize commands
commands.init()

# Check for API key
if not OPENAI_API_KEY:
    logging.error("Error: OPENAI_API_KEY environment variable not set.")
    logging.info("Please set it in a .env file or in your environment variables.")
    sys.exit(1)


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='SimpleAgent - An AI agent that can perform tasks')
    # Add flags first to prevent instruction from being consumed as a flag value
    parser.add_argument('-a', '--auto', type=int, nargs='?', const=10, default=0,
                      help='Auto-continue for N steps (default: 10 if no number provided)')
    parser.add_argument('-m', '--max-steps', type=int, default=10,
                      help='Maximum number of steps to run (default: 10)')
    parser.add_argument('-b', '--benchmark', action='store_true',
                      help='Run benchmark tests for all commands')
    parser.add_argument('-s', '--status', action='store_true',
                      help='Generate a status report for all commands without running tests')
    parser.add_argument('-o', '--output', default=None,
                      help='Output file path for status.md (default: SimpleAgent/status.md)')
    parser.add_argument('instruction', nargs='*', help='The instruction for the AI agent')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Run benchmarks if requested
    if args.benchmark:
        if not BENCHMARK_AVAILABLE:
            print("Error: Benchmark module not available. Please install it first.")
            return 1
        
        print("Running benchmark tests for all commands...")
        results = discover_and_run_tests()
        status_md = generate_status_markdown(results)
        output_path = save_status_file(status_md, args.output)
        print(f"Benchmark tests completed! Status file saved to: {output_path}")
        return 0
    
    # Generate status report if requested
    if args.status:
        if not BENCHMARK_AVAILABLE:
            print("Error: Benchmark module not available. Please install it first.")
            return 1
        
        status_path = args.output or os.path.join(os.path.dirname(__file__), 'status.md')
        if os.path.exists(status_path):
            print(f"Status report is available at: {status_path}")
            with open(status_path, 'r', encoding='utf-8') as f:
                # Print summary section
                for line in f:
                    print(line.strip())
                    if line.strip() == "## Command Status by Category":
                        break
        else:
            print(f"Status report not found. Run with --benchmark to generate it.")
        return 0
    
    # Ensure instruction is provided if not running benchmarks or status
    if not args.instruction:
        parser.print_help()
        return 1
    
    # Join the instruction parts back together
    instruction = ' '.join(args.instruction)
    
    # Ensure max_steps is at least as large as auto_continue
    max_steps = max(args.max_steps, args.auto) if args.auto > 0 else args.max_steps
    
    # Initialize and run the agent
    agent = SimpleAgent()
    agent.run(instruction, max_steps=max_steps, auto_continue=args.auto)
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 