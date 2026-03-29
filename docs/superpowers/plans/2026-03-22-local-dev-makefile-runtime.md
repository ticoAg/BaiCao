# Local Dev Makefile Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 BaiCao 提供一套以 `make <resource> <action>` 为入口、以单个 tmux session 为运行时、以 `deps` 容器栈为依赖边界的本地开发主链路。

**Architecture:** 根目录 `Makefile` 只负责把 `resource/action` 转发给一个 Python 运行时脚本；运行时统一管理帮助提示、参数校验、`docker compose` 依赖栈、tmux 单 session 编排和状态观测。`infra/docker-compose.yml` 收敛为纯依赖容器，旧 tmux 脚本直接移除，并把仍在使用它们的活入口迁移到新运行时。

**Tech Stack:** GNU Make, Python 3 standard library, tmux, Docker Compose, uv, pnpm

---

## 实施状态更新（2026-03-25）

### 已完成

- 本地开发主入口已经统一到根目录 `Makefile` 和 `scripts/dev_runtime.py`，支持 `make help`、`make deps help`、`make api up`、`make stack status` 等统一命令面
- 运行时测试已落地到 `scripts/tests/test_dev_runtime.py`，覆盖帮助提示、错误引导、`deps` 编排、单 session tmux 管理、状态汇总与 attach 恢复提示
- `scripts/test_e2e.sh` 的本地自起栈路径已经切到 `make stack up`，不再依赖旧 tmux/demo 启动脚本；仓库中当前只保留 `dev_runtime.py`、测试脚本与种子脚本等活入口
- `README.md` 已切换到“依赖服务走 Docker Compose、API/Web 走本地进程、统一挂到 tmux session”的主路径说明
- `infra/docker-compose.yml` 当前已作为依赖容器编排真源继续使用；后续 Wave 2 为 review/export 持久化又把 `minio` 纳入 compose 依赖栈，但未改变“依赖走 compose、应用走本地 tmux”的主设计

### 验证结果

- `python3 -m unittest discover -s scripts/tests -p 'test_dev_runtime.py' -v` → `16 tests OK`
- `make help` → 正常输出 `deps` / `api` / `web` / `stack` 资源总览
- `docker compose -f infra/docker-compose.yml config` → `OK`

### 风险与备注

- 这份计划最初把 `deps` 明确写成 `postgres`、`neo4j`、`redis` 三个服务；当前仓库事实已在后续波次扩展为包含 `minio` 的依赖栈，应以“compose 管理依赖边界”作为稳定结论，而不是把三服务列表视为不可变化的约束
- `scripts/test_e2e.sh` 在 CI 路径下仍直接起本地 API/Web 进程；该脚本的本地 fallback 已迁移到 `make stack up`，两条路径的设计意图不同
- 历史步骤中的 checkbox 未逐项回填；本节作为当前实现事实与验证证据的聚合更新

### 当前结论

- 这份 plan 已实施完成，属于“文档未回填，但实现已落地”的情况
- 同时它也是“checkbox 仍显示未开始，但仓库已经在继续基于该主路径演进”的典型例子

## File Map

- Create: `Makefile`
  - 提供 `make help`、`make api up`、`make stack status` 等统一入口，并把 `KEY=VALUE` 参数透传给运行时。
- Create: `scripts/dev_runtime.py`
  - 统一实现命令解析、帮助输出、错误提示、compose 依赖管理、tmux session/window 管理、状态与日志观测。
- Create: `scripts/tests/test_dev_runtime.py`
  - 为运行时的解析、错误引导、session/window 策略、命令构造和状态汇总提供可重复的回归测试。
- Modify: `infra/docker-compose.yml`
  - 移除 `api`、`web`、`nginx`，只保留 `postgres`、`neo4j`、`redis`。
- Delete: 旧 tmux 启动脚本
  - 直接移除过时 tmux 入口，避免与 `make` 主路径并存。
- Delete: 旧 demo 启动脚本
  - 直接移除过时 demo tmux 入口。
- Modify: `scripts/test_e2e.sh`
  - 把本地自动起栈路径迁移到 `make stack up`，不再依赖已删除脚本。
- Modify: `README.md`
  - 更新快速开始，明确“前后端本地启动、依赖走 compose、调试走 make/tmux”。

## Non-Goals

- 不引入新的后台守护或进程管理器。
- 不把 `deps` 改成纯本地安装。
- 不在本轮扩展 `doctor`、`bootstrap`、`test` 等额外命令面。
- 不为运行时引入第三方 Python 包。

