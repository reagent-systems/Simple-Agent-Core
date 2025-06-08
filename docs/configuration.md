# Configuration

Simple Agent is configured via environment variables in the `.env` file.

## Main Options
- `API_PROVIDER`: `openai`, `lmstudio`, or `gemini`
- `OPENAI_API_KEY`: Your OpenAI API key
- `GEMINI_API_KEY`: Your Google Gemini API key
- `API_BASE_URL`: LM-Studio endpoint (if using LM-Studio)
- `GITHUB_TOKEN`: GitHub token for tool loading (optional)
- `DEFAULT_MODEL`: Main model for agent operations
- `SUMMARIZER_MODEL`: Model for summarization
- `METACOGNITION_MODEL`: Model for metacognitive reflection
- `MAX_STEPS`: Maximum steps per run
- `DEBUG_MODE`: Enable debug logging
- `OUTPUT_DIR`: Directory for file operations
- `MEMORY_FILE`: File for persistent memory

## Example: OpenAI
```env
API_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key_here
GITHUB_TOKEN=your_github_token_here
DEFAULT_MODEL=gpt-4o
SUMMARIZER_MODEL=gpt-3.5-turbo
MAX_STEPS=10
DEBUG_MODE=False
OUTPUT_DIR=output
```

## Example: LM-Studio
```env
API_PROVIDER=lmstudio
API_BASE_URL=http://localhost:1234/v1
DEFAULT_MODEL=deepseek-r1-distill-llama-8b
SUMMARIZER_MODEL=deepseek-r1-distill-llama-8b
MAX_STEPS=10
DEBUG_MODE=False
```

## Example: Gemini
```env
API_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
DEFAULT_MODEL=gemini-2.0-flash
SUMMARIZER_MODEL=gemini-2.0-flash
MAX_STEPS=10
DEBUG_MODE=False
``` 