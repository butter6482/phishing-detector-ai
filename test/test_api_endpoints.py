def test_home_ok():
    import api
    client = api.app.test_client()
    res = client.get("/")
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert "provider" in data

def test_predict_ok():
    import api
    client = api.app.test_client()
    res = client.post("/predict", json={"message": "hola prueba"})
    assert res.status_code == 200
    data = res.get_json()
    assert "label" in data
    assert "phishing_score" in data

def test_predict_400():
    import api
    client = api.app.test_client()
    res = client.post("/predict", json={})
    assert res.status_code == 400
