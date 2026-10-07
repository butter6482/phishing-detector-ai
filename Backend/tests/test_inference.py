import pytest

from src import inference
from src.inference import (
    MODEL_DIR,
    compute_score,
    keyword_hits,
    normalize,
    risk_from_score,
)

PHISHING_TEXT = "URGENTE: tu cuenta fue suspendida. Verifica tu contrasena en http://192.168.0.1/login"
LEGIT_TEXT = "Hola equipo, adjunto las notas de la reunion de ayer. Nos vemos el lunes."


def test_normalize_strips_accents_and_leetspeak():
    assert normalize("V3rific@ tu Contraseña") == "verifica tu contrasena"


def test_keyword_hits_detects_phishing_signals():
    hits = keyword_hits(PHISHING_TEXT)
    assert len(hits) >= 3, "expected several phishing signals (urgency, suspension, verification...)"


@pytest.mark.xfail(
    strict=True,
    reason="Known bug: normalize() applies the leetspeak map to digits, so 192.168.0.1 becomes "
    "l92.l68.o.l and the ip_url pattern never matches. Remove this marker once fixed.",
)
def test_keyword_hits_detects_ip_urls():
    assert "ip_url" in keyword_hits("entra aqui http://192.168.0.1/login")


def test_keyword_hits_has_no_duplicates():
    hits = keyword_hits("urgente urgente urgente verifica verifica")
    assert len(hits) == len(set(hits))


def test_model_artifacts_resolve_independent_of_cwd(monkeypatch, tmp_path):
    # Regression: the model used to be loaded from a CWD-relative "backend/models" path
    # that silently failed on Linux. It must resolve from the package location instead.
    monkeypatch.chdir(tmp_path)
    assert (MODEL_DIR / "modelo_entrenado.pkl").is_file()
    assert (MODEL_DIR / "vectorizer.pkl").is_file()
    monkeypatch.setattr(inference, "_model", None)
    monkeypatch.setattr(inference, "_vec", None)
    model, vec = inference.load_model()
    assert model is not None and vec is not None


def test_model_ranks_phishing_above_legit():
    assert inference.predict_proba(PHISHING_TEXT) > inference.predict_proba(LEGIT_TEXT)


def test_probability_is_bounded():
    for text in (PHISHING_TEXT, LEGIT_TEXT, "x"):
        assert 0.0 <= inference.predict_proba(text) <= 1.0


def test_heuristic_fallback_when_model_unavailable(monkeypatch):
    monkeypatch.setattr(inference, "load_model", lambda: (None, None))
    low = inference.predict_proba(LEGIT_TEXT)
    high = inference.predict_proba(PHISHING_TEXT)
    assert high > low
    assert high <= 0.98


def test_compute_score_safebrowsing_threat_raises_floor():
    nb = {"phishing_score": 0.05}
    assert compute_score(nb, {"has_threats": True}, None) >= 70


def test_compute_score_llm_verdict_adjusts():
    nb = {"phishing_score": 0.5}
    assert compute_score(nb, {"has_threats": False}, {"verdict": "phishing"}) >= 80
    assert compute_score(nb, {"has_threats": False}, {"verdict": "safe"}) <= 30


def test_compute_score_is_clamped():
    assert 0 <= compute_score({"phishing_score": 5.0}, {}, None) <= 100
    assert 0 <= compute_score({"phishing_score": -3.0}, {}, None) <= 100


def test_risk_thresholds():
    assert risk_from_score(0) == "safe"
    assert risk_from_score(39) == "safe"
    assert risk_from_score(40) == "warning"
    assert risk_from_score(59) == "warning"
    assert risk_from_score(60) == "phishing"
