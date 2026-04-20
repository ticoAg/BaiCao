def recall_entity_keywords(question: str) -> list[str]:
    normalized = question.replace("？", "").replace("?", "").strip()
    if not normalized:
        return []
    return [token for token in normalized.split() if token]
