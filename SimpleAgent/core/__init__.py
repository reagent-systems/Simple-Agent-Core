"""
Core package for SimpleAgent.

This package contains the core components of the SimpleAgent system.
"""

from core.agent.agent import SimpleAgent
from core.execution.summarizer import ChangeSummarizer
from core.conversation.conversation import ConversationManager
from core.execution.execution import ExecutionManager
from core.conversation.memory import MemoryManager
from core.agent.run_manager import RunManager
from core.utils.security import get_secure_path
from core.utils.input_manager import InputManager

__all__ = [
    "SimpleAgent", 
    "ChangeSummarizer",
    "ConversationManager",
    "ExecutionManager",
    "MemoryManager",
    "RunManager",
    "get_secure_path",
    "InputManager"
]
