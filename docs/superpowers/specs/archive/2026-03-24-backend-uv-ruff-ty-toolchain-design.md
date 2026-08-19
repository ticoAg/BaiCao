# 后端 `uv` / `ruff` / `ty` 工具链统一设计

## 背景

当前 `packages/api/` 已经在事实层使用 `uv` 与 `ruff`，但工具链仍不完全统一：

- `packages/api/pyproject.toml` 中未接入 `ty`
- 后端验证命令入口仍偏分散，根脚本、CI、README、验收文档之间存在口径漂移
- CI 主要依赖 `./scripts/test_api.sh`，但脚本未明确体现 `uv + ruff + ty` 为唯一后端标准链路
- “后端使用什么工具链”目前更多是约定而不是可执行的仓库事实

本次改造目标是把后端的开发、验证、CI、文档口径统一到 Astral 工具链上，并保持与 monorepo 其他模块的边界清晰。

## 目标

将 `packages/api/` 的标准开发与验证链路统一为：

- 环境与依赖：`uv`
- lint / format：`ruff`
- 类型检查：`ty`
- 测试执行：`pytest`（通过 `uv run pytest`）

并保证以下一致性：

1. `packages/api/pyproject.toml` 是后端工具链真源
2. 本地命令、仓库脚本、CI workflow、README、验证矩阵口径一致
3. 前端工具链不受影响，仍保持 `pnpm` / `vite-plus`

## 非目标

以下内容不在本轮范围内：

- 不重写前端或全仓工具链
- 不引入 `mypy` / `pyright` 与 `ty` 并存
- 不做与工具链统一无关的大规模代码重构
- 不重塑整个 monorepo 的命令体系，只收敛后端主作用域与根入口对后端的调用方式

## 方案选择

### 方案 A：只补 dev 依赖与手工命令

仅在 `packages/api/pyproject.toml` 中加入 `ty`，约定开发者手工运行：

- `uv run ruff check`
- `uv run ty check`
- `uv run pytest`

优点是改动最小；缺点是 CI、脚本、文档不会随之统一，仓库事实仍不完整。

### 方案 B：后端标准化接入（采用）

统一以下层面：

- `pyproject.toml` 中声明后端工具链与配置
- `scripts/test_api.sh` 作为后端统一验证入口
- `.github/workflows/ci-fast.yml` 调用同一验证链
- README / 验证矩阵 / acceptance 文档同步更新

这样本地与 CI 运行的是同一套命令，且不会越界改造前端工作流。

### 方案 C：全仓命令体系重塑

把根脚本、Make runtime、docs、CI 全部重塑为更强统一的 monorepo 命令体系。

一致性最高，但当前收益不够匹配改动面，且会波及与本次需求无关的 web 工作流，因此不采用。

## 最终设计

### 1. `packages/api/pyproject.toml` 作为工具链真源

在 `packages/api/pyproject.toml` 中完成以下调整：

- 在 `dev` 依赖中加入 `ty`
- 完善 `tool.ruff` 配置，明确检查范围、基础规则与格式化协同方式
- 增加 `tool.ty` 配置，保证 `ty` 在仓库中可执行且口径稳定
- 尽量不增加独立配置文件，优先将 Astral 工具链配置集中在 `pyproject.toml`

约定后端标准命令为：

```bash
uv sync --extra dev
uv run ruff format app tests
uv run ruff check app tests
uv run ty check
uv run pytest
```

### 2. `scripts/test_api.sh` 作为后端统一验证入口

将 `scripts/test_api.sh` 明确为后端验证主入口，串行执行：

1. `uv sync --extra dev`
2. `uv run ruff check app tests`
3. `uv run ty check`
4. `uv run pytest`

这样仓库根的 `pnpm run test:api` 不需要知道内部细节，只调用统一脚本即可。

### 3. CI 与本地命令保持同构

更新 `.github/workflows/ci-fast.yml`，确保后端步骤与本地一致：

