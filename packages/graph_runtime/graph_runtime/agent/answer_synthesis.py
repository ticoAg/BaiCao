def synthesize_answer(
    question: str,
    center: dict | None,
    related_nodes: list[dict],
    related_edges: list[dict],
    plan: dict,
) -> str:
    if not center:
        return f"暂未找到与“{question}”直接相关的图谱节点。"

    if related_nodes:
        node_names = "、".join(node.get("name", "") for node in related_nodes if node.get("name"))
        if node_names:
            return f"{center.get('name', center.get('id', '目标节点'))}相关结果：{node_names}。"

    if related_edges:
        edge_types = "、".join(edge.get("type", "") for edge in related_edges if edge.get("type"))
        if edge_types:
            return f"{center.get('name', center.get('id', '目标节点'))}命中了关系：{edge_types}。"

    if plan.get("target_node_types"):
        return f"{center.get('name', center.get('id', '目标节点'))}已命中图谱语义：{'、'.join(plan['target_node_types'])}。"

    return f"已定位到节点 {center.get('name', center.get('id', '目标节点'))}，但暂无更多邻接信息。"
