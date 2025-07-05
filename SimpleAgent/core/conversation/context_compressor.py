"""
Context Compressor Module

This module implements intelligent context compression for long-running agent tasks

The compressor maintains key decisions, events, and outcomes while reducing token usage
for conversations that exceed context window limits.
"""

import json
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict

from core.utils.config import create_client, CONTEXT_COMPRESSION_MODEL


@dataclass
class CompressedContext:
    """Represents compressed context information"""
    key_decisions: List[str]
    critical_events: List[str]
    tool_outcomes: List[str]
    current_state: str
    unresolved_issues: List[str]
    compression_timestamp: float
    original_message_count: int
    compressed_message_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class ContextCompressor:
    """
    Intelligently compresses conversation history to maintain key information
    while staying within token limits for long-running tasks.
    """
    
    def __init__(self, model: str = None):
        self.model = model or CONTEXT_COMPRESSION_MODEL
        self.client = create_client()
        self.compression_threshold = 50  # Messages before compression kicks in
        self.keep_recent_count = 10  # Always keep this many recent messages
        
    def should_compress(self, conversation_history: List[Dict[str, Any]]) -> bool:
        """
        Determine if the conversation history should be compressed.
        
        Args:
            conversation_history: The full conversation history
            
        Returns:
            True if compression is needed
        """
        return len(conversation_history) > self.compression_threshold
        
    def compress_context(self, conversation_history: List[Dict[str, Any]], 
                        task_objective: str = None) -> Tuple[List[Dict[str, Any]], CompressedContext]:
        """
        Compress conversation history while preserving key decisions and context.
        
        Args:
            conversation_history: The full conversation history
            task_objective: The main task objective for context
            
        Returns:
            (compressed_history, compression_metadata)
        """
        if not self.should_compress(conversation_history):
            return conversation_history, None
            
        # Always preserve system message and recent messages
        system_messages = [msg for msg in conversation_history if msg.get("role") == "system"]
        recent_messages = conversation_history[-self.keep_recent_count:]
        
        # Messages to compress (middle portion)
        messages_to_compress = conversation_history[len(system_messages):-self.keep_recent_count]
        
        # Clean up any orphaned tool messages in recent messages to avoid API errors
        recent_messages = self._clean_orphaned_tool_messages(recent_messages)
        
        if not messages_to_compress:
            return conversation_history, None
            
        # Create compression prompt
        compression_prompt = self._create_compression_prompt(messages_to_compress, task_objective)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": compression_prompt}],
                temperature=0.1,
                max_tokens=1000
            )
            
            compression_result = json.loads(response.choices[0].message.content)
            
            # Create compressed context object
            compressed_context = CompressedContext(
                key_decisions=compression_result.get("key_decisions", []),
                critical_events=compression_result.get("critical_events", []),
                tool_outcomes=compression_result.get("tool_outcomes", []),
                current_state=compression_result.get("current_state", ""),
                unresolved_issues=compression_result.get("unresolved_issues", []),
                compression_timestamp=time.time(),
                original_message_count=len(messages_to_compress),
                compressed_message_count=1  # Will be replaced by summary message
            )
            
            # Create a single summary message to replace the compressed portion
            summary_content = self._format_compression_summary(compressed_context)
            summary_message = {
                "role": "system", 
                "content": summary_content,
                "metadata": {"type": "compressed_context", "timestamp": compressed_context.compression_timestamp}
            }
            
            # Build new conversation history and ensure it's clean
            compressed_history = system_messages + [summary_message] + recent_messages
            compressed_history = self._clean_orphaned_tool_messages(compressed_history)
            
            return compressed_history, compressed_context
            
        except Exception as e:
            print(f"⚠️ Context compression failed: {e}")
            # Fallback: just keep system and recent messages
            return system_messages + recent_messages, None
            
    def _create_compression_prompt(self, messages: List[Dict[str, Any]], task_objective: str = None) -> str:
        """Create the prompt for context compression."""
        
        # Convert messages to a readable format
        messages_text = ""
        for i, msg in enumerate(messages):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            
            # Truncate very long messages
            if len(content) > 1000:
                content = content[:1000] + "... [truncated]"
                
            messages_text += f"\n[{i+1}] {role.upper()}: {content}\n"
            
            # Include tool calls and results if present
            if "tool_calls" in msg:
                for tool_call in msg["tool_calls"]:
                    function_name = tool_call.get("function", {}).get("name", "unknown")
                    messages_text += f"   → Called tool: {function_name}\n"
                    
        objective_context = f"\nTask Objective: {task_objective}\n" if task_objective else ""
        
        return f"""You are compressing conversation history for a long-running AI agent task. 
Extract and preserve ONLY the most critical information that future decisions depend on.

{objective_context}
Conversation History to Compress:
{messages_text}

Return a JSON object with these fields:
{{
    "key_decisions": ["Decision 1", "Decision 2", ...],
    "critical_events": ["Event 1", "Event 2", ...], 
    "tool_outcomes": ["Tool result 1", "Tool result 2", ...],
    "current_state": "Brief description of current progress/state",
    "unresolved_issues": ["Issue 1", "Issue 2", ...]
}}

Focus on:
- Decisions that affect future actions
- Successful tool operations and their results
- Errors or failures that need to be remembered
- Current progress towards the objective
- Any constraints or requirements discovered

Ignore:
- Conversational filler
- Detailed explanations that don't affect decisions
- Redundant information
- Step-by-step reasoning (keep only conclusions)"""

    def _format_compression_summary(self, compressed_context: CompressedContext) -> str:
        """Format the compressed context into a readable summary."""
        
        summary = f"""=== COMPRESSED CONTEXT SUMMARY ===
(Compressed {compressed_context.original_message_count} messages at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(compressed_context.compression_timestamp))})

CURRENT STATE: {compressed_context.current_state}

KEY DECISIONS MADE:"""
        
        for decision in compressed_context.key_decisions:
            summary += f"\n• {decision}"
            
        summary += "\n\nCRITICAL EVENTS:"
        for event in compressed_context.critical_events:
            summary += f"\n• {event}"
            
        summary += "\n\nTOOL OUTCOMES:"
        for outcome in compressed_context.tool_outcomes:
            summary += f"\n• {outcome}"
            
        if compressed_context.unresolved_issues:
            summary += "\n\nUNRESOLVED ISSUES:"
            for issue in compressed_context.unresolved_issues:
                summary += f"\n• {issue}"
                
        summary += "\n=== END COMPRESSED CONTEXT ===\n"
        
        return summary
        
    def _clean_orphaned_tool_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove tool messages that don't have corresponding tool_calls to avoid API errors.
        
        Args:
            messages: List of messages to clean
            
        Returns:
            Cleaned list of messages
        """
        cleaned_messages = []
        tool_call_ids = set()
        
        # First pass: collect all tool_call_ids
        for msg in messages:
            if msg.get("role") == "assistant" and "tool_calls" in msg:
                for tool_call in msg["tool_calls"]:
                    tool_call_ids.add(tool_call.get("id"))
        
        # Second pass: only keep tool messages that have corresponding tool_calls
        for msg in messages:
            if msg.get("role") == "tool":
                tool_call_id = msg.get("tool_call_id")
                if tool_call_id in tool_call_ids:
                    cleaned_messages.append(msg)
                # Skip orphaned tool messages
            else:
                cleaned_messages.append(msg)
                
        return cleaned_messages
        
    def estimate_token_savings(self, original_history: List[Dict[str, Any]], 
                             compressed_history: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Estimate token savings from compression.
        
        Returns:
            Dictionary with token estimates
        """
        def estimate_tokens(text: str) -> int:
            # Rough estimation: ~4 characters per token
            return len(str(text)) // 4
            
        original_tokens = sum(estimate_tokens(msg.get("content", "")) for msg in original_history)
        compressed_tokens = sum(estimate_tokens(msg.get("content", "")) for msg in compressed_history)
        
        return {
            "original_tokens": original_tokens,
            "compressed_tokens": compressed_tokens,
            "tokens_saved": original_tokens - compressed_tokens,
            "compression_ratio": compressed_tokens / original_tokens if original_tokens > 0 else 1.0
        } 