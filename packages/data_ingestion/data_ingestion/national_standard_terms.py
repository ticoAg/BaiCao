"""清洗国标疾病、证候术语和成方制剂条目，按统一身份门禁入图。"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from knowledge_model.constants import NodeType

from data_ingestion.dataset_records import DatasetRecord, compute_stats
from data_ingestion.entity_identity import (
    EntityDraft,
    assign_display_names,
    contains_brand,
    merge_same_identity,
    redact_sensitive,
)
from data_ingestion.provenance import prompt_hash_for

SOURCE_ID = "national-standard-terms"
IMPORT_SCOPE_KEY = (
    "huggingface:ZJUFanLab/TCMChat-dataset-600k:pretrain/train/books/national_standard"
)
DEFAULT_BATCH_ID = "2026-08-19-national-standard-terms-v1"
PROCESSOR = "national_standard_terms"
PROMPT_HASH = prompt_hash_for(Path(__file__))

CODE_ONLY_RE = re.compile(r"^(\d+(?:\.\d+)+)$")
PINYIN_RE = re.compile(r"^[A-Za-z][A-Za-z0-9(),.\[\]-]*$")
COMPOSITION_RE = re.compile(r"^【药物组成】")


class NationalStandardTermsError(ValueError):
    pass


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


DEFAULT_INPUT_PATH = (
    repo_root()
    / ".cache/huggingface/ZJUFanLab/TCMChat-dataset-600k/pretrain/train/books/national_standard"
)


def _lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def parse_numbered_terms(path: Path) -> list[dict[str, Any]]:
    lines = _lines(path)
    terms: list[dict[str, Any]] = []
    index = 0
    while index < len(lines):
        current = lines[index].strip()
        if not CODE_ONLY_RE.fullmatch(current):
            index += 1
            continue
        code = current
        names: list[str] = []
        index += 1
        while index < len(lines):
            nxt = lines[index].strip()
            if not nxt:
                index += 1
                continue
            if CODE_ONLY_RE.fullmatch(nxt):
                break
            if names and (
                nxt.startswith("因")
                or nxt.startswith("泛指")
                or nxt.startswith("与")
                or nxt.startswith("指")
                or nxt.startswith("临床")
                or nxt.startswith("注")
            ):
                break
            names.append(nxt)
            index += 1
        definition_parts: list[str] = []
        while index < len(lines):
            nxt = lines[index].strip()
            if CODE_ONLY_RE.fullmatch(nxt):
                break
            if nxt:
                definition_parts.append(nxt)
            index += 1
        if names:
            terms.append(
                {
                    "code": code,
                    "primary": names[0],
                    "aliases": names[1:],
                    "definition": redact_sensitive("".join(definition_parts)),
                    "line": index,
                }
            )
    return terms


def _parent_code(code: str) -> str | None:
    if "." not in code:
        return None
    return code.rsplit(".", 1)[0]


def _term_drafts(
    terms: list[dict[str, Any]],
    *,
    role: str,
    file_name: str,
) -> list[EntityDraft]:
    by_code = {item["code"]: item["primary"] for item in terms}
    drafts: list[EntityDraft] = []
    for item in terms:
        parent_code = _parent_code(item["code"])
        parent_name = by_code.get(parent_code or "", "")
        drafts.append(
            EntityDraft(
                node_type=NodeType.DISEASE,
                raw_name=item["primary"],
                role=role,
                stable_id=item["code"],
                aliases=item["aliases"],
                parent_name=parent_name,
                evidence_refs=[f"{file_name}:{item['code']}"],
                properties={
                    "tcm_type": f"来源国标{role}",
                    "term_role": role,
                    "term_code": item["code"],
                    "parent_term": parent_name,
                    "aliases": item["aliases"],
                    "description": item["definition"],
                    "source_provider": "huggingface",
                    "dataset_name": "ZJUFanLab/TCMChat-dataset-600k",
                    "file_path": file_name,
                },
            )
        )
    return drafts


def parse_patent_formulas(path: Path) -> list[dict[str, Any]]:
    lines = _lines(path)
    try:
        start = next(index for index, line in enumerate(lines) if line.strip() == "各论")
    except StopIteration as exc:
        raise NationalStandardTermsError("成方制剂 missing 各论") from exc
    products: list[dict[str, Any]] = []
    for index in range(start, len(lines)):
        if not COMPOSITION_RE.match(lines[index].strip()):
            continue
        cursor = index - 1
        pinyin_parts: list[str] = []
        while cursor > start and PINYIN_RE.fullmatch(lines[cursor].strip()):
            pinyin_parts.append(lines[cursor].strip())
            cursor -= 1
        name = lines[cursor].strip() if cursor > start else ""
        if not name or name.startswith("【") or name.startswith("一、") or name.startswith("("):
            continue
        pinyin = "".join(reversed(pinyin_parts))
        composition = lines[index].strip().removeprefix("【药物组成】")
        indications = ""
        for look in range(index + 1, min(index + 12, len(lines))):
            if lines[look].strip().startswith("【功能与主治】"):
                indications = lines[look].strip().removeprefix("【功能与主治】")
                break
        products.append(
            {
                "name": name,
                "pinyin": pinyin,
                "composition": redact_sensitive(composition),
                "indications": redact_sensitive(indications),
                "line": index + 1,
            }
        )
    return products


def _formula_drafts(products: list[dict[str, Any]], *, file_name: str) -> list[EntityDraft]:
    drafts: list[EntityDraft] = []
    for item in products:
        drafts.append(
            EntityDraft(
                node_type=NodeType.FORMULA,
                raw_name=item["name"],
                role="中成药",
                stable_id=item["pinyin"] or item["name"],
                evidence_refs=[f"{file_name}:{item['line']}"],
                properties={
                    "tcm_type": "来源国标成方",
                    "term_role": "中成药",
                    "pinyin_name": item["pinyin"],
                    "composition_text": item["composition"],
                    "indications": item["indications"],
                    "source_provider": "huggingface",
                    "dataset_name": "ZJUFanLab/TCMChat-dataset-600k",
                    "file_path": file_name,
                },
            )
        )
    return drafts


def _to_record(
    draft: EntityDraft,
    *,
    source_id: str,
    batch_id: str,
    import_scope_key: str,
) -> DatasetRecord:
    unit_id = f"{draft.node_type.value}:{draft.display_name}"
    properties = {
        "import_source_id": source_id,
        "import_batch_id": batch_id,
        "import_unit_id": unit_id,
        **draft.properties,
    }
    record = DatasetRecord(
        source_id=source_id,
        batch_id=batch_id,
        unit_id=unit_id,
        unit_title=draft.display_name,
        processor=PROCESSOR,
        node_type=draft.node_type.value,
        node_name=draft.display_name,
        source=source_id,
        status="pending",
        evidence_refs=draft.evidence_refs,
        prompt_hash=PROMPT_HASH,
        import_scope_key=import_scope_key,
        properties=properties,
        edges=[],
    )
    record.validate_types()
    return record


def clean_directory(
    path: Path,
    *,
    source_id: str = SOURCE_ID,
    batch_id: str = DEFAULT_BATCH_ID,
    import_scope_key: str = IMPORT_SCOPE_KEY,
) -> tuple[list[DatasetRecord], dict[str, Any]]:
    if not path.is_dir():
        raise NationalStandardTermsError(f"input is not a directory: {path}")
    disease_path = path / "中医临床诊疗术语疾病.txt"
    syndrome_path = path / "中医临床诊疗术语证候.txt"
    formula_path = path / "中药成方制剂.txt"
    for required in (disease_path, syndrome_path, formula_path):
        if not required.is_file():
            raise NationalStandardTermsError(f"missing {required.name}")

    diseases = parse_numbered_terms(disease_path)
    syndromes = parse_numbered_terms(syndrome_path)
    formulas = parse_patent_formulas(formula_path)
    drafts = (
        _term_drafts(diseases, role="疾病", file_name=disease_path.name)
        + _term_drafts(syndromes, role="证候", file_name=syndrome_path.name)
        + _formula_drafts(formulas, file_name=formula_path.name)
    )
    merged, collapsed = merge_same_identity(drafts)
    resolved = assign_display_names(merged)
    brand_quarantine = [item for item in resolved if contains_brand(item.raw_name)]
    accepted = [item for item in resolved if item not in brand_quarantine]
    records = [
        _to_record(
            item,
            source_id=source_id,
            batch_id=batch_id,
            import_scope_key=import_scope_key,
        )
        for item in accepted
    ]
    records.sort(key=lambda record: (record.node_type, record.node_name))
    qualified = [item.display_name for item in accepted if item.display_name != item.raw_name]
    report = {
        "publish": False,
        "license_status": "apache-2.0_dataset_filter_brand_and_pii",
        "source_term_counts": {
            "疾病": len(diseases),
            "证候": len(syndromes),
            "成方": len(formulas),
        },
        "collapsed_same_identity": collapsed,
        "qualified_display_names": qualified,
        "brand_quarantine": [item.raw_name for item in brand_quarantine],
        "mapped_relation_counts": {},
        "quarantine_counts": {
            "brand_names": len(brand_quarantine),
            "unparsed_formula_gap": max(0, 2620 - len(formulas)),
            "unparsed_disease_gap": max(0, 1369 - len(diseases)),
        },
        "quality_samples": {
            "qualified_display_names": qualified[:20],
            "brand_quarantine": [item.raw_name for item in brand_quarantine],
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
