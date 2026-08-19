"""只读审计 ZY-BERT 预训练 RAR：不解压、不入图。"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from data_ingestion.dataset_records import DatasetRecord, compute_stats
from data_ingestion.provenance import prompt_hash_for

SOURCE_ID = "zybert-pretrain-corpus"
IMPORT_SCOPE_KEY = "dropbox:zybert:tcm_pretrain_corpus_a.rar"
DEFAULT_BATCH_ID = "2026-08-19-zybert-pretrain-v1"
PROCESSOR = "zybert_pretrain"
PROMPT_HASH = prompt_hash_for(Path(__file__))
RAR_MAGIC = b"Rar!"


class ZybertPretrainError(ValueError):
    pass


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


DEFAULT_INPUT_PATH = (
    repo_root()
    / "tmp/qibo-datasets/TCM-Pretrain/zybert-corpus/tcm_pretrain_corpus_a.rar"
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


def parse_bsdtar_listing(listing: str) -> list[dict[str, Any]]:
    members: list[dict[str, Any]] = []
    for line in listing.splitlines():
        parts = line.split()
        if len(parts) < 9:
            continue
        name = parts[-1]
        try:
            size = int(parts[4])
        except ValueError:
            size = None
        members.append({"name": name, "size": size, "listing": line})
    if not members:
        raise ZybertPretrainError("rar listing is empty")
    return members


def list_rar_members(path: Path) -> list[dict[str, Any]]:
    try:
        result = subprocess.run(
            ["bsdtar", "-tvf", str(path)],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        raise ZybertPretrainError("bsdtar is required to list the rar archive") from exc
    if result.returncode != 0:
        raise ZybertPretrainError(
            f"bsdtar failed: {result.stderr.strip() or result.stdout.strip()}"
        )
    return parse_bsdtar_listing(result.stdout)


def clean_file(
    path: Path,
    *,
    source_id: str = SOURCE_ID,
    batch_id: str = DEFAULT_BATCH_ID,
    import_scope_key: str = IMPORT_SCOPE_KEY,
) -> tuple[list[DatasetRecord], dict[str, Any]]:
    if not path.is_file():
        raise ZybertPretrainError(f"missing archive: {path}")
    header = path.read_bytes()[:4]
    if header != RAR_MAGIC:
        raise ZybertPretrainError(f"{path.name} is not a RAR archive")
    members = list_rar_members(path)
    records: list[DatasetRecord] = []
    report = {
        "publish": False,
        "license_status": "unverified_dropbox_archive_not_inherited_from_tcm_sd",
        "consumed_files": [path.name],
        "file_sha256": {path.name: _sha256(path)},
        "archive_bytes": path.stat().st_size,
        "members": [{"name": item["name"], "size": item["size"]} for item in members],
        "mapped_relation_counts": {},
        "quarantine_counts": {
            "archive_members": len(members),
            "uncompressed_bytes": sum(item["size"] or 0 for item in members),
        },
        "quality_samples": {"members": [item["name"] for item in members]},
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
        raise ZybertPretrainError("ZY-BERT pretrain corpus must not emit graph records")
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
