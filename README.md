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

SimpleAgent can be configured through environment variables in the `.env` file:

```
# OpenAI API key
OPENAI_API_KEY=your_openai_api_key_here

# Model settings
DEFAULT_MODEL=gpt-4-turbo
SUMMARIZER_MODEL=gpt-3.5-turbo

# Memory settings
MEMORY_FILE=memory.json

# Application settings
MAX_STEPS=10
DEBUG_MODE=False
```

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

To add a new command:

1. Create a new folder in the appropriate category directory (or create a new category)
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

## Continuous Integration (CI)

This project uses GitHub Actions for CI. On every push or pull request to `main`, the workflow will:
- Set up Python
- Install dependencies from `requirements.txt`
- Set a dummy `OPENAI_API_KEY`
- Run a basic test of `SimpleAgent.py`

See `.github/workflows/ci.yml` for details.
