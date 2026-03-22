from __future__ import annotations

import difflib
import os
import shlex
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable, NamedTuple
from urllib import error as urllib_error
from urllib import request as urllib_request

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


DEPS_SERVICES = ("postgres", "neo4j", "redis")
DEPS_PORTS = (
    ("postgres", 15433),
    ("neo4j", 17687),
    ("redis", 16380),
)
DEFAULT_ENV = {
    "LINES": "80",
    "SESSION": "baicao-dev",
    "API_PORT": "8000",
    "WEB_PORT": "3000",
    "DATABASE_URL": "postgresql+asyncpg://baicao:baicao_password@localhost:15433/baicao",
    "DATABASE_PORT": "15433",
    "NEO4J_URI": "bolt://localhost:17687",
    "NEO4J_USER": "neo4j",
    "NEO4J_PASSWORD": "neo4j_password",
    "REDIS_URL": "redis://localhost:16380",
}
ROOT_DIR = Path(__file__).resolve().parents[1]
API_DIR = ROOT_DIR / "packages" / "api"
WEB_DIR = ROOT_DIR / "packages" / "web"


class CommandResult(NamedTuple):
    exit_code: int
    stdout: str = ""
    stderr: str = ""


CLIResult = CommandResult
RunCommand = Callable[..., CommandResult]
PortChecker = Callable[[str, int], bool]


class RuntimeContext(NamedTuple):
    env: dict[str, str]
    run_command: RunCommand
    port_checker: PortChecker


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


def _merge_env(env: dict[str, str] | None) -> dict[str, str]:
    merged = DEFAULT_ENV.copy()
    merged.update(os.environ)
    if env:
        merged.update(env)
    return merged


def _default_run_command(
    cmd: list[str],
    *,
    cwd: str | None = None,
    env: dict[str, str] | None = None,
) -> CommandResult:
    completed = subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    return CommandResult(completed.returncode, completed.stdout, completed.stderr)


def _default_port_checker(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.2):
            return True
    except OSError:
        return False


def _compose_cmd(*parts: str) -> list[str]:
    return ["docker", "compose", "-f", "infra/docker-compose.yml", *parts]


def _tmux_cmd(*parts: str) -> list[str]:
    return ["tmux", *parts]


def _render_missing_binary(tool_label: str) -> str:
    return "\n".join(
        [
            f"`{tool_label}` is not available in PATH.",
            "Please install Docker Desktop or the docker compose plugin and try again.",
        ]
    )


def _render_missing_tmux() -> str:
    return "\n".join(
        [
            "`tmux` is not available in PATH.",
            "Please install tmux and try again.",
        ]
    )


def _run_external(
    ctx: RuntimeContext,
    cmd: list[str],
    *,
    missing_tool: str | None = None,
    cwd: str | None = None,
) -> CommandResult:
    try:
        return ctx.run_command(cmd, cwd=cwd, env=ctx.env)
    except FileNotFoundError:
        return CommandResult(
            exit_code=1,
            stderr=_render_missing_binary(missing_tool or cmd[0]),
        )


def _run_tmux(ctx: RuntimeContext, *parts: str) -> CommandResult:
    try:
        return ctx.run_command(_tmux_cmd(*parts), cwd=str(ROOT_DIR), env=ctx.env)
    except FileNotFoundError:
        return CommandResult(exit_code=1, stderr=_render_missing_tmux())


