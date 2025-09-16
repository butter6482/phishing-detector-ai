import json

def test_find_urls_basic():
    import streamlit_app as sa
    txt = "Visita https://example.com y http://mal.com/page."
    urls = sa.find_urls(txt)
    assert "https://example.com" in urls and "http://mal.com/page" in urls

def test_verificar_urls_ok(monkeypatch):
    import streamlit_app as sa
    class _Resp:
        def raise_for_status(self): pass
        def json(self):
            return {"matches":[{"threat":{"url":"http://mal.com/page"}}]}
    def fake_post(url, json=None, timeout=12):
        return _Resp()
    monkeypatch.setattr(sa.requests, "post", fake_post)
    malos, err = sa.verificar_urls_con_google("hola http://mal.com/page adios")
    assert err is None and malos == ["http://mal.com/page"]

def test_llm_analyze_parsing(monkeypatch):
    import streamlit_app as sa
    class _Resp:
        def raise_for_status(self): pass
        def json(self):
            return {"choices":[{"message":{"content": json.dumps({
                "label": "legit", "score": 0.2, "reasons": [], "explanation":"OK"
            })}}]}
    def fake_post(url, headers=None, json=None, timeout=30):
        return _Resp()
    monkeypatch.setattr(sa.requests, "post", fake_post)
    res = sa.llm_analyze("hola", "Español")
    assert res["label"] in {"phishing","legit","uncertain"}
    assert 0.0 <= float(res["score"]) <= 1.0

def test_fusion_rules():
    import streamlit_app as sa
    d1 = sa.fusion(0.85, "phishing", None)
    assert d1["engine"] == "nb" and d1["label"] == "phishing"
    llm = {"label":"legit","score":0.3,"explanation":"...", "reasons":["x"]}
    d2 = sa.fusion(0.5, "phishing", llm)
    assert d2["engine"] == "llm" and d2["label"] == "legit"
