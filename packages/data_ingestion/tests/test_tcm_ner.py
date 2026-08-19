from __future__ import annotations

import json
from pathlib import Path

import pytest

from data_ingestion.tcm_ner import TcmNerError, clean_directory, write_clean_outputs


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def labeled_doc(
    doc_id: int,
    text: str,
    labels: list[list[object]],
) -> dict[str, object]:
    return {
        "id": doc_id,
        "text": text,
        "labels": labels,
        "pseudo": False,
        "candidate_entities": ["候选"],
    }


def make_dataset(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    train = [
        labeled_doc(
            1,
            "补气养血，用于气血两亏。北京同仁堂股份有限公司。",
            [
                ["T1", "DRUG_EFFICACY", 0, 4, "补气养血"],
                ["T2", "SYNDROME", 7, 11, "气血两亏"],
            ],
        ),
        labeled_doc(
            2,
            "糖尿病患者慎用。",
            [
                ["T1", "DISEASE", 0, 3, "糖尿病"],
                ["T2", "PERSON_GROUP", 0, 5, "糖尿病患者"],
            ],
        ),
    ]
    dev = [
        labeled_doc(
            3,
            "糖尿病忌辛辣。",
            [["T1", "DISEASE", 0, 3, "糖尿病"]],
        )
    ]
    write_json(root / "train.json", train)
    write_json(root / "dev.json", dev)
    write_json(root / "stack.json", train + dev)
    write_json(
        root / "test.json",
        [{"id": 1000, "text": "未标注说明书。", "candidate_entities": []}],
    )


def test_clean_directory_emits_no_records_and_isolates_spans(tmp_path: Path):
    root = tmp_path / "DeepNER-raw"
    make_dataset(root)
    records, report = clean_directory(root)
    assert records == []
    assert report["publish"] is False
    assert report["labeled_docs"] == 3
    assert report["labeled_spans"] == 5
    assert report["unlabeled_test_docs"] == 1
    assert report["stack_is_train_dev_union"] is True
    assert report["unique_surfaces"]["DISEASE"] == 1
    assert report["cross_type_surface_count"] == 0
    assert report["manufacturer_docs"] == 1
    assert "stack.json" in report["isolated_files"]
    assert report["quarantine_counts"]["entity_nodes"] == 4


def test_stack_must_be_exact_union(tmp_path: Path):
    root = tmp_path / "DeepNER-raw"
    make_dataset(root)
    write_json(root / "stack.json", [labeled_doc(9, "其他。", [])])
    with pytest.raises(TcmNerError, match="exact union"):
        clean_directory(root)


def test_span_mismatch_fails(tmp_path: Path):
    root = tmp_path / "DeepNER-raw"
    make_dataset(root)
    write_json(
        root / "train.json",
        [labeled_doc(1, "补气养血。", [["T1", "DRUG_EFFICACY", 0, 2, "养血"]])],
    )
    with pytest.raises(TcmNerError, match="surface does not match"):
        clean_directory(root)


def test_unknown_type_fails(tmp_path: Path):
    root = tmp_path / "DeepNER-raw"
    make_dataset(root)
    write_json(
        root / "dev.json",
        [labeled_doc(3, "测试文本。", [["T1", "UNKNOWN", 0, 2, "测试"]])],
    )
    with pytest.raises(TcmNerError, match="unknown type"):
        clean_directory(root)


def test_test_split_cannot_carry_labels(tmp_path: Path):
    root = tmp_path / "DeepNER-raw"
    make_dataset(root)
    write_json(
        root / "test.json",
        [labeled_doc(1000, "补气养血。", [["T1", "DRUG_EFFICACY", 0, 4, "补气养血"]])],
    )
    with pytest.raises(TcmNerError, match="unexpectedly contains labels"):
        clean_directory(root)


def test_write_outputs_rejects_records_and_keeps_publish_false(tmp_path: Path):
    root = tmp_path / "DeepNER-raw"
    make_dataset(root)
    records, report = clean_directory(root)
    result = write_clean_outputs(records, report, tmp_path / "out")
    stats = json.loads((tmp_path / "out" / "stats.json").read_text(encoding="utf-8"))
    dumped = (tmp_path / "out" / "records.jsonl").read_text(encoding="utf-8")
    assert result["record_count"] == 0
    assert result["publish"] is False
    assert dumped == ""
    assert stats["record_count"] == 0
    assert "补气养血" not in dumped
    assert "北京同仁堂" not in dumped
