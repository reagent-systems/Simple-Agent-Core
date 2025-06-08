# core/metacognition/

## Overview
The `metacognition/` submodule provides self-reflection, loop detection, and prompt management for the agent.

### Files
- **metacognition.py**: Contains the `MetaCognition` class for internal monologue, task analysis, and intelligent stopping decisions.
- **loop_detector.py**: Implements the `LoopDetector` class for detecting and breaking repetitive loops in agent behavior.
- **prompts.py**: Centralizes all prompt templates and formatting logic for system, metacognitive, and loop-breaking messages.

### Key Classes
- **MetaCognition**: Analyzes tasks, reflects on actions, and decides when to continue or stop.
- **LoopDetector**: Detects exact and semantic repetition, confusion, and no-action loops.

### Responsibilities
- Enable the agent to reflect on its own progress
- Detect and break out of unproductive loops
- Centralize and manage all prompt templates 

## How Metacognition Works

1. **Task Analysis**: The agent thinks about what the user really wants and what success looks like.
2. **Action Reflection**: After each step, the agent reflects on what it just did and how much progress it made.
3. **Loop Detection**: The agent checks if it's repeating itself or getting stuck.
4. **Stopping Decision**: The agent decides if it should keep going or stop, based on progress and confidence.

### Example: Avoiding a Loop
- The agent notices it's giving the same answer multiple times.
- It triggers a loop-breaking prompt and tries a new approach or stops.

### In Plain English
- This part of the agent is like an inner voice: it thinks about the task, checks its own work, and knows when to stop or try something different. 