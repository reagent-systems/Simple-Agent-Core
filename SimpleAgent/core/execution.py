"""
SimpleAgent Execution Module

This module handles command execution and step management for SimpleAgent.
"""

import os
import json
import time
from typing import Dict, Any, List, Optional, Tuple, Callable

from core.tool_manager import REGISTERED_COMMANDS, COMMAND_SCHEMAS, load_tool
from core.security import get_secure_path
from core.config import OUTPUT_DIR, DEFAULT_MODEL, create_client, API_PROVIDER


class ExecutionManager:
    """
    Manages command execution and step management for SimpleAgent.6
    """
    
    # File operation commands that need path modification
    FILE_OPS = [
        "write_file", "edit_file", "advanced_edit_file", "append_file", "delete_file", 
        "read_file", "create_directory", "list_directory", "file_exists",
        "load_json", "save_json", "copy_file", "move_file", "rename_file",
        "github_fork_clone"
    ]
    
    def __init__(self, model: str = DEFAULT_MODEL, output_dir: str = OUTPUT_DIR):
        """
        Initialize the execution manager.
        
        Args:
            model: The model to use (OpenAI model name or LM-Studio model name)
            output_dir: The output directory for file operations
        """
        self.model = model
        self.output_dir = output_dir
        self.client = create_client()
        self.stop_requested = False
        
        # Ensure output directory exists
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
    def _modify_file_args(self, function_name: str, function_args: dict) -> dict:
        """
        Modify function arguments to ensure all file paths are within output directory.
        This provides centralized security for all file operations.
        
        Args:
            function_name: Name of the function being called
            function_args: Original function arguments
            
        Returns:
            Modified function arguments with updated paths
        """
        if function_name not in self.FILE_OPS:
            return function_args

        modified_args = function_args.copy()
        
        # Common path parameter names that tools might use
        path_params = [
            "file_path", "filepath", "path", "filename", "file_name",
            "directory_path", "dir_path", "directory", 
            "target_file", "source_file", "destination", "target_dir"
        ]
        
        for param_name in path_params:
            if param_name in modified_args:
                # Always convert paths to be within output directory
                modified_args[param_name] = get_secure_path(modified_args[param_name], self.output_dir)
                
                # For read operations, verify the file exists within output directory
                if function_name in ["read_file", "edit_file", "append_file", "delete_file", "file_exists"]:
                    abs_path = os.path.abspath(modified_args[param_name])
                    abs_output_dir = os.path.abspath(self.output_dir)
                    
                    if not abs_path.startswith(abs_output_dir):
                        if not os.path.exists(modified_args[param_name]):
                            print(f"⚠️ Security: File access restricted to output directory: {modified_args[param_name]}")
                            modified_args[param_name] = os.path.join(self.output_dir, "FILE_ACCESS_DENIED")
                
        return modified_args
        
    def _validate_function_args(self, function_name: str, function_args: Dict[str, Any]) -> Optional[str]:
        """
        Validate function arguments against the tool's schema and provide helpful feedback.
        
        Args:
            function_name: Name of the function being called
            function_args: Arguments being passed to the function
            
        Returns:
            Helpful message if there are parameter mismatches, None if all good
        """
        try:
            # Find the schema for this function
            function_schema = None
            for schema in COMMAND_SCHEMAS:
                if schema.get("function", {}).get("name") == function_name:
                    function_schema = schema
                    break
            
            if not function_schema:
                return None
            
            # Get expected parameters from schema
            schema_params = function_schema.get("function", {}).get("parameters", {}).get("properties", {})
            required_params = set(function_schema.get("function", {}).get("parameters", {}).get("required", []))
            
            if not schema_params:
                return None
            
            provided_params = set(function_args.keys())
            expected_params = set(schema_params.keys())
            
            # Check for parameter mismatches
            unexpected_params = provided_params - expected_params
            missing_required = required_params - provided_params
            
            messages = []
            
            if unexpected_params:
                expected_list = ', '.join(sorted(expected_params))
                unexpected_list = ', '.join(sorted(unexpected_params))
                messages.append(f"Unexpected parameters: {unexpected_list}. Expected: {expected_list}")
            
            if missing_required:
                missing_list = ', '.join(sorted(missing_required))
                messages.append(f"Missing required parameters: {missing_list}")
            
            if messages:
                return f"Parameter validation for {function_name}: " + "; ".join(messages)
            
            return None
            
        except Exception:
            return None
        
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
        
        # If function not found, try to load it dynamically
        if not function_to_call:
            print(f"🔧 Tool '{function_name}' not loaded, attempting dynamic loading...")
            if load_tool(function_name):
                function_to_call = REGISTERED_COMMANDS.get(function_name)
                print(f"✅ Successfully loaded tool '{function_name}'")
            else:
                print(f"❌ Failed to load tool '{function_name}'")
        
        if function_to_call:
            # Additional security check for file operations before execution
            if function_name in self.FILE_OPS:
                path_args = [v for k, v in function_args.items() 
                           if k in ["file_path", "filepath", "path", "filename", "file_name", 
                                   "directory_path", "dir_path", "directory", "target_file", 
                                   "source_file", "destination", "target_dir"]]
                
                # Verify all paths are within output directory
                for path in path_args:
                    abs_path = os.path.abspath(path)
                    abs_output_dir = os.path.abspath(self.output_dir)
                    
                    if not abs_path.startswith(abs_output_dir):
                        # Allow git repository operations
                        if function_name == "github_fork_clone" and any(segment in abs_path for segment in ["clix", ".git"]):
                            continue
                        
                        print(f"⚠️ SECURITY BLOCKED: Attempted to access path outside of output directory: {path}")
                        return "Operation blocked: Security violation - attempted to access path outside of output directory", None
                
                # Create directories as needed
                path_arg = next((v for k, v in function_args.items() 
                              if k in ["file_path", "filepath", "path", "filename", "directory_path", "target_file", "target_dir"]), None)
                if path_arg:
                    dir_path = os.path.dirname(path_arg) if function_name != "create_directory" else path_arg
                    if dir_path:
                        os.makedirs(dir_path, exist_ok=True)
            
            # Validate function arguments against schema (helpful for debugging)
            schema_validation_result = self._validate_function_args(function_name, function_args)
            if schema_validation_result:
                print(f"💡 {schema_validation_result}")
                        
            # Execute the function with sanitized arguments
            try:
                function_response = function_to_call(**function_args)
                print(f"📊 Function result: {function_response}")
            except Exception as e:
                print(f"❌ Error executing {function_name}: {str(e)}")
                function_response = f"Error in {function_name}: {str(e)}"
            
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
        # No need to change directory here - the run manager handles this
        try:
            if API_PROVIDER == "gemini":
                # Convert conversation_history to a single string prompt for Gemini
                prompt = "\n".join([
                    (msg.get("content") if isinstance(msg.get("content"), str) else str(msg.get("content")))
                    for msg in conversation_history if msg.get("role") == "user"
                ])
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt
                )
                if hasattr(response, "text"):
                    return {"role": "assistant", "content": response.text}
                return None
            else:
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