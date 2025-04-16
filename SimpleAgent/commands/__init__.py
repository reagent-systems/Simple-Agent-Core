"""
Commands package for SimpleAgent.

This package contains all the commands that SimpleAgent can execute.
Commands are organized by category in subdirectories.
"""

import os
import importlib
import pkgutil
import logging
from typing import Dict, Any, Callable, List
from collections import defaultdict

# Setup logger
def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # add formatter to ch
    ch.setFormatter(formatter)
    # add ch to logger
    logger.addHandler(ch)
    return logger

# Dictionary to store all registered commands
REGISTERED_COMMANDS: Dict[str, Callable] = {}

# Dictionary to store all command schemas
COMMAND_SCHEMAS: List[Dict[str, Any]] = []

# Dictionary to store commands by category
COMMANDS_BY_CATEGORY: Dict[str, List[str]] = defaultdict(list)

# Setup logger
logger = setup_logger('simple_agent_core')


def register_command(name: str, func: Callable, schema: Dict[str, Any]) -> None:
    """
    Register a command with SimpleAgent.
    
    Args:
        name: The name of the command
        func: The function to execute
        schema: The OpenAI function schema for the command
    """
    REGISTERED_COMMANDS[name] = func
    COMMAND_SCHEMAS.append(schema)
    
    # Determine category from the module path
    module = func.__module__
    category = module.split('.')[1] if len(module.split('.')) > 1 else 'misc'
    COMMANDS_BY_CATEGORY[category].append(name)
    logger.info(f'Registered command: {name} in category {category}')


def discover_commands() -> None:
    """
    Discover and register all commands in the commands package.
    This function walks through all subdirectories and imports all modules.
    """
    # Get the directory of the current package
    package_dir = os.path.dirname(__file__)
    
    # Walk through all subdirectories
    for _, category_name, is_pkg in pkgutil.iter_modules([package_dir]):
        if is_pkg:
            # Import the category package
            category_package = importlib.import_module(f"commands.{category_name}")
            
            # Get the category directory
            category_dir = os.path.join(package_dir, category_name)
            
            # Walk through all modules in the category
            for _, command_name, _ in pkgutil.iter_modules([category_dir]):
                # Import the command module
                importlib.import_module(f"commands.{category_name}.{command_name}")


def print_commands() -> None:
    """Print all registered commands in a nicely formatted way."""
    print("\n Available Commands:")
    print("=" * 50)
    
    if not COMMANDS_BY_CATEGORY:
        print("No commands registered yet.")
        return
        
    # Calculate the longest command name for padding
    max_length = max(len(cmd) for cmds in COMMANDS_BY_CATEGORY.values() for cmd in cmds)
    
    # Sort categories and commands
    for category in sorted(COMMANDS_BY_CATEGORY.keys()):
        # Format category name
        category_display = category.replace('_', ' ').title()
        print(f"\n {category_display} Commands:")
        print("-" * 30)
        
        # Sort commands within category
        for cmd in sorted(COMMANDS_BY_CATEGORY[category]):
            # Get command description from schema
            description = next((schema['function']['description'] 
                             for schema in COMMAND_SCHEMAS 
                             if schema['function']['name'] == cmd), 
                             "No description available")
            
            # Print command with padding and description
            print(f"  {cmd:<{max_length + 2}}  {description}")
    
    print("\n" + "=" * 50)
    print(f"Total commands: {len(REGISTERED_COMMANDS)}\n")


# Initialize the commands package
def init():
    """Initialize the commands package by discovering all commands."""
    discover_commands()
    print_commands() 
