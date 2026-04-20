FORBIDDEN = {"CREATE", "MERGE", "DELETE", "SET", "REMOVE", "DROP", "LOAD CSV", "FOREACH", "APOC"}


def ensure_readonly_cypher(query: str) -> str:
    normalized = " ".join(query.strip().split())
    upper = normalized.upper()
    if ";" in normalized:
        raise ValueError("只允许单条只读 Cypher 语句")
    for keyword in FORBIDDEN:
        if keyword in upper:
            raise ValueError("只允许执行只读 Cypher")
    return normalized
