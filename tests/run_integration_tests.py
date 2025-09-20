#!/usr/bin/env python3
"""
Integration Test Runner for Tidal MCP Server

Provides convenient scripts for running different types of integration tests
with proper environment setup and reporting.
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path


def run_command(cmd: list, description: str) -> bool:
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")

    start_time = time.time()
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        end_time = time.time()
        print(f"\n✅ {description} completed successfully in {end_time - start_time:.2f}s")
        return True
    except subprocess.CalledProcessError as e:
        end_time = time.time()
        print(f"\n❌ {description} failed after {end_time - start_time:.2f}s")
        print(f"Exit code: {e.returncode}")
        return False


def run_basic_integration_tests():
    """Run basic integration tests for core MCP tools."""
    cmd = [
        "python", "-m", "pytest",
        "tests/integration/test_mcp_tools_core.py",
        "-v",
        "--tb=short",
        "-m", "integration and not slow and not redis",
        "--durations=10"
    ]
    return run_command(cmd, "Basic Integration Tests")


def run_production_integration_tests():
    """Run integration tests for production/enhanced tools."""
    cmd = [
        "python", "-m", "pytest",
        "tests/integration/test_mcp_tools_production.py",
        "-v",
        "--tb=short",
        "-m", "integration and not slow",
        "--durations=10"
    ]
    return run_command(cmd, "Production Tools Integration Tests")


def run_e2e_tests():
    """Run end-to-end flow tests."""
    cmd = [
        "python", "-m", "pytest",
        "tests/integration/test_e2e_flows.py",
        "-v",
        "--tb=short",
        "-m", "e2e and not slow",
        "--durations=10"
    ]
    return run_command(cmd, "End-to-End Flow Tests")


def run_protocol_compliance_tests():
    """Run MCP protocol compliance tests."""
    cmd = [
        "python", "-m", "pytest",
        "tests/integration/test_mcp_protocol.py",
        "-v",
        "--tb=short",
        "-m", "integration",
        "--durations=10"
    ]
    return run_command(cmd, "MCP Protocol Compliance Tests")


def run_performance_tests():
    """Run performance and load tests."""
    cmd = [
        "python", "-m", "pytest",
        "tests/integration/test_performance.py",
        "-v",
        "--tb=short",
        "-m", "slow",
        "--durations=20",
        "--timeout=600"  # 10 minute timeout for performance tests
    ]
    return run_command(cmd, "Performance and Load Tests")


def run_redis_tests():
    """Run tests that require Redis."""
    cmd = [
        "python", "-m", "pytest",
        "tests/integration/",
        "-v",
        "--tb=short",
        "-m", "redis",
        "--durations=10"
    ]
    return run_command(cmd, "Redis Integration Tests")


def run_full_integration_suite():
    """Run the complete integration test suite."""
    cmd = [
        "python", "-m", "pytest",
        "tests/integration/",
        "-v",
        "--tb=short",
        "-m", "integration",
        "--durations=20",
        "--cov=src/tidal_mcp",
        "--cov-report=html:htmlcov/integration",
        "--cov-report=term-missing"
    ]
    return run_command(cmd, "Full Integration Test Suite")


def run_all_tests_with_coverage():
    """Run all tests including performance with coverage."""
    cmd = [
        "python", "-m", "pytest",
        "tests/integration/",
        "-v",
        "--tb=short",
        "--durations=30",
        "--cov=src/tidal_mcp",
        "--cov-report=html:htmlcov/all_integration",
        "--cov-report=term-missing",
        "--cov-report=xml:coverage_integration.xml",
        "--timeout=900"  # 15 minute timeout
    ]
    return run_command(cmd, "Complete Integration Test Suite with Coverage")


def run_quick_smoke_tests():
    """Run quick smoke tests to verify basic functionality."""
    cmd = [
        "python", "-m", "pytest",
        "tests/integration/test_mcp_tools_core.py::TestAuthenticationTools::test_tidal_login_success",
        "tests/integration/test_mcp_tools_core.py::TestSearchTools::test_tidal_search_tracks",
        "tests/integration/test_mcp_tools_core.py::TestPlaylistTools::test_tidal_create_playlist_success",
        "tests/integration/test_mcp_protocol.py::TestMCPToolRegistration::test_all_tools_registered",
        "-v",
        "--tb=short"
    ]
    return run_command(cmd, "Quick Smoke Tests")


def run_authentication_tests():
    """Run authentication-focused tests."""
    cmd = [
        "python", "-m", "pytest",
        "tests/integration/",
        "-v",
        "--tb=short",
        "-m", "auth",
        "--durations=10"
    ]
    return run_command(cmd, "Authentication Tests")


def run_search_tests():
    """Run search-focused tests."""
    cmd = [
        "python", "-m", "pytest",
        "tests/integration/",
        "-v",
        "--tb=short",
        "-m", "search",
        "--durations=10"
    ]
    return run_command(cmd, "Search Tests")


def run_playlist_tests():
    """Run playlist management tests."""
    cmd = [
        "python", "-m", "pytest",
        "tests/integration/",
        "-v",
        "--tb=short",
        "-m", "playlist",
        "--durations=10"
    ]
    return run_command(cmd, "Playlist Management Tests")


def run_favorites_tests():
    """Run favorites management tests."""
    cmd = [
        "python", "-m", "pytest",
        "tests/integration/",
        "-v",
        "--tb=short",
        "-m", "favorites",
        "--durations=10"
    ]
    return run_command(cmd, "Favorites Management Tests")


def check_environment():
    """Check if the test environment is properly set up."""
    print("Checking test environment...")

    # Check if pytest is available
    try:
        subprocess.run(["python", "-m", "pytest", "--version"],
                      check=True, capture_output=True)
        print("✅ pytest is available")
    except subprocess.CalledProcessError:
        print("❌ pytest is not available")
        return False

    # Check if the source code is available
    src_path = Path("src/tidal_mcp")
    if src_path.exists():
        print("✅ Source code found")
    else:
        print("❌ Source code not found")
        return False

    # Check if test files exist
    test_path = Path("tests/integration")
    if test_path.exists():
        print("✅ Integration test files found")
    else:
        print("❌ Integration test files not found")
        return False

    print("✅ Environment check passed")
    return True


def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(
        description="Integration Test Runner for Tidal MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available test suites:
  basic       - Core MCP tools integration tests (fast)
  production  - Production/enhanced tools tests
  e2e         - End-to-end workflow tests
  protocol    - MCP protocol compliance tests
  performance - Performance and load tests (slow)
  redis       - Tests requiring Redis connection
  full        - Complete integration suite
  all         - All tests with coverage
  smoke       - Quick smoke tests
  auth        - Authentication-focused tests
  search      - Search functionality tests
  playlist    - Playlist management tests
  favorites   - Favorites management tests

Examples:
  python tests/run_integration_tests.py basic
  python tests/run_integration_tests.py e2e --verbose
  python tests/run_integration_tests.py all --check-env
        """
    )

    parser.add_argument(
        "suite",
        choices=[
            "basic", "production", "e2e", "protocol", "performance",
            "redis", "full", "all", "smoke", "auth", "search",
            "playlist", "favorites"
        ],
        help="Test suite to run"
    )

    parser.add_argument(
        "--check-env",
        action="store_true",
        help="Check environment before running tests"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    args = parser.parse_args()

    if args.check_env:
        if not check_environment():
            print("\n❌ Environment check failed. Please fix the issues and try again.")
            sys.exit(1)

    # Test suite mapping
    test_runners = {
        "basic": run_basic_integration_tests,
        "production": run_production_integration_tests,
        "e2e": run_e2e_tests,
        "protocol": run_protocol_compliance_tests,
        "performance": run_performance_tests,
        "redis": run_redis_tests,
        "full": run_full_integration_suite,
        "all": run_all_tests_with_coverage,
        "smoke": run_quick_smoke_tests,
        "auth": run_authentication_tests,
        "search": run_search_tests,
        "playlist": run_playlist_tests,
        "favorites": run_favorites_tests,
    }

    print(f"🚀 Starting {args.suite} integration tests for Tidal MCP Server")
    print(f"📍 Working directory: {Path.cwd()}")
    print(f"🐍 Python: {sys.executable}")

    start_time = time.time()
    success = test_runners[args.suite]()
    end_time = time.time()

    print(f"\n{'='*60}")
    if success:
        print(f"🎉 All tests passed! Total time: {end_time - start_time:.2f}s")
        sys.exit(0)
    else:
        print(f"💥 Some tests failed. Total time: {end_time - start_time:.2f}s")
        sys.exit(1)


if __name__ == "__main__":
    main()