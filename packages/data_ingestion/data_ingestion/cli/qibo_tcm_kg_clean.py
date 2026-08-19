"""把 Knowlegde_Graph_TCM 关系 JSON 洗成 records.jsonl 与 stats.json。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from data_ingestion.qibo_tcm_kg import (
    DEFAULT_BATCH_ID,
    DEFAULT_FANGJI_PATH,
    DEFAULT_ZHONGYAO_PATH,
    IMPORT_SCOPE_KEY,
    SOURCE_ID,
    clean_relation_files,
    repo_root,
    write_clean_outputs,
)


def default_out_dir() -> Path:
    return (
        repo_root()
        / "datasets/baicao-knowledge/sources/fengxi177-knowledge-graph-tcm/processed/latest"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zhongyao", type=Path, default=DEFAULT_ZHONGYAO_PATH)
    parser.add_argument("--fangji", type=Path, default=DEFAULT_FANGJI_PATH)
    parser.add_argument("--out-dir", type=Path, default=default_out_dir())
    parser.add_argument("--batch-id", default=DEFAULT_BATCH_ID)
    parser.add_argument("--source-id", default=SOURCE_ID)
    parser.add_argument("--scope", default=IMPORT_SCOPE_KEY)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    if not args.zhongyao.is_file():
        raise SystemExit(f"zhongyao relations not found: {args.zhongyao}")
    if not args.fangji.is_file():
        raise SystemExit(f"fangji relations not found: {args.fangji}")
    records = clean_relation_files(
        args.zhongyao,
        args.fangji,
        batch_id=args.batch_id,
        source_id=args.source_id,
        import_scope_key=args.scope,
    )
    summary = write_clean_outputs(records, args.out_dir)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
