from typing import Any

from anyio import to_thread

from ..core.config import get_settings
from .llm_client import get_chat_model


class GraphCypherAgentService:
    def __init__(self, chain: Any | None = None) -> None:
        if chain is not None:
            self.chain = chain
            return

        from langchain_neo4j import GraphCypherQAChain, Neo4jGraph

        settings = get_settings()
        graph = Neo4jGraph(
            url=settings.neo4j_uri,
            username=settings.neo4j_user,
            password=settings.neo4j_password,
            refresh_schema=False,
        )
        llm = get_chat_model()
        if llm is None:
            raise RuntimeError("Graph cypher agent requires configured LLM")
        self.chain = GraphCypherQAChain.from_llm(
            llm=llm,
            graph=graph,
            verbose=False,
            allow_dangerous_requests=True,
            return_intermediate_steps=True,
            validate_cypher=True,
            top_k=8,
            use_function_response=True,
        )

    async def answer(self, question: str, top_k: int = 8) -> dict[str, Any]:
        restore_top_k = hasattr(self.chain, "top_k")
        previous_top_k = getattr(self.chain, "top_k", None)
        if restore_top_k:
            self.chain.top_k = top_k
        try:
            result = await to_thread.run_sync(self.chain.invoke, {"query": question})
        finally:
            if restore_top_k:
                self.chain.top_k = previous_top_k
        steps = result.get("intermediate_steps", [])
        generated_cypher = None
        context_rows: list[dict[str, Any]] = []
        for step in steps:
            if not isinstance(step, dict):
                continue
            if generated_cypher is None and isinstance(step.get("query"), str):
                generated_cypher = step["query"]
            context = step.get("context")
            if isinstance(context, list):
                context_rows.extend(
                    row for row in context if isinstance(row, dict)
                )
        node_names = [row["name"] for row in context_rows if isinstance(row, dict) and row.get("name")]
        return {
            "answer": result.get("result", ""),
            "generated_cypher": generated_cypher,
            "node_names": node_names,
            "intermediate_steps": steps,
        }
