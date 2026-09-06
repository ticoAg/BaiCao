# LLM 客户端 - OpenAI 兼容接口（Fireworks 等）

from collections.abc import Callable
from typing import Any

from langchain_core.language_models import BaseChatModel

from ..core.config import get_settings
from ..core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


def _try_openai() -> BaseChatModel | None:
    """尝试构建 OpenAI ChatModel（Responses API）"""
    if not settings.openai_api_key or settings.openai_api_key == "your_api_key_here":
        return None
    from langchain_openai import ChatOpenAI

    kwargs: dict[str, Any] = {
        "api_key": settings.openai_api_key,
        "model": settings.openai_model,
        "temperature": settings.llm_temperature,
        "streaming": True,
        "use_responses_api": True,
    }
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url
        kwargs["use_responses_api"] = False
    logger.info("Using OpenAI-compatible Chat Completions (model={model})", model=settings.openai_model)
    return ChatOpenAI(**kwargs)


# provider 名称 → 构建函数
_PROVIDERS: dict[str, Callable[[], BaseChatModel | None]] = {
    "openai": _try_openai,
}


def get_chat_model() -> BaseChatModel | None:
    """根据配置获取 LangChain ChatModel 实例

    策略:
      1. LLM_PROVIDER=openai（默认）→ 使用 OpenAI 兼容 Chat Completions
      2. LLM_PROVIDER=none → 直接返回 None

    Returns:
        ChatModel 实例，无可用 provider 时返回 None
    """
    provider = settings.llm_provider.lower()

    if provider == "none":
        logger.info("LLM disabled (LLM_PROVIDER=none)")
        return None

    if provider in _PROVIDERS:
        model = _PROVIDERS[provider]()
        if model:
            return model
        logger.warning("LLM_PROVIDER={provider} but no valid API key found, trying auto-detect", provider=provider)

    for name, builder in _PROVIDERS.items():
        model = builder()
        if model:
            return model

    logger.warning(
        "No LLM provider available (tried: {providers})",
        providers=", ".join(_PROVIDERS),
    )
    return None


def _normalize_chunk_content(content: Any) -> str:
    """将 LangChain 流式 chunk 的 content 统一规整为字符串。"""
    if content is None:
        return ""

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
                continue
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
                    continue
            text_attr = getattr(item, "text", None)
            if isinstance(text_attr, str):
                parts.append(text_attr)
        return "".join(parts)

    text_attr = getattr(content, "text", None)
    if isinstance(text_attr, str):
        return text_attr

    return str(content)
