"""覆盖药典条目 LLM 抽取边界的成功与失败分类。"""

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
    """验证合法 JSON 响应会被校验并标记为成功。"""

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
    """验证非法 JSON 会被识别为 llm_json_invalid。"""

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
    """验证 schema 不匹配时会保留原始响应用于调试。"""

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
    """验证超时会被统一归类为请求失败。"""

    class SlowTransport:
        """模拟会超时的 transport，实现请求失败分支覆盖。"""

        async def extract_json_text(self, *, system_prompt: str, user_payload: dict[str, object]) -> str:
            """延迟返回固定 JSON，触发外层超时控制。"""

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
    """验证真实 transport 使用 Responses API 并返回 output_text。"""

    class DummyResponse:
        """模拟 Responses API 返回对象。"""

        output_text = '{"herb":{"herb_name":"一枝黄花"},"prepared_piece":null,"warnings":[],"confidence_notes":"ok"}'

    class DummyResponses:
        """模拟 OpenAI client.responses 对象。"""

        def __init__(self) -> None:
            """初始化最近一次调用参数的记录槽。"""

            self.last_kwargs = None

        async def create(self, **kwargs):
            """记录调用参数并返回固定响应对象。"""

            self.last_kwargs = kwargs
            return DummyResponse()

    class DummyClient:
        """模拟最小可用的 OpenAI 式客户端。"""

        def __init__(self) -> None:
            """挂载伪造的 responses 资源。"""

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


def test_openai_transport_retries_rate_limit_then_succeeds():
    """验证真实 transport 在遇到限流错误时会按配置重试。"""

    class DummyResponse:
        output_text = '{"herb":{"herb_name":"一枝黄花"},"prepared_piece":null,"warnings":[],"confidence_notes":"ok"}'

    class DummyResponses:
        def __init__(self) -> None:
            self.calls = 0

        async def create(self, **kwargs):
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("429 rate limit exceeded")
            return DummyResponse()

    class DummyClient:
        def __init__(self) -> None:
            self.responses = DummyResponses()

    transport = OpenAICompatibleExtractionTransport(
        api_key="test",
        base_url="https://code.ticoag.fun",
        model="demo",
        max_attempts=2,
        retry_backoff_seconds=0,
    )
    dummy_client = DummyClient()
    transport.client = dummy_client

    raw_text = asyncio.run(
        transport.extract_json_text(system_prompt="return json", user_payload={"entry_title": "一枝黄花"})
    )

    assert raw_text.startswith('{"herb"')
    assert dummy_client.responses.calls == 2


def test_openai_transport_retries_without_thinking_hints_when_provider_rejects_field():
    """验证 provider 不支持 `enable_thinking` 时会自动降级重试。"""

    class DummyResponse:
        output_text = '{"herb":{"herb_name":"一枝黄花"},"prepared_piece":null,"warnings":[],"confidence_notes":"ok"}'

    class DummyResponses:
        def __init__(self) -> None:
            self.calls = []

        async def create(self, **kwargs):
            self.calls.append(kwargs)
            if len(self.calls) == 1:
                raise RuntimeError('400 unknown field "enable_thinking"')
            return DummyResponse()

    class DummyClient:
        def __init__(self) -> None:
            self.responses = DummyResponses()

    transport = OpenAICompatibleExtractionTransport(
        api_key="test",
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        model="demo",
        max_attempts=2,
        retry_backoff_seconds=0,
    )
    dummy_client = DummyClient()
    transport.client = dummy_client

    raw_text = asyncio.run(
        transport.extract_json_text(system_prompt="return json", user_payload={"entry_title": "一枝黄花"})
    )

    assert raw_text.startswith('{"herb"')
    assert len(dummy_client.responses.calls) == 2
    assert "extra_body" in dummy_client.responses.calls[0]
    assert "extra_body" not in dummy_client.responses.calls[1]


def test_normalize_openai_base_url_appends_v1_when_missing():
    """验证基础地址缺少 `/v1` 时会自动补齐。"""

    transport = OpenAICompatibleExtractionTransport(api_key="test", base_url="https://code.ticoag.fun", model="demo")

    assert normalize_openai_base_url(transport.base_url) == "https://code.ticoag.fun/v1"


def test_normalize_openai_base_url_keeps_existing_versioned_path():
    """验证已有版本路径时不会错误追加 `/v1`。"""

    assert normalize_openai_base_url("https://ark.cn-beijing.volces.com/api/v3") == "https://ark.cn-beijing.volces.com/api/v3"
