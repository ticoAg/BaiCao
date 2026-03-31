import asyncio
import time

from data_ingestion.processors.huggingface.zjufanlab_tcmchat_dataset_600k.national_standard_2022_pharmacopoeia.extraction_models import (
    PharmacopoeiaEntrySections,
)
from data_ingestion.processors.huggingface.zjufanlab_tcmchat_dataset_600k.national_standard_2022_pharmacopoeia.llm_extraction import (
    FakeExtractionTransport,
    OpenAICompatibleExtractionTransport,
    extract_entry_with_llm,
    normalize_openai_base_url,
)


def test_extract_entry_with_llm_returns_validated_result():
    sections = PharmacopoeiaEntrySections(
        title_zh="一枝黄花",
        header_lines=["Yizhihuanghua", "SOLIDAGINISHERBA"],
        base_description="本品为菊科植物一枝黄花SolidagodecurrensLour.的干燥全草。",
        sections={},
        piece_sections={"性味与归经": "辛、苦，凉。归肺、肝经。"},
        raw_text="一枝黄花\nYizhihuanghua\nSOLIDAGINISHERBA\n本品为菊科植物一枝黄花SolidagodecurrensLour.的干燥全草。",
    )
    transport = FakeExtractionTransport(
        response_text='{"herb":{"herb_name":"一枝黄花"},"prepared_piece":null,"warnings":[],"confidence_notes":"ok"}'
    )

    result = asyncio.run(extract_entry_with_llm(sections, transport))

    assert result.status == "success"
    assert result.validated_extraction is not None
    assert result.validated_extraction.herb.herb_name == "一枝黄花"
    assert result.elapsed_ms >= 0
    assert "一枝黄花" in result.raw_response_preview


def test_extract_entry_with_llm_marks_invalid_json():
    sections = PharmacopoeiaEntrySections(
        title_zh="一枝黄花",
        header_lines=[],
        base_description=None,
        sections={},
        piece_sections={},
        raw_text="一枝黄花\nYizhihuanghua\nSOLIDAGINISHERBA",
    )
    transport = FakeExtractionTransport(response_text="not-json")

    result = asyncio.run(extract_entry_with_llm(sections, transport))

    assert result.status == "llm_json_invalid"
    assert result.validated_extraction is None
    assert result.error_message
    assert result.elapsed_ms >= 0
    assert result.raw_response_preview == "not-json"


def test_extract_entry_with_llm_marks_schema_invalid_and_keeps_raw_response():
    sections = PharmacopoeiaEntrySections(
        title_zh="一枝黄花",
        header_lines=[],
        base_description=None,
        sections={},
        piece_sections={},
        raw_text="一枝黄花\nYizhihuanghua\nSOLIDAGINISHERBA",
    )
    transport = FakeExtractionTransport(response_text='{"药材名称":"一枝黄花","备注":"缺：丁公藤"}')

    result = asyncio.run(extract_entry_with_llm(sections, transport))

    assert result.status == "llm_schema_invalid"
    assert result.validated_extraction is None
    assert "Field required" in (result.error_message or "")
    assert result.raw_response.startswith("{")
    assert "药材名称" in result.raw_response_preview


def test_extract_entry_with_llm_marks_transport_failure_when_timeout_expires():
    class SlowTransport:
        async def extract_json_text(self, *, system_prompt: str, user_payload: dict[str, object]) -> str:
            await asyncio.sleep(0.05)
            return "{}"

    sections = PharmacopoeiaEntrySections(
        title_zh="一枝黄花",
        header_lines=[],
        base_description=None,
        sections={},
        piece_sections={},
        raw_text="一枝黄花",
    )
    started_at = time.perf_counter()

    result = asyncio.run(extract_entry_with_llm(sections, SlowTransport(), request_timeout_seconds=0.01))

    assert result.status == "llm_request_failed"
    assert "timed out" in (result.error_message or "")
    assert result.elapsed_ms >= 0
    assert (time.perf_counter() - started_at) < 0.5


def test_openai_transport_uses_raw_responses_create_and_returns_output_text():
    class DummyResponse:
        output_text = '{"herb":{"herb_name":"一枝黄花"},"prepared_piece":null,"warnings":[],"confidence_notes":"ok"}'

    class DummyResponses:
        def __init__(self) -> None:
            self.last_kwargs = None

        async def create(self, **kwargs):
            self.last_kwargs = kwargs
            return DummyResponse()

    class DummyClient:
        def __init__(self) -> None:
            self.responses = DummyResponses()

    transport = OpenAICompatibleExtractionTransport(api_key="test", base_url="https://code.ticoag.fun", model="demo")
    dummy_client = DummyClient()
    transport.client = dummy_client

    raw_text = asyncio.run(
        transport.extract_json_text(system_prompt="return json", user_payload={"entry_title": "一枝黄花"})
    )

    assert raw_text.startswith('{"herb"')
    assert dummy_client.responses.last_kwargs is not None
    assert dummy_client.responses.last_kwargs["model"] == "demo"
    assert dummy_client.responses.last_kwargs["instructions"] == "return json"
    assert dummy_client.responses.last_kwargs["input"] == '{"entry_title": "一枝黄花"}'
    assert dummy_client.responses.last_kwargs["extra_body"]["enable_thinking"] is False
    assert dummy_client.responses.last_kwargs["extra_body"]["chat_template_kwargs"]["enable_thinking"] is False


def test_normalize_openai_base_url_appends_v1_when_missing():
    transport = OpenAICompatibleExtractionTransport(api_key="test", base_url="https://code.ticoag.fun", model="demo")

    assert normalize_openai_base_url(transport.base_url) == "https://code.ticoag.fun/v1"
