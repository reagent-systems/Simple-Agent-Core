"""
SimpleAgent Conversation Module

This module handles the conversation history and message management for SimpleAgent.
"""

from typing import List, Dict, Any, Optional


class ConversationManager:
    """
    Manages the conversation history for the SimpleAgent.
    """
    
    def __init__(self):
        """Initialize the conversation manager."""
        self.conversation_history = []
        
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