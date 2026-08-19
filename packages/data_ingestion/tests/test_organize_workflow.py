from __future__ import annotations

import json
from pathlib import Path

from knowledge_model.constants import NodeType

from data_ingestion.models import ExtractionCandidate
from data_ingestion.organize_workflow import accept_agent_candidates
from data_ingestion.tcmchat_case_units import dump_prepare, prepare_directory, redact_case_text, split_case_book


def test_redact_and_split_case_book(tmp_path: Path):
    path = tmp_path / "01_丁光迪.txt"
    path.write_text(
        "前言\n例一汤某女22岁本校学生\n初诊感冒。\n例二岳某男40岁农民\n脾胃不健。\n",
        encoding="utf-8",
    )
    units = split_case_book(path)
    assert len(units) == 2
    assert "汤某" not in units[0].text
    assert "22岁" not in units[0].text
    assert "患者" in units[0].text
    assert redact_case_text("电话13800138000") != "电话13800138000"


def test_prepare_writes_agent_queue(tmp_path: Path):
    book = tmp_path / "cases"
    book.mkdir()
    (book / "01_丁光迪.txt").write_text("例一李某女30岁\n咳嗽。\n", encoding="utf-8")
    batch = prepare_directory(book)
    assert batch.records == []
    assert batch.report["unit_count"] == 1
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