## Runtime Contract

### Supported resources

- `help`
- `deps`
- `api`
- `web`
- `stack`

### Supported actions

- `help`: `help`
- `deps`: `up`, `down`, `status`, `logs`, `help`
- `api`: `up`, `down`, `restart`, `status`, `logs`, `attach`, `help`
- `web`: `up`, `down`, `restart`, `status`, `logs`, `attach`, `help`
- `stack`: `up`, `down`, `restart`, `status`, `attach`, `help`

### Defaults

- `SESSION=baicao-dev`
- `API_PORT=8000`
- `WEB_PORT=3000`
- `LINES=80`

### Fixed tmux windows

- `api`
- `web`
- `ops`

---

### Task 1: Build the Runtime Skeleton and Guidance Surface

**Files:**
- Create: `scripts/dev_runtime.py`
- Create: `scripts/tests/test_dev_runtime.py`
- Create: `Makefile`

- [ ] **Step 1: Write the failing runtime tests for help and error guidance**

```python
import unittest
import importlib.util
from pathlib import Path


def load_runtime_module():
    runtime_path = Path(__file__).resolve().parents[1] / "dev_runtime.py"
    spec = importlib.util.spec_from_file_location("dev_runtime", runtime_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


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
```

- [ ] **Step 2: Run the runtime tests to verify they fail**

Run:

```bash
python3 -m unittest discover -s scripts/tests -p 'test_dev_runtime.py' -v
```

Expected: FAIL because `scripts/dev_runtime.py`, `run_cli(...)`, and the test helper import target do not exist yet.

- [ ] **Step 3: Implement the minimal runtime skeleton and Makefile forwarding**

```python
SUPPORTED = {
    "help": {"help"},
    "deps": {"up", "down", "status", "logs", "help"},
    "api": {"up", "down", "restart", "status", "logs", "attach", "help"},
    "web": {"up", "down", "restart", "status", "logs", "attach", "help"},
    "stack": {"up", "down", "restart", "status", "attach", "help"},
}


def run_cli(argv: list[str], env: dict[str, str] | None = None) -> tuple[int, str]:
    resource = argv[0] if argv else "help"
    action = argv[1] if len(argv) > 1 else "help"
    ...
```

```make
.DEFAULT_GOAL := help

RESOURCE := $(firstword $(MAKECMDGOALS))
ACTION := $(or $(word 2,$(MAKECMDGOALS)),help)

VALID_RESOURCES := help deps api web stack

ifneq ($(filter $(RESOURCE),$(VALID_RESOURCES)),)
  $(eval $(ACTION):;@:)
endif

help:
	@python3 scripts/dev_runtime.py help

deps api web stack:
	@python3 scripts/dev_runtime.py $(RESOURCE) $(ACTION)
```

实现要求：

- `Makefile` 支持 `make help` 和 `make <resource> <action>`
- `scripts/dev_runtime.py` 先完整实现 help、资源校验、动作校验、渐进式错误提示
- 所有错误返回非 0 exit code
- 输出中带示例命令

- [ ] **Step 4: Run the runtime tests to verify they pass**

Run:

```bash
python3 -m unittest discover -s scripts/tests -p 'test_dev_runtime.py' -v
make help
make api help
```

Expected:

- `unittest` PASS
- `make help` 输出资源总览
- `make api help` 输出 `api` 支持的动作和参数示例

- [ ] **Step 5: Commit**

```bash
git add Makefile scripts/dev_runtime.py scripts/tests/test_dev_runtime.py
git commit -m "feat(dev): add local runtime command surface"
```

### Task 2: Trim Compose to Dependency-Only and Implement `deps`

**Files:**
- Modify: `infra/docker-compose.yml`
- Modify: `scripts/dev_runtime.py`
- Modify: `scripts/tests/test_dev_runtime.py`

- [ ] **Step 1: Write the failing tests for dependency orchestration**

