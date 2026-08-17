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
