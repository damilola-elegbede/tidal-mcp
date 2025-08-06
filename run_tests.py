#!/usr/bin/env python3
"""
Test runner script for Tidal MCP Server.

Provides convenient commands to run different types of tests with appropriate
configurations and reporting.
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, cwd=None):
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=False)
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Run Tidal MCP tests")
    parser.add_argument(
        "--type",
        choices=["unit", "integration", "all", "auth", "service", "coverage"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--parallel", "-p",
        action="store_true",
        help="Run tests in parallel"
    )
    parser.add_argument(
        "--coverage", "-c",
        action="store_true", 
        help="Generate coverage report"
    )
    parser.add_argument(
        "--file",
        help="Run specific test file"
    )
    
    args = parser.parse_args()
    
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add verbosity
    if args.verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    # Add parallel execution
    if args.parallel:
        cmd.extend(["-n", "auto"])
    
    # Add coverage if requested
    if args.coverage or args.type == "coverage":
        cmd.extend([
            "--cov=src/tidal_mcp",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing"
        ])
    
    # Select test type
    if args.file:
        cmd.append(f"tests/{args.file}")
    elif args.type == "unit":
        cmd.extend(["-m", "not integration"])
    elif args.type == "integration":
        cmd.extend(["-m", "integration"])
    elif args.type == "auth":
        cmd.append("tests/test_auth.py")
    elif args.type == "service":
        cmd.append("tests/test_service.py")
    elif args.type == "coverage":
        cmd.extend([
            "--cov=src/tidal_mcp",
            "--cov-report=html:htmlcov", 
            "--cov-report=term-missing",
            "--cov-fail-under=80"
        ])
    else:  # all
        cmd.append("tests/")
    
    # Run the tests
    success = run_command(cmd)
    
    if not success:
        print("\n❌ Tests failed!")
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")
        
        if args.coverage or args.type == "coverage":
            print("\n📊 Coverage report generated in htmlcov/index.html")


if __name__ == "__main__":
    main()