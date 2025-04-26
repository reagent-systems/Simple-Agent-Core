"""
SimpleAgent Memory Module

This module handles the memory operations for SimpleAgent, including saving and loading
conversation history and file changes.
"""

import os
from typing import Dict, Any, List

# Import commands package for file operations
import commands
from core.config import MEMORY_FILE, OUTPUT_DIR


class MemoryManager:
    """
    Manages the agent's memory, including conversation history and file changes.
    """
    
    def __init__(self, memory_file: str = MEMORY_FILE):
        """
        Initialize the memory manager.
        
        Args:
            memory_file: Path to the memory file
        """
        self.memory_file = memory_file
        self.memory = self._load_memory()
        
    def _load_memory(self) -> Dict[str, Any]:
        """
        Load the agent's memory from the memory file.
        
        Returns:
            The loaded memory or a new memory object if the file doesn't exist
        """
        if commands.REGISTERED_COMMANDS["file_exists"](self.memory_file):
            memory = commands.REGISTERED_COMMANDS["load_json"](self.memory_file)
            print(f"Loaded memory from {self.memory_file}")
            return memory
        else:
            return {"conversations": [], "files_created": [], "files_modified": []}
            
    def save_memory(self) -> None:
        """Save the agent's memory to the memory file."""
        commands.REGISTERED_COMMANDS["save_json"](self.memory_file, self.memory)
        print(f"Saved memory to {self.memory_file}")
        
    def add_conversation(self, conversation: List[Dict[str, Any]]) -> None:
        """
        Add a conversation to the memory.
        
        Args:
            conversation: The conversation to add
        """
        self.memory["conversations"].append(conversation)
        
    def add_file_created(self, file_path: str) -> None:
        """
        Add a created file to the memory.
        
        Args:
            file_path: The path of the created file
        """
        if file_path not in self.memory["files_created"]:
            self.memory["files_created"].append(file_path)
            
    def add_file_modified(self, file_path: str) -> None:
        """
        Add a modified file to the memory.
        
        Args:
            file_path: The path of the modified file
        """
        if file_path not in self.memory["files_modified"]:
            self.memory["files_modified"].append(file_path)
            
    def get_memory(self) -> Dict[str, Any]:
        """
        Get the current memory.
        
        Returns:
            The current memory
        """
        return self.memory 