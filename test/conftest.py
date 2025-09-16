import pytest, os

@pytest.fixture(autouse=True)
def _env_for_tests(monkeypatch):
    # Evita cargar .pkl y evita levantar la UI de Streamlit
    monkeypatch.setenv("UNIT_TESTS", "1")
    monkeypatch.setenv("RUN_STREAMLIT_UI", "0")
    monkeypatch.setenv("USE_OPENROUTER", "true")
    # Claves dummy
    monkeypatch.setenv("OPENROUTER_API_KEY", "dummy")
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")
    monkeypatch.setenv("GOOGLE_SAFE_BROWSING_KEY", "dummy")
    yield
