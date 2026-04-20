async def dfs_walk(backend, seed_node_id: str, max_depth: int, node_budget: int) -> dict:
    visited = set()
    stack = [(seed_node_id, 0)]
    nodes: list[dict] = []
    edges: list[dict] = []
    trace: list[dict] = []

    while stack and len(nodes) < node_budget:
        current_id, depth = stack.pop()
        if current_id in visited or depth > max_depth:
            continue
        visited.add(current_id)
        try:
            expanded = await backend.expand_neighbors(current_id, depth=1, limit=node_budget)
        except KeyError:
            trace.append({"strategy": "dfs", "node_id": current_id, "depth": depth, "skipped": True})
            continue
        for node in expanded.get("nodes", []):
            if len(nodes) >= node_budget:
                break
            nodes.append(node)
            next_id = node.get("id")
            if next_id and next_id not in visited:
                stack.append((next_id, depth + 1))
        edges.extend(expanded.get("edges", []))
        trace.append({"strategy": "dfs", "node_id": current_id, "depth": depth})

    return {"nodes": nodes, "edges": edges, "trace": trace}
