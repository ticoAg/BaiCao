# 本地开发 Makefile 与单 Session tmux 运行时设计

## 背景

当前仓库同时存在以下几类本地开发入口：

- `infra/docker-compose.yml` 中包含 `api`、`web`、`nginx`、数据库和中间件
- `scripts/dev-tmux.sh` 提供一套 tmux 启动方式
- `scripts/start_demo_tmux.sh` 提供另一套 demo 启动方式

这带来几个问题：

- 前后端到底应由容器还是本地进程启动，边界不够清晰
- tmux 编排分散在多个脚本中，行为和输出不一致
- 面向 agent 的操作面不够简洁，缺少统一的状态、日志和帮助入口
- 错误场景缺少渐进式引导，不利于快速恢复

本轮目标是把前后端本地开发入口收敛成一套 agent 友好的统一命令面。

## 目标

### 主要目标

1. 提供统一的 `make <resource> <action>` 开发命令面
2. 明确运行边界：`api` 与 `web` 仅本地启动，`deps` 仅通过 Docker Compose 管理
3. 使用单个 tmux session 承载整个本地开发工作面，通过不同 window 切换资源
4. 强化可观测性：统一支持 `status`、`logs`、`attach`、启动结果摘要和错误提示
5. 为 agent 提供低记忆负担、可恢复、可诊断的操作体验

### 非目标

- 不在本轮引入新的进程管理器，如 `pm2`、`supervisord`、`foreman`
- 不把数据库依赖改成纯本地原生安装运行
- 不处理生产部署或 CI 环境的运行入口
- 不扩展到仓库内所有脚本统一重构，只覆盖本地开发主链路

## 用户确认后的边界

基于本轮沟通，已确认以下约束：

- 前后端不再通过 Docker Compose 启动
- `infra/docker-compose.yml` 中应移除 `api`、`web`
- 调试主要服务于 agent，要求操作简洁、清晰、可观测
- 整个项目只使用一个 tmux session，通过不同 window 切换
- 命令面采用 `make <resource> <action>` 结构
- 第三段参数不采用裸位置参数，改用 `KEY=VALUE`
- 资源范围至少覆盖 `api`、`web`、`deps`，并提供 `stack` 作为组合资源
- 运行时实现语言可自选，允许 Bash、TypeScript 或 Python

## 设计决策

### 决策 1：采用 `Makefile` 作为统一命令入口

根目录新增 `Makefile`，作为唯一推荐入口。

`Makefile` 本身只做轻量转发，不承载复杂业务逻辑。这样可以：

- 保持命令短且符合用户预期
- 避免在 Make 语法里堆积复杂的 tmux 和诊断逻辑
- 让运行时实现更容易测试、重构和扩展

### 决策 2：运行时编排采用 Python 脚本

推荐新增一个 Python 脚本，例如 `scripts/dev_runtime.py`，作为统一运行时。

选择 Python 而不是纯 Bash 或 TypeScript 的原因：

- 更适合实现清晰的参数解析、帮助输出和错误分支
- 更容易做资源状态汇总、表格化输出和模糊提示
- 可以仅使用标准库完成，不引入额外运行时依赖
- 仓库本身已经要求本地开发具备 Python 环境，额外门槛低

不选择纯 Bash 作为主运行时的原因：

- tmux、compose、端口检查虽然适合 shell 调用，但复杂帮助文本、错误恢复提示、状态聚合较难维护
- 当资源和动作继续增加时，shell 分支和字符串处理会很快变脆

不选择 TypeScript 作为主运行时的原因：

- 会额外依赖 Node 运行链路和执行器，增加冷启动与调用前置条件
- 这类偏系统编排的任务并不需要引入前端工具链

### 决策 3：使用单个 tmux session 作为项目开发工作面

默认 session 名为 `baicao-dev`，整个项目只维护这一个 session。

推荐固定 window：

- `api`：本地 FastAPI 进程
- `web`：本地 Vite 开发进程
- `ops`：保留给 agent 或开发者执行临时命令、排查和人工干预

这样做的原因：

- attach 目标始终唯一，降低记忆负担
- agent 可以稳定地围绕同一个 session 工作
- 状态汇总和错误恢复更简单
- 对多资源联调更直观

