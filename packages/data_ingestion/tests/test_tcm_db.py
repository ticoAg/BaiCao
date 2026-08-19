from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from data_ingestion.tcm_db import clean_file, open_readonly, write_clean_outputs


SCHEMA = """
CREATE TABLE herbs (
  id INTEGER PRIMARY KEY, name TEXT NOT NULL, alias TEXT, category TEXT,
  nature TEXT, flavor TEXT, toxicity TEXT, meridian_tropism TEXT, origin TEXT,
  indication TEXT, bencao_raw TEXT, commentary TEXT, raw_path TEXT, source_repo TEXT
);
CREATE TABLE formulas (
  id INTEGER PRIMARY KEY, name TEXT NOT NULL, alias TEXT, source_book TEXT,
  chapter TEXT, six_channel TEXT, syndrome TEXT, indication TEXT, composition TEXT,
  dosage TEXT, contraindication TEXT, differentiation TEXT, lesson_ref TEXT,
  is_high_risk INTEGER, commentary TEXT, raw_path TEXT, source_repo TEXT
);
CREATE TABLE symptoms (
  id INTEGER PRIMARY KEY, name TEXT NOT NULL, category TEXT, description TEXT,
  first_gateway TEXT, target_module TEXT, required_questions TEXT, differential TEXT
);
CREATE TABLE syndromes (
  id INTEGER PRIMARY KEY, name TEXT NOT NULL, six_channel TEXT, eight_principles TEXT,
  location TEXT, core_symptoms TEXT, key_differentiation TEXT,
  representative_formulas TEXT, contraindication TEXT, course_ref TEXT, description TEXT
);
CREATE TABLE treatment_methods (
  id INTEGER PRIMARY KEY, name TEXT NOT NULL, category TEXT, description TEXT,
  related_pathomechanism TEXT, related_herbs TEXT, related_acupoints TEXT,
  raw_path TEXT, source_repo TEXT
);
CREATE TABLE formula_herbs (
  formula_id INTEGER, herb_id INTEGER, role TEXT, dosage_in_formula TEXT, note TEXT
);
CREATE TABLE formula_syndromes (
  formula_id INTEGER, syndrome_id INTEGER, relevance TEXT
);
CREATE TABLE syndrome_symptoms (
  syndrome_id INTEGER, symptom_id INTEGER, is_key INTEGER
);
"""


def make_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    conn.executemany(
        "INSERT INTO herbs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (1, "黄芪", None, "上经", "温", "甘", None, None, None, "补气", None, None, None, None),
            (2, "白芷", None, "中经", "温", "辛", "无毒", None, None, None, None, None, None, None),
            (3, "白芷", None, "补充", "温", "甘,辛", "无毒", None, None, None, None, None, None, None),
        ],
    )
    conn.executemany(
        "INSERT INTO formulas VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (10, "补中益气汤", None, "脾胃论", None, None, None, "补中益气", "黄芪", None, None, None, None, 0, None, None, None),
            (11, "白虎汤和承气汤", None, None, None, None, None, None, None, None, None, None, None, 0, None, None, None),
        ],
    )
    conn.execute(
        "INSERT INTO symptoms VALUES (20, '乳癌', '疾病误入', NULL, NULL, NULL, NULL, NULL)"
    )
    conn.execute(
        "INSERT INTO syndromes VALUES (30, '乳癌', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)"
    )
    conn.execute(
        "INSERT INTO treatment_methods VALUES (40, '补气', '内治法', '补益正气', NULL, '黄芪', NULL, NULL, NULL)"
    )
    conn.execute("INSERT INTO formula_herbs VALUES (10, 1, '未知', NULL, NULL)")
    conn.execute("INSERT INTO formula_syndromes VALUES (10, 30, 'primary')")
    conn.execute("INSERT INTO syndrome_symptoms VALUES (30, 20, 0)")
    conn.commit()
    conn.close()


def by_key(records):
    return {(record.node_type, record.node_name): record for record in records}


def test_clean_file_maps_explicit_edges_and_quarantines_ambiguous_rows(tmp_path: Path):
    db_path = tmp_path / "tcm_knowledge.db"
    make_db(db_path)

    records, report = clean_file(db_path)
    indexed = by_key(records)

    assert set(indexed) == {
        ("药材", "黄芪"),
        ("方剂", "补中益气汤"),
        ("症状", "乳癌"),
        ("病证", "乳癌"),
        ("治法", "补气"),
    }
    assert {(edge.type, edge.target) for edge in indexed[("方剂", "补中益气汤")].edges} == {
        ("组成药材", "黄芪"),
        ("关联证候", "乳癌"),
    }
    assert {
        edge.properties["evidence_ref"]
        for edge in indexed[("方剂", "补中益气汤")].edges
    } == {
        "tcm_knowledge.db:formula_herbs:1",
        "tcm_knowledge.db:formula_syndromes:1",
    }
    assert indexed[("病证", "乳癌")].edges == []
    assert indexed[("方剂", "补中益气汤")].properties["composition_text"] == "黄芪"
    assert indexed[("症状", "乳癌")].evidence_refs == ["tcm_knowledge.db:symptoms:20"]
    assert report["quarantine_counts"] == {
        "conflicting_duplicate_groups": 1,
        "conflicting_duplicate_rows": 2,
        "cross_type_same_name_edges": 1,
        "formula_name_warning_events": 1,
        "formula_name_warning_rows": 1,
    }
    assert report["publish"] is False


def test_clean_file_rejects_missing_required_column(tmp_path: Path):
    db_path = tmp_path / "broken.db"
    make_db(db_path)
    conn = sqlite3.connect(db_path)
    conn.execute("ALTER TABLE symptoms DROP COLUMN differential")
    conn.commit()
    conn.close()

    with pytest.raises(ValueError, match=r"symptoms.*differential"):
        clean_file(db_path)


def test_open_readonly_enforces_query_only(tmp_path: Path):
    db_path = tmp_path / "readonly.db"
    make_db(db_path)
    conn = open_readonly(db_path)
    try:
        assert conn.execute("PRAGMA query_only").fetchone()[0] == 1
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            conn.execute("DELETE FROM herbs")
    finally:
        conn.close()


def test_write_clean_outputs_keeps_quality_report(tmp_path: Path):
    db_path = tmp_path / "source.db"
    out_dir = tmp_path / "out"
    make_db(db_path)
    records, report = clean_file(db_path)

    summary = write_clean_outputs(records, report, out_dir)

    assert summary["record_count"] == 5
    stats = json.loads((out_dir / "stats.json").read_text(encoding="utf-8"))
    assert stats["edge_type_counts"] == {"组成药材": 1, "关联证候": 1}
    assert stats["publish"] is False
