# 验证矩阵

> 适用于 BaiCao 仓库内所有改动类型。目标不是追求最大验证量，而是保证每类改动至少有一条最小、可复现、与真实主链路一致的验证证据。

| 改动类型 | 最低验证 |
|---|---|
| `packages/web/` 页面 / 组件 / 前端服务 | `pnpm run test:web`；建议补 `pnpm --dir packages/web exec vp build` |
| `packages/api/` 服务 / 路由 / Schema | `uv run ruff check app tests` + `uv run ty check` + `uv run pytest -m "not integration"`（在 `packages/api/` 下执行） |
| 共享知识模型 / 导入导出 / `packages/data_ingestion/` | API 最低验证 + `cd packages/data_ingestion && uv run --with pytest pytest tests -q`；若改了共享契约，补对应 contract test |
| `packages/shared/` 共享类型 / DTO | `pnpm --dir packages/shared typecheck` + 至少一条消费方检查（通常是 `pnpm --dir packages/web exec vp build` 或相关 contract test） |
| `packages/db/` 图谱结构 / 导入样例 / 种子数据 | 至少一条可复现的数据或查询验证说明；若影响主链路，补 `./scripts/test_integration.sh` 或一条 API / 页面消费检查 |
| `infra/` 编排 / 环境模板 / 配置 | `docker compose -f infra/docker-compose.yml config`；若影响运行主链路，补一条启动或健康检查 |
| API contract / 跨模块负载变化 | 后端验证 + 一条前端消费侧检查；若是用户可感知主链路，建议同步更新相关 `docs/acceptance/` |
| OpenAI / LangChain / 问答链路 | 至少一条接口或服务验证；若外部依赖不可在本地完整验证，明确写出未验证项、环境依赖和复现命令 |
| 文档-only / 规范-only | 路径、命令、文件名、引用、作用域与当前仓库结构一致 |
| 工作流 / Agent 指导文档 | 阅读顺序、作用域边界、真源定义、命令与 `README.md` / `workflow.md` / `docs/README.md` 一致 |
| `docs/superpowers/plans/` / 验收文档状态更新 | 状态变更必须能追到对应实现证据、验证结果或明确的风险说明 |

## 验证优先级

1. 最小可复现
2. 与改动同层
3. 能证明上下游没有断链
4. 优先复用仓库现有统一命令，而不是临时拼接不可复用命令

## 统一命令入口

- API：`./scripts/test_api.sh`
- Web：`pnpm run test:web`
- 集成：`./scripts/test_integration.sh`
- E2E：`CI=true pnpm run test:e2e`
- 全量：`pnpm run verify:full`

补充口径：

- `packages/web` 的 `dev` / `build` / `test` / `preview` 统一走 `vp`；直接在包目录下执行时，优先使用 `pnpm --dir packages/web exec vp ...`
- 仓库根脚本（如 `pnpm run test:web`）允许继续作为统一入口使用，但底层仍应映射到 `vp`
- 对数据处理工作台这类页面定向回归，可使用 `pnpm --dir packages/web test --run src/pages/DataPipelinePage.test.tsx` 作为前端消费侧最小补充验证，再视情况补 `pnpm --dir packages/web exec vp build`

## 说明

- 若本轮无法执行某项验证，不要省略说明；请明确写出原因、阻塞条件与推荐复现命令。
- 文档改动通常不需要运行测试，但必须验证路径、引用、命令和当前仓库结构一致。
- 用户可感知的跨模块闭环改动，优先补 `docs/acceptance/` 中对应主链路文档，而不是只在最终回复里口头说明。
