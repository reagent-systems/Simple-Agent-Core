# Architecture Overview

```
+-------------------+
|   SimpleAgent.py  |
+-------------------+
          |
          v
+-------------------+
|      core/        |
+-------------------+
| agent/            |
| execution/        |
| conversation/     |
| metacognition/    |
| utils/            |
+-------------------+
          |
          v
+-------------------+
|   commands/       |
+-------------------+
```

## Main Components
- **SimpleAgent.py**: Entry point and CLI interface.
- **core/**: Main framework logic, split into submodules:
  - **agent/**: Main agent class and run loop manager.
  - **execution/**: Command execution, tool management, summarization.
  - **conversation/**: Conversation and memory management.
  - **metacognition/**: Self-reflection, loop detection, prompt templates.
  - **utils/**: Security, configuration, versioning.
- **commands/**: Pluggable tools and commands, loaded dynamically.

## How It Works
1. User provides an instruction via CLI.
2. The agent orchestrates conversation, tool use, and memory.
3. Tools are loaded on demand from local or remote sources.
4. All file operations are sandboxed and secure.
5. The agent uses metacognition to reflect, summarize, and avoid loops. 