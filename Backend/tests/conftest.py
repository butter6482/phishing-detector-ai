import pytest
from fastapi.testclient import TestClient

import api


@pytest.fixture(autouse=True)
def no_external_calls(monkeypatch):
    """Tests must never hit OpenRouter or Google Safe Browsing."""
    monkeypatch.setattr("src.safebrowsing.GSB_KEY", "")
    monkeypatch.setattr("src.openrouter.OPENROUTER_API_KEY", "")


@pytest.fixture
def client():
    return TestClient(api.app)
