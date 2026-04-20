from typing import Any

from graph_runtime.agent.graph_agent import GraphExplorationAgent
from graph_runtime.contracts.inputs import GraphAskRequest
from graph_runtime.service.graph_facade import GraphFacade

from ..graph_runtime_backend import ApiGraphRuntimeBackend
from .graph_cypher_agent import GraphCypherAgentService


class LazyGraphCypherAgent:
    def __init__(self) -> None:
        self._service: GraphCypherAgentService | None = None

    async def answer(self, question: str, top_k: int = 8) -> dict:
        if self._service is None:
            self._service = GraphCypherAgentService()
        return await self._service.answer(question, top_k=top_k)


class GraphAgentService:
    def __init__(self, graph_facade: Any | None = None, cypher_agent: Any | None = None) -> None:
        self.agent = GraphExplorationAgent(
            graph_facade=graph_facade or GraphFacade(ApiGraphRuntimeBackend()),
            cypher_agent=cypher_agent or LazyGraphCypherAgent(),
        )

    async def ask(self, question: str) -> dict:
        result = await self.agent.ask(GraphAskRequest(question=question))
        return result.model_dump(mode="json")
