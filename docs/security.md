# Security Model

## Overview
Simple Agent is designed with security in mind. All file operations are sandboxed and validated to prevent unauthorized access or modification outside the designated workspace.

## Key Features
- **Sandboxed Operations**: All file and directory operations are restricted to the configured `OUTPUT_DIR`.
- **Path Validation**: The `get_secure_path` utility ensures that all file paths are normalized and checked to prevent directory traversal attacks.
- **Session Isolation**: Each run can use a unique workspace directory for isolation.
- **Tool Security**: Tools are loaded in a controlled environment, and their file operations are also sandboxed.

## How It Works
1. All file paths are converted to be within the output directory.
2. Any attempt to access files outside the sandbox is blocked.
3. Directory traversal patterns (e.g., `../`) are sanitized.
4. Only files and directories within the allowed workspace can be read, written, or deleted.

## Example
```python
from core.utils.security import get_secure_path

safe_path = get_secure_path("../../etc/passwd")
# Result: 'output/passwd' (blocked from escaping output dir)
``` 