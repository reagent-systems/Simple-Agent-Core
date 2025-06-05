"""
Tool Manager for SimpleAgent.

This module handles dynamic loading of tools from the GitHub repository:
https://github.com/reagent-systems/Simple-Agent-Tools

Features:
- Dynamic tool discovery from GitHub
- On-demand tool loading
- Proper schema extraction
- Clean and simple API
"""

import os
import sys
import json
import base64
import logging
import requests
import tempfile
import importlib
import importlib.util
from typing import Dict, Any, Callable, List, Optional, Tuple
from dataclasses import dataclass, field
import ast
import re

# Import GitHub token from config
from core.config import GITHUB_TOKEN

# Global registries
REGISTERED_COMMANDS: Dict[str, Callable] = {}
COMMAND_SCHEMAS: List[Dict[str, Any]] = []

# GitHub repository configuration
GITHUB_REPO = "reagent-systems/Simple-Agent-Tools"
GITHUB_API_BASE = "https://api.github.com"


@dataclass
class Tool:
    """Represents a tool that can be loaded dynamically."""
    name: str
    category: str
    github_path: str
    schema: Dict[str, Any] = field(default_factory=dict)
    function: Optional[Callable] = None
    loaded: bool = False
    content: Optional[str] = None


class ToolManager:
    """Manages dynamic tool loading from GitHub repository."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.tools: Dict[str, Tool] = {}
        self.temp_dir: Optional[str] = None
        self._headers = self._setup_github_headers()
        
    def _setup_github_headers(self) -> Dict[str, str]:
        """Setup GitHub API headers with authentication if available."""
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        if GITHUB_TOKEN:
            headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
        return headers
    
    def initialize(self) -> None:
        """Initialize the tool manager by discovering available tools."""
        self.logger.info("🚀 Initializing Tool Manager...")
        self._create_temp_directory()
        self._discover_tools()
        self._register_tool_schemas()
        self.logger.info(f"✅ Discovered {len(self.tools)} tools")
        
    def _create_temp_directory(self) -> None:
        """Create a temporary directory for tool modules."""
        self.temp_dir = tempfile.mkdtemp(prefix="simple_agent_tools_")
        # Add to Python path
        sys.path.insert(0, self.temp_dir)
        
    def _discover_tools(self) -> None:
        """Discover all available tools from GitHub repository."""
        try:
            # Get repository tree
            url = f"{GITHUB_API_BASE}/repos/{GITHUB_REPO}/git/trees/main?recursive=1"
            response = requests.get(url, headers=self._headers, timeout=30)
            response.raise_for_status()
            tree = response.json()
            
            # Find all tool files
            for item in tree.get('tree', []):
                path = item.get('path', '')
                
                # Look for __init__.py files in commands directory
                if (path.startswith('commands/') and 
                    path.endswith('/__init__.py') and
                    path.count('/') == 3):  # commands/category/tool_name/__init__.py
                    
                    parts = path.split('/')
                    category = parts[1]
                    tool_name = parts[2]
                    
                    tool = Tool(
                        name=tool_name,
                        category=category,
                        github_path=path
                    )
                    self.tools[tool_name] = tool
                    self.logger.debug(f"Discovered tool: {tool_name} in {category}")
                    
        except Exception as e:
            self.logger.error(f"Failed to discover tools: {e}")
            
    def _fetch_tool_content(self, tool: Tool) -> Optional[str]:
        """Fetch the content of a tool file from GitHub."""
        if tool.content:
            return tool.content
            
        try:
            url = f"{GITHUB_API_BASE}/repos/{GITHUB_REPO}/contents/{tool.github_path}"
            response = requests.get(url, headers=self._headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('encoding') == 'base64':
                content = base64.b64decode(data['content']).decode('utf-8')
                tool.content = content
                return content
            
        except Exception as e:
            self.logger.error(f"Failed to fetch content for {tool.name}: {e}")
            
        return None
    
    def _extract_schema_from_content(self, content: str) -> Optional[Dict[str, Any]]:
        """Extract schema from tool file content."""
        try:
            # Try multiple approaches to extract the schema
            
            # Approach 1: Look for a complete schema assignment in the AST
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id.endswith('_SCHEMA'):
                            # Try to safely evaluate the schema
                            try:
                                # Find the schema definition in the original content
                                lines = content.splitlines()
                                start_line = node.lineno - 1
                                
                                # Find the complete dictionary definition
                                schema_lines = []
                                brace_count = 0
                                in_schema = False
                                
                                for i in range(start_line, len(lines)):
                                    line = lines[i]
                                    if not in_schema and '{' in line:
                                        in_schema = True
                                    
                                    if in_schema:
                                        schema_lines.append(line)
                                        brace_count += line.count('{') - line.count('}')
                                        
                                        if brace_count == 0:
                                            break
                                
                                if schema_lines:
                                    schema_text = '\n'.join(schema_lines)
                                    # Extract just the dictionary part
                                    dict_start = schema_text.find('{')
                                    if dict_start >= 0:
                                        schema_dict_text = schema_text[dict_start:]
                                        # Use ast.literal_eval for safe evaluation
                                        schema = ast.literal_eval(schema_dict_text)
                                        return schema
                            except:
                                pass
            
            # Approach 2: Use regex to find complete schema definitions
            # This handles multi-line schemas better
            schema_pattern = r'(\w+_SCHEMA)\s*=\s*(\{(?:[^{}]|(?:\{[^{}]*\}))*\})'
            matches = re.findall(schema_pattern, content, re.MULTILINE | re.DOTALL)
            
            for var_name, schema_str in matches:
                try:
                    # Clean up the schema string
                    schema_str = schema_str.strip()
                    # Use ast.literal_eval for safe evaluation
                    schema = ast.literal_eval(schema_str)
                    return schema
                except:
                    # If literal_eval fails, try to clean and evaluate
                    try:
                        # Remove comments
                        cleaned = re.sub(r'#.*', '', schema_str)
                        schema = ast.literal_eval(cleaned)
                        return schema
                    except:
                        pass
            
            # Approach 3: Look for register_command calls with inline schemas
            register_pattern = r'register_command\s*\(\s*["\'](\w+)["\']\s*,\s*\w+\s*,\s*(\{(?:[^{}]|(?:\{[^{}]*\}))*\})\s*\)'
            register_matches = re.findall(register_pattern, content, re.MULTILINE | re.DOTALL)
            
            for cmd_name, schema_str in register_matches:
                try:
                    schema = ast.literal_eval(schema_str.strip())
                    return schema
                except:
                    pass
                    
        except Exception as e:
            self.logger.debug(f"Failed to extract schema: {e}")
            
        # If we can't extract the schema, return a basic one
        # The tool will still work, just without proper parameter validation
        return None
    
    def _create_tool_module(self, tool: Tool) -> bool:
        """Create a Python module for the tool in the temp directory."""
        if not self.temp_dir or not tool.content:
            return False
            
        try:
            # Create category directory
            category_dir = os.path.join(self.temp_dir, tool.category)
            os.makedirs(category_dir, exist_ok=True)
            
            # Create category __init__.py
            category_init = os.path.join(category_dir, "__init__.py")
            if not os.path.exists(category_init):
                with open(category_init, 'w') as f:
                    f.write("")
            
            # Create tool directory and file
            tool_dir = os.path.join(category_dir, tool.name)
            os.makedirs(tool_dir, exist_ok=True)
            
            tool_file = os.path.join(tool_dir, "__init__.py")
            with open(tool_file, 'w', encoding='utf-8') as f:
                f.write(tool.content)
                
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create module for {tool.name}: {e}")
            return False
    
    def load_tool(self, tool_name: str) -> bool:
        """Load a specific tool on demand."""
        if tool_name not in self.tools:
            self.logger.error(f"Tool '{tool_name}' not found")
            return False
            
        tool = self.tools[tool_name]
        
        # Check if already loaded
        if tool.loaded and tool_name in REGISTERED_COMMANDS:
            return True
            
        self.logger.info(f"Loading tool: {tool_name}")
        
        try:
            # Fetch content if not already fetched
            if not tool.content:
                content = self._fetch_tool_content(tool)
                if not content:
                    return False
            
            # Extract schema if not already extracted
            if not tool.schema and tool.content:
                schema = self._extract_schema_from_content(tool.content)
                if schema:
                    tool.schema = schema
            
            # Create module
            if not self._create_tool_module(tool):
                return False
            
            # Import the module
            module_path = f"{tool.category}.{tool.name}"
            module = importlib.import_module(module_path)
            
            # The tool should have registered itself via register_command
            if tool_name in REGISTERED_COMMANDS:
                tool.loaded = True
                tool.function = REGISTERED_COMMANDS[tool_name]
                self.logger.info(f"✅ Successfully loaded: {tool_name}")
                return True
            else:
                self.logger.error(f"Tool {tool_name} did not register itself")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to load tool {tool_name}: {e}")
            return False
    
    def _register_tool_schemas(self) -> None:
        """Register schemas for all discovered tools."""
        for tool_name, tool in self.tools.items():
            # Create a basic schema that will be replaced when the tool loads
            basic_schema = {
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": f"{tool_name.replace('_', ' ').title()} - Tool in {tool.category} category",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
            
            # This will be replaced with the actual schema when the tool loads
            COMMAND_SCHEMAS.append(basic_schema)
    
    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """Get information about a specific tool."""
        return self.tools.get(tool_name)
    
    def list_tools(self) -> List[str]:
        """List all available tool names."""
        return list(self.tools.keys())
    
    def list_tools_by_category(self) -> Dict[str, List[str]]:
        """List tools grouped by category."""
        categories = {}
        for tool in self.tools.values():
            if tool.category not in categories:
                categories[tool.category] = []
            categories[tool.category].append(tool.name)
        return categories
    
    def print_tools(self) -> None:
        """Print a formatted list of available tools."""
        print("\n" + "=" * 80)
        print("🛠️  AVAILABLE TOOLS")
        print("=" * 80)
        
        categories = self.list_tools_by_category()
        
        for category in sorted(categories.keys()):
            # Determine display name and icon
            icons = {
                'file_ops': '📁',
                'github_ops': '🐙',
                'web_ops': '🌐',
                'system_ops': '💻',
                'data_ops': '📊'
            }
            icon = icons.get(category, '🔧')
            display_name = category.replace('_', ' ').title()
            
            tools = sorted(categories[category])
            loaded = sum(1 for t in tools if self.tools[t].loaded)
            
            print(f"\n{icon} {display_name} ({loaded}/{len(tools)} loaded)")
            print("-" * 50)
            
            for tool_name in tools:
                tool = self.tools[tool_name]
                status = "✅" if tool.loaded else "⏳"
                print(f"  {status} {tool_name}")
        
        total = len(self.tools)
        loaded = sum(1 for t in self.tools.values() if t.loaded)
        
        print("\n" + "=" * 80)
        print(f"📊 Total: {total} tools available, {loaded} loaded")
        print("💡 Tools are loaded automatically when needed")
        print("=" * 80 + "\n")
    
    def cleanup(self) -> None:
        """Clean up temporary resources."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                import shutil
                shutil.rmtree(self.temp_dir)
                self.logger.debug("Cleaned up temporary directory")
            except Exception as e:
                self.logger.error(f"Failed to cleanup: {e}")


