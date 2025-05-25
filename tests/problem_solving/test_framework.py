"""
Test Framework for Problem-Solving Implementation

This module provides the framework for testing and comparing the old and new
problem-solving implementations.
"""

import os
import sys
import json
import time
import tempfile
import shutil
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

# Add the SimpleAgent directory to the path so we can import it
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'SimpleAgent'))

try:
    from core.agent import SimpleAgent
except ImportError:
    print("Warning: Could not import SimpleAgent. Make sure the SimpleAgent directory is accessible.")
    SimpleAgent = None

class TaskStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"

@dataclass
class TaskResult:
    task_id: str
    status: TaskStatus
    execution_time: float
    steps_taken: int
    success_criteria_met: List[str]
    success_criteria_failed: List[str]
    error_messages: List[str]
    feedback_loop_iterations: int
    final_state: Dict[str, Any]

class TestCase:
    def __init__(self, 
                 task_id: str,
                 description: str,
                 initial_state: Dict[str, Any],
                 success_criteria: List[Dict[str, Any]],
                 max_steps: int = 10,
                 timeout_seconds: int = 300):
        self.task_id = task_id
        self.description = description
        self.initial_state = initial_state
        self.success_criteria = success_criteria
        self.max_steps = max_steps
        self.timeout_seconds = timeout_seconds

