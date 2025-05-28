"""
Tool Manager for SimpleAgent.

This module handles fetching and initializing tools from multiple sources:
1. Local commands directory
2. Remote GitHub repository via API
"""

import os
import sys
import json
import base64
import logging
import importlib
import pkgutil
import requests
from typing import Dict, Any, Callable, List, Optional, Tuple
from collections import defaultdict
import tempfile
import shutil

# Import GitHub token from config
from core.config import GITHUB_TOKEN

# Dictionary to store all registered commands
REGISTERED_COMMANDS: Dict[str, Callable] = {}

# Dictionary to store all command schemas
COMMAND_SCHEMAS: List[Dict[str, Any]] = []

# Dictionary to store commands by category
COMMANDS_BY_CATEGORY: Dict[str, List[str]] = defaultdict(list)

# GitHub repository configuration
GITHUB_REPO_OWNER = "reagent-systems"
GITHUB_REPO_NAME = "Simple-Agent-Tools"
GITHUB_COMMANDS_PATH = "commands"
GITHUB_API_BASE = "https://api.github.com"


class ToolManager:
    """Manages tools from both local and remote sources."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.temp_dir = None
        
    def register_command(self, name: str, func: Callable, schema: Dict[str, Any]) -> None:
        """
        Register a command with SimpleAgent.
        
        Args:
            name: The name of the command
            func: The function to execute
            schema: The OpenAI function schema for the command
        """
        REGISTERED_COMMANDS[name] = func
        COMMAND_SCHEMAS.append(schema)
        
        # Determine category from the module path
        module = func.__module__
        category = module.split('.')[1] if len(module.split('.')) > 1 else 'misc'
        COMMANDS_BY_CATEGORY[category].append(name)
        
        # Only log at debug level to reduce noise
        self.logger.debug(f'Registering command: {name} in category: {category}')

    def fetch_github_directory_contents(self, path: str = "") -> List[Dict[str, Any]]:
        """
        Fetch directory contents from GitHub repository.
        
        Args:
            path: Path within the repository (default: root)
            
        Returns:
            List of file/directory information
        """
        url = f"{GITHUB_API_BASE}/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/contents/{path}"
        
        # Set up headers with authentication if token is available
        headers = {}
        if GITHUB_TOKEN:
            headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
            headers["Accept"] = "application/vnd.github+json"
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch GitHub directory contents for {path}: {e}")
            return []

    def fetch_github_file_content(self, path: str) -> Optional[str]:
        """
        Fetch file content from GitHub repository.
        
        Args:
            path: Path to the file in the repository
            
        Returns:
            File content as string, or None if failed
        """
        url = f"{GITHUB_API_BASE}/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/contents/{path}"
        
        # Set up headers with authentication if token is available
        headers = {}
        if GITHUB_TOKEN:
            headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
            headers["Accept"] = "application/vnd.github+json"
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            file_info = response.json()
            
            if file_info.get('encoding') == 'base64':
                content = base64.b64decode(file_info['content']).decode('utf-8')
                return content
            else:
                self.logger.error(f"Unexpected encoding for file {path}: {file_info.get('encoding')}")
                return None
                
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch GitHub file content for {path}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Failed to decode file content for {path}: {e}")
            return None

    def create_temp_module_structure(self, github_tools: Dict[str, Dict[str, str]]) -> Optional[str]:
        """
        Create temporary module structure for GitHub tools.
        
        Args:
            github_tools: Dictionary mapping category -> {filename: content}
            
        Returns:
            Path to temporary directory, or None if failed
        """
        try:
            # Create temporary directory
            self.temp_dir = tempfile.mkdtemp(prefix="simple_agent_tools_")
            
            # Create __init__.py for the temp directory
            init_path = os.path.join(self.temp_dir, "__init__.py")
            with open(init_path, 'w') as f:
                f.write('# Temporary module for GitHub tools\n')
            
            # Create category directories and files
            for category, files in github_tools.items():
                category_dir = os.path.join(self.temp_dir, category)
                os.makedirs(category_dir, exist_ok=True)
                
                # Create category __init__.py
                category_init = os.path.join(category_dir, "__init__.py")
                with open(category_init, 'w') as f:
                    f.write(f'# {category} tools from GitHub\n')
                
                # Create tool files
                for filename, content in files.items():
                    if filename.endswith('.py'):
                        file_path = os.path.join(category_dir, filename)
                        with open(file_path, 'w') as f:
                            f.write(content)
            
            return self.temp_dir
            
        except Exception as e:
            self.logger.error(f"Failed to create temporary module structure: {e}")
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
            return None

    def discover_github_tools(self) -> Dict[str, Dict[str, str]]:
        """
        Discover and fetch all tools from GitHub repository.
        
        Returns:
            Dictionary mapping category -> {filename: content}
        """
        github_tools = {}
        
        # Get contents of the commands directory
        commands_contents = self.fetch_github_directory_contents(GITHUB_COMMANDS_PATH)
        
        for item in commands_contents:
            if item['type'] == 'dir':
                category_name = item['name']
                
                # Skip special directories
                if category_name.startswith('.') or category_name == '__pycache__':
                    continue
                
                self.logger.debug(f"Discovering GitHub tools in category: {category_name}")
                
                # Get contents of the category directory
                category_path = f"{GITHUB_COMMANDS_PATH}/{category_name}"
                category_contents = self.fetch_github_directory_contents(category_path)
                
                category_files = {}
                for tool_item in category_contents:
                    if tool_item['type'] == 'dir':
                        # Each tool is in its own directory
                        tool_name = tool_item['name']
                        tool_path = f"{category_path}/{tool_name}"
                        
                        # Get contents of the tool directory
                        tool_contents = self.fetch_github_directory_contents(tool_path)
                        
                        for file_item in tool_contents:
                            if file_item['type'] == 'file' and file_item['name'].endswith('.py'):
                                file_path = f"{tool_path}/{file_item['name']}"
                                file_content = self.fetch_github_file_content(file_path)
                                
                                if file_content:
                                    # Use tool_name as the filename (without .py extension for __init__.py)
                                    if file_item['name'] == '__init__.py':
                                        filename = f"{tool_name}.py"
                                    else:
                                        filename = f"{tool_name}_{file_item['name']}"
                                    
                                    category_files[filename] = file_content
                                    self.logger.debug(f"Fetched GitHub tool: {file_path} -> {filename}")
                    elif tool_item['type'] == 'file' and tool_item['name'].endswith('.py'):
                        # Handle direct Python files in category directory (fallback)
                        file_path = f"{category_path}/{tool_item['name']}"
                        file_content = self.fetch_github_file_content(file_path)
                        
                        if file_content:
                            category_files[tool_item['name']] = file_content
                            self.logger.debug(f"Fetched GitHub tool: {file_path}")
                
                if category_files:
                    github_tools[category_name] = category_files
        
        return github_tools

    def load_github_tools(self, temp_module_path: str, github_tools: Dict[str, Dict[str, str]]) -> None:
        """
        Load GitHub tools from temporary module structure.
        
        Args:
            temp_module_path: Path to temporary module directory
            github_tools: Dictionary mapping category -> {filename: content}
        """
        # Add temp directory to Python path
        if temp_module_path not in sys.path:
            sys.path.insert(0, temp_module_path)
        
        # Determine if running in CI
        skip_gui_commands = os.environ.get("CI", "").lower() == "true"
        gui_commands = [("system_ops", "screenshot")]
        
        try:
            for category_name, files in github_tools.items():
                for filename in files.keys():
                    if filename.endswith('.py') and filename != '__init__.py':
                        module_name = filename[:-3]  # Remove .py extension
                        
                        # Skip GUI commands in CI
                        if skip_gui_commands and (category_name, module_name) in gui_commands:
                            self.logger.info(f'Skipping GUI command module in CI: {category_name}.{module_name}')
                            continue
                        
                        try:
                            # Import the module
                            full_module_name = f"{category_name}.{module_name}"
                            module = importlib.import_module(full_module_name)
                            self.logger.debug(f'Imported GitHub tool module: {full_module_name}')
                            
                        except Exception as e:
                            self.logger.error(f"Failed to import GitHub tool module {full_module_name}: {e}")
                            
        except Exception as e:
            self.logger.error(f"Failed to load GitHub tools: {e}")

    def discover_local_commands(self) -> None:
        """
        Discover and register all commands in the local commands package.
        """
        try:
            # Import commands package
            import commands
            
            # Get the directory of the commands package
            package_dir = os.path.dirname(commands.__file__)

            # Determine if running in CI
            skip_gui_commands = os.environ.get("CI", "").lower() == "true"
            gui_commands = [("system_ops", "screenshot")]

            # Walk through all subdirectories
            for _, category_name, is_pkg in pkgutil.iter_modules([package_dir]):
                if is_pkg:
                    # Import the category package
                    category_package = importlib.import_module(f"commands.{category_name}")
                    
                    # Get the category directory
                    category_dir = os.path.join(package_dir, category_name)
                    
                    # Walk through all modules in the category
                    for _, command_name, _ in pkgutil.iter_modules([category_dir]):
                        # Skip GUI commands in CI
                        if skip_gui_commands and (category_name, command_name) in gui_commands:
                            self.logger.info(f'Skipping GUI command module in CI: commands.{category_name}.{command_name}')
                            continue
                        # Import the command module
                        importlib.import_module(f"commands.{category_name}.{command_name}")
                        self.logger.debug(f'Importing local command module: commands.{category_name}.{command_name}')
                        
        except ImportError:
            self.logger.info("No local commands package found, skipping local command discovery")
        except Exception as e:
            self.logger.error(f"Failed to discover local commands: {e}")

    def initialize_all_tools(self) -> None:
        """
        Initialize all tools from both local and remote sources.
        """
        self.logger.info("🔧 Initializing tool manager...")
        
        # First, discover and load local commands
        self.logger.info("📁 Discovering local commands...")
        local_count_before = len(REGISTERED_COMMANDS)
        self.discover_local_commands()
        local_tools_loaded = len(REGISTERED_COMMANDS) - local_count_before
        
        # Then, discover and load GitHub tools
        self.logger.info("🌐 Discovering GitHub tools...")
        github_tools = self.discover_github_tools()
        
        if github_tools:
            total_github_tools = sum(len(files) for files in github_tools.values())
            self.logger.info(f"📦 Found {total_github_tools} tools across {len(github_tools)} categories")
            
            # Create temporary module structure
            temp_module_path = self.create_temp_module_structure(github_tools)
            
            if temp_module_path:
                # Load GitHub tools
                github_count_before = len(REGISTERED_COMMANDS)
                self.load_github_tools(temp_module_path, github_tools)
                github_tools_loaded = len(REGISTERED_COMMANDS) - github_count_before
            else:
                self.logger.error("❌ Failed to create temporary module structure for GitHub tools")
                github_tools_loaded = 0
        else:
            self.logger.warning("⚠️ No GitHub tools found or failed to fetch them")
            github_tools_loaded = 0
        
        total_tools = len(REGISTERED_COMMANDS)
        self.logger.info(f"✅ Tool initialization complete: {total_tools} tools loaded ({local_tools_loaded} local, {github_tools_loaded} remote)")

    def cleanup(self) -> None:
        """Clean up temporary resources."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                self.logger.debug("🧹 Cleaned up temporary tool directory")
            except Exception as e:
                self.logger.error(f"❌ Failed to clean up temporary directory: {e}")

    def print_commands(self) -> None:
        """Print all registered commands in a nicely formatted way."""
        print("\n" + "=" * 80)
        print("🛠️  AVAILABLE TOOLS")
        print("=" * 80)
        
        if not COMMANDS_BY_CATEGORY:
            print("❌ No tools registered yet.")
            return
        
        # Group commands by their actual categories (file_ops, github_ops, etc.)
        actual_categories = defaultdict(list)
        for category, commands in COMMANDS_BY_CATEGORY.items():
            for cmd in commands:
                # Determine actual category from command name
                if any(x in cmd for x in ['file', 'read', 'write', 'edit', 'delete', 'create_directory', 'list_directory', 'load_json', 'save_json', 'append']):
                    actual_categories['📁 File Operations'].append(cmd)
                elif any(x in cmd for x in ['github', 'git_', 'pr_', 'issue_']):
                    actual_categories['🐙 GitHub Operations'].append(cmd)
                elif any(x in cmd for x in ['web_', 'extract_links', 'fetch_json_api', 'raw_web_read']):
                    actual_categories['🌐 Web Operations'].append(cmd)
                elif any(x in cmd for x in ['screenshot', 'system']):
                    actual_categories['💻 System Operations'].append(cmd)
                elif any(x in cmd for x in ['text_analysis', 'analyze_image']):
                    actual_categories['🔍 Analysis Tools'].append(cmd)
                else:
                    actual_categories['🔧 Other Tools'].append(cmd)
        
        # Display commands in a compact format
        for category in sorted(actual_categories.keys()):
            commands = sorted(actual_categories[category])
            print(f"\n{category} ({len(commands)} tools)")
            print("-" * 50)
            
            # Display commands in columns for better space usage
            cols = 2
            for i in range(0, len(commands), cols):
                row_commands = commands[i:i+cols]
                for j, cmd in enumerate(row_commands):
                    if j == 0:
                        print(f"  • {cmd:<35}", end="")
                    else:
                        print(f"  • {cmd}")
                if len(row_commands) == 1:
                    print()  # New line if only one command in row
        
        print("\n" + "=" * 80)
        print(f"📊 Total: {len(REGISTERED_COMMANDS)} tools ready to use")
        print("=" * 80 + "\n")


# Global tool manager instance
_tool_manager = None

def get_tool_manager() -> ToolManager:
    """Get the global tool manager instance."""
    global _tool_manager
    if _tool_manager is None:
        _tool_manager = ToolManager()
    return _tool_manager

def register_command(name: str, func: Callable, schema: Dict[str, Any]) -> None:
    """
    Register a command with SimpleAgent.
    
    Args:
        name: The name of the command
        func: The function to execute
        schema: The OpenAI function schema for the command
    """
    get_tool_manager().register_command(name, func, schema)

def init() -> None:
    """Initialize all tools from local and remote sources."""
    tool_manager = get_tool_manager()
    tool_manager.initialize_all_tools()
    tool_manager.print_commands()

def cleanup() -> None:
    """Clean up tool manager resources."""
    global _tool_manager
    if _tool_manager:
        _tool_manager.cleanup()
        _tool_manager = None 