from __future__ import annotations

import difflib
import sys
from typing import NamedTuple

SUPPORTED = {
    "help": {"help"},
    "deps": {"up", "down", "status", "logs", "help"},
    "api": {"up", "down", "restart", "status", "logs", "attach", "help"},
    "web": {"up", "down", "restart", "status", "logs", "attach", "help"},
    "stack": {"up", "down", "restart", "status", "attach", "help"},
}

RESOURCE_DESCRIPTIONS = {
    "deps": "PostgreSQL / Neo4j / Redis 等依赖服务",
    "api": "FastAPI 后端服务",
    "web": "React 前端服务",
    "stack": "本地联调整体运行面",
}


class CLIResult(NamedTuple):
    exit_code: int
    stdout: str = ""
    stderr: str = ""


def _example_lines(resource: str | None = None) -> list[str]:
    if resource is None:
        return [
            "Examples:",
            "  make help",
            "  make deps help",
            "  make api up",
            "  make stack status",
        ]

    return [
        "Examples:",
        f"  make {resource} help",
        f"  make {resource} up",
        f"  make {resource} status",
    ]


def _closest_match(value: str, options: list[str]) -> str | None:
    matches = difflib.get_close_matches(value, options, n=1, cutoff=0.5)
    return matches[0] if matches else None


def _render_root_help() -> str:
    lines = [
        "BaiCao local runtime commands",
        "",
        "Supported resources:",
    ]

    for resource in ("deps", "api", "web", "stack"):
        lines.append(f"  {resource:<5} {RESOURCE_DESCRIPTIONS[resource]}")

    lines.extend(["", *_example_lines()])
    return "\n".join(lines)


def _render_resource_help(resource: str) -> str:
    actions = sorted(SUPPORTED[resource] - {"help"})
    lines = [
        f"Resource: {resource}",
        "",
        "Supported actions:",
    ]
    lines.extend(f"  {action}" for action in actions)
    lines.extend(["", *_example_lines(resource)])
    return "\n".join(lines)


def _render_unknown_resource(resource: str) -> str:
    suggestion = _closest_match(resource, ["deps", "api", "web", "stack"])
    lines = [f"Unknown resource: {resource}"]
    if suggestion:
        lines.append(f"Did you mean: {suggestion}")
    lines.extend(
        [
            "Run `make help` to see supported resources.",
            "",
            *_example_lines(),
        ]
    )
    return "\n".join(lines)


def _render_unknown_action(resource: str, action: str) -> str:
    valid_actions = sorted(SUPPORTED[resource] - {"help"})
    suggestion = _closest_match(action, valid_actions)
    lines = [f"Unknown action: {action}"]
    if suggestion:
        lines.append(f"Did you mean: {suggestion}")
    lines.extend(
        [
            f"Run `make {resource} help` to see supported actions.",
            "",
            *_example_lines(resource),
        ]
    )
    return "\n".join(lines)


def _render_unexpected_arguments(
    resource: str,
    extra_args: list[str],
    action: str | None = None,
) -> str:
    extra_text = " ".join(extra_args)

    if resource == "help":
        lines = [
            f"Unexpected extra arguments: {extra_text}",
            "Root help does not accept additional positional arguments.",
            "Run `make help` to see supported resources.",
            "",
            *_example_lines(),
        ]
        return "\n".join(lines)

    lines = [f"Unexpected extra arguments: {extra_text}"]
    if action == "help":
        lines.append(f"`{resource} help` does not accept additional positional arguments.")
    else:
        lines.append(
            f"`{resource} {action}` does not accept additional positional arguments in Task 1."
        )
    lines.extend(
        [
            f"Run `make {resource} help` to see supported actions.",
            "",
            *_example_lines(resource),
        ]
    )
    return "\n".join(lines)


def run_cli_result(argv: list[str], env: dict[str, str] | None = None) -> CLIResult:
    del env

    args = list(argv)
    resource = args[0] if args else "help"
    action = args[1] if len(args) > 1 else "help"

    if resource == "help" and len(args) > 1:
        return CLIResult(
            exit_code=2,
            stderr=_render_unexpected_arguments("help", args[1:]),
        )

    if resource not in SUPPORTED:
        return CLIResult(exit_code=2, stderr=_render_unknown_resource(resource))

    if len(args) > 2:
        return CLIResult(
            exit_code=2,
            stderr=_render_unexpected_arguments(resource, args[2:], action=action),
        )

    if resource == "help":
        return CLIResult(exit_code=0, stdout=_render_root_help())

    if action == "help":
        return CLIResult(exit_code=0, stdout=_render_resource_help(resource))

    if action not in SUPPORTED[resource]:
        return CLIResult(exit_code=2, stderr=_render_unknown_action(resource, action))

    lines = [
        f"`{resource} {action}` is not implemented yet.",
        "This task only provides the runtime command skeleton and guidance surface.",
        "",
        *_example_lines(resource),
    ]
    return CLIResult(exit_code=1, stderr="\n".join(lines))


def run_cli(argv: list[str], env: dict[str, str] | None = None) -> tuple[int, str]:
    result = run_cli_result(argv, env=env)
    output_parts = [part for part in (result.stdout, result.stderr) if part]
    return result.exit_code, "\n".join(output_parts)


def main(argv: list[str] | None = None) -> int:
    result = run_cli_result(list(sys.argv[1:] if argv is None else argv))
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
