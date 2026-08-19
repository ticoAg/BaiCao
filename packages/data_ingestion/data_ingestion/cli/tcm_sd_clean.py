"""把 TCM-SD 证候词表洗成本地 records.jsonl 与质量统计。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from data_ingestion.tcm_sd import (
    DEFAULT_BATCH_ID,
    DEFAULT_INPUT_PATH,
    IMPORT_SCOPE_KEY,
    SOURCE_ID,
    clean_directory,
    repo_root,
    write_clean_outputs,
)


def default_out_dir() -> Path:
    return repo_root() / "datasets/baicao-knowledge/sources/tcm-sd/processed/latest"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--out-dir", type=Path, default=default_out_dir())
    parser.add_argument("--batch-id", default=DEFAULT_BATCH_ID)
    parser.add_argument("--source-id", default=SOURCE_ID)
    parser.add_argument("--scope", default=IMPORT_SCOPE_KEY)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    records, report = clean_directory(
        args.input,
        source_id=args.source_id,
        batch_id=args.batch_id,
        import_scope_key=args.scope,
    )
    print(
        json.dumps(
            write_clean_outputs(records, report, args.out_dir), ensure_ascii=False
        )
    )


if __name__ == "__main__":
    main()
