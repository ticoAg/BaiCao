from collections.abc import AsyncIterator
from uuid import uuid4

from mcp.client import Client
from pydantic_ai import Agent, AgentRunResultEvent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from ...core.config import get_settings
from ..knowledge_mcp.server import knowledge_mcp
from .mcp_agent_tools import schema_json_from_client, tools_from_mcp_client
from .pydantic_event_adapter import adapt_pydantic_stream
from .session_memory import InMemorySessionManager
from .system_prompt import build_graph_specialist_system_prompt

_MESSAGE_HISTORIES: dict[str, list] = {}


def _drop_history(session_id: str) -> None:
    _MESSAGE_HISTORIES.pop(session_id, None)


_SESSION_MANAGER = InMemorySessionManager(on_evict=_drop_history)


def _openai_ready(settings) -> bool:
    key = settings.openai_api_key
    return bool(key) and key != "your_api_key_here" and bool(settings.openai_base_url)


def _chat_model(settings) -> OpenAIChatModel:
    return OpenAIChatModel(
        settings.openai_model,
        provider=OpenAIProvider(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url or None,
        ),
    )


async def build_graph_agent(client: Client, settings=None) -> Agent:
    current = settings or get_settings()
    schema = await schema_json_from_client(client)
    return Agent(
        _chat_model(current),
        name="BaiCao Graph Specialist",
        instructions=[
            build_graph_specialist_system_prompt(),
            "当前图谱 schema（JSON）：\n" + schema,
        ],
        tools=await tools_from_mcp_client(client),
    )


def _history_for(session_id: str) -> list:
    return _MESSAGE_HISTORIES.setdefault(session_id, [])


def close_all_chat_sessions() -> None:
    _MESSAGE_HISTORIES.clear()


async def stream_turn(question: str, session_id: str | None = None) -> AsyncIterator[dict]:
    sid = session_id or str(uuid4())
    turn_id = str(uuid4())
    async with _SESSION_MANAGER.session(sid):
        yield {"type": "session", "data": {"session_id": sid, "turn_id": turn_id}}

        settings = get_settings()
        if not _openai_ready(settings):
            yield {
                "type": "error",
                "data": {
                    "message": "当前未配置 OPENAI_API_KEY / OPENAI_BASE_URL，无法启动知识 agent。"
                },
            }
            return

        try:
            async with Client(knowledge_mcp) as client:
                agent = await build_graph_agent(client, settings)
                history = _history_for(sid)

                async with agent.run_stream_events(
                    question, message_history=history or None
                ) as events:

                    async def _forward() -> AsyncIterator:
                        async for event in events:
                            if isinstance(event, AgentRunResultEvent):
                                all_messages = getattr(event.result, "all_messages", None)
                                if callable(all_messages):
                                    _MESSAGE_HISTORIES[sid] = list(all_messages())
                            yield event

                    async for event in adapt_pydantic_stream(
                        _forward(),
                        session_id=sid,
                        turn_id=turn_id,
                    ):
                        yield event
        except Exception as exc:
            yield {"type": "error", "data": {"message": str(exc)}}
