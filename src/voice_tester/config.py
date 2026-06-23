from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ASSESSMENT_NUMBER = "+18054398008"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    gemini_api_key: str = ""
    live_model: str = "gemini-2.5-flash-native-audio-preview-12-2025"
    live_voice: str = "Kore"
    analysis_model: str = "gemini-2.5-flash-lite"

    signalwire_space_url: str = ""
    signalwire_project_id: str = ""
    signalwire_api_token: str = ""
    signalwire_from_number: str = ""
    public_base_url: str = ""

    allowed_test_number: str = Field(default=ASSESSMENT_NUMBER)
    data_dir: Path = Path("artifacts")
    max_call_seconds: int = Field(default=240, ge=30, le=600)
    log_level: str = "INFO"

    @field_validator("allowed_test_number")
    @classmethod
    def lock_assessment_number(cls, value: str) -> str:
        normalized = normalize_phone(value)
        if normalized != ASSESSMENT_NUMBER:
            raise ValueError(
                f"ALLOWED_TEST_NUMBER is locked to the assessment line {ASSESSMENT_NUMBER}"
            )
        return normalized

    @field_validator("public_base_url")
    @classmethod
    def validate_public_url(cls, value: str) -> str:
        value = value.rstrip("/")
        if value:
            parsed = urlparse(value)
            if parsed.scheme != "https" or not parsed.netloc:
                raise ValueError("PUBLIC_BASE_URL must be a public https:// URL")
        return value

    @field_validator("signalwire_space_url")
    @classmethod
    def normalize_signalwire_space_url(cls, value: str) -> str:
        return value.strip().removeprefix("https://").removeprefix("http://").rstrip("/")

    def require_call_credentials(self) -> None:
        missing = [
            name
            for name, value in {
                "GEMINI_API_KEY": self.gemini_api_key,
                "SIGNALWIRE_SPACE_URL": self.signalwire_space_url,
                "SIGNALWIRE_PROJECT_ID": self.signalwire_project_id,
                "SIGNALWIRE_API_TOKEN": self.signalwire_api_token,
                "SIGNALWIRE_FROM_NUMBER": self.signalwire_from_number,
                "PUBLIC_BASE_URL": self.public_base_url,
            }.items()
            if not value
        ]
        if missing:
            raise RuntimeError(f"Missing required settings: {', '.join(missing)}")
        if normalize_phone(self.signalwire_from_number) == self.allowed_test_number:
            raise RuntimeError("SIGNALWIRE_FROM_NUMBER must not be the assessment destination")


def normalize_phone(number: str) -> str:
    value = "".join(char for char in number if char.isdigit() or char == "+")
    if not value.startswith("+"):
        raise ValueError("Phone numbers must use E.164 format, for example +13334445555")
    if value.count("+") != 1 or len(value) < 9:
        raise ValueError("Invalid E.164 phone number")
    return value


def websocket_base_url(public_base_url: str) -> str:
    parsed = urlparse(public_base_url)
    return parsed._replace(scheme="wss").geturl().rstrip("/")
