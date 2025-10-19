#!/usr/bin/env python3
"""Test runner script for minimal browser.

This script provides a convenient way to run tests with various options.
It's compatible with environments that don't have pytest installed globally.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main():
    """Run tests with pytest."""
    parser = argparse.ArgumentParser(
        description="Run tests for minimal browser",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests
  ./run_tests.py
  
  # Run only unit tests
  ./run_tests.py --unit
  
  # Run specific test file
  ./run_tests.py tests/unit/ai/test_schemas.py
  
  # Run with coverage
  ./run_tests.py --coverage
  
  # Run verbose with detailed output
  ./run_tests.py -v
        """,
    )
    
    parser.add_argument(
        "paths",
        nargs="*",
        default=["tests"],
        help="Specific test files or directories (default: tests)",
    )
    parser.add_argument(
        "--unit",
        action="store_true",
        help="Run only unit tests",
    )
    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run only integration tests",
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage report",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output",
    )
    parser.add_argument(
        "-k",
        dest="keyword",
        help="Run tests matching given substring expression",
    )
    parser.add_argument(
        "--no-warnings",
        action="store_true",
        help="Disable warnings",
    )
    
    args = parser.parse_args()
    
    # Check if pytest is available
    try:
        import pytest
    except ImportError:
        print("Error: pytest is not installed.", file=sys.stderr)
        print("Install it with: pip install pytest pytest-cov", file=sys.stderr)
        print("Or use: uv sync --dev", file=sys.stderr)
        return 1
    
    # Build pytest arguments
    pytest_args = []
    
    # Add test paths
    if args.unit:
        pytest_args.append("tests/unit")
    elif args.integration:
        pytest_args.append("tests/integration")
    else:
        pytest_args.extend(args.paths)
    
    # Add verbosity
    if args.verbose:
        pytest_args.append("-vv")
    
    # Add keyword filter
    if args.keyword:
        pytest_args.extend(["-k", args.keyword])
    
    # Add coverage
    if args.coverage:
        pytest_args.extend([
            "--cov=src/minimal_browser",
            "--cov-report=term-missing",
            "--cov-report=html",
        ])
    
    # Disable warnings if requested
    if args.no_warnings:
        pytest_args.append("--disable-warnings")
    
    # Run pytest
    print(f"Running pytest with args: {' '.join(pytest_args)}")
    return pytest.main(pytest_args)


if __name__ == "__main__":
    sys.exit(main())
