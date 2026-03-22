from __future__ import annotations

import difflib
import sys

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


def run_cli(argv: list[str], env: dict[str, str] | None = None) -> tuple[int, str]:
    del env

    resource = argv[0] if argv else "help"
    action = argv[1] if len(argv) > 1 else "help"

    if resource == "help":
        return 0, _render_root_help()

    if resource not in SUPPORTED:
        return 2, _render_unknown_resource(resource)

    if action == "help":
        return 0, _render_resource_help(resource)

    if action not in SUPPORTED[resource]:
        return 2, _render_unknown_action(resource, action)

    lines = [
        f"`{resource} {action}` is not implemented yet.",
        "This task only provides the runtime command skeleton and guidance surface.",
        "",
        *_example_lines(resource),
    ]
    return 1, "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    exit_code, output = run_cli(list(sys.argv[1:] if argv is None else argv))
    if output:
        print(output)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
