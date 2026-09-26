"""用官方 infisicalsdk 把 /baicao 的 secret 填进进程环境。

不依赖 Infisical CLI。进程里已经有值的变量保持不变。
"""

from __future__ import annotations

import os
import ssl
from pathlib import Path
from typing import Any, NamedTuple


class InfisicalEnvError(RuntimeError):
    pass


class InfisicalConfig(NamedTuple):
    api_url: str
    project_id: str
    environment: str
    secret_path: str
    token: str | None = None
    client_id: str | None = None
    client_secret: str | None = None

    def has_auth(self) -> bool:
        return bool(self.token) or bool(self.client_id and self.client_secret)


def find_repo_root(start: Path) -> Path | None:
    for directory in (start, *start.parents):
        if (directory / "infisical.defaults.env").is_file():
            return directory
    return None


def load_repo_env_files(root: Path | None = None) -> dict[str, str]:
    if root is None:
        root = find_repo_root(Path(__file__).resolve())
    if root is None:
        return {}
    loaded: dict[str, str] = {}
    for name in ("infisical.defaults.env", ".env", ".env.local"):
        path = root / name
        if not path.is_file():
            continue
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if key.startswith("export "):
                key = key[len("export ") :].strip()
            loaded[key] = value.strip().strip("'").strip('"')
    return loaded


def resolve_config(env: dict[str, str]) -> InfisicalConfig:
    return InfisicalConfig(
        api_url=(env.get("INFISICAL_API_URL") or "").rstrip("/"),
        project_id=env.get("INFISICAL_PROJECT_ID") or "",
        environment=env.get("INFISICAL_ENV") or "dev",
        secret_path=env.get("INFISICAL_SECRET_PATH") or env.get("INFISICAL_PATH") or "/",
        token=env.get("INFISICAL_TOKEN") or env.get("INFISICAL_ACCESS_TOKEN"),
        client_id=env.get("INFISICAL_CLIENT_ID") or env.get("INFISICAL_UNIVERSAL_AUTH_CLIENT_ID"),
        client_secret=env.get("INFISICAL_CLIENT_SECRET")
        or env.get("INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET"),
    )


def _pairs_from_list(response: Any) -> dict[str, str]:
    secrets: dict[str, str] = {}
    for item in getattr(response, "secrets", []) or []:
        key = getattr(item, "secretKey", None)
        value = getattr(item, "secretValue", None)
        if key and value is not None:
            secrets[str(key)] = str(value)
    for imported in getattr(response, "imports", []) or []:
        for item in getattr(imported, "secrets", []) or []:
            key = getattr(item, "secretKey", None)
            value = getattr(item, "secretValue", None)
            if key and value is not None:
                secrets.setdefault(str(key), str(value))
    return secrets


def fetch_secrets(config: InfisicalConfig, *, client_factory: Any = None) -> dict[str, str]:
    if client_factory is None:
        from infisical_sdk import InfisicalSDKClient

        client_factory = InfisicalSDKClient
    kwargs: dict[str, Any] = {"host": config.api_url, "cache_ttl": 0}
    if config.token:
        kwargs["token"] = config.token
    client = None
    listed = None
    try:
        client = client_factory(**kwargs)
        if not config.token:
            if not config.client_id or not config.client_secret:
                raise InfisicalEnvError(
                    "Need INFISICAL_CLIENT_ID + INFISICAL_CLIENT_SECRET"
                )
            client.auth.universal_auth.login(config.client_id, config.client_secret)
        listed = client.secrets.list_secrets(
            environment_slug=config.environment,
            secret_path=config.secret_path,
            project_id=config.project_id,
            expand_secret_references=True,
            view_secret_value=True,
            include_imports=True,
        )
    except ssl.SSLError as exc:
        raise InfisicalEnvError(f"Infisical TLS failed: {exc}") from exc
    except InfisicalEnvError:
        raise
    except Exception as exc:
        text = str(exc)
        if "SSL" in type(exc).__name__ or "certificate" in text.lower():
            raise InfisicalEnvError(f"Infisical TLS failed: {text}") from exc
        raise InfisicalEnvError(f"Infisical SDK request failed: {text}") from exc
    finally:
        if client is not None:
            close = getattr(client, "close", None)
            if callable(close):
                close()
    if listed is None:
        raise InfisicalEnvError("Infisical SDK request failed")
    return _pairs_from_list(listed)


def merge_env(base: dict[str, str], secrets: dict[str, str]) -> dict[str, str]:
    merged = dict(base)
    for key, value in secrets.items():
        if not merged.get(key):
            merged[key] = value
    return merged


def build_injected_env(
    env: dict[str, str] | None = None,
    *,
    client_factory: Any = None,
) -> dict[str, str]:
    current = dict(env or os.environ)
    config = resolve_config(current)
    if not config.has_auth():
        return current
    if not config.api_url:
        raise InfisicalEnvError("INFISICAL_API_URL is required when Infisical auth is set")
    if not config.project_id:
        raise InfisicalEnvError("INFISICAL_PROJECT_ID is required when Infisical auth is set")
    merged = merge_env(current, fetch_secrets(config, client_factory=client_factory))
    merged["INFISICAL_SECRETS_LOADED"] = "1"
    return merged


def apply_to_process_env() -> None:
    """把仓库 env 文件和 Infisical secret 写进当前进程。已有环境变量优先。"""
    if os.environ.get("INFISICAL_SECRETS_LOADED"):
        return
    base = load_repo_env_files()
    base.update({key: value for key, value in os.environ.items() if value})
    injected = build_injected_env(base)
    for key, value in injected.items():
        if value and not os.environ.get(key):
            os.environ[key] = value
