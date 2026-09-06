from __future__ import annotations

import json
from pathlib import Path

import pytest

from data_ingestion.tcm_sd import TcmSdError, clean_directory, write_clean_outputs


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def labeled_row(
    *,
    user_id: str,
    lcd_id: str,
    lcd_name: str,
    syndrome: str,
    norm: str,
    text: str,
) -> dict[str, str]:
    return {
        "user_id": user_id,
        "lcd_id": lcd_id,
        "lcd_name": lcd_name,
        "syndrome": syndrome,
        "chief_complaint": text,
        "description": text,
        "detection": "舌淡苔白，脉细。",
        "norm_syndrome": norm,
    }


def make_dataset(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "syndrome_vocab.txt").write_text("气虚血瘀证\n湿热下注证\n风寒湿痹证\n", encoding="utf-8")
    write_jsonl(
        root / "train.json",
        [
            labeled_row(
                user_id="u1",
                lcd_id="BNF001",
                lcd_name="中风病",
                syndrome="气虚血瘀证",
                norm="气虚血瘀证",
                text="患者头晕。",
            ),
            labeled_row(
                user_id="u2",
                lcd_id="BNP020",
                lcd_name="胃痛",
                syndrome="脾虚证",
                norm="湿热下注证",
                text="住院号123456，就诊于市中医院。",
            ),
            labeled_row(
                user_id="u3",
                lcd_id="A01.01",
                lcd_name="风寒湿痹证",
                syndrome="风寒湿痹证",
                norm="风寒湿痹证",
                text="关节冷痛。",
            ),
        ],
    )
    write_jsonl(
        root / "dev.json",
        [
            labeled_row(
                user_id="u1",
                lcd_id="BNF001",
                lcd_name="中风病",
                syndrome="气虚血瘀证",
                norm="气虚血瘀证",
                text="患者头晕。",
            )
        ],
    )
    write_jsonl(
        root / "test.json",
        [
            labeled_row(
                user_id="u4",
                lcd_id="BNP20",
                lcd_name="胃痞病",
                syndrome="湿热下注证",
                norm="湿热下注证",
                text="胃脘痞满。",
            )
        ],
    )
    write_jsonl(
        root / "test_no_answer.json",
        [
            {
                "user_id": "u4",
                "lcd_id": "BNP20",
                "lcd_name": "胃痞病",
                "chief_complaint": "胃脘痞满。",
                "description": "胃脘痞满。",
                "detection": "舌淡苔白，脉细。",
            }
        ],
    )
    write_jsonl(
        root / "syndrome_knowledge.json",
        [
            {
                "Name": "气虚血瘀证",
                "Definition": "证候定义",
                "Typical_performance": "",
                "Common_isease": "方用补阳还五汤。",
                "id": 0,
            },
            {
                "Name": "心气虚证",
                "Definition": "不在 148 词表",
                "Typical_performance": "",
                "Common_isease": "",
                "id": 1,
            },
        ],
    )


def test_clean_directory_emits_vocab_only_and_isolates_cases(tmp_path: Path):
    root = tmp_path / "TCM-SD"
    make_dataset(root)

    records, report = clean_directory(root)
    syndromes = [
        record
        for record in records
        if record.properties.get("tcm_type") == "来源标注证候"
    ]
    names = [record.node_name for record in syndromes]

    assert names == ["气虚血瘀证", "湿热下注证", "风寒湿痹证"]
    assert all(record.node_type == "病证" for record in syndromes)
    assert all(record.edges == [] for record in syndromes)
    assert all(record.evidence_text is None for record in records)
    assert any(record.node_type == "医案" for record in records)
    assert all(record.status == "pending" for record in records)
    assert report["publish"] is False
    assert report["unique_lcd_names"] == 4
    assert report["unique_disease_syndrome_pairs"] == 4
    assert report["cross_type_same_names"] == ["风寒湿痹证"]
    assert report["syndrome_ne_norm"] == {"train": 1}
    assert report["user_id_cross_split"] == 1
    assert report["fulltext_cross_split"] == 1
    assert report["pii_record_counts"]["admission_no"] == 1
    assert report["pii_record_counts"]["hospital"] == 1
    assert report["knowledge_names_outside_vocab"] == 1
    assert report["quarantine_counts"]["disease_name_nodes"] == 4
    assert report["quarantine_counts"]["case_label_pairs"] == 4
    dumped = [record.model_dump() for record in records]
    dumped_text = json.dumps(dumped, ensure_ascii=False)
    assert "住院号" not in dumped_text
    assert "市中医院" not in dumped_text
    assert "补阳还五汤" not in dumped_text
    assert "user_id" not in dumped_text


def test_unknown_norm_syndrome_fails(tmp_path: Path):
    root = tmp_path / "TCM-SD"
    make_dataset(root)
    write_jsonl(
        root / "train.json",
        [
            labeled_row(
                user_id="u9",
                lcd_id="X",
                lcd_name="中风病",
                syndrome="未知证",
                norm="未知证",
                text="x",
            )
        ],
    )
    with pytest.raises(TcmSdError, match="not in vocab"):
        clean_directory(root)


def test_missing_schema_fails(tmp_path: Path):
    root = tmp_path / "TCM-SD"
    make_dataset(root)
    write_jsonl(root / "dev.json", [{"user_id": "u", "lcd_name": "中风病"}])
    with pytest.raises(TcmSdError, match="missing keys"):
        clean_directory(root)


def test_test_no_answer_cannot_carry_labels(tmp_path: Path):
    root = tmp_path / "TCM-SD"
    make_dataset(root)
    write_jsonl(
        root / "test_no_answer.json",
        [
            labeled_row(
                user_id="u4",
                lcd_id="BNP20",
                lcd_name="胃痞病",
                syndrome="湿热下注证",
                norm="湿热下注证",
                text="胃脘痞满。",
            )
        ],
    )
    with pytest.raises(TcmSdError, match="unexpectedly contains syndrome labels"):
        clean_directory(root)


def test_write_outputs_keeps_publish_false(tmp_path: Path):
    root = tmp_path / "TCM-SD"
    make_dataset(root)
    records, report = clean_directory(root)
    result = write_clean_outputs(records, report, tmp_path / "out")
    stats = json.loads((tmp_path / "out" / "stats.json").read_text(encoding="utf-8"))
    assert result["publish"] is False
    assert result["record_count"] >= 3
    assert stats["publish"] is False
    assert stats["record_count"] >= 3