def _render_deps_status(ctx: RuntimeContext, compose_result: CommandResult) -> CommandResult:
    lines = ["Dependency stack status"]
    compose_stdout = compose_result.stdout.strip()
    compose_stderr = compose_result.stderr.strip()
    ports_healthy = True

    if compose_stdout:
        lines.extend(["", "Compose:", compose_stdout])
    elif compose_result.exit_code == 0:
        lines.extend(["", "Compose:", "No dependency containers are currently running."])

    if compose_stderr:
        lines.extend(["", "Compose diagnostics:", compose_stderr])

    lines.extend(["", "Ports:"])
    for service, port in DEPS_PORTS:
        is_open = ctx.port_checker("127.0.0.1", port)
        ports_healthy = ports_healthy and is_open
        state = "open" if is_open else "closed"
        lines.append(f"  - {service}: localhost:{port} {state}")

    exit_code = 0 if compose_result.exit_code == 0 and ports_healthy else 1
    return CommandResult(exit_code=exit_code, stdout="\n".join(lines))


def _handle_deps(action: str, ctx: RuntimeContext) -> CommandResult:
    if action == "up":
        return _run_external(
            ctx,
            _compose_cmd("up", "-d", *DEPS_SERVICES),
            missing_tool="docker compose",
        )

    if action == "down":
        return _run_external(
            ctx,
            _compose_cmd("down"),
            missing_tool="docker compose",
        )

    if action == "logs":
        return _run_external(
            ctx,
            _compose_cmd("logs", "--tail", ctx.env["LINES"], *DEPS_SERVICES),
            missing_tool="docker compose",
        )

    compose_result = _run_external(
        ctx,
        _compose_cmd("ps"),
        missing_tool="docker compose",
    )
    if compose_result.exit_code != 0:
        return compose_result
    return _render_deps_status(ctx, compose_result)


def _session_name(ctx: RuntimeContext) -> str:
    return ctx.env["SESSION"]


def _resource_port(ctx: RuntimeContext, resource: str) -> int:
    default_key = "API_PORT" if resource == "api" else "WEB_PORT"
    value = ctx.env.get(default_key) or ctx.env.get("PORT") or DEFAULT_ENV[default_key]
    return int(value)


def _resource_url(ctx: RuntimeContext, resource: str) -> str:
    port = _resource_port(ctx, resource)
    if resource == "api":
        return f"http://localhost:{port}/health"
    return f"http://localhost:{port}"


def _tmux_window_names(ctx: RuntimeContext, session: str) -> list[str]:
    result = _run_tmux(ctx, "list-windows", "-t", session, "-F", "#W")
    if result.exit_code != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _ensure_tmux_session(ctx: RuntimeContext, session: str) -> CommandResult:
    has_session = _run_tmux(ctx, "has-session", "-t", session)
    if has_session.exit_code == 0:
        windows = _tmux_window_names(ctx, session)
        if "ops" not in windows:
            return _run_tmux(ctx, "new-window", "-d", "-t", session, "-n", "ops")
        return CommandResult(0)

    created = _run_tmux(ctx, "new-session", "-d", "-s", session, "-n", "ops")
    if created.exit_code != 0:
        return created
    return CommandResult(0)


def _http_check(url: str) -> bool:
    try:
        with urllib_request.urlopen(url, timeout=0.5) as response:
            return 200 <= response.status < 400
    except (urllib_error.URLError, TimeoutError, ValueError):
        return False


def _resource_is_running(ctx: RuntimeContext, resource: str) -> bool:
    port = _resource_port(ctx, resource)
    if not ctx.port_checker("127.0.0.1", port):
        return False
    if resource == "api":
        return _http_check(_resource_url(ctx, resource))
    return True


def _resource_port_in_use(ctx: RuntimeContext, resource: str) -> bool:
    return ctx.port_checker("127.0.0.1", _resource_port(ctx, resource))


def _tmux_target(session: str, window: str) -> str:
    return f"{session}:{window}"


