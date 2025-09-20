"""
Sample integration test to validate pytest configuration.
"""

import pytest


@pytest.mark.integration
def test_sample_integration():
    """Simple integration test to verify pytest works."""
    assert True


@pytest.mark.integration
def test_mock_redis_simple():
    """Test simple mock Redis functionality."""
    # Simple test without external dependencies
    fake_redis = {"test_key": "test_value"}
    assert fake_redis["test_key"] == "test_value"


@pytest.mark.integration
async def test_async_redis_fixture(mock_async_redis):
    """Test async Redis fixture works."""
    await mock_async_redis.set("test_key", "test_value")
    result = await mock_async_redis.get("test_key")
    assert result == "test_value"


@pytest.mark.integration
def test_aiohttp_mock(mock_aiohttp_session):
    """Test aiohttp mocking works."""
    assert mock_aiohttp_session is not None