```python
class DepsCommandTests(unittest.TestCase):
    def setUp(self):
        self.runtime = load_runtime_module()

    def test_deps_up_targets_only_dependency_services(self):
        calls: list[list[str]] = []

        def fake_run(cmd, **kwargs):
            calls.append(cmd)
            return self.runtime.CommandResult(0, "", "")

        exit_code, _ = self.runtime.run_cli(
            ["deps", "up"],
            env={},
            run_command=fake_run,
        )

        self.assertEqual(exit_code, 0)
        self.assertIn(
            ["docker", "compose", "-f", "infra/docker-compose.yml", "up", "-d", "postgres", "neo4j", "redis"],
            calls,
        )

    def test_deps_status_reports_missing_compose_binary_cleanly(self):
        def fake_run(cmd, **kwargs):
            raise FileNotFoundError("docker")

        exit_code, output = self.runtime.run_cli(
            ["deps", "status"],
            env={},
            run_command=fake_run,
        )

        self.assertEqual(exit_code, 1)
        self.assertIn("docker compose", output)
        self.assertIn("install", output.lower())
```

- [ ] **Step 2: Run the dependency tests to verify they fail**

Run:

```bash
python3 -m unittest discover -s scripts/tests -p 'test_dev_runtime.py' -v
```

Expected: FAIL because `deps` action handlers and `CommandResult` / injectable command runner are not implemented yet.

- [ ] **Step 3: Implement dependency-only compose management**

```yaml
services:
  postgres:
    ...
  neo4j:
    ...
  redis:
    ...
```

```python
def compose_cmd(*parts: str) -> list[str]:
    return ["docker", "compose", "-f", "infra/docker-compose.yml", *parts]


def handle_deps(action: str, ctx: RuntimeContext) -> CommandResult:
    if action == "up":
        return run_external(compose_cmd("up", "-d", "postgres", "neo4j", "redis"))
    ...
```

实现要求：

- 从 `infra/docker-compose.yml` 中移除 `api`、`web`、`nginx`
- `deps up/down/status/logs` 全部走统一 compose 封装
- `deps status` 除 compose 状态外，还检查 `15433`、`17687`、`16380` 端口
- 缺少 `docker compose` 时输出清晰安装提示

- [ ] **Step 4: Run the tests and compose validation**

Run:

```bash
python3 -m unittest discover -s scripts/tests -p 'test_dev_runtime.py' -v
docker compose -f infra/docker-compose.yml config
make deps status
```

Expected:

- `unittest` PASS
- `docker compose ... config` PASS
- `make deps status` 在依赖未启动时给出清晰状态，而不是崩溃

- [ ] **Step 5: Commit**

```bash
git add infra/docker-compose.yml scripts/dev_runtime.py scripts/tests/test_dev_runtime.py
git commit -m "refactor(dev): separate dependency compose stack"
```

### Task 3: Implement Single-Session tmux Runtime for `api`, `web`, and `stack`

**Files:**
- Modify: `scripts/dev_runtime.py`
- Modify: `scripts/tests/test_dev_runtime.py`

- [ ] **Step 1: Write the failing tests for tmux session/window orchestration**

```python
class TmuxRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.runtime = load_runtime_module()

    def test_api_up_creates_single_session_with_fixed_windows(self):
        tmux_calls: list[list[str]] = []

        def fake_run(cmd, **kwargs):
            tmux_calls.append(cmd)
            return self.runtime.CommandResult(0, "", "")

        exit_code, _ = self.runtime.run_cli(
            ["api", "up"],
            env={"SESSION": "baicao-dev", "API_PORT": "8000"},
            run_command=fake_run,
        )

        self.assertEqual(exit_code, 0)
        self.assertTrue(any(cmd[:3] == ["tmux", "new-session", "-d"] for cmd in tmux_calls))
        self.assertTrue(any("api" in cmd for cmd in tmux_calls))
        self.assertTrue(any("ops" in cmd for cmd in tmux_calls))

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
            return self.runtime.CommandResult(1, "", "no server running")

        exit_code, output = self.runtime.run_cli(
            ["stack", "attach"],
            env={"SESSION": "baicao-dev"},
            run_command=fake_run,
        )

        self.assertEqual(exit_code, 1)
        self.assertIn("make stack up", output)
```

- [ ] **Step 2: Run the tmux runtime tests to verify they fail**

Run:

```bash
python3 -m unittest discover -s scripts/tests -p 'test_dev_runtime.py' -v
```

Expected: FAIL because tmux session/window helpers, status rendering, and attach recovery hints are not implemented yet.

- [ ] **Step 3: Implement tmux orchestration for `api`, `web`, and `stack`**

```python
API_ENV = {
    "DATABASE_URL": "postgresql+asyncpg://baicao:baicao_password@localhost:15433/baicao",
    "DATABASE_PORT": "15433",
    "NEO4J_URI": "bolt://localhost:17687",
    "NEO4J_USER": "neo4j",
    "NEO4J_PASSWORD": "neo4j_password",
    "REDIS_URL": "redis://localhost:16380",
}


def ensure_session(session: str) -> None:
    ...


def ensure_window(session: str, window: str, command: str) -> None:
    ...


def capture_window_logs(session: str, window: str, lines: int) -> str:
    ...
```

