"""
SimpleAgent Run Manager Module

This module handles the run loop from agent.py

Args:
    model: The OpenAI model to use
    output_dir: The output directory for file operations
"""

import os
import time
import json
from typing import List, Dict, Any, Optional

from core.conversation import ConversationManager
from core.execution import ExecutionManager
from core.memory import MemoryManager
from core.summarizer import ChangeSummarizer
from core.config import OUTPUT_DIR


class RunManager:
    """
    Manages the run loop for SimpleAgent, coordinating the conversation,
    execution, and memory components.
    """
    
    def __init__(self, model: str, output_dir: str = OUTPUT_DIR):
        """
        Initialize the run manager.
        
        Args:
            model: The OpenAI model to use
            output_dir: The output directory for file operations
        """
        self.output_dir = output_dir
        self.conversation_manager = ConversationManager()
        self.execution_manager = ExecutionManager(model=model, output_dir=output_dir)
        self.memory_manager = MemoryManager()
        self.summarizer = ChangeSummarizer()
        
    def run(self, user_instruction: str, max_steps: int = 10, auto_continue: int = 0):
        """
        Run the SimpleAgent with the given instruction.
        
        Args:
            user_instruction: The instruction from the user
            max_steps: Maximum number of steps to run
            auto_continue: Number of steps to auto-continue (0 = disabled, -1 = infinite)
        """
        # Reset stop flag
        self.execution_manager.stop_requested = False
        
        # Setup initial console output
        print(f"\n🤖 SimpleAgent initialized with instruction: {user_instruction}")
        print(f"📁 Using output directory: {self.output_dir}")
        
        # Get current date and time information for the system message
        current_datetime = time.strftime("%Y-%m-%d %H:%M:%S")
        current_year = time.strftime("%Y")
        print(f"📅 Current date: {current_datetime}")
        
        # Only print auto-continue message if it's enabled (non-zero and not None)
        if auto_continue and auto_continue != 0:
            print(f"📌 Auto-continue enabled for {auto_continue if auto_continue > 0 else 'all'} steps")
            print("💡 Press Ctrl+C at any time to interrupt and stop execution")
        else:
            print("📌 Manual mode (auto-continue disabled)")
        print()
        
        # Save and change to the output directory
        original_cwd = os.getcwd()
        
        try:
            # Change to the output directory so all operations happen there
            if os.path.exists(self.output_dir):
                os.chdir(self.output_dir)
                print(f"🔄 Changed working directory to: {os.getcwd()}")
            
            # Clear the conversation history and start fresh
            self.conversation_manager.clear()
            
            # Create system message
            system_message = {
                "role": "system",
                "content": """You are an AI agent that can manage its own execution steps.
You are currently running with the following capabilities:
- You can stop execution early if the task is complete
- You can continue automatically if more steps are needed
- You should be mindful of the current step number and total steps available

Current date and time: {current_datetime}
Your knowledge cutoff might be earlier, but you should consider the current date when processing tasks.
Always work with the understanding that it is now {current_year} when handling time-sensitive information.

When responding:
1. Always consider if the task truly needs more steps
2. If a task is complete, include phrases like "task complete", "all done", "finished", or "completed successfully"
3. If you need more steps than allocated, make this clear in your response

{auto_mode_guidance}

Current execution context:
- You are on step {current_step} of {max_steps} total steps
- Auto-continue is {auto_status}
"""
            }
            self.conversation_manager.add_message("system", system_message["content"])
            
            # Add the user instruction to the conversation
            self.conversation_manager.add_message("user", user_instruction)
            
            # Check if the instruction is potentially date/time related
            date_keywords = ["today", "current date", "this year", "this month", "schedule", "calendar", 
                           "deadline", "upcoming", "recently", "last year", "next week", "time", 
                           "date", "year", "month", "day", "2023", "2024", "2025", "future", "past"]
            
            instruction_lower = user_instruction.lower()
            is_date_related = any(keyword in instruction_lower for keyword in date_keywords)
            
            # If date-related, add a reminder about the current date
            if is_date_related:
                date_reminder = f"Remember that today's date is {current_datetime} as you work on this task. All date-related calculations should use this as a reference point."
                print(f"📅 Adding date reminder: {date_reminder}")
                self.conversation_manager.add_message("user", date_reminder)
            
            # Track changes for summarization
            changes_made = []
            step_changes = []  # Track changes for each step
            
            # Run the agent loop
            step = 0
            # Ensure auto_steps_remaining is an integer (0 if auto_continue is None)
            auto_steps_remaining = 0 if auto_continue is None else auto_continue
            
            while step < max_steps and not self.execution_manager.stop_requested:
                try:
                    step += 1
                    
                    # Get current date and time for the system message
                    current_datetime = time.strftime("%Y-%m-%d %H:%M:%S")
                    current_year = time.strftime("%Y")
                    
                    # Update the system message with current step information
                    if auto_steps_remaining == -1:
                        auto_status = "enabled (infinite)"
                        auto_mode_guidance = """IMPORTANT: You are running in AUTO-CONTINUE mode with infinite steps. 
Do NOT ask the user questions or for input during task execution. 
Instead, make decisions independently and proceed with executing the task to completion.
Your goal is to complete the requested task fully without human intervention."""
                    elif auto_steps_remaining > 0:
                        auto_status = f"enabled ({auto_steps_remaining} steps remaining)"
                        auto_mode_guidance = """IMPORTANT: You are running in AUTO-CONTINUE mode.
Do NOT ask the user questions or for input during task execution.
Instead, make decisions independently and proceed with executing the task.
Your goal is to complete as much of the task as possible without human intervention."""
                    else:
                        auto_status = "disabled"
                        auto_mode_guidance = """You are running in MANUAL mode.
If you need user input, make it clear by using phrases like "do you need", "would you like", etc.
The user will be prompted after each step to continue or provide new instructions."""
                        
                    # Update the system message
                    updated_system_content = system_message["content"].format(
                        current_step=step,
                        max_steps=max_steps,
                        auto_status=auto_status,
                        auto_mode_guidance=auto_mode_guidance,
                        current_datetime=current_datetime,
                        current_year=current_year
                    )
                    self.conversation_manager.update_system_message(updated_system_content)
                    
                    print(f"\n--- Step {step}/{max_steps} ---")
                    
                    try:
                        # Get the next action from the model
                        assistant_message = self.execution_manager.get_next_action(
                            self.conversation_manager.get_history()
                        )
                        
                        if not assistant_message:
                            print("Error: Failed to get a response from the model.")
                            break
                            
                        # Add the assistant's response to conversation history
                        content = None
                        if hasattr(assistant_message, 'content'):
                            content = assistant_message.content
                        elif isinstance(assistant_message, dict) and 'content' in assistant_message:
                            content = assistant_message['content']
                        if content:
                            print(f"\n🤖 Assistant: {content}")
                        
                        # Create a proper assistant message for the conversation history
                        message_dict = {"role": "assistant"}
                        if content:
                            message_dict["content"] = content
                        
                        # Add tool calls if present
                        if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
                            message_dict["tool_calls"] = [
                                {
                                    "id": tool_call.id,
                                    "type": "function",
                                    "function": {
                                        "name": tool_call.function.name,
                                        "arguments": tool_call.function.arguments
                                    }
                                } for tool_call in assistant_message.tool_calls
                            ]
                        
                        # Add the complete assistant message to the conversation
                        self.conversation_manager.conversation_history.append(message_dict)
                        
                        # Reset step changes
                        step_changes = []
                        
                        # Handle any tool calls
                        if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
                            for tool_call in assistant_message.tool_calls:
                                function_name = tool_call.function.name
                                function_args = json.loads(tool_call.function.arguments)
                                
                                # Execute the function
                                function_response, change = self.execution_manager.execute_function(
                                    function_name, function_args
                                )
                                
                                # Track changes if any were made
                                if change:
                                    changes_made.append(change)
                                    step_changes.append(change)
                                
                                # Add the function call and response to the conversation
                                self.conversation_manager.add_message(
                                    "tool", 
                                    str(function_response), 
                                    tool_call_id=tool_call.id,
                                    name=function_name
                                )
                        
                        # Generate a summary of changes for this step if any were made
                        if step_changes:
                            step_summary = self.summarizer.summarize_changes(step_changes, is_step_summary=True)
                            if step_summary:
                                print(f"\n{step_summary}")
                        
                        # Check if the agent is done or needs to continue
                        should_continue = True
                        needs_more_steps = False
                        
                        if content:
                            content_lower = content.lower()
                            
                            # Check for completion phrases
                            if any(phrase in content_lower for phrase in [
                                "task complete",
                                "i've completed",
                                "all done",
                                "finished",
                                "completed successfully"
                            ]):
                                print("\n✅ Task completed")
                                break
                                
                            # Check if the assistant is just waiting for input
                            elif not hasattr(assistant_message, 'tool_calls') and any(phrase in content_lower for phrase in [
                                "do you need",
                                "would you like",
                                "let me know",
                                "please specify",
                                "can you clarify",
                                "if you need"
                            ]):
                                # Only set should_continue to False in manual mode
                                if auto_steps_remaining == 0:  # Only in manual mode
                                    should_continue = False
                                else:
                                    print("\n🔄 In auto-mode: Continuing despite questions in response")
                                    
                            # Check if more steps are needed
                            elif any(phrase in content_lower for phrase in [
                                "need more steps",
                                "additional steps required",
                                "more steps needed",
                                "cannot complete within current steps"
                            ]):
                                needs_more_steps = True
                        
                        # Special handling in auto-mode: continue even if there are no tool calls
                        if (auto_steps_remaining == -1 or auto_steps_remaining > 0) and not hasattr(assistant_message, 'tool_calls'):
                            # In auto-mode, provide additional context to help the model continue
                            if content and not any(phrase in content_lower for phrase in [
                                "task complete", "i've completed", "all done", "finished", "completed successfully"
                            ]):
                                print("\n🔄 Auto-mode: Encouraging model to continue making progress")
                                self.conversation_manager.add_message("user", 
                                    "Please continue with the next step of the task. Remember to use the available commands to make progress.")
                        
                        # Only continue if there's more to do
                        if step < max_steps and should_continue and not self.execution_manager.stop_requested:
                            # Only show overall progress if there are changes and it's different from step summary
                            if changes_made:
                                overall_summary = self.summarizer.summarize_changes(changes_made)
                                if overall_summary and (not step_changes or overall_summary != step_summary):
                                    print(f"\n{overall_summary}")
                            
                            # Handle auto-continue
                            if auto_steps_remaining == -1 or auto_steps_remaining > 0:
                                if auto_steps_remaining > 0:  # Only decrement if it's a positive number
                                    auto_steps_remaining -= 1
                                    
                                # Check if the model is asking a question
                                if not hasattr(assistant_message, 'tool_calls') and content and any(phrase in content_lower for phrase in [
                                    "do you need", "would you like", "let me know", "please specify", 
                                    "can you clarify", "if you need", "what would you like", "your preference",
                                    "should i", "do you want"
                                ]):
                                    print("\n🔄 Auto-mode: Automatically responding 'y' to continue despite questions")
                                    # Add an automatic 'y' response in auto-mode to keep the flow going
                                    self.conversation_manager.add_message("user", "y")
                                
                                # Check if a stop was requested
                                if self.execution_manager.stop_requested:
                                    print("\n🛑 Stop requested. Halting auto-continue execution.")
                                    break
                                    
                                # Check if the model is using outdated date references
                                if content and any(outdated_year in content_lower for outdated_year in ["2020", "2021", "2022", "2023", "2024"]):
                                    # Check if it's not referring to historical context
                                    if any(current_indicator in content_lower for current_indicator in ["current", "now", "today", "present", "currently"]):
                                        date_correction = f"Important correction: Today's date is {current_datetime}. Please use {current_year} as the current year for this task, not older years from your training data."
                                        print(f"\n📅 Auto-mode: Correcting outdated date reference")
                                        self.conversation_manager.add_message("user", date_correction)
                                    
                                if needs_more_steps:
                                    print("\n⚠️ Note: Task requires more steps than currently allocated")
                                
                                print("\n🔄 Auto-continuing...")
                                continue
                            
                            # Manual mode - ask for user input
                            user_input = input("\n🧑 Enter your next instruction, 'y' to continue with current task, or 'n' to stop: ")
                            
                            # Normalize the input
                            normalized_input = user_input.strip().lower()
                            
                            if normalized_input == 'n':
                                print("Stopping the agent")
                                break
                            elif normalized_input == 'y':
                                # Simply continue
                                continue
                            else:
                                # Add the custom message to the conversation
                                print(f"\n🧑 User: {user_input}")
                                self.conversation_manager.add_message("user", user_input)
                        else:
                            # If we're at max steps or have nothing more to do, break
                            if not should_continue:
                                print("\n✅ No further actions needed")
                            elif needs_more_steps:
                                print("\n⚠️ Reached maximum steps but task requires more steps")
                            break
                    
                    except Exception as e:
                        print(f"Error in step execution: {str(e)}")
                        break
                
                except KeyboardInterrupt:
                    print("\n🛑 KeyboardInterrupt received. Stopping the agent...")
                    self.execution_manager.stop_requested = True
                    print("\n✅ Agent execution interrupted by user")
            
            # Generate a final summary of all changes
            if changes_made:
                final_summary = self.summarizer.summarize_changes(changes_made)
                print(f"\n📝 Final Summary of All Changes:\n{final_summary}")
            
            # Save the memory
            self.memory_manager.add_conversation(self.conversation_manager.get_history())
            self.memory_manager.save_memory()
            
            print("\n🏁 SimpleAgent execution completed")
            
        finally:
            # Always restore the original working directory
            if os.getcwd() != original_cwd:
                os.chdir(original_cwd)
                print(f"🔄 Restored working directory to: {original_cwd}") 