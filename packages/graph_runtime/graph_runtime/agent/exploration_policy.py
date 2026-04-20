def choose_exploration_depth(plan: dict, requested_depth: int) -> int:
    if plan.get("target_node_types"):
        return max(1, requested_depth)
    return 1
