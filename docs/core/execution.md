# core/execution/

## Overview
The `execution/` submodule handles command execution, tool management, and summarization.

### Files
- **execution.py**: Contains the `ExecutionManager` class, which manages command execution, step management, and file operation security.
- **tool_manager.py**: Implements the `ToolManager` class and related functions for dynamic tool discovery, loading, and registration.
- **summarizer.py**: Provides the `ChangeSummarizer` class for summarizing changes made by the agent.

### Key Classes
- **ExecutionManager**: Executes commands, manages tool calls, and enforces file operation security.
- **ToolManager**: Discovers, loads, and registers tools from local and remote sources.
- **ChangeSummarizer**: Summarizes changes for step-by-step and overall reporting.

### Responsibilities
- Execute agent actions and tool calls
- Manage dynamic tool/plugin loading
- Summarize changes and progress
- Enforce security for all file operations 

## How Execution Works

1. **Receives an action** from the agent (e.g., "write a file").
2. **Validates and secures** all file paths and arguments.
3. **Loads the required tool** (from local or remote) if not already loaded.
4. **Executes the tool function** with the given arguments.
5. **Tracks changes** for summarization and memory.
6. **Returns results** to the agent for further processing.

### Example: Writing a File

- The agent decides to call the `write_file` tool.
- `ExecutionManager` ensures the file path is safe, loads the tool, and runs it.
- The result (e.g., "Wrote to output/app.py") is tracked and summarized.

### In Plain English
- This part of the agent is like a secure, smart robot arm: it only does safe actions, loads the right tool for the job, and keeps a log of everything it changes. 