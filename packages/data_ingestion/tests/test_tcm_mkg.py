from __future__ import annotations

import csv
from pathlib import Path

import pytest

from data_ingestion.tcm_mkg import (
    REQUIRED_COLUMNS,
    SOURCE_FILES,
    clean_directory,
    write_clean_outputs,
)


def _write(root: Path, table: str, rows: list[list[str]]) -> None:
    path = root / SOURCE_FILES[table]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(REQUIRED_COLUMNS[table])
        writer.writerows(rows)


def _d1_row(
    tcmt_id: str,
    group: str,
    chinese: str,
    english: str,
    *,
    synonyms: str = "",
) -> list[str]:
    return [
        tcmt_id,
        group,
        f"English {group}",
        chinese,
        "pin yin",
        "",
        english,
        synonyms,
        f"Definition for {english}",
    ]


def _d18_row(code: str, chinese: str, english: str, chapter: str) -> list[str]:
    values = {column: "" for column in REQUIRED_COLUMNS["D18"]}
    values.update(
        {
            "ICD11_code": code,
            "English_term": english,
            "Chinese_term": chinese,
            "ClassKind": "category",
            "DepthInKind": "1",
            "IsResidual": "False",
            "ChapterNo": chapter,
            "BrowserLink": "browser",
            "isLeaf": "True",
            "Primary tabulation": "True",
        }
    )
    return [values[column] for column in REQUIRED_COLUMNS["D18"]]


def make_dataset(root: Path) -> None:
    d1 = [
        _d1_row("TCMT00001", "传统医学疾病", "霍乱", "Cholera", synonyms="Cholera synonym"),
        _d1_row("TCMT00002", "传统医学证候", "肝阳上亢证", "Liver yang rising"),
        _d1_row("TCMT00003", "治则", "扶正祛邪", "Reinforce healthy qi"),
        _d1_row("TCMT00004", "治法", "清热解毒", "Clear heat"),
        _d1_row("TCMT00005", "病因", "外感", "External contraction"),
        _d1_row("TCMT00006", "药性", "寒", "Cold therapeutic"),
        _d1_row("TCMT00007", "药性", "肺", "Lung meridian"),
    ]
    _write(root, "D1", d1)
    _write(root, "D2", [["CPM00001", "测试中成药", "ce shi", "Oral"]])
    d3 = []
    for tcmt_id, synonyms in (
        ("TCMT00001", ""),
        ("TCMT00001", "Different synonym"),
        ("TCMT00002", ""),
        ("TCMT00003", ""),
        ("TCMT00004", ""),
        ("TCMT00005", ""),
    ):
        row = next(item for item in d1 if item[0] == tcmt_id)
        d3.append(["CPM00001", tcmt_id, row[1], row[2], row[3], row[4], row[6], synonyms])
    _write(root, "D3", d3)
    _write(root, "D4", [["CPM00001", "CHP00001", "0.5"]])
    _write(
        root,
        "D5",
        [
            ["CPM00001", "1A00"],
            ["CPM00001", "MC1Y"],
            ["CPM00001", "NA00.Y"],
        ],
    )
    _write(
        root,
        "D6",
        [
            [
                "CHP00001",
                "黄芪",
                "膜荚黄芪",
                "",
                "huang qi",
                "root of Membranous Milkvetch",
                "Viridiplantae",
            ]
        ],
    )
    _write(
        root,
        "D7",
        [
            ["CHP00001", "Cold therapeutic", "Therapeutic nature", "1", "2"],
            ["CHP00001", "Lung meridian", "Meridian tropism", "3", "4"],
        ],
    )
    _write(
        root,
        "D18",
        [
            _d18_row("1A00", "霍乱", "Cholera", "1"),
            _d18_row("MC1Y", "视觉症状", "Visual symptom", "21"),
            _d18_row("NA00.Y", "头部浅表损伤", "Head injury", "22"),
        ],
    )


def _by_key(records):
    return {(record.node_type, record.node_name): record for record in records}


def test_clean_directory_maps_only_main_domain_facts(tmp_path: Path):
    make_dataset(tmp_path)

    records, report = clean_directory(tmp_path)
    indexed = _by_key(records)

    assert set(indexed) == {
        ("方剂", "测试中成药"),
        ("饮片", "黄芪"),
        ("病证", "霍乱"),
        ("病证", "肝阳上亢证"),
        ("治法", "扶正祛邪"),
        ("治法", "清热解毒"),
        ("性味", "寒"),
        ("归经", "肺"),
    }
    formula_edges = {
        (edge.type, edge.target): edge for edge in indexed[("方剂", "测试中成药")].edges
    }
    assert set(formula_edges) == {
        ("适用于", "霍乱"),
        ("关联证候", "肝阳上亢证"),
        ("采用治法", "扶正祛邪"),
        ("采用治法", "清热解毒"),
        ("组成药材", "黄芪"),
    }
    assert formula_edges[("组成药材", "黄芪")].properties["dosage_ratio"] == "0.5"
    assert "D3_CPM_TCMT.tsv" in formula_edges[("适用于", "霍乱")].properties["evidence_ref"]
    assert "D5_CPM_ICD11.tsv" in formula_edges[("适用于", "霍乱")].properties["evidence_ref"]
    herb_edges = {(edge.type, edge.target) for edge in indexed[("饮片", "黄芪")].edges}
    assert herb_edges == {("具有性味", "寒"), ("归于经脉", "肺")}
    assert "pinyin_name" not in indexed[("饮片", "黄芪")].properties
    assert indexed[("饮片", "黄芪")].properties["aliases"] == ["膜荚黄芪"]
    assert indexed[("病证", "霍乱")].properties["tcmt_id"] == "TCMT00001"
    assert indexed[("病证", "霍乱")].properties["icd11_code"] == "1A00"
    assert report["repair_counts"] == {
        "D6_shifted_column_record": 1,
        "D6_shifted_column_rows": 1,
    }
    assert report["quarantine_counts"] == {
        "excluded_D1_group:病因": 1,
        "excluded_D3_group:病因": 1,
        "excluded_D5_chapter:21": 1,
        "excluded_D5_chapter:22": 1,
    }
    assert report["duplicate_edge_counts"] == {
        "collapsed_D3_edges": 1,
        "collapsed_cross_table_treatment_edges": 1,
        "duplicate_D3_pairs": 1,
    }
    assert report["merged_tcmt_icd_exact_names"] == 1
    assert report["publish"] is False

    summary = write_clean_outputs(records, report, tmp_path / "out")
    assert summary["record_count"] == 8
    assert summary["edge_count"] == 7


def test_clean_directory_rejects_missing_column(tmp_path: Path):
    make_dataset(tmp_path)
    path = tmp_path / SOURCE_FILES["D4"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(("CPM_ID", "CHP_ID"))
        writer.writerow(("CPM00001", "CHP00001"))

    with pytest.raises(ValueError, match="D4 unexpected columns"):
        clean_directory(tmp_path)


def test_clean_directory_rejects_ambiguous_source_id(tmp_path: Path):
    make_dataset(tmp_path)
    path = tmp_path / SOURCE_FILES["D2"]
    with path.open("a", encoding="utf-8", newline="") as handle:
        csv.writer(handle, delimiter="\t").writerow(
            ["CPM00001", "另一个中成药", "ling yi ge", "Oral"]
        )

    with pytest.raises(ValueError, match="D2 duplicate CPM_ID"):
        clean_directory(tmp_path)
