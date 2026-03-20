from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


class AskQuestionRequest(BaseModel):
    question: str
    session_id: Optional[str] = None


@router.post("/question")
async def ask_question(
    payload: Optional[AskQuestionRequest] = Body(None),
    question: Optional[str] = Query(None),
    session_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    提问接口

    基于知识图谱的智能问答，返回回答、推理链和引用来源。
    """
    resolved_question = payload.question if payload else question
    resolved_session_id = payload.session_id if payload else session_id

    if not resolved_question:
        raise HTTPException(status_code=422, detail="question is required")

    chat_service = ChatService(db)
    result = await chat_service.answer_question(resolved_question, resolved_session_id)
    return result


@router.get("/session/{session_id}")
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """获取聊天会话"""
    chat_service = ChatService(db)
    session = await chat_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/session")
async def create_session(
    user_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """创建新的聊天会话"""
    chat_service = ChatService(db)
    session = await chat_service.create_session(user_id)
    return session
