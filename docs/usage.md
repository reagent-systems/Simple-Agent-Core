# Usage Guide

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/reagent-systems/Simple-Agent-Core
   cd Simple-Agent-Core/SimpleAgent
   ```
2. Set up a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # or: source venv/bin/activate  # Linux/Mac
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy and edit the `.env` file:
   ```bash
   copy env_example.txt .env  # Windows
   # or: cp env_example.txt .env  # Linux/Mac
   ```

## Running the Agent

```bash
python SimpleAgent.py -a 10 "Create a Python Flask API with time endpoints"
```

## Command-Line Options
- `-a, --auto [N]`: Auto-continue for N steps (default: 10)
- `-m, --max-steps N`: Maximum number of steps (default: 10)
- `--eager-loading`: Load all tools at startup
- `instruction`: The task instruction for the AI agent

## Example Tasks
- Web API creation
- Data analysis
- Web scraping
- File processing
- Research and summarization

See [commands.md](commands.md) for more examples. 