实现要求：

- 整个项目只使用一个 tmux session，默认 `baicao-dev`
- 创建 session 时一并创建 `ops` window
- `api up` / `web up` 对已有健康 window 保持幂等
- `status` 需要同时检查 tmux window 存在性、端口和关键健康信息
- `logs` 通过 `tmux capture-pane` 获取，不要求先 attach
- `stack up` 顺序为 `deps up -> wait ports -> api up -> web up`
- `stack down` 顺序为 `api/web down -> deps down`

- [ ] **Step 4: Run the tests and tmux smoke checks**

Run:

```bash
python3 -m unittest discover -s scripts/tests -p 'test_dev_runtime.py' -v
make stack status
make api status
make web status
```

Expected:

- `unittest` PASS
- 未启动时的 `status` 输出清晰、可恢复
- 已启动时能展示统一状态表和下一步建议

- [ ] **Step 5: Commit**

```bash
git add scripts/dev_runtime.py scripts/tests/test_dev_runtime.py
git commit -m "feat(dev): add tmux-based local stack runtime"
```

### Task 4: Remove Legacy Scripts and Update Developer Docs

**Files:**
- Delete: 旧 tmux 启动脚本
- Delete: 旧 demo 启动脚本
- Modify: `scripts/test_e2e.sh`
- Modify: `README.md`
- Modify: `scripts/dev_runtime.py`
- Modify: `scripts/tests/test_dev_runtime.py`

- [ ] **Step 1: Write the failing regression tests for legacy cleanup**

```python
class LegacyCleanupTests(unittest.TestCase):
    def setUp(self):
        self.runtime = load_runtime_module()

    def test_demo_start_sequence_uses_make_stack_runtime(self):
        calls: list[list[str]] = []

        def fake_run(cmd, **kwargs):
            calls.append(cmd)
            return self.runtime.CommandResult(0, "", "")

        self.runtime.run_demo_bootstrap(run_command=fake_run)

        self.assertTrue(any(cmd[:3] == ["make", "-C", str(ROOT)] for cmd in calls))
        self.assertTrue(any("stack" in cmd for cmd in calls))
```

- [ ] **Step 2: Run the regression tests to verify they fail**

Run:

```bash
python3 -m unittest discover -s scripts/tests -p 'test_dev_runtime.py' -v
```

Expected: FAIL because E2E startup still depends on the removed scripts.

- [ ] **Step 3: Delete legacy scripts, migrate E2E startup, and update README**

README 要覆盖：

- `make help`
- `make deps up`
- `make stack up`
- `make stack attach`
- `make stack status`
- 说明 `api` / `web` 默认本地运行

`scripts/test_e2e.sh` 要点：

- CI 仍保留当前本地子进程起栈方式
- 非 CI 自动起栈改为 `make stack up`
- 清理逻辑不再依赖已删除脚本

- [ ] **Step 4: Run final verification for docs and command surface**

Run:

```bash
python3 -m unittest discover -s scripts/tests -p 'test_dev_runtime.py' -v
docker compose -f infra/docker-compose.yml config
bash -n scripts/test_e2e.sh
make help
make deps up
make stack up
make stack status
make api logs
make web logs
make stack down
```

Expected:

- `unittest` PASS
- `docker compose ... config` PASS
- `bash -n scripts/test_e2e.sh` PASS
- Make 命令主链路全部可执行
- `stack status` / `logs` 输出具备清晰的可观测性和恢复提示

- [ ] **Step 5: Commit**

```bash
git add README.md scripts/test_e2e.sh scripts/dev_runtime.py scripts/tests/test_dev_runtime.py
git rm <旧 tmux 启动脚本> <旧 demo 启动脚本>
git commit -m "docs(dev): document local make and tmux workflow"
```

## Review Checklist

- `infra/docker-compose.yml` 中不再出现 `api`、`web`、`nginx`
- `Makefile` 覆盖 `help`、`deps`、`api`、`web`、`stack`
- `scripts/dev_runtime.py` 使用单个 tmux session 和固定 window 名
- 错误场景均带恢复提示
- README 已更新为本地开发主链路
- 最终验证包含 compose 检查和 make 主链路 smoke
