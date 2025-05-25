"""
Problem Solving Test Package

This package contains the test framework and test cases for comparing
the old and new problem-solving implementations.
"""

from .test_framework import TestFramework, TestCase, TaskResult, TaskStatus
from .test_cases import TEST_CASES
from .run_tests import run_comparison_tests

__all__ = [
    'TestFramework',
    'TestCase',
    'TaskResult',
    'TaskStatus',
    'TEST_CASES',
    'run_comparison_tests'
] 