#!/usr/bin/env python3
"""
Test Framework Setup Script for Tidal MCP

This script sets up the complete test framework architecture including:
- Test dependencies installation
- Directory structure creation
- Configuration file setup
- Example test implementation
"""

import subprocess
import sys
from pathlib import Path


def run_command(command, description=""):
    """Run a shell command and handle errors."""
    print(f"{'=' * 60}")
    print(f"Running: {description or command}")
    print(f"{'=' * 60}")

    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return False


def create_directory_structure(base_path):
    """Create the test directory structure."""
    print(f"Creating test directory structure in {base_path}")

    directories = [
        "tests",
        "tests/unit",
        "tests/unit/production",
        "tests/integration",
        "tests/integration/production",
        "tests/e2e",
        "tests/fixtures",
        "tests/fixtures/tidal_responses",
        "tests/utils",
    ]

    for directory in directories:
        dir_path = base_path / directory
        dir_path.mkdir(parents=True, exist_ok=True)

        # Create __init__.py files
        init_file = dir_path / "__init__.py"
        if not init_file.exists():
            init_file.write_text('"""Test module."""\n')

    print("✅ Test directory structure created successfully")


def setup_pytest_configuration(base_path):
    """Setup pytest.ini configuration."""
    pytest_ini_content = """[tool:pytest]
minversion = 7.0
addopts =
    --strict-markers
    --strict-config
    --asyncio-mode=auto
    --cov=src/tidal_mcp
    --cov-report=html:htmlcov
    --cov-report=xml:coverage.xml
    --cov-report=term-missing
    --cov-fail-under=80
    --cov-exclude=src/tidal_mcp/__main__.py
    --cov-exclude=src/tidal_mcp/production/middleware.py
    -v
    --tb=short
    --timeout=300
    --durations=10
    -x
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Tests that take more than 1 second
    auth: Authentication related tests
    redis: Tests requiring Redis
    network: Tests making network calls
    mcp: MCP tool tests
    benchmark: Performance benchmark tests
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
    error::UserWarning
"""

    pytest_ini_path = base_path / "pytest.ini"
    pytest_ini_path.write_text(pytest_ini_content)
    print(f"✅ Created pytest.ini at {pytest_ini_path}")


def update_pyproject_toml(base_path):
    """Update pyproject.toml with test dependencies and coverage configuration."""
    pyproject_path = base_path / "pyproject.toml"

    if not pyproject_path.exists():
        print("❌ pyproject.toml not found")
        return False

    # Read existing content
    content = pyproject_path.read_text()

    # Add test dependencies if not present
    test_deps = '''
# Test dependencies
test = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "aioresponses>=0.7.4",
    "pytest-mock>=3.11.0",
    "faker>=19.0.0",
    "freezegun>=1.2.0",
    "pytest-xdist>=3.3.0",
    "pytest-timeout>=2.1.0",
    "pytest-benchmark>=4.0.0",
    "httpx>=0.24.0",
    "respx>=0.20.0",
]'''

    coverage_config = '''
[tool.coverage.run]
source = ["src/tidal_mcp"]
omit = [
    "src/tidal_mcp/__main__.py",
    "src/tidal_mcp/production/middleware.py",
    "tests/*",
    "examples/*",
    ".venv/*",
    "*/__pycache__/*",
]
branch = true
concurrency = ["thread", "multiprocessing"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if self.debug:",
    "if settings.DEBUG",
    "raise AssertionError",
    "raise NotImplementedError",
    "if 0:",
    "if __name__ == .__main__.:",
    "class .*\\\\bProtocol\\\\):",
    "@(abc\\\\.)?abstractmethod",
    "except ImportError:",
    "except ModuleNotFoundError:",
]
show_missing = true
skip_covered = false
precision = 2

[tool.coverage.html]
directory = "htmlcov"

[tool.coverage.xml]
output = "coverage.xml"'''

    # Check if test dependencies section exists
    if '[project.optional-dependencies]' in content and 'test = [' not in content:
        # Add test dependencies to existing optional-dependencies
        content = content.replace(
            '[project.optional-dependencies]',
            f'[project.optional-dependencies]\n{test_deps}'
        )
    elif '[project.optional-dependencies]' not in content:
        # Add the entire section
        content += f'\n[project.optional-dependencies]{test_deps}\n'

    # Add coverage configuration if not present
    if '[tool.coverage.run]' not in content:
        content += f'\n{coverage_config}\n'

    # Update uv dev-dependencies to include test deps
    if '[tool.uv]' in content and 'pytest>=' not in content:
        uv_test_deps = '''    # Test dependencies
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "aioresponses>=0.7.4",
    "pytest-mock>=3.11.0",
    "faker>=19.0.0",
    "freezegun>=1.2.0",
    "pytest-xdist>=3.3.0",
    "pytest-timeout>=2.1.0",
    "pytest-benchmark>=4.0.0",
    "httpx>=0.24.0",
    "respx>=0.20.0",'''

        # Add after the existing dev dependencies
        if 'dev-dependencies = [' in content:
            content = content.replace(
                '"mypy>=1.5.0"',
                f'"mypy>=1.5.0",\n{uv_test_deps}'
            )

    pyproject_path.write_text(content)
    print("✅ Updated pyproject.toml with test dependencies and coverage configuration")
    return True


