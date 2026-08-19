"""把国标疾病、证候和成方制剂洗成本地 records.jsonl。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from data_ingestion.national_standard_terms import (
    DEFAULT_BATCH_ID,
    DEFAULT_INPUT_PATH,
    IMPORT_SCOPE_KEY,
    SOURCE_ID,
    clean_directory,
    repo_root,
    write_clean_outputs,
)


def default_out_dir() -> Path:
    return repo_root() / "datasets/baicao-knowledge/sources/national-standard-terms/processed/latest"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--out-dir", type=Path, default=default_out_dir())
    parser.add_argument("--batch-id", default=DEFAULT_BATCH_ID)
    parser.add_argument("--source-id", default=SOURCE_ID)
    parser.add_argument("--scope", default=IMPORT_SCOPE_KEY)
    args = parser.parse_args(argv)
    records, report = clean_directory(
        args.input,
        source_id=args.source_id,
        batch_id=args.batch_id,
        import_scope_key=args.scope,
    )
    print(json.dumps(write_clean_outputs(records, report, args.out_dir), ensure_ascii=False))


if __name__ == "__main__":
    main()
