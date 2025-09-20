#!/usr/bin/env python3
"""
Test runner script for Tidal MCP Server unit tests.

Provides convenient test execution with coverage reporting and
performance timing. Supports different test categories and
provides detailed output for CI/CD integration.
"""

import subprocess
import sys
import time
from pathlib import Path


def run_command(cmd, description=""):
    """Run a command and capture its output."""
    print(f"\n{'='*60}")
    if description:
        print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")

    start_time = time.time()
    try:
        subprocess.run(
            cmd,
            cwd=Path(__file__).parent,
            capture_output=False,
            text=True,
            check=True
        )
        end_time = time.time()
        print(f"\n✅ {description or 'Command'} completed successfully in {end_time - start_time:.2f}s")
        return True
    except subprocess.CalledProcessError as e:
        end_time = time.time()
        print(f"\n❌ {description or 'Command'} failed in {end_time - start_time:.2f}s")
        print(f"Return code: {e.returncode}")
        return False


def main():
    """Run comprehensive test suite."""
    print("🧪 Tidal MCP Server - Comprehensive Unit Test Suite")
    print("=" * 60)

    # Check if we're in a virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Warning: Not running in a virtual environment")
        print("   Consider activating your virtual environment first")

    # Test categories to run
    test_categories = [
        {
            "name": "Auth Module Tests (High Priority)",
            "cmd": ["python", "-m", "pytest", "tests/test_auth.py", "-v", "--tb=short"],
            "description": "OAuth flow, token management, session persistence"
        },
        {
            "name": "Service Module Tests (Critical Priority)",
            "cmd": ["python", "-m", "pytest", "tests/test_service.py", "-v", "--tb=short"],
            "description": "Search, playlist, favorites functionality"
        },
        {
            "name": "Models Module Tests (Medium Priority)",
            "cmd": ["python", "-m", "pytest", "tests/test_models.py", "-v", "--tb=short"],
            "description": "Data validation, serialization, API response parsing"
        },
        {
            "name": "Utils Module Tests (Medium Priority)",
            "cmd": ["python", "-m", "pytest", "tests/test_utils.py", "-v", "--tb=short"],
            "description": "Input validation, sanitization, format conversion"
        }
    ]

    # Run individual test categories
    results = {}
    total_start_time = time.time()

    for category in test_categories:
        print(f"\n🔍 {category['name']}")
        print(f"   {category['description']}")
        success = run_command(category["cmd"], category["name"])
        results[category["name"]] = success

    # Run comprehensive coverage report
    print("\n📊 Running comprehensive test suite with coverage...")
    coverage_cmd = [
        "python", "-m", "pytest",
        "tests/",
        "--cov=src/tidal_mcp",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--cov-report=xml:coverage.xml",
        "--cov-fail-under=85",
        "--tb=short",
        "-v"
    ]

    coverage_success = run_command(coverage_cmd, "Comprehensive Coverage Report")
    results["Coverage Report"] = coverage_success

    # Performance benchmark - run all tests and measure timing
    print("\n⏱️  Running performance benchmark...")
    perf_cmd = [
        "python", "-m", "pytest",
        "tests/",
        "--durations=10",
        "-q"
    ]

    perf_success = run_command(perf_cmd, "Performance Benchmark")
    results["Performance Benchmark"] = perf_success

    # Summary
    total_end_time = time.time()
    total_time = total_end_time - total_start_time

    print(f"\n{'='*60}")
    print("📋 TEST SUITE SUMMARY")
    print(f"{'='*60}")
    print(f"Total execution time: {total_time:.2f} seconds")
    print(f"Target: < 10 seconds (Current: {'✅ PASS' if total_time < 10 else '❌ FAIL'})")

    success_count = sum(1 for success in results.values() if success)
    total_count = len(results)

    print(f"\nResults: {success_count}/{total_count} test categories passed")

    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} {test_name}")

    if all(results.values()):
        print("\n🎉 All tests passed! Unit test suite is comprehensive and fast.")
        print("\n📁 Coverage reports generated:")
        print("   - HTML: htmlcov/index.html")
        print("   - XML: coverage.xml")
        print("   - Terminal output above")
        return 0
    else:
        print("\n💥 Some tests failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