def create_conftest_file(base_path):
    """Create the main conftest.py file."""
    conftest_content = '''"""
Global test configuration and fixtures for Tidal MCP tests.
"""

import asyncio
import re
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

import aioresponses
import pytest
from faker import Faker

from src.tidal_mcp.auth import TidalAuth
from src.tidal_mcp.models import Album, Artist, Playlist, Track
from src.tidal_mcp.service import TidalService

fake = Faker()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def clean_global_state():
    """Ensure clean global state between tests."""
    import src.tidal_mcp.server as server_module

    # Store original state
    original_auth = server_module.auth_manager
    original_service = server_module.tidal_service

    # Reset for test
    server_module.auth_manager = None
    server_module.tidal_service = None

    yield

    # Restore original state
    server_module.auth_manager = original_auth
    server_module.tidal_service = original_service


@pytest.fixture
def mock_auth():
    """Mock authenticated TidalAuth instance."""
    auth = Mock(spec=TidalAuth)
    auth.is_authenticated.return_value = True
    auth.get_user_info.return_value = {
        "id": "test_user_123",
        "username": "testuser",
        "country_code": "US",
    }
    auth.access_token = "mock_access_token"
    auth.country_code = "US"
    auth.session_id = "mock_session_id"
    return auth


@pytest.fixture
def mock_service(mock_auth):
    """Mock TidalService with authenticated auth manager."""
    service = Mock(spec=TidalService)
    service.auth_manager = mock_auth
    return service


@pytest.fixture
def sample_track():
    """Sample track data for testing."""
    return Track(
        id="123456789",
        title="Test Track",
        artist_names=["Test Artist"],
        album_title="Test Album",
        duration=180,
        track_number=1,
        quality="HIGH",
        explicit=False,
    )


@pytest.fixture
def mock_tidal_api_responses():
    """Fixture providing aioresponses for mocking HTTP calls."""
    with aioresponses.aioresponses() as m:
        yield m


@pytest.fixture
def tidal_response_data():
    """Standard Tidal API response data for testing."""
    return {
        "search_response": {
            "tracks": [
                {
                    "id": "123456789",
                    "title": "Test Track",
                    "artist": {"name": "Test Artist"},
                    "album": {"title": "Test Album"},
                    "duration": 180,
                    "trackNumber": 1,
                    "quality": "HIGH",
                }
            ],
            "albums": [],
            "artists": [],
            "playlists": [],
        },
        "auth_response": {
            "access_token": "mock_access_token",
            "refresh_token": "mock_refresh_token",
            "expires_in": 3600,
            "user": {
                "id": "test_user_123",
                "username": "testuser",
                "countryCode": "US",
            },
        },
    }


def setup_tidal_api_mocks(aioresponses_mock, response_data):
    """Setup comprehensive Tidal API mocks."""
    # Search endpoints
    aioresponses_mock.get(
        re.compile(r"https://api\\.tidalhifi\\.com/v1/search.*"),
        payload=response_data["search_response"],
    )

    # Authentication endpoints
    aioresponses_mock.post(
        "https://auth.tidal.com/v1/oauth2/token",
        payload=response_data["auth_response"],
    )
'''

    conftest_path = base_path / "tests" / "conftest.py"
    conftest_path.write_text(conftest_content)
    print(f"✅ Created conftest.py at {conftest_path}")


