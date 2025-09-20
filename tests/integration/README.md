# Integration Test Framework for Tidal MCP Server

A comprehensive integration testing framework that validates the complete request/response cycle for all MCP tools, tests end-to-end workflows, and ensures MCP protocol compliance.

## Overview

This integration test framework provides:

- **Complete MCP tool testing** - All 15+ core tools and 7 enhanced production tools
- **End-to-end workflow validation** - Multi-step operations and user flows
- **MCP protocol compliance** - Ensures adherence to Model Context Protocol standards
- **Performance testing** - Load testing and performance benchmarks
- **Mock data factories** - Realistic test data generation
- **Production middleware testing** - Rate limiting, security, and observability

## Test Structure

```
tests/integration/
├── conftest.py              # Test fixtures and configuration
├── test_mcp_tools_core.py   # Core MCP tools integration tests
├── test_mcp_tools_production.py # Production tools integration tests
├── test_e2e_flows.py        # End-to-end workflow tests
├── test_mcp_protocol.py     # MCP protocol compliance tests
├── test_performance.py      # Performance and load tests
├── test_helpers.py          # Test utilities and mock data generators
└── README.md               # This file
```

## Quick Start

### Running Basic Integration Tests

```bash
# Run core MCP tools tests
python tests/run_integration_tests.py basic

# Run production tools tests
python tests/run_integration_tests.py production

# Run end-to-end workflow tests
python tests/run_integration_tests.py e2e
```

### Running Specific Test Categories

```bash
# Authentication tests
python tests/run_integration_tests.py auth

# Search functionality tests
python tests/run_integration_tests.py search

# Playlist management tests
python tests/run_integration_tests.py playlist

# Favorites management tests
python tests/run_integration_tests.py favorites
```

### Running Performance Tests

```bash
# Performance and load tests (slower)
python tests/run_integration_tests.py performance

# Quick smoke tests
python tests/run_integration_tests.py smoke
```

### Running Complete Test Suite

```bash
# Full integration suite with coverage
python tests/run_integration_tests.py all

# Environment check + full suite
python tests/run_integration_tests.py all --check-env
```

## Test Categories

### Core MCP Tools Tests (`test_mcp_tools_core.py`)

Tests all basic MCP tools with complete request/response validation:

- **Authentication Tools**
  - `tidal_login` - OAuth2 authentication flow
  - Session management and user info retrieval

- **Search Tools**
  - `tidal_search` - Multi-type content search (tracks, albums, artists, playlists)
  - Parameter validation and result formatting
  - Error handling and edge cases

- **Playlist Management Tools**
  - `tidal_get_playlist` - Playlist retrieval with track lists
  - `tidal_create_playlist` - New playlist creation
  - `tidal_add_to_playlist` - Track addition to playlists
  - `tidal_remove_from_playlist` - Track removal by index
  - `tidal_get_user_playlists` - User playlist listing

- **Favorites Management Tools**
  - `tidal_get_favorites` - Retrieve user favorites by type
  - `tidal_add_favorite` - Add items to favorites
  - `tidal_remove_favorite` - Remove items from favorites

- **Content Retrieval Tools**
  - `tidal_get_track` - Detailed track information
  - `tidal_get_album` - Detailed album information
  - `tidal_get_artist` - Detailed artist information

- **Recommendation Tools**
  - `tidal_get_recommendations` - Personalized recommendations
  - `tidal_get_track_radio` - Track-based radio generation

### Production Tools Tests (`test_mcp_tools_production.py`)

Tests enhanced production tools with middleware integration:

- **Health and Monitoring**
  - `health_check` - Comprehensive system health validation
  - `get_system_status` - Detailed system metrics and status

- **Enhanced Authentication**
  - Enhanced `tidal_login` with security metadata
  - `refresh_session` - Session token refresh
  - Security middleware integration

- **Streaming Services**
  - `get_stream_url` - Streaming URL generation with quality options
  - DRM and geo-restriction handling
  - Format and quality validation

- **Advanced Search**
  - `tidal_search_advanced` - Enhanced search with filtering and metadata
  - Relevance scoring and pagination
  - Performance metrics integration

- **Rate Limiting**
  - `get_rate_limit_status` - Rate limit monitoring and recommendations
  - Middleware rate limiting integration
  - Tier-based limit enforcement

### End-to-End Flow Tests (`test_e2e_flows.py`)

Tests complete user workflows and multi-step operations:

- **Authentication → Search Flows**
  - Login → Search → Track details retrieval
  - Multi-type search → Content detail workflows

