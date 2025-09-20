"""
Sample E2E test to validate pytest configuration.
"""

import pytest


@pytest.mark.e2e
@pytest.mark.slow
def test_sample_e2e():
    """Simple E2E test to verify pytest works."""
    assert True


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.skipif(
    True,  # Skip by default since it's just a sample
    reason="Sample E2E test - normally would require full system"
)
def test_full_system_mock():
    """Mock test representing full system integration."""
    # This would test the entire MCP server flow
    assert True