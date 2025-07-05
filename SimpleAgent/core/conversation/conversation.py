"""
SimpleAgent Conversation Module

This module handles the conversation history and message management for SimpleAgent.
"""

from typing import List, Dict, Any, Optional, Tuple
from core.conversation.context_compressor import ContextCompressor, CompressedContext


class ConversationManager:
    """
    Manages the conversation history for the SimpleAgent with intelligent context compression.
    """
    
    def __init__(self, memory_manager=None):
        """Initialize the conversation manager."""
        self.conversation_history = []
        self.context_compressor = ContextCompressor()
        self.compression_history = []  # Track compression events
        self.task_objective = None  # Set by the agent to help with compression
        self.memory_manager = memory_manager  # Optional memory manager for persistence
        
    def add_message(self, role: str, content: str, **kwargs) -> None:
        """
        Add a message to the conversation history.
        
        Args:
            role: The role of the message sender (user, assistant, system, tool)
            content: The content of the message
            **kwargs: Additional fields for tool responses
        """
        message = {"role": role, "content": content}
        
        # Add additional fields for tool responses if provided
        for key, value in kwargs.items():
            message[key] = value
            
        self.conversation_history.append(message)
    
    def update_system_message(self, new_content: str) -> None:
        """
        Update the system message in the conversation history.
        
        Args:
            new_content: The new content for the system message
        """
        if self.conversation_history and self.conversation_history[0]["role"] == "system":
            self.conversation_history[0]["content"] = new_content
        else:
            # If there's no system message yet, add it
            self.conversation_history.insert(0, {"role": "system", "content": new_content})
    
    def clear(self) -> None:
        """Clear the conversation history."""
        self.conversation_history = []
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get the current conversation history."""
        return self.conversation_history
        
    def set_task_objective(self, objective: str) -> None:
        """
        Set the main task objective for better context compression.
        
        Args:
            objective: The primary objective of the current task
        """
        self.task_objective = objective
        
    def compress_if_needed(self) -> bool:
        """
        Compress conversation history if it's getting too long.
        
        Returns:
            True if compression was performed
        """
        if not self.context_compressor.should_compress(self.conversation_history):
            return False
            
        print(f"🗜️ Compressing conversation history ({len(self.conversation_history)} messages)")
        
        compressed_history, compression_metadata = self.context_compressor.compress_context(
            self.conversation_history, 
            self.task_objective
        )
        
        if compressed_history and compression_metadata:
            # Calculate savings
            token_savings = self.context_compressor.estimate_token_savings(
                self.conversation_history, 
                compressed_history
            )
            
            # Update conversation history
            old_length = len(self.conversation_history)
            self.conversation_history = compressed_history
            new_length = len(self.conversation_history)
            
            # Track compression event
            compression_event = {
                "timestamp": compression_metadata.compression_timestamp,
                "original_messages": old_length,
                "compressed_messages": new_length,
                "token_savings": token_savings,
                "metadata": compression_metadata.to_dict()  # Convert to dict for JSON serialization
            }
            self.compression_history.append(compression_event)
            
            # Persist to memory if available
            if self.memory_manager:
                self.memory_manager.add_context_compression(compression_event)
            
            print(f"✅ Compressed {old_length} → {new_length} messages")
            print(f"💾 Estimated token savings: {token_savings['tokens_saved']} tokens ({token_savings['compression_ratio']:.1%} of original)")
            
            return True
        else:
            print("⚠️ Context compression failed, continuing with full history")
            return False
            
    def get_compression_stats(self) -> Dict[str, Any]:
        """
        Get statistics about context compression usage.
        
        Returns:
            Dictionary with compression statistics
        """
        if not self.compression_history:
            return {"total_compressions": 0, "total_tokens_saved": 0}
            
        total_tokens_saved = sum(
            comp["token_savings"]["tokens_saved"] 
            for comp in self.compression_history
        )
        
        return {
            "total_compressions": len(self.compression_history),
            "total_tokens_saved": total_tokens_saved,
            "latest_compression": self.compression_history[-1]["timestamp"] if self.compression_history else None,
            "compression_events": self.compression_history
        } 