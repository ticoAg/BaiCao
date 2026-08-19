"""只读清洗 TCM-SD：保留 148 个证候术语，隔离病历原文与病例标签边。"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from knowledge_model.constants import NodeType
from knowledge_model.text_normalize import canonicalize_name

from data_ingestion.dataset_records import DatasetRecord, compute_stats
from data_ingestion.provenance import prompt_hash_for

SOURCE_ID = "tcm-sd"
IMPORT_SCOPE_KEY = "github:Borororo/ZY-BERT:TCM-SD"
DEFAULT_BATCH_ID = "2026-08-19-tcm-sd-v1"
PROCESSOR = "tcm_sd"
PROMPT_HASH = prompt_hash_for(Path(__file__))

LABELED_SPLITS = ("train", "dev", "test")
OPTIONAL_SPLITS = ("test_no_answer",)
REQUIRED_LABEL_KEYS = (
    "user_id",
    "lcd_id",
    "lcd_name",
    "syndrome",
    "chief_complaint",
    "description",
    "detection",
    "norm_syndrome",
)
UNLABELED_KEYS = (
    "user_id",
    "lcd_id",
    "lcd_name",
    "chief_complaint",
    "description",
    "detection",
)
FORBIDDEN_RECORD_KEYS = {
    "user_id",
    "chief_complaint",
    "description",
    "detection",
    "lcd_id",
    "lcd_name",
    "syndrome",
}
PHONE_RE = re.compile(r"(?<!\d)(?:1[3-9]\d{9}|0\d{2,3}-?\d{7,8})(?!\d)")
IDCARD_RE = re.compile(
    r"(?<!\d)[1-9]\d{5}(?:18|19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx](?!\d)"
)
ADMISSION_RE = re.compile(r"住院号[:：]?\s*\d+")
HOSPITAL_RE = re.compile(r"[\u4e00-\u9fff]{1,12}(?:医院|卫生院|中医院|人民医院|附属医院)")


class TcmSdError(ValueError):
    pass


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


DEFAULT_INPUT_PATH = repo_root() / "tmp/qibo-datasets/TCM-SD"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _clinical_text(row: dict[str, Any]) -> str:
    return "\n".join(
        str(row.get(field) or "")
        for field in ("chief_complaint", "description", "detection")
    )


def _scan_pii(text: str) -> dict[str, int]:
    return {
        "phone": int(bool(PHONE_RE.search(text))),
        "id_card": int(bool(IDCARD_RE.search(text))),
        "admission_no": int(bool(ADMISSION_RE.search(text))),
        "hospital": int(bool(HOSPITAL_RE.search(text))),
    }


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise TcmSdError(f"{path.name}:{line_no} is not valid JSON") from exc
        if not isinstance(payload, dict):
            raise TcmSdError(f"{path.name}:{line_no} is not a JSON object")
        payload["_line"] = line_no
        rows.append(payload)
    return rows


def load_vocab(path: Path) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        name = canonicalize_name(raw, NodeType.DISEASE.value)
        if not name:
            continue
        if name in seen:
            raise TcmSdError(f"duplicate vocab name after canonicalize: {name}")
        seen.add(name)
        names.append(name)
    if not names:
        raise TcmSdError("syndrome_vocab.txt is empty")
    return names


def _require_keys(row: dict[str, Any], keys: tuple[str, ...], *, locator: str) -> None:
    missing = [key for key in keys if key not in row]
    if missing:
        raise TcmSdError(f"{locator} missing keys: {missing}")


def _make_syndrome_record(
    name: str,
    *,
    line_no: int,
    source_id: str,
    batch_id: str,
    import_scope_key: str,
) -> DatasetRecord:
    unit_id = f"{NodeType.DISEASE.value}:{name}"
    record = DatasetRecord(
        source_id=source_id,
        batch_id=batch_id,
        unit_id=unit_id,
        unit_title=name,
        processor=PROCESSOR,
        node_type=NodeType.DISEASE.value,
        node_name=name,
        source=source_id,
        status="pending",
        evidence_refs=[f"TCM-SD/syndrome_vocab.txt:{line_no}"],
        prompt_hash=PROMPT_HASH,
        import_scope_key=import_scope_key,
        properties={
            "import_source_id": source_id,
            "import_batch_id": batch_id,
            "import_unit_id": unit_id,
            "tcm_type": "来源标注证候",
            "label_set": "syndrome_vocab",
        },
    )
    record.validate_types()
    leaked = FORBIDDEN_RECORD_KEYS & set(record.properties)
    if leaked or record.evidence_text or record.edges:
        raise TcmSdError(f"clinical payload leaked into {name}: {leaked}")
    return record


def clean_directory(
    path: Path,
    *,
    source_id: str = SOURCE_ID,
    batch_id: str = DEFAULT_BATCH_ID,
    import_scope_key: str = IMPORT_SCOPE_KEY,
) -> tuple[list[DatasetRecord], dict[str, Any]]:
    if not path.is_dir():
        raise TcmSdError(f"input is not a directory: {path}")

    vocab_path = path / "syndrome_vocab.txt"
    if not vocab_path.is_file():
        raise TcmSdError("missing syndrome_vocab.txt")
    vocab = load_vocab(vocab_path)
    vocab_index = {name: index for index, name in enumerate(vocab, 1)}

    split_rows: dict[str, list[dict[str, Any]]] = {}
    source_row_counts: dict[str, int] = {}
    file_hashes: dict[str, str] = {"syndrome_vocab.txt": _sha256(vocab_path)}
    for split in LABELED_SPLITS:
        split_path = path / f"{split}.json"
        if not split_path.is_file():
            raise TcmSdError(f"missing {split}.json")
        rows = load_jsonl(split_path)
        split_rows[split] = rows
        source_row_counts[split] = len(rows)
        file_hashes[f"{split}.json"] = _sha256(split_path)
        for row in rows:
            locator = f"{split}.json:{row['_line']}"
            _require_keys(row, REQUIRED_LABEL_KEYS, locator=locator)

    unlabeled_rows: list[dict[str, Any]] = []
    unlabeled_path = path / "test_no_answer.json"
    if unlabeled_path.is_file():
        unlabeled_rows = load_jsonl(unlabeled_path)
        source_row_counts["test_no_answer"] = len(unlabeled_rows)
        file_hashes["test_no_answer.json"] = _sha256(unlabeled_path)
        for row in unlabeled_rows:
            locator = f"test_no_answer.json:{row['_line']}"
            _require_keys(row, UNLABELED_KEYS, locator=locator)
            if row.get("syndrome") or row.get("norm_syndrome"):
                raise TcmSdError(f"{locator} unexpectedly contains syndrome labels")

    knowledge_names: list[str] = []
    knowledge_path = path / "syndrome_knowledge.json"
    if knowledge_path.is_file():
        knowledge_rows = load_jsonl(knowledge_path)
        source_row_counts["syndrome_knowledge"] = len(knowledge_rows)
        file_hashes["syndrome_knowledge.json"] = _sha256(knowledge_path)
        for row in knowledge_rows:
            name = canonicalize_name(str(row.get("Name") or ""), NodeType.DISEASE.value)
            if name:
                knowledge_names.append(name)

    pii_counts = Counter()
    empty_fields: dict[str, Counter[str]] = {split: Counter() for split in LABELED_SPLITS}
    syndrome_ne_norm = Counter()
    raw_syndrome_norms: dict[str, set[str]] = defaultdict(set)
    lcd_id_to_names: dict[str, set[str]] = defaultdict(set)
    name_to_ids: dict[str, set[str]] = defaultdict(set)
    pair_counts: Counter[tuple[str, str]] = Counter()
    user_splits: dict[str, set[str]] = defaultdict(set)
    text_splits: dict[str, set[str]] = defaultdict(set)
    exact_blobs: Counter[str] = Counter()
    label_not_in_vocab = 0
    labeled_total = 0

    for split, rows in split_rows.items():
        for row in rows:
            labeled_total += 1
            for key in REQUIRED_LABEL_KEYS:
                if row.get(key) in (None, ""):
                    empty_fields[split][key] += 1
            raw_syn = canonicalize_name(str(row.get("syndrome") or ""), NodeType.DISEASE.value)
            norm = canonicalize_name(
                str(row.get("norm_syndrome") or ""), NodeType.DISEASE.value
            )
            if not norm:
                raise TcmSdError(f"{split}.json:{row['_line']} has empty norm_syndrome")
            if norm not in vocab_index:
                label_not_in_vocab += 1
                raise TcmSdError(
                    f"{split}.json:{row['_line']} norm_syndrome not in vocab: {norm}"
                )
            if raw_syn != norm:
                syndrome_ne_norm[split] += 1
            if raw_syn:
                raw_syndrome_norms[raw_syn].add(norm)
            lcd_id = str(row.get("lcd_id") or "").strip()
            lcd_name = canonicalize_name(
                str(row.get("lcd_name") or ""), NodeType.DISEASE.value
            )
            if lcd_id and lcd_name:
                lcd_id_to_names[lcd_id].add(lcd_name)
                name_to_ids[lcd_name].add(lcd_id)
                pair_counts[(lcd_name, norm)] += 1
            user_id = str(row.get("user_id") or "")
            if user_id:
                user_splits[user_id].add(split)
            text = _clinical_text(row)
            text_splits[text].add(split)
            exact_blobs[
                json.dumps(
                    {key: row.get(key) for key in REQUIRED_LABEL_KEYS},
                    ensure_ascii=False,
                    sort_keys=True,
                )
            ] += 1
            for kind, hit in _scan_pii(text).items():
                if hit:
                    pii_counts[kind] += 1

    if label_not_in_vocab:
        raise TcmSdError("labels outside syndrome_vocab are not allowed")

    records = [
        _make_syndrome_record(
            name,
            line_no=line_no,
            source_id=source_id,
            batch_id=batch_id,
            import_scope_key=import_scope_key,
        )
        for name, line_no in vocab_index.items()
    ]
    records.sort(key=lambda record: record.node_name)

    disease_names = set(name_to_ids)
    syndrome_names = set(vocab)
    cross_type = sorted(disease_names & syndrome_names)
    ambiguous_raw = {
        raw: sorted(norms)
        for raw, norms in raw_syndrome_norms.items()
        if len(norms) > 1
    }
    report = {
        "publish": False,
        "license_status": "cc_by_nc_sa_4_0_dataset_mit_code_residual_phi",
        "consumed_files": [
            "syndrome_vocab.txt",
            *(f"{split}.json" for split in LABELED_SPLITS),
        ],
        "isolated_files": [
            name
            for name in ("syndrome_knowledge.json", "test_no_answer.json")
            if name in file_hashes
        ],
        "file_sha256": file_hashes,
        "source_row_counts": source_row_counts,
        "labeled_rows": labeled_total,
        "unique_syndrome_labels": len(vocab),
        "unique_lcd_names": len(name_to_ids),
        "unique_lcd_ids": len(lcd_id_to_names),
        "unique_disease_syndrome_pairs": len(pair_counts),
        "pairs_with_single_case": sum(1 for count in pair_counts.values() if count == 1),
        "lcd_id_multi_name": sum(1 for names in lcd_id_to_names.values() if len(names) > 1),
        "lcd_name_multi_id": sum(1 for ids in name_to_ids.values() if len(ids) > 1),
        "syndrome_ne_norm": dict(syndrome_ne_norm),
        "ambiguous_raw_syndromes": ambiguous_raw,
        "cross_type_same_names": cross_type,
        "empty_fields": {split: dict(counter) for split, counter in empty_fields.items()},
        "exact_duplicate_groups": sum(1 for count in exact_blobs.values() if count > 1),
        "exact_duplicate_extra_copies": sum(
            count - 1 for count in exact_blobs.values() if count > 1
        ),
        "user_id_cross_split": sum(1 for splits in user_splits.values() if len(splits) > 1),
        "fulltext_cross_split": sum(1 for splits in text_splits.values() if len(splits) > 1),
        "pii_record_counts": dict(sorted(pii_counts.items())),
        "knowledge_names": len(set(knowledge_names)),
        "knowledge_names_outside_vocab": len(set(knowledge_names) - syndrome_names),
        "mapped_relation_counts": {},
        "quarantine_counts": {
            "clinical_text_rows": labeled_total + len(unlabeled_rows),
            "case_label_pairs": len(pair_counts),
            "knowledge_entries": len(set(knowledge_names)),
            "disease_name_nodes": len(name_to_ids),
        },
        "quality_samples": {
            "lcd_id_multi_name": [
                {"lcd_id": lcd_id, "names": sorted(names)}
                for lcd_id, names in sorted(lcd_id_to_names.items())
                if len(names) > 1
            ],
            "cross_type_same_names": cross_type,
            "ambiguous_raw_syndromes": ambiguous_raw,
        },
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
    stats_path.write_text(
        json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return {
        "records": str(records_path),
        "stats": str(stats_path),
        "record_count": len(records),
        "edge_count": sum(len(record.edges) for record in records),
        "publish": False,
    }
