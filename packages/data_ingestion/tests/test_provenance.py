from pathlib import Path

from data_ingestion.dataset_records import DatasetEdge, DatasetRecord
from data_ingestion.provenance import (
    append_unique,
    fill_if_empty,
    lookup_names,
    prompt_hash_for,
    slim_record,
)


def test_prompt_hash_is_stable(tmp_path: Path):
    path = tmp_path / "prompt.md"
    path.write_text("v3 contract\n", encoding="utf-8")
    first = prompt_hash_for(path)
    second = prompt_hash_for(path)
    assert first == second
    assert first.startswith("sha256:")
    assert len(first) == 19


def test_lookup_names_acupoint_variants():
    assert lookup_names("穴位", "太溪") == ["太溪", "太溪穴"]
    assert lookup_names("穴位", "太溪穴") == ["太溪穴", "太溪"]
    assert lookup_names("药材", "人参") == ["人参"]


def test_slim_record_drops_run_metadata_and_keeps_graph_fields():
    record = DatasetRecord(
        source_id="daoyi-suyang",
        batch_id="2026-08-16-suyang-v3-b01",
        unit_id="chapter-002",
        unit_title="第2章",
        processor="composer-2.5-subagent",
        extracted_at="2026-08-16T18:00:00+00:00",
        node_type="方剂",
        node_name="止嗽散",
        source="daoyi-suyang",
        evidence_refs=["证据:daoyi-suyang:chapter-002"],
        evidence_text="桔梗4g",
        properties={
            "import_source_id": "daoyi-suyang",
            "import_batch_id": "2026-08-16-suyang-v3-b01",
            "composition_text": "桔梗4g",
            "aliases": ["止咳散", "Zhisousan"],
            "origin": ["华北"],
            "formula_name": "止嗽散",
            "tcm_type": "证候",
            "location": ["干燥根茎"],
            "quantity": ["3～10g"],
            "toxicity": ["有毒"],
            "snomed_id": "123456",
            "cpm_id": "CPM00001",
            "latin_name": "GINSENG",
            "pinyin_name": "renshen",
            "note": "drop me",
        },
        edges=[DatasetEdge(type="组成药材", target="桔梗", properties={"dosage": "4g", "dosage_ratio": "0.5", "junk": 1})],
    )
    slim = slim_record(record, prompt_hash="sha256:abc", import_scope_key="manual:baicao-knowledge:daoyi-suyang")
    assert slim.processor is None
    assert slim.unit_title is None
    assert slim.prompt_hash == "sha256:abc"
    assert slim.import_scope_key == "manual:baicao-knowledge:daoyi-suyang"
    assert slim.properties == {
        "composition_text": "桔梗4g",
        "aliases": ["止咳散"],
        "origin": ["华北"],
        "formula_name": "止嗽散",
        "tcm_type": "证候",
        "location": ["干燥根茎"],
        "quantity": ["3～10g"],
        "toxicity": ["有毒"],
        "snomed_id": "123456",
        "cpm_id": "CPM00001",
    }
    assert slim.edges[0].properties == {"dosage": "4g", "dosage_ratio": "0.5"}


def test_fill_if_empty_does_not_overwrite_pharmacopoeia():
    existing = {"name": "人参", "source": "huggingface", "description": "药典描述", "composition_text": None}
    incoming = {"description": "should-not-win", "composition_text": "人参 10g", "source": "daoyi-suyang"}
    assert fill_if_empty(existing, incoming) == {"composition_text": "人参 10g"}


def test_append_unique_keeps_order():
    assert append_unique(["daoyi-suyang"], "daoyi-suyang") == ["daoyi-suyang"]
    assert append_unique(["pharm"], "daoyi-suyang") == ["pharm", "daoyi-suyang"]
