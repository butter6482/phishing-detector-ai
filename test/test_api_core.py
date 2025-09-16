import json

class _FakeResp:
    def __init__(self, payload):
        self._payload = payload
    def raise_for_status(self): pass
    def json(self): return self._payload

def test_analyze_gray_uses_llm(monkeypatch):
    import Backend.api as api
    payload = {
        "choices": [{
            "message": {
                "content": json.dumps({
                    "label": "phishing",
                    "score": 0.85,
                    "reasons": ["urgent"],
                    "explanation": "Texto sospechoso"
                })
            }
        }]
    }
    def fake_post(url, headers=None, json=None, timeout=30):
        return _FakeResp(payload)

    monkeypatch.setattr(api.requests, "post", fake_post)

    client = api.app.test_client()
    res = client.post("/analyze", json={"message": "verifica urgente", "lang": "es"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["llm"] is not None
    assert data["final"]["engine"] in ("llm", "hybrid_disagree")
