def test_register(client):
    r = client.post("/auth/register", json={"email": "a@b.com", "password": "pass123"})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_register_duplicate_email(client):
    client.post("/auth/register", json={"email": "a@b.com", "password": "pass123"})
    r = client.post("/auth/register", json={"email": "a@b.com", "password": "other"})
    assert r.status_code == 400


def test_login(client):
    client.post("/auth/register", json={"email": "a@b.com", "password": "pass123"})
    r = client.post("/auth/login", json={"email": "a@b.com", "password": "pass123"})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_wrong_password(client):
    client.post("/auth/register", json={"email": "a@b.com", "password": "pass123"})
    r = client.post("/auth/login", json={"email": "a@b.com", "password": "wrong"})
    assert r.status_code == 401


def test_get_me(client):
    r = client.post("/auth/register", json={"email": "a@b.com", "password": "pass123"})
    token = r.json()["access_token"]
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == "a@b.com"
    assert data["has_api_key"] is False


def test_update_api_key(client):
    r = client.post("/auth/register", json={"email": "a@b.com", "password": "pass123"})
    token = r.json()["access_token"]
    r = client.put(
        "/auth/api-key",
        json={"gemini_api_key": "AIzaTestKey123"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.json()["has_api_key"] is True
