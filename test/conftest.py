import pytest
import os

@pytest.fixture(autouse=True)
def _env_for_tests(monkeypatch):
    # Evita cargar .pkl y evita levantar UI de Streamlit durante los imports
    monkeypatch.setenv("UNIT_TESTS", "1")
    monkeypatch.setenv("RUN_STREAMLIT_UI", "0")
    monkeypatch.setenv("USE_OPENROUTER", "true")
    # Claves dummy (no se usan realmente gracias a los mocks)
    monkeypatch.setenv("OPENROUTER_API_KEY", "dummy")
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")
    monkeypatch.setenv("GOOGLE_SAFE_BROWSING_KEY", "dummy")
    yield
