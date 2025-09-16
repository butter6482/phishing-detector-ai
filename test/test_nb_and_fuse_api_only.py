def test_nb_predict_and_fuse_api_only():
    import Backend.api as api
    s, lbl = api.nb_predict("texto de prueba")
    assert 0.0 <= s <= 1.0
    assert lbl in ("phishing", "legit")
    d = api.fuse(s, lbl, {"label":"phishing","score":0.8,"reasons":[],"explanation":"ok"})
    assert d["engine"] in ("nb", "llm", "hybrid_disagree")
