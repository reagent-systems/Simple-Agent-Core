# Commands System

## Overview
Simple Agent supports a dynamic, extensible command system. Tools (commands) can be loaded from both local and remote sources, and are used to perform actions such as file operations, web requests, data analysis, and more.

## How Commands Work (Step by Step)

1. **Discovery**: On startup, the agent scans the local `commands/` directory and fetches the remote tool catalog.
2. **On-Demand Loading**: When the agent needs a tool, it loads it from local or remote sources as needed.
3. **Schema Validation**: Each tool defines a schema for its parameters, ensuring correct usage.
4. **Execution**: The tool is called with the required arguments, and the result is returned to the agent.
5. **Tracking**: All tool usage is tracked for memory and summarization.

---

### Example: Using a Tool
- The agent needs to write a file, so it loads the `write_file` tool.
- The tool is executed with the file path and content.
- The result is logged and added to memory.

---

### In Plain English
- The commands system is like a toolbox: the agent grabs the right tool for the job, uses it safely, and always keeps track of what it did.

## Adding Your Own Command
1. Create a new directory under `commands/` for your category (if needed).
2. Add a subdirectory for your tool, with an `__init__.py` file.
3. Register your command using the `register_command` function from the tool manager.
4. Define a schema for your command's parameters.
5. (Optional) Contribute your tool to the main tools repo!

## Example Command Structure
```
commands/
  file_ops/
    write_file/
      __init__.py
```

## Example Command Registration
```python
from core.execution.tool_manager import register_command

def write_file(file_path: str, content: str):
    with open(file_path, 'w') as f:
        f.write(content)
    return f"Wrote to {file_path}"

WRITE_FILE_SCHEMA = {
    "function": {
        "name": "write_file",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["file_path", "content"]
        }
    }
}

register_command("write_file", write_file, WRITE_FILE_SCHEMA)
``` 