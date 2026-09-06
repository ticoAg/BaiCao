"""回写 JSONL：去掉拼音/拉丁名键、无汉字别名、证据里的纯拉丁行。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from data_ingestion.dataset_catalog import load_catalog
from data_ingestion.dataset_records import DatasetRecord
from data_ingestion.entity_identity import LATIN_NAME_KEYS, sanitize_record


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def source_jsonl_path(dataset_root: Path, source_id: str) -> Path:
    return dataset_root / "sources" / source_id / "processed" / "latest" / "records.jsonl"


def rewrite_jsonl(path: Path) -> dict[str, int]:
    tmp = path.with_suffix(".jsonl.tmp")
    total = 0
    changed = 0
    stripped_keys = 0
    with path.open(encoding="utf-8") as src, tmp.open("w", encoding="utf-8") as dst:
        for line in src:
            if not line.strip():
                continue
            total += 1
            payload = json.loads(line)
            properties = dict(payload.get("properties") or {})
            stripped_keys += sum(1 for key in LATIN_NAME_KEYS if key in properties)
            record = sanitize_record(DatasetRecord.model_validate(payload))
            next_payload = dict(payload)
            next_payload["properties"] = record.properties
            if record.evidence_text:
                next_payload["evidence_text"] = record.evidence_text
            else:
                next_payload.pop("evidence_text", None)
            if next_payload != payload:
                changed += 1
            dst.write(json.dumps(next_payload, ensure_ascii=False) + "\n")
    tmp.replace(path)
    return {"records": total, "rewritten": changed, "stripped_name_keys": stripped_keys}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, default=repo_root() / "datasets/baicao-knowledge")
    args = parser.parse_args()
    catalog = load_catalog(args.dataset_root / "catalog.json")
    reports = []
    for source in catalog.sources:
        path = source_jsonl_path(args.dataset_root, source.source_id)
        if not path.is_file():
            continue
        report = rewrite_jsonl(path)
        report["source_id"] = source.source_id
        report["path"] = str(path.relative_to(args.dataset_root) if path.is_relative_to(args.dataset_root) else path)
        reports.append(report)
    if not reports:
        missing = source_jsonl_path(args.dataset_root, catalog.sources[0].source_id)
        raise SystemExit(f"no records.jsonl under {args.dataset_root} (looked like {missing})")
    print(json.dumps({"ok": True, "sources": reports}, ensure_ascii=False))


if __name__ == "__main__":
    main()
