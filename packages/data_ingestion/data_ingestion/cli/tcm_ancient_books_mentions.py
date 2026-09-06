"""从 TCM-Ancient-Books 正文抽词表提及。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from data_ingestion.tcm_ancient_books import (
    DEFAULT_INPUT_PATH,
    IMPORT_SCOPE_KEY,
    MENTION_BATCH_ID,
    SOURCE_ID,
    extract_directory,
    repo_root,
    write_extract_outputs,
)


def default_out_dir() -> Path:
    return repo_root() / "datasets/baicao-knowledge/sources/tcm-ancient-books/processed/latest"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--out-dir", type=Path, default=default_out_dir())
    parser.add_argument("--batch-id", default=MENTION_BATCH_ID)
    parser.add_argument("--source-id", default=SOURCE_ID)
    parser.add_argument("--scope", default=IMPORT_SCOPE_KEY)
    parser.add_argument("--min-id", type=int, default=0)
    parser.add_argument("--max-id", type=int, default=999)
    parser.add_argument("--include-unnumbered", action="store_true")
    args = parser.parse_args(argv)
    records, report = extract_directory(
        args.input,
        source_id=args.source_id,
        batch_id=args.batch_id,
        import_scope_key=args.scope,
        min_id=args.min_id,
        max_id=args.max_id,
        include_unnumbered=args.include_unnumbered,
    )
    print(json.dumps(write_extract_outputs(records, report, args.out_dir), ensure_ascii=False))


if __name__ == "__main__":
    main()
