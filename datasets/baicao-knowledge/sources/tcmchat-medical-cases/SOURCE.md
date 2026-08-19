# TCMChat 名医验案（agent 协作）

## 身份

- `source_id`: `tcmchat-medical-cases`
- 载体：`pretrain/train/books/medical_case/` 18 本 TXT
- 状态：已 `prepare`，等待 agent 抽取后 `accept`
- `publish: false`

## 协作方式

```text
规则切分/去标识
  -> agent_queue.jsonl
  -> agent 按 ExtractionCandidate 抽取
  -> organize accept（身份门禁 + 品牌隔离）
  -> records.jsonl
  -> importer / Neo4j
```

命令：

```bash
cd packages/data_ingestion
uv run python -m data_ingestion.cli.organize prepare
uv run python -m data_ingestion.cli.organize accept --extractions <agent.jsonl>
```

规则层已切出 461 个去标识单元。姓氏+年龄已替换为「患者」。agent 只允许输出病证、方剂、药材、治法，不得回写姓名或商品名。

本轮尚未执行 accept，图记录为 0。