- 安装 `uv`
- 在 `packages/api/` 下执行 `uv sync --extra dev`
- 调用 `./scripts/test_api.sh` 或等价的后端标准链

关键原则：CI 不再额外维护一套与本地不同的后端验证命令。

### 4. 根入口只做转发，不重复定义后端事实

保留根 `package.json` 中的：

- `test:api`
- `verify`
- `verify:full`

但这些入口只负责调用后端统一脚本，不在根目录重复拼装后端细节。

这样可以保持 monorepo 易用性，同时避免“后端验证真源”散落在根脚本和包配置中。

### 5. 文档与验证矩阵同步

同步更新：

- `README.md`
- `docs/verification-matrix.md`
- 必要时更新 `docs/acceptance/README.md` 或后端相关 acceptance 文档

文档中的后端最小验证口径统一为：

- `uv run ruff check app tests`
- `uv run ty check`
- `uv run pytest`

仓库根入口仍可保留 `pnpm run test:api` 作为便捷命令，但文档需说明其内部调用的是后端标准工具链。

## 文件边界

本次改造预期触达的主要文件：

- `packages/api/pyproject.toml`
- `packages/api/uv.lock`
- `scripts/test_api.sh`
- `.github/workflows/ci-fast.yml`
- `README.md`
- `docs/verification-matrix.md`
- 视需要补充的 acceptance 文档

若为让 `ty` 通过而出现少量历史类型问题，也可能触达部分 `packages/api/app/**` 或 `packages/api/tests/**` 文件，但应保持小 diff、只修阻塞项。

## 数据流与执行流

### 本地开发

```text
开发者
  -> uv sync --extra dev
  -> uv run ruff check app tests
  -> uv run ty check
  -> uv run pytest
```

### 仓库根入口

```text
pnpm run test:api
  -> ./scripts/test_api.sh
  -> packages/api 内统一执行 uv + ruff + ty + pytest
```

### CI

```text
GitHub Actions
  -> 安装 uv
  -> uv sync --extra dev
  -> scripts/test_api.sh
  -> 产出与本地一致的验证结果
```

## 错误处理与约束

- 若 `ty` 暴露历史类型问题，优先做最小修复；仅在确有必要时使用局部忽略，并要求忽略范围最小、理由明确
- 不允许通过大面积关闭类型检查来“接入成功”
- 若某些第三方库类型信息不足，应优先局部收窄边界而不是放宽全局检查
- `ruff` 继续作为后端格式与 lint 唯一入口，不引入额外 Python lint / format 工具

## 验证策略

最低验证链路：

```bash
cd packages/api
uv sync --extra dev
uv run ruff check app tests
uv run ty check
uv run pytest
```

仓库根联动验证：

```bash
pnpm run test:api
```

若 CI workflow 被修改，还需至少验证：

```bash
git diff .github/workflows/ci-fast.yml
```

并确认其命令与本地口径一致。

## 风险与回滚

### 风险

- `ty` 首次接入可能暴露历史类型问题，导致本轮改动范围略大于纯配置修改
- 脚本和文档口径统一后，旧命令说明可能失效，需要同步更新引用
- CI 若缓存或工作目录处理不当，可能出现“本地能跑、CI 失败”的路径问题

### 回滚点

若需要回滚，可按层次撤回：

1. 回退 `packages/api/pyproject.toml` 与 `packages/api/uv.lock`
2. 回退 `scripts/test_api.sh`
3. 回退 `.github/workflows/ci-fast.yml`
4. 回退 README / docs 中新的工具链口径

## 预期结果

完成后，仓库内关于后端工具链的稳定事实应为：

- 后端开发与验证使用 `uv`
- lint / format 使用 `ruff`
- 类型检查使用 `ty`
- 测试使用 `pytest`
- 本地、脚本、CI、文档都围绕同一链路工作

这会把“后端使用 uv / ruff / ty 工具链”从偏口头约定，提升为仓库内可执行、可验证、可维护的统一事实。