### 决策 4：把依赖栈与应用进程彻底分离

`deps` 仅负责依赖容器：

- `postgres`
- `neo4j`
- `redis`

`api` 与 `web` 一律本地运行，不再由 `docker compose` 托管。

`stack` 作为组合资源，表示：

- 启动或关闭 `deps`
- 管理 `api` 和 `web` 对应的 tmux window
- 输出整个本地开发栈的统一状态

### 决策 5：帮助与错误提示采用渐进式引导

运行时必须提供：

- `make help`
- `make <resource> help`

并在错误场景下提供下一步建议，例如：

- 未知资源时提示候选资源和 `make help`
- 未知动作时提示该资源支持的动作和 `make <resource> help`
- 参数错误时给出合法值和示例
- 资源未启动时给出最短修复命令

这类提示的目标不是“报错即结束”，而是帮助 agent 和开发者快速恢复操作链路。

## 命令面设计

### 顶层命令

```bash
make help
make deps up
make deps down
make deps status
make deps logs

make api up
make api down
make api restart
make api status
make api logs
make api attach
make api help

make web up
make web down
make web restart
make web status
make web logs
make web attach
make web help

make stack up
make stack down
make stack restart
make stack status
make stack attach
make stack help
```

### 参数形式

第三段参数统一采用 Make 变量，而不是裸位置参数：

```bash
make api up PORT=8000
make web up PORT=3000
make api logs LINES=120
make stack up SESSION=baicao-dev
```

默认参数建议：

- `SESSION=baicao-dev`
- `API_PORT=8000`
- `WEB_PORT=3000`
- `LINES=80`

## 资源与动作语义

### `deps`

- `up`：启动 `postgres`、`neo4j`、`redis`
- `down`：关闭依赖容器
- `status`：展示 compose 层状态和关键端口可达性
- `logs`：展示依赖容器日志摘要，可按服务过滤

### `api`

- `up`：确保 session 存在，创建或复用 `api` window，并启动本地 FastAPI
- `down`：关闭 `api` window
- `restart`：重启 `api` window 中的进程
- `status`：检查 window、pane 进程、端口和 `/health`
- `logs`：读取 `api` window 最近输出
- `attach`：attach 到 session，并优先切到 `api` window
- `help`：展示资源帮助

### `web`

- `up`：确保 session 存在，创建或复用 `web` window，并启动本地前端 dev server
- `down`：关闭 `web` window
- `restart`：重启 `web` window 中的进程
- `status`：检查 window、端口和最近日志摘要
- `logs`：读取 `web` window 最近输出
- `attach`：attach 到 session，并优先切到 `web` window
- `help`：展示资源帮助

### `stack`

- `up`：启动 `deps`，等待依赖就绪，再启动 `api` 与 `web`
- `down`：关闭 `api`、`web` 并停止 `deps`
- `restart`：重启整个本地开发栈
- `status`：汇总 `deps`、`api`、`web` 的统一状态
- `attach`：attach 到默认 session
- `help`：展示组合资源帮助

## tmux 行为设计

### Session 策略

- session 默认名：`baicao-dev`
- 若 session 不存在，首次启动 `api`、`web` 或 `stack` 时自动创建
- 若 session 已存在，则复用

### Window 策略

- `api` 和 `web` 为固定窗口名
- `ops` 窗口在创建 session 时一并创建
- `up` 时若 window 已存在且进程健康，则提示“已运行”并返回成功
- `up` 时若 window 已存在但进程异常，则自动重启对应命令

### 启动命令

推荐命令如下：

- `api`：在 `packages/api` 下执行 `uv sync --extra dev` 后运行 `uv run uvicorn app.main:app --host 0.0.0.0 --port <API_PORT> --reload`
- `web`：在 `packages/web` 下执行 `pnpm install` 后运行 `pnpm dev --host 0.0.0.0 --port <WEB_PORT>`

说明：

- `uv sync --extra dev` 和 `pnpm install` 可以在首次启动或缺依赖时执行；实现上可进一步优化为“必要时才执行”，但不作为本轮阻塞条件
- 运行时需注入与 compose 端口一致的本地开发环境变量，使 `api` 能连到 `deps`

### 日志读取

优先通过 `tmux capture-pane` 读取输出，而不是要求用户先 attach。

