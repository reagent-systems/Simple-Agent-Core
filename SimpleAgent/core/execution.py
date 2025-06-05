"""
SimpleAgent Execution Module

This module handles command execution and step management for SimpleAgent.
"""

import os
import json
import time
import inspect
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
        
        Args:
            function_name: Name of the function being called
            function_args: Original function arguments
            
        Returns:
            Modified function arguments with updated paths
        """
        if function_name not in self.FILE_OPS:
            return function_args

        modified_args = function_args.copy()
        path_params = {
            "file_path": "file_path",
            "directory_path": "directory_path",
            "target_file": "target_file",
            "source_file": "source_file",
            "destination": "destination",
            "path": "path",
            "target_dir": "target_dir"  # Add target_dir for github_fork_clone
        }
        for param_name in path_params.values():
            if param_name in modified_args:

                # Always convert paths to be within output directory
                modified_args[param_name] = get_secure_path(modified_args[param_name], self.output_dir)
                
                # For some operations (like read_file), verify the file exists within output directory
                if function_name in ["read_file", "edit_file", "append_file", "delete_file", "file_exists"]:
                    # Get absolute paths for comparison
                    abs_path = os.path.abspath(modified_args[param_name])
                    abs_output_dir = os.path.abspath(self.output_dir)
                    
                    # Handle the case of nested output directories
                    is_within_output = False
                    
                    # Check direct path containment
                    if abs_path.startswith(abs_output_dir):
                        is_within_output = True
                    
                    # Check if path matches pattern of doubled output dir
                    output_dir_name = os.path.basename(abs_output_dir)
                    doubled_pattern = os.path.join(abs_output_dir, output_dir_name)
                    if abs_path.startswith(doubled_pattern):
                        is_within_output = True
                        
                    # Verify file exists and is within output directory
                    if not os.path.exists(modified_args[param_name]) or not is_within_output:
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
                           if k in ["file_path", "directory_path", "target_file", "source_file", "destination", "path", "target_dir"]]
                
                # Verify all paths are within output directory
                for path in path_args:
                    abs_path = os.path.abspath(path)
                    abs_output_dir = os.path.abspath(self.output_dir)
                    
                    # Handle the case of nested output directories
                    # Check if the path contains the output directory anywhere in its path
                    # This fixes the issue with paths like output\output\clix\file.txt
                    is_within_output = False
                    
                    # Check direct path containment
                    if abs_path.startswith(abs_output_dir):
                        is_within_output = True
                    
                    # Check if path matches pattern of doubled output dir
                    output_dir_name = os.path.basename(abs_output_dir)
                    doubled_pattern = os.path.join(abs_output_dir, output_dir_name)
                    if abs_path.startswith(doubled_pattern):
                        is_within_output = True
                        
                    # If dealing with a git repository or other allowed operation
                    if function_name == "github_fork_clone" and any(segment in abs_path for segment in ["clix", ".git"]):
                        is_within_output = True
                    
                    # If path not within output directory, block the operation
                    if not is_within_output:
                        print(f"⚠️ SECURITY BLOCKED: Attempted to access path outside of output directory: {path}")
                        return "Operation blocked: Security violation - attempted to access path outside of output directory", None
                path_arg = next((v for k, v in function_args.items() 
                              if k in ["file_path", "directory_path", "target_file", "target_dir"]), None)
                if path_arg:
                    dir_path = os.path.dirname(path_arg) if function_name != "create_directory" else path_arg
                    if dir_path:
                        os.makedirs(dir_path, exist_ok=True)
                        
            # Execute the function with sanitized arguments
            try:
                # Apply dynamic parameter mapping to handle parameter name mismatches
                mapped_args = self._map_function_parameters(function_to_call, function_args)
                function_response = function_to_call(**mapped_args)
                print(f"📊 Function result: {function_response}")
            except UnboundLocalError as e:
                if "stop_words" in str(e) and function_name == "text_analysis":
                    print(f"⚠️ Warning: text_analysis command has a scoping issue with 'stop_words' variable")
                    print(f"   This occurs when 'summary' analysis is requested without 'keywords' analysis")
                    print(f"   Retrying with both 'keywords' and requested analysis types...")
                    
                    # Fix the issue by ensuring keywords analysis is included
                    if 'analysis_types' in function_args:
                        analysis_types = function_args['analysis_types']
                        if 'keywords' not in analysis_types:
                            function_args['analysis_types'] = ['keywords'] + analysis_types
                            print(f"   Modified analysis_types to: {function_args['analysis_types']}")
                            
                    # Retry the function call
                    try:
                        # Re-apply parameter mapping after modifying analysis_types
                        mapped_args = self._map_function_parameters(function_to_call, function_args)
                        function_response = function_to_call(**mapped_args)
                        print(f"📊 Function result (retry): {function_response}")
                    except Exception as retry_e:
                        print(f"❌ Retry failed: {str(retry_e)}")
                        function_response = f"Error in {function_name}: {str(retry_e)}"
                else:
                    print(f"❌ UnboundLocalError in {function_name}: {str(e)}")
                    function_response = f"Error in {function_name}: {str(e)}"
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

    def _map_function_parameters(self, function: Callable, function_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map function arguments using the tool's schema.
        
        Args:
            function: The function to call
            function_args: The arguments from the LLM
            
        Returns:
            Mapped arguments that match the function signature
        """
        try:
            # Get the function signature
            sig = inspect.signature(function)
            expected_params = set(sig.parameters.keys())
            provided_params = set(function_args.keys())
            
            # If all parameters match, no mapping needed
            if provided_params.issubset(expected_params):
                return function_args
            
            # Find the schema for this function
            function_name = function.__name__
            function_schema = None
            
            for schema in COMMAND_SCHEMAS:
                schema_name = schema.get("function", {}).get("name")
                if schema_name == function_name:
                    function_schema = schema
                    break
            
            if not function_schema:
                print(f"⚠️ No schema found for {function_name}")
                return function_args
            
            # Get expected parameter names from schema
            schema_params = function_schema.get("function", {}).get("parameters", {}).get("properties", {})
            schema_param_names = set(schema_params.keys())
            
            mapped_args = {}
            
            # Map parameters based on schema
            for provided_key, value in function_args.items():
                # Direct match with schema
                if provided_key in schema_param_names:
                    mapped_args[provided_key] = value
                    continue
                
                # Case-insensitive match
                matched = False
                for schema_param in schema_param_names:
                    if provided_key.lower() == schema_param.lower():
                        mapped_args[schema_param] = value
                        print(f"🔧 Parameter mapping: '{provided_key}' -> '{schema_param}' (case insensitive)")
                        matched = True
                        break
                
                # If no match, try partial matching (e.g., 'path' -> 'file_path')
                if not matched:
                    for schema_param in schema_param_names:
                        # Enhanced partial matching for common variations
                        provided_lower = provided_key.lower()
                        schema_lower = schema_param.lower()
                        
                        # Check if they share common roots
                        match_found = False
                        
                        # Common file/path parameter variations
                        if (('file' in provided_lower or 'path' in provided_lower or 'name' in provided_lower) and 
                            ('file' in schema_lower or 'path' in schema_lower)):
                            match_found = True
                        
                        # Standard partial matching (substring check)
                        elif (provided_lower in schema_lower or schema_lower in provided_lower):
                            match_found = True
                        
                        if match_found and schema_param not in mapped_args:
                            mapped_args[schema_param] = value
                            print(f"🔧 Parameter mapping: '{provided_key}' -> '{schema_param}' (partial match)")
                            matched = True
                            break
                
                # If still no match, keep the original parameter name
                if not matched:
                    mapped_args[provided_key] = value
            
            return mapped_args
            
        except Exception as e:
            print(f"⚠️ Parameter mapping failed: {e}")
            return function_args 