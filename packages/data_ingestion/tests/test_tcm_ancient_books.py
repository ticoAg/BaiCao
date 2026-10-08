from __future__ import annotations

from pathlib import Path

import pytest

from graph_schema.constants import EdgeType, NodeType

from data_ingestion.tcm_ancient_books import (
    TcmAncientBooksError,
    clean_directory,
    extract_directory,
    write_clean_outputs,
    write_extract_outputs,
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


def test_extract_directory_emits_source_and_lexicon_mentions(tmp_path: Path):
    root = tmp_path / "TCM-Ancient-Books"
    make_dataset(root)
    lexicon = tmp_path / "lex.jsonl"
    lexicon.write_text('{"node_type":"药材","node_name":"甘草"}\n', encoding="utf-8")
    write_gb18030(root / "000-神农本草经.txt", "<书名>神农本草经\n甘草。\n")
    records, report = extract_directory(
        root,
        lexicon_path=lexicon,
        min_id=0,
        max_id=1,
    )
    names = {(record.node_type, record.node_name) for record in records}
    assert ("来源", "神农本草经") in names
    assert ("药材", "甘草") in names
    assert all(record.node_type in {item.value for item in NodeType} for record in records)
    assert all(
        edge.type in {item.value for item in EdgeType} for record in records for edge in record.edges
    )
    assert report["publish"] is False
    result = write_extract_outputs(records, report, tmp_path / "out")
    assert result["record_count"] >= 2
    assert result["publish"] is False


def test_extract_lossy_decode_and_unnumbered(tmp_path: Path):
    root = tmp_path / "TCM-Ancient-Books"
    make_dataset(root)
    (root / "002-婴童类萃.txt").write_bytes("甘草".encode("gb18030") + b"\xb5" + "正文".encode("gb18030"))
    lexicon = tmp_path / "lex.jsonl"
    lexicon.write_text('{"node_type":"药材","node_name":"甘草"}\n', encoding="utf-8")
    records, report = extract_directory(
        root,
        lexicon_path=lexicon,
        min_id=2,
        max_id=2,
        include_unnumbered=True,
    )
    names = {record.node_name for record in records}
    assert "婴童类萃" in names
    assert "甘草" in names
    assert report["lossy_decode_files"]
    unnumbered, unnumbered_report = extract_directory(
        root,
        lexicon_path=[],
        min_id=900,
        max_id=900,
        include_unnumbered=True,
    )
    assert any(record.node_name.startswith("700") for record in unnumbered)
    assert unnumbered_report["include_unnumbered"] is True


def test_extract_merges_mentions_across_numbered_and_unnumbered(tmp_path: Path):
    root = tmp_path / "TCM-Ancient-Books"
    make_dataset(root)
    lexicon = tmp_path / "lex.jsonl"
    lexicon.write_text('{"node_type":"药材","node_name":"甘草"}\n', encoding="utf-8")
    write_gb18030(root / "000-神农本草经.txt", "甘草。\n")
    write_gb18030(root / "700.李培生老中医经验集.txt", "甘草\n")
    records, report = extract_directory(
        root,
        lexicon_path=lexicon,
        min_id=0,
        max_id=0,
        include_unnumbered=True,
    )
    herbs = [record for record in records if record.node_name == "甘草"]
    assert len(herbs) == 1
    assert herbs[0].properties["tcm_type"] == "来源古籍书目提及"
    origins = {edge.target for edge in herbs[0].edges}
    assert "神农本草经" in origins
    assert any("李培生" in target for target in origins)
    sources = {
        record.node_name: record.properties.get("tcm_type")
        for record in records
        if record.node_type == NodeType.SOURCE.value
    }
    assert sources["神农本草经"] == "来源古籍书目"
    assert any(name.startswith("700") and value == "来源现代医论" for name, value in sources.items())
    assert report["include_unnumbered"] is True


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