class TestFramework:
    def __init__(self, output_dir: str = "test_results"):
        self.output_dir = output_dir
        self.results: Dict[str, List[TaskResult]] = {}
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def _create_test_instruction(self, test_case: TestCase) -> str:
        """
        Convert a test case into an instruction for the SimpleAgent.
        """
        if test_case.task_id == "file_creation":
            return f"Create a file at '{test_case.initial_state['target_file']}' with the content '{test_case.initial_state['expected_content']}'"
        
        elif test_case.task_id == "file_operations":
            instructions = []
            for file_info in test_case.initial_state['files_to_create']:
                instructions.append(f"Create file '{file_info['path']}' with content '{file_info['content']}'")
            for mod in test_case.initial_state['modifications']:
                instructions.append(f"Modify file '{mod['file']}' to contain '{mod['new_content']}'")
            for file_path in test_case.initial_state['files_to_delete']:
                instructions.append(f"Delete file '{file_path}'")
            return ". Then ".join(instructions)
        
        elif test_case.task_id == "api_interaction":
            return f"Make a GET request to '{test_case.initial_state['api_url']}' and verify the response contains the fields: {', '.join(test_case.initial_state['expected_fields'])}"
        
        elif test_case.task_id == "error_recovery":
            return "Attempt to write a file to a nonexistent directory, read a nonexistent file, and make a request to an invalid URL. Handle all errors gracefully and continue operation."
        
        elif test_case.task_id == "complex_problem":
            return "Process data files by filtering values > 0, sorting by timestamp, and aggregating with sum operation. Output the result in JSON format."
        
        else:
            return test_case.description
    
    def _evaluate_success_criteria(self, test_case: TestCase, final_state: Dict[str, Any]) -> tuple:
        """
        Evaluate the success criteria for a test case.
        
        Returns:
            Tuple of (success_criteria_met, success_criteria_failed)
        """
        success_criteria_met = []
        success_criteria_failed = []
        
        for criterion in test_case.success_criteria:
            try:
                if criterion['check'](final_state):
                    success_criteria_met.append(criterion['name'])
                else:
                    success_criteria_failed.append(criterion['name'])
            except Exception as e:
                success_criteria_failed.append(f"{criterion['name']} (error: {str(e)})")
        
        return success_criteria_met, success_criteria_failed
    
    def _capture_final_state(self, test_case: TestCase, temp_dir: str) -> Dict[str, Any]:
        """
        Capture the final state after test execution for evaluation.
        """
        final_state = {}
        
        if test_case.task_id == "file_creation":
            target_file = os.path.join(temp_dir, test_case.initial_state['target_file'])
            final_state['file_exists'] = os.path.exists(target_file)
            if final_state['file_exists']:
                try:
                    with open(target_file, 'r') as f:
                        final_state['file_content'] = f.read().strip()
                except:
                    final_state['file_content'] = ""
            final_state['expected_content'] = test_case.initial_state['expected_content']
        
        elif test_case.task_id == "file_operations":
            created_files = {}
            file_exists = {}
            for file_info in test_case.initial_state['files_to_create']:
                file_path = os.path.join(temp_dir, file_info['path'])
                created_files[file_info['path']] = os.path.exists(file_path)
            
            for file_path in test_case.initial_state['files_to_delete']:
                full_path = os.path.join(temp_dir, file_path)
                file_exists[file_path] = os.path.exists(full_path)
            
            final_state['created_files'] = created_files
            final_state['file_exists'] = file_exists
            final_state['files_to_delete'] = test_case.initial_state['files_to_delete']
            
            # Check modifications
            modifications_successful = True
            for mod in test_case.initial_state['modifications']:
                file_path = os.path.join(temp_dir, mod['file'])
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read().strip()
                            if content != mod['new_content']:
                                modifications_successful = False
                    except:
                        modifications_successful = False
                else:
                    modifications_successful = False
            final_state['modifications_successful'] = modifications_successful
        
        # For other test cases, we'll add basic state capture
        return final_state
    
    def run_test(self, test_case: TestCase, implementation: str) -> TaskResult:
        """
        Run a single test case with the specified implementation.
        
        Args:
            test_case: The test case to run
            implementation: Either "old" or "new" to specify which implementation to use
            
        Returns:
            TaskResult containing the test results
        """
        start_time = time.time()
        steps_taken = 0
        feedback_loop_iterations = 0
        error_messages = []
        success_criteria_met = []
        success_criteria_failed = []
        final_state = {}
        
        # For now, we only have the "old" implementation
        if implementation == "new":
            # Return placeholder for new implementation
            return TaskResult(
                task_id=test_case.task_id,
                status=TaskStatus.NOT_STARTED,
                execution_time=0.001,
                steps_taken=0,
                success_criteria_met=[],
                success_criteria_failed=[],
                error_messages=["New implementation not yet available"],
                feedback_loop_iterations=0,
                final_state={}
            )
        
        if SimpleAgent is None:
            error_messages.append("SimpleAgent could not be imported")
            return TaskResult(
                task_id=test_case.task_id,
                status=TaskStatus.FAILED,
                execution_time=time.time() - start_time,
                steps_taken=steps_taken,
                success_criteria_met=success_criteria_met,
                success_criteria_failed=success_criteria_failed,
                error_messages=error_messages,
                feedback_loop_iterations=feedback_loop_iterations,
                final_state=final_state
            )
        
        # Create a temporary directory for this test
        temp_dir = tempfile.mkdtemp(prefix=f"test_{test_case.task_id}_")
        
        try:
            # Initialize the agent with the temporary directory
            agent = SimpleAgent(output_dir=temp_dir)
            
            # Create the instruction for this test case
            instruction = self._create_test_instruction(test_case)
            
            print(f"  Running instruction: {instruction}")
            
            # Run the agent
            agent.run(
                user_instruction=instruction,
                max_steps=test_case.max_steps,
                auto_continue=-1  # Auto-continue indefinitely
            )
            
            # Capture the final state
            final_state = self._capture_final_state(test_case, temp_dir)
            
            # Evaluate success criteria
            success_criteria_met, success_criteria_failed = self._evaluate_success_criteria(
                test_case, final_state
            )
            
            # Determine overall status
            if success_criteria_failed:
                status = TaskStatus.FAILED
            elif success_criteria_met:
                status = TaskStatus.COMPLETED
            else:
                status = TaskStatus.FAILED
            
            # For now, we'll estimate steps taken (this would need to be tracked properly)
            steps_taken = test_case.max_steps  # Placeholder
            
            return TaskResult(
                task_id=test_case.task_id,
                status=status,
                execution_time=time.time() - start_time,
                steps_taken=steps_taken,
                success_criteria_met=success_criteria_met,
                success_criteria_failed=success_criteria_failed,
                error_messages=error_messages,
                feedback_loop_iterations=feedback_loop_iterations,
                final_state=final_state
            )
            
        except Exception as e:
            error_messages.append(str(e))
            return TaskResult(
                task_id=test_case.task_id,
                status=TaskStatus.FAILED,
                execution_time=time.time() - start_time,
                steps_taken=steps_taken,
                success_criteria_met=success_criteria_met,
                success_criteria_failed=success_criteria_failed,
                error_messages=error_messages,
                feedback_loop_iterations=feedback_loop_iterations,
                final_state=final_state
            )
        finally:
            # Clean up temporary directory
            try:
                shutil.rmtree(temp_dir)
            except:
                pass  # Ignore cleanup errors
    
    def compare_implementations(self, test_case: TestCase) -> Dict[str, Any]:
        """
        Compare the old and new implementations for a test case.
        
        Args:
            test_case: The test case to compare
            
        Returns:
            Dictionary containing comparison metrics
        """
        old_result = self.run_test(test_case, "old")
        new_result = self.run_test(test_case, "new")
        
        return {
            "test_case_id": test_case.task_id,
            "old_implementation": {
                "status": old_result.status.value,
                "execution_time": old_result.execution_time,
                "steps_taken": old_result.steps_taken,
                "success_criteria_met": len(old_result.success_criteria_met),
                "success_criteria_failed": len(old_result.success_criteria_failed),
                "feedback_loop_iterations": old_result.feedback_loop_iterations,
                "success_criteria_met_list": old_result.success_criteria_met,
                "success_criteria_failed_list": old_result.success_criteria_failed,
                "error_messages": old_result.error_messages
            },
            "new_implementation": {
                "status": new_result.status.value,
                "execution_time": new_result.execution_time,
                "steps_taken": new_result.steps_taken,
                "success_criteria_met": len(new_result.success_criteria_met),
                "success_criteria_failed": len(new_result.success_criteria_failed),
                "feedback_loop_iterations": new_result.feedback_loop_iterations,
                "success_criteria_met_list": new_result.success_criteria_met,
                "success_criteria_failed_list": new_result.success_criteria_failed,
                "error_messages": new_result.error_messages
            },
            "improvement_metrics": {
                "execution_time_improvement": old_result.execution_time - new_result.execution_time,
                "steps_improvement": old_result.steps_taken - new_result.steps_taken,
                "success_criteria_improvement": (
                    len(new_result.success_criteria_met) - 
                    len(old_result.success_criteria_met)
                )
            }
        }
    
    def save_results(self, results: Dict[str, Any], filename: str):
        """
        Save test results to a JSON file.
        
        Args:
            results: The results to save
            filename: The name of the file to save to
        """
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2) 