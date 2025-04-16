"""
SimpleAgent Agent Module

This module contains the SimpleAgent agent class that handles the conversation
with the AI model and executes commands.

Security Notes:
- All file operations are restricted to the output directory
- Multiple layers of path validation prevent directory traversal attacks:
  1. _get_output_path normalizes and constrains paths to output directory
  2. _modify_file_args applies path constraints to all file operation arguments
  3. Additional runtime validation blocks operations that attempt to access files outside output directory
- Absolute paths and path traversal attempts (../) are sanitized
- Security messages are logged when unauthorized access is attempted
"""

import os
import sys
import json
import time
from typing import List, Dict, Any, Optional, Callable
from openai import OpenAI

# Import commands package
import commands
from commands import REGISTERED_COMMANDS, COMMAND_SCHEMAS
from core.summarizer import ChangeSummarizer
from core.config import OPENAI_API_KEY, DEFAULT_MODEL, MEMORY_FILE, OUTPUT_DIR


# Expose output directory security function for command modules to use
def get_secure_path(file_path: str, base_dir: str = OUTPUT_DIR) -> str:
    """
    Securely convert any file path to be within the specified base directory.
    This prevents path traversal attacks and ensures file operations are contained.
    
    Args:
        file_path: Original file path
        base_dir: Base directory to contain the file (defaults to OUTPUT_DIR)
        
    Returns:
        Modified file path within the base directory
    """
    # Normalize path separators to system default
    file_path = file_path.replace('/', os.path.sep).replace('\\', os.path.sep)
    
    # Get just the basename to handle absolute paths or traversal attempts
    file_name = os.path.basename(file_path)
    
    # If the path is absolute or empty, just use the filename in base dir
    if os.path.isabs(file_path) or not file_path:
        return os.path.join(base_dir, file_name)
    
    # Remove any leading dots, slashes, or path traversal patterns
    # This prevents patterns like '../../../.env' from working
    clean_path = file_path
    while clean_path.startswith(('.', os.path.sep)):
        clean_path = clean_path.lstrip('.' + os.path.sep)
        
    # If path is empty after cleaning, just use filename
    if not clean_path:
        return os.path.join(base_dir, file_name)
        
    # For security, resolve absolute paths after joining with output directory
    # to ensure the final path is always within output directory
    combined_path = os.path.normpath(os.path.join(base_dir, clean_path))
    
    # Final security check: ensure the resolved path is within output directory
    # by comparing the absolute paths
    abs_base_dir = os.path.abspath(base_dir)
    abs_combined_path = os.path.abspath(combined_path)
    
    if not abs_combined_path.startswith(abs_base_dir):
        # If the path escapes output directory, fall back to just using filename in output dir
        return os.path.join(base_dir, file_name)
        
    return combined_path