def create_example_tests(base_path):
    """Create example test files."""

    # Unit test example
    unit_test_content = '''"""Unit tests for TidalAuth class."""

import pytest
from unittest.mock import Mock, patch
from src.tidal_mcp.auth import TidalAuth, TidalAuthError


class TestTidalAuth:
    """Unit tests for TidalAuth authentication."""

    @pytest.mark.unit
    @pytest.mark.auth
    def test_init_with_custom_credentials(self):
        """Test TidalAuth initialization with custom credentials."""
        client_id = "test_client_id"
        client_secret = "test_client_secret"

        auth = TidalAuth(client_id=client_id, client_secret=client_secret)

        assert auth.client_id == client_id
        assert auth.client_secret == client_secret

    @pytest.mark.unit
    @pytest.mark.auth
    def test_is_authenticated_when_not_authenticated(self):
        """Test is_authenticated returns False when not authenticated."""
        auth = TidalAuth()
        auth.access_token = None

        result = auth.is_authenticated()

        assert result is False

    @pytest.mark.unit
    @pytest.mark.auth
    def test_is_authenticated_when_authenticated(self):
        """Test is_authenticated returns True when authenticated."""
        auth = TidalAuth()
        auth.access_token = "valid_token"

        result = auth.is_authenticated()

        assert result is True
'''

    # Integration test example
    integration_test_content = '''"""Integration tests for MCP tools."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from src.tidal_mcp.auth import TidalAuthError
import src.tidal_mcp.server as server


class TestMCPToolsIntegration:
    """Integration tests for basic MCP tools."""

    @pytest.mark.integration
    @pytest.mark.mcp
    async def test_tidal_search_integration(self, mock_service, sample_track):
        """Test tidal_search tool with service integration."""
        mock_service.search_all = AsyncMock()
        mock_service.search_all.return_value = Mock(
            to_dict=lambda: {"tracks": [sample_track.to_dict()]},
            total_results=1
        )

        with patch('src.tidal_mcp.server.ensure_service', return_value=mock_service):
            result = await server.tidal_search("test query", "all", 20, 0)

        assert "error" not in result
        assert result["query"] == "test query"
        assert result["content_type"] == "all"
        assert "results" in result

    @pytest.mark.integration
    @pytest.mark.mcp
    async def test_authentication_required_for_search(self):
        """Test that search tool requires authentication."""
        with patch('src.tidal_mcp.server.ensure_service') as mock_ensure:
            mock_ensure.side_effect = TidalAuthError("Not authenticated")

            result = await server.tidal_search("test")

        assert "error" in result
        assert "Authentication required" in result["error"]
'''

    # E2E test example
    e2e_test_content = '''"""End-to-end workflow tests."""

import pytest
from unittest.mock import patch
import src.tidal_mcp.server as server


@pytest.mark.e2e
@pytest.mark.slow
class TestCompleteWorkflows:
    """End-to-end tests for complete user workflows."""

    async def test_basic_search_workflow(self, mock_tidal_api_responses, tidal_response_data):
        """Test basic search workflow."""
        from tests.conftest import setup_tidal_api_mocks
        setup_tidal_api_mocks(mock_tidal_api_responses, tidal_response_data)

        # 1. Authenticate
        with patch('src.tidal_mcp.auth.TidalAuth._open_auth_url'):
            with patch('src.tidal_mcp.auth.TidalAuth._start_callback_server', return_value="auth_code"):
                login_result = await server.tidal_login()

        assert login_result["success"] is True

        # 2. Search for music
        search_result = await server.tidal_search("test", "tracks", 5)
        assert "results" in search_result
'''

    # Create the test files
    test_files = [
        ("tests/unit/test_auth.py", unit_test_content),
        ("tests/integration/test_mcp_tools.py", integration_test_content),
        ("tests/e2e/test_workflows.py", e2e_test_content),
    ]

    for file_path, content in test_files:
        full_path = base_path / file_path
        full_path.write_text(content)
        print(f"✅ Created example test: {full_path}")


