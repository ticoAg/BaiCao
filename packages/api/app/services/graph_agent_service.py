from typing import Any

from graph_runtime.agent.graph_agent import GraphExplorationAgent
from graph_runtime.contracts.inputs import GraphAskRequest
from graph_runtime.service.graph_facade import GraphFacade

from ..graph_runtime_backend import ApiGraphRuntimeBackend


class GraphAgentService:
    def __init__(self, graph_facade: Any | None = None) -> None:
        self.agent = GraphExplorationAgent(
            graph_facade=graph_facade or GraphFacade(ApiGraphRuntimeBackend())
        )

    async def ask(self, question: str) -> dict:
        result = await self.agent.ask(GraphAskRequest(question=question))
        return result.model_dump(mode="json")
