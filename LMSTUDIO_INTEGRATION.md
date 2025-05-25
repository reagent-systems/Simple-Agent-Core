# LMStudio Integration

SimpleAgent now supports LMStudio for local inference, allowing you to run the agent completely offline with your own models.

## Overview

The LMStudio integration maintains full compatibility with the OpenAI API while adding the flexibility to point to a local LMStudio server. This means:

- ✅ All existing functionality works unchanged
- ✅ Same function calling and tool usage patterns
- ✅ Complete privacy (no data sent to external APIs)
- ✅ No API costs
- ✅ Full control over the model

## Setup

### 1. Install and Configure LMStudio

1. Download and install [LMStudio](https://lmstudio.ai/)
2. Load a compatible model (models with function calling support work best)
3. Start the local server (usually runs on `http://localhost:1234`)

### 2. Configure Environment Variables

Set the following environment variables to enable LMStudio:

**Windows (PowerShell):**
```powershell
$env:API_BASE_URL="http://localhost:1234/v1"
$env:LOCAL_MODEL="your-model-name"
$env:OPENAI_API_KEY="lm-studio"
```

**Linux/Mac (Bash):**
```bash
export API_BASE_URL="http://localhost:1234/v1"
export LOCAL_MODEL="your-model-name"
export OPENAI_API_KEY="lm-studio"
```

**Or create a `.env` file:**
```env
API_BASE_URL=http://localhost:1234/v1
LOCAL_MODEL=your-model-name
OPENAI_API_KEY=lm-studio
```

### 3. Run SimpleAgent

Once configured, run SimpleAgent normally:

```bash
python SimpleAgent.py "Create a file with today's date"
```

The agent will automatically detect the custom API base URL and use LMStudio instead of OpenAI's API.

## Configuration Options

| Environment Variable | Description | Example |
|---------------------|-------------|---------|
| `API_BASE_URL` | LMStudio server URL | `http://localhost:1234/v1` |
| `LOCAL_MODEL` | Model name to use | `llama-2-7b-chat` |
| `OPENAI_API_KEY` | Can be any value for LMStudio | `lm-studio` |

## Testing

Run the included test to verify your LMStudio integration:

```bash
python test_lmstudio.py
```

For usage instructions:

```bash
python test_lmstudio.py --usage
```

## Model Recommendations

For best results with SimpleAgent, use models that support:

1. **Function Calling**: Essential for tool usage
2. **Instruction Following**: Better task completion
3. **Code Generation**: Improved file operations

Some recommended model families:
- Code Llama
- Llama 2/3 (with function calling fine-tuning)
- Mistral (with function calling support)
- Qwen Coder

## Troubleshooting

### Common Issues

**1. Connection Refused**
- Ensure LMStudio server is running
- Check the port number (default is 1234)
- Verify the API_BASE_URL format

**2. Function Calling Not Working**
- Use a model that supports function calling
- Check LMStudio's function calling settings
- Some models may need specific prompting

**3. Slow Performance**
- Use a smaller model for faster responses
- Adjust LMStudio's performance settings
- Consider using GPU acceleration

### Debug Mode

Enable debug mode to see detailed API interactions:

```bash
export DEBUG_MODE=true
python SimpleAgent.py "your instruction"
```

## Implementation Details

The integration works by:

1. **Config Detection**: Checking for `API_BASE_URL` environment variable
2. **Client Initialization**: Creating OpenAI client with custom base URL
3. **Model Selection**: Using `LOCAL_MODEL` if specified
4. **Transparent Operation**: All existing code works without changes

### Code Changes

The integration required minimal changes:

1. **Config Module** (`core/config.py`): Added LMStudio configuration options
2. **Execution Manager** (`core/execution.py`): Modified OpenAI client initialization
3. **Summarizer** (`core/summarizer.py`): Added LMStudio support for summaries

## Benefits

### Privacy
- All processing happens locally
- No data sent to external APIs
- Complete control over your data

### Cost
- No API usage fees
- One-time model download
- Unlimited usage

### Customization
- Use any compatible model
- Adjust model parameters
- Fine-tune for specific tasks

### Reliability
- No internet dependency
- No rate limits
- Consistent availability

## Limitations

- Requires local computational resources
- Model quality depends on your hardware
- Some models may not support all features
- Initial setup is more complex than cloud APIs

## Future Enhancements

Planned improvements:
- Automatic model detection
- Performance optimization suggestions
- Model-specific configuration profiles
- Enhanced error handling for local models 