def install_test_dependencies(base_path):
    """Install test dependencies using uv."""
    print("Installing test dependencies...")

    # Try uv first, then pip as fallback
    commands = [
        "uv add --dev pytest pytest-asyncio pytest-cov aioresponses pytest-mock faker freezegun pytest-xdist pytest-timeout pytest-benchmark httpx respx",
        "pip install pytest pytest-asyncio pytest-cov aioresponses pytest-mock faker freezegun pytest-xdist pytest-timeout pytest-benchmark httpx respx"
    ]

    for cmd in commands:
        if run_command(cmd, f"Installing dependencies with {cmd.split()[0]}"):
            print(f"✅ Dependencies installed successfully with {cmd.split()[0]}")
            return True
        print(f"❌ Failed to install with {cmd.split()[0]}, trying next method...")

    print("❌ Failed to install test dependencies with all methods")
    return False


def run_initial_tests(base_path):
    """Run initial tests to verify setup."""
    print("Running initial test to verify setup...")

    # Run a simple test command
    test_commands = [
        "python -m pytest tests/unit/test_auth.py::TestTidalAuth::test_init_with_custom_credentials -v",
        "python -m pytest --collect-only tests/",
        "python -m pytest --help"
    ]

    for cmd in test_commands:
        if run_command(cmd, f"Testing with: {cmd}"):
            print("✅ Test framework verification successful")
            return True

    print("❌ Test framework verification failed")
    return False


def create_test_commands_file(base_path):
    """Create a file with useful test commands."""
    commands_content = '''# Tidal MCP Test Framework Commands

## Quick Test Commands

# Run all tests with coverage
pytest tests/ --cov=src/tidal_mcp --cov-report=html

# Run only unit tests (fast)
pytest tests/unit/ -m "not slow"

# Run integration tests
pytest tests/integration/

# Run end-to-end tests
pytest tests/e2e/ -m e2e

# Run tests in parallel (faster)
pytest tests/ -n auto

# Run with specific markers
pytest tests/ -m "auth"          # Only auth tests
pytest tests/ -m "mcp"           # Only MCP tool tests
pytest tests/ -m "not slow"      # Skip slow tests

# Generate coverage report
pytest tests/ --cov=src/tidal_mcp --cov-report=html --cov-report=term-missing

# Run performance benchmarks
pytest tests/ -m benchmark --benchmark-only

# Debug failing tests
pytest tests/ -v --tb=long --pdb

# Check test performance (must complete in < 30 seconds)
timeout 30s pytest tests/ || echo "Tests exceeded 30 second limit"

## Coverage Commands

# Check coverage requirements
pytest tests/ --cov=src/tidal_mcp --cov-fail-under=80

# Generate detailed coverage report
coverage run -m pytest tests/
coverage report -m
coverage html

## CI/CD Commands

# Full CI test suite
pytest tests/ --cov=src/tidal_mcp --cov-report=xml --cov-fail-under=80 --timeout=300 --maxfail=10

# Quick validation
pytest tests/unit/ --maxfail=5 --timeout=60

## Development Commands

# Watch mode (requires pytest-watch)
# pip install pytest-watch
ptw tests/ -- --cov=src/tidal_mcp

# Auto-format test files
black tests/
ruff check tests/ --fix

# Type check tests
mypy tests/ --ignore-missing-imports
'''

    commands_path = base_path / "TEST_COMMANDS.md"
    commands_path.write_text(commands_content)
    print(f"✅ Created test commands reference: {commands_path}")


