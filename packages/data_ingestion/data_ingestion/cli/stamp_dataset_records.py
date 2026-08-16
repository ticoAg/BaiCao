"""给抽取 JSONL 打上 prompt_hash / scope，并去掉对图谱无用的字段。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from data_ingestion.dataset_records import DatasetRecord
from data_ingestion.provenance import DEFAULT_PROMPT_FILES, prompt_hash_for, scope_key_for, slim_record


def load_jsonl(path: Path) -> list[DatasetRecord]:
    records: list[DatasetRecord] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            record = DatasetRecord.model_validate(json.loads(line))
            record.validate_types()
            records.append(record)
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--prompt-file", type=Path)
    parser.add_argument("--scope-key")
    args = parser.parse_args()
    records = load_jsonl(args.records)
    if not records:
        raise SystemExit(f"no records in {args.records}")
    source_id = records[0].source_id
    prompt_file = args.prompt_file or DEFAULT_PROMPT_FILES.get(source_id)
    if prompt_file is None or not prompt_file.is_file():
        raise SystemExit("prompt file missing; pass --prompt-file")
    prompt_hash = prompt_hash_for(prompt_file)
    scope = args.scope_key or scope_key_for(source_id)
    slimmed = [slim_record(record, prompt_hash=prompt_hash, import_scope_key=scope) for record in records]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        "".join(record.model_dump_json(exclude_none=True) + "\n" for record in slimmed),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "records": len(slimmed),
                "prompt_hash": prompt_hash,
                "import_scope_key": scope,
                "out": str(args.out),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
