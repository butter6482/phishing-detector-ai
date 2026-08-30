"""Tests de la lógica de scoring/heurística (sin dependencias de FastAPI/pydantic)."""
import pytest

from src import inference, openrouter, safebrowsing


# --- normalize -------------------------------------------------------------
def test_normalize_strips_accents_and_leet():
    assert inference.normalize("Vér1f1c@") == "verlflca"
    assert inference.normalize("BANCO") == "banco"


# --- keyword_hits --------------------------------------------------------
def test_keyword_hits_detects_phishing_language():
    hits = inference.keyword_hits("URGENTE: verifica tu cuenta del banco, haz clic aqui")
    assert hits  # no vacío
    assert len(hits) == len(set(hits))  # sin duplicados


def test_keyword_hits_labels_url_shortener():
    assert "url_shortener" in inference.keyword_hits("entra a https://bit.ly/abc123")


def test_keyword_hits_empty_for_benign_text():
    assert inference.keyword_hits("hola, nos vemos el martes para almorzar") == []


# --- risk_from_score ----------------------------------------------------
@pytest.mark.parametrize(
    "score,expected",
    [(0, "safe"), (39, "safe"), (40, "warning"), (59, "warning"), (60, "phishing"), (100, "phishing")],
)
def test_risk_from_score(score, expected):
    assert inference.risk_from_score(score) == expected


# --- compute_score ----------------------------------------------------
def test_compute_score_scales_local_probability():
    assert inference.compute_score({"phishing_score": 0.0}, {}, None) == 0
    assert inference.compute_score({"phishing_score": 0.9}, {}, None) == 90


def test_compute_score_floor_on_safebrowsing_threat():
    assert inference.compute_score({"phishing_score": 0.1}, {"has_threats": True}, None) == 70


def test_compute_score_llm_phishing_raises_floor():
    assert inference.compute_score({"phishing_score": 0.1}, {}, {"verdict": "phishing"}) == 80


def test_compute_score_llm_safe_caps_value():
    assert inference.compute_score({"phishing_score": 0.9}, {}, {"verdict": "safe"}) == 30


def test_compute_score_clamped_to_0_100():
    assert 0 <= inference.compute_score({"phishing_score": 5.0}, {}, None) <= 100


# --- analyze_message --------------------------------------------------
def test_analyze_message_shape():
    out = inference.analyze_message("verifica tu cuenta urgente banco haz clic aqui")
    assert out["engine"] == "nb"
    assert out["label"] in ("phishing", "legit")
    assert 0.0 <= out["phishing_score"] <= 1.0
    assert isinstance(out["keywords"], list)


# --- safebrowsing.extract_urls -------------------------------------
def test_extract_urls_adds_scheme_and_dedupes():
    urls = safebrowsing.extract_urls("mira a.com y http://a.com y tambien b.org/login")
    assert urls == ["http://a.com", "http://b.org/login"]


def test_extract_urls_empty():
    assert safebrowsing.extract_urls("") == []


def test_check_urls_no_key_returns_no_threats(monkeypatch):
    monkeypatch.setattr(safebrowsing, "GSB_KEY", "")
    res = safebrowsing.check_urls("visita http://ejemplo.com")
    assert res["has_threats"] is False
    assert res["urls"] == ["http://ejemplo.com"]


# --- openrouter.call_openrouter ----------------------------------
def test_call_openrouter_disabled_returns_none(monkeypatch):
    monkeypatch.setenv("USE_OPENROUTER", "false")
    monkeypatch.setenv("OPENROUTER_API_KEY", "whatever")
    assert openrouter.call_openrouter("hola") is None


def test_call_openrouter_no_key_returns_none(monkeypatch):
    monkeypatch.setenv("USE_OPENROUTER", "true")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    assert openrouter.call_openrouter("hola") is None
