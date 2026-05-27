from backend.models import User, Slide


def test_user_model_fields():
    u = User(email="a@b.com", password_hash="h", gemini_api_key_enc=None)
    assert u.email == "a@b.com"
    assert u.gemini_api_key_enc is None


def test_slide_model_fields():
    s = Slide(user_id=1, title="T", language="vi", slide_count=10, theme="purple", content_json="[]")
    assert s.title == "T"
    assert s.slide_count == 10
