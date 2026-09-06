"""清洗 wangekxy 专题 HF sample.jsonl。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from data_ingestion.wangekxy_topic_sample import (
    clean_file,
    repo_root,
    write_clean_outputs,
)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--batch-id", required=True)
    parser.add_argument("--scope", required=True)
    parser.add_argument("--role", default="专题古籍")
    parser.add_argument("--tcm-type", default="来源专题古籍")
    args = parser.parse_args(argv)
    records, report = clean_file(
        args.input,
        source_id=args.source_id,
        batch_id=args.batch_id,
        import_scope_key=args.scope,
        role=args.role,
        tcm_type=args.tcm_type,
    )
    print(json.dumps(write_clean_outputs(records, report, args.out_dir), ensure_ascii=False))


if __name__ == "__main__":
    main()
