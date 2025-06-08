# core/conversation/

## Overview
The `conversation/` submodule manages conversation history and persistent memory.

### Files
- **conversation.py**: Contains the `ConversationManager` class for managing the conversation history and message flow.
- **memory.py**: Implements the `MemoryManager` class for saving, loading, and updating persistent memory (conversations, files created/modified).

### Key Classes
- **ConversationManager**: Handles the conversation history, message addition, and system message updates.
- **MemoryManager**: Manages persistent memory, including conversations and file tracking.

---

## How Conversation & Memory Work

1. **Every message** (user, agent, tool) is added to the conversation history.
2. **System messages** are updated to keep the agent on track.
3. **MemoryManager** saves conversations and file changes to disk.
4. **On startup**, memory is loaded so the agent can pick up where it left off.

---

### Example: Remembering a File
- The agent creates a file. The path is added to memory.
- On the next run, the agent can see what files it created or modified before.

---

### In Plain English
- This part of the agent is like a notebook: it remembers every conversation and every file it touches, so it never loses track of what it's done.

### Responsibilities
- Track and manage all agent conversations
- Persist memory across runs
- Support context-aware and stateful agent behavior 