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


def test_non_local_runtime_requires_premium_first_profile() -> None:
    with pytest.raises(ValidationError, match="NEBULA_RUNTIME_PROFILE must be premium_first"):
        Settings(
            env="production",
            runtime_profile="local_dev",
            premium_provider="openai_compatible",
            premium_base_url="https://api.openai.com/v1",
            premium_api_key="secret",
            premium_model="gpt-4o-mini",
            admin_api_key="prod-admin",
            bootstrap_api_key="prod-bootstrap",
        )


def test_non_local_runtime_rejects_default_admin_key() -> None:
    with pytest.raises(ValidationError, match="NEBULA_ADMIN_API_KEY must be changed"):
        Settings(
            env="production",
            runtime_profile="premium_first",
            premium_provider="openai_compatible",
            premium_base_url="https://api.openai.com/v1",
            premium_api_key="secret",
            premium_model="gpt-4o-mini",
            admin_api_key="nebula-admin-key",
            bootstrap_api_key="prod-bootstrap",
        )


def test_non_local_runtime_rejects_default_bootstrap_key() -> None:
    with pytest.raises(ValidationError, match="NEBULA_BOOTSTRAP_API_KEY must be changed"):
        Settings(
            env="production",
            runtime_profile="premium_first",
            premium_provider="openai_compatible",
            premium_base_url="https://api.openai.com/v1",
            premium_api_key="secret",
            premium_model="gpt-4o-mini",
            admin_api_key="prod-admin",
            bootstrap_api_key="nebula-dev-key",
        )


def test_non_local_runtime_rejects_mock_premium_provider() -> None:
    with pytest.raises(ValidationError, match="NEBULA_PREMIUM_PROVIDER=mock is not allowed"):
        Settings(
            env="production",
            runtime_profile="premium_first",
            premium_provider="mock",
            premium_base_url=None,
            premium_api_key=None,
            admin_api_key="prod-admin",
            bootstrap_api_key="prod-bootstrap",
        )
