from fastapi import APIRouter
from pydantic import BaseModel

from ..services.graph_agent_service import GraphAgentService

router = APIRouter(prefix="/graph-agent", tags=["graph-agent"])


class GraphAgentAskPayload(BaseModel):
    question: str


@router.post("/ask")
async def ask_graph_agent(payload: GraphAgentAskPayload):
    return await GraphAgentService().ask(payload.question)
