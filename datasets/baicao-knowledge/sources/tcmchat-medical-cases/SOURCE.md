# TCMChat 名医验案（agent 协作）

## 身份

- `source_id`: `tcmchat-medical-cases`
- 载体：`pretrain/train/books/medical_case/` 18 本 TXT
- 状态：`imported`（已入本地图；agent 仍可补抽）；`publish: false`
- `publish: false`

## 过滤

去掉姓氏（`汤某` → `患者`），**保留性别和年龄**（`女22岁`、`男40岁`）。电话、证件、住院号、国药准字仍过滤。

## 协作

规则：切分 461 案，写入医案节点，并用国标词表做最长匹配。
agent：继续从 `agent_queue.jsonl` 补药材/治法等规则没抓住的项，经 `organize accept` 入图。

## 本轮产量

- 医案 461，其中 113 案解析到性别
- 病证提及 3,189，方剂提及 339
- 合计 3,989 records；提及边为 `记载于医案`
