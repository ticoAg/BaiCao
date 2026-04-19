"""覆盖药典 dry-run 产物落盘和并发行为。"""

import asyncio
import json
import time

from data_ingestion.processors.huggingface.zjufanlab_tcmchat_dataset_600k.national_standard_2022_pharmacopoeia.dry_run import (
    run_pharmacopoeia_dry_run,
)
from data_ingestion.processors.huggingface.zjufanlab_tcmchat_dataset_600k.national_standard_2022_pharmacopoeia.llm_extraction import (
    FakeExtractionTransport,
)


def test_dry_run_writes_expected_artifacts(tmp_path):
    """验证 dry-run 会生成调试所需的阶段性落盘文件。"""

    source = tmp_path / "sample.txt"
    source.write_text(
        (
            "一枝黄花\nYizhihuanghua\nSOLIDAGINISHERBA\n本品为菊科植物一枝黄花SolidagodecurrensLour.的干燥全草。\n"
            "饮片\n【炮制】除去杂质。\n【性味与归经】辛、苦，凉。归肺、肝经。\n【功能与主治】清热解毒，疏散风热。\n"
        )
        * 2,
        encoding="utf-8",
    )
    transport = FakeExtractionTransport(
        response_text='{"herb":{"herb_name":"一枝黄花"},"prepared_piece":null,"warnings":[],"confidence_notes":"ok"}'
    )

    result = run_pharmacopoeia_dry_run(
        local_path=source,
        output_dir=tmp_path / "out",
        limit=1,
        transport=transport,
    )

    assert result.summary["entries_attempted"] == 1
    assert result.summary["llm_request_failed_count"] == 0
    assert (result.output_dir / "entries.jsonl").exists()
    assert (result.output_dir / "parsed_sections.jsonl").exists()
    assert (result.output_dir / "llm_requests.jsonl").exists()
    assert (result.output_dir / "llm_responses.jsonl").exists()
    assert (result.output_dir / "validated_extractions.jsonl").exists()
    assert (result.output_dir / "graph_bundles.jsonl").exists()
    assert (result.output_dir / "summary.json").exists()


def test_dry_run_honors_entry_offset_and_persists_llm_debug_fields(tmp_path):
    """验证 dry-run 支持 entry offset，并保留 LLM 调试字段。"""

    source = tmp_path / "sample.txt"
    source.write_text(
        (
            "一枝黄花\nYizhihuanghua\nSOLIDAGINISHERBA\n本品为菊科植物一枝黄花SolidagodecurrensLour.的干燥全草。\n"
            "饮片\n【炮制】除去杂质。\n【性味与归经】辛、苦，凉。归肺、肝经。\n【功能与主治】清热解毒，疏散风热。\n"
            "丁公藤\nDinggongteng\nERYCIBAERHERBA\n本品为旋花科植物丁公藤的干燥藤茎。\n"
            "饮片\n【炮制】除去杂质。\n【性味与归经】辛，温。归肝经。\n【功能与主治】祛风除湿。\n"
        ),
        encoding="utf-8",
    )
    transport = FakeExtractionTransport(
        response_text='{"herb":{"herb_name":"丁公藤"},"prepared_piece":null,"warnings":[],"confidence_notes":"ok"}'
    )

    result = run_pharmacopoeia_dry_run(
        local_path=source,
        output_dir=tmp_path / "out",
        limit=1,
        entry_offset=1,
        transport=transport,
    )

    entries = [
        json.loads(line)
        for line in (result.output_dir / "entries.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    llm_responses = [
        json.loads(line)
        for line in (result.output_dir / "llm_responses.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert result.summary["entries_attempted"] == 1
    assert entries[0]["entry_title"] == "丁公藤"
    assert llm_responses[0]["elapsed_ms"] >= 0
    assert "raw_response_preview" in llm_responses[0]


def test_dry_run_uses_chinese_edge_labels_and_supports_concurrency(tmp_path):
    """验证 dry-run 并发执行时仍会输出中文边标签。"""

    class SlowTransport:
        """用固定延迟模拟真实模型调用，验证并发调度是否生效。"""

        async def extract_json_text(self, *, system_prompt: str, user_payload: dict[str, object]) -> str:
            """返回一份稳定的饮片抽取 JSON，便于断言映射结果。"""

            await asyncio.sleep(0.05)
            return (
                '{"herb":{"herb_name":"一枝黄花"},"prepared_piece":{"piece_name":"一枝黄花饮片",'
                '"parent_herb_name":"一枝黄花","processing_text":"除去杂质。","flavors":["辛"],'
                '"nature":"凉","meridians":["肺经"],"efficacies":["清热解毒"],"indications":["喉痹"],'
                '"usage_text":"9～15g。","storage_text":"置干燥处。","caution_text":null},'
                '"warnings":[],"confidence_notes":"ok"}'
            )

    source = tmp_path / "sample.txt"
    source.write_text(
        (
            "一枝黄花\nYizhihuanghua\nSOLIDAGINISHERBA\n本品为菊科植物一枝黄花SolidagodecurrensLour.的干燥全草。\n"
            "饮片\n【炮制】除去杂质。\n【性味与归经】辛、苦，凉。归肺、肝经。\n【功能与主治】清热解毒，疏散风热。用于喉痹。\n"
        )
        * 3,
        encoding="utf-8",
    )

    started_at = time.perf_counter()
    result = run_pharmacopoeia_dry_run(
        local_path=source,
        output_dir=tmp_path / "out",
        limit=3,
        concurrency=3,
        transport=SlowTransport(),
    )
    elapsed = time.perf_counter() - started_at

    graph_bundle = json.loads((result.output_dir / "graph_bundles.jsonl").read_text(encoding="utf-8").splitlines()[0])

    assert elapsed < 0.13
    assert "具有性味" in graph_bundle["edge_types"]
    assert "归于经脉" in graph_bundle["edge_types"]
    assert "具有功效" in graph_bundle["edge_types"]
    assert "治疗病证" in graph_bundle["edge_types"]
