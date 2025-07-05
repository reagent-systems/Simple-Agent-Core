# SimpleAgent Input Directory

This directory is where you can place files that you want the SimpleAgent to access and work with.

## How to Use

1. **Place your files** in this `input/` directory
2. **Run SimpleAgent** with instructions like:
   - "Hey, access sample.txt"
   - "List all input files"
   - "Read config.json and tell me about the project"
   - "Search for 'security' in sample.txt"

## Supported File Types

The system supports the following file extensions:
- **Text files**: `.txt`, `.md`
- **Data files**: `.json`, `.csv`, `.yaml`, `.yml`
- **Code files**: `.py`, `.js`, `.html`, `.css`, `.xml`

## Security Features

- **Directory restriction**: Files can only be accessed from this input directory
- **Size limits**: Files are limited to 10MB by default
- **Extension validation**: Only allowed file types can be accessed
- **Read-only access**: Input files cannot be modified by the agent
- **Path traversal protection**: Prevents access to files outside this directory

## Available Operations

When asking the agent to access files, you can use these operations:

- **`read`** - Read the full content of a file
- **`info`** - Get detailed information about a file
- **`list`** - List all available input files
- **`search`** - Search for text within a file
- **`json`** - Parse and display JSON files
- **`csv`** - Read and display CSV files
- **`summary`** - Get a summary of all input files

## Example Commands

```
"Access sample.txt"
"List input files"
"Get info about config.json"
"Search for 'features' in sample.txt"
"Read config.json as JSON"
```

## Configuration

You can customize the input system through environment variables:

- `INPUT_DIR` - Change the input directory path (default: "input")
- `MAX_INPUT_FILE_SIZE` - Set maximum file size in bytes (default: 10MB)
- `ALLOWED_INPUT_EXTENSIONS` - Comma-separated list of allowed extensions

## Sample Files

This directory includes some sample files to demonstrate the system:

- `sample.txt` - A basic text file with information about the input system
- `config.json` - A JSON configuration file showing project details
- `README.md` - This documentation file

Feel free to replace these with your own files!
