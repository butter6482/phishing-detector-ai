"""Smoke test del endpoint HTTP. Requiere fastapi/pydantic instalados y cargables
(en algunos Windows con Application Control el .pyd de pydantic-core está bloqueado;
por eso se hace skip en vez de fallar)."""
import pytest

pytest.importorskip("fastapi")
try:
    from fastapi.testclient import TestClient

    from api import app
except Exception as e:  # pragma: no cover - entorno sin binarios nativos
    pytest.skip(f"no se puede cargar la app FastAPI: {e}", allow_module_level=True)

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_analyze_without_llm(monkeypatch):
    monkeypatch.setenv("USE_OPENROUTER", "false")
    r = client.post("/analyze", json={"message": "Verifica tu cuenta urgente, haz clic aqui", "lang": "es"})
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"nb", "llm", "safebrowsing", "final"}
    assert body["final"]["risk"] in ("safe", "warning", "phishing")
    assert 0 <= body["final"]["score"] <= 100
    assert body["llm"] is None


def test_analyze_rejects_short_message():
    r = client.post("/analyze", json={"message": "hi", "lang": "es"})
    assert r.status_code == 422
