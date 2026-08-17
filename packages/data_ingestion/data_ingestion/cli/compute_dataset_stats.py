"""从 processed JSONL 计算统计，并回写 stats.json / catalog / VIEW 数量段。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from knowledge_model.graph_i18n import SCOPE_VALUE_EN_TO_ZH, SOURCE_VALUE_EN_TO_ZH

from data_ingestion.dataset_records import DatasetRecord, compute_stats


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def load_jsonl(path: Path) -> list[DatasetRecord]:
    records: list[DatasetRecord] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        raw = json.loads(line)
        record = DatasetRecord.model_validate(raw)
        record.validate_types()
        records.append(record)
    if not records:
        raise ValueError(f"no records in {path}")
    return records


def localized_source_name(source_id: str) -> str:
    return SOURCE_VALUE_EN_TO_ZH.get(source_id, source_id)


def localized_scope_key(filter_key: str) -> str:
    return SCOPE_VALUE_EN_TO_ZH.get(filter_key, filter_key)


def render_view(source_id: str, stats: dict[object, object], filter_key: str) -> str:
    node_rows = "\n".join(
        f"| {name} | {count} |"
        for name, count in sorted((stats.get("node_type_counts") or {}).items())
    )
    edge_rows = "\n".join(
        f"| {name} | {count} |"
        for name, count in sorted((stats.get("edge_type_counts") or {}).items())
    )
    batch_rows = "\n".join(
        f"| `{batch_id}` | {body['unit_count']} | {body['record_count']} |"
        for batch_id, body in (stats.get("by_batch") or {}).items()
    )
    source_name = localized_source_name(source_id)
    scope_key = localized_scope_key(filter_key)
    return f"""# VIEW · {source_id}

本页数量由 `compute_dataset_stats` 生成，不要手改数字。

## 处理状态

| 项 | 值 |
|----|----|
| records | {stats.get("record_count")} |
| units | {stats.get("unit_count")} |
| batches | {len(stats.get("batch_ids") or [])} |
| generated_at | {stats.get("generated_at")} |

## 批次

| batch_id | units | records |
|----------|-------|---------|
{batch_rows}

## 节点类型

| 类型 | 数量 |
|------|------|
{node_rows}

## 关系类型

| 类型 | 数量 |
|------|------|
{edge_rows}

## 筛选

```cypher
MATCH (n)
WHERE n.导入源 = '{source_name}'
   OR '{source_name}' IN coalesce(n.导入源列表, [])
RETURN n
```

按批次：

```cypher
MATCH (n)
WHERE n.导入批次 = '<batch_id>'
   OR '<batch_id>' IN coalesce(n.导入批次列表, [])
RETURN n
```

scope key: `{scope_key}`
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--filter-key", required=True)
    args = parser.parse_args()
    records = load_jsonl(args.records)
    unexpected = {record.source_id for record in records if record.source_id != args.source_id}
    if unexpected:
        raise SystemExit(f"source_id mismatch: {unexpected}")
    stats = compute_stats(records)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    stats_path = args.out_dir / "stats.json"
    if stats_path.is_file():
        previous = json.loads(stats_path.read_text(encoding="utf-8"))
        for key in ("entries_succeeded", "entries_failed", "runs"):
            if key in previous and key not in stats:
                stats[key] = previous[key]
    stats_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    view_path = args.out_dir.parent.parent / "VIEW.md"
    if view_path.parent.name.startswith("sources") or (args.out_dir.parent.parent / "SOURCE.md").exists():
        view_path.write_text(render_view(args.source_id, stats, args.filter_key), encoding="utf-8")
    print(json.dumps({"stats": str(stats_path), **{k: stats[k] for k in ("record_count", "unit_count")}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
