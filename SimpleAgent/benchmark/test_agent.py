"""
Tests for the main SimpleAgent class functionality.

This module contains benchmark tests for the SimpleAgent class itself.
"""

import os
from typing import Tuple, Dict, Any
import unittest.mock as mock

from benchmark.test_framework import TEST_OUTPUT_DIR
from core.agent import SimpleAgent
from core.config import DEFAULT_MODEL

def test_agent_initialization() -> Tuple[bool, str]:
    """Test the SimpleAgent initialization."""
    try:
        # Create agent with default model
        agent = SimpleAgent()
        
        # Verify that components are initialized
        if not agent.model:
            return False, "Agent model not initialized"
            
        if not agent.output_dir:
            return False, "Agent output_dir not initialized"
            
        if not agent.conversation_manager:
            return False, "Agent conversation_manager not initialized"
            
        if not agent.execution_manager:
            return False, "Agent execution_manager not initialized"
            
        if not agent.memory_manager:
            return False, "Agent memory_manager not initialized"
            
        # Verify model is set correctly
        if agent.model != DEFAULT_MODEL:
            return False, f"Agent model mismatch: {agent.model} != {DEFAULT_MODEL}"
            
        return True, "Agent initialized successfully"
    except Exception as e:
        return False, f"Exception: {str(e)}"

def test_agent_run() -> Tuple[bool, str]:
    """Test the SimpleAgent run method with mocked execution."""
    try:
        # Create agent
        agent = SimpleAgent()
        
        # Mock run_manager.run method to avoid actual execution
        agent.run_manager.run = mock.Mock()
        
        # Call run method
        agent.run("Test instruction", max_steps=5, auto_continue=2)
        
        # Verify run was called with correct arguments
        agent.run_manager.run.assert_called_once_with(
            user_instruction="Test instruction",
            max_steps=5,
            auto_continue=2
        )
            
        return True, "Agent run method called successfully"
    except Exception as e:
        return False, f"Exception: {str(e)}"

def test_agent_memory() -> Tuple[bool, str]:
    """Test the SimpleAgent memory operations."""
    try:
        # Create agent
        agent = SimpleAgent()
        
        # Mock memory manager methods to avoid file operations
        agent.memory_manager._load_memory = mock.Mock(return_value={"test_key": "test_value"})
        agent.memory_manager.save_memory = mock.Mock()
        
        # Test loading memory
        memory = agent.load_memory()
        
        # Verify memory was loaded
        if not memory or not isinstance(memory, dict):
            return False, f"Expected dict memory, got: {type(memory)}"
            
        if memory.get("test_key") != "test_value":
            return False, f"Memory content mismatch: {memory}"
            
        # Verify memory manager method was called
        agent.memory_manager._load_memory.assert_called_once()
        
        # Test saving memory
        agent.save_memory()
        
        # Verify memory manager method was called
        agent.memory_manager.save_memory.assert_called_once()
            
        return True, "Agent memory operations successful"
    except Exception as e:
        return False, f"Exception: {str(e)}" 