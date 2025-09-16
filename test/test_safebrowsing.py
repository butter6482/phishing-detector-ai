import os
from Backend.src import safebrowsing as sb


def test_extract_urls_basic():
    text = "Visita ejemplo.com y https://openai.com/docs ahora. Ojo con bad-site.xyz/login"
    urls = sb.extract_urls(text)
    assert any("http://ejemplo.com" == u or "http://ejemplo.com/" == u.rstrip("/") for u in urls)
    assert any(u.startswith("https://openai.com" ) for u in urls)
    assert any("http://bad-site.xyz/login" == u for u in urls)


def test_check_urls_mocked(monkeypatch):
    monkeypatch.setenv("GOOGLE_SAFE_BROWSING_KEY", "dummy")

    class DummyResp:
        def __init__(self, data):
            self._data = data

        def raise_for_status(self):
            return None

        def json(self):
            return self._data

    class DummyClient:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def post(self, url, json):
            # Simula una coincidencia de amenazas
            return DummyResp({
                "matches": [
                    {
                        "threatType": "SOCIAL_ENGINEERING",
                        "platformType": "ANY_PLATFORM",
                        "threat": {"url": json["threatInfo"]["threatEntries"][0]["url"]},
                    }
                ]
            })

    # parchea httpx.Client usado internamente
    import httpx
    monkeypatch.setattr(httpx, "Client", DummyClient)

    res = sb.check_urls("Cuidado con http://malicioso.xyz/login")
    assert res["has_threats"] is True
    assert res["matches"]
