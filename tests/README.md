# Tidal MCP Server Tests

This directory contains comprehensive tests for the Tidal MCP server, covering authentication, service layer functionality, and end-to-end integration scenarios.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and test configuration
├── test_auth.py             # Authentication and OAuth2 flow tests
├── test_service.py          # Service layer business logic tests  
├── test_integration.py      # End-to-end integration tests
├── requirements-test.txt    # Test-specific dependencies
└── README.md               # This file
```

## Test Categories

### Authentication Tests (`test_auth.py`)
- **OAuth2 PKCE Flow**: Complete authentication workflow with mocked external calls
- **Token Management**: Access token refresh, expiration handling, and session persistence
- **Session Management**: File-based session storage and loading
- **Error Handling**: Network errors, invalid tokens, and edge cases
- **Security**: PKCE parameter generation and validation

**Key Test Classes:**
- `TestTidalAuth`: Core authentication functionality
- `TestSessionManagement`: Session file operations
- `TestOAuth2Flow`: OAuth2 workflow components
- `TestErrorHandling`: Error scenarios and recovery
- `TestEdgeCases`: Boundary conditions and edge cases

### Service Layer Tests (`test_service.py`)
- **Search Functionality**: Multi-type search across tracks, albums, artists, and playlists
- **Playlist Management**: CRUD operations for playlists and track management
- **Favorites Management**: Adding/removing favorites across content types
- **Recommendations**: Track and artist radio, personalized recommendations
- **Content Retrieval**: Detailed information fetching for all content types
- **Data Conversion**: Transformation between tidalapi objects and internal models

**Key Test Classes:**
- `TestTidalService`: Core service initialization and utilities
- `TestSearchFunctionality`: Search operations and pagination
- `TestPlaylistManagement`: Playlist CRUD and track operations
- `TestFavoritesManagement`: Favorites operations
- `TestRecommendationsAndRadio`: Recommendation algorithms
- `TestDetailedItemRetrieval`: Content fetching
- `TestConversionMethods`: Data model transformations
- `TestErrorHandling`: Service-level error handling

### Integration Tests (`test_integration.py`)
- **End-to-End Workflows**: Complete user scenarios from authentication to content access
- **Authentication Integration**: Full OAuth2 flow with session persistence
- **Search Integration**: Multi-step search workflows with realistic data
- **Playlist Lifecycle**: Complete playlist management scenarios
- **Concurrent Operations**: Thread safety and parallel operation testing
- **Error Recovery**: System resilience and graceful degradation

**Key Test Classes:**
- `TestAuthenticationFlow`: Complete auth workflows
- `TestSearchIntegration`: Integrated search scenarios
- `TestPlaylistManagementIntegration`: End-to-end playlist workflows
- `TestFavoritesIntegration`: Complete favorites management
- `TestRecommendationsIntegration`: Recommendation system integration
- `TestErrorHandlingAndRecovery`: System resilience
- `TestConcurrentOperations`: Concurrency and thread safety

## Running Tests

### Prerequisites

Install test dependencies:
```bash
pip install -r tests/requirements-test.txt
```

Or install main dependencies with test extras:
```bash
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov
```

### Using the Test Runner

The provided test runner script (`run_tests.py`) offers convenient test execution:

```bash
# Run all tests
python run_tests.py

# Run only unit tests (fast)
python run_tests.py --type unit

# Run integration tests
python run_tests.py --type integration

# Run specific test files
python run_tests.py --type auth      # Authentication tests
python run_tests.py --type service   # Service layer tests

# Run with coverage report
python run_tests.py --coverage

# Run in parallel for faster execution
python run_tests.py --parallel

# Verbose output
python run_tests.py --verbose

# Run specific test file
python run_tests.py --file test_auth.py
```

### Using Pytest Directly

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/tidal_mcp --cov-report=html

# Run specific test files
pytest tests/test_auth.py
pytest tests/test_service.py
pytest tests/test_integration.py

# Run tests by marker
pytest -m "not integration"  # Skip integration tests
pytest -m "auth"            # Only auth tests
pytest -m "slow"            # Only slow tests

# Run with different verbosity
pytest -v                   # Verbose
pytest -vv                  # Extra verbose
pytest -q                   # Quiet

# Run in parallel
pytest -n auto              # Auto-detect CPU cores
```

## Test Configuration

### Pytest Configuration (`pytest.ini`)
- Async test support with `pytest-asyncio`
- Coverage settings with 80% minimum threshold
- Test markers for different test categories
- Timeout configuration for long-running tests
- Warning filters for clean output

### Test Markers

Tests are marked with categories for easy filtering:
- `unit`: Fast, isolated unit tests
- `integration`: Slower integration tests
- `auth`: Authentication-related tests
- `search`: Search functionality tests
- `playlist`: Playlist management tests
- `favorites`: Favorites management tests
- `slow`: Long-running tests
- `network`: Tests requiring network (normally skipped)

### Mock Strategy

Tests use comprehensive mocking to avoid external dependencies:
- **TidalAPI Mocking**: Complete tidalapi.Session mock with realistic behavior
- **HTTP Mocking**: aiohttp responses for OAuth2 flows
- **File System Mocking**: Temporary files for session persistence
- **Time Mocking**: Controlled time for token expiration testing

## Coverage Goals

- **Minimum Coverage**: 80% line coverage
- **Critical Paths**: 95%+ coverage for authentication and core service methods
- **Error Handling**: All error scenarios covered with appropriate tests
- **Edge Cases**: Boundary conditions and unusual inputs tested

## Test Data

Tests use factory functions to create realistic test data:
- `create_sample_tidal_track()`: Mock tidalapi track objects
- `create_sample_tidal_playlist()`: Mock tidalapi playlist objects
- Fixtures provide consistent mock sessions and temporary files

## Performance Considerations

- **Fast Unit Tests**: <50ms per test average
- **Integration Tests**: <500ms per test average
- **Parallel Execution**: Tests designed to run safely in parallel
- **Minimal Setup**: Shared fixtures reduce test setup overhead

## Debugging Tests

### Running Individual Tests
```bash
# Run specific test method
pytest tests/test_auth.py::TestTidalAuth::test_pkce_generation -v

# Run specific test class
pytest tests/test_service.py::TestSearchFunctionality -v

# Run with debugger on failure
pytest --pdb

# Run with print statements visible
pytest -s
```

### Common Issues

1. **Async Test Failures**: Ensure `@pytest.mark.asyncio` decorator is present
2. **Mock Issues**: Verify mock setup matches actual API interfaces
3. **File Permission Errors**: Tests clean up temporary files automatically
4. **Import Errors**: Ensure PYTHONPATH includes src directory

## Contributing

When adding new tests:

1. **Follow Naming Conventions**: Use descriptive test names starting with `test_`
2. **Use Appropriate Markers**: Mark tests with relevant categories
3. **Mock External Dependencies**: Don't rely on actual Tidal API calls
4. **Test Error Scenarios**: Include negative test cases
5. **Document Complex Tests**: Add docstrings for complex test scenarios
6. **Maintain Coverage**: Ensure new code has appropriate test coverage

## CI/CD Integration

Tests are designed to run in CI/CD environments:
- No external network dependencies
- Deterministic behavior with mocked time/randomness
- Parallel execution support
- Coverage reporting in multiple formats
- Clear exit codes for build integration