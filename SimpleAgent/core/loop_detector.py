"""
Loop Detection Module

This module detects when the AI agent is stuck in repetitive loops and provides
feedback to help the agent break out of unproductive patterns.
"""

import difflib
from typing import List, Dict, Any, Optional
from collections import deque


class LoopDetector:
    """
    Detects when the agent is stuck in repetitive loops and provides feedback
    to help break out of unproductive patterns.
    """
    
    def __init__(self, window_size: int = 5, similarity_threshold: float = 0.7):
        """
        Initialize the loop detector.
        
        Args:
            window_size: Number of recent responses to analyze for loops
            similarity_threshold: Minimum similarity ratio to consider responses as repetitive (0.0-1.0)
        """
        self.window_size = window_size
        self.similarity_threshold = similarity_threshold
        self.response_history = deque(maxlen=window_size)
        self.loop_count = 0
        self.last_loop_detection_step = -1
        
    def add_response(self, response_content: str, step_number: int, has_tool_calls: bool = False):
        """
        Add a response to the history for loop detection.
        
        Args:
            response_content: The content of the assistant's response
            step_number: The current step number
            has_tool_calls: Whether this response included tool calls (actions)
        """
        self.response_history.append({
            'content': response_content.strip(),
            'step': step_number,
            'has_tool_calls': has_tool_calls,
            'length': len(response_content.strip())
        })
        
    def detect_loop(self, current_step: int) -> Optional[Dict[str, Any]]:
        """
        Detect if the agent is stuck in a loop.
        
        Args:
            current_step: The current step number
            
        Returns:
            Loop detection info if a loop is detected, None otherwise
        """
        # Need at least 3 responses to detect a meaningful loop
        if len(self.response_history) < 3:
            return None
            
        # Don't detect loops too frequently (give agent time to recover)
        if current_step - self.last_loop_detection_step < 3:  # Increased from 2 to 3
            return None
            
        recent_responses = list(self.response_history)
        current_response = recent_responses[-1]
        
        # Check for exact repetition (most obvious loop)
        exact_matches = []
        for i, response in enumerate(recent_responses[:-1]):
            if response['content'] == current_response['content']:
                exact_matches.append(response)
                
        if len(exact_matches) >= 1:  # Found exact repetition
            self.loop_count += 1
            self.last_loop_detection_step = current_step
            return {
                'type': 'exact_repetition',
                'count': len(exact_matches) + 1,
                'repeated_content': current_response['content'],
                'loop_severity': 'high',
                'steps_involved': [r['step'] for r in exact_matches] + [current_response['step']]
            }
            
        # Check for high similarity (semantic loops)
        high_similarity_matches = []
        for i, response in enumerate(recent_responses[:-1]):
            similarity = self._calculate_similarity(response['content'], current_response['content'])
            if similarity >= self.similarity_threshold:
                high_similarity_matches.append({
                    'response': response,
                    'similarity': similarity
                })
                
        if len(high_similarity_matches) >= 2:  # Multiple similar responses
            self.loop_count += 1
            self.last_loop_detection_step = current_step
            return {
                'type': 'semantic_repetition',
                'count': len(high_similarity_matches) + 1,
                'repeated_content': current_response['content'],
                'loop_severity': 'medium',
                'similarity_scores': [m['similarity'] for m in high_similarity_matches],
                'steps_involved': [m['response']['step'] for m in high_similarity_matches] + [current_response['step']]
            }
            
        # Check for no-action loops (responses without tool calls)
        no_action_responses = [r for r in recent_responses if not r['has_tool_calls']]
        
        # Only trigger if we have at least 3 no-action responses AND they show confusion patterns
        if len(no_action_responses) >= 3:
            # Check if they're asking similar questions or expressing confusion
            confusion_keywords = [
                'clarify', 'specify', 'provide', 'need', 'help', 'unclear', 
                'which', 'what', 'how', 'could you', 'please', 'not sure',
                'specific', 'more information', 'details'
            ]
            
            confusion_count = 0
            for response in no_action_responses:
                content_lower = response['content'].lower()
                if any(keyword in content_lower for keyword in confusion_keywords):
                    confusion_count += 1
                    
            # Only trigger if MOST of the no-action responses show confusion (more strict)
            if confusion_count >= len(no_action_responses) * 0.6:  # At least 60% must be confusion
                # Also check if there have been any productive actions recently
                recent_productive_actions = [r for r in recent_responses if r['has_tool_calls']]
                
                # If there were recent productive actions, be more lenient
                if len(recent_productive_actions) > 0:
                    # Only trigger if the confusion responses are very recent and concentrated
                    recent_confusion = [r for r in no_action_responses if r['step'] >= current_step - 2]
                    if len(recent_confusion) < 2:
                        return None  # Don't trigger if not enough recent confusion
                
                self.loop_count += 1
                self.last_loop_detection_step = current_step
                return {
                    'type': 'no_action_confusion',
                    'count': len(no_action_responses),
                    'repeated_content': current_response['content'],
                    'loop_severity': 'medium',
                    'confusion_responses': confusion_count,
                    'steps_involved': [r['step'] for r in no_action_responses],
                    'recent_actions': len(recent_productive_actions) > 0
                }
                
        return None
        
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two text strings using SequenceMatcher.
        
        Args:
            text1: First text string
            text2: Second text string
            
        Returns:
            Similarity ratio between 0.0 and 1.0
        """
        return difflib.SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
        
    def generate_loop_breaking_message(self, loop_info: Dict[str, Any], original_instruction: str) -> str:
        """
        Generate a message to help the agent break out of the detected loop.
        
        Args:
            loop_info: Information about the detected loop
            original_instruction: The original user instruction
            
        Returns:
            A message to inject into the conversation to break the loop
        """
        loop_type = loop_info['type']
        severity = loop_info['loop_severity']
        count = loop_info['count']
        steps = loop_info['steps_involved']
        
        # Check if there were recent productive actions
        had_recent_actions = loop_info.get('recent_actions', False)
        
        base_message = f"""
