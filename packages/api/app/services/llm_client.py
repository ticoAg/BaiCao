# LLM 客户端 - 基于 LangChain + LangGraph
# 支持 OpenAI 和 Anthropic 双后端，通过 .env 配置切换

import logging
from collections.abc import AsyncIterator, Callable
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel

from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# 知识图谱问答系统提示
SYSTEM_PROMPT = """你是白草药坛的中药材知识助手。基于知识图谱中的药材信息回答用户问题。

规则:
1. 只基于提供的知识图谱上下文回答，不要编造信息
2. 如果知识图谱中没有足够信息，明确告知用户
3. 回答应包含药材的关键属性（功效、性味、归经等）
4. 引用数据来源时注明出处
5. 使用中文回答"""


def _build_user_prompt(question: str, graph_context: str) -> str:
    """构建包含图谱上下文的用户提示"""
    return f"""用户问题: {question}

知识图谱上下文:
{graph_context}

请基于以上知识图谱信息回答用户的问题。如果信息不足，请说明。"""


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
    logger.info("Using OpenAI Responses API (model=%s)", settings.openai_model)
    return ChatOpenAI(**kwargs)


def _try_anthropic() -> BaseChatModel | None:
    """尝试构建 Anthropic ChatModel（Messages API）"""
    if not settings.anthropic_api_key:
        return None
    from langchain_anthropic import ChatAnthropic

    kwargs: dict[str, Any] = {
        "api_key": settings.anthropic_api_key,
        "model": settings.anthropic_model,
        "temperature": settings.llm_temperature,
        "streaming": True,
        "max_tokens": 2048,
    }
    if settings.anthropic_base_url:
        kwargs["base_url"] = settings.anthropic_base_url
    logger.info("Using Anthropic Messages API (model=%s)", settings.anthropic_model)
    return ChatAnthropic(**kwargs)


# provider 名称 → 构建函数
_PROVIDERS: dict[str, Callable[[], BaseChatModel | None]] = {
    "openai": _try_openai,
    "anthropic": _try_anthropic,
}


def get_chat_model() -> BaseChatModel | None:
    """根据配置获取 LangChain ChatModel 实例

    策略:
      1. LLM_PROVIDER 指定了具体 provider → 只尝试该 provider
      2. LLM_PROVIDER=auto（默认）→ 按 openai → anthropic 顺序自动探测第一个有 key 的
      3. LLM_PROVIDER=none → 直接返回 None（规则引擎）

    Returns:
        ChatModel 实例，无可用 provider 时返回 None
    """
    provider = settings.llm_provider.lower()

    # 显式禁用 LLM
    if provider == "none":
        logger.info("LLM disabled (LLM_PROVIDER=none), using rule engine")
        return None

    # 指定具体 provider
    if provider in _PROVIDERS:
        model = _PROVIDERS[provider]()
        if model:
            return model
        logger.warning("LLM_PROVIDER=%s but no valid API key found, trying auto-detect", provider)

    # 自动探测：按优先级尝试所有 provider
    for name, builder in _PROVIDERS.items():
        model = builder()
        if model:
            return model

    logger.warning("No LLM provider available (tried: %s), falling back to rule engine", ", ".join(_PROVIDERS))
    return None


async def stream_llm(question: str, graph_context: str) -> AsyncIterator[str]:
    """统一 LLM 流式接口

    使用 LangChain ChatModel.astream() 实现流式输出。
    当无可用 LLM 时返回空迭代器（由调用方 fallback 到规则引擎）。
    """
    model = get_chat_model()
    if model is None:
        return

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=_build_user_prompt(question, graph_context)),
    ]

    async for chunk in model.astream(messages):
        normalized = _normalize_chunk_content(chunk.content)
        if normalized:
            yield normalized


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


def is_llm_available() -> bool:
    """检查 LLM 是否可用"""
    return get_chat_model() is not None
