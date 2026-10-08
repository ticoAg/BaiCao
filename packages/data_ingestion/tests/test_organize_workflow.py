from __future__ import annotations

from pathlib import Path

from graph_schema.constants import NodeType

from data_ingestion.models import ExtractionCandidate
from data_ingestion.organize_workflow import accept_agent_candidates
from data_ingestion.tcmchat_case_units import dump_prepare, prepare_directory, redact_case_text, split_case_book
from data_ingestion.tcmchat_textbooks import split_textbook


def test_redact_and_split_case_book(tmp_path: Path):
    path = tmp_path / "01_丁光迪.txt"
    path.write_text(
        "前言\n例一汤某女22岁本校学生\n初诊感冒。\n例二岳某男40岁农民\n脾胃不健。\n",
        encoding="utf-8",
    )
    units = split_case_book(path)
    assert len(units) == 2
    assert "汤某" not in units[0].text
    assert "女22岁" in units[0].text
    assert "患者" in units[0].text
    assert "岳某" not in units[1].text
    assert "男40岁" in units[1].text
    assert redact_case_text("电话13800138000") != "电话13800138000"


def test_prepare_writes_agent_queue(tmp_path: Path):
    book = tmp_path / "cases"
    book.mkdir()
    (book / "01_丁光迪.txt").write_text("例一李某女30岁\n咳嗽。\n", encoding="utf-8")
    batch = prepare_directory(book)
    assert batch.report["unit_count"] == 1
    assert any(record.node_type == "医案" for record in batch.records)
    dumped = dump_prepare(batch, tmp_path / "out")
    queue = (tmp_path / "out" / "agent_queue.jsonl").read_text(encoding="utf-8")
    assert dumped["unit_count"] == 1
    assert "李某" not in queue
    assert "病证" in queue


def test_accept_runs_identity_and_brand_gate():
    batch = accept_agent_candidates(
        [
            ExtractionCandidate(
                node_type=NodeType.DISEASE,
                node_name="感冒",
                source_name="case",
                role="疾病",
                stable_id="感冒",
                evidence_ref="01_丁光迪.txt:例一",
            ),
            ExtractionCandidate(
                node_type=NodeType.FORMULA,
                node_name="同仁堂乌鸡白凤丸",
                source_name="case",
                role="中成药",
                stable_id="wuji",
            ),
        ],
        source_id="tcmchat-medical-cases",
        batch_id="test",
        import_scope_key="test",
        processor="test",
    )
    assert [record.node_name for record in batch.records] == ["感冒"]
    assert batch.quarantined[0]["reason"] == "brand"


def test_prepare_keeps_demographics_and_lexicon_hits(tmp_path: Path):
    book = tmp_path / "cases"
    book.mkdir()
    (book / "01_丁光迪.txt").write_text("例一汤某女22岁\n诊为感冒，予桂枝汤。\n", encoding="utf-8")
    lexicon = tmp_path / "lex.jsonl"
    lexicon.write_text(
        '{"node_type":"病证","node_name":"感冒"}\n{"node_type":"方剂","node_name":"桂枝汤"}\n',
        encoding="utf-8",
    )
    batch = prepare_directory(book, lexicon_path=lexicon)
    cases = [record for record in batch.records if record.node_type == "医案"]
    assert cases[0].properties["sex"] == "女"
    assert cases[0].properties["age"] == "22岁"
    names = {record.node_name for record in batch.records}
    assert {"感冒", "桂枝汤"} <= names
    assert any(edge.type == "记载于医案" for record in batch.records for edge in record.edges)


def test_split_textbook_chapters(tmp_path: Path):
    path = tmp_path / "中医基础理论.txt"
    path.write_text("前言说明。\n第一章中医学概述\n正文甲。\n第二章阴阳\n正文乙。\n", encoding="utf-8")
    units = split_textbook(path)
    assert len(units) == 3
    assert units[0].metadata["marker"] == "前言"
    assert "第一章" in units[1].metadata["marker"]