class SimpleAgent:
    # File operation commands that need path modification
    FILE_OPS = [
        "write_file", "edit_file", "advanced_edit_file", "append_file", "delete_file", 
        "read_file", "create_directory", "list_directory", "file_exists",
        "load_json", "save_json", "copy_file", "move_file", "rename_file"
    ]

    def __init__(self, model: str = None):
        """
        Initialize the SimpleAgent agent.
        
        Args:
            model: The OpenAI model to use (defaults to config value)
        """
        self.model = model or DEFAULT_MODEL
        self.conversation_history = []
        self.output_dir = OUTPUT_DIR
        # Ensure output directory exists
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        # Memory file should also be in output directory
        self.memory_file = MEMORY_FILE
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.summarizer = ChangeSummarizer()
        self.stop_requested = False
        self.load_memory()
        
    def load_memory(self):
        """Load the agent's memory from a file if it exists."""
        if REGISTERED_COMMANDS["file_exists"](self.memory_file):
            self.memory = REGISTERED_COMMANDS["load_json"](self.memory_file)
            print(f"Loaded memory from {self.memory_file}")
        else:
            self.memory = {"conversations": [], "files_created": [], "files_modified": []}
            
    def save_memory(self):
        """Save the agent's memory to a file."""
        REGISTERED_COMMANDS["save_json"](self.memory_file, self.memory)
        print(f"Saved memory to {self.memory_file}")
        
    def add_to_conversation(self, role: str, content: str, **kwargs):
        """Add a message to the conversation history."""
        message = {"role": role, "content": content}
        # Add additional fields for tool responses if provided
        for key, value in kwargs.items():
            message[key] = value
        self.conversation_history.append(message)
        
    def _get_output_path(self, file_path: str) -> str:
        """
        Convert any file path to be within the output directory.
        
        Args:
            file_path: Original file path
            
        Returns:
            Modified file path within output directory
        """
        # Use the instance's output_dir (which might be thread-specific)
        return get_secure_path(file_path, self.output_dir)

    def _modify_file_args(self, function_name: str, function_args: dict) -> dict:
        """
        Modify function arguments to ensure all file paths are within output directory.
        
        Args:
            function_name: Name of the function being called
            function_args: Original function arguments
            
        Returns:
            Modified function arguments with updated paths
        """
        if function_name not in self.FILE_OPS:
            return function_args

        modified_args = function_args.copy()
        
        # Handle different parameter names for different commands
        path_params = {
            "file_path": "file_path",
            "directory_path": "directory_path",
            "target_file": "target_file",
            "source_file": "source_file",
            "destination": "destination",
            "path": "path"
        }
        
        # Process all path parameters in the arguments
        for param_name in path_params.values():
            if param_name in modified_args:
                # Always convert paths to be within output directory
                modified_args[param_name] = self._get_output_path(modified_args[param_name])
                
                # For some operations (like read_file), verify the file exists within output directory
                if function_name in ["read_file", "edit_file", "append_file", "delete_file", "file_exists"]:
                    # Get absolute paths for comparison
                    abs_path = os.path.abspath(modified_args[param_name])
                    abs_output_dir = os.path.abspath(self.output_dir)
                    
                    # Verify file exists and is within output directory
                    if not os.path.exists(modified_args[param_name]) or not abs_path.startswith(abs_output_dir):
                        # For read operations, we want to be more strict
                        if function_name == "read_file":
                            # Return a clear security message instead of the file content
                            print(f"⚠️ Security: Attempted to access file outside of output directory: {modified_args[param_name]}")
                            # Replace the argument with a file that doesn't exist to trigger the file not found error
                            modified_args[param_name] = os.path.join(self.output_dir, "FILE_ACCESS_DENIED")
                
        return modified_args

    def run(self, user_instruction: str, max_steps: int = 10, auto_continue: int = 0):
        """
        Run the SimpleAgent agent with the given instruction.
        
        Args:
            user_instruction: The instruction from the user
            max_steps: Maximum number of steps to run
            auto_continue: Number of steps to auto-continue (0 = disabled, -1 = infinite)
        """
        # Flag to track if we should stop execution due to interrupt
        self.stop_requested = False
        
        print(f"\n🤖 SimpleAgent initialized with instruction: {user_instruction}")
        print(f"📁 Using output directory: {self.output_dir}")
        
        # Get current date and time information for the system message
        current_datetime = time.strftime("%Y-%m-%d %H:%M:%S")
        current_year = time.strftime("%Y")
        print(f"📅 Current date: {current_datetime}")
        
        # Change working directory to output directory
        original_cwd = os.getcwd()
        
        # Only print auto-continue message if it's enabled (non-zero and not None)
        if auto_continue and auto_continue != 0:
            print(f"📌 Auto-continue enabled for {auto_continue if auto_continue > 0 else 'all'} steps")
            print("💡 Press Ctrl+C at any time to interrupt and stop execution")
        else:
            print("📌 Manual mode (auto-continue disabled)")
        print()
        
        try:
            # Change to the output directory so all operations happen there
            # This ensures that the current working directory matches the output directory
            # which helps with relative file paths and makes the debug info consistent
            if os.path.exists(self.output_dir):
                os.chdir(self.output_dir)
                print(f"🔄 Changed working directory to: {os.getcwd()}")
            
            # Clear the conversation history and start fresh
            self.conversation_history = []
            
            # Add system message to make the model aware of step management
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
            self.conversation_history.append(system_message)
            
            # Add the user instruction to the conversation
            self.add_to_conversation("user", user_instruction)
            
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
                self.add_to_conversation("user", date_reminder)
            
            # Track changes for summarization
            changes_made = []
            step_changes = []  # Track changes for each step
            
            # Run the agent loop
            step = 0
            # Ensure auto_steps_remaining is an integer (0 if auto_continue is None)
            auto_steps_remaining = 0 if auto_continue is None else auto_continue
            
            while step < max_steps and not self.stop_requested:
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
                        
                    system_message["content"] = system_message["content"].format(
                        current_step=step,
                        max_steps=max_steps,
                        auto_status=auto_status,
                        auto_mode_guidance=auto_mode_guidance,
                        current_datetime=current_datetime,
                        current_year=current_year
                    )
                    self.conversation_history[0] = system_message
                    
                    print(f"\n--- Step {step}/{max_steps} ---")
                    
                    try:
                        # Get the next action from the model
                        response = self.client.chat.completions.create(
                            model=self.model,
                            messages=self.conversation_history,
                            tools=COMMAND_SCHEMAS,
                            tool_choice="auto",
                        )
                        
                        if not response.choices or not response.choices[0].message:
                            print("Error: Failed to get a response from the model.")
                            break
                            
                        assistant_message = response.choices[0].message
                        
                        # Add the assistant's response to conversation history
                        if assistant_message.content:
                            print(f"\n🤖 Assistant: {assistant_message.content}")
                        
                        # Create a proper assistant message for the conversation history
                        message_dict = {"role": "assistant"}
                        if assistant_message.content:
                            message_dict["content"] = assistant_message.content
                        
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
                        self.conversation_history.append(message_dict)
                        
                        # Reset step changes
                        step_changes = []
                        
                        # Handle any tool calls
                        if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
                            for tool_call in assistant_message.tool_calls:
                                function_name = tool_call.function.name
                                function_args = json.loads(tool_call.function.arguments)
                                
                                # Modify all file-related arguments to be in output directory
                                function_args = self._modify_file_args(function_name, function_args)
                                
                                # Execute the function
                                print(f"📋 Executing function: {function_name}")
                                print(f"   with arguments: {function_args}")
                                
                                function_to_call = REGISTERED_COMMANDS.get(function_name)
                                if function_to_call:
                                    # Additional security check for file operations before execution
                                    if function_name in self.FILE_OPS:
                                        # Find all path arguments
                                        path_args = [v for k, v in function_args.items() 
                                                   if k in ["file_path", "directory_path", "target_file", "source_file", "destination", "path"]]
                                        
                                        # Verify all paths are within output directory
                                        for path in path_args:
                                            abs_path = os.path.abspath(path)
                                            abs_output_dir = os.path.abspath(self.output_dir)
                                            
                                            # If path not within output directory, block the operation
                                            if not abs_path.startswith(abs_output_dir):
                                                print(f"⚠️ SECURITY BLOCKED: Attempted to access path outside of output directory: {path}")
                                                function_response = "Operation blocked: Security violation - attempted to access path outside of output directory"
                                                break
                                        else:  # This else belongs to the for loop - executes if no break occurs
                                            # Create any necessary subdirectories for file operations
                                            path_arg = next((v for k, v in function_args.items() 
                                                          if k in ["file_path", "directory_path", "target_file"]), None)
                                            if path_arg:
                                                dir_path = os.path.dirname(path_arg) if function_name != "create_directory" else path_arg
                                                if dir_path:
                                                    os.makedirs(dir_path, exist_ok=True)
                                        
                                        # Execute the function with sanitized arguments
                                        function_response = function_to_call(**function_args)
                                    else:
                                        # Non-file operations can proceed normally
                                        function_response = function_to_call(**function_args)
                                    
                                    print(f"📊 Function result: {function_response}")
                                    
                                    # Track file operations for summarization
                                    if function_name in self.FILE_OPS:
                                        change = {
                                            "operation": function_name,
                                            "file": next((v for k, v in function_args.items() 
                                                       if k in ["file_path", "directory_path", "target_file"]), "unknown"),
                                            "content": function_args.get("content", ""),
                                            "result": str(function_response)
                                        }
                                        changes_made.append(change)
                                        step_changes.append(change)
                                    
                                    # Add the function call and response to the conversation
                                    self.conversation_history.append({
                                        "role": "tool",
                                        "tool_call_id": tool_call.id,
                                        "name": function_name,
                                        "content": str(function_response)
                                    })
                                else:
                                    print(f"❌ Function {function_name} not found")
                        
                        # Generate a summary of changes for this step if any were made
                        if step_changes:
                            step_summary = self.summarizer.summarize_changes(step_changes, is_step_summary=True)
                            if step_summary:
                                print(f"\n{step_summary}")
                        
                        # Check if the agent is done or needs to continue
                        should_continue = True
                        needs_more_steps = False
                        if assistant_message.content:
                            content_lower = assistant_message.content.lower()
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
                            # Check if the assistant is just waiting for input or has nothing to do
                            # In auto mode, we want to continue even if the model asks a question
                            elif not assistant_message.tool_calls and any(phrase in content_lower for phrase in [
                                "do you need",
                                "would you like",
                                "let me know",
                                "please specify",
                                "can you clarify",
                                "if you need"
                            ]):
                                # Only set should_continue to False in manual mode
                                # In auto mode, we ignore questions and continue
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
                        # as long as the model didn't explicitly say the task is complete
                        if (auto_steps_remaining == -1 or auto_steps_remaining > 0) and not assistant_message.tool_calls:
                            # In auto-mode, provide additional context to help the model continue
                            if not any(phrase in content_lower for phrase in [
                                "task complete", "i've completed", "all done", "finished", "completed successfully"
                            ]):
                                print("\n🔄 Auto-mode: Encouraging model to continue making progress")
                                self.add_to_conversation("user", "Please continue with the next step of the task. Remember to use the available commands to make progress.")
                        
                        # Only continue if there's more to do
                        if step < max_steps and should_continue and not self.stop_requested:
                            # Only show overall progress if there are changes and it's different from step summary
                            if changes_made:
                                overall_summary = self.summarizer.summarize_changes(changes_made)
                                if overall_summary and (not step_summary or overall_summary != step_summary):
                                    print(f"\n{overall_summary}")
                            
                            # Handle auto-continue
                            # Auto-continue if either: 1) it's infinite (-1) or 2) there are remaining steps (>0)
                            if auto_steps_remaining == -1 or auto_steps_remaining > 0:
                                if auto_steps_remaining > 0:  # Only decrement if it's a positive number
                                    auto_steps_remaining -= 1
                                    
                                # Check if the model is asking a question
                                if not assistant_message.tool_calls and assistant_message.content and any(phrase in content_lower for phrase in [
                                    "do you need", "would you like", "let me know", "please specify", 
                                    "can you clarify", "if you need", "what would you like", "your preference",
                                    "should i", "do you want"
                                ]):
                                    print("\n🔄 Auto-mode: Automatically responding 'y' to continue despite questions")
                                    # Add an automatic 'y' response in auto-mode to keep the flow going
                                    self.add_to_conversation("user", "y")
                                
                                # Check if a stop was requested
                                if self.stop_requested:
                                    print("\n🛑 Stop requested. Halting auto-continue execution.")
                                    break
                                    
                                # Check if the model is using outdated date references
                                if assistant_message.content and any(outdated_year in content_lower for outdated_year in ["2020", "2021", "2022", "2023", "2024"]):
                                    # Check if it's not referring to historical context
                                    if any(current_indicator in content_lower for current_indicator in ["current", "now", "today", "present", "currently"]):
                                        date_correction = f"Important correction: Today's date is {current_datetime}. Please use {current_year} as the current year for this task, not older years from your training data."
                                        print(f"\n📅 Auto-mode: Correcting outdated date reference")
                                        self.add_to_conversation("user", date_correction)
                                    
                                if needs_more_steps:
                                    print("\n⚠️ Note: Task requires more steps than currently allocated")
                                
                                print("\n🔄 Auto-continuing...")
                                continue
                            
                            # If we reach here, it means auto-continue is disabled (0) - manual mode
                            user_input = input("\n🧑 Enter your next instruction, 'y' to continue with current task, or 'n' to stop: ")
                            
                            # Normalize the input by stripping whitespace and converting to lowercase for comparison
                            normalized_input = user_input.strip().lower()
                            
                            # IMPORTANT: Do exact string comparison
                            if normalized_input == 'n':
                                print("Stopping the agent")
                                break
                            elif normalized_input == 'y':
                                # Simply continue without additional logging
                                continue
                            else:
                                # Add the custom message to the conversation as a user message
                                print(f"\n🧑 User: {user_input}")
                                self.add_to_conversation("user", user_input)
                        else:
                            # If we're at max steps or have nothing more to do, break
                            if not should_continue:
                                print("\n✅ No further actions needed")
                            elif needs_more_steps:
                                print("\n⚠️ Reached maximum steps but task requires more steps")
                            break
                        
                    except Exception as e:
                        print(f"Error getting next action: {str(e)}")
                        break
                
                except KeyboardInterrupt:
                    print("\n🛑 KeyboardInterrupt received. Stopping the agent...")
                    self.stop_requested = True
                    print("\n✅ Agent execution interrupted by user")
            
            # Generate a final summary of all changes
            if changes_made:
                final_summary = self.summarizer.summarize_changes(changes_made)
                print(f"\n📝 Final Summary of All Changes:\n{final_summary}")
            
            # Save the memory
            self.memory["conversations"].append(self.conversation_history)
            self.save_memory()
            
            print("\n🏁 SimpleAgent execution completed")
            
        finally:
            # Always restore the original working directory when done
            if os.getcwd() != original_cwd:
                os.chdir(original_cwd)
                print(f"🔄 Restored working directory to: {original_cwd}")
        
    def request_stop(self):
        """Request the agent to stop execution at the next convenient point."""
        self.stop_requested = True
        print("\n🛑 Stop requested. The agent will stop at the next step.")
        return True

    def get_next_action(self):
        """
        Get the next action from the model.

        Returns:
            The model's response
        """
        # Save current working directory
        original_cwd = os.getcwd()
        
        try:
            # Change to output directory for consistent operations
            # This ensures that the current working directory matches the output directory
            # which helps with relative file paths and makes the debug info consistent
            if os.path.exists(self.output_dir):
                os.chdir(self.output_dir)
                print(f"🔄 Changed working directory to: {os.getcwd()}")
                
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.conversation_history,
                tools=COMMAND_SCHEMAS,
                tool_choice="auto",
            )

            # Ensure the response structure is correct
            if response.choices and response.choices[0].message:
                return response.choices[0].message

        except Exception as e:
            print(f"Error getting next action: {str(e)}")
            return None
        finally:
            # Restore original working directory
            if os.getcwd() != original_cwd:
                os.chdir(original_cwd)
                print(f"🔄 Restored working directory to: {original_cwd}") 