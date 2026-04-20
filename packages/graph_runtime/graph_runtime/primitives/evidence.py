def collect_evidence_snippets(nodes: list[dict]) -> list[dict]:
    evidence: list[dict] = []
    for node in nodes:
        snippet = node.get("snippet") or node.get("summary") or node.get("name")
        if not snippet:
            continue
        evidence.append({"node_id": node.get("id"), "snippet": snippet})
    return evidence
