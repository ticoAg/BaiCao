"""盘点 TCMChat-dataset-600k 本地缓存，不把原文整包写入图谱。"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from data_ingestion.dataset_records import DatasetRecord, compute_stats
from data_ingestion.provenance import prompt_hash_for

SOURCE_ID = "tcmchat-600k"
IMPORT_SCOPE_KEY = "huggingface:ZJUFanLab/TCMChat-dataset-600k"
DEFAULT_BATCH_ID = "2026-08-19-tcmchat-600k-v1"
PROCESSOR = "tcmchat_600k"
PROMPT_HASH = prompt_hash_for(Path(__file__))

EXPECTED_GROUPS = {
    "books/national_standard": "pretrain/train/books/national_standard",
    "books/textbook": "pretrain/train/books/textbook",
    "books/medical_case": "pretrain/train/books/medical_case",
    "opendata": "pretrain/train/opendata",
    "web": "pretrain/train/web",
    "papers": "pretrain/train/papers",
    "pretrain_test": "pretrain/test",
    "sft_train": "sft/train",
    "sft_test": "sft/test",
    "sft_baichuan": "sft/final_train_data_for_baichuan_format",
}


class TcmChat600kError(ValueError):
    pass


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


DEFAULT_INPUT_PATH = (
    repo_root() / ".cache/huggingface/ZJUFanLab/TCMChat-dataset-600k"
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _iter_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if "download" in path.parts:
            continue
        if path.name in {".gitattributes", ".gitignore", "logo.png"}:
            continue
        if path.suffix.lower() in {".md"}:
            continue
        files.append(path)
    return files


def clean_directory(
    path: Path,
    *,
    source_id: str = SOURCE_ID,
    batch_id: str = DEFAULT_BATCH_ID,
    import_scope_key: str = IMPORT_SCOPE_KEY,
) -> tuple[list[DatasetRecord], dict[str, Any]]:
    if not path.is_dir():
        raise TcmChat600kError(f"input is not a directory: {path}")

    files = _iter_files(path)
    if not files:
        raise TcmChat600kError("no content files found")

    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for file_path in files:
        rel = file_path.relative_to(path).as_posix()
        group = "other"
        for name, prefix in EXPECTED_GROUPS.items():
            if rel.startswith(prefix + "/") or rel == prefix:
                group = name
                break
        groups[group].append(
            {
                "path": rel,
                "bytes": file_path.stat().st_size,
            }
        )

    standard_dir = path / "pretrain/train/books/national_standard"
    test_dir = path / "pretrain/test"
    identical_test: list[str] = []
    divergent_test: list[str] = []
    if standard_dir.is_dir() and test_dir.is_dir():
        for standard in sorted(standard_dir.glob("*.txt")):
            counterpart = test_dir / standard.name
            if not counterpart.is_file():
                continue
            if _sha256(standard) == _sha256(counterpart):
                identical_test.append(standard.name)
            else:
                divergent_test.append(standard.name)

    papers = path / "pretrain/train/papers"
    missing_papers = not papers.is_dir() or not any(papers.glob("*"))

    records: list[DatasetRecord] = []
    report = {
        "publish": False,
        "license_status": "apache-2.0_dataset_filter_brand_and_pii",
        "file_count": len(files),
        "total_bytes": sum(item["bytes"] for items in groups.values() for item in items),
        "group_counts": {
            name: {
                "files": len(items),
                "bytes": sum(item["bytes"] for item in items),
                "names": [item["path"].rsplit("/", 1)[-1] for item in items],
            }
            for name, items in sorted(groups.items())
        },
        "identical_pretrain_test_copies": identical_test,
        "divergent_pretrain_test_copies": divergent_test,
        "missing_papers": missing_papers,
        "mapped_relation_counts": {},
        "quarantine_counts": {
            "duplicate_test_files": len(identical_test),
            "sft_conversation_files": len(groups.get("sft_baichuan", [])),
            "missing_paper_dir": int(missing_papers),
        },
        "quality_samples": {
            "identical_pretrain_test_copies": identical_test,
            "divergent_pretrain_test_copies": divergent_test,
        },
        "source_id": source_id,
        "batch_id": batch_id,
        "import_scope_key": import_scope_key,
        "processor": PROCESSOR,
        "prompt_hash": PROMPT_HASH,
    }
    return records, report


def write_clean_outputs(
    records: list[DatasetRecord], report: dict[str, Any], out_dir: Path
) -> dict[str, Any]:
    if records:
        raise TcmChat600kError("TCMChat-600k inventory must not emit graph records this round")
    out_dir.mkdir(parents=True, exist_ok=True)
    records_path = out_dir / "records.jsonl"
    stats_path = out_dir / "stats.json"
    records_path.write_text("", encoding="utf-8")
    stats = {**compute_stats(records), **report}
    stats_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "records": str(records_path),
        "stats": str(stats_path),
        "record_count": 0,
        "edge_count": 0,
        "publish": False,
    }
