import pytest
from pydantic import ValidationError

from nebula.core.config import Settings


def test_openai_compatible_provider_requires_api_key() -> None:
    with pytest.raises(ValidationError, match="NEBULA_PREMIUM_API_KEY is required"):
        Settings(
            premium_provider="openai_compatible",
            premium_base_url="https://api.openai.com/v1",
            premium_api_key="",
            premium_model="gpt-4o-mini",
        )


def test_mock_provider_does_not_require_premium_credentials() -> None:
    settings = Settings(
        premium_provider="mock",
        premium_base_url=None,
        premium_api_key=None,
    )

    assert settings.premium_provider == "mock"
