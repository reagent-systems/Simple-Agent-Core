# core/agent/

## Overview
The `agent/` submodule contains the main agent interface and the run loop manager.

### Files
- **agent.py**: Defines the `SimpleAgent` class, the main entry point for using the agent. It coordinates conversation, execution, memory, and security.
- **run_manager.py**: Implements the `RunManager` class, which manages the main execution loop, orchestrating conversation, tool use, memory, and metacognition.

### Key Classes
- **SimpleAgent**: High-level interface for running the agent, managing state, and exposing core functionality.
- **RunManager**: Handles the step-by-step execution of tasks, including metacognitive analysis, loop detection, and summarization.

### Responsibilities
- Orchestrate the agent's workflow
- Manage conversation and memory
- Coordinate tool execution and metacognitive reasoning
- Provide a secure, extensible interface for automation tasks 

## How the Agent Works (Step by Step)

1. **User Input**
   - The user runs `python SimpleAgent.py "Do something"`.
   - The agent receives the instruction.
2. **Initialization**
   - Loads configuration and environment variables.
   - Sets up memory, conversation, and tool management.
3. **Task Analysis (Metacognition)**
   - The agent analyzes the instruction to determine the main goal and success criteria.
4. **Main Run Loop**
   - For each step:
     - Updates the system prompt with the current objective and context.
     - Asks the model what to do next.
     - Executes any tool calls securely.
     - Updates memory and conversation history.
     - Reflects on progress and checks for loops.
     - Decides whether to continue or stop.
5. **Finalization**
   - Summarizes changes and progress.
   - Saves the final state to memory.
   - Prints a summary and exits.

### Example: Creating a Flask API

```bash
python SimpleAgent.py -a 10 "Create a Python Flask API with time endpoints"
```
- The agent analyzes the instruction, plans the steps, and uses tools to write code files.
- It checks its own progress after each step, ensuring it's on track.
- If it gets stuck, it detects the loop and tries a new approach or stops.

### Diagram

```
User Input
   |
   v
SimpleAgent (agent.py)
   |
   v
RunManager (run_manager.py)
   |
   v
[Conversation | Execution | Memory | Metacognition]
   |
   v
Tools/Commands
```

### In Plain English
- The agent is like a smart assistant that plans, acts, checks its own work, and learns from each step.
- It keeps everything secure and organized, and always knows when to stop or try something new. 