# Global instance
_tool_manager: Optional[ToolManager] = None


def get_tool_manager() -> ToolManager:
    """Get or create the global tool manager instance."""
    global _tool_manager
    if _tool_manager is None:
        _tool_manager = ToolManager()
    return _tool_manager


def register_command(name: str, func: Callable, schema: Dict[str, Any]) -> None:
    """
    Register a command with SimpleAgent.
    This is called by tools when they are loaded.
    """
    REGISTERED_COMMANDS[name] = func
    
    # Update the schema in COMMAND_SCHEMAS
    for i, existing_schema in enumerate(COMMAND_SCHEMAS):
        if existing_schema.get("function", {}).get("name") == name:
            COMMAND_SCHEMAS[i] = schema
            break
    else:
        COMMAND_SCHEMAS.append(schema)
    
    logging.getLogger(__name__).debug(f"Registered command: {name}")


def init() -> None:
    """Initialize the tool manager."""
    manager = get_tool_manager()
    manager.initialize()
    manager.print_tools()


def load_tool(tool_name: str) -> bool:
    """Load a specific tool on demand."""
    return get_tool_manager().load_tool(tool_name)


def cleanup() -> None:
    """Clean up tool manager resources."""
    global _tool_manager
    if _tool_manager:
        _tool_manager.cleanup()
        _tool_manager = None 