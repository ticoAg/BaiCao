# Infisical CLI 环境变量注入设计

## 背景

当前 BaiCao 的本地开发主路径已经统一到根目录 `Makefile` 和 `scripts/dev_runtime.py`：

- `deps` 通过 `docker compose` 管理依赖容器
- `api` 与 `web` 通过 tmux window 启动本地进程
- `scripts/test_integration.sh`、`scripts/test_e2e.sh` 负责测试时的依赖和临时进程拉起

在这个结构下，如果继续让前后端分别自行集成 Infisical SDK，会把 secret 拉取逻辑散落到应用运行时代码里，既增加维护成本，也和当前“前后端主要从进程环境读取配置”的事实不匹配。

## 目标

1. 让前后端和测试脚本都支持通过 Infisical CLI 注入环境变量
2. 用户本地只需要配置 Infisical 相关环境变量，不再要求同时维护一套业务环境变量
3. 不侵入应用运行时代码，不把 Infisical SDK 引入 API / Web 的业务逻辑
4. 未启用 Infisical 时，保持现有本地开发与测试行为不变

## 非目标

- 不在本轮为 API 或 Web 接入 Infisical SDK
- 不改变现有 `BaseSettings` / Vite 读取环境变量的方式
- 不要求所有开发者都必须使用 Infisical

## 设计决策

### 决策 1：统一使用 Infisical CLI，而不是 SDK

Infisical 只作为“进程启动前的环境注入层”存在：

- `make deps/api/web/stack ...`
- `scripts/test_integration.sh`
- `scripts/test_e2e.sh`

这样前端继续用 `process.env` / `import.meta.env`，后端继续用 `pydantic-settings`，不需要知道 secret 从哪里来。

### 决策 2：采用“自动检测并启用”的行为

当满足任一条件时，运行时自动改为使用 `infisical run`：

- 仓库根目录存在 `infisical.json` 或 `.infisical.json`
- 当前 shell 中存在任一 Infisical 相关环境变量：
  - `INFISICAL_TOKEN`
  - `INFISICAL_API_URL`
  - `INFISICAL_PROJECT_ID`
  - `INFISICAL_ENV`
  - `INFISICAL_PATH`
  - `INFISICAL_DISABLE_UPDATE_CHECK`

未满足条件时，完全保持当前行为。

### 决策 3：把根目录作为 project config dir

由于 API / Web / 测试脚本常常在 `packages/...` 子目录执行，若仓库根目录存在 `infisical.json` / `.infisical.json`，需要显式把根目录传给 CLI，避免子目录执行时找不到项目配置。

因此统一约定：

- 只要检测到根目录配置文件，就为 `infisical run` 追加 `--project-config-dir=<repo-root>`

### 决策 4：只使用一组 Infisical 相关环境变量

用户本地只需要维护 Infisical 相关变量；业务变量例如：

- `DATABASE_URL`
- `NEO4J_PASSWORD`
- `OPENAI_API_KEY`
- `WEB_API_BASE_URL`

统一放进 Infisical secret，由 CLI 在启动时注入。

## 影响范围

- `scripts/dev_runtime.py`
- `scripts/test_integration.sh`
- `scripts/test_e2e.sh`
- `README.md`
- `infra/.env.example`
- `scripts/tests/test_dev_runtime.py`

## 验证策略

最小验证包括：

1. `scripts/tests/test_dev_runtime.py` 增加 Infisical 包装层回归测试
2. `docker compose -f infra/docker-compose.yml config`
3. 保持现有帮助 / 运行时测试通过

## 风险

- 若用户显式触发了 Infisical 模式但本机未安装 `infisical` CLI，启动会失败；因此需要给出明确的缺失工具提示
- `deps` 通过 `infisical run docker compose ...` 启动时，只有插值变量来自 Infisical，容器内环境仍由 compose 文件定义，这是本轮预期行为