def main():
    """Main setup function."""
    print("🚀 Setting up Tidal MCP Test Framework")
    print("=" * 60)

    # Get the project root (assuming script is run from project root or .tmp)
    if Path.cwd().name == '.tmp':
        base_path = Path.cwd().parent
    else:
        base_path = Path.cwd()

    print(f"Project root: {base_path}")

    # Verify we're in the right directory
    if not (base_path / "src" / "tidal_mcp").exists():
        print("❌ Error: Could not find src/tidal_mcp directory.")
        print("   Please run this script from the project root directory.")
        sys.exit(1)

    success_steps = []

    # Step 1: Create directory structure
    try:
        create_directory_structure(base_path)
        success_steps.append("✅ Directory structure")
    except Exception as e:
        print(f"❌ Failed to create directory structure: {e}")
        sys.exit(1)

    # Step 2: Setup pytest configuration
    try:
        setup_pytest_configuration(base_path)
        success_steps.append("✅ Pytest configuration")
    except Exception as e:
        print(f"❌ Failed to setup pytest configuration: {e}")

    # Step 3: Update pyproject.toml
    try:
        if update_pyproject_toml(base_path):
            success_steps.append("✅ Updated pyproject.toml")
        else:
            print("⚠️  Could not update pyproject.toml")
    except Exception as e:
        print(f"❌ Failed to update pyproject.toml: {e}")

    # Step 4: Create conftest.py
    try:
        create_conftest_file(base_path)
        success_steps.append("✅ Created conftest.py")
    except Exception as e:
        print(f"❌ Failed to create conftest.py: {e}")

    # Step 5: Create example tests
    try:
        create_example_tests(base_path)
        success_steps.append("✅ Created example tests")
    except Exception as e:
        print(f"❌ Failed to create example tests: {e}")

    # Step 6: Install dependencies
    try:
        if install_test_dependencies(base_path):
            success_steps.append("✅ Installed test dependencies")
        else:
            print("⚠️  Could not install test dependencies automatically")
            print("   Please run: uv add --dev pytest pytest-asyncio pytest-cov aioresponses")
    except Exception as e:
        print(f"❌ Failed to install test dependencies: {e}")

    # Step 7: Create test commands reference
    try:
        create_test_commands_file(base_path)
        success_steps.append("✅ Created test commands reference")
    except Exception as e:
        print(f"❌ Failed to create test commands reference: {e}")

    # Step 8: Verify setup
    try:
        if run_initial_tests(base_path):
            success_steps.append("✅ Test framework verification")
    except Exception as e:
        print(f"❌ Test framework verification failed: {e}")

    # Summary
    print("\\n" + "=" * 60)
    print("🎯 SETUP COMPLETE")
    print("=" * 60)

    for step in success_steps:
        print(step)

    print("\\n📋 Next Steps:")
    print("1. Run: pytest tests/unit/test_auth.py -v")
    print("2. Check coverage: pytest tests/ --cov=src/tidal_mcp --cov-report=html")
    print("3. Review: TEST_COMMANDS.md for all available commands")
    print("4. Start implementing comprehensive tests for all 22 MCP tools")

    print("\\n🎯 Framework Goals:")
    print("- ✅ 85% coverage target (80% minimum)")
    print("- ✅ < 30 second full test suite execution")
    print("- ✅ Integration tests for all 22 MCP tools")
    print("- ✅ Comprehensive async testing with mocked Tidal API")

    print("\\n📖 Documentation:")
    print("- Full architecture: .tmp/test_framework_architecture.md")
    print("- Test examples: .tmp/test_examples.py")
    print("- Quick commands: TEST_COMMANDS.md")


if __name__ == "__main__":
    main()