能力要求：

- 默认输出最近 `LINES` 行
- 资源未运行时返回清晰提示
- `stack status` 中可附带少量最近日志摘要，帮助快速判断故障

### 状态输出

建议使用稳定列结构，例如：

```text
RESOURCE  STATE    RUNTIME  TARGET             CHECK
deps      up       docker   postgres/neo4j/... ports reachable
api       up       tmux     baicao-dev:api     GET /health ok
web       up       tmux     baicao-dev:web     port reachable
```

并附加下一步建议：

- `Try: make api logs`
- `Try: make stack attach`

## 本地环境变量策略

运行时需要为本地 `api` 注入默认依赖地址，使其与当前 compose 端口一致：

- `DATABASE_URL=postgresql+asyncpg://baicao:baicao_password@localhost:15433/baicao`
- `DATABASE_PORT=15433`
- `NEO4J_URI=bolt://localhost:17687`
- `NEO4J_USER=neo4j`
- `NEO4J_PASSWORD=neo4j_password`
- `REDIS_URL=redis://localhost:16380`
- `OPENAI_API_KEY` 透传本地环境值

这些默认值可以在运行时中集中定义，避免散落在多个脚本里。

## Docker Compose 调整

`infra/docker-compose.yml` 应移除：

- `api`
- `web`
- `nginx`

保留：

- `postgres`
- `neo4j`
- `redis`

移除 `nginx` 的原因：

- 它当前依赖 `api` / `web` 容器，不符合“前后端仅本地启动”的新边界
- 若后续仍需要本地反向代理，应另行设计基于本地进程的代理策略，而不是保留失配的容器配置

## 兼容与迁移策略

### 旧脚本处理

- `scripts/dev-tmux.sh` 不立即删除
- 先改为薄兼容层：输出迁移提示，或直接转发到新运行时
- `scripts/start_demo_tmux.sh` 保留 demo 数据预热职责，但 session/window 编排复用新运行时

### README 更新

需同步更新 `README.md` 中的快速开始：

- 弱化“全栈容器启动”
- 强调 `make deps up`、`make stack up`
- 明确前后端默认本地运行

## 实施落位

本轮实施预计涉及以下文件：

- `Makefile`
- `scripts/dev_runtime.py`
- `scripts/dev-tmux.sh`
- `scripts/start_demo_tmux.sh`
- `infra/docker-compose.yml`
- `README.md`

## 验证策略

最低验证建议：

1. `docker compose -f infra/docker-compose.yml config`
2. `make help`
3. `make deps up`
4. `make stack up`
5. `make stack status`
6. `make api logs`
7. `make web logs`
8. `make stack down`

如果因本地环境缺少 `tmux`、`docker compose`、`uv` 或 `pnpm` 导致无法完整验证，需要在实施结论中明确写出阻塞项和复现命令。

## 风险与取舍

### 风险 1：本地依赖安装耗时

首次 `api up` / `web up` 可能包含 `uv sync` 或 `pnpm install`，会拉长启动时间。

取舍：

- 先保证入口统一和行为清晰
- 后续如有必要，可再增加依赖缓存探测或 `doctor/bootstrap` 动作

### 风险 2：tmux 与本地工具链强依赖

这套方案默认开发机具备：

- `tmux`
- `docker compose`
- `uv`
- `pnpm`

取舍：

- 这是当前仓库本地开发链路本来就依赖的能力
- 运行时应在缺失时给出明确安装提示，而不是静默失败

### 风险 3：单 session 可能被手工改坏

开发者或 agent 可能手工关闭 pane、改名 window、在 `ops` 中执行长期任务。

取舍：

- 运行时按固定 window 名和状态探测做幂等恢复
- 不要求严格控制 session 内所有手工操作，但对 `api` / `web` 这两个窗口保持强约束

## 结论

本设计将本地开发主链路收敛为：

- `Makefile` 统一命令面
- Python 运行时负责 tmux / compose / 观测逻辑
- `deps` 使用 Docker Compose
- `api` / `web` 使用单 session tmux 本地运行

这样可以在不引入额外复杂度的前提下，显著提升本地开发操作的一致性、可观测性和 agent 友好性，并为后续 implementation plan 提供明确、聚焦、可执行的边界。
