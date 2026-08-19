from __future__ import annotations

from pathlib import Path

from data_ingestion.tcmchat_600k import clean_directory, write_clean_outputs


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_corpus(root: Path) -> None:
    _write(root / "pretrain/train/books/national_standard/2022年中药药典.txt", "药典\n")
    _write(root / "pretrain/train/books/national_standard/中医临床诊疗术语疾病.txt", "疾病\n")
    _write(root / "pretrain/train/books/textbook/中药学.txt", "中药学\n")
    _write(root / "pretrain/train/books/medical_case/01_丁光迪.txt", "汤某女22岁\n")
    _write(root / "pretrain/train/opendata/ChatMed_TCM-v0.2_.txt", "问答\n")
    _write(root / "pretrain/train/web/2019_baidubaike.txt", "百科\n")
    _write(root / "pretrain/test/2022年中药药典.txt", "药典不同\n")
    _write(root / "pretrain/test/中医临床诊疗术语疾病.txt", "疾病\n")
    _write(root / "sft/train/knowledge.json", "[]\n")
    _write(root / "sft/final_train_data_for_baichuan_format/train_baichuan.json", "[]\n")
    _write(root / "README.md", "apache\n")


def test_inventory_groups_and_detects_duplicate_test(tmp_path: Path):
    root = tmp_path / "TCMChat-dataset-600k"
    make_corpus(root)
    records, report = clean_directory(root)
    assert records == []
    assert report["publish"] is False
    assert report["group_counts"]["books/national_standard"]["files"] == 2
    assert report["group_counts"]["books/medical_case"]["files"] == 1
    assert report["identical_pretrain_test_copies"] == ["中医临床诊疗术语疾病.txt"]
    assert report["divergent_pretrain_test_copies"] == ["2022年中药药典.txt"]
    assert report["missing_papers"] is True
    result = write_clean_outputs(records, report, tmp_path / "out")
    assert result["record_count"] == 0
    assert "汤某" not in (tmp_path / "out" / "records.jsonl").read_text(encoding="utf-8")