def _build_api_command(ctx: RuntimeContext) -> str:
    export_keys = (
        "DATABASE_URL",
        "DATABASE_PORT",
        "NEO4J_URI",
        "NEO4J_USER",
        "NEO4J_PASSWORD",
        "REDIS_URL",
        "OPENAI_API_KEY",
    )
    exports = " ".join(
        f"{key}={shlex.quote(ctx.env[key])}"
        for key in export_keys
        if key in ctx.env and ctx.env[key]
    )
    prefix = f"export {exports} && " if exports else ""
    port = _resource_port(ctx, "api")
    return (
        f"cd {shlex.quote(str(API_DIR))} && "
        f"{prefix}"
        "uv sync --extra dev && "
        f"uv run uvicorn app.main:app --host 0.0.0.0 --port {port} --reload"
    )


def _build_web_command(ctx: RuntimeContext) -> str:
    port = _resource_port(ctx, "web")
    return (
        f"cd {shlex.quote(str(WEB_DIR))} && "
        "pnpm install && "
        f"pnpm dev --host 0.0.0.0 --port {port}"
    )


def _ensure_tmux_window(
    ctx: RuntimeContext,
    session: str,
    window: str,
    command: str,
) -> CommandResult:
    windows = _tmux_window_names(ctx, session)
    target = _tmux_target(session, window)

    if window in windows:
        killed = _run_tmux(ctx, "kill-window", "-t", target)
        if killed.exit_code != 0:
            return killed

    created = _run_tmux(ctx, "new-window", "-d", "-t", session, "-n", window)
    if created.exit_code != 0:
        return created

    sent = _run_tmux(ctx, "send-keys", "-t", target, command, "C-m")
    if sent.exit_code != 0:
        return sent

    return CommandResult(0)


def capture_window_logs(ctx: RuntimeContext, session: str, window: str, lines: int) -> CommandResult:
    return _run_tmux(
        ctx,
        "capture-pane",
        "-p",
        "-S",
        f"-{lines}",
        "-t",
        _tmux_target(session, window),
    )


def render_status_table(rows: list[tuple[str, str, str, str, str]]) -> str:
    headers = ("RESOURCE", "STATE", "RUNTIME", "TARGET", "CHECK")
    widths = [
        max(len(headers[index]), *(len(row[index]) for row in rows))
        for index in range(len(headers))
    ]
    lines = [
        "  ".join(header.ljust(widths[index]) for index, header in enumerate(headers))
    ]
    lines.extend(
        "  ".join(column.ljust(widths[index]) for index, column in enumerate(row))
        for row in rows
    )
    return "\n".join(lines)


def _deps_status_row(ctx: RuntimeContext) -> tuple[tuple[str, str, str, str, str], CommandResult]:
    compose_result = _run_external(
        ctx,
        _compose_cmd("ps"),
        missing_tool="docker compose",
    )
    if compose_result.exit_code != 0:
        detail = compose_result.stderr.strip() or "compose unavailable"
        return ("deps", "down", "docker", "postgres/neo4j/redis", detail), compose_result

    ports_healthy = all(ctx.port_checker("127.0.0.1", port) for _, port in DEPS_PORTS)
    check = "ports reachable" if ports_healthy else "ports missing"
    state = "up" if ports_healthy else "degraded"
    return ("deps", state, "docker", "postgres/neo4j/redis", check), compose_result


def _resource_status_row(ctx: RuntimeContext, resource: str) -> tuple[str, str, str, str, str]:
    session = _session_name(ctx)
    target = _tmux_target(session, resource)
    windows = _tmux_window_names(ctx, session)
    if resource not in windows:
        if _resource_port_in_use(ctx, resource):
            return (resource, "external", "host", target, "external process on port")
        return (resource, "down", "tmux", target, "window missing")

    if _resource_is_running(ctx, resource):
        check = "GET /health ok" if resource == "api" else "port reachable"
        return (resource, "up", "tmux", target, check)

    check = "port unreachable"
    if resource == "api":
        check = "health unavailable"
    return (resource, "starting", "tmux", target, check)


