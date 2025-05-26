"""
SimpleAgent - A minimalist AI agent framework

This script implements a simple AI agent that can perform basic operations
through function calling. It uses the OpenAI API to generate responses and
execute functions based on user instructions.
"""

import os
import sys
import json
import time
import argparse
import logging
import uuid
from typing import List, Dict, Any, Optional, Callable

# Set up basic logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Import commands package
import commands
from commands import REGISTERED_COMMANDS, COMMAND_SCHEMAS

# Import core modules
from core.agent import SimpleAgent
from core.config import OPENAI_API_KEY, GEMINI_API_KEY, AI_PROVIDER, LMSTUDIO_BASE_URL, MAX_STEPS
from core.version import AGENT_VERSION

# Initialize commands
commands.init()

# Check for appropriate API key based on provider
provider = AI_PROVIDER.lower()
if provider == "openai" and not OPENAI_API_KEY:
    logging.error("Error: OPENAI_API_KEY environment variable not set for OpenAI provider.")
    logging.info("Please set it in a .env file or in your environment variables.")
    sys.exit(1)
elif provider == "gemini" and not GEMINI_API_KEY:
    logging.error("Error: GEMINI_API_KEY environment variable not set for Gemini provider.")
    logging.info("Please set it in a .env file or in your environment variables.")
    sys.exit(1)
elif provider == "lmstudio":
    # LMStudio doesn't require an API key, just log which provider is being used
    logging.info(f"Using LMStudio provider at base URL: {LMSTUDIO_BASE_URL}")
elif provider not in ["openai", "gemini", "lmstudio"]:
    logging.error(f"Error: Unsupported AI provider '{provider}'. Supported providers: openai, gemini, lmstudio")
    sys.exit(1)
else:
    logging.info(f"Using {provider} provider")


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='SimpleAgent - An AI agent that can perform tasks')
    # Add flags first to prevent instruction from being consumed as a flag value
    parser.add_argument('-a', '--auto', type=int, nargs='?', const=10, default=0,
                      help='Auto-continue for N steps (default: 10 if no number provided)')
    parser.add_argument('-m', '--max-steps', type=int, default=10,
                      help='Maximum number of steps to run (default: 10)')
    parser.add_argument('instruction', nargs='+', help='The instruction for the AI agent')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Join the instruction parts back together
    instruction = ' '.join(args.instruction)
    
    # Ensure max_steps is at least as large as auto_continue
    max_steps = max(args.max_steps, args.auto) if args.auto > 0 else args.max_steps

    # Create a unique output directory for this run
    base_output_dir = os.path.abspath('output')
    if not os.path.exists(base_output_dir):
        os.makedirs(base_output_dir)
    run_id = str(uuid.uuid4())[:8]
    version_folder = 'v' + '_'.join(AGENT_VERSION.lstrip('v').split('.'))
    run_output_dir = os.path.join(base_output_dir, f"{version_folder}_{run_id}")
    os.makedirs(run_output_dir, exist_ok=True)

    # Initialize and run the agent with the unique output directory
    agent = SimpleAgent(output_dir=run_output_dir)
    agent.run(instruction, max_steps=max_steps, auto_continue=args.auto)


if __name__ == "__main__":
    main() 