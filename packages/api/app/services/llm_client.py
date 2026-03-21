# LLM 客户端 - 基于 LangChain + LangGraph
# 支持 OpenAI 和 Anthropic 双后端，通过 .env 配置切换

import logging
from typing import AsyncIterator

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


def get_chat_model() -> BaseChatModel | None:
    """根据配置获取 LangChain ChatModel 实例

    Returns:
        ChatModel 实例，无可用 provider 时返回 None
    """
    provider = settings.llm_provider.lower()

    if provider == "openai" and settings.openai_api_key:
        from langchain_openai import ChatOpenAI

        kwargs = {
            "api_key": settings.openai_api_key,
            "model": settings.openai_model,
            "temperature": settings.llm_temperature,
            "streaming": True,
        }
        if settings.openai_base_url:
            kwargs["base_url"] = settings.openai_base_url
        return ChatOpenAI(**kwargs)

    if provider == "anthropic" and settings.anthropic_api_key:
        from langchain_anthropic import ChatAnthropic

        kwargs = {
            "api_key": settings.anthropic_api_key,
            "model": settings.anthropic_model,
            "temperature": settings.llm_temperature,
            "streaming": True,
            "max_tokens": 2048,
        }
        if settings.anthropic_base_url:
            kwargs["base_url"] = settings.anthropic_base_url
        return ChatAnthropic(**kwargs)

    logger.warning("No LLM provider configured (provider=%s)", provider)
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
        if chunk.content:
            yield chunk.content


def is_llm_available() -> bool:
    """检查 LLM 是否可用"""
    return get_chat_model() is not None
