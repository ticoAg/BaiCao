"""只读审计 TCM-NER / DeepNER：不把说明书跨度提升为图事实。"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from knowledge_model.constants import NodeType

from data_ingestion.dataset_records import DatasetRecord, compute_stats
from data_ingestion.entity_identity import EntityDraft, contains_brand
from data_ingestion.organize_workflow import finalize_drafts
from data_ingestion.provenance import prompt_hash_for

SOURCE_ID = "tcm-ner"
IMPORT_SCOPE_KEY = "github:z814081807/DeepNER:data/raw_data"
DEFAULT_BATCH_ID = "2026-08-19-tcm-ner-v1"
PROCESSOR = "tcm_ner"
PROMPT_HASH = prompt_hash_for(Path(__file__))

LABELED_FILES = ("train.json", "dev.json")
UNLABELED_FILES = ("test.json",)
ISOLATED_DUPLICATE_FILES = ("stack.json",)
KNOWN_LABEL_TYPES = frozenset(
    {
        "DISEASE",
        "DISEASE_GROUP",
        "DRUG",
        "DRUG_DOSAGE",
        "DRUG_EFFICACY",
        "DRUG_GROUP",
        "DRUG_INGREDIENT",
        "DRUG_TASTE",
        "FOOD",
        "FOOD_GROUP",
        "PERSON_GROUP",
        "SYMPTOM",
        "SYNDROME",
    }
)
MANUFACTURER_MARKERS = ("有限公司", "制药厂", "药业股份")
LABEL_TO_NODE = {
    "DISEASE": NodeType.DISEASE,
    "DISEASE_GROUP": NodeType.DISEASE,
    "SYNDROME": NodeType.DISEASE,
    "SYMPTOM": NodeType.SYMPTOM,
    "DRUG": NodeType.HERB,
    "DRUG_INGREDIENT": NodeType.HERB,
    "DRUG_EFFICACY": NodeType.EFFICACY,
    "DRUG_TASTE": NodeType.FLAVOR,
}
SKIP_LABELS = {
    "DRUG_DOSAGE",
    "DRUG_GROUP",
    "FOOD",
    "FOOD_GROUP",
    "PERSON_GROUP",
}


class TcmNerError(ValueError):
    pass


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


DEFAULT_INPUT_PATH = repo_root() / ".cache/github/z814081807/DeepNER/data/raw_data"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_docs(path: Path) -> list[dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TcmNerError(f"{path.name} is not valid JSON") from exc
    if not isinstance(payload, list):
        raise TcmNerError(f"{path.name} is not a JSON array")
    docs: list[dict[str, Any]] = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise TcmNerError(f"{path.name}[{index}] is not a JSON object")
        docs.append(item)
    return docs


def _require_keys(doc: dict[str, Any], keys: tuple[str, ...], *, locator: str) -> None:
    missing = [key for key in keys if key not in doc]
    if missing:
        raise TcmNerError(f"{locator} missing keys: {missing}")


def _validate_labels(doc: dict[str, Any], *, locator: str) -> list[tuple[str, str]]:
    labels = doc.get("labels")
    if not isinstance(labels, list):
        raise TcmNerError(f"{locator} labels must be a list")
    text = str(doc.get("text") or "")
    surfaces: list[tuple[str, str]] = []
    for index, label in enumerate(labels):
        if not isinstance(label, list) or len(label) != 5:
            raise TcmNerError(f"{locator} labels[{index}] must be a 5-tuple")
        _entity_id, typ, start, end, surface = label
        if typ not in KNOWN_LABEL_TYPES:
            raise TcmNerError(f"{locator} labels[{index}] unknown type: {typ}")
        try:
            start_i = int(start)
            end_i = int(end)
        except (TypeError, ValueError) as exc:
            raise TcmNerError(f"{locator} labels[{index}] has non-integer span") from exc
        if start_i < 0 or end_i > len(text) or start_i >= end_i:
            raise TcmNerError(f"{locator} labels[{index}] span out of range")
        actual = text[start_i:end_i]
        if actual != str(surface):
            raise TcmNerError(f"{locator} labels[{index}] surface does not match span")
        surfaces.append((str(typ), str(surface).strip()))
    return surfaces


def clean_directory(
    path: Path,
    *,
    source_id: str = SOURCE_ID,
    batch_id: str = DEFAULT_BATCH_ID,
    import_scope_key: str = IMPORT_SCOPE_KEY,
) -> tuple[list[DatasetRecord], dict[str, Any]]:
    if not path.is_dir():
        raise TcmNerError(f"input is not a directory: {path}")

    docs_by_file: dict[str, list[dict[str, Any]]] = {}
    file_hashes: dict[str, str] = {}
    source_doc_counts: dict[str, int] = {}
    for name in (*LABELED_FILES, *UNLABELED_FILES, *ISOLATED_DUPLICATE_FILES):
        file_path = path / name
        if not file_path.is_file():
            if name in LABELED_FILES:
                raise TcmNerError(f"missing {name}")
            continue
        docs = load_docs(file_path)
        docs_by_file[name] = docs
        file_hashes[name] = _sha256(file_path)
        source_doc_counts[name] = len(docs)

    span_counts: Counter[str] = Counter()
    unique_surfaces: dict[str, set[str]] = defaultdict(set)
    type_by_surface: dict[str, set[str]] = defaultdict(set)
    ids_by_file: dict[str, set[int]] = {}
    manufacturer_docs = 0
    labeled_docs = 0
    labeled_spans = 0

    for name in LABELED_FILES:
        for index, doc in enumerate(docs_by_file[name]):
            locator = f"{name}[{index}]"
            _require_keys(doc, ("id", "text", "labels"), locator=locator)
            surfaces = _validate_labels(doc, locator=locator)
            labeled_docs += 1
            labeled_spans += len(surfaces)
            ids_by_file.setdefault(name, set()).add(int(doc["id"]))
            text = str(doc.get("text") or "")
            if any(marker in text for marker in MANUFACTURER_MARKERS):
                manufacturer_docs += 1
            for typ, surface in surfaces:
                if surface:
                    span_counts[typ] += 1
                    unique_surfaces[typ].add(surface)
                    type_by_surface[surface].add(typ)

    unlabeled_docs = 0
    for name in UNLABELED_FILES:
        if name not in docs_by_file:
            continue
        for index, doc in enumerate(docs_by_file[name]):
            locator = f"{name}[{index}]"
            _require_keys(doc, ("id", "text"), locator=locator)
            if doc.get("labels"):
                raise TcmNerError(f"{locator} unexpectedly contains labels")
            unlabeled_docs += 1
            ids_by_file.setdefault(name, set()).add(int(doc["id"]))

    stack_ids = {int(doc["id"]) for doc in docs_by_file.get("stack.json", [])}
    labeled_ids = set().union(*(ids_by_file.get(name, set()) for name in LABELED_FILES))
    stack_is_union = bool(stack_ids) and stack_ids == labeled_ids
    if "stack.json" in docs_by_file and not stack_is_union:
        raise TcmNerError("stack.json is not the exact union of train.json and dev.json")

    cross_type = {
        surface: sorted(types)
        for surface, types in type_by_surface.items()
        if len(types) > 1
    }
    drafts: list[EntityDraft] = []
    skipped_cross = 0
    skipped_noise = 0
    mapped_surfaces: dict[str, NodeType] = {}
    for surface, types in type_by_surface.items():
        name = surface.strip()
        if len(name) < 2 or contains_brand(name) or any(marker in name for marker in MANUFACTURER_MARKERS):
            skipped_noise += 1
            continue
        mapped = {LABEL_TO_NODE[typ] for typ in types if typ in LABEL_TO_NODE}
        if not mapped:
            skipped_noise += 1
            continue
        if len(mapped) > 1:
            skipped_cross += 1
            continue
        mapped_surfaces[name] = next(iter(mapped))
    for name, node_type in mapped_surfaces.items():
        drafts.append(
            EntityDraft(
                node_type=node_type,
                raw_name=name,
                role="说明书跨度",
                stable_id=name,
                evidence_refs=["DeepNER:span"],
                properties={"tcm_type": "来源说明书跨度"},
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
        "license_status": "unverified_competition_mirror_unlicensed_repo",
        "consumed_files": [name for name in LABELED_FILES if name in docs_by_file],
        "isolated_files": [
            name
            for name in (*UNLABELED_FILES, *ISOLATED_DUPLICATE_FILES)
            if name in docs_by_file
        ],
        "file_sha256": file_hashes,
        "source_doc_counts": source_doc_counts,
        "labeled_docs": labeled_docs,
        "labeled_spans": labeled_spans,
        "unlabeled_test_docs": unlabeled_docs,
        "stack_is_train_dev_union": stack_is_union,
        "unique_surfaces": {typ: len(values) for typ, values in sorted(unique_surfaces.items())},
        "span_counts": dict(sorted(span_counts.items())),
        "cross_type_surface_count": len(cross_type),
        "manufacturer_docs": manufacturer_docs,
        "mapped_relation_counts": {},
        "quarantine_counts": {
            "labeled_docs": labeled_docs,
            "labeled_spans": labeled_spans,
            "unlabeled_test_docs": unlabeled_docs,
            "stack_docs": source_doc_counts.get("stack.json", 0),
            "entity_nodes": sum(len(values) for values in unique_surfaces.values()),
            "cross_type_surfaces": len(cross_type),
        },
        "quality_samples": {
            "cross_type_surfaces": [
                {"surface": surface, "types": types}
                for surface, types in sorted(cross_type.items(), key=lambda item: (-len(item[1]), item[0]))[:20]
            ]
        },
        "source_id": source_id,
        "batch_id": batch_id,
        "import_scope_key": import_scope_key,
        "processor": PROCESSOR,
        "prompt_hash": PROMPT_HASH,
        "skipped_cross_type": skipped_cross,
        "skipped_noise": skipped_noise,
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
