"""封装药典条目的 LLM 抽取传输层与结果校验逻辑。"""

from __future__ import annotations

import asyncio
import json
import os
import re
import time
from typing import Literal, Protocol

from openai import AsyncOpenAI
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .extraction_models import PharmacopoeiaEntrySections, PharmacopoeiaExtractionResult
from .prompts import PHARMACOPOEIA_EXTRACTION_SYSTEM_PROMPT, build_pharmacopoeia_user_payload


class ExtractionTransport(Protocol):
    """约束不同上游模型客户端都能返回同一份 JSON 文本。"""

    async def extract_json_text(self, *, system_prompt: str, user_payload: dict[str, object]) -> str:
        """执行一次结构化抽取请求并返回原始 JSON 文本。"""

        raise NotImplementedError


class FakeExtractionTransport:
    """提供固定响应，便于 dry-run 和测试调试链路本身。"""

    def __init__(self, response_text: str) -> None:
        """保存测试或本地调试时要返回的假响应文本。"""

        self.response_text = response_text

    async def extract_json_text(self, *, system_prompt: str, user_payload: dict[str, object]) -> str:
        """直接返回预设响应，不访问真实模型服务。"""

        return self.response_text


def normalize_openai_base_url(base_url: str) -> str:
    """把兼容 OpenAI 的基础地址统一成带 `/v1` 的形式。"""

    normalized = base_url.rstrip("/")
    if re.search(r"/v\d+$", normalized):
        return normalized
    return f"{normalized}/v1"


class OpenAICompatibleExtractionTransport:
    """使用 OpenAI Responses API 执行真实药典抽取请求。"""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        temperature: float = 0.0,
        timeout_seconds: float | None = None,
        max_attempts: int = 1,
        retry_backoff_seconds: float = 1.0,
    ) -> None:
        """从显式参数或环境变量初始化真实模型传输层。"""

        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        configured_base_url = base_url or os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1"
        self.base_url = normalize_openai_base_url(configured_base_url)
        self.model = model or os.getenv("OPENAI_MODEL") or "gpt-4.1-mini"
        self.temperature = temperature
        configured_timeout = timeout_seconds or float(os.getenv("OPENAI_TIMEOUT_SECONDS", "90"))
        self.timeout_seconds = configured_timeout
        self.max_attempts = max(1, max_attempts)
        self.retry_backoff_seconds = max(0.0, retry_backoff_seconds)
        self.client = AsyncOpenAI(
            api_key=self.api_key or "missing",
            base_url=self.base_url,
            timeout=self.timeout_seconds,
        )

    def _build_request_kwargs(
        self,
        *,
        system_prompt: str,
        user_payload: dict[str, object],
        include_thinking_hints: bool,
    ) -> dict[str, object]:
        """构造一次 Responses API 请求参数。"""

        kwargs: dict[str, object] = {
            "model": self.model,
            "instructions": system_prompt,
            "input": json.dumps(user_payload, ensure_ascii=False),
            "temperature": self.temperature,
        }
        if include_thinking_hints:
            kwargs["extra_body"] = {
                "enable_thinking": False,
                "chat_template_kwargs": {"enable_thinking": False},
            }
        return kwargs

    async def extract_json_text(self, *, system_prompt: str, user_payload: dict[str, object]) -> str:
        """向兼容 OpenAI 的模型服务发起一次结构化抽取请求。"""

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required for real LLM dry-run")
        last_error: Exception | None = None
        include_thinking_hints = True
        for attempt in range(1, self.max_attempts + 1):
            try:
                response = await self.client.responses.create(
                    **self._build_request_kwargs(
                        system_prompt=system_prompt,
                        user_payload=user_payload,
                        include_thinking_hints=include_thinking_hints,
                    )
                )
                response_text = getattr(response, "output_text", "")
                if not response_text:
                    raise ValueError("Responses API did not return output_text")
                return response_text
            except Exception as exc:
                last_error = exc
                message = str(exc).lower()
                if include_thinking_hints and "enable_thinking" in message and "unknown field" in message:
                    include_thinking_hints = False
                    continue
                should_retry = "429" in message or "rate limit" in message or "timed out" in message
                if attempt >= self.max_attempts or not should_retry:
                    raise
                await asyncio.sleep(self.retry_backoff_seconds * attempt)
        raise last_error or ValueError("LLM request failed")


