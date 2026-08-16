"""苏子阳抽取验收。失败则 exit 1，不得标 latest / 上传 HF。"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from data_ingestion.dataset_records import DatasetRecord

KNOWLEDGE_TYPES = {
    "医案",
    "方剂",
    "药材",
    "饮片",
    "穴位",
    "治法",
    "病证",
    "功效",
    "性味",
    "归经",
    "工艺",
}
FORMULA_SUFFIXES = ("散", "汤", "丸", "饮", "方")
VAGUE_DISEASES = {"内科杂病", "疑难杂症", "各种痛症", "杂病"}
FORBIDDEN_METHODS = {
    "铁布衫",
    "铁布衫训练",
    "金钟罩",
    "金钟罩训练",
    "八卦掌",
    "字门拳",
    "字门小手",
    "千金功",
    "子午乾坤功",
    "诚意正心修身",
    "说破不灵骗术",
    "认药",
    "五运六气",
    "望而知之",
    "手诊",
    "手相诊法",
    "大周天",
    "百日筑基",
    "炼气",
}
TREAT_SOURCES = {"医案", "方剂", "药材", "治法"}
EDGE_TARGET_TYPES = {
    "组成药材": {"药材", "饮片"},
    "使用方剂": {"方剂"},
    "取用穴位": {"穴位"},
    "采用治法": {"治法"},
    "治疗病证": {"病证"},
    "记载于医案": {"医案"},
    "由证据支持": {"证据"},
    "来源于": {"来源"},
    "经过工艺": {"工艺"},
    "具有功效": {"功效"},
    "具有性味": {"性味"},
    "归于经脉": {"归经"},
}
DOSAGE_RE = re.compile(r"\d+(?:\.\d+)?\s*(?:g|克|钱)")


def load_records(path: Path) -> tuple[list[DatasetRecord], list[str]]:
    records: list[DatasetRecord] = []
    errors: list[str] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
            if not isinstance(raw.get("edges"), list):
                raise ValueError("edges must be a list")
            record = DatasetRecord.model_validate(raw)
            record.validate_types()
            records.append(record)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{path.name}:{line_no}: {exc}")
    return records, errors


def validate(records: list[DatasetRecord], expected_units: set[str], batch_id: str | None) -> list[str]:
    failures: list[str] = []
    names = {record.node_name for record in records}
    units = {record.unit_id for record in records}
    name_types: dict[str, set[str]] = defaultdict(set)
    by_unit: dict[str, list[DatasetRecord]] = defaultdict(list)
    for record in records:
        name_types[record.node_name].add(record.node_type)
        by_unit[record.unit_id].append(record)

    if expected_units - units:
        failures.append(f"missing units: {sorted(expected_units - units)[:20]}")

    skip_units = {
        record.unit_id
        for record in records
        if (record.properties or {}).get("skip_reason") == "no_clinical_knowledge"
    }
    for unit_id in sorted(skip_units):
        extra = [
            f"{item.node_type}:{item.node_name}"
            for item in by_unit[unit_id]
            if item.node_type != "来源" or item.node_name != "道医苏子阳"
        ]
        if extra:
            failures.append(f"skip unit has knowledge: {unit_id} {extra[:6]}")

    formula_as_herb = [
        record.node_name
        for record in records
        if record.node_type == "药材" and str(record.node_name).endswith(FORMULA_SUFFIXES)
    ]
    if formula_as_herb:
        failures.append(f"formula typed as 药材: {sorted(set(formula_as_herb))[:12]}")

    book_as_evidence = [
        record.node_name
        for record in records
        if record.node_type == "证据" and str(record.node_name).startswith("《")
    ]
    if book_as_evidence:
        failures.append(f"book titled as 证据: {book_as_evidence[:8]}")

    bad_evidence_name = [
        record.node_name
        for record in records
        if record.node_type == "证据" and not str(record.node_name).startswith("证据:")
    ]
    if bad_evidence_name:
        failures.append(f"evidence name must start with 证据:: {bad_evidence_name[:8]}")

    dangling = Counter()
    for record in records:
        for edge in record.edges:
            if edge.target not in names:
                dangling[edge.target] += 1
    if dangling:
        failures.append(f"dangling targets: {dangling.most_common(8)}")

    isolated = 0
    for record in records:
        if record.node_type not in KNOWLEDGE_TYPES:
            continue
        if (record.properties or {}).get("skip_reason"):
            continue
        types = {edge.type for edge in record.edges}
        if "来源于" not in types or "由证据支持" not in types:
            isolated += 1
    if records and isolated / len(records) > 0.2:
        failures.append(f"knowledge nodes missing 来源于+由证据支持: {isolated}/{len(records)}")

    treat_from_disease = [
        record.node_name
        for record in records
        if record.node_type == "病证" and any(edge.type == "治疗病证" for edge in record.edges)
    ]
    if treat_from_disease:
        failures.append(f"病证 emitted 治疗病证: {treat_from_disease[:8]}")

    treat_from_wrong = [
        f"{record.node_type}:{record.node_name}"
        for record in records
        if any(edge.type == "治疗病证" for edge in record.edges) and record.node_type not in TREAT_SOURCES
    ]
    if treat_from_wrong:
        failures.append(f"治疗病证 from unsupported type: {treat_from_wrong[:8]}")

    vague = sorted({record.node_name for record in records if record.node_type == "病证" and record.node_name in VAGUE_DISEASES})
    if vague:
        failures.append(f"vague 病证: {vague}")

    forbidden_methods = sorted(
        {record.node_name for record in records if record.node_type == "治法" and record.node_name in FORBIDDEN_METHODS}
    )
    if forbidden_methods:
        failures.append(f"forbidden 治法: {forbidden_methods[:8]}")

    type_mismatch: list[str] = []
    for record in records:
        for edge in record.edges:
            allowed = EDGE_TARGET_TYPES.get(edge.type)
            if not allowed:
                continue
            actual = name_types.get(edge.target, set())
            if actual and not (actual & allowed):
                type_mismatch.append(f"{edge.type} target not {'/'.join(sorted(allowed))}: {edge.target}->{sorted(actual)}")
    if type_mismatch:
        failures.append(type_mismatch[0] if len(type_mismatch) == 1 else f"{type_mismatch[0]} (+{len(type_mismatch) - 1})")

    weak_cases = []
    no_intervention = []
    for record in records:
        if record.node_type != "医案":
            continue
        types = {edge.type for edge in record.edges}
        if "治疗病证" not in types:
            weak_cases.append(record.node_name)
        if not ({"使用方剂", "取用穴位", "采用治法"} & types):
            no_intervention.append(record.node_name)
    if weak_cases:
        failures.append(f"医案 missing 治疗病证: {weak_cases[:8]}")
    if no_intervention:
        failures.append(f"医案 missing intervention: {no_intervention[:8]}")

    incomplete_formulas = [
        record.node_name
        for record in records
        if record.node_type == "方剂"
        and DOSAGE_RE.search(record.evidence_text or "")
        and not any(edge.type == "组成药材" for edge in record.edges)
    ]
    if incomplete_formulas:
        failures.append(f"方剂 missing 组成药材 despite dosage text: {incomplete_formulas[:8]}")

    if batch_id:
        wrong = [record.unit_id for record in records if record.batch_id != batch_id]
        if wrong:
            failures.append(f"batch_id mismatch count={len(wrong)}")

    return failures


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--expected-units", nargs="*", default=[])
    parser.add_argument("--batch-id")
    args = parser.parse_args()
    records, parse_errors = load_records(args.records)
    failures = list(parse_errors)
    failures.extend(validate(records, set(args.expected_units), args.batch_id))
    print(
        json.dumps(
            {
                "records": len(records),
                "units": len({record.unit_id for record in records}),
                "ok": not failures,
                "failures": failures,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
