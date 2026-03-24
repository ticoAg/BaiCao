# 后端 `uv` / `ruff` / `ty` 工具链统一 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 `packages/api/` 的开发、验证、CI 与文档口径统一到 `uv + ruff + ty + pytest` 工具链。

**Architecture:** 以 `packages/api/pyproject.toml` 作为后端工具链真源，`scripts/test_api.sh` 作为统一验证入口，CI 和根脚本只做转发，避免重复维护后端事实。若 `ty` 暴露历史类型问题，只做最小必要修复以让标准链路可执行。

**Tech Stack:** `uv`、`ruff`、`ty`、`pytest`、GitHub Actions、Bash

---

### Task 1: 将后端工具链真源集中到 `pyproject.toml`

**Files:**
- Modify: `packages/api/pyproject.toml`
- Modify: `packages/api/uv.lock`

- [ ] **Step 1: 写失败验证，确认 `ty` 尚未接入**

Run: `cd packages/api && uv run ty check`
Expected: FAIL with `No such file or directory` or missing dependency / config

- [ ] **Step 2: 在 dev 依赖中加入 `ty`**

在 `packages/api/pyproject.toml` 的 `project.optional-dependencies.dev` 中加入：

```toml
"ty>=0.0.1",
```

- [ ] **Step 3: 补全 `ruff` / `ty` 配置**

在 `packages/api/pyproject.toml` 中补齐：

- `tool.ruff.lint`
- `tool.ruff.format`
- `tool.ty`

要求：

- 范围明确针对 `app` 与 `tests`
- 不引入额外 Python lint / type 工具
- 保持最小配置，不做花哨定制

- [ ] **Step 4: 刷新锁文件**

Run: `cd packages/api && uv lock`
Expected: `packages/api/uv.lock` 纳入 `ty`

- [ ] **Step 5: 运行工具链烟囱验证**

Run: `cd packages/api && uv sync --extra dev && uv run ruff check app tests && uv run ty check`
Expected: PASS，若失败则进入 Task 4 修阻塞项


### Task 2: 统一后端脚本入口

**Files:**
- Modify: `scripts/test_api.sh`
- Modify: `package.json`

- [ ] **Step 1: 写失败验证，确认脚本未覆盖完整链路**

Run: `sed -n '1,80p' scripts/test_api.sh`
Expected: 当前只跑 `pytest` 子集，未体现 `ruff + ty + pytest`

- [ ] **Step 2: 将 `scripts/test_api.sh` 改为后端唯一验证入口**

脚本顺序调整为：

```bash
cd "$ROOT/packages/api"
uv sync --extra dev
uv run ruff check app tests
uv run ty check
uv run pytest
```

- [ ] **Step 3: 保持根脚本只做转发**

检查 `package.json` 中：

- `test:api`
- `verify`
- `verify:full`

如需修改，仅做最小口径更新，不在根层重复拼装后端细节

- [ ] **Step 4: 运行脚本验证**

Run: `./scripts/test_api.sh`
Expected: exit code `0`


### Task 3: 统一 CI 与文档口径

**Files:**
- Modify: `.github/workflows/ci-fast.yml`
- Modify: `README.md`
- Modify: `docs/verification-matrix.md`
- Modify: `docs/acceptance/README.md`

- [ ] **Step 1: 更新 CI 后端步骤**

要求：

- 显式安装 `uv`
- 调用与本地一致的后端验证入口
- 不维护另一套独立命令链

- [ ] **Step 2: 更新 README 后端命令说明**

明确写出：

- `uv sync --extra dev`
- `uv run ruff check app tests`
- `uv run ty check`
- `uv run pytest`
- `pnpm run test:api` 只是仓库根转发入口

- [ ] **Step 3: 更新验证矩阵与验收入口**

将 `packages/api/` 最低验证口径更新为：

```bash
uv run ruff check app tests
uv run ty check
uv run pytest
```

并说明统一入口仍为 `./scripts/test_api.sh`

- [ ] **Step 4: 运行文档路径自检**

Run: `rg -n "ty check|test:api|ruff check app tests" README.md docs packages/api/.github scripts`
Expected: 引用路径与命令一致


### Task 4: 修复 `ty` 阻塞项

**Files:**
- Modify: `packages/api/app/**`（仅阻塞项）
- Modify: `packages/api/tests/**`（仅阻塞项）

- [ ] **Step 1: 运行 `ty` 收集真实错误**

Run: `cd packages/api && uv run ty check`
Expected: 若报类型问题，记录最小阻塞集

- [ ] **Step 2: 做最小类型修复**

优先顺序：

1. 显式返回类型
2. 可空值收窄
3. dict / list 边界显式化
4. 局部 `Any` 或局部忽略（仅在必要时）

- [ ] **Step 3: 每修一组错误就回跑 `ty`**

Run: `cd packages/api && uv run ty check`
Expected: 错误数下降，直到为 0


### Task 5: 统一验证并收尾

**Files:**
- Modify: `docs/superpowers/plans/2026-03-24-backend-uv-ruff-ty-toolchain.md`

- [ ] **Step 1: 跑后端 lint**

Run: `cd packages/api && uv run ruff check app tests`
Expected: PASS

- [ ] **Step 2: 跑后端 typecheck**

Run: `cd packages/api && uv run ty check`
Expected: PASS

- [ ] **Step 3: 跑后端测试**

Run: `cd packages/api && uv run pytest`
Expected: PASS

- [ ] **Step 4: 跑统一脚本入口**

Run: `./scripts/test_api.sh`
Expected: PASS

- [ ] **Step 5: 记录未覆盖项**

若本轮未执行：

- GitHub Actions 远端实际运行
- integration / e2e 之外的更大闭环

则在最终交付中明确写出原因与复现方式。
