import logging

import pytest

from app.config import Settings


def test_settings_parse_cors_string():
    settings = Settings(CORS_ORIGINS="https://a.example, https://b.example ")
    assert settings.CORS_ORIGINS == ["https://a.example", "https://b.example"]


def test_settings_warn_on_default_secret(caplog: pytest.LogCaptureFixture):
    caplog.set_level(logging.WARNING)
    settings = Settings(SECRET_KEY="change-me-in-prod")
    assert settings.SECRET_KEY == "change-me-in-prod"
    assert "SECRET_KEY is using default value" in caplog.text


def test_settings_validate_custom_secret(caplog: pytest.LogCaptureFixture):
    caplog.set_level(logging.INFO)
    secret_value = "A-secure-secret-value-with-length-1234567890"
    settings = Settings(SECRET_KEY=secret_value)
    assert settings.SECRET_KEY == secret_value
    assert "SECRET_KEY validation passed" in caplog.text
