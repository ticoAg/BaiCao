# Infisical CLI Env Injection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 BaiCao 的本地开发主路径和测试脚本增加 Infisical CLI 自动环境注入能力，让用户只需配置 Infisical 相关环境变量。

**Architecture:** 在 `scripts/dev_runtime.py` 中增加统一的 Infisical 包装层，并在测试脚本中复用相同的自动检测规则。应用代码不感知 Infisical，仍然只读取进程环境变量。

**Tech Stack:** Python 3 standard library, Bash, Docker Compose, tmux, uv, pnpm, Infisical CLI

---

## 实施状态更新（2026-03-29）

### 已完成

- `scripts/dev_runtime.py` 已增加 Infisical 自动检测与 `infisical run` 包装逻辑，可覆盖 `deps` 的 compose 命令，以及 `api` / `web` tmux window 中的本地进程启动命令
- `scripts/test_integration.sh`、`scripts/test_e2e.sh` 已增加同样的自动检测逻辑，集成测试和 E2E 在启用 Infisical 时会通过 CLI 注入环境变量
- `scripts/tests/test_dev_runtime.py` 已补充 Infisical 包装层的命令构造和缺失 CLI 提示测试
- `README.md` 与 `infra/.env.example` 已补充 Infisical 使用说明和口径

### 验证目标

- `python3 -m unittest discover -s scripts/tests -p 'test_dev_runtime.py' -v`
- `docker compose -f infra/docker-compose.yml config`

### 风险与备注

- 本轮不引入 Infisical SDK，应用层仍保持 `.env` / `process.env` / `BaseSettings` 的现有模式
- 若启用 Infisical 但本机缺少 CLI，会返回明确的缺失工具提示
