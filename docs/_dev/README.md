# 研发草案

本目录包含正在开发中的文档草案。

## 草案元信息要求

在草案文件的前 20 行内必须写清：

- `Status:` Draft / WIP / Deprecated
- `Owner:`（可空，但建议写）
- `Expires:` YYYY-MM-DD（到期后要么毕业到稳定文档，要么归档/删除）
- `Graduation:` 目标稳定文档路径
- `Req:` 关联的 `docs/superpowers/plans/*.md`（若有）

## 示例

```markdown
<!--
Status: WIP
Owner: @username
Expires: 2026-04-01
Graduation: docs/architecture/llm-integration.md
Req: docs/superpowers/plans/YYYY-MM-DD-<topic>.md
-->

# LLM 集成设计（草案）

...
```

## 毕业路径

草案文档在满足以下条件后可"毕业"到 `docs/architecture/` 或 `docs/acceptance/`：

1. 经过至少一次评审
2. 有可执行的验收标准
3. Owner 确认稳定

## 归档路径

草案文档在以下情况下应归档或删除：

1. 过期未毕业
2. 对应需求已取消
3. 被新草案替代
