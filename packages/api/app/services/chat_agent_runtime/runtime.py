from collections.abc import AsyncIterator
from typing import cast
from uuid import uuid4

from deepagents import create_deep_agent
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from ..graph_tools import build_graph_tools
from ..llm_client import get_chat_model
from .event_adapter import adapt_agent_events
from .session_memory import InMemorySessionManager
from .system_prompt import build_graph_specialist_system_prompt


_SESSION_MANAGER = InMemorySessionManager()


async def stream_turn(question: str, session_id: str | None = None) -> AsyncIterator[dict]:
    sid = session_id or str(uuid4())
    turn_id = str(uuid4())
    async with _SESSION_MANAGER.session(sid):
        messages = [HumanMessage(content=question)]

        yield {"type": "session", "data": {"session_id": sid, "turn_id": turn_id}}

        model = get_chat_model()
        if model is None:
            yield {"type": "error", "data": {"message": "当前未配置可用的聊天模型，无法执行图谱问答 agent。"}}
            return

        agent = create_deep_agent(
            model=model,
            tools=build_graph_tools(),
            system_prompt=build_graph_specialist_system_prompt(),
            checkpointer=cast(InMemorySaver, _SESSION_MANAGER.checkpointer),
        )

        try:
            async for event in adapt_agent_events(
                agent.astream_events(
                    {"messages": messages},
                    config={"configurable": {"thread_id": sid}},
                    version="v2",
                ),
                session_id=sid,
                turn_id=turn_id,
            ):
                yield event
        except Exception as exc:
            yield {"type": "error", "data": {"message": str(exc)}}
