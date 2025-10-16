import os
import json
import importlib
from fastapi.testclient import TestClient

# Ensure env does not call external services by default
os.environ.setdefault("USE_OPENROUTER", "false")
os.environ.setdefault("GOOGLE_SAFE_BROWSING_KEY", "")

api = importlib.import_module("Backend.api")
app = api.app
client = TestClient(app)


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


def test_analyze_minimal():
    payload = {"message": "Hola, actualiza tu password en http://example.com", "lang": "es"}
    r = client.post("/analyze", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert set(data.keys()) == {"nb", "llm", "safebrowsing", "final"}
    assert isinstance(data["nb"], dict)
    assert isinstance(data["safebrowsing"], dict)
    assert isinstance(data["final"], dict)
    # Ensure score bounded and required fields
    assert 0 <= int(data["final"]["score"]) <= 100
    assert data["final"]["label"] in {"phishing", "legit"}
