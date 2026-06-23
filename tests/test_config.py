import pytest

from voice_tester.config import ASSESSMENT_NUMBER, Settings, normalize_phone, websocket_base_url


def test_assessment_number_is_locked(monkeypatch):
    monkeypatch.setenv("ALLOWED_TEST_NUMBER", "+15551234567")
    with pytest.raises(ValueError, match="locked"):
        Settings(_env_file=None)


def test_default_assessment_number():
    settings = Settings(_env_file=None)
    assert settings.allowed_test_number == ASSESSMENT_NUMBER


def test_phone_normalization():
    assert normalize_phone("+1 (805) 439-8008") == ASSESSMENT_NUMBER


def test_websocket_url():
    assert websocket_base_url("https://example.com") == "wss://example.com"

