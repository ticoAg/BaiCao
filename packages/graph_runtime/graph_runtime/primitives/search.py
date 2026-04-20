async def search_nodes(backend, query: str, label: str | None = None, limit: int = 20) -> list[dict]:
    return await backend.search_nodes(query=query, label=label, limit=limit)
