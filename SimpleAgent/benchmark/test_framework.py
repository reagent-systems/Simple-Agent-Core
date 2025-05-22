"""
Test framework for SimpleAgent commands.

This module provides a framework for testing all SimpleAgent commands
and generating a status report in Markdown format.
"""

import os
import importlib
import inspect
import pkgutil
import time
import json
import shutil
from typing import Dict, List, Callable, Any, Tuple
from datetime import datetime

# Import SimpleAgent modules
import commands
from commands import REGISTERED_COMMANDS, COMMANDS_BY_CATEGORY
from core.agent import SimpleAgent

# Initialize test results dictionary
test_results = {}

# Setup test environment
TEST_OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'test_output')

def setup_test_environment():
    """Setup the test environment including test directories."""
    # Create test directory if it doesn't exist
    if not os.path.exists(TEST_OUTPUT_DIR):
        os.makedirs(TEST_OUTPUT_DIR)
    else:
        # Clean up any previous test files
        for filename in os.listdir(TEST_OUTPUT_DIR):
            file_path = os.path.join(TEST_OUTPUT_DIR, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')

def discover_test_modules() -> List[str]:
    """
    Discover all test modules in the benchmark package.
    
    Returns:
        List of test module names
    """
    test_modules = []
    package_dir = os.path.dirname(__file__)
    
    for _, module_name, is_pkg in pkgutil.iter_modules([package_dir]):
        if not is_pkg and module_name.startswith('test_') and module_name != 'test_framework':
            test_modules.append(module_name)
    
    return test_modules

def run_test(test_func: Callable, test_name: str) -> Tuple[bool, str]:
    """
    Run a single test function and return the results.
    
    Args:
        test_func: The test function to run
        test_name: The name of the test
        
    Returns:
        Tuple of (success, message)
    """
    start_time = time.time()
    try:
        result = test_func()
        elapsed_time = time.time() - start_time
        
        # If the test returns a tuple with a boolean and a message
        if isinstance(result, tuple) and len(result) == 2 and isinstance(result[0], bool):
            success, message = result
            return success, f"{message} (Completed in {elapsed_time:.2f}s)"
        
        # If the test just returns a boolean
        elif isinstance(result, bool):
            return result, f"Completed in {elapsed_time:.2f}s"
        
        # If the test doesn't return anything, assume success
        elif result is None:
            return True, f"Completed in {elapsed_time:.2f}s"
        
        # Otherwise, convert the result to a string message
        else:
            return True, f"{result} (Completed in {elapsed_time:.2f}s)"
    
    except Exception as e:
        elapsed_time = time.time() - start_time
        return False, f"Error: {str(e)} (Failed after {elapsed_time:.2f}s)"

def discover_and_run_tests() -> Dict[str, Dict[str, Any]]:
    """
    Discover and run all tests for SimpleAgent commands.
    
    Returns:
        Dictionary of test results by category and command
    """
    # Initialize commands
    commands.init()
    
    # Setup test environment
    setup_test_environment()
    
    # Discover test modules
    test_modules = discover_test_modules()
    print(f"Discovered {len(test_modules)} test modules: {test_modules}")
    
    # Import test modules
    for module_name in test_modules:
        try:
            importlib.import_module(f"benchmark.{module_name}")
            print(f"Imported test module: {module_name}")
        except ImportError as e:
            print(f"Error importing test module {module_name}: {e}")
    
    # Initialize results dictionary with categories and commands
    results = {}
    for category, cmd_list in COMMANDS_BY_CATEGORY.items():
        results[category] = {}
        for cmd in cmd_list:
            results[category][cmd] = {
                "status": "Not Tested",
                "message": "No test available",
                "timestamp": datetime.now().isoformat()
            }
    
    # Find test functions for each command
    for test_module_name in test_modules:
        module = importlib.import_module(f"benchmark.{test_module_name}")
        
        # Get all test functions from the module
        test_functions = inspect.getmembers(module, 
                         lambda member: inspect.isfunction(member) and member.__name__.startswith('test_'))
        
        for func_name, test_func in test_functions:
            # Extract command name from test function name (removing 'test_' prefix)
            cmd_name = func_name[5:]  # Remove 'test_' prefix
            
            # Find category for this command
            category = None
            for cat, cmds in COMMANDS_BY_CATEGORY.items():
                if cmd_name in cmds:
                    category = cat
                    break
            
            if category:
                print(f"Running test for {category}.{cmd_name}...")
                success, message = run_test(test_func, func_name)
                
                # Update results
                results[category][cmd_name] = {
                    "status": "Working" if success else "Failed",
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                print(f"Warning: Could not find category for command '{cmd_name}'")
    
    return results

def generate_status_markdown(results: Dict[str, Dict[str, Any]]) -> str:
    """
    Generate a Markdown file with the status of all commands.
    
    Args:
        results: Test results by category and command
        
    Returns:
        Markdown string with command status
    """
    md_content = "# SimpleAgent Command Status\n\n"
    md_content += f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    # Count totals
    total_commands = 0
    working_commands = 0
    failed_commands = 0
    untested_commands = 0
    
    for category, commands in results.items():
        for cmd, result in commands.items():
            total_commands += 1
            if result['status'] == 'Working':
                working_commands += 1
            elif result['status'] == 'Failed':
                failed_commands += 1
            else:
                untested_commands += 1
    
    # Add summary
    md_content += "## Summary\n\n"
    md_content += f"- Total Commands: {total_commands}\n"
    md_content += f"- Working: {working_commands} ({working_commands/total_commands*100:.1f}%)\n"
    md_content += f"- Failed: {failed_commands} ({failed_commands/total_commands*100:.1f}%)\n"
    md_content += f"- Not Tested: {untested_commands} ({untested_commands/total_commands*100:.1f}%)\n\n"
    
    # Add details by category
    md_content += "## Command Status by Category\n\n"
    
    for category in sorted(results.keys()):
        category_display = category.replace('_', ' ').title()
        md_content += f"### {category_display} Commands\n\n"
        
        md_content += "| Command | Status | Message |\n"
        md_content += "|---------|--------|--------|\n"
        
        commands = results[category]
        for cmd_name in sorted(commands.keys()):
            result = commands[cmd_name]
            status_emoji = "✅" if result['status'] == 'Working' else "❌" if result['status'] == 'Failed' else "⚠️"
            md_content += f"| `{cmd_name}` | {status_emoji} {result['status']} | {result['message']} |\n"
        
        md_content += "\n"
    
    return md_content

def save_status_file(markdown_content: str, filepath: str = None) -> str:
    """
    Save the status markdown to a file.
    
    Args:
        markdown_content: The markdown content to save
        filepath: The file path to save to (default: SimpleAgent/status.md)
        
    Returns:
        The path to the saved file
    """
    if filepath is None:
        filepath = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'status.md')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    return filepath 