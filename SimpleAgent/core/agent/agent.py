"""
SimpleAgent Agent Module

This module contains the SimpleAgent agent class that serves as the main
interface for using the agent. It delegates to specialized modules for
conversation management, execution, memory, and security.

Security Notes:
- All file operations are restricted to the output directory
- Multiple layers of path validation prevent directory traversal attacks
- Absolute paths and path traversal attempts (../) are sanitized
"""

import os
from typing import List, Dict, Any, Optional

from core.conversation.conversation import ConversationManager
from core.execution.execution import ExecutionManager
from core.conversation.memory import MemoryManager
from core.agent.run_manager import RunManager
from core.utils.security import get_secure_path
from core.utils.config import DEFAULT_MODEL, OUTPUT_DIR
from core.utils.input_manager import InputManager


class SimpleAgent:
    """
    SimpleAgent class that serves as the main interface for using the agent.
    This class coordinates the conversation, execution, memory, and security modules.
    """
    
    def __init__(self, model: str = None, output_dir: str = None):
        """
        Initialize the SimpleAgent agent.
        
        Args:
            model: The OpenAI model to use (defaults to config value)
            output_dir: The output directory for file operations (defaults to config value)
        """
        self.model = model or DEFAULT_MODEL
        self.output_dir = output_dir or OUTPUT_DIR
        
        # Create the run manager that will coordinate all operations
        self.run_manager = RunManager(model=self.model, output_dir=self.output_dir)
        
        # Direct access to the components for advanced usage
        self.conversation_manager = self.run_manager.conversation_manager
        self.execution_manager = self.run_manager.execution_manager
        self.memory_manager = self.run_manager.memory_manager
        
        # Initialize input manager for accessing input files
        self.input_manager = InputManager()
        
        # Initialize memory
        self.memory = self.memory_manager.get_memory()
        
    def set_output_dir(self, output_dir: str):
        """
        Update the output directory for the agent and all managers.
        """
        self.output_dir = output_dir
        self.run_manager.output_dir = output_dir
        self.execution_manager.output_dir = output_dir
        
    def run(self, user_instruction: str, max_steps: int = 10, auto_continue: int = 0):
        """
        Run the SimpleAgent agent with the given instruction.
        
        Args:
            user_instruction: The instruction from the user
            max_steps: Maximum number of steps to run
            auto_continue: Number of steps to auto-continue (0 = disabled, -1 = infinite)
        """
        # Delegate to the run manager
        self.run_manager.run(
            user_instruction=user_instruction,
            max_steps=max_steps,
            auto_continue=auto_continue
        )
        
        # Update memory reference after run
        self.memory = self.memory_manager.get_memory()
        
    def request_stop(self):
        """
        Request the agent to stop execution at the next convenient point.
        
        Returns:
            True to indicate stop was requested
        """
        return self.execution_manager.request_stop()
        
    def get_next_action(self):
        """
        Get the next action from the model.
        
        Returns:
            The model's response
        """
        return self.execution_manager.get_next_action(
            self.conversation_manager.get_history()
        )
        
    def load_memory(self):
        """
        Explicitly load the agent's memory from the memory file.
        
        Returns:
            The loaded memory
        """
        self.memory = self.memory_manager._load_memory()
        return self.memory
        
    def save_memory(self):
        """
        Explicitly save the agent's memory to the memory file.
        """
        self.memory_manager.save_memory()
        
    def add_to_conversation(self, role: str, content: str, **kwargs):
        """
        Add a message to the conversation history.
        
        Args:
            role: The role of the message sender (user, assistant, system, tool)
            content: The content of the message
            **kwargs: Additional fields for tool responses
        """
        self.conversation_manager.add_message(role, content, **kwargs)
        
    def get_secure_path(self, file_path: str) -> str:
        """
        Convert any file path to be within the output directory.
        
        Args:
            file_path: Original file path
            
        Returns:
            Modified file path within output directory
        """
        return get_secure_path(file_path, self.output_dir)
    
    def list_input_files(self) -> List[str]:
        """
        List all available input files.
        
        Returns:
            List of input file names
        """
        files = self.input_manager.list_input_files()
        return [f.name for f in files]
    
    def read_input_file(self, filename: str) -> str:
        """
        Read the contents of an input file.
        
        Args:
            filename: Name of the file to read
            
        Returns:
            File contents as string
        """
        return self.input_manager.read_input_file(filename)
    
    def get_input_file_info(self, filename: str) -> Dict[str, Any]:
        """
        Get information about an input file.
        
        Args:
            filename: Name of the file
            
        Returns:
            Dictionary with file information
        """
        file_info = self.input_manager.get_input_file_info(filename)
        return {
            'name': file_info.name,
            'size': file_info.size,
            'extension': file_info.extension,
            'mime_type': file_info.mime_type,
            'modified_time': file_info.modified_time.isoformat(),
            'is_text': file_info.is_text
        }
    
    def input_file_exists(self, filename: str) -> bool:
        """
        Check if an input file exists.
        
        Args:
            filename: Name of the file to check
            
        Returns:
            True if file exists and is accessible, False otherwise
        """
        return self.input_manager.file_exists(filename)
