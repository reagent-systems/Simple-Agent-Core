"""
Terminal Core Module for SimpleAgent

This module provides terminal control capabilities as a core feature.
Allows agents to execute shell commands, interact with CLI tools, and maintain
persistent terminal sessions.
"""

from .terminal_manager import SimpleTerminalManager, SimpleTerminalSession
from .commands import register_terminal_commands

# For backward compatibility, also export with original names
TerminalManager = SimpleTerminalManager
TerminalSession = SimpleTerminalSession

__all__ = [
    'SimpleTerminalManager',
    'SimpleTerminalSession', 
    'TerminalManager',
    'TerminalSession',
    'register_terminal_commands'
] 