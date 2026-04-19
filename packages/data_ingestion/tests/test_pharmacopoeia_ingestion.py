"""覆盖药典条目大批量 ingest 编排的记录快照产物。"""

import json

from data_ingestion.processors.huggingface.zjufanlab_tcmchat_dataset_600k.national_standard_2022_pharmacopoeia.ingestion import (
    run_pharmacopoeia_ingestion,
)
from data_ingestion.processors.huggingface.zjufanlab_tcmchat_dataset_600k.national_standard_2022_pharmacopoeia.llm_extraction import (
    FakeExtractionTransport,
    build_openai_compatible_transport_from_env,
)


def test_run_pharmacopoeia_ingestion_writes_graph_import_records_snapshot(tmp_path):
    """验证 ingest 编排会产出 GraphImportRecord JSONL 快照。"""

    source = tmp_path / "sample.txt"
    source.write_text(
        (
            "一枝黄花\nYizhihuanghua\nSOLIDAGINISHERBA\n本品为菊科植物一枝黄花SolidagodecurrensLour.的干燥全草。\n"
            "饮片\n【炮制】除去杂质。\n【性味与归经】辛、苦，凉。归肺、肝经。\n【功能与主治】清热解毒，疏散风热。用于喉痹。\n"
        ),
        encoding="utf-8",
    )

    result = run_pharmacopoeia_ingestion(
        local_path=source,
        output_dir=tmp_path / "out",
        limit=1,
        transport=FakeExtractionTransport(
            response_text=(
                '{"herb":{"herb_name":"一枝黄花"},"prepared_piece":{"piece_name":"一枝黄花饮片",'
                '"parent_herb_name":"一枝黄花","processing_text":"除去杂质。","flavors":["辛"],'
                '"nature":"凉","meridians":["肺经"],"efficacies":["清热解毒"],"indications":["喉痹"],'
                '"usage_text":"9～15g。","storage_text":"置干燥处。","caution_text":null},'
                '"warnings":[],"confidence_notes":"ok"}'
            )
        ),
    )

    records_path = result.output_dir / "graph_import_records.jsonl"
    assert records_path.exists()
    lines = [json.loads(line) for line in records_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert result.summary["records_generated"] == len(lines)
    assert {line["node_name"] for line in lines} >= {"一枝黄花", "一枝黄花条目证据", "一枝黄花饮片"}


def test_run_pharmacopoeia_ingestion_can_retry_only_failed_entries(tmp_path):
    """验证基于前一次产物重跑时，只会处理此前失败的条目。"""

    source = tmp_path / "sample.txt"
    source.write_text(
        (
            "一枝黄花\nYizhihuanghua\nSOLIDAGINISHERBA\n本品为菊科植物一枝黄花的干燥全草。\n"
            "饮片\n【炮制】除去杂质。\n"
            "丁公藤\nDinggongteng\nERYCIBAERHERBA\n本品为旋花科植物丁公藤的干燥藤茎。\n"
            "饮片\n【炮制】除去杂质。\n"
        ),
        encoding="utf-8",
    )
    previous_run = tmp_path / "previous"
    previous_run.mkdir()
    (previous_run / "validated_extractions.jsonl").write_text(
        "\n".join(
            [
                '{"entry_key":"一枝黄花:1-6","entry_title":"一枝黄花","status":"success"}',
                '{"entry_key":"丁公藤:7-12","entry_title":"丁公藤","status":"llm_request_failed"}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = run_pharmacopoeia_ingestion(
        local_path=source,
        output_dir=tmp_path / "retry",
        limit=None,
        retry_failed_from=previous_run,
        transport=FakeExtractionTransport(
            response_text='{"herb":{"herb_name":"丁公藤"},"prepared_piece":null,"warnings":[],"confidence_notes":"retry"}'
        ),
    )

    entries = [
        json.loads(line)
        for line in (result.output_dir / "entries.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert result.summary["entries_attempted"] == 1
    assert entries[0]["entry_title"] == "丁公藤"


def test_build_openai_compatible_transport_from_env_prefers_explicit_args(monkeypatch):
    """验证 transport 初始化支持环境变量和显式覆盖。"""

    monkeypatch.setenv("OPENAI_API_KEY", "env-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.com")
    monkeypatch.setenv("OPENAI_MODEL", "env-model")

    transport = build_openai_compatible_transport_from_env(model="explicit-model", timeout_seconds=12)

    assert transport.api_key == "env-key"
    assert transport.base_url == "https://example.com/v1"
    assert transport.model == "explicit-model"
    assert transport.timeout_seconds == 12


def test_build_openai_compatible_transport_from_env_accepts_retry_options(monkeypatch):
    """验证 transport 初始化能携带限流重试参数。"""

    monkeypatch.setenv("OPENAI_API_KEY", "env-key")

    transport = build_openai_compatible_transport_from_env(max_attempts=3, retry_backoff_seconds=0.5)

    assert transport.max_attempts == 3
    assert transport.retry_backoff_seconds == 0.5
