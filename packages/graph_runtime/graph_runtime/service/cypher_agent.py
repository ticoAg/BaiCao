from typing import Any, Protocol


class GraphCypherAgent(Protocol):
    async def answer(self, question: str, top_k: int = 8) -> dict[str, Any]: ...
