"""
SimpleAgent Execution Module

This module handles command execution and step management for SimpleAgent.
"""

import os
import json
import time
from typing import Dict, Any, List, Optional, Tuple, Callable

from openai import OpenAI
import commands
from commands import REGISTERED_COMMANDS, COMMAND_SCHEMAS
from core.security import get_secure_path
from core.config import OUTPUT_DIR, DEFAULT_MODEL, OPENAI_API_KEY


class ExecutionManager:
    """
    Manages command execution and step management for SimpleAgent.
    """
    
    # File operation commands that need path modification
    FILE_OPS = [
        "write_file", "edit_file", "advanced_edit_file", "append_file", "delete_file", 
        "read_file", "create_directory", "list_directory", "file_exists",
        "load_json", "save_json", "copy_file", "move_file", "rename_file"
    ]
    
    def __init__(self, model: str = DEFAULT_MODEL, output_dir: str = OUTPUT_DIR):
        """
        Initialize the execution manager.
        
        Args:
            model: The OpenAI model to use
            output_dir: The output directory for file operations
        """
        self.model = model
        self.output_dir = output_dir
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.stop_requested = False
        
        # Ensure output directory exists
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
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
                modified_args[param_name] = get_secure_path(modified_args[param_name], self.output_dir)
                
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
        
    def request_stop(self) -> bool:
        """
        Request the agent to stop execution at the next convenient point.
        
        Returns:
            True to indicate stop was requested
        """
        self.stop_requested = True
        print("\n🛑 Stop requested. The agent will stop at the next step.")
        return True
        
    def execute_function(self, function_name: str, function_args: Dict) -> Tuple[Any, Optional[Dict]]:
        """
        Execute a function with the given arguments.
        
        Args:
            function_name: The name of the function to execute
            function_args: The arguments to pass to the function
            
        Returns:
            A tuple containing the function result and any tracked changes
        """
        # Modify file-related arguments to be in output directory
        function_args = self._modify_file_args(function_name, function_args)
        
        # Print execution information
        print(f"📋 Executing function: {function_name}")
        print(f"   with arguments: {function_args}")
        
        function_to_call = REGISTERED_COMMANDS.get(function_name)
        change = None
        
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
                        return "Operation blocked: Security violation - attempted to access path outside of output directory", None
                
                # Create any necessary subdirectories for file operations
                path_arg = next((v for k, v in function_args.items() 
                              if k in ["file_path", "directory_path", "target_file"]), None)
                if path_arg:
                    dir_path = os.path.dirname(path_arg) if function_name != "create_directory" else path_arg
                    if dir_path:
                        os.makedirs(dir_path, exist_ok=True)
                        
            # Execute the function with sanitized arguments
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
                
            return function_response, change
        else:
            print(f"❌ Function {function_name} not found")
            return f"Function {function_name} not found", None
            
    def get_next_action(self, conversation_history: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Get the next action from the model.
        
        Args:
            conversation_history: The current conversation history
            
        Returns:
            The assistant's message with the next action
        """
        # Save current working directory
        original_cwd = os.getcwd()
        
        try:
            # Change to output directory for consistent operations
            if os.path.exists(self.output_dir):
                os.chdir(self.output_dir)
                print(f"🔄 Changed working directory to: {os.getcwd()}")
                
            response = self.client.chat.completions.create(
                model=self.model,
                messages=conversation_history,
                tools=COMMAND_SCHEMAS,
                tool_choice="auto",
            )

            # Ensure the response structure is correct
            if response.choices and response.choices[0].message:
                return response.choices[0].message
            return None

        except Exception as e:
            print(f"Error getting next action: {str(e)}")
            return None
        finally:
            # Restore original working directory
            if os.getcwd() != original_cwd:
                os.chdir(original_cwd)
                print(f"🔄 Restored working directory to: {original_cwd}") 