# SimpleAgent Benchmark Tests

This directory contains benchmark tests for all SimpleAgent commands to ensure they work correctly. The tests are designed to be run periodically to verify that all functionality is working as expected.

## Running Benchmark Tests

There are several ways to run the benchmark tests:

### 1. Using SimpleAgent.py

The simplest way is to use the `--benchmark` flag with SimpleAgent.py:

```bash
python SimpleAgent.py --benchmark
```

This will run all tests and generate a status.md file with the results.

### 2. Using the Benchmark Runner

You can also use the dedicated benchmark runner script:

```bash
./benchmark/run_all.py
```

### 3. Using Individual Test Modules

You can run individual test modules using Python:

```bash
python -m benchmark.test_file_ops
python -m benchmark.test_web_ops
python -m benchmark.test_data_ops
python -m benchmark.test_github_ops
python -m benchmark.test_agent
```

## Viewing Test Results

After running the tests, you can view the results in the generated status.md file. This file contains a summary of all tests and their status.

You can also display a summary of the results using the `--status` flag:

```bash
python SimpleAgent.py --status
```

## Adding New Tests

To add tests for a new command, create a test function in the appropriate test module. The test function should:

1. Be named `test_commandname`
2. Return a tuple of (success, message)
3. Handle exceptions gracefully

Example:

```python
def test_new_command() -> Tuple[bool, str]:
    """Test the new_command command."""
    try:
        # Test code here
        result = new_command(param1, param2)
        
        # Verify the result
        if not result:
            return False, "Command failed"
            
        return True, "Command successful"
    except Exception as e:
        return False, f"Exception: {str(e)}"
```

## Test Environment

Tests run in a dedicated test environment with:

- A clean test directory (`TEST_OUTPUT_DIR`)
- Mocked network calls to avoid actual web requests
- Mocked GitHub API calls to avoid actual GitHub operations

This ensures tests can run without external dependencies or side effects.

## Failed Tests

If a test fails, it will be marked as "Failed" in the status.md file. You can fix the issue and run the tests again to update the status. 