def _render_resource_status(ctx: RuntimeContext, resource: str) -> CommandResult:
    if resource == "deps":
        status = _handle_deps("status", ctx)
        if status.exit_code == 0:
            return status
        return CommandResult(status.exit_code, stdout=status.stdout, stderr=status.stderr)

    row = _resource_status_row(ctx, resource)
    table = render_status_table([row])
    exit_code = 0 if row[1] == "up" else 1
    return CommandResult(exit_code=exit_code, stdout=table)


def _handle_stack_status(ctx: RuntimeContext) -> CommandResult:
    deps_row, deps_result = _deps_status_row(ctx)
    rows = [
        deps_row,
        _resource_status_row(ctx, "api"),
        _resource_status_row(ctx, "web"),
    ]
    table = render_status_table(rows)
    notes = ["", "Try: make api logs", "Try: make stack attach"]
    exit_code = 0 if all(row[1] == "up" for row in rows) else 1
    if deps_result.exit_code != 0:
        exit_code = 1
    return CommandResult(exit_code=exit_code, stdout=f"{table}\n" + "\n".join(notes))


def _wait_for_ports(ctx: RuntimeContext, ports: tuple[tuple[str, int], ...], retries: int = 60) -> CommandResult:
    for _ in range(retries):
        if all(ctx.port_checker("127.0.0.1", port) for _, port in ports):
            return CommandResult(0)
        time.sleep(1)
    labels = ", ".join(f"{name}:{port}" for name, port in ports)
    return CommandResult(1, stderr=f"Timed out waiting for dependency ports: {labels}")


def _start_local_resource(ctx: RuntimeContext, resource: str) -> CommandResult:
    session = _session_name(ctx)
    ensured = _ensure_tmux_session(ctx, session)
    if ensured.exit_code != 0:
        return ensured

    windows = _tmux_window_names(ctx, session)
    if resource in windows and _resource_is_running(ctx, resource):
        return CommandResult(
            exit_code=0,
            stdout=f"{resource} already running in {_tmux_target(session, resource)}",
        )

    if resource not in windows and _resource_port_in_use(ctx, resource):
        port_key = "API_PORT" if resource == "api" else "WEB_PORT"
        port = _resource_port(ctx, resource)
        return CommandResult(
            exit_code=1,
            stderr=(
                f"`{resource}` port {port} is already in use by a process outside tmux.\n"
                f"Stop the external process or rerun with {port_key}=<port>."
            ),
        )

    command = _build_api_command(ctx) if resource == "api" else _build_web_command(ctx)
    started = _ensure_tmux_window(ctx, session, resource, command)
    if started.exit_code != 0:
        return started

    return CommandResult(
        exit_code=0,
        stdout="\n".join(
            [
                f"Started {resource} in {_tmux_target(session, resource)}",
                f"URL: {_resource_url(ctx, resource)}",
                f"Next: make {resource} logs",
            ]
        ),
    )


def _stop_local_resource(ctx: RuntimeContext, resource: str) -> CommandResult:
    session = _session_name(ctx)
    if resource not in _tmux_window_names(ctx, session):
        return CommandResult(0, stdout=f"{resource} is already stopped.")
    return _run_tmux(ctx, "kill-window", "-t", _tmux_target(session, resource))


def _handle_attach(ctx: RuntimeContext, resource: str) -> CommandResult:
    session = _session_name(ctx)
    has_session = _run_tmux(ctx, "has-session", "-t", session)
    if has_session.exit_code != 0:
        return CommandResult(
            exit_code=1,
            stderr=f"tmux session `{session}` is not running. Try: make stack up",
        )

    if resource in {"api", "web"}:
        select = _run_tmux(ctx, "select-window", "-t", _tmux_target(session, resource))
        if select.exit_code != 0:
            return CommandResult(
                exit_code=1,
                stderr=f"`{resource}` window is not available. Try: make {resource} up",
            )

    attached = _run_tmux(ctx, "attach-session", "-t", session)
    if attached.exit_code != 0:
        detail = attached.stderr.strip() or attached.stdout.strip() or "attach failed"
        return CommandResult(
            exit_code=1,
            stderr=f"{detail}\nTry: make stack up",
        )
    return attached


