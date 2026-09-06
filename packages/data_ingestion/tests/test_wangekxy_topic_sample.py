from pathlib import Path

import pytest

from knowledge_model.constants import EdgeType, NodeType

from data_ingestion.wangekxy_topic_sample import clean_file, write_clean_outputs

GO_SOURCE_IDS = [
    "tcm-materia-medica",
    "tcm-case-records",
    "tcm-acupuncture-classics",
    "tcm-diagnostics",
    "tcm-gynecology-pediatrics",
    "tcm-external-surgical",
    "tcm-collected-works",
    "tcm-health-cultivation",
    "tcm-reference-compendia",
]


@pytest.mark.parametrize("source_id", GO_SOURCE_IDS)
def test_topic_sample_emits_source_node(tmp_path: Path, source_id: str):
    path = tmp_path / "sample.jsonl"
    path.write_text(
        '{"title":"辅行诀脏腑用药法要","dynasty":"梁","author":"陶弘景","text":"小泻肝汤 枳实 芍药 生姜。"}\n',
        encoding="utf-8",
    )
    records, report = clean_file(
        path,
        source_id=source_id,
        batch_id="test-batch",
        import_scope_key=f"huggingface:wangekxy/{source_id}",
        lexicon_path=[],
    )
    names = {record.node_name for record in records}
    assert "辅行诀脏腑用药法要" in names
    assert all(record.node_type in {item.value for item in NodeType} for record in records)
    assert all(
        edge.type in {item.value for item in EdgeType} for record in records for edge in record.edges
    )
    assert report["work_count"] == 1
    assert report["publish"] is False
    result = write_clean_outputs(records, report, tmp_path / "out")
    assert result["record_count"] >= 1
    assert result["publish"] is False


def test_topic_sample_mentions_known_lexicon_term(tmp_path: Path):
    lexicon = tmp_path / "lex.jsonl"
    lexicon.write_text(
        '{"node_type":"药材","node_name":"人参"}\n',
        encoding="utf-8",
    )
    path = tmp_path / "sample.jsonl"
    path.write_text(
        '{"title":"药性歌括四百味","dynasty":"明","author":"龚廷贤","text":"人参味甘，大补元气。"}\n',
        encoding="utf-8",
    )
    records, report = clean_file(
        path,
        source_id="tcm-materia-medica",
        batch_id="test-batch",
        import_scope_key="huggingface:wangekxy/tcm-materia-medica",
        lexicon_path=lexicon,
    )
    names = {(record.node_type, record.node_name) for record in records}
    assert ("来源", "药性歌括四百味") in names
    assert ("药材", "人参") in names
    assert report["publish"] is False
