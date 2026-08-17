"""通过 Infisical HTTP API 拉 secret，并注入子进程环境。"""

from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
from pathlib import Path
from typing import Any, NamedTuple
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request

ROOT_DIR = Path(__file__).resolve().parents[1]
REPO_ENV_FILES = ("infisical.defaults.env", ".env", ".env.local")


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


def load_repo_env_files(root: Path = ROOT_DIR) -> dict[str, str]:
    loaded: dict[str, str] = {}
    for name in REPO_ENV_FILES:
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


def _combined_env(explicit: dict[str, str] | None = None) -> dict[str, str]:
    merged = load_repo_env_files()
    merged.update({key: value for key, value in os.environ.items() if value})
    if explicit:
        merged.update({key: value for key, value in explicit.items() if value})
    return merged


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


def _request_json(url: str, *, method: str = "GET", token: str | None = None, body: dict[str, Any] | None = None) -> Any:
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib_request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib_request.urlopen(request, timeout=30) as response:
            payload = response.read().decode("utf-8")
    except urllib_error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise InfisicalEnvError(f"Infisical API {exc.code} {url}: {detail[:400]}") from exc
    except urllib_error.URLError as exc:
        reason = exc.reason
        if isinstance(reason, (ssl.SSLError, ssl.SSLCertVerificationError)):
            host = urllib_parse.urlparse(url).netloc
            raise InfisicalEnvError(
                f"Infisical TLS failed for {host}: {reason}. "
                "Fix the server certificate; this script does not skip TLS verification."
            ) from exc
        raise InfisicalEnvError(f"Infisical request failed {url}: {reason}") from exc
    if not payload:
        return {}
    return json.loads(payload)


def login_universal_auth(config: InfisicalConfig) -> str:
    payload = _request_json(
        f"{config.api_url}/api/v1/auth/universal-auth/login",
        method="POST",
        body={"clientId": config.client_id, "clientSecret": config.client_secret},
    )
    token = payload.get("accessToken")
    if not token:
        raise InfisicalEnvError("Infisical Universal Auth did not return accessToken")
    return str(token)


def access_token(config: InfisicalConfig) -> str:
    if config.token:
        return config.token
    if config.client_id and config.client_secret:
        return login_universal_auth(config)
    raise InfisicalEnvError("Need INFISICAL_TOKEN or INFISICAL_CLIENT_ID + INFISICAL_CLIENT_SECRET")


def _secret_pair(item: dict[str, Any]) -> tuple[str, str] | None:
    name = item.get("secretName") or item.get("secretKey") or item.get("key")
    value = item.get("secretValue") or item.get("value")
    if not name or value is None:
        return None
    return str(name), str(value)


def fetch_secrets(config: InfisicalConfig, token: str) -> dict[str, str]:
    secrets: dict[str, str] = {}
    offset = 0
    limit = 100
    while True:
        query = urllib_parse.urlencode(
            {
                "projectId": config.project_id,
                "environment": config.environment,
                "secretPath": config.secret_path,
                "viewSecretValue": "true",
                "expandSecretReferences": "true",
                "offset": str(offset),
                "limit": str(limit),
            }
        )
        payload = _request_json(f"{config.api_url}/api/v4/secrets?{query}", token=token)
        rows = payload.get("secrets") or []
        if not isinstance(rows, list):
            raise InfisicalEnvError("Infisical secrets response is missing a list")
        for item in rows:
            if isinstance(item, dict):
                pair = _secret_pair(item)
                if pair:
                    secrets[pair[0]] = pair[1]
        if len(rows) < limit:
            break
        offset += limit
    return secrets


def merge_env(base: dict[str, str], secrets: dict[str, str]) -> dict[str, str]:
    merged = dict(base)
    for key, value in secrets.items():
        if not merged.get(key):
            merged[key] = value
    return merged


def build_injected_env(env: dict[str, str] | None = None) -> dict[str, str]:
    current = dict(env or os.environ)
    config = resolve_config(current)
    if not config.has_auth():
        return current
    if not config.api_url:
        raise InfisicalEnvError("INFISICAL_API_URL is required when Infisical auth is set")
    if not config.project_id:
        raise InfisicalEnvError("INFISICAL_PROJECT_ID is required when Infisical auth is set")
    token = access_token(config)
    return merge_env(current, fetch_secrets(config, token))


def run_child(argv: list[str], env: dict[str, str]) -> int:
    if not argv:
        raise InfisicalEnvError("missing command after `run --`")
    os.execvpe(argv[0], argv, env)
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch Infisical secrets over HTTP and run a command")
    parser.add_argument("action", choices=["run"])
    parser.add_argument("--command", default=None, help="shell command string")
    parser.add_argument("command_argv", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    try:
        injected = build_injected_env(_combined_env())
        if args.command:
            os.execvpe("/bin/bash", ["/bin/bash", "-lc", args.command], injected)
        child = list(args.command_argv)
        if child and child[0] == "--":
            child = child[1:]
        return run_child(child, injected)
    except InfisicalEnvError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
