import subprocess
import sys
import re


def run_agent_and_check():
    # Adjust the command as needed for your environment
    cmd = [
        sys.executable,  # This uses the current Python interpreter
        "SimpleAgent/SimpleAgent.py",
        "-a", "1",
        "Say hello"
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60  # seconds, adjust as needed
        )
    except subprocess.TimeoutExpired:
        print("❌ SimpleAgent timed out!")
        sys.exit(1)

    print("=== STDOUT ===")
    print(result.stdout)
    print("=== STDERR ===")
    print(result.stderr)

    # Look for a success marker in stdout
    success_patterns = [
        r"SimpleAgent execution completed",
        r"Task completed",
        r"🏁 SimpleAgent execution completed"
    ]
    if any(re.search(pat, result.stdout) for pat in success_patterns):
        print("✅ SimpleAgent ran successfully!")
        sys.exit(0)
    else:
        print("❌ SimpleAgent did not complete successfully!")
        sys.exit(1)

if __name__ == "__main__":
    run_agent_and_check() 