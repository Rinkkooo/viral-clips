"""
Global test configuration and fixtures for Viral Clips AI test suite.
"""

import pytest
from viral_clips.config import settings


@pytest.fixture(autouse=True)
def configure_test_environment(monkeypatch):
    """
    Sets test environment flags so that unit tests can run offline
    fixtures without crashing if Faster-Whisper or external API keys are absent,
    while individual tests can still monkeypatch to test production enforcement.
    """
    monkeypatch.setattr(settings, "app_env", "test")
    monkeypatch.setattr(settings, "allow_test_fixtures", True)
