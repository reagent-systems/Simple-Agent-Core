"""
Core package for SimpleAgent.

This package contains the core components of the SimpleAgent system.
"""

from core.agent import SimpleAgent
from core.summarizer import ChangeSummarizer
from core.conversation import ConversationManager
from core.execution import ExecutionManager
from core.memory import MemoryManager
from core.run_manager import RunManager
from core.security import get_secure_path

# Terminal control system
from core.terminal import TerminalManager, TerminalSession, register_terminal_commands

__all__ = [
    "SimpleAgent", 
    "ChangeSummarizer",
    "ConversationManager",
    "ExecutionManager",
    "MemoryManager",
    "RunManager",
    "get_secure_path",
    "TerminalManager",
    "TerminalSession",
    "register_terminal_commands"
] 