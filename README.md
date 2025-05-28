# SimpleAgent

A minimalist AI agent framework focused on simplicity and modularity.

## Philosophy

SimpleAgent is designed with the belief that AI agents don't need to be complex to be useful. By focusing on a small set of core operations and using function calling for all interactions, SimpleAgent remains easy to understand, modify, and extend.

## Features

- **Minimalist Design**: Only essential components, no bloat
- **Highly Modular Command System**: Each command is in its own folder for maximum modularity
- **Function-Based Operations**: All actions are performed through clear function calls
- **Transparent Execution**: See exactly what the agent is doing at each step
- **Easy to Extend**: Add new capabilities by creating new command modules
- **Change Summarization**: Automatically summarizes changes made using a cheaper GPT model
- **Modular Architecture**: Core components are separated into their own modules

## Tool Loading System

SimpleAgent features a sophisticated dual-source tool loading system that automatically fetches tools from multiple sources:

### 🌐 Remote Tool Repository
- **Primary Source**: Tools are automatically fetched from the [Simple-Agent-Tools](https://github.com/reagent-systems/Simple-Agent-Tools) GitHub repository
- **Optimized Loading**: Uses GitHub's Git Trees API to fetch the entire repository structure in just 2 API calls
- **Categories Available**:
  - `file_ops`: File operations (read, write, edit, delete, etc.)
  - `github_ops`: GitHub operations (clone, create repos, manage PRs, etc.)
  - `web_ops`: Web operations (scraping, API calls, link extraction, etc.)
  - `data_ops`: Data analysis and processing tools
  - `system_ops`: System-level operations (screenshots, etc.)
  - More to be added soon!

### 📁 Local Commands Directory
- **Secondary Source**: Tools can also be loaded from the local `commands/` directory
- **Override Capability**: Local tools take precedence over remote tools with the same name
- **Development Friendly**: Perfect for developing and testing new tools before contributing them to the main repository

### 🔧 How It Works
1. **Initialization**: When SimpleAgent starts, it initializes the tool manager
2. **Local Discovery**: First, it scans the local `commands/` directory for any custom tools
3. **Remote Discovery**: Then, it fetches the complete tool catalog from the GitHub repository using optimized API calls
4. **Tool Loading**: All discovered tools are loaded and made available to the agent
5. **Automatic Cleanup**: Temporary resources are automatically cleaned up when the session ends

## Project Structure

SimpleAgent is organized in a modular structure:

```
SimpleAgent/
  ├── core/                  # Core components
  │   ├── __init__.py        # Core package initialization
  │   ├── agent.py           # SimpleAgent agent implementation
  │   ├── config.py          # Configuration settings
  │   └── summarizer.py      # Change summarization functionality
  ├── commands/              # Command modules
  │   ├── __init__.py        # Command registration system
  │   ├── file_ops/          # File operation commands
  │   │   ├── read_file/
  │   │   ├── write_file/
  │   │   └── ...
  │   └── ...                # Other command categories
  ├── output/                # Generated files and input files directory
  ├── SimpleAgent.py          # Main entry point
  ├── requirements.txt       # Dependencies
  └── .env                   # Environment variables (create from .env.example)
```

## Command Structure

SimpleAgent organizes commands in a hierarchical structure:

```
commands/
  ├── file_ops/
  │   ├── read_file/
  │   │   └── __init__.py
  │   ├── write_file/
  │   │   └── __init__.py
  │   ├── append_file/
  │   │   └── __init__.py
  │   └── ...
  ├── web_ops/  (example future category)
  │   ├── fetch_url/
  │   │   └── __init__.py
  │   └── ...
  └── ...
```

## File Management

SimpleAgent uses an `output` directory for all file operations:

- **Generated Files**: All files created by SimpleAgent are stored in the `output` directory, organized by thread/session ID
- **Reading Files**: To have SimpleAgent read your files:
  1. Place the files you want SimpleAgent to read in the `output` directory
  2. Reference the file using its name in your instruction (e.g., "read the file 'mydata.txt' from the output folder")
  3. SimpleAgent will look for the file in the output directory and process it

This approach ensures all file operations are contained within a safe, dedicated directory.

## Configuration

SimpleAgent supports both OpenAI API and LM-Studio for local models. Configure through environment variables in the `.env` file:

### OpenAI Configuration (Default)
```
# API Provider
API_PROVIDER=openai

# OpenAI API key
OPENAI_API_KEY=your_openai_api_key_here

# GitHub API token (optional but recommended for tool loading)
GITHUB_TOKEN=your_github_personal_access_token_here

# Model settings
DEFAULT_MODEL=gpt-4o
SUMMARIZER_MODEL=gpt-3.5-turbo

# Application settings
MAX_STEPS=10
DEBUG_MODE=False
```

### LM-Studio Configuration (Local Models)
```
# API Provider
API_PROVIDER=lmstudio

# LM-Studio endpoint
API_BASE_URL=http://192.168.0.2:1234/v1

# Model settings (use your LM-Studio model name)
DEFAULT_MODEL=deepseek-r1-distill-llama-8b
SUMMARIZER_MODEL=deepseek-r1-distill-llama-8b

# Application settings
MAX_STEPS=10
DEBUG_MODE=False
```

### Gemini Configuration (Google Gemini API)
```
# API Provider
API_PROVIDER=gemini

# Gemini API key
GEMINI_API_KEY=your_gemini_api_key_here

# Model settings
DEFAULT_MODEL=gemini-2.0-flash
SUMMARIZER_MODEL=gemini-2.0-flash

# Application settings
MAX_STEPS=10
DEBUG_MODE=False
```

### Configuration Options

- **API_PROVIDER**: Set to `openai` for OpenAI API, `lmstudio` for LM-Studio, or `gemini` for Google Gemini
- **API_BASE_URL**: Required for LM-Studio, should point to your LM-Studio endpoint (e.g., `http://192.168.0.2:1234/v1`)
- **OPENAI_API_KEY**: Required for OpenAI provider
- **GEMINI_API_KEY**: Required for Gemini provider
- **DEFAULT_MODEL**: The main model to use for agent operations
- **SUMMARIZER_MODEL**: Model used for summarizing changes (can be the same as DEFAULT_MODEL for LM-Studio or Gemini)
- **MAX_STEPS**: Maximum number of execution steps
- **DEBUG_MODE**: Enable debug logging
- **OUTPUT_DIR**: Directory for file operations (default: `output`)
- **MEMORY_FILE**: Memory persistence file (default: `memory.json`)

**Note**: When using LM-Studio, some features like image analysis may not be available as they require OpenAI's vision-capable models.

## Getting Started

First (in cmd)
```
cd SimpleAgent 
python -m venv venv
venv\Scripts\activate
```

Then
```
pip install -r requirements.txt
```

### Setting up Configuration

1. Copy the example configuration:
   ```
   copy env_example.txt .env
   ```

2. Edit `.env` file with your settings:
   - For OpenAI: Set your `OPENAI_API_KEY`
   - For LM-Studio: Set `API_PROVIDER=lmstudio` and `API_BASE_URL` to your LM-Studio endpoint

Now you can run the agent
```
python SimpleAgent.py -a 10 "Your goal or instruction here"
```

Examples:
```
python SimpleAgent.py -a 10 "id like to make a python flask api that has the api /time and it simply replies the time, add a bunch of useful endpoints that can be used to get the current time, date, day, utc time, etc and more"
```

```
python SimpleAgent.py -a 10 "search the web for the latest news about AI and then write a summary of the news to a folder called news and into a file called news_summary.txt"
```

```
python SimpleAgent.py -a 15 -m 20 "make a compiler using c that will compile Arduino code into a binary file"
```

```
python SimpleAgent.py -a 10 "research and look into https://github.com/PyGithub/PyGithub, then make a docment called 'PyGitHub.txt' and do a writeup about the project"
```

```
python SimpleAgent.py -a 10 "please research the latest in stock and look at the top 10 stock prices and write them to a file called 'stock_prices.txt'"
```


## Adding New Commands

SimpleAgent supports adding commands in two ways:

### 🏠 Local Commands (Development & Custom Tools)

For developing new tools or adding custom functionality to your local instance:

1. Create a new folder in the appropriate category directory under `commands/` (or create a new category)
2. Create an `__init__.py` file in the folder
3. Define your function and its schema in the `__init__.py` file
4. Register the command using the `register_command` function
5. The command will be automatically discovered and available to the agent

Example:

```python
# commands/my_category/my_command/__init__.py
from commands import register_command

def my_command(param1: str) -> str:
    # Command implementation
    return f"Processed {param1}"

MY_COMMAND_SCHEMA = {
    "type": "function",
    "function": {
        "name": "my_command",
        "description": "Description of what the command does",
        "parameters": {
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "Description of param1"
                }
            },
            "required": ["param1"]
        }
    }
}

register_command("my_command", my_command, MY_COMMAND_SCHEMA)
```

### 🌐 Contributing to the Remote Repository

To make your tools available to all SimpleAgent users:

1. **Fork the Repository**: Fork [Simple-Agent-Tools](https://github.com/reagent-systems/Simple-Agent-Tools)
2. **Add Your Tool**: Follow the same structure as local commands
3. **Test Locally**: Test your tool in your local SimpleAgent instance first
4. **Submit PR**: Create a pull request to the main repository
5. **Community Benefit**: Once merged, your tool becomes available to all users automatically

### 🔄 Tool Loading Priority

When SimpleAgent initializes:
1. **Local tools are loaded first** - giving you full control over your environment
2. **Remote tools are loaded second** - providing the community tool catalog
3. **Local tools override remote tools** - if you have a local tool with the same name as a remote tool, the local version takes precedence

This system allows you to:
- 🧪 **Develop and test** new tools locally
- 🔧 **Customize existing tools** by creating local versions
- 🚀 **Contribute back** to the community repository
- 📦 **Benefit from community tools** automatically

### 📁 Directory Structure for Local Commands

```
commands/
  ├── file_ops/
  │   ├── my_custom_file_tool/
  │   │   └── __init__.py
  │   └── ...
  ├── my_custom_category/
  │   ├── my_tool/
  │   │   └── __init__.py
  │   └── ...
  └── ...
```

## Continuous Integration (CI)

This project uses GitHub Actions for CI. On every push or pull request to `main`, the workflow will:
- Set up Python
- Install dependencies from `requirements.txt`
- Set a dummy `OPENAI_API_KEY`
- Run a basic test of `SimpleAgent.py`

See `.github/workflows/ci.yml` for details.
