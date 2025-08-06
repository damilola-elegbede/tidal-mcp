#!/usr/bin/env python3
"""
Quick test runner for Tidal MCP development
"""
import subprocess
import sys
from pathlib import Path

def run_quick_tests():
    """Run essential tests quickly for development"""
    
    print("🚀 Running Quick Test Suite...")
    print("=" * 50)
    
    # Essential test modules only
    quick_tests = [
        "tests/test_models.py",
        "tests/test_utils.py", 
        "tests/test_server.py::test_tidal_search",
        "tests/test_server.py::test_tidal_login",
        "tests/test_integration.py::test_server_initialization"
    ]
    
    cmd = [
        "uv", "run", "pytest",
        *quick_tests,
        "-v",
        "--tb=short",
        "--maxfail=5",
        "--disable-warnings"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=False, timeout=180)
        if result.returncode == 0:
            print("✅ Quick tests PASSED!")
            return True
        else:
            print("❌ Some quick tests FAILED")
            return False
    except subprocess.TimeoutExpired:
        print("⏰ Tests timed out")
        return False
    except Exception as e:
        print(f"💥 Error running tests: {e}")
        return False

def run_coverage_report():
    """Generate a quick coverage report"""
    print("\n📊 Generating Coverage Report...")
    print("=" * 50)
    
    cmd = [
        "uv", "run", "pytest", 
        "tests/test_models.py",
        "tests/test_utils.py",
        "--cov=src/tidal_mcp",
        "--cov-report=term",
        "--cov-fail-under=85",
        "-q"
    ]
    
    try:
        subprocess.run(cmd, timeout=120)
        print("✅ Coverage report generated!")
    except Exception as e:
        print(f"⚠️  Coverage report failed: {e}")

if __name__ == "__main__":
    success = run_quick_tests()
    if success:
        run_coverage_report()
        print("\n🎉 Development tests completed!")
        sys.exit(0)
    else:
        print("\n🚨 Fix failing tests before proceeding")
        sys.exit(1)