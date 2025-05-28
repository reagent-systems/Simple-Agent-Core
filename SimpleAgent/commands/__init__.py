"""
Commands package for SimpleAgent.

This package contains all the commands that SimpleAgent can execute.
Commands are organized by category in subdirectories.

This module now uses the new ToolManager from core.tool_manager to handle
both local and remote (GitHub) tools.
"""

# Import the new tool manager
from core.tool_manager import (
    REGISTERED_COMMANDS,
    COMMAND_SCHEMAS,
    COMMANDS_BY_CATEGORY,
    register_command,
    init,
    cleanup
)

# Re-export for backward compatibility
__all__ = [
    'REGISTERED_COMMANDS',
    'COMMAND_SCHEMAS', 
    'COMMANDS_BY_CATEGORY',
    'register_command',
    'init',
    'cleanup'
] 