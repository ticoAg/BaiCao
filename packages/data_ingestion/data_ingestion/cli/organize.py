"""规则切分 + agent 抽取回写的整理入口。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from data_ingestion.dataset_records import compute_stats
from data_ingestion.models import ExtractionCandidate
from data_ingestion.organize_workflow import accept_agent_candidates
from data_ingestion.tcmchat_case_units import (
    DEFAULT_BATCH_ID,
    DEFAULT_INPUT_PATH,
    IMPORT_SCOPE_KEY,
    PROCESSOR,
    SOURCE_ID,
    dump_prepare,
    prepare_directory,
    repo_root,
)
from data_ingestion.tcmchat_textbooks import (
    DEFAULT_INPUT_PATH as TEXTBOOK_INPUT,
    dump_prepare as dump_textbooks,
    prepare_directory as prepare_textbooks,
)


def default_out_dir() -> Path:
    return repo_root() / "datasets/baicao-knowledge/sources/tcmchat-medical-cases/processed/latest"


def _prepare(args: argparse.Namespace) -> None:
    batch = prepare_directory(args.input, lexicon_path=args.lexicon)
    print(json.dumps(dump_prepare(batch, args.out_dir), ensure_ascii=False))


def _accept(args: argparse.Namespace) -> None:
    candidates: list[ExtractionCandidate] = []
    for line in args.extractions.read_text(encoding="utf-8").splitlines():
        if line.strip():
            candidates.append(ExtractionCandidate.model_validate(json.loads(line)))
    batch = accept_agent_candidates(
        candidates,
        source_id=SOURCE_ID,
        batch_id=args.batch_id,
        import_scope_key=IMPORT_SCOPE_KEY,
        processor=PROCESSOR,
    )
    args.out_dir.mkdir(parents=True, exist_ok=True)
    records_path = args.out_dir / "records.jsonl"
    stats_path = args.out_dir / "stats.json"
    records_path.write_text(
        "".join(record.model_dump_json(exclude_none=True) + "\n" for record in batch.records),
        encoding="utf-8",
    )
    stats = {
        **compute_stats(batch.records),
        **batch.report,
        "quarantined": batch.quarantined,
        "publish": False,
    }
    stats_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "records": str(records_path),
                "stats": str(stats_path),
                "record_count": len(batch.records),
                "publish": False,
            },
            ensure_ascii=False,
        )
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    prepare.add_argument("--out-dir", type=Path, default=default_out_dir())
    prepare.add_argument(
        "--lexicon",
        type=Path,
        default=repo_root()
        / "datasets/baicao-knowledge/sources/national-standard-terms/processed/latest/records.jsonl",
    )
    prepare.set_defaults(func=_prepare)
    textbooks = sub.add_parser("prepare-textbooks")
    textbooks.add_argument("--input", type=Path, default=TEXTBOOK_INPUT)
    textbooks.add_argument(
        "--out-dir",
        type=Path,
        default=repo_root() / "datasets/baicao-knowledge/sources/tcmchat-textbooks/processed/latest",
    )
    textbooks.add_argument(
        "--lexicon",
        type=Path,
        default=repo_root()
        / "datasets/baicao-knowledge/sources/national-standard-terms/processed/latest/records.jsonl",
    )
    textbooks.set_defaults(
        func=lambda args: print(
            json.dumps(
                dump_textbooks(
                    prepare_textbooks(args.input, lexicon_path=args.lexicon), args.out_dir
                ),
                ensure_ascii=False,
            )
        )
    )
    accept = sub.add_parser("accept")
    accept.add_argument("--extractions", type=Path, required=True)
    accept.add_argument("--out-dir", type=Path, default=default_out_dir())
    accept.add_argument("--batch-id", default=DEFAULT_BATCH_ID)
    accept.set_defaults(func=_accept)
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
