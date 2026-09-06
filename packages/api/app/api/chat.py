import json
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..services.chat_agent_runtime import stream_turn as stream_chat_turn

router = APIRouter(prefix="/chat", tags=["chat"])


class AskQuestionRequest(BaseModel):
    question: str = Field(description="用户问题文本")
    session_id: Optional[str] = Field(default=None, description="会话标识")


@router.post("/stream")
async def stream_answer(payload: AskQuestionRequest):
    """SSE 流式问答接口

    事件类型：session、tool_start、tool_result、subgraph_patch、
    answer_chunk、provider_reasoning、final、error。
    """
    async def event_generator():
        async for event in stream_chat_turn(payload.question, payload.session_id):
            event_type = event["type"]
            event_data = json.dumps(event["data"], ensure_ascii=False)
            yield f"event: {event_type}\ndata: {event_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
