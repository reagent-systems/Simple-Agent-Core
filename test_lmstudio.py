"""
LMStudio Integration Test

This script demonstrates how to use SimpleAgent with LMStudio for local inference.
"""

import os
import sys

# Add SimpleAgent to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'SimpleAgent'))

def test_lmstudio_integration():
    """
    Test LMStudio integration with SimpleAgent.
    """
    # Set environment variables for LMStudio
    os.environ["API_BASE_URL"] = "http://localhost:1234/v1"
    os.environ["LOCAL_MODEL"] = "your-local-model-name"  # Replace with your actual model name
    os.environ["OPENAI_API_KEY"] = "lm-studio"  # LMStudio doesn't require a real API key
    
    try:
        from core.agent import SimpleAgent
        
        print("🚀 Testing LMStudio integration...")
        print(f"API Base URL: {os.environ.get('API_BASE_URL')}")
        print(f"Local Model: {os.environ.get('LOCAL_MODEL')}")
        
        # Initialize agent
        agent = SimpleAgent()
        
        # Test with a simple task
        test_instruction = "Create a file called 'test.txt' with the content 'Hello from LMStudio!'"
        
        print(f"\n📝 Running test instruction: {test_instruction}")
        
        # Run the agent
        agent.run(
            user_instruction=test_instruction,
            max_steps=5,
            auto_continue=3
        )
        
        print("\n✅ LMStudio integration test completed!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running this from the correct directory.")
    except Exception as e:
        print(f"❌ Error during test: {e}")

def print_usage():
    """
    Print usage instructions for LMStudio integration.
    """
    print("""
🔧 LMStudio Integration Usage

To use SimpleAgent with LMStudio:

1. Start LMStudio and load a model
2. Enable the local server (usually on port 1234)
3. Set environment variables:
   
   Windows (PowerShell):
   $env:API_BASE_URL="http://localhost:1234/v1"
   $env:LOCAL_MODEL="your-model-name"
   $env:OPENAI_API_KEY="lm-studio"
   
   Linux/Mac (Bash):
   export API_BASE_URL="http://localhost:1234/v1"
   export LOCAL_MODEL="your-model-name"
   export OPENAI_API_KEY="lm-studio"

4. Run SimpleAgent normally:
   python SimpleAgent.py "your instruction here"

The agent will automatically detect the custom API base URL and use LMStudio instead of OpenAI's API.

📋 Key Benefits:
- Complete privacy (no data sent to external APIs)
- No API costs
- Full control over the model
- Same functionality as OpenAI integration
""")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--usage":
        print_usage()
    else:
        test_lmstudio_integration() 