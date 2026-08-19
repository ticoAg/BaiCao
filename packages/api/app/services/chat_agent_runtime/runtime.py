from collections.abc import AsyncIterator
from uuid import uuid4

from agents import Agent, OpenAIChatCompletionsModel, Runner, SQLiteSession, set_tracing_disabled
from openai import AsyncOpenAI

from ...core.config import get_settings
from ..knowledge_mcp.agent_client import get_knowledge_mcp_server
from .openai_event_adapter import adapt_openai_stream
from .session_memory import InMemorySessionManager
from .system_prompt import build_graph_specialist_system_prompt

set_tracing_disabled(disabled=True)

_OPENAI_SESSIONS: dict[str, SQLiteSession] = {}


def _close_registered_session(session_id: str) -> None:
    session = _OPENAI_SESSIONS.pop(session_id, None)
    if session is not None:
        session.close()


_SESSION_MANAGER = InMemorySessionManager(on_evict=_close_registered_session)


def _openai_ready(settings) -> bool:
    key = settings.openai_api_key
    return bool(key) and key != "your_api_key_here" and bool(settings.openai_base_url)


async def build_graph_agent(settings=None) -> Agent:
    current = settings or get_settings()
    client = AsyncOpenAI(api_key=current.openai_api_key, base_url=current.openai_base_url)
    model = OpenAIChatCompletionsModel(model=current.openai_model, openai_client=client)
    mcp_server = await get_knowledge_mcp_server()
    return Agent(
        name="BaiCao Graph Specialist",
        instructions=build_graph_specialist_system_prompt(),
        model=model,
        mcp_servers=[mcp_server],
    )


def _session_for(session_id: str) -> SQLiteSession:
    existing = _OPENAI_SESSIONS.get(session_id)
    if existing is not None:
        return existing
    session = SQLiteSession(session_id)
    _OPENAI_SESSIONS[session_id] = session
    return session


def close_all_openai_sessions() -> None:
    for session_id in list(_OPENAI_SESSIONS):
        _close_registered_session(session_id)


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
            result = Runner.run_streamed(
                await build_graph_agent(settings),
                question,
                session=_session_for(sid),
            )
            async for event in adapt_openai_stream(
                result.stream_events(),
                session_id=sid,
                turn_id=turn_id,
            ):
                yield event
        except Exception as exc:
            yield {"type": "error", "data": {"message": str(exc)}}
