from __future__ import annotations

import json
from pathlib import Path

import pytest

from data_ingestion.shennong_tcm_kg import (
    clean_triples,
    parse_lines,
    write_clean_outputs,
)


def triples(*rows: tuple[str, str, str]):
    return parse_lines(["\t".join(row) for row in rows])


def by_key(records):
    return {(record.node_type, record.node_name): record for record in records}


def edge_keys(record):
    return {(edge.type, edge.target) for edge in record.edges}


def test_parse_lines_requires_head_tail_relation_columns():
    parsed = triples(("腹痛", "心经积热证", "证候"))
    assert (parsed[0].head, parsed[0].tail, parsed[0].relation) == (
        "腹痛",
        "心经积热证",
        "证候",
    )

    with pytest.raises(ValueError, match="line 1"):
        parse_lines(["腹痛\t证候"])
    with pytest.raises(ValueError, match="empty field"):
        parse_lines(["腹痛\t\t证候"])
    with pytest.raises(ValueError, match="unknown relation"):
        parse_lines(["腹痛\t心经积热证\t近义"])


def test_clean_triples_maps_edges_attributes_and_quarantines_external_mappings():
    records, report = clean_triples(
        triples(
            ("腹痛", "心经积热证", "证候"),
            ("心经积热证", "仙茅", "中药"),
            ("心经积热证", "温阳散寒", "治法"),
            ("仙茅", "祛寒除湿", "功能"),
            ("仙茅", "腹痛", "功能"),
            ("仙茅", "肝经、肾经", "归经"),
            ("仙茅", "辛", "药味"),
            ("仙茅", "热", "药性"),
            ("仙茅", "干燥根茎", "部位"),
            ("仙茅", "置干燥处", "贮藏"),
            ("仙茅", "3～10g", "用量"),
            ("仙茅", "有毒", "毒性"),
            ("仙茅", "阴虚火旺者忌服", "注意"),
            ("仙茅", "水煎服", "用法"),
            ("腹痛", "Abdominal Pain", "TS_MS"),
            ("仙茅", "SMIT00001", "symmap_chemical"),
            ("SMIT00001", "Abdominal Pain", "chemical_MM"),
        )
    )
    indexed = by_key(records)

    clinical = indexed[("病证", "腹痛")]
    syndrome = indexed[("病证", "心经积热证")]
    method = indexed[("治法", "温阳散寒")]
    herb = indexed[("药材", "仙茅")]

    assert edge_keys(clinical) == {("关联证候", "心经积热证")}
    assert syndrome.properties["tcm_type"] == "来源标注证候"
    assert edge_keys(syndrome) == {
        ("关联药材", "仙茅"),
        ("关联治法", "温阳散寒"),
    }
    assert edge_keys(method) == set()
    assert edge_keys(herb) == {
        ("具有功效", "祛寒除湿"),
        ("具有性味", "辛"),
        ("具有性味", "热"),
        ("归于经脉", "肝经"),
        ("归于经脉", "肾经"),
    }
    assert herb.properties == {
        "import_source_id": "shennong-tcm-kg",
        "import_batch_id": "2026-08-19-shennong-tcm-kg-v1",
        "import_unit_id": "药材:仙茅",
        "location": ["干燥根茎"],
        "storage_text": ["置干燥处"],
        "quantity": ["3～10g"],
        "toxicity": ["有毒"],
        "caution_text": ["阴虚火旺者忌服"],
        "usage_text": ["水煎服"],
    }
    assert "alias" not in clinical.properties
    assert report["decision_counts"] == {
        "mapped_edge": 7,
        "mapped_property": 6,
        "quarantined_external_mapping": 1,
        "quarantined_function_clinical_overlap": 1,
        "excluded_chemical": 2,
    }


def test_known_syndrome_wins_over_untyped_head_and_cross_type_names_stay_separate():
    records, report = clean_triples(
        triples(
            ("麻黄", "风寒束表证", "证候"),
            ("风寒束表证", "麻黄", "中药"),
            ("其他病证", "麻黄", "中药"),
        )
    )
    indexed = by_key(records)

    assert indexed[("病证", "风寒束表证")].properties["tcm_type"] == "来源标注证候"
    assert ("病证", "麻黄") in indexed
    assert ("药材", "麻黄") in indexed
    assert report["role_counts"]["cross_type_same_name"] == 1


def test_duplicate_and_self_relation_are_counted_without_duplicate_edges():
    records, report = clean_triples(
        triples(
            ("腹痛", "心经积热证", "证候"),
            ("腹痛", "心经积热证", "证候"),
            ("心经积热证", "心经积热证", "证候"),
        )
    )
    clinical = by_key(records)[("病证", "腹痛")]

    assert edge_keys(clinical) == {("关联证候", "心经积热证")}
    assert report["duplicate_rows"] == 1
    assert report["self_edges_skipped"] == 1


def test_write_clean_outputs_keeps_quality_report(tmp_path: Path):
    records, report = clean_triples(triples(("腹痛", "心经积热证", "证候")))
    summary = write_clean_outputs(records, report, tmp_path)

    assert summary["record_count"] == 2
    assert (tmp_path / "records.jsonl").is_file()
    stats = json.loads((tmp_path / "stats.json").read_text(encoding="utf-8"))
    assert stats["source_relation_counts"] == {"证候": 1}
    assert stats["decision_counts"]["mapped_edge"] == 1
