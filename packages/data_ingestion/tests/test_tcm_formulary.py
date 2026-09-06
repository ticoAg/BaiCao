from pathlib import Path

from data_ingestion.tcm_formulary import clean_file, write_clean_outputs


def test_sample_emits_source_and_optional_mentions(tmp_path: Path):
    path = tmp_path / "sample.jsonl"
    path.write_text(
        '{"title":"辅行诀脏腑用药法要","dynasty":"梁","author":"陶弘景","text":"小泻肝汤 枳实 芍药 生姜。"}\n',
        encoding="utf-8",
    )
    records, report = clean_file(path, lexicon_path=[])
    names = {record.node_name for record in records}
    assert "辅行诀脏腑用药法要" in names
    assert report["work_count"] == 1
    assert report["publish"] is False
    result = write_clean_outputs(records, report, tmp_path / "out")
    assert result["record_count"] >= 1