def build_openai_compatible_transport_from_env(
    *,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
    temperature: float = 0.0,
    timeout_seconds: float | None = None,
    max_attempts: int = 1,
    retry_backoff_seconds: float = 1.0,
) -> OpenAICompatibleExtractionTransport:
    """从显式参数或环境变量构造真实的 OpenAI 兼容 transport。"""

    return OpenAICompatibleExtractionTransport(
        api_key=api_key,
        base_url=base_url,
        model=model,
        temperature=temperature,
        timeout_seconds=timeout_seconds,
        max_attempts=max_attempts,
        retry_backoff_seconds=retry_backoff_seconds,
    )


class PharmacopoeiaLLMExtractionRecord(BaseModel):
    """记录单条药典条目在 LLM 边界上的执行结果。"""

    entry_title: str = Field(description="条目标题")
    status: Literal["llm_json_invalid", "llm_request_failed", "llm_schema_invalid", "success"] = Field(
        description="抽取状态"
    )
    raw_response: str = Field(description="LLM 原始响应")
    raw_response_preview: str = Field(description="原始响应摘要")
    elapsed_ms: int = Field(description="LLM 请求耗时（毫秒）")
    error_message: str | None = Field(default=None, description="错误信息")
    validated_extraction: PharmacopoeiaExtractionResult | None = Field(default=None, description="校验通过的抽取结果")

    model_config = ConfigDict(use_enum_values=False)


async def extract_entry_with_llm(
    sections: PharmacopoeiaEntrySections,
    transport: ExtractionTransport,
    request_timeout_seconds: float | None = None,
) -> PharmacopoeiaLLMExtractionRecord:
    """执行单条条目的 LLM 抽取，并把失败类型分类成稳定状态。"""

    payload = build_pharmacopoeia_user_payload(sections)
    started_at = time.perf_counter()
    try:
        # 这里把 transport 调用单独提成 awaitable，便于统一套超时控制。
        request = transport.extract_json_text(
            system_prompt=PHARMACOPOEIA_EXTRACTION_SYSTEM_PROMPT,
            user_payload=payload,
        )
        raw_response = (
            await asyncio.wait_for(request, timeout=request_timeout_seconds)
            if request_timeout_seconds is not None
            else await request
        )
    except asyncio.TimeoutError:
        elapsed_ms = max(0, round((time.perf_counter() - started_at) * 1000))
        return PharmacopoeiaLLMExtractionRecord(
            entry_title=sections.title_zh,
            status="llm_request_failed",
            raw_response="",
            raw_response_preview="",
            elapsed_ms=elapsed_ms,
            error_message=f"LLM request timed out after {request_timeout_seconds}s",
        )
    except Exception as exc:
        elapsed_ms = max(0, round((time.perf_counter() - started_at) * 1000))
        return PharmacopoeiaLLMExtractionRecord(
            entry_title=sections.title_zh,
            status="llm_request_failed",
            raw_response="",
            raw_response_preview="",
            elapsed_ms=elapsed_ms,
            error_message=str(exc),
        )

    elapsed_ms = max(0, round((time.perf_counter() - started_at) * 1000))
    raw_response_preview = raw_response.strip().replace("\n", " ")[:200]
    try:
        parsed = json.loads(raw_response)
    except json.JSONDecodeError as exc:
        return PharmacopoeiaLLMExtractionRecord(
            entry_title=sections.title_zh,
            status="llm_json_invalid",
            raw_response=raw_response,
            raw_response_preview=raw_response_preview,
            elapsed_ms=elapsed_ms,
            error_message=str(exc),
        )

    try:
        validated = PharmacopoeiaExtractionResult.model_validate(parsed)
    except ValidationError as exc:
        return PharmacopoeiaLLMExtractionRecord(
            entry_title=sections.title_zh,
            status="llm_schema_invalid",
            raw_response=raw_response,
            raw_response_preview=raw_response_preview,
            elapsed_ms=elapsed_ms,
            error_message=str(exc),
        )

    return PharmacopoeiaLLMExtractionRecord(
        entry_title=sections.title_zh,
        status="success",
        raw_response=raw_response,
        raw_response_preview=raw_response_preview,
        elapsed_ms=elapsed_ms,
        validated_extraction=validated,
    )
