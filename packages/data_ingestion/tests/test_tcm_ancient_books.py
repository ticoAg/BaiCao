from __future__ import annotations

from pathlib import Path

import pytest

from data_ingestion.tcm_ancient_books import (
    TcmAncientBooksError,
    clean_directory,
    write_clean_outputs,
)


def write_gb18030(path: Path, text: str) -> None:
    path.write_bytes(text.encode("gb18030"))


def make_dataset(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    write_gb18030(root / "000-神农本草经.txt", "<书名>神农本草经\n上经。\n")
    write_gb18030(root / "001-本草纲目.txt", "<书名>本草纲目\n草部。\n")
    (root / "README.md").write_text("# books\n", encoding="utf-8")
    (root / "000-神农本草经.txt.baiduyun.downloading").write_bytes(b"partial")
    write_gb18030(root / "700.李培生老中医经验集.txt", "名老中医经验集\n")


def test_clean_directory_builds_bibliography_without_records(tmp_path: Path):
    root = tmp_path / "TCM-Ancient-Books"
    make_dataset(root)
    records, report = clean_directory(root)
    assert records == []
    assert report["publish"] is False
    assert report["book_count"] == 2
    assert report["encoding_counts"] == {"gb18030": 2}
    assert report["first_book"] == "神农本草经"
    assert report["last_book"] == "本草纲目"
    reasons = {item["file"]: item["reason"] for item in report["isolated_files"]}
    assert reasons["README.md"] == "repo_metadata"
    assert reasons["000-神农本草经.txt.baiduyun.downloading"] == "incomplete_download"
    assert reasons["700.李培生老中医经验集.txt"] == "unnumbered_or_non_txt"


def test_duplicate_title_fails(tmp_path: Path):
    root = tmp_path / "TCM-Ancient-Books"
    make_dataset(root)
    write_gb18030(root / "002-神农本草经.txt", "重复书名\n")
    with pytest.raises(TcmAncientBooksError, match="duplicate title"):
        clean_directory(root)


def test_missing_id_fails(tmp_path: Path):
    root = tmp_path / "TCM-Ancient-Books"
    make_dataset(root)
    write_gb18030(root / "003-肘后备急方.txt", "缺号\n")
    with pytest.raises(TcmAncientBooksError, match="missing book ids"):
        clean_directory(root)


def test_undecodable_numbered_file_is_isolated(tmp_path: Path):
    root = tmp_path / "TCM-Ancient-Books"
    make_dataset(root)
    (root / "002-无法解码.txt").write_bytes(b"\xff\xfe\x00\x80bad")
    records, report = clean_directory(root)
    assert records == []
    assert report["book_count"] == 2
    assert {"file": "002-无法解码.txt", "reason": "decode_error"} in report["isolated_files"]


def test_write_outputs_keeps_empty_records(tmp_path: Path):
    root = tmp_path / "TCM-Ancient-Books"
    make_dataset(root)
    records, report = clean_directory(root)
    result = write_clean_outputs(records, report, tmp_path / "out")
    dumped = (tmp_path / "out" / "records.jsonl").read_text(encoding="utf-8")
    stats_text = (tmp_path / "out" / "stats.json").read_text(encoding="utf-8")
    assert result["record_count"] == 0
    assert result["publish"] is False
    assert dumped == ""
    assert "上经" not in dumped
    assert "上经" not in stats_text
