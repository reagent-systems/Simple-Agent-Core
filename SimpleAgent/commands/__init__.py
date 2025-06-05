"""
Commands package for SimpleAgent.

This package contains all the commands that SimpleAgent can execute.
Commands are organized by category in subdirectories.

This module now uses the new ToolManager from core.tool_manager to handle
both local and remote (GitHub) tools with dynamic loading support.
"""

# Import the new tool manager
from core.tool_manager import (
    REGISTERED_COMMANDS,
    COMMAND_SCHEMAS,
    register_command,
    init as _init,
    cleanup,
    load_tool,
    get_tool_manager
)

# Backward compatibility wrapper for init
def init(dynamic: bool = True) -> None:
    """Initialize the tool manager. The dynamic parameter is kept for backward compatibility."""
    # The new system always uses dynamic loading
    _init()

# Additional helper functions
def get_available_tools():
    """Get list of all available tools."""
    return get_tool_manager().list_tools()

def get_loaded_tools():
    """Get list of currently loaded tools."""
    return [name for name, tool in get_tool_manager().tools.items() if tool.loaded]

def is_tool_loaded(tool_name: str) -> bool:
    """Check if a tool is loaded."""
    tool = get_tool_manager().get_tool(tool_name)
    return tool.loaded if tool else False

# For backward compatibility - COMMANDS_BY_CATEGORY
def get_commands_by_category():
    """Get commands organized by category."""
    return get_tool_manager().list_tools_by_category()

COMMANDS_BY_CATEGORY = property(lambda self: get_commands_by_category())

# Re-export for backward compatibility
__all__ = [
    'REGISTERED_COMMANDS',
    'COMMAND_SCHEMAS', 
    'COMMANDS_BY_CATEGORY',
    'register_command',
    'init',
    'cleanup',
    'load_tool',
    'get_available_tools',
    'get_loaded_tools',
    'is_tool_loaded'
] 