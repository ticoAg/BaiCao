# Plans

Dated execution plans. Product, architecture, interaction, and data-model facts stay in the durable docs tree; files here only say how to land, in what order, and what to verify.

Layout: `YYYY/MM-DD/<plan-name>-<hex>.md`. Mint files with the `plan-docs` skill script; do not invent paths. Todos use `- [ ]` / `- [x]` / `- [-]`; scan and print sections with `scripts/todos.py`.

仓库里更早的任务拆解仍在 [`docs/superpowers/plans/`](../superpowers/plans/README.md)。新的按日落盘执行计划从这里建。

# This layer

- [2026](2026/README.md)
  - [问答 chat 走最新 MCP 并清适配](2026/09-06/问答-chat-走最新-mcp-并清适配-b042.md) — 升官方 mcp v2；产品 chat 改同进程 MCP 客户端；删问答侧遗留适配
  - [问答 agent MCP 检索收口](2026/09-06/问答-agent-mcp-检索收口-8eca.md) — 轻量图检索：tool 契约、schema Resource；runtime 口径已被上一条取代
  - [中文属性与实体消歧合并](2026/09-06/中文属性与实体消歧合并-94ae.md) — 剥离拼音/拉丁名，收口身份模块，重发 HF 并重建图
  - [清洗完成后删除原文与中间态](2026/09-06/清洗完成后删除原文与中间态-4fa3.md) — 30 源已清洗后删除 `.cache` 原文与 `work` 中间态，保留 JSONL

# Parent

* [docs/](../README.md) — documentation root.
