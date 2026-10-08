"""清洗 wangekxy/tcm-formulary 已公开样本：方书来源节点 + 词表提及。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from graph_schema.constants import EdgeType, NodeType

from data_ingestion.dataset_records import DatasetRecord, compute_stats
from data_ingestion.entity_identity import EntityDraft
from data_ingestion.organize_workflow import finalize_drafts
from data_ingestion.provenance import prompt_hash_for
from data_ingestion.tcmchat_case_units import default_lexicon_paths, load_lexicon, longest_lexicon_hits

SOURCE_ID = "tcm-formulary"
IMPORT_SCOPE_KEY = "huggingface:wangekxy/tcm-formulary"
DEFAULT_BATCH_ID = "2026-08-20-tcm-formulary-sample-v1"
PROCESSOR = "tcm_formulary"
PROMPT_HASH = prompt_hash_for(Path(__file__))


class TcmFormularyError(ValueError):
    pass


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


DEFAULT_INPUT_PATH = (
    repo_root() / ".cache/huggingface/wangekxy/tcm-formulary/sample.jsonl"
)


def load_works(path: Path) -> list[dict[str, Any]]:
    works: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        payload = json.loads(line)
        title = str(payload.get("title") or "").strip()
        text = str(payload.get("text") or "")
        if not title or not text.strip():
            raise TcmFormularyError(f"sample.jsonl:{line_no} missing title or text")
        works.append(
            {
                "title": title,
                "dynasty": str(payload.get("dynasty") or ""),
                "author": str(payload.get("author") or ""),
                "text": text,
                "line": line_no,
            }
        )
    if not works:
        raise TcmFormularyError("sample.jsonl is empty")
    return works


def clean_file(
    path: Path,
    *,
    source_id: str = SOURCE_ID,
    batch_id: str = DEFAULT_BATCH_ID,
    import_scope_key: str = IMPORT_SCOPE_KEY,
    lexicon_path: Path | list[Path] | None = None,
) -> tuple[list[DatasetRecord], dict[str, Any]]:
    if not path.is_file():
        raise TcmFormularyError(f"missing sample: {path}")
    works = load_works(path)
    lexicon = load_lexicon(lexicon_path if lexicon_path is not None else default_lexicon_paths())
    drafts: list[EntityDraft] = []
    mention_count = 0
    for work in works:
        drafts.append(
            EntityDraft(
                node_type=NodeType.SOURCE,
                raw_name=work["title"],
                role="方书",
                stable_id=work["title"],
                evidence_refs=[f"sample.jsonl:{work['line']}"],
                properties={
                    "tcm_type": "来源方书样本",
                    "source_book": work["title"],
                    "author": work["author"],
                },
            )
        )
        for name, node_type in longest_lexicon_hits(work["text"], lexicon):
            mention_count += 1
            drafts.append(
                EntityDraft(
                    node_type=NodeType(node_type),
                    raw_name=name,
                    role="方书提及",
                    stable_id=name,
                    evidence_refs=[f"sample.jsonl:{work['line']}:{name}"],
                    properties={"tcm_type": "来源方书提及"},
                    edges=[(EdgeType.ORIGINATED_FROM.value, work["title"])],
                )
            )
    records, quarantined, identity = finalize_drafts(
        drafts,
        source_id=source_id,
        batch_id=batch_id,
        import_scope_key=import_scope_key,
        processor=PROCESSOR,
    )
    report = {
        "publish": False,
        "license_status": "commercial_sample_only_full_set_not_held",
        "work_count": len(works),
        "lexicon_size": len(lexicon),
        "raw_mention_hits": mention_count,
        "titles": [work["title"] for work in works],
        "source_id": source_id,
        "batch_id": batch_id,
        "import_scope_key": import_scope_key,
        "processor": PROCESSOR,
        "prompt_hash": PROMPT_HASH,
        **identity,
        "quarantined": quarantined[:20],
    }
    return records, report


def write_clean_outputs(
    records: list[DatasetRecord], report: dict[str, Any], out_dir: Path
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    records_path = out_dir / "records.jsonl"
    stats_path = out_dir / "stats.json"
    records_path.write_text(
        "".join(record.model_dump_json(exclude_none=True) + "\n" for record in records),
        encoding="utf-8",
    )
    stats = {**compute_stats(records), **report}
    stats_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "records": str(records_path),
        "stats": str(stats_path),
        "record_count": len(records),
        "edge_count": sum(len(record.edges) for record in records),
        "publish": False,
    }
