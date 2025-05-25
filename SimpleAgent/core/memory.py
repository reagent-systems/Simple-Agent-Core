"""
SimpleAgent Memory Module

This module handles the memory operations for SimpleAgent, including saving and loading
conversation history and file changes.
"""

import os
import json
from typing import Dict, Any, List

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
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    memory = json.load(f)
                print(f"Loaded memory from {self.memory_file}")
                return memory
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading memory from {self.memory_file}: {e}")
                return {"conversations": [], "files_created": [], "files_modified": []}
        else:
            return {"conversations": [], "files_created": [], "files_modified": []}
            
    def save_memory(self) -> None:
        """Save the agent's memory to the memory file."""
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
            
            with open(self.memory_file, 'w') as f:
                json.dump(self.memory, f, indent=2)
            print(f"Saved memory to {self.memory_file}")
        except IOError as e:
            print(f"Error saving memory to {self.memory_file}: {e}")
        
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