async def expand_subgraph(backend, node_id: str, depth: int = 1, limit: int = 20) -> dict:
    return await backend.expand_neighbors(node_id=node_id, depth=depth, limit=limit)