- **Playlist Management Flows**
  - Create playlist → Add tracks → Manage tracks → Cleanup
  - Search → Create playlist → Add search results

- **Favorites Management Flows**
  - Add to favorites → Retrieve favorites → Remove from favorites
  - Cross-content-type favorites workflows

- **Discovery Flows**
  - Recommendations → Playlist creation → Add recommended tracks
  - Track radio → Discovery → Favorites management

- **Production Flows**
  - Enhanced authentication → Advanced search → Stream URL generation
  - System monitoring → Health checks → Status validation

### MCP Protocol Compliance Tests (`test_mcp_protocol.py`)

Ensures adherence to Model Context Protocol standards:

- **Tool Registration and Discovery**
  - All expected tools are properly registered
  - Tool metadata and documentation compliance
  - Parameter and return type validation

- **Parameter Handling**
  - Required parameter validation
  - Optional parameter defaults
  - Type coercion and bounds checking
  - Input sanitization

- **Response Formatting**
  - Consistent response structure across tools
  - Success/error response format compliance
  - Boolean operation consistency
  - Metadata inclusion and formatting

- **Error Handling**
  - Authentication error propagation
  - Service layer error handling
  - Validation error responses
  - Enhanced error handling with middleware

- **Async Operation Compliance**
  - All tools are properly async
  - Concurrent execution support
  - Error propagation in async context

- **Data Integrity**
  - Model consistency across tools
  - Null value handling
  - Unicode character support

### Performance Tests (`test_performance.py`)

Validates performance characteristics and scalability:

- **Performance Baselines**
  - Individual tool performance benchmarks
  - Response time validation
  - Resource usage monitoring

- **Concurrent Request Handling**
  - Multi-request concurrent execution
  - Mixed operation concurrency
  - Middleware overhead under load

- **Rate Limiting Performance**
  - Rate limiter performance under load
  - Concurrent rate limit enforcement
  - Redis operation scaling

- **Memory and Resource Usage**
  - Memory consumption under sustained load
  - Resource cleanup validation
  - Connection handling efficiency

- **Stress Testing**
  - Large result set handling
  - Rapid successive request processing
  - Error handling performance
  - Breaking point identification

## Test Fixtures and Utilities

### Core Fixtures (`conftest.py`)

- **Mock Services**
  - `mock_redis` - Fake Redis client for testing
  - `mock_auth_manager` - Mock authentication manager
  - `tidal_service` - Configured Tidal service instance
  - `middleware_stack` - Production middleware stack

- **Data Factories**
  - `track_factory` - Create Track model instances
  - `album_factory` - Create Album model instances
  - `artist_factory` - Create Artist model instances
  - `playlist_factory` - Create Playlist model instances
  - `search_results_factory` - Create SearchResults instances

- **Mock Objects**
  - `mock_track_objects` - Mock Tidal API track objects
  - `mock_album_objects` - Mock Tidal API album objects
  - `mock_artist_objects` - Mock Tidal API artist objects
  - `mock_playlist_objects` - Mock Tidal API playlist objects

- **Utilities**
  - `mock_successful_response` - Standard success response format
  - `mock_error_response` - Standard error response format
  - `fixed_time` - Fixed reference time for consistent testing (does not freeze system time)
  - `frozen_time` - Frozen time control for tests that need time manipulation

### Test Helpers (`test_helpers.py`)

- **Mock Data Generator**
  - `TidalMockDataGenerator` - Realistic data generation
  - Configurable data pools and templates
  - Consistent ID generation

- **Mock Object Creator**
  - `MockTidalObjects` - Create mock API objects
  - Realistic property simulation
  - Method mocking for API interactions

- **Test Data Factories**
  - `TestDataFactories` - Scenario-based data creation
  - Search scenarios, user libraries, recommendations
  - Complete workflow data sets

- **Response Validators**
  - `ResponseValidators` - Format compliance validation
  - Type-specific response validation
  - Enhanced response format checks

- **Custom Assertions**
  - `TestAssertion` - Specialized test assertions
  - Data validity checks
  - Performance assertions
  - Pagination validation

## Running Tests

### Prerequisites

```bash
# Install test dependencies
pip install -e ".[test]"

# Or with uv
uv sync --extra test
```

### Test Markers

The framework uses pytest markers to categorize tests:

- `integration` - Integration tests (default for most tests)
- `e2e` - End-to-end workflow tests
- `auth` - Authentication-related tests
- `search` - Search functionality tests
- `playlist` - Playlist management tests
- `favorites` - Favorites management tests
- `slow` - Slow-running tests (performance, load)
- `redis` - Tests requiring Redis connection

