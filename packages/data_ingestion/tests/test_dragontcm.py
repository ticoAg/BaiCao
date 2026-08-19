from __future__ import annotations

import json
from pathlib import Path

import pytest

pa = pytest.importorskip("pyarrow")
pq = pytest.importorskip("pyarrow.parquet")

from data_ingestion.dragontcm import clean_directory, write_clean_outputs  # noqa: E402


def _write(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pylist(rows), path)


def make_dataset(root: Path) -> None:
    _write(
        root / "herbs/train-00000-of-00001.parquet",
        [
            {
                "name": name,
                "synonyms": json.dumps(aliases),
                "category": "[]",
                "properties": "{}",
                "actions": "[]",
                "contraindications": "[]",
                "interactions": "[]",
                "incompatibility": "[]",
                "notes": "[]",
                "dosage": "[]",
                "indications": "[]",
            }
            for name, aliases in (("BAI ZHI", ["白芷"]), ("SAME", []))
        ],
    )
    _write(
        root / "formulas/train-00000-of-00001.parquet",
        [
            {
                "name": name,
                "synonyms": "[]",
                "actions": "[]",
                "syndromes": "[]",
                "treats": "[]",
                "contraindications": "[]",
                "notes": "[]",
                "composition": composition,
            }
            for name, composition in (("FORMULA A", '{"Bai Zhi":{}}'), ("SAME", "{}"))
        ],
    )
    _write(
        root / "conditions/train-00000-of-00001.parquet",
        [
            {
                "name": "MIGRAINE (DISORDER)",
                "synonyms": '["Migraine", "SNOMED:123456"]',
                "symptoms": json.dumps(
                    [
                        {
                            "name": "LIVER YANG RISING",
                            "clinical_manifestations": ["Headache", "P: Wiry", "...", ""],
                        }
                    ]
                ),
                "description": "test disease",
                "herb_formulas": "[]",
                "points": "[]",
            },
            {
                "name": "PAIN (FINDING)",
                "synonyms": "[]",
                "symptoms": "[]",
                "description": "",
                "herb_formulas": "[]",
                "points": "[]",
            },
        ],
    )
    _write(
        root / "relations/train-00000-of-00001.parquet",
        [
            {
                "source": "FORMULA A",
                "target": "Bai Zhi",
                "source_type": "formula",
                "target_type": "herb",
                "edge_type": "contains",
                "dosage": "10g",
            },
            {
                "source": "MIGRAINE (DISORDER)",
                "target": "FORMULA A",
                "source_type": "condition",
                "target_type": "formula",
                "edge_type": "treats",
                "dosage": "",
            },
            {
                "source": "MIGRAINE (DISORDER)",
                "target": "BAI ZHI",
                "source_type": "condition",
                "target_type": "herb",
                "edge_type": "treats",
                "dosage": "",
            },
            {
                "source": "PAIN (FINDING)",
                "target": "BAI ZHI",
                "source_type": "condition",
                "target_type": "herb",
                "edge_type": "treats",
                "dosage": "",
            },
        ],
    )


def by_key(records):
    return {(record.node_type, record.node_name): record for record in records}


def test_clean_directory_keeps_only_deterministic_entities_and_relations(
    tmp_path: Path,
):
    make_dataset(tmp_path)

    records, report = clean_directory(tmp_path)
    indexed = by_key(records)

    assert set(indexed) == {
        ("药材", "BAI ZHI"),
        ("药材", "SAME"),
        ("方剂", "FORMULA A"),
        ("方剂", "SAME"),
        ("病证", "MIGRAINE (DISORDER)"),
        ("症状", "Headache"),
        ("症状", "P: Wiry"),
    }
    assert {(edge.type, edge.target) for edge in indexed[("方剂", "FORMULA A")].edges} == {
        ("组成药材", "BAI ZHI")
    }
    assert {(edge.type, edge.target) for edge in indexed[("病证", "MIGRAINE (DISORDER)")].edges} == {
        ("关联药材", "BAI ZHI"),
        ("关联症状", "Headache"),
        ("关联症状", "P: Wiry"),
    }
    assert indexed[("病证", "MIGRAINE (DISORDER)")].properties["snomed_id"] == "123456"
    assert report["mapped_relation_counts"] == {
        "关联症状": 2,
        "关联药材": 1,
        "组成药材": 1,
    }
    assert report["identity_counts"] == {
        "cross_type_herb_formula_names": 1,
        "endpoint_casefold_matches": 1,
        "surface_rewritten_endpoints": 0,
        "chinese_alias_herb_rows": 1,
        "herb_surface_duplicate_groups": 0,
        "herb_surface_merged_groups": 0,
        "herb_surface_conflict_groups": 0,
        "formula_surface_duplicate_groups": 0,
        "formula_surface_merged_groups": 0,
        "formula_surface_conflict_groups": 0,
        "alias_based_merges": 0,
        "cross_language_merges": 0,
    }
    assert report["quarantine_counts"] == {
        "condition_formula_treats_relations": 1,
        "empty_manifestations": 1,
        "quarantined_relations": 1,
        "truncated_manifestations": 1,
        "unsupported_condition_rows": 1,
        "unsupported_condition_tag:finding": 1,
    }
    assert report["publish"] is False

    summary = write_clean_outputs(records, report, tmp_path / "out")
    assert summary["record_count"] == 7
    assert summary["edge_count"] == 4


def test_clean_directory_rejects_ambiguous_same_type_identity(tmp_path: Path):
    make_dataset(tmp_path)
    path = tmp_path / "herbs/train-00000-of-00001.parquet"
    rows = pq.read_table(path).to_pylist()
    rows.append({**rows[0], "name": "bai zhi"})
    _write(path, rows)

    with pytest.raises(ValueError, match="ambiguous identity key"):
        clean_directory(tmp_path)


def test_clean_directory_rejects_missing_required_column(tmp_path: Path):
    make_dataset(tmp_path)
    path = tmp_path / "relations/train-00000-of-00001.parquet"
    pq.write_table(pq.read_table(path).drop(["dosage"]), path)

    with pytest.raises(ValueError, match=r"relations.*dosage"):
        clean_directory(tmp_path)