🚨 LOOP DETECTION ALERT 🚨

You are stuck in a {loop_type} loop (Severity: {severity}).
You have repeated similar responses {count} times across steps: {steps}

ORIGINAL INSTRUCTION: "{original_instruction}"

🤔 CRITICAL DECISION POINT:
You need to make a decision about how to proceed. You have TWO OPTIONS:

OPTION 1: STOP EXECUTION (Recommended if instruction is unclear/impossible)
- If the original instruction is too vague, unclear, or seems like a placeholder
- If you genuinely cannot determine what action to take
- If the task appears to be impossible or nonsensical
- If you believe stopping would be more helpful than continuing aimlessly

OPTION 2: TAKE CONCRETE ACTION (Recommended if you can make reasonable assumptions)
- If you can make reasonable assumptions about what the user wants
- If you can demonstrate useful capabilities even with unclear instructions
- If you can break down the vague instruction into actionable steps

💡 TO HELP YOU DECIDE:
- Is "{original_instruction}" a clear, actionable request?
- Can you reasonably infer what the user wants you to accomplish?
- Would taking action be more helpful than stopping?

🎯 IF YOU CHOOSE OPTION 1 (STOP):
Simply respond with a message containing the phrase "task complete" or "stopping execution" and explain why you believe stopping is the best choice given the unclear instruction.

🎯 IF YOU CHOOSE OPTION 2 (TAKE ACTION):
Execute ONE specific tool call immediately. Here are concrete suggestions:
"""

        if loop_type == 'exact_repetition':
            base_message += """
- Use write_file to create a capabilities demonstration file
- Use web_search to find current information on a relevant topic
- Use list_directory to explore and work with available files
"""
        elif loop_type == 'semantic_repetition':
            base_message += """
- Use web_search to gather information instead of asking questions
- Use write_file to create something useful based on reasonable assumptions
- Use any data analysis tools to demonstrate capabilities
"""
        elif loop_type == 'no_action_confusion':
            if had_recent_actions:
                base_message += """
- Build upon the actions you already took
- Extend or analyze what you previously created
- Complete the work you started rather than asking for more direction
"""
            else:
                base_message += """
- Use list_directory to explore available files and work with them
- Use write_file to create a useful demonstration
- Use web_search to find relevant information
"""

        base_message += f"""

⚡ IMPORTANT RULES:
- Make your decision quickly and definitively
- NO more questions like "could you clarify", "please specify", or "what would you like"
- If you stop, explain your reasoning clearly
- If you continue, take concrete action with tools immediately

🧠 ASK YOURSELF: 
"Given the instruction '{original_instruction}', is it better to stop and explain why this instruction is unclear, or can I make reasonable assumptions and proceed with useful actions?"

CHOOSE YOUR OPTION AND ACT NOW!
"""

        return base_message.strip()
        
    def reset(self):
        """Reset the loop detector state."""
        self.response_history.clear()
        self.loop_count = 0
        self.last_loop_detection_step = -1
        
    def get_stats(self) -> Dict[str, Any]:
        """Get current loop detection statistics."""
        return {
            'total_loops_detected': self.loop_count,
            'responses_in_history': len(self.response_history),
            'last_loop_detection_step': self.last_loop_detection_step
        } 