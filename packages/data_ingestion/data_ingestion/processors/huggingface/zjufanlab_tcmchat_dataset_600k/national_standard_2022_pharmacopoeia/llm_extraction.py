from __future__ import annotations

import asyncio
import json
import os
import time
from typing import Literal, Protocol

from openai import AsyncOpenAI
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .extraction_models import PharmacopoeiaEntrySections, PharmacopoeiaExtractionResult
from .prompts import PHARMACOPOEIA_EXTRACTION_SYSTEM_PROMPT, build_pharmacopoeia_user_payload


class ExtractionTransport(Protocol):
    async def extract_json_text(self, *, system_prompt: str, user_payload: dict[str, object]) -> str:
        raise NotImplementedError


class FakeExtractionTransport:
    def __init__(self, response_text: str) -> None:
        self.response_text = response_text

    async def extract_json_text(self, *, system_prompt: str, user_payload: dict[str, object]) -> str:
        return self.response_text


def normalize_openai_base_url(base_url: str) -> str:
    normalized = base_url.rstrip("/")
    if normalized.endswith("/v1"):
        return normalized
    return f"{normalized}/v1"


class OpenAICompatibleExtractionTransport:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        temperature: float = 0.0,
        timeout_seconds: float | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        configured_base_url = base_url or os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1"
        self.base_url = normalize_openai_base_url(configured_base_url)
        self.model = model or os.getenv("OPENAI_MODEL") or "gpt-4.1-mini"
        self.temperature = temperature
        configured_timeout = timeout_seconds or float(os.getenv("OPENAI_TIMEOUT_SECONDS", "90"))
        self.timeout_seconds = configured_timeout
        self.client = AsyncOpenAI(
            api_key=self.api_key or "missing",
            base_url=self.base_url,
            timeout=self.timeout_seconds,
        )

    async def extract_json_text(self, *, system_prompt: str, user_payload: dict[str, object]) -> str:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required for real LLM dry-run")
        response = await self.client.responses.create(
            model=self.model,
            instructions=system_prompt,
            input=json.dumps(user_payload, ensure_ascii=False),
            temperature=self.temperature,
            extra_body={
                "enable_thinking": False,
                "chat_template_kwargs": {"enable_thinking": False},
            },
        )
        response_text = getattr(response, "output_text", "")
        if not response_text:
            raise ValueError("Responses API did not return output_text")
        return response_text


class PharmacopoeiaLLMExtractionRecord(BaseModel):
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
    payload = build_pharmacopoeia_user_payload(sections)
    started_at = time.perf_counter()
    try:
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
