import os

from pydantic_settings import SettingsConfigDict

from app.core.config import Settings


class _EnvOnlySettings(Settings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")


def test_openai_key_reads_single_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "fw-from-openai")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.fireworks.ai/inference/v1")
    monkeypatch.setenv("OPENAI_MODEL", "accounts/fireworks/models/deepseek-v4-flash-0731")
    settings = _EnvOnlySettings()
    assert settings.openai_api_key == "fw-from-openai"
    assert settings.openai_base_url == "https://api.fireworks.ai/inference/v1"
    assert not hasattr(settings, "anthropic_auth_token")


def test_get_settings_applies_infisical_sdk_result(monkeypatch):
    from app.core import config
    from app.core import infisical_secrets

    monkeypatch.delenv("INFISICAL_SECRETS_LOADED", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.setenv("INFISICAL_CLIENT_ID", "client")
    monkeypatch.setenv("INFISICAL_CLIENT_SECRET", "secret")
    monkeypatch.setenv("INFISICAL_API_URL", "https://app.infisical.com")
    monkeypatch.setenv("INFISICAL_PROJECT_ID", "proj-1")

    def fake_build(env: dict[str, str] | None = None, *, client_factory=None):
        del client_factory
        assert env is not None
        assert env["INFISICAL_CLIENT_ID"] == "client"
        merged = dict(env)
        merged["OPENAI_MODEL"] = "from-sdk"
        merged["INFISICAL_SECRETS_LOADED"] = "1"
        return merged

    monkeypatch.setattr(infisical_secrets, "build_injected_env", fake_build)
    config.get_settings.cache_clear()
    try:
        settings = config.get_settings()
        assert settings.openai_model == "from-sdk"
        assert os.environ["INFISICAL_SECRETS_LOADED"] == "1"
    finally:
        config.get_settings.cache_clear()


def test_typesafe_settings_read_env(monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", "ts-key")
    monkeypatch.setenv("TYPESAFE_BASE_URL", "https://typesafe.example/v1")
    monkeypatch.setenv("TYPESAFE_MODEL", "decision-model-preview")
    settings = _EnvOnlySettings()
    assert settings.typesafe_api_key == "ts-key"
    assert settings.typesafe_base_url == "https://typesafe.example/v1"
    assert settings.typesafe_model == "decision-model-preview"
