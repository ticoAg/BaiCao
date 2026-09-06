---
type: Implementation Plan
title: 剩余已持有原文词表抽取入图
description: 对清理后仍保留的古籍全文、ChatMed 剩余行、ZY-BERT 非索引正文做现有类型词表抽取，publish 保持 false。
resource: docs/superpowers/plans/2026-08-20-remaining-held-extract.md
tags: [data-sources, data-ingestion]
timestamp: 2026-08-20T00:00:00+08:00
status: active
---

# 剩余已持有原文词表抽取入图

**Goal:** 把上一轮留下、尚未整包抽取的原文抽成 `来源` + 词表提及 + `来源于`，写入各源 `processed/latest` 并入本地 Neo4j。`publish: false`。不发明 `NodeType` / `EdgeType`。

**Architecture:** 沿用 classical-tcm-canon / wangekxy sample 变换。catalog / data-sources / graph_i18n 由主代理合并。子代理按非重叠范围跑清洗器。

**Status:** done

## 范围

| 源 | 做什么 | 不做什么 |
|---|---|---|
| `tcm-ancient-books` | 699 本编号 TXT 正文词表提及；203 用替换解码；700 李培生作现代医论来源 | 不把 OCR 当已验证事实 |
| `tcmchat-chatmed` | 取消 8000 行上限，全量唯一提及 | 仍标「对话提及」，不当事实 |
| `zybert-pretrain-corpus` | 在已有方剂索引上，对非索引行补唯一词表提及 | 不覆盖已有组成边 |

百科 / 论文 / `entity_extraction` / `recommend_herb` / knowledge / daiy 已抽过，本轮不重跑。

## 入图契约

- 节点/边只能用 `packages/knowledge_model` 已有枚举
- `publish: false`
- 记录 `pending`
