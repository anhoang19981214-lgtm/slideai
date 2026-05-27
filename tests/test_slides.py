import json
from unittest.mock import patch, MagicMock


MOCK_SLIDES = [
    {"index": 1, "type": "cover", "title": "AI in Education", "subtitle": "The future is now"},
    {"index": 2, "type": "content", "title": "Overview", "bullets": ["Point 1", "Point 2", "Point 3"]},
    {"index": 3, "type": "conclusion", "title": "Conclusion", "summary": "AI transforms education"},
]


def _register_and_get_token(client):
    r = client.post("/auth/register", json={"email": "u@test.com", "password": "pass123"})
    token = r.json()["access_token"]
    client.put(
        "/auth/api-key",
        json={"gemini_api_key": "AIzaFake"},
        headers={"Authorization": f"Bearer {token}"},
    )
    return token


def test_generate_slide(client):
    token = _register_and_get_token(client)
    mock_response = MagicMock()
    mock_response.text = json.dumps(MOCK_SLIDES)

    with patch("backend.slides.genai.GenerativeModel") as mock_model_cls:
        mock_model_cls.return_value.generate_content.return_value = mock_response
        r = client.post(
            "/slides/generate",
            json={"topic": "AI in Education", "slide_count": 5, "language": "en", "theme": "purple"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert r.status_code == 200
    data = r.json()
    assert "slide_id" in data
    assert isinstance(data["slide_id"], int)
    assert len(data["slides"]) == 3
    assert data["slides"][0]["type"] == "cover"
    assert data["slides"][0]["title"] == "AI in Education"


def test_generate_requires_api_key(client):
    r = client.post("/auth/register", json={"email": "nokey@test.com", "password": "pass123"})
    token = r.json()["access_token"]
    r = client.post(
        "/slides/generate",
        json={"topic": "Test", "slide_count": 5, "language": "vi", "theme": "blue"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 400


def test_generate_slide_count_validation(client):
    token = _register_and_get_token(client)
    r = client.post(
        "/slides/generate",
        json={"topic": "Test", "slide_count": 30, "language": "vi", "theme": "blue"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 422


def test_generate_requires_auth(client):
    r = client.post(
        "/slides/generate",
        json={"topic": "Test", "slide_count": 5, "language": "vi", "theme": "purple"},
    )
    assert r.status_code == 403
