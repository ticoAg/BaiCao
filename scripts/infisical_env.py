"""用官方 infisicalsdk 拉 secret，并注入子进程环境。不调用 Infisical CLI。"""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
_MODULE_PATH = ROOT_DIR / "packages" / "api" / "app" / "core" / "infisical_secrets.py"


def _load_secrets_module():
    spec = importlib.util.spec_from_file_location("infisical_secrets", _MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {_MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


http = _load_secrets_module()
InfisicalEnvError = http.InfisicalEnvError
build_injected_env = http.build_injected_env
load_repo_env_files = http.load_repo_env_files
resolve_config = http.resolve_config


def _combined_env(explicit: dict[str, str] | None = None) -> dict[str, str]:
    merged = load_repo_env_files(ROOT_DIR)
    merged.update({key: value for key, value in os.environ.items() if value})
    if explicit:
        merged.update({key: value for key, value in explicit.items() if value})
    return merged


def run_child(argv: list[str], env: dict[str, str]) -> int:
    if not argv:
        raise InfisicalEnvError("missing command after `run --`")
    os.execvpe(argv[0], argv, env)
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch Infisical secrets with the Python SDK and run a command")
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
