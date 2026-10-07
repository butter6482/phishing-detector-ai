import pytest

import api


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_analyze_flags_obvious_phishing(client):
    msg = "URGENTE: tu cuenta fue suspendida, verifica tu contrasena ya en http://192.168.0.1/login"
    r = client.post("/analyze", json={"message": msg, "lang": "es"})
    assert r.status_code == 200
    body = r.json()
    assert set(body) >= {"nb", "llm", "safebrowsing", "final"}
    assert body["final"]["is_phishing"] is True
    assert body["final"]["risk"] in {"warning", "phishing"}
    assert body["llm"] is None  # no OpenRouter key in tests
    assert body["final"]["source"].startswith("fallback:")


def test_analyze_benign_message_is_not_phishing(client):
    msg = "Hola equipo, adjunto las notas de la reunion de ayer. Nos vemos el lunes."
    r = client.post("/analyze", json={"message": msg, "lang": "es"})
    assert r.status_code == 200
    assert r.json()["final"]["is_phishing"] is False


def test_analyze_rejects_too_short_message(client):
    r = client.post("/analyze", json={"message": "a"})
    assert r.status_code == 422


def test_analyze_rejects_unknown_language(client):
    r = client.post("/analyze", json={"message": "hola mundo", "lang": "fr"})
    assert r.status_code == 422


def test_analyze_uses_llm_verdict_when_available(client, monkeypatch):
    monkeypatch.setattr(
        api,
        "call_openrouter",
        lambda text, lang: {"verdict": "phishing", "explanation": "looks fake", "advice": "do not click"},
    )
    r = client.post("/analyze", json={"message": "mensaje cualquiera de prueba", "lang": "es"})
    assert r.status_code == 200
    body = r.json()
    assert body["llm"]["verdict"] == "phishing"
    assert body["final"]["source"] == "openrouter:phishing"
    assert body["final"]["score"] >= 80


def test_analyze_surfaces_llm_error_and_falls_back(client, monkeypatch):
    monkeypatch.setattr(api, "call_openrouter", lambda text, lang: {"error": "openrouter_error: boom"})
    r = client.post("/analyze", json={"message": "mensaje cualquiera de prueba", "lang": "es"})
    assert r.status_code == 200
    assert r.json()["final"]["source"] == "fallback:llm_error"


@pytest.mark.xfail(
    strict=True,
    reason="Known bug: api.analyze() adds final['llm_error'] but the FinalResult response_model "
    "has no such field, so FastAPI drops it. Remove this marker once fixed.",
)
def test_analyze_exposes_llm_error_to_client(client, monkeypatch):
    monkeypatch.setattr(api, "call_openrouter", lambda text, lang: {"error": "openrouter_error: boom"})
    r = client.post("/analyze", json={"message": "mensaje cualquiera de prueba", "lang": "es"})
    assert "boom" in r.json()["final"]["llm_error"]
