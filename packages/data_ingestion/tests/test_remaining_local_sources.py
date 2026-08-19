from __future__ import annotations

import json
from pathlib import Path

import pytest

from data_ingestion.classical_tcm_canon import (
    ClassicalTcmCanonError,
    clean_file as clean_canon,
    write_clean_outputs as write_canon,
)
from data_ingestion.sylvanl_tcm_pretrain import (
    HELD_FILES,
    SylvanLPretrainError,
    clean_directory as clean_pretrain,
    write_clean_outputs as write_pretrain,
)
from data_ingestion.zybert_pretrain import (
    ZybertPretrainError,
    clean_file as clean_rar,
    parse_bsdtar_listing,
)


def write_parquet(path: Path, rows: list[dict]) -> None:
    pytest.importorskip("pyarrow")
    import pyarrow as pa
    import pyarrow.parquet as pq

    pq.write_table(pa.Table.from_pylist(rows), path)


CANON_ROW = {
    "id": "canon-伤寒论-0000",
    "work_family": "伤寒论",
    "title": "伤寒论",
    "author": "张仲景",
    "dynasty": "汉",
    "source_format": "txt",
    "edition_type": "scan_original",
    "extraction_method": "TEXT_EXTRACT",
    "rights_status": "pd",
    "rights_basis": "author_death",
    "validation_status": "single_source",
    "validation_overlap": 0.0,
    "char_count": 4,
    "cjk_ratio": 1.0,
    "ship_tier": "A",
    "text": "太阳病。",
}


def test_canon_emits_no_records(tmp_path: Path):
    path = tmp_path / "classical-tcm-canon.parquet"
    second = dict(CANON_ROW)
    second.update({"id": "canon-内经-0001", "work_family": "黄帝内经", "title": "素问", "char_count": 3, "text": "内经。"})
    write_parquet(path, [CANON_ROW, second])
    records, report = clean_canon(path)
    assert records == []
    assert report["work_count"] == 2
    assert report["char_count_sum"] == 7
    assert report["publish"] is False
    result = write_canon(records, report, tmp_path / "out")
    assert result["record_count"] == 0
    assert "太阳病" not in (tmp_path / "out" / "records.jsonl").read_text(encoding="utf-8")


def test_canon_duplicate_title_fails(tmp_path: Path):
    path = tmp_path / "classical-tcm-canon.parquet"
    dup = dict(CANON_ROW)
    dup["id"] = "canon-伤寒论-0001"
    write_parquet(path, [CANON_ROW, dup])
    with pytest.raises(ClassicalTcmCanonError, match="duplicate title"):
        clean_canon(path)


def test_pretrain_isolates_mixup_and_emits_no_records(tmp_path: Path):
    root = tmp_path / "TCM-Pretrain"
    root.mkdir()
    (root / HELD_FILES[0]).write_text(json.dumps([{"text": "肺痈 桔梗汤"}], ensure_ascii=False), encoding="utf-8")
    (root / HELD_FILES[1]).write_text(json.dumps([{"text": "灵砂\n出处：局方"}], ensure_ascii=False), encoding="utf-8")
    (root / HELD_FILES[2]).write_text(
        json.dumps(
            [
                {
                    "text": "药名:注射用亚锡葡庚糖酸钠Ⅰ\n药理作用:氨苄西林钠为青霉素类抗生素。"
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    records, report = clean_pretrain(root)
    assert records == []
    assert report["mixed_pharmacology_rows"] == [
        {"file": HELD_FILES[2], "index": 0}
    ]
    assert report["quarantine_counts"]["text_rows"] == 3
    result = write_pretrain(records, report, tmp_path / "out")
    dumped = (tmp_path / "out" / "records.jsonl").read_text(encoding="utf-8")
    assert result["publish"] is False
    assert dumped == ""
    assert "氨苄西林" not in dumped


def test_pretrain_missing_file_fails(tmp_path: Path):
    with pytest.raises(SylvanLPretrainError, match="missing"):
        clean_pretrain(tmp_path)


def test_rar_listing_parser_and_magic():
    listing = "-rw-r--r--  0 0      0   820949983 Sep 20  2021 tcm_pretrain_corpus_a.txt\n"
    members = parse_bsdtar_listing(listing)
    assert members == [
        {
            "name": "tcm_pretrain_corpus_a.txt",
            "size": 820949983,
            "listing": listing.strip(),
        }
    ]
    with pytest.raises(ZybertPretrainError, match="not a RAR"):
        clean_rar(Path(__file__))
