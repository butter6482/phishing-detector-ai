from src import safebrowsing
from src.safebrowsing import check_urls, extract_urls


def test_extract_urls_normalizes_and_dedupes():
    text = "visita example.com y tambien https://example.org/a?b=1 y example.com otra vez"
    urls = extract_urls(text)
    assert "http://example.com" in urls
    assert "https://example.org/a?b=1" in urls
    assert len(urls) == len(set(urls))


def test_extract_urls_empty_input():
    assert extract_urls("") == []
    assert extract_urls("sin enlaces aqui") == []


def test_check_urls_without_key_skips_network(monkeypatch):
    monkeypatch.setattr(safebrowsing, "GSB_KEY", "")

    def boom(*a, **k):
        raise AssertionError("network must not be used without an API key")

    monkeypatch.setattr(safebrowsing.httpx, "Client", boom)
    result = check_urls("mira https://example.com")
    assert result["has_threats"] is False
    assert result["urls"] == ["https://example.com"]


def test_check_urls_reports_matches(monkeypatch):
    monkeypatch.setattr(safebrowsing, "GSB_KEY", "test-key")

    class FakeResp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"matches": [{"threatType": "SOCIAL_ENGINEERING"}]}

    class FakeClient:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def post(self, *a, **k):
            return FakeResp()

    monkeypatch.setattr(safebrowsing.httpx, "Client", FakeClient)
    result = check_urls("http://malicious.example")
    assert result["has_threats"] is True
    assert result["matches"][0]["threatType"] == "SOCIAL_ENGINEERING"


def test_check_urls_fails_open_on_network_error(monkeypatch):
    monkeypatch.setattr(safebrowsing, "GSB_KEY", "test-key")

    class BrokenClient:
        def __init__(self, *a, **k):
            raise RuntimeError("network down")

    monkeypatch.setattr(safebrowsing.httpx, "Client", BrokenClient)
    result = check_urls("http://example.com")
    assert result["has_threats"] is False
    assert result["matches"] == []
