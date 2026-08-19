"""只读审计 SylvanL 预训练书/百科 JSON：不把自由文本提升为图事实。"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from data_ingestion.dataset_records import DatasetRecord, compute_stats
from data_ingestion.provenance import prompt_hash_for

SOURCE_ID = "sylvanl-tcm-pretrain"
IMPORT_SCOPE_KEY = (
    "huggingface:SylvanL/Traditional-Chinese-Medicine-Dataset-Pretrain"
)
DEFAULT_BATCH_ID = "2026-08-19-sylvanl-tcm-pretrain-v1"
PROCESSOR = "sylvanl_tcm_pretrain"
PROMPT_HASH = prompt_hash_for(Path(__file__))
HELD_FILES = (
    "CPT_tcmBooks_source1_146244.json",
    "CPT_tcmKnowledge_source1_17921.json",
    "CPT_tcmKnowledge_source2_12889.json",
)
UNHELD_MEDICAL_RECORDS = (
    "CPT_medicalRecord_source1_61486.json",
    "CPT_medicalRecord_source2_15307.json",
    "CPT_medicalRecord_source3_230000.json",
    "CPT_medicalRecord_source4_48665.json",
)
MIXUP_MARKERS = ("亚锡葡庚糖酸钠Ⅰ", "氨苄西林")


class SylvanLPretrainError(ValueError):
    pass


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


DEFAULT_INPUT_PATH = (
    repo_root()
    / ".cache/huggingface/SylvanL/Traditional-Chinese-Medicine-Dataset-Pretrain"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_array(path: Path) -> list[dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SylvanLPretrainError(f"{path.name} is not valid JSON") from exc
    if not isinstance(payload, list):
        raise SylvanLPretrainError(f"{path.name} is not a JSON array")
    return payload


def _prefix(text: str) -> str:
    head = text.split("\n", 1)[0]
    return head.split(":", 1)[0][:12] if ":" in head else "plain_text"


def clean_directory(
    path: Path,
    *,
    source_id: str = SOURCE_ID,
    batch_id: str = DEFAULT_BATCH_ID,
    import_scope_key: str = IMPORT_SCOPE_KEY,
) -> tuple[list[DatasetRecord], dict[str, Any]]:
    if not path.is_dir():
        raise SylvanLPretrainError(f"input is not a directory: {path}")

    file_hashes: dict[str, str] = {}
    source_counts: dict[str, int] = {}
    prefix_counts: dict[str, Counter[str]] = {}
    empty_text = 0
    mixup: list[dict[str, Any]] = []

    for name in HELD_FILES:
        file_path = path / name
        if not file_path.is_file():
            raise SylvanLPretrainError(f"missing {name}")
        rows = _load_array(file_path)
        file_hashes[name] = _sha256(file_path)
        source_counts[name] = len(rows)
        prefixes: Counter[str] = Counter()
        for index, row in enumerate(rows):
            if not isinstance(row, dict) or "text" not in row:
                raise SylvanLPretrainError(f"{name}[{index}] missing text")
            text = str(row.get("text") or "")
            if not text.strip():
                empty_text += 1
                continue
            prefixes[_prefix(text)] += 1
            if name.endswith("source2_12889.json") and all(marker in text for marker in MIXUP_MARKERS):
                mixup.append({"file": name, "index": index})
        prefix_counts[name] = prefixes

    if empty_text:
        raise SylvanLPretrainError(f"empty text rows: {empty_text}")

    records: list[DatasetRecord] = []
    report = {
        "publish": False,
        "license_status": "apache-2.0_card_mixed_unstructured_content",
        "consumed_files": list(HELD_FILES),
        "isolated_files": [name for name in UNHELD_MEDICAL_RECORDS],
        "file_sha256": file_hashes,
        "source_row_counts": source_counts,
        "prefix_counts": {
            name: dict(counter.most_common(12)) for name, counter in prefix_counts.items()
        },
        "mixed_pharmacology_rows": mixup,
        "mapped_relation_counts": {},
        "quarantine_counts": {
            "text_rows": sum(source_counts.values()),
            "unheld_medical_record_files": len(UNHELD_MEDICAL_RECORDS),
            "mixed_pharmacology_rows": len(mixup),
        },
        "quality_samples": {"mixed_pharmacology_rows": mixup[:5]},
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
        raise SylvanLPretrainError("SylvanL pretrain must not emit graph records")
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
