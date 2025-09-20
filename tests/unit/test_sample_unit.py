"""
Sample unit test to validate pytest configuration.
"""

import pytest


@pytest.mark.unit
def test_sample_unit():
    """Simple unit test to verify pytest works."""
    assert 1 + 1 == 2


@pytest.mark.unit
def test_env_vars_fixture(mock_env_vars):
    """Test that env vars fixture works."""
    # Check that the fixture provides the expected keys with fake test values
    assert "TIDAL_CLIENT_ID" in mock_env_vars
    assert mock_env_vars["TIDAL_CLIENT_ID"].startswith("fake_test_client_")
    assert "TIDAL_CLIENT_SECRET" in mock_env_vars
    assert mock_env_vars["TIDAL_CLIENT_SECRET"].startswith("fake_test_secret_")
    assert mock_env_vars["TIDAL_REDIRECT_URI"] == "http://fake-test-callback.localhost:9999/callback"
    assert mock_env_vars["TIDAL_COUNTRY_CODE"] == "XX"


@pytest.mark.unit
def test_track_factory(mock_factory_boy):
    """Test track factory fixture."""
    track = mock_factory_boy["track_factory"](title="Custom Track")
    assert track["title"] == "Custom Track"
    assert track["id"] == 12345