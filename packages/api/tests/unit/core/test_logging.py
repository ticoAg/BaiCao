from unittest.mock import MagicMock

import pytest

from app.core.config import Settings


def test_settings_supports_log_format_and_level() -> None:
    settings = Settings(log_level="DEBUG", log_format="json")

    assert settings.log_level == "DEBUG"
    assert settings.log_format == "json"


def test_configure_logging_enables_json_serialization(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core import logging as logging_module

    remove_mock = MagicMock()
    add_mock = MagicMock()
    monkeypatch.setattr(logging_module.logger, "remove", remove_mock)
    monkeypatch.setattr(logging_module.logger, "add", add_mock)

    settings = Settings(log_level="INFO", log_format="json")

    logging_module.configure_logging(settings)

    remove_mock.assert_called_once()
    add_mock.assert_called_once()
    assert add_mock.call_args.kwargs["serialize"] is True
    assert add_mock.call_args.kwargs["level"] == "INFO"


def test_configure_logging_uses_text_formatter(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core import logging as logging_module

    remove_mock = MagicMock()
    add_mock = MagicMock()
    monkeypatch.setattr(logging_module.logger, "remove", remove_mock)
    monkeypatch.setattr(logging_module.logger, "add", add_mock)

    settings = Settings(log_level="WARNING", log_format="text")

    logging_module.configure_logging(settings)

    assert add_mock.call_args.kwargs["serialize"] is False
    assert "{level:" in add_mock.call_args.kwargs["format"]
