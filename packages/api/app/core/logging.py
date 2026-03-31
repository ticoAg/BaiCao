import sys
from collections.abc import Mapping
from typing import Any

from loguru import logger


TEXT_LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{extra[component]}</cyan> | "
    "<level>{message}</level>"
)


def configure_logging(settings: Any) -> None:
    log_level = str(getattr(settings, "log_level", "INFO")).upper()
    log_format = str(getattr(settings, "log_format", "text")).lower()
    serialize = log_format == "json"

    logger.remove()
    logger.configure(extra={"component": "app"})
    sink_kwargs: dict[str, Any] = {
        "sink": sys.stderr,
        "level": log_level,
        "serialize": serialize,
        "backtrace": False,
        "diagnose": False,
    }
    if not serialize:
        sink_kwargs["format"] = TEXT_LOG_FORMAT
    logger.add(**sink_kwargs)


def get_logger(name: str, **extra: Any):
    payload: Mapping[str, Any] = {"component": name, **extra}
    return logger.bind(**payload)
