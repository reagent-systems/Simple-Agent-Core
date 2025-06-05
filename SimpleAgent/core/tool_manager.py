"""
Tool Manager for SimpleAgent.

This module handles fetching and initializing tools from multiple sources:
1. Local commands directory
2. Remote GitHub repository via API

Features dynamic/lazy loading - tools are only loaded when needed.
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
import threading
from dataclasses import dataclass

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


@dataclass
class ToolInfo:
    """Information about a tool that can be loaded on demand."""
    name: str
    category: str
    source: str  # 'local' or 'remote'
    file_path: str
    schema: Optional[Dict[str, Any]] = None
    content: Optional[str] = None  # For remote tools
    loaded: bool = False


class DynamicToolManager:
    """Manages tools with dynamic/lazy loading from both local and remote sources."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.temp_dir = None
        self._tool_registry: Dict[str, ToolInfo] = {}
        self._load_lock = threading.Lock()
        self._initialized = False
        
    def register_command(self, name: str, func: Callable, schema: Dict[str, Any]) -> None:
        """
        Register a command with SimpleAgent.
        
        Args:
            name: The name of the command
            func: The function to execute
            schema: The OpenAI function schema for the command
        """
        REGISTERED_COMMANDS[name] = func
        
        # Remove any existing placeholder schema for this command
        existing_schema_index = None
        for i, existing_schema in enumerate(COMMAND_SCHEMAS):
            if existing_schema.get("function", {}).get("name") == name:
                existing_schema_index = i
                break
        
        if existing_schema_index is not None:
            # Replace the placeholder schema with the real one
            COMMAND_SCHEMAS[existing_schema_index] = schema
            self.logger.debug(f'Replaced placeholder schema for {name} with real schema')
        else:
            # No existing schema, append the new one
            COMMAND_SCHEMAS.append(schema)
        
        # Determine category from the module path
        module = func.__module__
        category = module.split('.')[1] if len(module.split('.')) > 1 else 'misc'
        COMMANDS_BY_CATEGORY[category].append(name)
        
        # Mark tool as loaded in registry if it exists
        if name in self._tool_registry:
            self._tool_registry[name].loaded = True
        
        # Only log at debug level to reduce noise
        self.logger.debug(f'Registering command: {name} in category: {category}')

    def discover_available_tools(self) -> None:
        """
        Discover all available tools without loading them.
        This creates a registry of tools that can be loaded on demand.
        """
        self.logger.info("🔍 Discovering available tools...")
        
        # Discover local tools
        self._discover_local_tools()
        
        # Discover remote tools
        self._discover_remote_tools()
        
        local_count = sum(1 for tool in self._tool_registry.values() if tool.source == 'local')
        remote_count = sum(1 for tool in self._tool_registry.values() if tool.source == 'remote')
        
        self.logger.info(f"✅ Tool discovery complete: {len(self._tool_registry)} tools available ({local_count} local, {remote_count} remote)")
        self._initialized = True

    def _discover_local_tools(self) -> None:
        """Discover local tools without loading them."""
        try:
            # Import commands package
            import commands
            
            # Get the directory of the commands package
            package_dir = os.path.dirname(commands.__file__)

            # Walk through all subdirectories
            for _, category_name, is_pkg in pkgutil.iter_modules([package_dir]):
                if is_pkg:
                    # Get the category directory
                    category_dir = os.path.join(package_dir, category_name)
                    
                    # Walk through all modules in the category
                    for _, command_name, _ in pkgutil.iter_modules([category_dir]):
                        tool_info = ToolInfo(
                            name=command_name,
                            category=category_name,
                            source='local',
                            file_path=f"commands.{category_name}.{command_name}"
                        )
                        self._tool_registry[command_name] = tool_info
                        self.logger.debug(f'Discovered local tool: {command_name} in {category_name}')
                        
        except ImportError:
            self.logger.info("No local commands package found, skipping local tool discovery")
        except Exception as e:
            self.logger.error(f"Failed to discover local tools: {e}")

    def _discover_remote_tools(self) -> None:
        """Discover remote tools without loading them."""
        # Get the entire repository tree in one API call
        tree_data = self.get_repository_tree()
        if not tree_data:
            return

        # Parse the tree to find all Python files in the commands directory
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
                
                # Extract category and tool name from path
                path_parts = path.split('/')
                
                if len(path_parts) >= 4 and path_parts[-1] == '__init__.py':
                    # Format: commands/category/tool_name/__init__.py
                    category = path_parts[1]
                    tool_name = path_parts[2]
                    
                    # Skip if local tool with same name exists (local takes precedence)
                    if tool_name in self._tool_registry and self._tool_registry[tool_name].source == 'local':
                        continue
                    
                    tool_info = ToolInfo(
                        name=tool_name,
                        category=category,
                        source='remote',
                        file_path=path
                    )
                    self._tool_registry[tool_name] = tool_info
                    self.logger.debug(f'Discovered remote tool: {tool_name} in {category}')
                    
                elif len(path_parts) >= 3 and not path_parts[-1] == '__init__.py':
                    # Format: commands/category/tool_name.py (direct Python file)
                    category = path_parts[1]
                    tool_name = path_parts[2][:-3]  # Remove .py extension
                    
                    # Skip if local tool with same name exists (local takes precedence)
                    if tool_name in self._tool_registry and self._tool_registry[tool_name].source == 'local':
                        continue
                    
                    tool_info = ToolInfo(
                        name=tool_name,
                        category=category,
                        source='remote',
                        file_path=path
                    )
                    self._tool_registry[tool_name] = tool_info
                    self.logger.debug(f'Discovered remote tool: {tool_name} in {category}')

    def load_tool_on_demand(self, tool_name: str) -> bool:
        """
        Load a specific tool on demand.
        
        Args:
            tool_name: Name of the tool to load
            
        Returns:
            True if tool was loaded successfully, False otherwise
        """
        with self._load_lock:
            # Check if tool is already loaded
            if tool_name in REGISTERED_COMMANDS:
                return True
            
            # Check if tool exists in registry
            if tool_name not in self._tool_registry:
                self.logger.warning(f"Tool '{tool_name}' not found in registry")
                return False
            
            tool_info = self._tool_registry[tool_name]
            
            if tool_info.loaded:
                return True
            
            self.logger.info(f"🔧 Loading tool on demand: {tool_name} ({tool_info.source})")
            
            try:
                if tool_info.source == 'local':
                    return self._load_local_tool(tool_info)
                else:
                    return self._load_remote_tool(tool_info)
            except Exception as e:
                self.logger.error(f"Failed to load tool '{tool_name}': {e}")
                return False

    def _load_local_tool(self, tool_info: ToolInfo) -> bool:
        """Load a local tool."""
        try:
            # Determine if running in CI and skip GUI commands
            skip_gui_commands = os.environ.get("CI", "").lower() == "true"
            gui_commands = [("system_ops", "screenshot")]
            
            if skip_gui_commands and (tool_info.category, tool_info.name) in gui_commands:
                self.logger.info(f'Skipping GUI command in CI: {tool_info.name}')
                return False
            
            # Import the module
            module = importlib.import_module(tool_info.file_path)
            tool_info.loaded = True
            self.logger.debug(f'Loaded local tool: {tool_info.name}')
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load local tool {tool_info.name}: {e}")
            return False

    def _load_remote_tool(self, tool_info: ToolInfo) -> bool:
        """Load a remote tool."""
        try:
            # First try to fetch just the specific tool content
            tool_content = self._fetch_single_tool_content(tool_info.file_path)
            if not tool_content:
                self.logger.error(f"Failed to fetch content for tool: {tool_info.name}")
                return False
            
            # Create temporary module structure if needed
            if not self.temp_dir:
                self._create_temp_module_structure()
            
            # Write the tool to temporary directory
            category_dir = os.path.join(self.temp_dir, tool_info.category)
            os.makedirs(category_dir, exist_ok=True)
            
            # Create __init__.py for category if it doesn't exist
            category_init = os.path.join(category_dir, "__init__.py")
            if not os.path.exists(category_init):
                with open(category_init, 'w') as f:
                    f.write('# Category module\n')
            
            # Write the tool file
            if tool_info.file_path.endswith('__init__.py'):
                tool_file = os.path.join(category_dir, tool_info.name, "__init__.py")
                os.makedirs(os.path.dirname(tool_file), exist_ok=True)
            else:
                tool_file = os.path.join(category_dir, f"{tool_info.name}.py")
            
            with open(tool_file, 'w', encoding='utf-8') as f:
                f.write(tool_content)
            
            # Import the module
            if tool_info.file_path.endswith('__init__.py'):
                module_name = f"{tool_info.category}.{tool_info.name}"
            else:
                module_name = f"{tool_info.category}.{tool_info.name}"
            
            module = importlib.import_module(module_name)
            tool_info.loaded = True
            self.logger.debug(f'Loaded remote tool: {tool_info.name}')
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load remote tool {tool_info.name}: {e}")
            return False

    def _fetch_single_tool_content(self, file_path: str) -> Optional[str]:
        """Fetch content for a single tool file."""
        headers = {}
        if GITHUB_TOKEN:
            headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
            headers["Accept"] = "application/vnd.github+json"
        
        try:
            url = f"{GITHUB_API_BASE}/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/contents/{file_path}"
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            file_info = response.json()
            
            if file_info.get('encoding') == 'base64':
                content = base64.b64decode(file_info['content']).decode('utf-8')
                self.logger.debug(f"✅ Fetched single tool: {file_path}")
                return content
            else:
                self.logger.error(f"❌ Unexpected encoding for {file_path}: {file_info.get('encoding')}")
                return None
                
        except requests.RequestException as e:
            self.logger.error(f"❌ Failed to fetch {file_path}: {e}")
            return None

    def _create_temp_module_structure(self) -> None:
        """Create temporary module structure for remote tools."""
        if self.temp_dir:
            return
            
        try:
            # Create temporary directory
            self.temp_dir = tempfile.mkdtemp(prefix="simple_agent_tools_")
            
            # Create __init__.py for the temp directory
            init_path = os.path.join(self.temp_dir, "__init__.py")
            with open(init_path, 'w') as f:
                f.write('# Temporary module for GitHub tools\n')
            
            # Add to Python path
            if self.temp_dir not in sys.path:
                sys.path.insert(0, self.temp_dir)
                
        except Exception as e:
            self.logger.error(f"Failed to create temporary module structure: {e}")
            self.temp_dir = None

    def get_available_tools(self) -> List[str]:
        """Get list of all available tools (loaded and unloaded)."""
        if not self._initialized:
            self.discover_available_tools()
        return list(self._tool_registry.keys())

    def get_tool_info(self, tool_name: str) -> Optional[ToolInfo]:
        """Get information about a specific tool."""
        return self._tool_registry.get(tool_name)

    def is_tool_loaded(self, tool_name: str) -> bool:
        """Check if a tool is currently loaded."""
        return tool_name in REGISTERED_COMMANDS

    def get_loaded_tools(self) -> List[str]:
        """Get list of currently loaded tools."""
        return list(REGISTERED_COMMANDS.keys())

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
        This is the old method - kept for backward compatibility.
        """
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
        This is the old method - kept for backward compatibility.
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
        This is the old method - kept for backward compatibility.
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

    def initialize_dynamic_tools(self) -> None:
        """
        Initialize the dynamic tool system - discovers tools but doesn't load them.
        This is the new method for dynamic loading.
        """
        self.logger.info("🚀 Initializing dynamic tool system...")
        self.discover_available_tools()
        
        # Create schemas for all available tools (needed for OpenAI function calling)
        self._create_schemas_for_available_tools()
        
        self.logger.info(f"✅ Dynamic tool system ready: {len(self._tool_registry)} tools available for on-demand loading")

    def _create_schemas_for_available_tools(self) -> None:
        """Create basic schemas for all available tools so they can be called by the AI."""
        # For now, we'll create basic schemas. In a full implementation, 
        # we might want to extract schemas from tool files without loading them.
        for tool_name, tool_info in self._tool_registry.items():
            if tool_info.schema is None:
                # Create a basic schema - this could be improved by parsing the tool file
                basic_schema = {
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "description": f"Tool from {tool_info.source} source in {tool_info.category} category",
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    }
                }
                tool_info.schema = basic_schema
                COMMAND_SCHEMAS.append(basic_schema)

    def print_available_tools(self) -> None:
        """Print all available tools (loaded and unloaded) in a nicely formatted way."""
        print("\n" + "=" * 80)
        print("🛠️  AVAILABLE TOOLS (Dynamic Loading)")
        print("=" * 80)
        
        if not self._tool_registry:
            print("❌ No tools discovered yet.")
            return
        
        # Group tools by category and source
        categories = defaultdict(lambda: {'local': [], 'remote': []})
        
        for tool_name, tool_info in self._tool_registry.items():
            categories[tool_info.category][tool_info.source].append({
                'name': tool_name,
                'loaded': tool_info.loaded or tool_name in REGISTERED_COMMANDS
            })
        
        # Display tools by category
        for category in sorted(categories.keys()):
            local_tools = sorted(categories[category]['local'], key=lambda x: x['name'])
            remote_tools = sorted(categories[category]['remote'], key=lambda x: x['name'])
            
            if local_tools or remote_tools:
                # Determine category display name
                if category == 'file_ops':
                    display_name = '📁 File Operations'
                elif category == 'github_ops':
                    display_name = '🐙 GitHub Operations'
                elif category == 'web_ops':
                    display_name = '🌐 Web Operations'
                elif category == 'system_ops':
                    display_name = '💻 System Operations'
                elif category == 'data_ops':
                    display_name = '📊 Data Operations'
                else:
                    display_name = f'🔧 {category.replace("_", " ").title()}'
                
                total_in_category = len(local_tools) + len(remote_tools)
                loaded_in_category = sum(1 for t in local_tools + remote_tools if t['loaded'])
                
                print(f"\n{display_name} ({loaded_in_category}/{total_in_category} loaded)")
                print("-" * 50)
                
                # Display local tools first
                if local_tools:
                    print("  📍 Local:")
                    for tool in local_tools:
                        status = "✅" if tool['loaded'] else "⏳"
                        print(f"    {status} {tool['name']}")
                
                # Display remote tools
                if remote_tools:
                    if local_tools:
                        print("  🌐 Remote:")
                    for tool in remote_tools:
                        status = "✅" if tool['loaded'] else "⏳"
                        print(f"    {status} {tool['name']}")
        
        total_tools = len(self._tool_registry)
        loaded_tools = len(REGISTERED_COMMANDS)
        
        print("\n" + "=" * 80)
        print(f"📊 Total: {total_tools} tools available, {loaded_tools} currently loaded")
        print("💡 Tools marked with ⏳ will be loaded automatically when needed")
        print("=" * 80 + "\n")

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

def get_tool_manager() -> DynamicToolManager:
    """Get the global tool manager instance."""
    global _tool_manager
    if _tool_manager is None:
        _tool_manager = DynamicToolManager()
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

def init(dynamic: bool = True) -> None:
    """
    Initialize tools from local and remote sources.
    
    Args:
        dynamic: If True, use dynamic loading (tools loaded on demand).
                If False, use eager loading (all tools loaded at startup).
    """
    tool_manager = get_tool_manager()
    
    if dynamic:
        tool_manager.initialize_dynamic_tools()
        tool_manager.print_available_tools()
    else:
        tool_manager.initialize_all_tools()
        tool_manager.print_commands()

def load_tool(tool_name: str) -> bool:
    """
    Load a specific tool on demand.
    
    Args:
        tool_name: Name of the tool to load
        
    Returns:
        True if tool was loaded successfully, False otherwise
    """
    return get_tool_manager().load_tool_on_demand(tool_name)

def get_available_tools() -> List[str]:
    """Get list of all available tools (loaded and unloaded)."""
    return get_tool_manager().get_available_tools()

def get_loaded_tools() -> List[str]:
    """Get list of currently loaded tools."""
    return get_tool_manager().get_loaded_tools()

def is_tool_loaded(tool_name: str) -> bool:
    """Check if a tool is currently loaded."""
    return get_tool_manager().is_tool_loaded(tool_name)

def cleanup() -> None:
    """Clean up tool manager resources."""
    global _tool_manager
    if _tool_manager:
        _tool_manager.cleanup()
        _tool_manager = None 