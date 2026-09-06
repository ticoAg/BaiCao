"""从 ZY-BERT 非索引行抽唯一词表提及，不覆盖方剂索引快照。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from data_ingestion.zybert_pretrain import (
    DEFAULT_EXTRACTED_PATH,
    IMPORT_SCOPE_KEY,
    MENTION_BATCH_ID,
    SOURCE_ID,
    extract_remaining_mentions,
    repo_root,
    write_clean_outputs,
)


def default_out_dir() -> Path:
    return (
        repo_root()
        / "datasets/baicao-knowledge/sources/zybert-pretrain-corpus/work/extracts/mentions"
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_EXTRACTED_PATH)
    parser.add_argument("--out-dir", type=Path, default=default_out_dir())
    parser.add_argument("--batch-id", default=MENTION_BATCH_ID)
    parser.add_argument("--source-id", default=SOURCE_ID)
    parser.add_argument("--scope", default=IMPORT_SCOPE_KEY)
    args = parser.parse_args(argv)
    records, report = extract_remaining_mentions(
        args.input,
        source_id=args.source_id,
        batch_id=args.batch_id,
        import_scope_key=args.scope,
    )
    print(json.dumps(write_clean_outputs(records, report, args.out_dir), ensure_ascii=False))


if __name__ == "__main__":
    main()
