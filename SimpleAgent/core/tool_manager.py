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

    def get_repository_tree(self) -> Optional[Dict[str, Any]]:
        """
        Get the entire repository tree structure using Git Trees API.
        This is much more efficient than making individual API calls.
        
        Returns:
            Repository tree data, or None if failed
        """
        # First, get the default branch to get the latest commit SHA
        repo_url = f"{GITHUB_API_BASE}/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}"
        
        # Set up headers with authentication if token is available
        headers = {}
        if GITHUB_TOKEN:
            headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
            headers["Accept"] = "application/vnd.github+json"
        
        try:
            # Get repository info to get default branch
            response = requests.get(repo_url, headers=headers, timeout=10)
            response.raise_for_status()
            repo_info = response.json()
            default_branch = repo_info.get('default_branch', 'main')
            
            # Get the tree SHA for the default branch
            tree_url = f"{GITHUB_API_BASE}/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/git/trees/{default_branch}?recursive=1"
            
            self.logger.info(f"🌳 Fetching entire repository tree from GitHub (branch: {default_branch})...")
            response = requests.get(tree_url, headers=headers, timeout=30)
            response.raise_for_status()
            tree_data = response.json()
            
            if tree_data.get('truncated', False):
                self.logger.warning("⚠️ Repository tree was truncated - some files may be missing")
            
            return tree_data
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch repository tree: {e}")
            return None

    def fetch_file_content_batch(self, file_paths: List[str]) -> Dict[str, str]:
        """
        Fetch multiple file contents efficiently.
        
        Args:
            file_paths: List of file paths to fetch
            
        Returns:
            Dictionary mapping file path to content
        """
        file_contents = {}
        
        # Set up headers with authentication if token is available
        headers = {}
        if GITHUB_TOKEN:
            headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
            headers["Accept"] = "application/vnd.github+json"
        
        self.logger.info(f"📥 Fetching {len(file_paths)} tool files from GitHub...")
        
        for i, file_path in enumerate(file_paths):
            try:
                url = f"{GITHUB_API_BASE}/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/contents/{file_path}"
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                file_info = response.json()
                
                if file_info.get('encoding') == 'base64':
                    content = base64.b64decode(file_info['content']).decode('utf-8')
                    file_contents[file_path] = content
                    self.logger.debug(f"✅ Fetched {file_path} ({i+1}/{len(file_paths)})")
                else:
                    self.logger.error(f"❌ Unexpected encoding for {file_path}: {file_info.get('encoding')}")
                    
            except requests.RequestException as e:
                if "rate limit" in str(e).lower():
                    self.logger.warning(f"⚠️ Rate limit reached while fetching {file_path}. Consider using a GitHub token.")
                    break
                else:
                    self.logger.error(f"❌ Failed to fetch {file_path}: {e}")
            except Exception as e:
                self.logger.error(f"❌ Failed to decode {file_path}: {e}")
        
        return file_contents

    def discover_github_tools_optimized(self) -> Dict[str, Dict[str, str]]:
        """
        Discover and fetch all tools from GitHub repository using optimized tree API.
        
        Returns:
            Dictionary mapping category -> {filename: content}
        """
        github_tools = {}
        
        # Get the entire repository tree in one API call
        tree_data = self.get_repository_tree()
        if not tree_data:
            return github_tools
        
        # Parse the tree to find all Python files in the commands directory
        tool_files = []
        commands_prefix = f"{GITHUB_COMMANDS_PATH}/"
        
        for item in tree_data.get('tree', []):
            path = item.get('path', '')
            item_type = item.get('type', '')
            
            # Only process files in the commands directory
            if not path.startswith(commands_prefix):
                continue
                
            # Only process Python files
            if item_type == 'blob' and path.endswith('.py'):
                # Skip __pycache__ files but include __init__.py files (they contain the tools)
                if '__pycache__' in path:
                    continue
                    
                tool_files.append(path)
        
        if not tool_files:
            self.logger.warning("⚠️ No tool files found in repository")
            return github_tools
        
        self.logger.info(f"🔍 Found {len(tool_files)} tool files in repository")
        
        # Fetch all file contents
        file_contents = self.fetch_file_content_batch(tool_files)
        
        # Organize files by category
        for file_path, content in file_contents.items():
            # Extract category and tool name from path
            # Expected format: commands/category/tool_name/__init__.py
            path_parts = file_path.split('/')
            
            if len(path_parts) >= 4 and path_parts[-1] == '__init__.py':
                # Format: commands/category/tool_name/__init__.py
                category = path_parts[1]  # e.g., 'file_ops'
                tool_name = path_parts[2]  # e.g., 'edit_file'
                filename = f"{tool_name}.py"
                
                if category not in github_tools:
                    github_tools[category] = {}
                
                github_tools[category][filename] = content
                self.logger.debug(f"📦 Organized tool: {file_path} -> {category}/{filename}")
            elif len(path_parts) >= 3 and not path_parts[-1] == '__init__.py':
                # Format: commands/category/tool_name.py (direct Python file)
                category = path_parts[1]  # e.g., 'file_ops'
                filename = path_parts[2]  # e.g., 'tool_name.py'
                
                if category not in github_tools:
                    github_tools[category] = {}
                
                github_tools[category][filename] = content
                self.logger.debug(f"📦 Organized tool: {file_path} -> {category}/{filename}")
        
        total_tools = sum(len(files) for files in github_tools.values())
        self.logger.info(f"✅ Successfully organized {total_tools} tools across {len(github_tools)} categories")
        
        return github_tools

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
        
        # Then, discover and load GitHub tools using optimized method
        self.logger.info("🌐 Discovering GitHub tools (optimized)...")
        github_tools = self.discover_github_tools_optimized()
        
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