def _handle_local_resource(action: str, resource: str, ctx: RuntimeContext) -> CommandResult:
    if action == "up":
        return _start_local_resource(ctx, resource)
    if action == "down":
        return _stop_local_resource(ctx, resource)
    if action == "restart":
        stopped = _stop_local_resource(ctx, resource)
        if stopped.exit_code != 0:
            return stopped
        return _start_local_resource(ctx, resource)
    if action == "status":
        return _render_resource_status(ctx, resource)
    if action == "logs":
        session = _session_name(ctx)
        if resource not in _tmux_window_names(ctx, session):
            return CommandResult(
                exit_code=1,
                stderr=f"`{resource}` window is not running. Try: make {resource} up",
            )
        return capture_window_logs(ctx, session, resource, int(ctx.env["LINES"]))
    return _handle_attach(ctx, resource)


def _handle_stack(action: str, ctx: RuntimeContext) -> CommandResult:
    if action == "status":
        return _handle_stack_status(ctx)
    if action == "attach":
        return _handle_attach(ctx, "stack")
    if action == "down":
        stop_api = _stop_local_resource(ctx, "api")
        stop_web = _stop_local_resource(ctx, "web")
        stop_deps = _handle_deps("down", ctx)
        outputs = [part for part in (stop_api.stdout, stop_web.stdout, stop_deps.stdout) if part]
        errors = [part for part in (stop_api.stderr, stop_web.stderr, stop_deps.stderr) if part]
        exit_code = 0 if all(result.exit_code == 0 for result in (stop_api, stop_web, stop_deps)) else 1
        return CommandResult(exit_code=exit_code, stdout="\n".join(outputs), stderr="\n".join(errors))
    if action == "restart":
        down_result = _handle_stack("down", ctx)
        if down_result.exit_code not in (0, 1):
            return down_result
        return _handle_stack("up", ctx)

    deps_up = _handle_deps("up", ctx)
    if deps_up.exit_code != 0:
        return deps_up

    waited = _wait_for_ports(ctx, DEPS_PORTS)
    if waited.exit_code != 0:
        return waited

    api_up = _start_local_resource(ctx, "api")
    if api_up.exit_code != 0:
        return api_up

    web_up = _start_local_resource(ctx, "web")
    if web_up.exit_code != 0:
        return web_up

    status = _handle_stack_status(ctx)
    combined = "\n\n".join(part for part in (deps_up.stdout, api_up.stdout, web_up.stdout, status.stdout) if part)
    return CommandResult(
        exit_code=0,
        stdout=combined,
        stderr=status.stderr,
    )


def run_cli_result(
    argv: list[str],
    env: dict[str, str] | None = None,
    *,
    run_command: RunCommand | None = None,
    port_checker: PortChecker | None = None,
) -> CLIResult:
    ctx = RuntimeContext(
        env=_merge_env(env),
        run_command=run_command or _default_run_command,
        port_checker=port_checker or _default_port_checker,
    )

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

    if resource == "deps":
        return _handle_deps(action, ctx)
    if resource in {"api", "web"}:
        return _handle_local_resource(action, resource, ctx)
    if resource == "stack":
        return _handle_stack(action, ctx)

    lines = [
        f"`{resource} {action}` is not implemented yet.",
        "This task only provides the runtime command skeleton and guidance surface.",
        "",
        *_example_lines(resource),
    ]
    return CLIResult(exit_code=1, stderr="\n".join(lines))


def run_cli(
    argv: list[str],
    env: dict[str, str] | None = None,
    *,
    run_command: RunCommand | None = None,
    port_checker: PortChecker | None = None,
) -> tuple[int, str]:
    result = run_cli_result(
        argv,
        env=env,
        run_command=run_command,
        port_checker=port_checker,
    )
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