### Running Specific Test Types

```bash
# Run only fast integration tests
pytest tests/integration/ -m "integration and not slow"

# Run only authentication tests
pytest tests/integration/ -m "auth"

# Run only search-related tests
pytest tests/integration/ -m "search"

# Run end-to-end tests
pytest tests/integration/ -m "e2e"

# Run performance tests
pytest tests/integration/ -m "slow"

# Run Redis-dependent tests
pytest tests/integration/ -m "redis"
```

### Coverage Reports

```bash
# Generate HTML coverage report
pytest tests/integration/ --cov=src/tidal_mcp --cov-report=html

# Generate XML coverage report
pytest tests/integration/ --cov=src/tidal_mcp --cov-report=xml

# Terminal coverage report
pytest tests/integration/ --cov=src/tidal_mcp --cov-report=term-missing
```

## Configuration

### Environment Variables

Tests can be configured with environment variables:

```bash
# Test environment (set automatically)
export ENVIRONMENT="test"

# Redis URL for tests (uses fake Redis by default)
export REDIS_URL="redis://localhost:6379/15"

# Test Tidal credentials (mocked by default)
export TIDAL_CLIENT_ID="test_client_id"
export TIDAL_CLIENT_SECRET="test_client_secret"
```

### pytest.ini Configuration

The test framework is configured via `pytest.ini`:

```ini
[pytest]
testpaths = tests
asyncio_mode = auto
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    auth: Authentication tests
    search: Search tests
    playlist: Playlist tests
    favorites: Favorites tests
    slow: Slow tests
    redis: Redis tests
```

## Performance Benchmarks

### Expected Performance Baselines

- **Authentication**: < 1.0s average
- **Search operations**: < 2.0s average
- **Playlist operations**: < 2.0s average
- **Favorites operations**: < 1.5s average
- **Health checks**: < 1.0s average

### Concurrent Request Limits

- **Basic integration tests**: 10 concurrent requests
- **Performance tests**: 50-100 concurrent requests
- **Rate limiting tests**: User-specific limits based on tier

### Memory Usage

- **Sustained load**: < 100MB memory increase
- **Large result sets**: Graceful handling of 1000+ items
- **Garbage collection**: Proper cleanup between test batches

## Debugging and Troubleshooting

### Common Issues

1. **Redis Connection Errors**
   ```bash
   # Use fake Redis for testing
   pytest tests/integration/ -m "not redis"
   ```

2. **Performance Test Timeouts**
   ```bash
   # Increase timeout for slow tests
   pytest tests/integration/ -m "slow" --timeout=600
   ```

3. **Mock Data Issues**
   ```bash
   # Run with verbose output
   pytest tests/integration/ -v --tb=long
   ```

### Debug Mode

```bash
# Run with debugging output
pytest tests/integration/ -s -vv --tb=long

# Run specific test with debugging
pytest tests/integration/test_mcp_tools_core.py::TestSearchTools::test_tidal_search_tracks -s -vv
```

### Test Data Inspection

The framework provides utilities for inspecting test data:

```python
# In test files
from tests.integration.test_helpers import TestDataFactories

# Create and inspect test scenarios
scenario = TestDataFactories.create_search_scenario("debug", 3, 2, 2, 1)
print(f"Generated {len(scenario['tracks'])} tracks")
```

## Contributing

When adding new tests:

1. Follow existing test patterns and naming conventions
2. Use appropriate pytest markers for categorization
3. Include both success and failure test cases
4. Validate response formats and data integrity
5. Add performance expectations for new functionality
6. Update this README with new test categories

### Test Development Guidelines

- **Isolation**: Tests should be independent and not rely on external services
- **Mocking**: Use comprehensive mocking for external dependencies
- **Assertions**: Include detailed assertions with descriptive error messages
- **Coverage**: Aim for comprehensive coverage of all code paths
- **Performance**: Include performance validations for all operations
- **Documentation**: Document complex test scenarios and edge cases

## Continuous Integration

The integration test framework is designed for CI/CD integration:

```yaml
# GitHub Actions example
- name: Run Integration Tests
  run: |
    python tests/run_integration_tests.py basic
    python tests/run_integration_tests.py production
    python tests/run_integration_tests.py e2e
    python tests/run_integration_tests.py protocol

- name: Run Performance Tests
  run: python tests/run_integration_tests.py performance
  if: github.event_name == 'schedule'  # Run performance tests on schedule
```

The framework provides exit codes and structured output suitable for CI/CD pipeline integration.