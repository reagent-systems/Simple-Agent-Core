# core/utils/

## Overview
The `utils/` submodule provides utility functions and configuration for the agent.

### Files
- **security.py**: Contains secure path handling and validation logic to prevent directory traversal and enforce sandboxing.
- **config.py**: Loads and manages all configuration and environment variables for the agent.
- **version.py**: Tracks the current version and changelog notes for the project.

### Key Functions/Classes
- **get_secure_path**: Ensures all file operations are restricted to the output directory.
- **create_client**: Instantiates the correct API client based on configuration.

---

## How Utils Work

1. **Security**: Every file path is checked and sanitized before use.
2. **Configuration**: All settings are loaded from `.env` and made available to the agent.
3. **Versioning**: The current version is tracked for debugging and changelogs.

---

### Example: Securing a File Path
```python
from core.utils.security import get_secure_path
safe_path = get_secure_path("../../etc/passwd")
# Result: 'output/passwd' (blocked from escaping output dir)
```

---

### In Plain English
- This part of the agent is like a safety net and a settings panel: it keeps everything secure and makes sure the agent always knows its configuration and version. 