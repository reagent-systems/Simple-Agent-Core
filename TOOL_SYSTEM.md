# Tool Management System

## Overview

The SimpleAgent now uses a unified tool management system that can fetch and initialize tools from multiple sources:

1. **Local Commands**: Tools stored in the local `SimpleAgent/commands/` directory
2. **Remote GitHub Tools**: Tools fetched from the [Simple-Agent-Tools](https://github.com/reagent-systems/Simple-Agent-Tools) repository via GitHub API

## Architecture

### Core Components

- **`core/tool_manager.py`**: Main tool management system
- **`commands/__init__.py`**: Simplified interface that delegates to the tool manager
- **`core/execution.py`**: Updated to use the tool manager directly

### Tool Manager Features

- **Unified Registration**: Single system for registering tools from any source
- **GitHub API Integration**: Fetches tools directly from GitHub repository
- **Temporary Module Loading**: Creates temporary Python modules for GitHub tools
- **Error Handling**: Graceful handling of network issues and rate limits
- **Cleanup**: Automatic cleanup of temporary resources

## Tool Structure

### GitHub Repository Structure

The GitHub repository follows this structure:
```
commands/
├── data_ops/
│   └── text_analysis/
│       └── __init__.py
├── file_ops/
│   ├── read_file/
│   │   └── __init__.py
│   ├── write_file/
│   │   └── __init__.py
│   └── ...
├── github_ops/
│   └── ...
├── system_ops/
│   └── ...
└── web_ops/
    └── ...
```

Each tool is in its own directory with an `__init__.py` file containing the tool implementation.

### Local Commands Structure

Local commands follow the same structure as before:
```
SimpleAgent/commands/
├── __init__.py
└── test_tools/
```

## Usage

### Initialization

The tool system is automatically initialized when importing commands:

```python
import commands
commands.init()  # Fetches and registers all tools
```

### Available Tools

After initialization, tools are available in:
- `commands.REGISTERED_COMMANDS`: Dictionary of command functions
- `commands.COMMAND_SCHEMAS`: List of OpenAI function schemas
- `commands.COMMANDS_BY_CATEGORY`: Commands organized by category

### Cleanup

The system automatically cleans up temporary resources:

```python
commands.cleanup()  # Called automatically in main()
```

## Configuration

### GitHub Repository Settings

The GitHub repository configuration is in `core/tool_manager.py`:

```python
GITHUB_REPO_OWNER = "reagent-systems"
GITHUB_REPO_NAME = "Simple-Agent-Tools"
GITHUB_COMMANDS_PATH = "commands"
GITHUB_API_BASE = "https://api.github.com"
```

### Rate Limiting

The GitHub API has rate limits:
- **Unauthenticated**: 60 requests per hour
- **Authenticated**: 5,000 requests per hour

For production use, consider:
1. Adding GitHub authentication
2. Implementing caching
3. Adding retry logic with exponential backoff

## Benefits

1. **Centralized Tool Repository**: All tools in one GitHub repository
2. **Automatic Updates**: Tools are fetched fresh each time
3. **No Local Storage**: No need to maintain local copies of all tools
4. **Scalable**: Easy to add new tools to the GitHub repository
5. **Fallback Support**: Works with local tools if GitHub is unavailable

## Migration Path

### Current Status

✅ **Completed**:
- Tool manager implementation
- GitHub API integration
- Local command discovery
- Unified registration system
- Cleanup and error handling

### Next Steps

1. **Move Local Tools**: Move existing local tools to the GitHub repository
2. **Add Authentication**: Add GitHub token for higher rate limits
3. **Implement Caching**: Cache fetched tools to reduce API calls
4. **Add Retry Logic**: Handle temporary network issues
5. **Remove Local Commands**: Once all tools are in GitHub, remove local commands folder

### Moving Tools to GitHub

To move the current local commands to GitHub:

1. Create tool directories in the GitHub repository
2. Move each tool's code to its own `__init__.py` file
3. Test the tools work from GitHub
4. Remove the local commands folder

## Error Handling

The system gracefully handles:
- Network connectivity issues
- GitHub API rate limits
- Missing or malformed tools
- Import errors in tool modules

Errors are logged but don't prevent the system from working with available tools.

## Testing

The system has been tested with:
- GitHub API connectivity
- Tool discovery and fetching
- Temporary module creation
- Tool registration
- Cleanup procedures

All core functionality is working correctly. The main limitation is GitHub API rate limits when fetching many tools. 