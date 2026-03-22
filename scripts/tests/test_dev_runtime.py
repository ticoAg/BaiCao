import importlib.util
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def load_runtime_module():
    runtime_path = Path(__file__).resolve().parents[1] / "dev_runtime.py"
    spec = importlib.util.spec_from_file_location("dev_runtime", runtime_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def run_command(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args),
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class RuntimeHelpTests(unittest.TestCase):
    def setUp(self):
        self.runtime = load_runtime_module()

    def test_root_help_lists_supported_resources(self):
        exit_code, output = self.runtime.run_cli(["help"], env={})

        self.assertEqual(exit_code, 0)
        self.assertIn("deps", output)
        self.assertIn("api", output)
        self.assertIn("stack", output)

    def test_unknown_resource_suggests_help(self):
        exit_code, output = self.runtime.run_cli(["ap", "up"], env={})

        self.assertEqual(exit_code, 2)
        self.assertIn("Unknown resource: ap", output)
        self.assertIn("Did you mean: api", output)
        self.assertIn("make help", output)

    def test_unknown_action_suggests_resource_help(self):
        exit_code, output = self.runtime.run_cli(["api", "upp"], env={})

        self.assertEqual(exit_code, 2)
        self.assertIn("Unknown action: upp", output)
        self.assertIn("make api help", output)

    def test_root_help_rejects_extra_args(self):
        exit_code, output = self.runtime.run_cli(["help", "typo"], env={})

        self.assertEqual(exit_code, 2)
        self.assertIn("Unexpected extra arguments: typo", output)
        self.assertIn("make help", output)

    def test_make_unknown_resource_routes_to_runtime_guidance(self):
        result = run_command("make", "ap", "up")

        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("Unknown resource: ap", result.stderr)
        self.assertIn("Did you mean: api", result.stderr)
        self.assertIn("make help", result.stderr)
        self.assertNotIn("No rule to make target", result.stderr)

    def test_make_same_name_directory_still_routes_to_runtime(self):
        result = run_command("make", "docs", "up")

        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("Unknown resource: docs", result.stderr)
        self.assertIn("make help", result.stderr)
        self.assertNotIn("is up to date", result.stderr)

    def test_make_help_rejects_extra_args(self):
        result = run_command("make", "help", "typo")

        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("Unexpected extra arguments: typo", result.stderr)
        self.assertIn("make help", result.stderr)

    def test_python_cli_rejects_extra_args_via_stderr(self):
        result = run_command(
            "python3",
            "scripts/dev_runtime.py",
            "api",
            "help",
            "typo",
        )

        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("Unexpected extra arguments: typo", result.stderr)
        self.assertIn("make api help", result.stderr)


class DepsCommandTests(unittest.TestCase):
    def setUp(self):
        self.runtime = load_runtime_module()

    def test_deps_up_targets_only_dependency_services(self):
        calls: list[list[str]] = []

        def fake_run(cmd, **kwargs):
            del kwargs
            calls.append(cmd)
            return self.runtime.CommandResult(0, "", "")

        exit_code, _ = self.runtime.run_cli(
            ["deps", "up"],
            env={},
            run_command=fake_run,
        )

        self.assertEqual(exit_code, 0)
        self.assertIn(
            [
                "docker",
                "compose",
                "-f",
                "infra/docker-compose.yml",
                "up",
                "-d",
                "postgres",
                "neo4j",
                "redis",
            ],
            calls,
        )

    def test_deps_status_reports_missing_compose_binary_cleanly(self):
        def fake_run(cmd, **kwargs):
            del cmd, kwargs
            raise FileNotFoundError("docker")

        exit_code, output = self.runtime.run_cli(
            ["deps", "status"],
            env={},
            run_command=fake_run,
        )

        self.assertEqual(exit_code, 1)
        self.assertIn("docker compose", output)
        self.assertIn("install", output.lower())

    def test_deps_logs_honors_lines_env_override(self):
        calls: list[list[str]] = []

        def fake_run(cmd, **kwargs):
            del kwargs
            calls.append(cmd)
            return self.runtime.CommandResult(0, "", "")

        exit_code, _ = self.runtime.run_cli(
            ["deps", "logs"],
            env={"LINES": "5"},
            run_command=fake_run,
        )

        self.assertEqual(exit_code, 0)
        self.assertIn(
            [
                "docker",
                "compose",
                "-f",
                "infra/docker-compose.yml",
                "logs",
                "--tail",
                "5",
                "postgres",
                "neo4j",
                "redis",
            ],
            calls,
        )


class TmuxRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.runtime = load_runtime_module()

    def test_api_up_creates_single_session_with_fixed_windows(self):
        tmux_calls: list[list[str]] = []

        def fake_run(cmd, **kwargs):
            del kwargs
            tmux_calls.append(cmd)
            if cmd[:3] == ["tmux", "has-session", "-t"]:
                return self.runtime.CommandResult(1, "", "")
            if cmd[:3] == ["tmux", "list-windows", "-t"]:
                return self.runtime.CommandResult(0, "ops\n", "")
            return self.runtime.CommandResult(0, "", "")

        exit_code, _ = self.runtime.run_cli(
            ["api", "up"],
            env={"SESSION": "baicao-dev", "API_PORT": "8000"},
            run_command=fake_run,
            port_checker=lambda host, port: False,
        )

        self.assertEqual(exit_code, 0)
        self.assertTrue(any(cmd[:4] == ["tmux", "new-session", "-d", "-s"] for cmd in tmux_calls))
        self.assertTrue(any("api" in cmd for cmd in tmux_calls))
        self.assertTrue(any("ops" in cmd for cmd in tmux_calls))

    def test_api_up_detects_external_process_outside_tmux(self):
        original_http_check = self.runtime._http_check
        self.runtime._http_check = lambda url: True
        try:
            def fake_run(cmd, **kwargs):
                del kwargs
                if cmd[:3] == ["tmux", "has-session", "-t"]:
                    return self.runtime.CommandResult(0, "", "")
                if cmd[:3] == ["tmux", "list-windows", "-t"]:
                    return self.runtime.CommandResult(0, "ops\n", "")
                return self.runtime.CommandResult(0, "", "")

            exit_code, output = self.runtime.run_cli(
                ["api", "up"],
                env={"SESSION": "baicao-dev", "API_PORT": "8000"},
                run_command=fake_run,
                port_checker=lambda host, port: True,
            )
        finally:
            self.runtime._http_check = original_http_check

        self.assertEqual(exit_code, 1)
        self.assertIn("outside tmux", output)
        self.assertIn("API_PORT", output)

    def test_stack_status_summarizes_deps_api_and_web(self):
        summary = self.runtime.render_status_table(
            [
                ("deps", "up", "docker", "postgres/neo4j/redis", "ports reachable"),
                ("api", "up", "tmux", "baicao-dev:api", "GET /health ok"),
                ("web", "down", "tmux", "baicao-dev:web", "port unreachable"),
            ]
        )

        self.assertIn("RESOURCE", summary)
        self.assertIn("baicao-dev:api", summary)
        self.assertIn("port unreachable", summary)

    def test_attach_to_missing_session_returns_recovery_hint(self):
        def fake_run(cmd, **kwargs):
            del cmd, kwargs
            return self.runtime.CommandResult(1, "", "no server running")

        exit_code, output = self.runtime.run_cli(
            ["stack", "attach"],
            env={"SESSION": "baicao-dev"},
            run_command=fake_run,
        )

        self.assertEqual(exit_code, 1)
        self.assertIn("make stack up", output)
